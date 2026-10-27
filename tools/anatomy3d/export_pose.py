# Экспорт позы модели OpenSim (Rajagopal, Lai, Uhlrich 2023) в JSON для рендера в three.js.
# Запуск: python3 tools/anatomy3d/export_pose.py <поза.json> <выход.json>
# Поза: {"coords": {"имя_координаты": градусы, ...}, "tiers": {"мышца_без_стороны": 1..4}, "bar": true}
# Тиры: 1 главные (бордовый), 2 вторые (светло-красный), 3 помощники (зелёный), 4 стабилизаторы в тонусе (синий).
import json, math, os, re, sys
import numpy as np
import opensim as osim

ROOT = os.environ.get('OSIM_MODELS', '/home/user/opensim-org/opensim-models')
MODEL = f'{ROOT}/Models/Rajagopal/RajagopalLaiUhlrich2023.osim'
GEOM_DIRS = [f'{ROOT}/Models/Rajagopal/Geometry', f'{ROOT}/Geometry']


def read_vtp(path):
    txt = open(path).read()
    def arr(tag):
        m = re.search(rf'<{tag}>(.*?)</{tag}>', txt, re.S)
        return m.group(1) if m else ''
    pts = re.search(r'<Points>\s*<DataArray[^>]*>(.*?)</DataArray>', txt, re.S).group(1)
    v = np.array(pts.split(), dtype=float).reshape(-1, 3)
    polys = arr('Polys')
    conn = re.search(r'Name="connectivity"[^>]*>(.*?)</DataArray>', polys, re.S).group(1)
    offs = re.search(r'Name="offsets"[^>]*>(.*?)</DataArray>', polys, re.S).group(1)
    conn = np.array(conn.split(), dtype=int); offs = np.array(offs.split(), dtype=int)
    faces, start = [], 0
    for o in offs:
        poly = conn[start:o]
        for i in range(1, len(poly) - 1):  # веер треугольников
            faces.append((poly[0], poly[i], poly[i + 1]))
        start = o
    return v, np.array(faces, dtype=int)


def find_mesh(name):
    for d in GEOM_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


def main(pose_path, out_path):
    pose = json.load(open(pose_path))
    for d in GEOM_DIRS:
        osim.ModelVisualizer.addDirToGeometrySearchPaths(d)
    m = osim.Model(MODEL)
    s = m.initSystem()
    cs = m.getCoordinateSet()
    for i in range(cs.getSize()): cs.get(i).setClamped(s, False)
    for name, deg in pose['coords'].items():
        c = cs.get(name)
        val = math.radians(deg) if c.getMotionType() != 2 else deg  # 2 = поступательная, в метрах
        c.setValue(s, val, False)
    m.assemble(s)
    # assemble возвращает координаты в пределы модели; позу из файла ставим заново поверх (без пересборки)
    for name, deg in pose['coords'].items():
        c = cs.get(name)
        if not c.getLocked(s):
            c.setValue(s, math.radians(deg) if c.getMotionType() != 2 else deg, False)
    m.realizePosition(s)

    bones = []
    bs = m.getBodySet()
    for i in range(bs.getSize()):
        b = bs.get(i)
        for g in range(b.getPropertyByName('attached_geometry').size()):
            geo = b.get_attached_geometry(g)
            mesh = osim.Mesh.safeDownCast(geo)
            if mesh is None:
                continue
            path = find_mesh(mesh.get_mesh_file())
            if not path:
                print('нет файла', mesh.get_mesh_file()); continue
            v, f = read_vtp(path)
            if len(v) < 2500:  # упрощённые кости сглаживаем подразбиением Loop
                import trimesh
                tm = trimesh.Trimesh(v, f, process=True)
                for _ in range(2 if len(v) < 800 else 1):
                    try:
                        vv, ff = trimesh.remesh.subdivide_loop(tm.vertices, tm.faces)
                        tm = trimesh.Trimesh(vv, ff, process=False)
                    except ValueError:  # неманифолдная сетка: делим пополам и сглаживаем
                        vv, ff = trimesh.remesh.subdivide(tm.vertices, tm.faces)
                        tm = trimesh.Trimesh(vv, ff, process=True)
                        trimesh.smoothing.filter_taubin(tm, iterations=8)
                v, f = np.asarray(tm.vertices), np.asarray(tm.faces)
            sc = mesh.get_scale_factors(); v = v * np.array([sc.get(0), sc.get(1), sc.get(2)])
            T = mesh.getFrame().getTransformInGround(s)
            R = np.array([[T.R().get(r, c) for c in range(3)] for r in range(3)])
            p = np.array([T.p().get(k) for k in range(3)])
            w = v @ R.T + p
            bones.append({'name': mesh.get_mesh_file(), 'v': np.round(w, 5).ravel().tolist(), 'f': f.ravel().tolist()})

    tiers = pose.get('tiers', {})
    muscles = []
    ms = m.getMuscles()
    for i in range(ms.getSize()):
        mu = ms.get(i)
        base = re.sub(r'_[rl]$', '', mu.getName())
        tier = tiers.get(base)
        if not tier:
            continue
        cp = mu.getGeometryPath().getCurrentPath(s)
        pts = []
        for k in range(cp.getSize()):
            q = cp.get(k).getLocationInGround(s)
            pts.append([round(q.get(0), 5), round(q.get(1), 5), round(q.get(2), 5)])
        muscles.append({'name': mu.getName(), 'tier': tier, 'force': mu.getMaxIsometricForce(), 'pts': pts})

    # пол по самой нижней точке стоп, полезные ориентиры для штанги и стрелок
    allv = np.concatenate([np.array(b['v']).reshape(-1, 3) for b in bones])
    floor = float(allv[:, 1].min())
    def body_origin(name):
        t = bs.get(name).getTransformInGround(s).p(); return [t.get(0), t.get(1), t.get(2)]
    def body_frame(name):
        T = bs.get(name).getTransformInGround(s)
        return {'p': [T.p().get(k) for k in range(3)], 'R': [[T.R().get(r, c) for c in range(3)] for r in range(3)]}
    out = {'bones': bones, 'muscles': muscles, 'floor': floor, 'frames': {k: body_frame(k) for k in ['pelvis', 'torso']},
           'marks': {k: body_origin(k) for k in ['pelvis', 'torso', 'femur_r', 'tibia_r', 'calcn_r', 'humerus_r', 'hand_r', 'hand_l']}}
    json.dump(out, open(out_path, 'w'))
    print('костей', len(bones), 'мышц', len(muscles), 'пол', round(floor, 3))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
