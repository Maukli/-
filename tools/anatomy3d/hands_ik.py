# Подбирает углы рук, чтобы кисти легли на гриф (точка задаётся в системе координат корпуса).
# Запуск: python3 tools/anatomy3d/hands_ik.py <поза.json>  (дописывает углы рук в позу)
import json, math, os, sys
import numpy as np
import opensim as osim
from scipy.optimize import minimize

ROOT = '/home/user/opensim-org/opensim-models'
pose_path = sys.argv[1]
pose = json.load(open(pose_path))
m = osim.Model(f'{ROOT}/Models/Rajagopal/RajagopalLaiUhlrich2023.osim')
s = m.initSystem(); cs = m.getCoordinateSet()
for i in range(cs.getSize()): cs.get(i).setDefaultClamped(False); cs.get(i).setClamped(s, False)
def setc(name, deg): cs.get(name).setValue(s, math.radians(deg), False)
for k, v in pose['coords'].items(): setc(k, v)
m.assemble(s); m.realizePosition(s)
T = m.getBodySet().get('torso').getTransformInGround(s)
R = np.array([[T.R().get(r, c) for c in range(3)] for r in range(3)]); p = np.array([T.p().get(k) for k in range(3)])
bar = p + R @ np.array(pose['bar_local'])
grip = pose.get('grip', 0.42)
names = ['arm_flex', 'arm_add', 'arm_rot', 'elbow_flex', 'pro_sup', 'wrist_flex', 'wrist_dev']
bounds = [(-100, 90), (-120, 90), (-130, 90), (0, 150), (0, 120), (-70, 70), (-25, 35)]
if 'grip_local' in pose:
    gl = pose['grip_local']
elif pose.get('grip_curl'):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from export_pose import curl_center
    gl = curl_center(pose['grip_curl'], m)[0]
else:
    gl = [0.03, -0.12, -0.005]
GRIP = osim.Vec3(*gl)  # центр обхвата в системе кисти: сюда ставится гриф
for side, sz in (('r', 1), ('l', -1)):
    target = bar + np.array([0, -pose.get('wrist_below', 0.0), sz * grip])  # начало кисти это запястье, оно чуть ниже грифа
    el = pose.get('elbow_local')  # желаемый локоть в системе корпуса (z для правой стороны)
    elbow_target = p + R @ np.array([el[0], el[1], sz * el[2]]) if el else None
    hand = m.getBodySet().get(f'hand_{side}'); ulna = m.getBodySet().get(f'ulna_{side}')
    def pos(body):
        q = body.getTransformInGround(s).p(); return np.array([q.get(0), q.get(1), q.get(2)])
    def cost(x):
        for n, v in zip(names, x): setc(f'{n}_{side}', v)
        m.realizePosition(s)
        q = hand.findStationLocationInGround(s, GRIP)
        d = np.array([q.get(0), q.get(1), q.get(2)]) - target
        c = float(d @ d)
        Rh = hand.getTransformInGround(s).R()
        hz = np.array([Rh.get(0, 2), Rh.get(1, 2), Rh.get(2, 2)])
        c += 0.02 * (1 - abs(hz[2]))  # ось пальцев поперёк грифа: z кисти вдоль грифа (мировая z)
        if elbow_target is not None:
            e = pos(ulna) - elbow_target; c += pose.get('elbow_w', 0.5) * float(e @ e)
        return c
    x0 = [pose['coords'].get(f'{n}_{side}', d) for n, d in zip(names, [0, -60, 0, 110, 60, 0, 0])]
    best = min((minimize(cost, st, method='L-BFGS-B', bounds=bounds) for st in [x0, [-44, -27, -110, 120, 60, 0, 0], [-44, -27, -110, 120, 100, -30, 0], [-30, -60, -60, 120, 20, 20, 0], [-50, -30, -120, 110, 110, 40, 10]]), key=lambda r: r.fun)
    for n, v in zip(names, best.x): pose['coords'][f'{n}_{side}'] = round(float(v), 1)
    cost(best.x)
    gq = hand.findStationLocationInGround(s, GRIP); eh = np.linalg.norm(np.array([gq.get(0), gq.get(1), gq.get(2)]) - target) * 100
    ee = np.linalg.norm(pos(ulna) - elbow_target) * 100 if elbow_target is not None else 0
    print(side, 'кисть мимо, см', round(eh, 1), 'локоть мимо, см', round(ee, 1), [round(v) for v in best.x])
pose['bar_world'] = [round(float(x), 4) for x in bar]
json.dump(pose, open(pose_path, 'w'), ensure_ascii=False, indent=1)
print('гриф', pose['bar_world'])
