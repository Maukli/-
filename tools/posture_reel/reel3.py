# Рилс "Живот выпирает, хотя жира мало", версия 3 (12.11).
# По образцу из папки "Качество, которое хочу видеть": кинематографичный тёмный цвет, человек выделен светом,
# огромное слово позади человека, белый силуэт-вспышка на переходах, значок Instagram с ником.
# Линии только классические и только там, где их объясняем: отвес, линия таза, лордоз, силовая пара таза
# и крест Янды на схеме, уровень таза, ось шеи на скручиваниях. Где мышца должна работать, она "загорается" по силуэту.
import os, sys, math, subprocess
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
import pelvis as PV
import pose as POSE
from look import GRADE3, finish_fast, big_word, behind, glow_map, add_glow

OUT = f'{B}/seg3'
Z9673 = 'crop=iw/1.6:ih/1.6:iw*0.16:ih*0.26,'
MODEL = f'{B}/../models/pose_heavy.task'
WARM, HOT, COOL = (255, 150, 60), (255, 90, 40), (90, 180, 255)
IDX = {'ear': (7, 8), 'sh': (11, 12), 'el': (13, 14), 'wr': (15, 16), 'hip': (23, 24), 'knee': (25, 26), 'ank': (27, 28),
       'heel': (29, 30), 'toe': (31, 32)}


class Pose:
    def __init__(self, raw):
        arr, last = [], None
        for f in raw:
            last = f if f else last
            arr.append(last)
        a = np.array(arr, dtype=float)
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
        return -1 if self.p(0)[0] < self.p('ear')[0] else 1


def pulse(t, f=1.3):
    return (0.75 + 0.25 * math.sin(2 * math.pi * f * t)) * ph(t, 0.2, 0.5)


def tag(L, t, num, name, color=YEL):
    """Номер шага протокола и название, сверху слева. Под ним полоска 7 сегментов."""
    a = ph(t, 0.0, 0.3)
    text(L, (60, 170), num, 64, color, a, 'la', 4)
    text(L, (60 + text_w(num, 64) + 18, 196), name, 40, WHITE, a, 'la', 4)
    for i in range(7):
        c = color if i + 1 == int(num) else (WHITE if i + 1 < int(num) else (120, 130, 140))
        L.d.rectangle([S((60 + i * 58, 270)), S((60 + i * 58 + 48, 276))], fill=rgba(c, a * (1 if i + 1 <= int(num) else 0.6)))


def label(L, xy, lines, t, t0, col=YEL, anchor='la', size=34):
    a = ph(t, t0, 0.35)
    for i, s in enumerate(lines):
        text(L, (xy[0], xy[1] + i * size * 1.2), s, size if i == 0 else size * 0.78, col if i == 0 else WHITE, a, anchor, 4)


# ---------- графика по кадрам: fx(L, t, P, d, ctx) -> список эффектов для пикселей ----------
# ctx: dict, куда кладём слова позади человека и подсветку мышц

def fx_hook(L, t, P, d, ctx):
    ctx['word'] = ('АНТЕВЕРСИЯ', 430, 560, YEL, ph(t, 0.15, 0.35))


def pelvis_pts(P):
    h, s = P.p('hip'), P.p('sh')
    L_ = math.dist(h, s); f = P.fwd()
    return (h[0] + f * 0.20 * L_, h[1] - 0.20 * L_), (h[0] - f * 0.30 * L_, h[1] - 0.26 * L_), f, h, L_


def fx_tilt(L, t, P, d, ctx):
    asis, psis, f, h, ln = pelvis_pts(P)
    marker(L, asis, YEL, 12, ph(t, 0.3, 0.3)); marker(L, psis, YEL, 12, ph(t, 0.3, 0.3))
    label(L, (asis[0] + f * 30, asis[1] + 30), ['ПВПО'], t, 0.5, YEL, 'ra' if f < 0 else 'la', 32)
    label(L, (psis[0] - f * 30, psis[1] - 70), ['ЗВПО'], t, 0.5, YEL, 'la' if f < 0 else 'ra', 32)
    polyline(L, [psis, asis], YEL, 6, ph(t, 0.9, 0.5), 1)
    polyline(L, [psis, (psis[0] + f * 0.75 * ln, psis[1])], WHITE, 2.5, ph(t, 1.4, 0.4), 0.8, dash=(12, 9))
    ang = math.degrees(math.atan2(asis[1] - psis[1], asis[0] - psis[0]))
    polyline(L, arc_pts(psis, 0.5 * ln, 180 if f < 0 else 0, ang), YEL, 4, ph(t, 1.8, 0.4), 1)
    c = (h[0], h[1] - 0.1 * ln)
    a0, a1 = (130, 200) if f < 0 else (50, -20)
    arc_arrow(L, c, 0.55 * ln, a0, a1, YEL, 6, ph(t, 2.4, 0.7), ph(t, 2.4, 0.2), 26)
    label(L, (c[0] + f * 0.65 * ln, c[1] + 0.55 * ln), ['АНТЕВЕРСИЯ', 'наклон таза вперёд'], t, 2.8, YEL, 'ra' if f < 0 else 'la', 40)


def fx_lordosis(L, t, P, d, ctx):
    s, h, f = P.p('sh'), P.p('hip'), P.fwd()
    ln = math.dist(s, h)
    b = -f
    top = (s[0] + b * 0.20 * ln, s[1] + 0.35 * ln)
    apex = (lerp(s, h, 0.78)[0] + b * 0.02 * ln, lerp(s, h, 0.78)[1])
    bot = (h[0] + b * 0.30 * ln, h[1] + 0.05 * ln)
    curve = PV.catmull([top, apex, bot], 12, False)
    polyline(L, curve, RED, 7, ph(t, 0.3, 0.7), 1)
    label(L, (apex[0] + b * 60, apex[1] - 20), ['ГИПЕРЛОРДОЗ', 'поясничного отдела'], t, 0.8, RED, 'la' if b > 0 else 'ra', 36)
    belly = (lerp(s, h, 0.7)[0] + f * 0.30 * ln, lerp(s, h, 0.7)[1])
    arrow(L, belly, (belly[0] + f * 0.30 * ln, belly[1]), RED, 7, ph(t, 1.6, 0.4), ph(t, 1.6, 0.2), 28)
    label(L, (belly[0] + f * 0.05 * ln, belly[1] + 50), ['ЖИВОТ ВПЕРЁД'], t, 1.9, RED, 'ra' if f < 0 else 'la', 34)
    ctx['glow'] = [(glow_map((), [(top, bot, 0.09 * ln)], 12), HOT, 0.55 * pulse(t))]


def fx_couple(L, t, P, d, ctx):
    """Силовая пара таза и крест Янды на схеме."""
    th = 7 + 13 * ph(t, 2.2, 2.4)
    grid(L, 0.07)
    g = PV.draw_skeleton(L, th, 0.85, ph(t, 0.0, 1.0), labels=False)
    HC = PV.HC
    wheel = arc_pts((HC[0] - 5, HC[1] - 110), 300, 0, 360, 80)
    polyline(L, wheel, WHITE, 2.5, ph(t, 0.9, 0.8), 0.6, dash=(10, 10))
    text(L, (HC[0] - 5, HC[1] - 440), 'ТАЗ КАК КОЛЕСО', 38, WHITE, ph(t, 1.0, 0.4), 'mm')
    asis, psis = g['asis'], g['psis']
    isch = PV.rot((108, 128), th); pub = PV.rot((-122, 118), th)
    # вперёд: разгибатели поясницы тянут заднюю часть вверх, подвздошно-поясничная тянет переднюю вниз
    a1 = ph(t, 2.0, 0.4)
    arrow(L, (psis[0] + 40, psis[1] - 10), (psis[0] + 60, psis[1] - 230), RED, 9, a1, a1, 30)
    label(L, (psis[0] + 85, psis[1] - 260), ['РАЗГИБАТЕЛИ', 'ПОЯСНИЦЫ'], t, 2.2, RED, 'la', 34)
    a2 = ph(t, 2.8, 0.4)
    arrow(L, (asis[0] - 10, asis[1] + 30), (asis[0] - 30, asis[1] + 250), RED, 9, a2, a2, 30)
    label(L, (asis[0] - 55, asis[1] + 250), ['ПОДВЗДОШНО-', 'ПОЯСНИЧНАЯ'], t, 3.0, RED, 'ra', 34)
    arc_arrow(L, (HC[0] - 5, HC[1] - 110), 330, 205, 150, RED, 7, ph(t, 3.4, 0.8), ph(t, 3.4, 0.2), 30)
    # назад: мышцы живота тянут лобок вверх, ягодичные и задняя поверхность бедра тянут седалищный бугор вниз
    b1, b2 = ph(t, 5.2, 0.4), ph(t, 6.0, 0.4)
    arrow(L, (pub[0] - 10, pub[1] - 20), (pub[0] - 40, pub[1] - 260), BLUE, 5, b1, b1 * 0.8, 24)
    label(L, (pub[0] - 70, pub[1] - 300), ['МЫШЦЫ ЖИВОТА'], t, 5.4, BLUE, 'ra', 34)
    arrow(L, (isch[0] + 10, isch[1] + 10), (isch[0] + 40, isch[1] + 260), BLUE, 5, b2, b2 * 0.8, 24)
    label(L, (1030, isch[1] + 290), ['ЯГОДИЧНЫЕ И ЗАДНЯЯ', 'ПОВЕРХНОСТЬ БЕДРА'], t, 6.2, BLUE, 'ra', 30)
    text(L, (540, 1560), 'выключены', 34, BLUE, ph(t, 6.8, 0.4) * (1 - ph(t, 8.6, 0.3)), 'mm')
    # крест Янды
    c1, c2 = ph(t, 8.6, 0.6), ph(t, 9.2, 0.6)
    polyline(L, [(psis[0] + 60, psis[1] - 200), (asis[0] - 30, asis[1] + 230)], RED, 5, c1, 0.95, dash=(18, 10))
    polyline(L, [(pub[0] - 40, pub[1] - 240), (isch[0] + 40, isch[1] + 240)], BLUE, 5, c2, 0.95, dash=(18, 10))
    a = ph(t, 9.6, 0.4)
    if a > 0:
        text(L, (540, 330), 'НИЖНИЙ ПЕРЕКРЁСТНЫЙ', 58, YEL, a, 'mm', 4)
        text(L, (540, 400), 'СИНДРОМ ПО ЯНДЕ', 58, YEL, a, 'mm', 4)


def fx_research(L, t, P, d, ctx):
    a = ph(t, 0.3, 0.35)
    panel(L, (60, 1130, 1020, 1400), a, BLUE)
    text(L, (95, 1160), 'WALKER 1987, YOUDAS 1996, LEVINE 1997', 30, BLUE, a, stroke=0)
    text(L, (95, 1215), 'Пресс сильнее', 50, WHITE, a * ph(t, 0.8, 0.3), stroke=0)
    text(L, (95, 1285), 'Угол таза тот же', 50, YEL, a * ph(t, 1.6, 0.3), stroke=0)


def fx_85(L, t, P, d, ctx):
    n = int(round(85 * ph(t, 0.2, 1.4)))
    ctx['word'] = (f'{n}%', 560, 620, YEL, ph(t, 0.1, 0.3))
    label(L, (540, 960), ['ЗДОРОВЫХ МУЖЧИН', 'с лёгкой антеверсией'], t, 1.0, WHITE, 'ma', 40)
    a = ph(t, 2.6, 0.3)
    if a > 0:
        L.d.rounded_rectangle([S((370, 1150)), S((710, 1240))], radius=16 * SS, fill=rgba(GREEN, a))
        text(L, (540, 1195), 'НОРМА', 60, INK, a, 'mm', 0)
    text(L, (540, 1290), 'HERRINGTON, 2011', 26, (180, 190, 205), ph(t, 1.0, 0.3), 'mm', 3)


def fx_plain(L, t, P, d, ctx):
    pass


def fx_intro(L, t, P, d, ctx):
    ctx['word'] = ('СВЕРХУ', 400, 520, YEL, ph(t, 0.05, 0.3))
    ctx['word2'] = ('ВНИЗ', 400, 900, YEL, ph(t, 0.35, 0.3))


def fx_head(L, t, P, d, ctx):
    e, s = P['ear'], P['sh']
    polyline(L, [s, e], YEL, 6, ph(t, 0.3, 0.4), 1)
    polyline(L, [s, (s[0], s[1] - 1.6 * math.dist(e, s))], WHITE, 3, ph(t, 0.6, 0.4), 0.8, dash=(14, 9))
    marker(L, e, YEL, 11, ph(t, 0.3, 0.3)); marker(L, s, YEL, 11, ph(t, 0.3, 0.3))
    head = P['head']
    marker(L, head, WHITE, 14, ph(t, 1.0, 0.3))
    arrow(L, head, (head[0], head[1] + 230), WHITE, 7, ph(t, 1.2, 0.4), ph(t, 1.2, 0.2), 30)
    label(L, (head[0] - 40, head[1] + 120), ['ОКОЛО 5 КГ'], t, 1.4, WHITE, 'ra', 52)
    label(L, (s[0] + 40, s[1] - 40), ['ПЕРЕДНЕЕ ПОЛОЖЕНИЕ', 'ГОЛОВЫ'], t, 2.0, YEL, 'la', 34)


def fx_neck(L, t, P, d, ctx):
    tag(L, t, '01', 'ШЕЯ')
    e, s, f = P.p('ear'), P.p('sh'), P.fwd()
    ln = math.dist(e, s)
    nk0 = (lerp(e, s, 0.15)[0] + f * 0.22 * ln, lerp(e, s, 0.15)[1])
    nk1 = (lerp(e, s, 0.85)[0] + f * 0.22 * ln, lerp(e, s, 0.85)[1])
    ctx['glow'] = [(glow_map((), [(nk0, nk1, 0.16 * ln)], 10), HOT, 0.75 * pulse(t))]
    label(L, (60, 1180), ['ГЛУБОКИЕ СГИБАТЕЛИ ШЕИ', 'длинная мышца шеи и длинная мышца головы'], t, 0.6, YEL, 'la', 38)


def fx_scap(L, t, P, d, ctx):
    tag(L, t, '02', 'ЛОПАТКИ')
    ls, rs, lh, rh = P.p('sh', 0), P.p('sh', 1), P.p('hip', 0), P.p('hip', 1)
    ms, mh = lerp(ls, rs, 0.5), lerp(lh, rh, 0.5)
    tl = math.dist(ms, mh)
    segs = [((ms[0] - 0.10 * tl, ms[1] + 0.10 * tl), (ms[0] - 0.07 * tl, ms[1] + 0.48 * tl), 0.08 * tl),
            ((ms[0] + 0.10 * tl, ms[1] + 0.10 * tl), (ms[0] + 0.07 * tl, ms[1] + 0.48 * tl), 0.08 * tl)]
    ctx['glow'] = [(glow_map((), segs, 10), HOT, 0.55 * pulse(t))]
    for sgn in (-1, 1):
        q = (ms[0] + sgn * 0.34 * tl, ms[1] + 0.28 * tl)
        arrow(L, q, (ms[0] + sgn * 0.17 * tl, q[1]), YEL, 6, ph(t, 0.6, 0.4), ph(t, 0.6, 0.2), 24)
        arrow(L, (q[0], q[1] + 0.06 * tl), (q[0], q[1] + 0.26 * tl), YEL, 6, ph(t, 1.2, 0.4), ph(t, 1.2, 0.2), 24)
    label(L, (60, 1180), ['РЕТРАКЦИЯ И ДЕПРЕССИЯ', 'ромбовидные, средняя и нижняя части трапециевидной'], t, 0.9, YEL, 'la', 38)


def fx_ham(L, t, P, d, ctx):
    tag(L, t, '03', 'ЗАДНЯЯ ПОВЕРХНОСТЬ БЕДРА')
    h, k = P.p('hip'), P.p('knee')
    ln = math.dist(h, k)
    ctx['glow'] = [(glow_map((), [(lerp(h, k, 0.12), lerp(h, k, 0.88), 0.18 * ln)], 10), HOT, 0.8 * pulse(t, 1.0))]
    label(L, (60, 1180), ['ТЯНЕТ ТАЗ В РЕТРОВЕРСИЮ', 'от седалищного бугра к голени'], t, 0.8, YEL, 'la', 38)
    label(L, (60, 1320), ['НОСОК ВЫТЯНУТ', 'икроножная не помогает'], t, 3.2, WHITE, 'la', 34)


def fx_glmed(L, t, P, d, ctx):
    tag(L, t, '04', 'СРЕДНЯЯ ЯГОДИЧНАЯ')
    lh, rh = P.p('hip', 0), P.p('hip', 1)
    v = (rh[0] - lh[0], rh[1] - lh[1]); m = math.hypot(*v); u = (v[0] / m, v[1] / m)
    mid = lerp(lh, rh, 0.5)
    polyline(L, [(mid[0] - 300, mid[1]), (mid[0] + 300, mid[1])], WHITE, 3, ph(t, 0.3, 0.4), 0.8, dash=(14, 9))
    polyline(L, [(lh[0] - u[0] * 150, lh[1] - u[1] * 150), (rh[0] + u[0] * 150, rh[1] + u[1] * 150)], YEL, 6, ph(t, 0.5, 0.4), 1)
    stance = 0 if P.p('ank', 0)[1] > P.p('ank', 1)[1] else 1
    hp = P.p('hip', stance); out = -1 if hp[0] < mid[0] else 1
    c = (hp[0] + out * 0.25 * m, hp[1] - 0.15 * m)
    ctx['glow'] = [(glow_map([(c[0], c[1], 0.30 * m, 0.38 * m)], (), 10), HOT, 0.85 * pulse(t))]
    label(L, (mid[0], mid[1] - 90), ['ТАЗ РОВНО'], t, 0.9, YEL, 'ma', 40)
    label(L, (60, 1240), ['ФРОНТАЛЬНАЯ ПЛОСКОСТЬ', 'проба Тренделенбурга отрицательная'], t, 1.4, WHITE, 'la', 34)


def fx_foot(L, t, P, d, ctx):
    tag(L, t, '05', 'СТОПА')
    side = 0 if P.p('toe', 0)[0] < P.p('toe', 1)[0] else 1
    an, to = P.p('ank', side), P.p('toe', side)
    ln = math.dist(an, to)
    ctx['glow'] = [(glow_map((), [(an, to, 0.5 * ln)], 6), HOT, 0.85 * pulse(t, 1.6))]
    label(L, (60, 1180), ['ПОДОШВЕННЫЙ АПОНЕВРОЗ', 'миофасциальный релиз'], t, 0.4, YEL, 'la', 38)
    label(L, (60, 1310), ['GRIEVE, 2015: наклон вперёд', 'лучше сразу после раскатки'], t, 1.1, WHITE, 'la', 30)


def fx_rf(L, t, P, d, ctx):
    tag(L, t, '06', 'РАСТЯЖКА')
    h, k, f = P.p('hip'), P.p('knee'), P.fwd()
    ln = math.dist(h, k)
    g1 = glow_map((), [(lerp(h, k, 0.1), lerp(h, k, 0.9), 0.17 * ln)], 10)
    g2 = glow_map([(h[0] - f * 0.15 * ln, h[1] + 0.05 * ln, 0.25 * ln, 0.22 * ln)], (), 10)
    ctx['glow'] = [(g1, COOL, 0.7), (g2, HOT, 0.75 * pulse(t))]
    label(L, (60, 1160), ['ПРЯМАЯ МЫШЦА БЕДРА', 'растяжение'], t, 0.4, COOL, 'la', 38)
    label(L, (60, 1290), ['ЯГОДИЧНЫЕ', 'напряжены'], t, 1.0, (255, 170, 90), 'la', 38)


def fx_psoas(L, t, P, d, ctx):
    tag(L, t, '06', 'РАСТЯЖКА')
    def kang(sd):
        h, k, a = P.p('hip', sd), P.p('knee', sd), P.p('ank', sd)
        v1, v2 = (h[0] - k[0], h[1] - k[1]), (a[0] - k[0], a[1] - k[1])
        return math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2) + 1e-6)))))
    back = 0 if kang(0) > kang(1) else 1
    hb, kb = P.p('hip', back), P.p('knee', back)
    mh = lerp(P.p('hip', 0), P.p('hip', 1), 0.5); ms = lerp(P.p('sh', 0), P.p('sh', 1), 0.5)
    lp = lerp(mh, ms, 0.3)
    lt = (hb[0] + (mh[0] - hb[0]) * 0.3, hb[1] + 0.14 * math.dist(hb, kb))
    r = 0.07 * math.dist(mh, ms)
    ctx['glow'] = [(glow_map((), [(lp, lerp(mh, hb, 0.5), r), (lerp(mh, hb, 0.5), lt, r)], 8), COOL, 0.8)]
    label(L, (60, 1160), ['ПОДВЗДОШНО-ПОЯСНИЧНАЯ', 'от позвонков Th12-L5 к малому вертелу'], t, 0.3, COOL, 'la', 38)
    label(L, (60, 1290), ['ТАЗ В РЕТРОВЕРСИИ'], t, 1.0, YEL, 'la', 38)


def fx_press_tag(L, t, P, d, ctx):
    tag(L, t, '07', 'ПРЕСС')


def fx_bad(L, t, P, d, ctx):
    tag(L, t, '07', 'ПРЕСС', RED)
    e, s, f = P.p('ear'), P.p('sh'), P.fwd()
    ln = math.dist(e, s)
    polyline(L, [s, e, (e[0] + (e[0] - s[0]) * 0.4, e[1] + (e[1] - s[1]) * 0.4)], RED, 7, ph(t, 0.3, 0.4), 1)
    cross(L, (e[0], e[1] - 1.6 * ln), 36, RED, ph(t, 0.9, 0.2))
    label(L, (60, 1180), ['ТАК НЕ ДАЮ', 'руки тянут шейный отдел в сгибание'], t, 0.6, RED, 'la', 42)


def fx_good(L, t, P, d, ctx):
    tag(L, t, '07', 'ПРЕСС', GREEN)
    e, s, h = P.p('ear'), P.p('sh'), P.p('hip')
    polyline(L, [(e[0] + (e[0] - s[0]) * 0.35, e[1] + (e[1] - s[1]) * 0.35), e, s], GREEN, 7, ph(t, 0.3, 0.4), 1)
    check(L, (e[0], e[1] - 170), 36, GREEN, 1, 9, ph(t, 0.8, 0.4))
    ln = math.dist(s, h)
    ctx['glow'] = [(glow_map((), [(lerp(s, h, 0.25), lerp(s, h, 0.9), 0.2 * ln)], 10), HOT, 0.8 * pulse(t))]
    label(L, (60, 1180), ['ШЕЙНЫЙ ОТДЕЛ НЕЙТРАЛЕН', 'руки заняты блином'], t, 0.5, GREEN, 'la', 42)
    label(L, (60, 1310), ['ПРЯМАЯ МЫШЦА ЖИВОТА'], t, 1.4, (255, 170, 90), 'la', 36)


def fx_cta(L, t, P, d, ctx):
    ctx['word'] = ('ОСАНКА', 470, 560, YEL, ph(t, 0.1, 0.35))
    label(L, (540, 1150), ['ТЕСТ У СТЕНЫ, 30 СЕКУНД'], t, 0.8, WHITE, 'ma', 44)
    label(L, (540, 1230), ['напиши в комментариях'], t, 1.2, WHITE, 'ma', 36)


def fx_end(L, t, P, d, ctx):
    pass


# (тип, источник, начало, конец/длина, кроп, графика, голос, вспышка-силуэт на входе)
SHOTS = [
    ('clip', '9673', 0.3, 4.3, Z9673, fx_hook, 'Жира мало, а живот выпирает? Это не пресс. Это таз.', False),
    ('clip', '9675', 0.0, 5.0, '', fx_tilt, 'Передняя верхняя подвздошная ость уходит вниз, и таз наклоняется вперёд. Это антеверсия.', True),
    ('clip', '9673', 7.0, 10.6, '', fx_lordosis, 'Поясница проваливается в гиперлордоз и выталкивает живот вперёд.', False),
    ('diagram', None, 0, 12.5, '', fx_couple, 'Таз работает как колесо. Вперёд его крутят подвздошно-поясничная мышца и разгибатели поясницы. Назад мышцы живота, ягодичные и задняя поверхность бедра. Первые в гипертонусе, вторые выключены: это нижний перекрёстный синдром по Янде.', False),
    ('clip', '9671', 0.0, 4.6, '', fx_research, 'Качать пресс бесполезно: в исследованиях пресс становился сильнее, а угол таза не менялся.', True),
    ('clip', '9678', 0.0, 4.6, '', fx_85, 'А лёгкая антеверсия есть у 85% здоровых мужчин. Это норма.', False),
    ('clip', '9672', 0.0, 3.0, '', fx_plain, 'Просто на сушке её становится видно.', False),
    ('clip', '9677', 0.0, 3.1, '', fx_intro, 'Поэтому я работаю сверху вниз.', True),
    ('still', 'IMG_9706', 0, 4.0, '', fx_head, 'Голова весит около 5 килограммов. Уходит вперёд, и тело ищет баланс ниже по цепи.', False),
    ('clip', '9680', 0.5, 5.0, '', fx_neck, 'Шея: сгибание шейного отдела, включаю глубокие сгибатели.', True),
    ('clip', '9679', 13.0, 17.5, '', fx_scap, 'Лопатки: ретракция и депрессия, ромбовидные и нижняя часть трапециевидной.', False),
    ('clip', '9681', 7.5, 13.7, '', fx_ham, 'Через 2 недели задняя поверхность бедра: она крепится к седалищному бугру и тянет таз назад. Носок вытянут, чтобы икроножная не помогала.', False),
    ('clip', '9689', 12.5, 16.0, '', fx_glmed, 'Средняя ягодичная держит таз ровно во фронтальной плоскости.', False),
    ('clip', '9687', 2.5, 5.0, '', fx_foot, 'Стопа: после раскатки подошвенного апоневроза наклон вперёд сразу лучше.', False),
    ('clip', '9690', 13.5, 16.5, '', fx_rf, 'Растягиваю то, что крутит таз вперёд: прямую мышцу бедра', False),
    ('clip', '9688', 4.0, 6.5, '', fx_psoas, 'и подвздошно-поясничную. Ягодицы напряжены, таз в ретроверсии.', False),
    ('clip', '9691', 3.0, 5.0, '', fx_press_tag, 'И только в конце пресс.', True),
    ('clip', '9691', 11.5, 15.0, '', fx_bad, 'Обычные скручивания не даю: руки тянут шейный отдел в сгибание.', False),
    ('clip', '9667', 12.0, 16.0, '', fx_good, 'Блин на прямых руках: руки заняты, шея нейтральна, работает прямая мышца живота.', False),
    ('clip', '9674', 0.0, 4.5, '', fx_cta, 'Проверить свой таз за 30 секунд: пиши ОСАНКА.', True),
    ('end', None, 0, 1.8, '', fx_end, '', False),
]


def chunks(vo):
    words, out, cur = vo.split(), [], []
    for w_ in words:
        cur.append(w_)
        if len(' '.join(cur)) > 40 or (w_.endswith(('.', '?', ':')) and len(' '.join(cur)) > 16):
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    return out


def still_frame(name):
    im = Image.open(f'{B}/photos/{name}.jpg'); w, h = im.size
    cw = int(h * 9 / 16)
    return im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((W, H), Image.LANCZOS)


def render(i):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    kind, src, s, e, pre, fx, vo, flash = SHOTS[i]
    out = f'{OUT}/s{i:02d}.mp4'
    if os.path.exists(out) and '--force' not in sys.argv and str(i) not in sys.argv:
        return out
    dur = e - s
    n = int(round(dur * 30))
    P, lm, still = None, None, None
    mode = vision.RunningMode.VIDEO if kind == 'clip' else vision.RunningMode.IMAGE
    if kind in ('clip', 'still'):
        lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL), running_mode=mode, num_poses=1, output_segmentation_masks=True))
    if kind == 'clip':
        P = Pose(POSE.run(src, s, e, pre))
        dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/IMG_{src} (1).MOV', '-vf',
                                f'{pre}scale={W}:{H}:flags=lanczos,fps=30,{GRADE3}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                               stdout=subprocess.PIPE)
    if kind == 'still':
        im = still_frame(src)
        g = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-i', '-', '-vf', GRADE3,
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], input=im.tobytes(), capture_output=True).stdout
        still = np.frombuffer(g, np.uint8).reshape(H, W, 3)
        r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(Image.fromarray(still).resize((540, 960))))))
        L_ = r.pose_landmarks[0]
        sd = 7 if L_[7].visibility >= L_[8].visibility else 8
        sh = 11 if sd == 7 else 12
        ear = (L_[sd].x * W, L_[sd].y * H); shp = (L_[sh].x * W, L_[sh].y * H)
        face = 1 if L_[0].x * W > ear[0] else -1
        dl = math.dist(ear, shp)
        P = {'ear': ear, 'sh': shp, 'head': (ear[0] + face * 0.22 * dl, ear[1] - 0.18 * dl)}
        smask = r.segmentation_masks[0].numpy_view().squeeze()
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    subs = chunks(vo)
    wts = [len(c.split()) for c in subs]
    words = {}
    mprev = None
    k = 0
    while True:
        t = k / 30.0
        if kind == 'clip':
            buf = dec.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            arr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(Image.fromarray(arr).resize((540, 960))))), int(k * 1000 / 30))
            msk = r.segmentation_masks[0].numpy_view().squeeze() if r.segmentation_masks else np.zeros((960, 540), np.float32)
            P.i = k
        elif kind == 'still':
            if k >= n:
                break
            z = 1 + 0.06 * t / dur
            im2 = Image.fromarray(still).resize((int(W * z), int(H * z)), Image.BILINEAR)
            ox, oy = (im2.width - W) // 2, (im2.height - H) // 2
            arr = np.asarray(im2.crop((ox, oy, ox + W, oy + H)))
            mm = Image.fromarray((smask * 255).astype(np.uint8)).resize((int(W * z), int(H * z)), Image.BILINEAR).crop((ox, oy, ox + W, oy + H))
            msk = np.asarray(mm.resize((540, 960)), dtype=np.float32) / 255.0
            Pz = {key: ((v[0] - W / 2) * z + W / 2, (v[1] - H / 2) * z + H / 2) for key, v in P.items()}
        else:
            if k >= n:
                break
            arr = None; msk = None
        if msk is not None:
            msk = msk.astype(np.float32)
            mprev = msk if mprev is None else 0.55 * msk + 0.45 * mprev
            mfull = np.asarray(Image.fromarray((np.clip(mprev, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
                               .filter(ImageFilter.GaussianBlur(2)), dtype=np.float32) / 255.0
        L = Layer(); ctx = {}
        fx(L, t, Pz if kind == 'still' else P, dur, ctx)
        if kind in ('clip', 'still'):
            fl = (1 - ph(t, 0.0, 0.35)) if flash else 0.0
            o = finish_fast(arr.astype(np.float32), mfull, fl)
            for key in ('word', 'word2'):
                if key in ctx:
                    wd, size, y, col, a = ctx[key]
                    kk = (wd, size, y)
                    if kk not in words:
                        words[kk] = big_word(wd, size, y=y)
                    o = behind(o, words[kk], mfull, col, a)
            for gmap, col, st in ctx.get('glow', []):
                o = add_glow(o, gmap, mfull, col, st)
            base = Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).convert('RGBA')
        elif kind == 'diagram':
            base = Image.new('RGBA', (W, H), (9, 15, 22, 255))
        else:
            base = Image.new('RGBA', (W, H), (0, 0, 0, 255))
            wm = Image.open(f'{B}/../challenge/wm_mi.png').convert('RGBA')
            wm = wm.resize((int(wm.width * 1.8), int(wm.height * 1.8)), Image.LANCZOS)
            a = ph(t, 0.1, 0.4)
            wm.putalpha(Image.eval(wm.getchannel('A'), lambda v: int(v * a)))
            base.alpha_composite(wm, ((W - wm.width) // 2, (H - wm.height) // 2))
        acc, tot = 0.0, sum(wts) or 1
        for c, w_ in zip(subs, wts):
            a0, a1 = dur * acc / tot, dur * (acc + w_) / tot
            if a0 <= t < a1:
                subtitle(L, c, 1.0)
            acc += w_
        if kind != 'end':
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
    order = sorted(idx, key=lambda i: -(SHOTS[i][3] - SHOTS[i][2]))
    with Pool(4) as pool:
        pool.map(render, order)
    if only:
        sys.exit(0)
    parts = [f'{OUT}/s{i:02d}.mp4' for i in range(len(SHOTS))]
    open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    # значок Instagram с ником: всё время в кадре (кроме схемы и концовки), место меняется каждые 6 с
    durs = [SHOTS[i][3] - SHOTS[i][2] for i in range(len(SHOTS))]
    t0, en = 0.0, []
    for i, dd in enumerate(durs):
        if SHOTS[i][0] in ('clip', 'still'):
            en.append(f'gte(t,{t0:.2f})*lt(t,{t0 + dd:.2f})')
        t0 += dd
    pos = [('W-w-50', '1440'), ('50', '1440')]
    px = f"if(eq(mod(floor(t/6),2),0),{pos[0][0]},{pos[1][0]})"
    final = f'{B}/posture_draft_v3.mp4'
    fc = (f"[1:v]format=rgba,scale=iw*0.8:-1,colorchannelmixer=aa=0.85[wm];"
          f"[0:v][wm]overlay=x='{px}':y=1440:enable='{'+'.join(en)}':shortest=1:format=auto,format=yuv420p[v]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-loop', '1', '-i', f'{B}/../challenge/wm_mi.png',
                    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-shortest',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', final], check=True)
    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', final], capture_output=True, text=True).stdout
    print('final', final, d)
