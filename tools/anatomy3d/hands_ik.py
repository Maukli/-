# Подбирает углы рук, чтобы кисти легли на гриф (точка задаётся в системе координат корпуса).
# Запуск: python3 tools/anatomy3d/hands_ik.py <поза.json>  (дописывает углы рук в позу)
import json, math, sys
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
names = ['arm_flex', 'arm_add', 'arm_rot', 'elbow_flex']
bounds = [(-100, 90), (-120, 90), (-130, 90), (0, 150)]
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
        d = pos(hand) - target
        c = float(d @ d)
        if elbow_target is not None:
            e = pos(ulna) - elbow_target; c += pose.get('elbow_w', 0.5) * float(e @ e)
        return c
    x0 = [pose['coords'].get(f'{n}_{side}', 0) for n in names]
    best = min((minimize(cost, st, method='L-BFGS-B', bounds=bounds) for st in [x0, [-30, -80, 40, 120], [-50, -60, 60, 140], [-20, -70, -40, 110], [0, -90, -60, 120], [-40, -40, 0, 130]]), key=lambda r: r.fun)
    for n, v in zip(names, best.x): pose['coords'][f'{n}_{side}'] = round(float(v), 1)
    cost(best.x)
    eh = np.linalg.norm(pos(hand) - target) * 100
    ee = np.linalg.norm(pos(ulna) - elbow_target) * 100 if elbow_target is not None else 0
    print(side, 'кисть мимо, см', round(eh, 1), 'локоть мимо, см', round(ee, 1), [round(v) for v in best.x])
pose['bar_world'] = [round(float(x), 4) for x in bar]
json.dump(pose, open(pose_path, 'w'), ensure_ascii=False, indent=1)
print('гриф', pose['bar_world'])
