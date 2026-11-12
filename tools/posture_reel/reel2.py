# Рилс "Живот выпирает, хотя жира мало", версия 2 (12.11): экспертная подача кинезиолога.
# Чертёжная графика на теле (по отслеживанию суставов MediaPipe), схема таза, карточки с официальными названиями,
# лестница протокола сверху вниз. Голоса пока нет: субтитры показывают будущий текст.
# Запуск: python3 reel2.py   (исходники raw/, фото photos/, позы считает pose.py и кэширует в pose/)
import os, sys, math, subprocess
import numpy as np
from multiprocessing import Pool
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import pelvis as PV
import pose as POSE

OUT = f'{B}/seg2'
GRADE = ("eq=contrast=1.05:saturation=0.96:brightness=0.01,"
         "colorbalance=rs=-0.02:bs=0.02:rh=0.04:bh=-0.03,unsharp=5:5:0.5:5:5:0.0,vignette=angle=PI/6,noise=alls=2:allf=t")
Z9673 = 'crop=iw/1.6:ih/1.6:iw*0.16:ih*0.26,'
IDX = {'ear': (7, 8), 'sh': (11, 12), 'el': (13, 14), 'wr': (15, 16), 'hip': (23, 24), 'knee': (25, 26), 'ank': (27, 28),
       'heel': (29, 30), 'toe': (31, 32)}


class Pose:
    def __init__(self, raw):
        arr = []
        last = None
        for f in raw:
            last = f if f else last
            arr.append(last)
        a = np.array(arr, dtype=float)  # (N,33,3)
        k = 7
        pad = np.pad(a, ((k // 2, k // 2), (0, 0), (0, 0)), mode='edge')
        self.a = np.stack([pad[i:i + len(a)] for i in range(k)]).mean(0)
        self.a[:, :, 0] *= W; self.a[:, :, 1] *= H
        vis = self.a[:, :, 2].mean(0)
        self.side = 0 if sum(vis[i] for i in (7, 11, 23, 25, 27)) >= sum(vis[i] for i in (8, 12, 24, 26, 28)) else 1
        self.i = 0

    def p(self, name, side=None):
        j = IDX[name][self.side if side is None else side] if name in IDX else name
        x, y = self.a[min(self.i, len(self.a) - 1), j, :2]
        return (float(x), float(y))

    def fwd(self):
        n, e = self.p(0), self.p('ear')
        return -1 if n[0] < e[0] else 1


# ---------- кадры с графикой ----------

def fx_plumb(L, t, P, d):
    grid(L, 0.07 * ph(t, 0, 0.5))
    chip(L, ['ОЦЕНКА ОСАНКИ', 'ВИД СБОКУ, САГИТТАЛЬНАЯ ПЛОСКОСТЬ'], ph(t, 0.1, 0.4), y=1430)
    f = P.fwd()
    pts = [(P.p('ear'), 'НАРУЖНЫЙ СЛУХОВОЙ ПРОХОД'), (P.p('sh'), 'АКРОМИОН'), (P.p('hip'), 'БОЛЬШОЙ ВЕРТЕЛ'),
           (P.p('knee'), 'КОЛЕННЫЙ СУСТАВ'), (P.p('ank'), 'ЛАТЕРАЛЬНАЯ ЛОДЫЖКА')]
    x0 = pts[-1][0][0] + f * 14
    polyline(L, [(x0, pts[0][0][1] - 170), (x0, pts[-1][0][1] + 60)], WHITE, 3, ph(t, 0.3, 1.0), 0.9, dash=(16, 10))
    text(L, (x0, pts[0][0][1] - 190), 'ЛИНИЯ ОТВЕСА', 30, WHITE, ph(t, 0.7, 0.4), 'mb')
    for i, (p, name) in enumerate(pts):
        a = ph(t, 1.1 + 0.42 * i, 0.35)
        if a <= 0:
            continue
        polyline(L, [p, (x0, p[1])], YEL, 2.5, a, a, dash=(8, 6))
        lx = max(p[0], x0) + 70 if f < 0 else min(p[0], x0) - 70
        callout(L, p, (lx, p[1] - (110 if i == 4 else 30)), [name], YEL, a, 28)


def pelvis_pts(P):
    h, s = P.p('hip'), P.p('sh')
    L_ = math.dist(h, s); f = P.fwd()
    asis = (h[0] + f * 0.20 * L_, h[1] - 0.20 * L_)
    psis = (h[0] - f * 0.30 * L_, h[1] - 0.26 * L_)
    return asis, psis, f


def fx_pelvis(L, t, P, d):
    grid(L, 0.06 * ph(t, 0, 0.5))
    asis, psis, f = pelvis_pts(P)
    a1, a2 = ph(t, 0.3, 0.4), ph(t, 1.1, 0.4)
    callout(L, asis, (asis[0] + f * 70, asis[1] - 260), ['ПЕРЕДНЯЯ ВЕРХНЯЯ', 'ПОДВЗДОШНАЯ ОСТЬ'], YEL, a1, 30)
    callout(L, psis, (psis[0] - f * 60, psis[1] - 330), ['ЗАДНЯЯ ВЕРХНЯЯ', 'ПОДВЗДОШНАЯ ОСТЬ'], YEL, a2, 30)
    polyline(L, [psis, asis], YEL, 5, ph(t, 2.0, 0.6), 1)
    polyline(L, [psis, (psis[0] + f * 520, psis[1])], WHITE, 2.5, ph(t, 2.7, 0.5), 0.8, dash=(12, 9))
    if t > 3.2:
        ang = math.degrees(math.atan2(asis[1] - psis[1], asis[0] - psis[0]))
        a0 = 180 if f < 0 else 0
        polyline(L, arc_pts(psis, 200, a0, ang), YEL, 4, ph(t, 3.2, 0.5), 1)
        mid = math.radians((a0 + ang) / 2)
        text(L, (psis[0] + 250 * math.cos(mid), psis[1] + 250 * math.sin(mid) + 40), 'УГОЛ НАКЛОНА ТАЗА', 34, YEL,
             ph(t, 3.5, 0.4), 'mm')


def fx_tilt(L, t, P, d):
    th = 7 + 13 * ph(t, 1.3, 2.6)
    grid(L, 0.10)
    chip(L, ['АНТЕВЕРСИЯ ТАЗА', 'СХЕМА, ВИД СБОКУ'], ph(t, 0.1, 0.4))
    PV.body_outline(L, th, ph(t, 0.2, 0.6))
    g = PV.draw_skeleton(L, th, 1, ph(t, 0.0, 1.0))
    PV.angle_mark(L, g, ph(t, 0.9, 0.4))
    text(L, (g['asis'][0] - 30, g['asis'][1] + 50), 'ПЕРЕДНЯЯ ОСТЬ', 26, YEL, ph(t, 1.0, 0.4), 'ra', 3)
    text(L, (g['psis'][0] + 30, g['psis'][1] - 40), 'ЗАДНЯЯ ОСТЬ', 26, YEL, ph(t, 1.0, 0.4), 'la', 3)
    arc_arrow(L, PV.HC, 330, 150, 205, YEL, 5, ph(t, 1.3, 1.6), ph(t, 1.3, 0.3))
    text(L, (PV.HC[0] - 360, PV.HC[1] + 210), 'НАКЛОН ВПЕРЁД', 32, YEL, ph(t, 1.6, 0.4), 'ma')
    c3 = g['verts'][2][0]
    callout(L, c3, (c3[0] + 330, c3[1] - 60), ['ПОЯСНИЧНЫЙ', 'ГИПЕРЛОРДОЗ'], RED, ph(t, 3.9, 0.4), 32)
    belly = (PV.HC[0] - 275 - 7 * (th - 7), PV.HC[1] - 470)
    arrow(L, (belly[0] + 10, belly[1]), (belly[0] - 130, belly[1]), RED, 6, ph(t, 4.5, 0.4), ph(t, 4.5, 0.2))
    text(L, (belly[0] - 20, belly[1] + 60), 'ЖИВОТ ВПЕРЁД', 30, RED, ph(t, 4.7, 0.4), 'la')


def fx_janda(L, t, P, d):
    th = 20
    grid(L, 0.10)
    chip(L, ['НИЖНИЙ ПЕРЕКРЁСТНЫЙ СИНДРОМ', 'МОДЕЛЬ В. ЯНДЫ'], ph(t, 0.1, 0.4))
    PV.body_outline(L, th, 0.8)
    g = PV.draw_skeleton(L, th, 0.75, 1, labels=False)
    HC = PV.HC
    # разгибатели поясницы: позади остистых отростков
    er = []
    for c, phi in reversed(g['verts']):
        dx, dy = -math.sin(math.radians(phi)), -math.cos(math.radians(phi))
        nx, ny = -dy, dx
        if nx > 0:
            nx, ny = -nx, -ny
        er.append((c[0] - nx * 150, c[1] - ny * 150))
    er.append(PV.rot((175, -150), th))
    ip = [(c[0] + 30, c[1]) for c, _ in list(reversed(g['verts']))[:4]] + [(HC[0] - 70, HC[1] - 30), (HC[0] + 30, HC[1] + 130)]
    ip = PV.catmull(ip, 8, False)
    ra = PV.catmull([(HC[0] - 215, HC[1] - 800), (HC[0] - 238 - 7 * (th - 7), HC[1] - 470), (HC[0] - 215 - 3 * (th - 7), HC[1] - 190),
                     PV.rot((-118, 110), th)], 10, False)
    gm = PV.catmull([PV.rot((150, -110), th), (HC[0] + 255, HC[1] + 10), (HC[0] + 200, HC[1] + 170), (HC[0] + 110, HC[1] + 240)], 10, False)
    polyline(L, er, RED, 18, ph(t, 0.6, 0.6), 0.75)
    polyline(L, ip, RED, 18, ph(t, 1.5, 0.7), 0.75)
    polyline(L, ra, BLUE, 18, ph(t, 3.4, 0.6), 0.75)
    polyline(L, gm, BLUE, 18, ph(t, 4.2, 0.6), 0.75)
    m_er, m_ip, m_ra, m_gm = er[2], ip[len(ip) // 2], ra[len(ra) // 2], gm[len(gm) // 2]
    callout(L, m_er, (m_er[0] + 150, m_er[1] - 160), ['РАЗГИБАТЕЛИ', 'ПОЯСНИЦЫ'], RED, ph(t, 0.9, 0.4), 30)
    callout(L, m_ip, (m_ip[0] - 240, m_ip[1] + 230), ['ПОДВЗДОШНО-', 'ПОЯСНИЧНАЯ'], RED, ph(t, 1.9, 0.4), 30)
    callout(L, m_ra, (m_ra[0] - 10, m_ra[1] - 300), ['МЫШЦЫ ЖИВОТА'], BLUE, ph(t, 3.7, 0.4), 30)
    callout(L, m_gm, (m_gm[0] + 40, m_gm[1] - 200), ['БОЛЬШАЯ', 'ЯГОДИЧНАЯ'], BLUE, ph(t, 4.5, 0.4), 30)
    polyline(L, [m_er, m_ip], RED, 4, ph(t, 2.5, 0.6), 0.95, dash=(16, 10))
    polyline(L, [m_ra, m_gm], BLUE, 4, ph(t, 5.1, 0.6), 0.95, dash=(16, 10))
    a = ph(t, 5.8, 0.4)
    if a > 0:
        panel(L, (60, 1440, 1020, 1580), a, WHITE)
        L.d.rectangle([S((100, 1470)), S((140, 1500))], fill=rgba(RED, a))
        text(L, (160, 1485), 'ГИПЕРТОНУС', 34, WHITE, a, 'lm', 0)
        L.d.rectangle([S((100, 1525)), S((140, 1555))], fill=rgba(BLUE, a))
        text(L, (160, 1540), 'СЛАБО ВКЛЮЧАЮТСЯ', 34, WHITE, a, 'lm', 0)


def fx_card1(L, t, P, d):
    card(L, 60, 1080, 'YOUDAS, 1996', ['90 взрослых без боли в спине', 'Сила пресса и угол таза у мужчин'], ph(t, 0.8, 0.4), t, 0.8, BLUE, 760)
    a = ph(t, 2.6, 0.3)
    if a > 0:
        panel(L, (60, 1300, 470, 1390), a, YEL)
        text(L, (90, 1345), 'СВЯЗИ НЕТ', 52, YEL, a, 'lm', 0)


def fx_card2(L, t, P, d):
    a = ph(t, 0.1, 0.4)
    if a <= 0:
        return
    panel(L, (60, 1020, 1020, 1430), a, BLUE)
    text(L, (90, 1040), 'LEVINE, 1997', 40, BLUE, a, stroke=0)
    text(L, (90, 1095), 'Тренировка мышц живота', 31, WHITE, a, stroke=0)
    rows = [('СИЛА ПРЕССА', 0.45, 0.88), ('УГОЛ ТАЗА', 0.62, 0.62)]
    for i, (lab, b0, b1) in enumerate(rows):
        y = 1180 + i * 120
        text(L, (90, y), lab, 30, WHITE, a, stroke=0)
        L.d.rectangle([S((330, y + 2)), S((330 + 600 * b0, y + 28))], fill=rgba((140, 160, 185), a))
        text(L, (330 + 600 * b0 + 12, y + 15), 'ДО', 22, WHITE, a * 0.8, 'lm', 0)
        grow = ph(t, 0.9 + 0.5 * i, 0.8)
        L.d.rectangle([S((330, y + 40)), S((330 + 600 * (b0 + (b1 - b0) * grow) if b1 != b0 else 330 + 600 * b1 * grow, y + 66))],
                      fill=rgba(YEL, a))
        text(L, (330 + 600 * b1 + 12, y + 53), 'ПОСЛЕ', 22, YEL, a * ph(t, 1.5 + 0.5 * i, 0.3), 'lm', 0)


def fx_85(L, t, P, d):
    a = ph(t, 0.1, 0.4)
    panel(L, (60, 190, 1020, 830), a, YEL)
    n = int(round(85 * ph(t, 0.3, 1.6)))
    text(L, (540, 370), f'{n}%', 190, YEL, a, 'mm', 0)
    text(L, (540, 500), 'ЗДОРОВЫХ МУЖЧИН С ЛЁГКОЙ АНТЕВЕРСИЕЙ', 32, WHITE, a, 'mm', 0)
    for i, (lab, v) in enumerate([('МУЖЧИНЫ', 85), ('ЖЕНЩИНЫ', 75)]):
        y = 575 + i * 62
        g = ph(t, 1.2 + 0.3 * i, 0.9)
        text(L, (100, y + 14), lab, 28, WHITE, a, 'lm', 0)
        L.d.rectangle([S((260, y)), S((260 + 620, y + 28))], fill=rgba((60, 75, 95), a))
        L.d.rectangle([S((260, y)), S((260 + 620 * v / 100 * g, y + 28))], fill=rgba(YEL if i == 0 else WHITE, a))
        text(L, (900, y + 14), f'{int(v * g)}%', 28, WHITE, a * g, 'lm', 0)
    text(L, (100, 735), 'HERRINGTON, 2011: 120 ЧЕЛОВЕК БЕЗ БОЛИ', 24, (170, 185, 205), a, 'lm', 0)
    b = ph(t, 3.6, 0.3)
    if b > 0:
        panel(L, (300, 860, 780, 950), b, GREEN)
        text(L, (540, 905), 'ВАРИАНТ НОРМЫ', 46, GREEN, b, 'mm', 0)


def fx_intro(L, t, P, d):
    a = ph(t, 0.05, 0.3)
    panel(L, (40, 300, 720, 1250), a * 0.9, YEL)
    text(L, (80, 340), 'ПРОТОКОЛ: СВЕРХУ ВНИЗ', 46, YEL, a, stroke=0)
    ladder(L, 1, a, big=True, t=t, t0=0.2)


def steps(L, t, step, title, lines, accent=YEL):
    ladder(L, step, ph(t, 0.0, 0.3))
    card(L, 40, 150, title, lines, ph(t, 0.05, 0.35), t, 0.05, accent, 700)


def fx_neck(L, t, P, d):
    steps(L, t, 1, '1. ШЕЙНЫЙ ОТДЕЛ', ['Сгибание из нейтрального положения', 'Плоскость: сагиттальная'])
    e, s, f = P.p('ear'), P.p('sh'), P.fwd()
    ln = math.dist(e, s)
    polyline(L, [s, e], YEL, 5, ph(t, 0.5, 0.5), 1)
    marker(L, e, YEL, 11, ph(t, 0.5, 0.3)); marker(L, s, YEL, 11, ph(t, 0.5, 0.3))
    a0, a1 = (225, 130) if f < 0 else (-45, 50)
    arc_arrow(L, e, 0.75 * ln, a0, a1, YEL, 6, ph(t, 1.0, 0.8), ph(t, 1.0, 0.2))
    text(L, (e[0] + f * 0.95 * ln, e[1] - 0.2 * ln), 'СГИБАНИЕ', 34, YEL, ph(t, 1.4, 0.4), 'rm' if f < 0 else 'lm')
    nk = lerp(e, s, 0.45); nk = (nk[0] + f * 0.2 * ln, nk[1])
    callout(L, nk, (nk[0] - f * 330, nk[1] + 330), ['ГЛУБОКИЕ СГИБАТЕЛИ ШЕИ', 'длинная мышца шеи и головы'], YEL, ph(t, 2.0, 0.4), 30)


def fx_scap(L, t, P, d):
    steps(L, t, 2, '2. ЛОПАТКИ', ['Ретракция и депрессия', 'Ромбовидные, средняя и нижняя части трапециевидной'])
    ls, rs, lh, rh = P.p('sh', 0), P.p('sh', 1), P.p('hip', 0), P.p('hip', 1)
    ms, mh = lerp(ls, rs, 0.5), lerp(lh, rh, 0.5)
    tl = math.dist(ms, mh)
    polyline(L, [(ms[0], ms[1] - 40), mh], WHITE, 3, ph(t, 0.4, 0.6), 0.85, dash=(14, 9))
    for i, sp in enumerate((ls, rs)):
        q = (sp[0] + (ms[0] - sp[0]) * 0.42, sp[1] + 0.26 * tl)
        a = ph(t, 0.8 + 0.2 * i, 0.4)
        marker(L, q, YEL, 12, a)
        tip = (q[0] + (ms[0] - q[0]) * 0.55, q[1])
        arrow(L, q, tip, YEL, 6, ph(t, 1.1 + 0.2 * i, 0.4), a)
        arrow(L, (q[0], q[1] + 20), (q[0], q[1] + 120), BLUE, 6, ph(t, 2.2 + 0.2 * i, 0.4), ph(t, 2.2, 0.2))
    text(L, (ms[0], ms[1] + 0.26 * tl - 70), 'РЕТРАКЦИЯ', 34, YEL, ph(t, 1.4, 0.4), 'mm')
    text(L, (ms[0], ms[1] + 0.26 * tl + 175), 'ДЕПРЕССИЯ', 34, BLUE, ph(t, 2.5, 0.4), 'mm')


def fx_ham(L, t, P, d):
    steps(L, t, 3, '3. ЗАДНЯЯ ПОВЕРХНОСТЬ БЕДРА', ['Через 2 недели, вместе с поясницей', 'Двуглавая, полусухожильная, полуперепончатая',
                                                     'Икроножная в активной недостаточности'])
    h, k, an = P.p('hip'), P.p('knee'), P.p('ank')
    polyline(L, [h, k], YEL, 20, ph(t, 0.5, 0.5), 0.45)
    polyline(L, [k, an], WHITE, 4, ph(t, 0.7, 0.4), 0.9)
    a1 = math.degrees(math.atan2(h[1] - k[1], h[0] - k[0])); a2 = math.degrees(math.atan2(an[1] - k[1], an[0] - k[0]))
    if a2 - a1 > 180: a2 -= 360
    if a1 - a2 > 180: a2 += 360
    polyline(L, arc_pts(k, 75, a1, a2), YEL, 5, ph(t, 1.0, 0.4), 1)
    marker(L, k, YEL, 11, ph(t, 1.0, 0.3))
    callout(L, k, (k[0] + 200, k[1] - 120), ['СГИБАНИЕ', 'в коленном суставе'], YEL, ph(t, 1.3, 0.4), 30)
    callout(L, an, (an[0] - 240, an[1] - 260), ['ПОДОШВЕННОЕ', 'СГИБАНИЕ СТОПЫ'], WHITE, ph(t, 2.6, 0.4), 28)


def fx_glmed(L, t, P, d):
    steps(L, t, 4, '4. СРЕДНЯЯ ЯГОДИЧНАЯ', ['Стабилизация таза во фронтальной плоскости', 'Проба Тренделенбурга отрицательная'])
    lh, rh = P.p('hip', 0), P.p('hip', 1)
    v = (rh[0] - lh[0], rh[1] - lh[1]); m = math.hypot(*v); u = (v[0] / m, v[1] / m)
    p0, p1 = (lh[0] - u[0] * 140, lh[1] - u[1] * 140), (rh[0] + u[0] * 140, rh[1] + u[1] * 140)
    mid = lerp(lh, rh, 0.5)
    polyline(L, [(mid[0] - 280, mid[1]), (mid[0] + 280, mid[1])], WHITE, 3, ph(t, 0.4, 0.5), 0.8, dash=(14, 9))
    polyline(L, [p0, p1], YEL, 6, ph(t, 0.7, 0.5), 1)
    marker(L, lh, YEL, 11, ph(t, 0.7, 0.3)); marker(L, rh, YEL, 11, ph(t, 0.7, 0.3))
    text(L, (mid[0], mid[1] - 60), 'ТАЗ РОВНО', 36, YEL, ph(t, 1.2, 0.4), 'mm')
    stance = 0 if P.p('ank', 0)[1] > P.p('ank', 1)[1] else 1
    sh_ = P.p('hip', stance)
    callout(L, sh_, (sh_[0] + (-260 if sh_[0] < mid[0] else 260), sh_[1] + 260), ['СРЕДНЯЯ ЯГОДИЧНАЯ', 'опорной ноги'], YEL, ph(t, 1.7, 0.4), 30)


def fx_foot(L, t, P, d):
    steps(L, t, 5, '5. СТОПА', ['Миофасциальный релиз', 'подошвенного апоневроза'])
    side = 0 if P.p('toe', 0)[0] < P.p('toe', 1)[0] else 1
    an, to = P.p('ank', side), P.p('toe', side)
    polyline(L, [an, to], YEL, 7, ph(t, 0.5, 0.5), 1)
    marker(L, lerp(an, to, 0.5), YEL, 12, ph(t, 0.5, 0.3))
    c = lerp(an, to, 0.5)
    callout(L, c, (c[0] + 260, c[1] - 260), ['ПОДОШВЕННЫЙ', 'АПОНЕВРОЗ'], YEL, ph(t, 0.9, 0.4), 32)


def fx_rf(L, t, P, d):
    steps(L, t, 6, '6. РАСТЯЖКА', ['Прямая мышца бедра', 'Ягодичные напряжены, таз в ретроверсии'])
    h, k, s = P.p('hip'), P.p('knee'), P.p('sh')
    polyline(L, [h, k], YEL, 20, ph(t, 0.4, 0.5), 0.5)
    marker(L, h, YEL, 11, ph(t, 0.4, 0.3)); marker(L, k, YEL, 11, ph(t, 0.4, 0.3))
    m = lerp(h, k, 0.5)
    callout(L, m, (m[0] + 60, m[1] - 380), ['ПРЯМАЯ МЫШЦА БЕДРА', 'сгибает бедро и разгибает голень'], YEL, ph(t, 0.9, 0.4), 30)


def fx_psoas(L, t, P, d):
    steps(L, t, 6, '6. РАСТЯЖКА', ['Подвздошно-поясничная мышца', 'Таз в ретроверсии'])
    def kang(sd):
        h, k, a = P.p('hip', sd), P.p('knee', sd), P.p('ank', sd)
        v1, v2 = (h[0] - k[0], h[1] - k[1]), (a[0] - k[0], a[1] - k[1])
        return math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2) + 1e-6)))))
    back = 0 if kang(0) > kang(1) else 1
    hb, kb = P.p('hip', back), P.p('knee', back)
    mh = lerp(P.p('hip', 0), P.p('hip', 1), 0.5); ms = lerp(P.p('sh', 0), P.p('sh', 1), 0.5)
    lp = lerp(mh, ms, 0.3)
    lt = (hb[0] + (mh[0] - hb[0]) * 0.3, hb[1] + 0.14 * math.dist(hb, kb))
    path = PV.catmull([lp, lerp(mh, hb, 0.5), lt], 10, False)
    polyline(L, path, RED, 16, ph(t, 0.4, 0.6), 0.7)
    marker(L, lp, YEL, 10, ph(t, 0.4, 0.3)); marker(L, lt, YEL, 10, ph(t, 0.9, 0.3))
    callout(L, lerp(lp, lt, 0.5), (lp[0] + (300 if lp[0] < 540 else -300), lp[1] - 260),
            ['ПОДВЗДОШНО-ПОЯСНИЧНАЯ', 'от позвонков Th12-L5', 'к малому вертелу бедра'], RED, ph(t, 0.9, 0.4), 30)


def fx_bad_wide(L, t, P, d):
    steps(L, t, 7, '7. ПРЕСС', ['Только в самом конце протокола'])


def fx_bad(L, t, P, d):
    steps(L, t, 7, '7. ПРЕСС: ТАК НЕ ДАЮ', ['Обычные скручивания, руки за головой'], RED)
    e, s, f = P.p('ear'), P.p('sh'), P.fwd()
    ln = math.dist(e, s)
    polyline(L, [s, e], RED, 6, ph(t, 0.4, 0.4), 1)
    up = -1
    a0, a1 = (200, 300) if f > 0 else (340, 240)
    arc_arrow(L, e, 0.9 * ln, a0, a1, RED, 6, ph(t, 0.8, 0.7), ph(t, 0.8, 0.2))
    cross(L, (e[0], e[1] - 1.5 * ln), 34, RED, ph(t, 1.6, 0.2))
    callout(L, lerp(e, s, 0.5), (lerp(e, s, 0.5)[0] + (-260 if e[0] > 540 else 260), lerp(e, s, 0.5)[1] + 330),
            ['РУКИ ТЯНУТ ШЕЙНЫЙ ОТДЕЛ', 'В СГИБАНИЕ', 'а он и так растянут в части сегментов'], RED, ph(t, 1.9, 0.4), 30)


def fx_good(L, t, P, d):
    steps(L, t, 7, '7. ПРЕСС: ТАК ДАЮ', ['Скручивания с блином на прямых руках', 'Поднимаю голову и часть грудного отдела'], GREEN)
    e, s, h = P.p('ear'), P.p('sh'), P.p('hip')
    v = (s[0] - e[0], s[1] - e[1])
    polyline(L, [(e[0] - v[0] * 0.3, e[1] - v[1] * 0.3), e, s], GREEN, 6, ph(t, 0.5, 0.5), 1)
    marker(L, e, GREEN, 11, ph(t, 0.5, 0.3)); marker(L, s, GREEN, 11, ph(t, 0.5, 0.3))
    check(L, (e[0], e[1] - 160), 34, GREEN, 1, 9, ph(t, 1.0, 0.4))
    callout(L, lerp(e, s, 0.5), (lerp(e, s, 0.5)[0] + 250, lerp(e, s, 0.5)[1] - 330), ['ШЕЙНЫЙ ОТДЕЛ', 'НЕЙТРАЛЕН'], GREEN, ph(t, 1.2, 0.4), 32)
    ab = lerp(s, h, 0.55)
    callout(L, ab, (ab[0] + 220, ab[1] + 150), ['ПРЯМАЯ МЫШЦА ЖИВОТА', 'сгибание грудного отдела'], YEL, ph(t, 2.2, 0.4), 30)


def fx_cta(L, t, P, d):
    h, s, f = P.p('hip'), P.p('sh'), P.fwd()
    ln = math.dist(h, s)
    p = (h[0] - f * 0.17 * ln, h[1] - 0.22 * ln)
    chip(L, ['ТЕСТ У СТЕНЫ', '30 СЕКУНД'], ph(t, 0.1, 0.3))
    callout(L, p, (p[0] - 300, p[1] - 480), ['ЛАДОНЬ МЕЖДУ', 'ПОЯСНИЦЕЙ И СТЕНОЙ'], YEL, ph(t, 0.4, 0.4), 32)
    a = ph(t, 1.6, 0.3)
    if a > 0:
        L.d.rounded_rectangle([S((290, 1300)), S((790, 1440))], radius=20 * SS, fill=rgba(YEL, a))
        text(L, (540, 1370), 'ОСАНКА', 92, INK, a, 'mm', 0)
        text(L, (540, 1480), 'напиши в комментариях', 34, WHITE, a, 'mm')


# ---------- монтаж ----------
# (тип, источник, начало, конец или длина, кроп, графика, текст голоса)
SHOTS = [
    ('clip', '9673', 0.3, 4.9, Z9673, fx_plumb, 'Живот выпирает, хотя жира мало? Смотрю не на пресс, а на таз.'),
    ('clip', '9675', 0.0, 6.9, '', fx_pelvis, 'Линия от передней верхней подвздошной ости к задней показывает наклон таза.'),
    ('diagram', None, 0, 6.2, '', fx_tilt, 'Чем ниже передняя ость, тем больше антеверсия: поясница уходит в гиперлордоз, живот выходит вперёд.'),
    ('diagram', None, 0, 7.6, '', fx_janda, 'По модели Янды это нижний перекрёстный синдром: сгибатели бедра и разгибатели поясницы в гипертонусе, ягодичные и мышцы живота включаются слабо.'),
    ('clip', '9671', 0.0, 4.6, '', fx_card1, 'Качать пресс не поможет. В 1996 году у мужчин сила пресса с углом таза не была связана.'),
    ('clip', '9672', 0.0, 3.5, '', fx_card2, 'В 1997-м пресс стал сильнее, а угол таза не изменился.'),
    ('clip', '9678', 0.0, 6.8, '', fx_85, 'И это не болезнь: лёгкая антеверсия есть у 85% здоровых мужчин. На сушке, когда уходит подкожный жир, её просто становится видно.'),
    ('clip', '9677', 0.0, 3.0, '', fx_intro, 'Поэтому мой протокол идёт сверху вниз.'),
    ('clip', '9680', 0.5, 6.0, '', fx_neck, 'Первое: шея. Сгибание шейного отдела из нейтрального положения.'),
    ('clip', '9679', 13.0, 18.0, '', fx_scap, 'Второе: лопатки. Ретракция и депрессия.'),
    ('clip', '9681', 7.5, 13.7, '', fx_ham, 'Через 2 недели поясница и задняя поверхность бедра. Носок в подошвенном сгибании, чтобы икроножная не помогала.'),
    ('clip', '9689', 12.5, 16.0, '', fx_glmed, 'Средняя ягодичная держит таз ровно во фронтальной плоскости.'),
    ('clip', '9687', 2.5, 5.0, '', fx_foot, 'Стопа: релиз подошвенного апоневроза.'),
    ('clip', '9690', 13.5, 16.5, '', fx_rf, 'Растяжка прямой мышцы бедра'),
    ('clip', '9688', 4.0, 6.5, '', fx_psoas, 'и подвздошно-поясничной. Таз в ретроверсии.'),
    ('clip', '9691', 3.0, 6.0, '', fx_bad_wide, 'И только в конце пресс.'),
    ('clip', '9691', 11.0, 16.8, '', fx_bad, 'Обычные скручивания не даю: руки тянут шейный отдел в сгибание, а он и так растянут в части сегментов.'),
    ('clip', '9667', 12.0, 16.5, '', fx_good, 'Поэтому скручивания с блином: шея нейтральна, работает прямая мышца живота.'),
    ('clip', '9674', 0.0, 5.0, '', fx_cta, 'Проверить таз за 30 секунд у стены: пиши в комментариях ОСАНКА.'),
]


def chunks(vo):
    words = vo.split()
    out, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(' '.join(cur)) > 46 or w_.endswith(('.', '?', ':')) and len(' '.join(cur)) > 18:
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    return out


def render(i):
    kind, src, s, e, pre, fx, vo = SHOTS[i]
    out = f'{OUT}/s{i:02d}.mp4'
    if os.path.exists(out) and '--force' not in sys.argv and str(i) not in sys.argv:
        return out
    dur = e - s
    n = int(round(dur * 30))
    P = None
    if kind == 'clip':
        P = Pose(POSE.run(src, s, e, pre))
        dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/IMG_{src} (1).MOV', '-vf',
                                f'{pre}scale={W}:{H}:flags=lanczos,fps=30,{GRADE}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                               stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    subs = chunks(vo)
    wts = [len(c.split()) for c in subs]
    bg_diag = Image.new('RGBA', (W, H), PV.BG + (255,))
    k = 0
    while True:
        if kind == 'clip':
            buf = dec.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            base = Image.frombuffer('RGB', (W, H), buf).convert('RGBA')
            P.i = k
        else:
            if k >= n:
                break
            base = bg_diag.copy()
        t = k / 30.0
        L = Layer()
        fx(L, t, P, dur)
        # субтитры: будущий голос
        acc, tot = 0.0, sum(wts)
        for c, w_ in zip(subs, wts):
            a0, a1 = dur * acc / tot, dur * (acc + w_) / tot
            if a0 <= t < a1:
                subtitle(L, c, 1.0)
            acc += w_
        draft_tag(L)
        base.alpha_composite(L.out())
        enc.stdin.write(base.convert('RGB').tobytes())
        k += 1
    enc.stdin.close(); enc.wait()
    return out


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = [int(a) for a in sys.argv[1:] if a.isdigit()]
    idx = only or list(range(len(SHOTS)))
    with Pool(4) as pool:
        parts = pool.map(render, idx)
    if only:
        print('rendered', parts); sys.exit(0)
    parts = [f'{OUT}/s{i:02d}.mp4' for i in range(len(SHOTS))]
    open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    final = f'{B}/posture_draft_v2.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-f', 'lavfi', '-i',
                    'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-preset', 'medium',
                    '-crf', '20', '-maxrate', '10M', '-bufsize', '20M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac',
                    '-b:a', '128k', final], check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', final], capture_output=True, text=True).stdout
    print('final', final, d)
