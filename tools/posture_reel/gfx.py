# Графика для экспертного рилса: чертёжные линии, стрелки, дуги, метки, карточки, лестница протокола, субтитры.
# Рисуем в 2 раза крупнее (SS) и уменьшаем, чтобы линии были гладкими. Координаты в функциях даются в пикселях кадра 1080x1920.
import math, os, textwrap
from PIL import Image, ImageDraw, ImageFont

B = os.path.dirname(os.path.abspath(__file__))
SS = 2
W, H = 1080, 1920
FONT = f'{B}/../challenge/fonts/Oswald.ttf'
WHITE = (240, 245, 250)
YEL = (255, 210, 31)
RED = (255, 90, 78)
BLUE = (79, 179, 255)
GREEN = (61, 220, 132)
INK = (8, 14, 22)
_fonts = {}


def font(size):
    k = int(size * SS)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT, k)
    return _fonts[k]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ph(t, t0, d=0.5):
    """Прогресс анимации 0..1 от момента t0 за d секунд."""
    return ease((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def rgba(c, a):
    return (c[0], c[1], c[2], int(255 * max(0, min(1, a))))


class Layer:
    def __init__(self):
        self.img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def out(self):
        return self.img.resize((W, H), Image.BILINEAR)


def S(p):
    return (p[0] * SS, p[1] * SS)


def lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def polyline(L, pts, col, w=3, frac=1.0, a=1.0, dash=None):
    """Ломаная, нарисованная на долю frac своей длины (эффект прорисовки)."""
    if frac <= 0 or a <= 0 or len(pts) < 2:
        return
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) * frac
    out, acc = [pts[0]], 0.0
    for i, s in enumerate(seg):
        if acc + s >= total:
            out.append(lerp(pts[i], pts[i + 1], (total - acc) / s if s else 1))
            break
        out.append(pts[i + 1]); acc += s
    c = rgba(col, a)
    if dash:
        on, off = dash
        for i in range(len(out) - 1):
            p, q = out[i], out[i + 1]
            L_ = math.dist(p, q); n = 0.0
            while n < L_:
                e = min(n + on, L_)
                L.d.line([S(lerp(p, q, n / L_)), S(lerp(p, q, e / L_))], fill=c, width=int(w * SS))
                n += on + off
    else:
        L.d.line([S(p) for p in out], fill=c, width=int(w * SS), joint='curve')
    return out[-1]


def arrowhead(L, tip, frm, col, size=22, a=1.0):
    ang = math.atan2(tip[1] - frm[1], tip[0] - frm[0])
    p1 = (tip[0] - size * math.cos(ang - 0.45), tip[1] - size * math.sin(ang - 0.45))
    p2 = (tip[0] - size * math.cos(ang + 0.45), tip[1] - size * math.sin(ang + 0.45))
    L.d.polygon([S(tip), S(p1), S(p2)], fill=rgba(col, a))


def arrow(L, p0, p1, col, w=5, frac=1.0, a=1.0, head=24):
    if frac <= 0:
        return
    tip = polyline(L, [p0, p1], col, w, frac, a)
    if frac > 0.15:
        arrowhead(L, tip, p0, col, head, a)


def arc_pts(c, r, a0, a1, n=40):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def arc_arrow(L, c, r, a0, a1, col, w=5, frac=1.0, a=1.0, head=24):
    pts = arc_pts(c, r, a0, a1)
    tip = polyline(L, pts, col, w, frac, a)
    if frac > 0.2 and tip:
        k = max(1, int(len(pts) * frac) - 3)
        arrowhead(L, tip, pts[min(k, len(pts) - 1)] if math.dist(tip, pts[min(k, len(pts) - 1)]) > 2 else pts[max(0, k - 3)], col, head, a)


def marker(L, p, col=YEL, r=13, a=1.0):
    """Метка-перекрестие, как на чертеже."""
    if a <= 0:
        return
    c = rgba(col, a)
    L.d.ellipse([S((p[0] - r, p[1] - r)), S((p[0] + r, p[1] + r))], outline=c, width=int(3 * SS))
    L.d.ellipse([S((p[0] - 4, p[1] - 4)), S((p[0] + 4, p[1] + 4))], fill=c)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        L.d.line([S((p[0] + dx * (r + 3), p[1] + dy * (r + 3))), S((p[0] + dx * (r + 11), p[1] + dy * (r + 11)))], fill=c, width=int(2 * SS))


def text(L, xy, s, size, col=WHITE, a=1.0, anchor='la', stroke=3):
    if a <= 0:
        return
    L.d.text(S(xy), s, font=font(size), fill=rgba(col, a), anchor=anchor,
             stroke_width=int(stroke * SS), stroke_fill=rgba(INK, a * 0.85))


def text_w(s, size):
    return font(size).getlength(s) / SS


def callout(L, p, lab_xy, lines, col=YEL, a=1.0, size=30, sub=None):
    """Выноска: точка, ломаная линия к подписи, подпись (первая строка цветом, остальные белые)."""
    if a <= 0:
        return
    marker(L, p, col, 11, a)
    lab_xy = (lab_xy[0], max(200, min(lab_xy[1], 1570)))
    right = lab_xy[0] >= p[0]
    x = lab_xy[0] + (10 if right else -10)
    anchor = 'lm' if right else 'rm'
    y = lab_xy[1]
    ls = lines if isinstance(lines, list) else [lines]
    wmax = max(text_w(s_, size if i == 0 else size * 0.82) for i, s_ in enumerate(ls))
    if right and x + wmax > W - 25:
        x = W - 25 - wmax
    if not right and x - wmax < 25:
        x = 25 + wmax
    y = max(200, min(y, 1570 - size * 1.25 * (len(ls) - 1)))
    end = (x - (6 if right else -6), y)
    elbow = (p[0] + (end[0] - p[0]) * 0.35, end[1]) if abs(end[1] - p[1]) > 40 else (end[0], p[1])
    polyline(L, [p, elbow, end], col, 2.5, 1.0, a)
    for i, s in enumerate(ls):
        text(L, (x, y + i * size * 1.25), s, size if i == 0 else size * 0.82, col if i == 0 else WHITE, a, anchor)


def panel(L, box, a=1.0, accent=YEL):
    x0, y0, x1, y1 = box
    L.d.rounded_rectangle([S((x0, y0)), S((x1, y1))], radius=18 * SS, fill=(8, 14, 22, int(170 * a)))
    L.d.rectangle([S((x0, y0 + 14)), S((x0 + 7, y1 - 14))], fill=rgba(accent, a))


def card(L, x, y, title, lines, a=1.0, t=99, t0=0.0, accent=YEL, wmax=640):
    """Карточка шага: заголовок и строки появляются по очереди."""
    if a <= 0:
        return
    wrapped = []
    for s in lines:
        wrapped += textwrap.wrap(s, 34) or ['']
    h = 74 + 40 * len(wrapped)
    w = max([text_w(title, 40)] + [text_w(s, 31) for s in wrapped]) + 70
    w = min(max(w, 300), wmax)
    panel(L, (x, y, x + w, y + h), a, accent)
    text(L, (x + 30, y + 20), title, 40, accent, a, stroke=0)
    for i, s in enumerate(wrapped):
        text(L, (x + 30, y + 72 + 40 * i), s, 31, WHITE, a * ph(t, t0 + 0.35 + 0.18 * i, 0.3), stroke=0)


LADDER = ['ШЕЯ', 'ЛОПАТКИ', 'ПОЯСНИЦА И БЕДРО', 'СРЕДНЯЯ ЯГОДИЧНАЯ', 'СТОПА', 'РАСТЯЖКА', 'ПРЕСС']


def ladder(L, step, a=1.0, big=False, t=99, t0=0.0):
    """Протокол сверху вниз: текущий шаг жёлтый, пройденные белые, будущие тусклые."""
    if a <= 0:
        return
    if big:
        x, y0, dy, fs = 120, 470, 108, 50
    else:
        x, y0, dy, fs = 1040, 330, 54, 27
    n = len(LADDER)
    line_x = x - 38 if big else x + 0
    if big:
        polyline(L, [(line_x, y0 - 30), (line_x, y0 + dy * (n - 1) + 30)], WHITE, 3, ph(t, t0, 1.2), a * 0.8)
        arrowhead(L, (line_x, y0 + dy * (n - 1) + 52), (line_x, y0), WHITE, 24, a * ph(t, t0 + 1.0, 0.3))
    for i, s in enumerate(LADDER):
        ai = a * (ph(t, t0 + 0.15 * i, 0.3) if big else 1.0)
        col = YEL if i + 1 == step else WHITE
        al = ai * (1.0 if (big or i + 1 <= step) else 0.45)
        lab = f'{i + 1}  {s}'
        if big:
            L.d.ellipse([S((line_x - 9, y0 + i * dy - 9)), S((line_x + 9, y0 + i * dy + 9))], fill=rgba(YEL if i == 0 else WHITE, ai))
            text(L, (x, y0 + i * dy), lab, fs, col if i else YEL, ai, 'lm', 4)
        else:
            text(L, (x, y0 + i * dy), lab, fs, col, al, 'rm', 3)


def subtitle(L, s, a=1.0):
    lines = textwrap.wrap(s, 30)
    y = 1700 - 34 * (len(lines) - 1)
    for i, ln in enumerate(lines):
        text(L, (W / 2, y + i * 68), ln, 54, WHITE, a, 'mm', 5)


def draft_tag(L):
    text(L, (W / 2, 70), 'ЧЕРНОВИК: СУБТИТРЫ = БУДУЩИЙ ГОЛОС', 28, WHITE, 0.75, 'mm', 3)


def grid(L, a=0.12, step=60):
    c = rgba((150, 200, 255), a)
    for x in range(0, W, step):
        L.d.line([S((x, 0)), S((x, H))], fill=c, width=SS)
    for y in range(0, H, step):
        L.d.line([S((0, y)), S((W, y))], fill=c, width=SS)


def chip(L, lines, a=1.0, x=60, y=150):
    if a <= 0:
        return
    w = max(text_w(s, 30 if i else 34) for i, s in enumerate(lines)) + 50
    panel(L, (x, y, x + w, y + 22 + 44 * len(lines)), a, BLUE)
    for i, s in enumerate(lines):
        text(L, (x + 26, y + 16 + 44 * i), s, 34 if i == 0 else 28, BLUE if i == 0 else WHITE, a, stroke=0)


def cross(L, c, r, col=RED, a=1.0, w=9):
    L.d.line([S((c[0] - r, c[1] - r)), S((c[0] + r, c[1] + r))], fill=rgba(col, a), width=int(w * SS))
    L.d.line([S((c[0] - r, c[1] + r)), S((c[0] + r, c[1] - r))], fill=rgba(col, a), width=int(w * SS))


def check(L, c, r, col=GREEN, a=1.0, w=9, frac=1.0):
    polyline(L, [(c[0] - r, c[1]), (c[0] - r * 0.3, c[1] + r * 0.7), (c[0] + r, c[1] - r * 0.8)], col, w, frac, a)
