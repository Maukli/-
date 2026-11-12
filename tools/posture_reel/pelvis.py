# Схема-чертёж: тазовая кость, крестец, поясничный отдел и бедренная кость, вид сбоку (перед слева).
# theta: наклон таза в градусах (7 около нейтрального, 20 выраженная антеверсия).
import math
from gfx import *

HC = (600, 1180)  # центр вертлужной впадины на схеме
BG = (11, 23, 38)
BONE = (225, 236, 250)


def rot(p, th):
    a = math.radians(-th)  # передний наклон: передняя ость уходит вниз и вперёд
    x, y = p
    return (HC[0] + x * math.cos(a) - y * math.sin(a), HC[1] + x * math.sin(a) + y * math.cos(a))


def catmull(pts, n=10, closed=True):
    P = pts + pts[:3] if closed else [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    if not closed:
        out.append(pts[-1])
    return out


# Тазовая кость сбоку: подвздошный гребень, передняя верхняя ость, нижняя ость, лобок, седалищный бугор, большая седалищная вырезка, задняя верхняя ость
ILIUM = [(-175, -130), (-120, -235), (-20, -290), (90, -268), (150, -175), (152, -120), (112, -60), (80, -5), (96, 40), (108, 128),
         (62, 178), (-40, 150), (-122, 118), (-118, 62), (-92, 30), (-150, -38), (-150, -88)]
ASIS0, PSIS0 = (-175, -130), (152, -150)
SACRUM = [(30, -300), (102, -358), (160, -250), (168, -120), (140, 0), (95, -60), (55, -180)]
OBTURATOR = (-42, 92, 44, 30)


def lumbar_chain(th):
    """Пять позвонков от верхней площадки S1. Чем больше наклон таза, тем сильнее лордоз."""
    s1f, s1b = rot((30, -300), th), rot((102, -358), th)
    base = lerp(s1f, s1b, 0.5)
    ex, ey = s1b[0] - s1f[0], s1b[1] - s1f[1]
    phi0 = math.degrees(math.atan2(-ex, ey))  # нормаль к площадке S1, от вертикали, + вперёд
    nx, ny = -ey, ex
    phi0 = math.degrees(math.atan2(-nx if nx < 0 else nx, -ny if ny < 0 else ny))
    phi0 = 40 + (th - 7)  # уклон крестца растёт вместе с наклоном таза
    phi_end = -24 - 0.6 * (th - 7)
    verts, p, phi = [], base, phi0
    step = (phi_end - phi0) / 5.0
    for i in range(5):
        phi_mid = phi + step * 0.5
        dx, dy = -math.sin(math.radians(phi_mid)), -math.cos(math.radians(phi_mid))
        c = (p[0] + dx * 40, p[1] + dy * 40)
        verts.append((c, phi_mid))
        p = (p[0] + dx * 92, p[1] + dy * 92)
        phi += step
    return base, verts, p


def draw_vertebra(L, c, phi, a, col=BONE, label=None):
    dx, dy = -math.sin(math.radians(phi)), -math.cos(math.radians(phi))  # вверх по позвоночнику
    nx, ny = -dy, dx  # перпендикуляр
    if nx > 0:
        nx, ny = -nx, -ny  # вперёд (влево)
    hw, hh = 52, 33
    pts = [(c[0] + nx * hw + dx * hh, c[1] + ny * hw + dy * hh), (c[0] + nx * hw - dx * hh, c[1] + ny * hw - dy * hh),
           (c[0] - nx * hw - dx * hh, c[1] - ny * hw - dy * hh), (c[0] - nx * hw + dx * hh, c[1] - ny * hw + dy * hh)]
    L.d.polygon([S(q) for q in pts], outline=rgba(col, a), width=int(4 * SS))
    back = (c[0] - nx * hw, c[1] - ny * hw)
    tip = (back[0] - nx * 70 - dx * 30, back[1] - ny * 70 - dy * 30)
    L.d.line([S(back), S(tip)], fill=rgba(col, a), width=int(6 * SS))
    if label:
        text(L, (c[0] + nx * (hw + 16), c[1] + ny * (hw + 16)), label, 24, col, a * 0.85, 'rm', 0)
    return pts


def geometry(th):
    g = {'ilium': [rot(p, th) for p in ILIUM], 'sacrum': [rot(p, th) for p in SACRUM],
         'asis': rot(ASIS0, th), 'psis': rot(PSIS0, th)}
    g['s1'], g['verts'], g['t12'] = lumbar_chain(th)
    return g


def draw_skeleton(L, th, a=1.0, frac=1.0, labels=True):
    g = geometry(th)
    # бедренная кость: головка в вертлужной впадине, шейка, большой вертел, диафиз
    L.d.ellipse([S((HC[0] - 38, HC[1] - 38)), S((HC[0] + 38, HC[1] + 38))], outline=rgba(BONE, a * min(1, frac * 2)), width=int(4 * SS))
    polyline(L, [(HC[0] + 20, HC[1] + 28), (HC[0] + 78, HC[1] + 70), (HC[0] + 98, HC[1] + 40), (HC[0] + 112, HC[1] + 92),
                 (HC[0] + 96, HC[1] + 650)], BONE, 4, frac, a)
    polyline(L, [(HC[0] + 12, HC[1] + 34), (HC[0] + 52, HC[1] + 130), (HC[0] + 56, HC[1] + 650)], BONE, 4, frac, a)
    il = catmull(g['ilium'], 8)
    polyline(L, il + [il[0]], BONE, 4, frac, a)
    acet = arc_pts(HC, 50, 140, 380)
    polyline(L, acet, BONE, 3, frac, a * 0.8)
    ox, oy, rx, ry = OBTURATOR
    obt = [rot((ox + rx * math.cos(u / 20 * 2 * math.pi), oy + ry * math.sin(u / 20 * 2 * math.pi)), th) for u in range(21)]
    polyline(L, obt, BONE, 3, frac, a * 0.8)
    sc = catmull(g['sacrum'], 8)
    polyline(L, sc + [sc[0]], BONE, 3, frac, a * 0.75, dash=(10, 8))  # крестец за тазовой костью: невидимый контур пунктиром
    if frac > 0.5:
        av = a * ph(frac, 0.5, 0.5)
        for i, (c, phi) in enumerate(g['verts']):
            draw_vertebra(L, c, phi, av, BONE, f'L{5 - i}' if labels else None)
        text(L, (g['t12'][0] - 70, g['t12'][1] - 10), 'Th12', 24, BONE, av * 0.7, 'rm', 0)
    return g


def body_outline(L, th, a=1.0):
    d = th - 7
    front = [(HC[0] - 250, HC[1] - 860), (HC[0] - 275 - 7 * d, HC[1] - 470), (HC[0] - 250 - 3 * d, HC[1] - 190),
             (HC[0] - 200, HC[1] + 40), (HC[0] - 160, HC[1] + 600)]
    back = [(HC[0] + 280, HC[1] - 860), (HC[0] + 220 - 5 * d, HC[1] - 470), (HC[0] + 300, HC[1] - 70),
            (HC[0] + 240, HC[1] + 220), (HC[0] + 170, HC[1] + 600)]
    polyline(L, catmull(front, 12, False), (150, 200, 255), 3, 1.0, a * 0.55, dash=(14, 10))
    polyline(L, catmull(back, 12, False), (150, 200, 255), 3, 1.0, a * 0.55, dash=(14, 10))
    return front, back


def angle_mark(L, g, a=1.0, col=YEL):
    asis, psis = g['asis'], g['psis']
    polyline(L, [psis, (psis[0] - 440, psis[1])], WHITE, 2.5, 1.0, a * 0.7, dash=(12, 9))
    polyline(L, [psis, asis], col, 5, 1.0, a)
    marker(L, asis, col, 12, a); marker(L, psis, col, 12, a)
    ang = math.degrees(math.atan2(asis[1] - psis[1], asis[0] - psis[0]))
    polyline(L, arc_pts(psis, 190, 180, ang), col, 4, 1.0, a)
    return ang
