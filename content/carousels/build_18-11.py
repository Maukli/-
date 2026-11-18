# Карусели c5 (сон), c6 (креатин и протеин), c7 (скручивания), версия 2 от 18.11:
# больше интерактива по просьбе Микаела: чертёжная графика по смыслу (углы, ориентиры, шкалы, схемы),
# подсветка работающих мышц, вопрос к подписчикам. Пишет слайды в carousels.json, готовит фото в img/src/.
# Запуск: python3 content/carousels/build_18-11.py && CAROUSELS=... node content/carousels/render_slides.js
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = f'{DIR}/img/src'
SP = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
A, TXT, SOFT, MUTED, BG, RED = '#FF9F5A', '#F4F1EA', '#D5DCE4', '#8597AB', '#102033', '#FF5A4E'
FONT = "font-family=\"Manrope\""
SH = 'style="filter:drop-shadow(0 3px 8px rgba(0,0,0,.55))"'


# ---------- векторные элементы (пиксели блока) ----------
def wl(text, size):
    return len(text) * size * 0.6


def pill(x, y, text, fill=A, color=BG, size=32, anchor='start'):
    w = wl(text, size) + 36; h = size * 1.55
    x0 = x - w / 2 if anchor == 'middle' else (x - w if anchor == 'end' else x)
    return (f'<g {SH}><rect x="{x0:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{h / 2.6:.0f}" fill="{fill}"/>'
            f'<text x="{x0 + w / 2:.0f}" y="{y + h * 0.69:.0f}" {FONT} font-weight="800" font-size="{size}" fill="{color}" text-anchor="middle">{text}</text></g>')


def text(x, y, s, size=30, color=TXT, weight=800, anchor='start'):
    return f'<text x="{x:.0f}" y="{y:.0f}" {FONT} font-weight="{weight}" font-size="{size}" fill="{color}" text-anchor="{anchor}" {SH}>{s}</text>'


def line(x0, y0, x1, y1, color=A, w=8, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x0:.0f}" y1="{y0:.0f}" x2="{x1:.0f}" y2="{y1:.0f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d} {SH}/>'


def arrow(x0, y0, x1, y1, color=A, w=8, head=26):
    import math
    a = math.atan2(y1 - y0, x1 - x0)
    p1 = (x1 - head * math.cos(a - 0.45), y1 - head * math.sin(a - 0.45))
    p2 = (x1 - head * math.cos(a + 0.45), y1 - head * math.sin(a + 0.45))
    bx, by = x1 - head * 0.8 * math.cos(a), y1 - head * 0.8 * math.sin(a)
    return (line(x0, y0, bx, by, color, w) +
            f'<polygon points="{x1:.0f},{y1:.0f} {p1[0]:.0f},{p1[1]:.0f} {p2[0]:.0f},{p2[1]:.0f}" fill="{color}" {SH}/>')


def dbl(x0, y0, x1, y1, color=A, w=7):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    return arrow(mx, my, x0, y0, color, w, 22) + arrow(mx, my, x1, y1, color, w, 22)


def ring(x, y, rx, ry=None, color=A, w=7):
    return f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.0f}" ry="{(ry or rx):.0f}" fill="none" stroke="{color}" stroke-width="{w}" {SH}/>'


def dot(x, y, r=12, color=A, stroke=None):
    s = f' stroke="{stroke}" stroke-width="5"' if stroke else ''
    return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{color}"{s} {SH}/>'


def arc(cx, cy, r, a0, a1, color=A, w=7):
    import math
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy - r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy - r * math.sin(math.radians(a1))
    large = 1 if abs(a1 - a0) > 180 else 0
    sweep = 0 if a1 > a0 else 1
    return f'<path d="M{x0:.0f} {y0:.0f} A{r} {r} 0 {large} {sweep} {x1:.0f} {y1:.0f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" {SH}/>'


def panel(x, y, w, h, op=0.72):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="{BG}" fill-opacity="{op}"/>'


def svg(w, h, *parts):
    return {'type': 'svg', 'w': w, 'h': h, 'svg': ''.join(parts)}


def P(xp, yp, w, h):
    return xp * w / 100, yp * h / 100


# ---------- фото ----------
def crop_to(src, out, ratio, y0=None, focus_y=0.5, blur_top=None, width=1620):
    im = Image.open(src).convert('RGB')
    W, H = im.size
    if W / H > ratio:  # шире нужного: режем по бокам
        cw = int(H * ratio); im = im.crop(((W - cw) // 2, 0, (W - cw) // 2 + cw, H)); W = cw
    ch = int(W / ratio)
    top = int(H * y0) if y0 is not None else int((H - ch) * focus_y)
    top = max(0, min(top, H - ch))
    im = im.crop((0, top, W, top + ch)).resize((width, int(width / ratio)), Image.LANCZOS)
    im.save(out, quality=90)


def grid_bg(out, w=1620, h=2025):
    im = Image.new('RGB', (w, h), (13, 27, 43)); d = ImageDraw.Draw(im)
    for x in range(0, w, 54):
        d.line([(x, 0), (x, h)], fill=(22, 40, 61) if x % 270 else (30, 52, 78), width=2)
    for y in range(0, h, 54):
        d.line([(0, y), (w, y)], fill=(22, 40, 61) if y % 270 else (30, 52, 78), width=2)
    g = Image.new('L', (w, h), 0); ImageDraw.Draw(g).ellipse([w * 0.1, h * 0.05, w * 0.9, h * 0.55], fill=90)
    glow = Image.new('RGB', (w, h), (40, 70, 105))
    im = Image.composite(glow, im, g.filter(ImageFilter.GaussianBlur(220)))
    im.save(out, quality=92)


def glow(src, out, caps, color=A, strength=0.6):
    subprocess.run([sys.executable, f'{DIR}/img/glow.py', src, out, json.dumps(caps), color, str(strength)], check=True, capture_output=True)


def prep():
    B = f'{SP}/car/base'; DL = f'{SP}/car/dl'
    grid_bg(f'{SRC}/bg_grid.jpg')
    crop_to(f'{DL}/px_6944004.jpg', f'{SRC}/c5_night.jpg', 0.75, focus_y=0.45)
    crop_to(f'{DL}/px_3838706.jpg', f'{SRC}/c5_tired_gym.jpg', 0.75, focus_y=0.6)
    crop_to(f'{DL}/px_18542702.jpg', f'{SRC}/c5_clock.jpg', 0.8)
    crop_to(f'{DL}/px_9615255.jpg', f'{SRC}/c5_bedroom.jpg', 0.8)
    crop_to(f'{DL}/px_13779116.jpg', f'{SRC}/c6_container.jpg', 0.8)
    # c7: подсветка мышц по силуэту
    glow(f'{B}/c7_cover_bad.jpg', f'{SRC}/c7_cover.jpg', [[40, 44, 42, 54, 5]], RED, 0.55)
    glow(f'{B}/c7_bad.jpg', f'{SRC}/c7_bad.jpg', [[56, 48, 54, 60, 5]], RED, 0.55)
    for n in ('c7_phone', 'c7_good_side', 'c7_good_close', 'c7_protocol', 'c7_cta', 'c7_good_top'):
        Image.open(f'{B}/{n}.jpg' if os.path.exists(f'{B}/{n}.jpg') else f'{SRC}/{n}.jpg').save(f'{SRC}/{n}.jpg', quality=90)


# ---------- слайды ----------
def c5():
    W, F = 1080, 1350
    q = svg(W, 783,
            pill(40, 560, '1 жим лёжа', BG, TXT, 32), pill(560, 560, '2 жим ногами', BG, TXT, 32),
            pill(40, 650, '3 становая тяга', BG, TXT, 32), pill(560, 650, '4 сгибание рук', BG, TXT, 32))
    ans = svg(W, 783,
              arrow(270, 240, 270, 470, RED, 14, 44), pill(268, 500, 'максимум упал', RED, TXT, 32, 'middle'),
              line(760, 330, 860, 330, A, 14), line(760, 375, 860, 375, A, 14), pill(810, 500, 'без изменений', A, BG, 32, 'middle'))
    # ночи: 3 часа сна из обычных 8
    nights = []
    for i, x in enumerate((230, 540, 850)):
        nights += [text(x, 205, f'ночь {i + 1}', 34, TXT, 800, 'middle'),
                   f'<rect x="{x - 45}" y="230" width="90" height="220" rx="20" fill="{MUTED}" fill-opacity=".35"/>',
                   f'<rect x="{x - 45}" y="368" width="90" height="82" rx="20" fill="{A}"/>',
                   text(x, 492, '3 ч сна', 28, SOFT, 700, 'middle')]
        nights += ([line(x - 30, 548, x + 30, 548, SOFT, 10), line(x - 30, 576, x + 30, 576, SOFT, 10)] if i == 0
                   else [arrow(x, 522, x, 610, RED, 12, 36)])
    nights += [text(540, 660, 'вес на 20 повторений', 30, MUTED, 700, 'middle')]
    tl = svg(W, F, panel(70, 145, 940, 545), *nights)
    bars = svg(W, F, panel(70, 170, 940, 360),
               text(110, 240, 'все виды нагрузки', 30, SOFT, 700), f'<rect x="110" y="262" width="760" height="56" rx="14" fill="{A}"/>',
               text(890, 302, '7,6%', 34, TXT, 800),
               text(110, 395, 'сила', 30, SOFT, 700), f'<rect x="110" y="417" width="285" height="56" rx="14" fill="{A}" fill-opacity=".75"/>',
               text(415, 457, 'около 3%', 34, TXT, 800))
    # окно сна: ось 22-8, пример
    x0, step = 130, 82  # 22:00 -> x0, шаг 1 час
    hx = lambda h: x0 + ((h - 22) % 24) * step
    axis = [line(hx(22), 300, hx(8), 300, MUTED, 4)]
    for h in (22, 0, 2, 4, 6, 8):
        axis += [line(hx(h), 290, hx(h), 310, MUTED, 4), text(hx(h), 275, str(h), 26, MUTED, 700, 'middle')]
    rows = [('обычный сон', 23, 7, SOFT, None, None), ('встал раньше', 23, 4, A, 'просадка стабильная', A),
            ('лёг позже', 3, 7, A, 'эффект нестабильный', MUTED)]
    for i, (lab, a, b, col, tag, tcol) in enumerate(rows):
        y = 370 + i * 125
        axis += [text(hx(22), y, lab, 30, TXT, 800), f'<rect x="{hx(a):.0f}" y="{y + 14}" width="{hx(b) - hx(a):.0f}" height="38" rx="12" fill="{col}"/>']
        if tag:
            axis += [pill(hx(8), y - 30, tag, tcol, BG if tcol == A else TXT, 26, 'end')]
    axis += [text(hx(8), 215, 'пример', 26, MUTED, 700, 'end')]
    win = svg(W, F, panel(70, 170, 940, 590), *axis)
    # шкала решений Микаела: 3-9 часов
    sx = lambda h: 110 + (h - 3) * 143.3
    sc = [panel(70, 150, 940, 640),
          text(110, 220, 'сколько спал', 30, MUTED, 700),
          f'<rect x="{sx(3):.0f}" y="245" width="{sx(5) - sx(3):.0f}" height="60" rx="14" fill="{RED}"/>',
          f'<rect x="{sx(5):.0f}" y="245" width="{sx(7) - sx(5):.0f}" height="60" fill="{A}"/>',
          f'<rect x="{sx(7):.0f}" y="245" width="{sx(9) - sx(7):.0f}" height="60" rx="14" fill="{SOFT}"/>']
    for h in range(3, 10):
        sc += [text(sx(h), 345, f'{h}', 28, TXT, 800, 'middle')]
    for xa, lines_, col in ((sx(4), ['меньше 5 ч', 'тяжёлый день', 'меняю на', 'средний,', 'все рабочие', 'минус 5%'], RED),
                            (sx(6), ['меньше 7 ч', 'в тяжёлый', 'и средний', 'день верхний', 'вес минус 3%'], A),
                            (sx(8), ['7 ч и больше', 'по плану'], SOFT)):
        for j, l in enumerate(lines_):
            sc += [text(xa, 410 + j * 40, l, 30 if j == 0 else 27, col if j == 0 else TXT, 800 if j == 0 else 700, 'middle')]
    scale = svg(W, F, *sc)
    return [
        {'layout': 'photo-top', 'photoHeight': 66, 'big': True, 'photo': 'src/c5_night.jpg', 'focus': '40% 50%',
         'photo2': 'src/c5_tired_gym.jpg', 'focus2': '45% 50%',
         'title': 'Спал 4 часа?\nТяжёлого дня\nне будет', 'body': 'Мои правила: меньше 7 и меньше 5 часов. И 2 исследования.'},
        {'layout': 'photo-top', 'photoHeight': 58, 'photo': 'src/mikael_bench.jpg', 'focus': '50% 70%', 'photo2': 'src/mikael_curl.jpg', 'focus2': '50% 50%',
         'title': '3 ночи по 3 часа сна. Какой максимум не упал?', 'body': 'Ливерпуль, 1994. 8 парней 18-24 лет. Выбери номер, ответ на следующем слайде.', 'marks': [q]},
        {'layout': 'photo-top', 'photoHeight': 58, 'photo': 'src/mikael_bench.jpg', 'focus': '50% 70%', 'photo2': 'src/mikael_curl.jpg', 'focus2': '50% 50%',
         'title': 'Не упал только максимум в сгибании рук', 'body': 'В жиме лёжа, жиме ногами и становой тяге максимум упал. Похоже, тяжёлым многосуставным упражнениям собранность нужна больше всего.', 'marks': [ans]},
        {'layout': 'big-number', 'photo': 'src/c5_clock.jpg', 'focus': '50% 50%',
         'title': 'Подходы на 20 повторений просели', 'body': 'Вес на 20 повторений при той же ощущаемой тяжести снизился во всех 4 упражнениях после второй ночи. Бодрость упала, усталость выросла.', 'marks': [tl]},
        {'layout': 'big-number', 'photo': 'src/c5_bedroom.jpg', 'focus': '50% 50%', 'number': '7,6%',
         'title': 'В среднем минус после недосыпа', 'body': 'Метаанализ 2022 года: 69 работ, почти тысяча человек.', 'marks': [bars]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%',
         'title': 'Важно, как именно не доспал', 'body': 'Ранний подъём бьёт стабильно, поздний отбой нестабильно. До полудня результат почти не страдал, во второй половине дня проседал.', 'marks': [win]},
        {'layout': 'big-number', 'photo': 'src/c5_gym_phone.jpg', 'focus': '50% 40%',
         'title': 'Мои правила для клиентов', 'body': 'Онлайн-клиент перед каждой тренировкой пишет, сколько спал. Нагрузку правлю по этой шкале.', 'marks': [scale]},
        {'layout': 'cta-photo', 'photo': 'src/c5_smile.jpg', 'focus': '50% 30%',
         'title': 'А ты сколько спал сегодня?', 'body': 'Найди себя на шкале и пиши цифру в комментариях. Сохрани, чтобы проверить себя перед тяжёлой тренировкой.'},
    ]


def c6():
    W, F = 1080, 1350
    chips = svg(W, 891, pill(1040, 170, 'креатин 5 г', A, BG, 34, 'end'), pill(1040, 250, 'протеин до и после', A, BG, 34, 'end'),
                pill(1040, 330, 'EAA 10-15 г', A, BG, 34, 'end'), pill(1040, 410, 'BCAA не беру', MUTED, BG, 34, 'end'))
    wk = [panel(70, 170, 940, 330), text(110, 235, 'креатин по дням недели', 30, MUTED, 700)]
    for i, d in enumerate(['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']):
        x = 150 + i * 130
        wk += [dot(x, 330, 52, A), text(x, 343, '5 г', 32, BG, 800, 'middle'), text(x, 440, d, 30, TXT, 800, 'middle')]
    week = svg(W, F, *wk)
    # загрузка: схема по Hultman 1996
    cx0, cy0, cw, chh = 150, 660, 820, 400
    dx = lambda d: cx0 + d / 28 * cw
    lvl = cy0 - chh * 0.85
    fast = ' '.join(f'{dx(d):.0f},{cy0 - chh * 0.85 * min(1, (1 - (0.5 ** (d / 1.6))) / (1 - 0.5 ** (6 / 1.6))):.0f}' for d in [x / 2 for x in range(0, 57)])
    slow = ' '.join(f'{dx(d):.0f},{cy0 - chh * 0.85 * min(1, (1 - (0.5 ** (d / 8.5))) / (1 - 0.5 ** (28 / 8.5))):.0f}' for d in [x / 2 for x in range(0, 57)])
    ld = svg(W, F, panel(70, 170, 940, 590),
             text(110, 230, 'креатин в мышцах', 30, MUTED, 700),
             line(cx0, cy0, cx0 + cw, cy0, MUTED, 4), line(cx0, cy0, cx0, cy0 - chh, MUTED, 4),
             line(cx0, lvl, cx0 + cw, lvl, SOFT, 4, '14 12'),
             *[text(dx(d), cy0 + 45, str(d), 26, MUTED, 700, 'middle') for d in (0, 7, 14, 21, 28)],
             text(cx0 + cw, cy0 + 85, 'дней', 26, MUTED, 700, 'end'),
             f'<polyline points="{slow}" fill="none" stroke="{SOFT}" stroke-width="9" stroke-linecap="round" {SH}/>',
             f'<polyline points="{fast}" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round" {SH}/>',
             pill(dx(7.5), lvl + 22, '20 г в день: 6 дней', A, BG, 28), pill(dx(28), lvl + 120, '3 г в день: 28 дней', SOFT, BG, 28, 'end'),
             text(dx(28), lvl - 16, 'тот же уровень', 26, SOFT, 700, 'end'))
    pr = svg(W, F, panel(70, 200, 940, 470),
             line(110, 450, 970, 450, MUTED, 5),
             f'<rect x="390" y="395" width="300" height="110" rx="22" fill="none" stroke="{A}" stroke-width="7"/>',
             text(540, 463, 'тренировка', 34, TXT, 800, 'middle'),
             dot(300, 450, 34, A), text(300, 375, 'до', 30, A, 800, 'middle'), text(300, 560, 'протеин', 28, TXT, 700, 'middle'),
             dot(780, 450, 34, A), text(780, 375, 'после', 30, A, 800, 'middle'), text(780, 560, 'протеин', 28, TXT, 700, 'middle'),
             text(780, 600, 'креатин 5 г', 28, TXT, 700, 'middle'),
             dot(150, 450, 16, MUTED), dot(930, 450, 16, MUTED), text(150, 300, 'еда', 30, MUTED, 800, 'middle'), text(930, 300, 'еда', 30, MUTED, 800, 'middle'),
             text(540, 270, 'вне тренировки протеин не пью', 28, MUTED, 700, 'middle'))
    # белок: перелом около 1,6 г/кг (Morton 2018)
    gx0, gy0, gw, gh = 150, 455, 820, 170
    gx = lambda g: gx0 + (g - 0.8) / 1.8 * gw
    import math
    curve = ' '.join(f'{gx(g):.0f},{gy0 - gh * (min(g, 1.6) - 0.8) / 0.8 * 0.85 - gh * 0.15 * (1 - math.exp(-(max(g, 1.6) - 1.6) * 2)):.0f}' for g in [0.8 + i * 0.05 for i in range(37)])
    pro = svg(W, F, panel(70, 178, 940, 372),
              f'<rect x="{gx(1.8):.0f}" y="{gy0 - gh - 10}" width="{gx(2.2) - gx(1.8):.0f}" height="{gh + 10}" fill="{A}" fill-opacity=".22"/>',
              text((gx(1.8) + gx(2.2)) / 2, gy0 - gh - 25, 'сушка', 28, A, 800, 'middle'),
              line(gx0, gy0, gx0 + gw, gy0, MUTED, 4), line(gx(1.6), gy0, gx(1.6), gy0 - gh, SOFT, 4, '12 10'),
              f'<polyline points="{curve}" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round" {SH}/>',
              *[text(gx(g), gy0 + 42, f'{g:.1f}'.replace('.', ','), 26, SOFT if g != 1.6 else A, 800, 'middle') for g in (0.8, 1.2, 1.6, 2.0, 2.4)],
              text(110, 228, 'прирост безжировой массы', 28, MUTED, 700), text(gx0 + gw, gy0 + 78, 'г белка на кг в день', 24, MUTED, 700, 'end'))
    names = ['лейцин', 'изолейцин', 'валин', 'лизин', 'метионин', 'фенилаланин', 'треонин', 'триптофан', 'гистидин']

    def aa(hl, top=235):
        parts = [panel(70, top - 85, 940, 480)]
        for i, n in enumerate(names):
            x, y = 230 + (i % 3) * 310, top + (i // 3) * 140
            on = hl is None or i in hl
            parts += [f'<circle cx="{x}" cy="{y}" r="38" fill="{A if on else "none"}" stroke="{A if on else MUTED}" stroke-width="6" {SH}/>',
                      text(x, y + 72, n, 27, TXT if on else MUTED, 800 if on else 700, 'middle')]
        return parts
    eaa = svg(W, F, *aa(None))
    bc = aa({0, 1, 2}, 330) + [f'<rect x="100" y="262" width="880" height="180" rx="30" fill="none" stroke="{A}" stroke-width="5" stroke-dasharray="16 12"/>',
                          pill(980, 232, 'BCAA', A, BG, 30, 'end')]
    bcaa = svg(W, F, *bc)
    tlp = [panel(70, 150, 940, 640), line(170, 230, 170, 710, MUTED, 6)]
    for i, (lab, val) in enumerate([('до тренировки', 'протеин'), ('во время', 'EAA 10-15 г'), ('после', 'протеин и креатин 5 г'), ('выходной', 'креатин 5 г')]):
        y = 240 + i * 155
        tlp += [dot(170, y, 26, A if i < 3 else SOFT), text(230, y - 8, lab, 28, MUTED, 700), text(230, y + 38, val, 40, TXT, 800)]
    day = svg(W, F, *tlp)
    return [
        {'layout': 'photo-top', 'photoHeight': 66, 'big': True, 'photo': 'src/c6_cover.jpg', 'focus': '50% 8%',
         'title': 'Жму 170 кг.\nПротеин пью 2 раза', 'body': 'До и после тренировки. В выходной только креатин.', 'marks': [chips]},
        {'layout': 'big-number', 'photo': 'src/c6_scoop.jpg', 'focus': '45% 50%', 'number': '5 г',
         'title': 'Креатин каждый день', 'body': 'В дни отдыха тоже. В день тренировки пью после неё, вместе с протеином.', 'marks': [week]},
        {'layout': 'big-number', 'photo': 'src/c6_container.jpg', 'focus': '50% 50%',
         'title': 'Загрузка не обязательна', 'body': 'Итог тот же, разница только в сроке (Hultman, 1996). Беру моногидрат: он изучен лучше всех форм.', 'marks': [ld]},
        {'layout': 'big-number', 'photo': 'src/mikael_pullup.jpg', 'focus': '50% 25%',
         'title': 'Протеин только вокруг тренировки', 'body': 'Порция до, порция после. Белок на остальной день добираю едой.', 'marks': [pr]},
        {'layout': 'big-number', 'photo': 'src/px_1640777.jpg', 'focus': '50% 50%', 'number': '1,6 г',
         'title': 'Белок за день важнее всего', 'body': 'Метаанализ 2018 года, 49 исследований. Для максимума до 2,2 г. На сушке беру 1,8-2,2 г.', 'marks': [pro]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%', 'number': '10-15 г',
         'title': 'EAA во время тренировки', 'body': 'Все 9 незаменимых аминокислот. Пью по ходу тренировки.', 'marks': [eaa]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%',
         'title': 'BCAA не беру', 'body': 'Это 3 из 9 незаменимых аминокислот. Для синтеза мышечного белка нужны все 9. Поэтому если пить аминокислоты, то полный набор EAA.', 'marks': [bcaa]},
        {'layout': 'big-number', 'photo': 'src/c6_container.jpg', 'focus': '30% 50%',
         'title': 'Мой день тренировки', 'body': 'Сохрани схему, чтобы не путать.', 'marks': [day]},
        {'layout': 'cta-photo', 'photo': 'src/c6_cta.jpg', 'focus': '50% 30%',
         'title': 'А ты что пьёшь?', 'body': 'Пиши в комментариях, разберу твою схему.'},
    ]


def c7():
    W = 1080
    b1 = (W, 891); x, y = P(42, 37, *b1)
    cover = svg(*b1, ring(x, y, 150, 150, RED, 8), pill(P(60, 0, *b1)[0], P(0, 56, *b1)[1], 'так не даю', RED, TXT, 36))
    b2 = (W, 810)
    bad = svg(*b2, ring(*P(54, 41, *b2), 150, 130, RED, 7), arrow(*P(61, 30, *b2), *P(44, 16, *b2), RED, 10, 34),
              pill(*P(3, 22, *b2), 'руки тянут голову', RED, TXT, 28), pill(*P(57, 70, *b2), 'сгибание шейного отдела', RED, TXT, 30))
    b3 = (W, 837)
    tr, c7p = P(51.5, 47, *b3), P(60, 57, *b3)
    cva = svg(*b3, line(c7p[0] - 10, c7p[1], c7p[0] + 230, c7p[1], A, 6, '16 12'), line(*c7p, *tr, A, 7),
              arc(c7p[0], c7p[1], 95, 180, 132, A, 6), dot(*tr, 13, A, BG), dot(*c7p, 13, A, BG),
              pill(tr[0] - 20, tr[1] - 95, 'козелок уха', A, BG, 28, 'end'), pill(c7p[0] + 40, c7p[1] - 70, 'C7', A, BG, 28),
              pill(c7p[0] - 120, c7p[1] + 40, 'краниовертебральный угол', BG, A, 26, 'end'))
    b4 = (W, 810)
    chin, chest = P(41, 77, *b4), P(37, 90, *b4)
    good = svg(*b4, dbl(chin[0] - 30, chin[1] + 14, chest[0] - 30, chest[1] + 6, A, 6),
               pill(*P(3, 74, *b4), 'подбородок не прижат', A, BG, 28), pill(*P(60, 58, *b4), 'шея нейтральная', A, BG, 30),
               arrow(*P(66, 66, *b4), *P(50, 76, *b4), A, 7, 26), pill(*P(3, 20, *b4), 'блин 5-25 кг', A, BG, 30))
    b5 = (W, 810)
    side = svg(*b5, pill(*P(3, 46, *b5), 'прямая мышца живота', A, BG, 30), arrow(*P(18, 56, *b5), *P(24, 84, *b5), A, 7, 26),
               arc(*P(42, 80, *b5), 120, 150, 40, A, 7), pill(*P(55, 44, *b5), 'сгибание грудного отдела', A, BG, 28),
               arrow(*P(62, 54, *b5), *P(47, 66, *b5), A, 7, 26))
    ticks = []
    for i in range(20):
        x = 96 + i * 45; last = i == 19
        ticks += [f'<rect x="{x}" y="{400 if last else 440}" width="30" height="{110 if last else 70}" rx="8" fill="{A if last else SOFT}" fill-opacity="{1 if last else .8}" {SH}/>']
    ticks += [pill(1000, 330, 'задержка', A, BG, 28, 'end')]
    rep = svg(W, 1350, *ticks)
    b7 = (W, 945)
    pts = [(1, 49.5, 25.5), (2, 54.5, 32.5), (3, 57, 43), (3, 55.5, 57), (4, 57.5, 50), (5, 52, 79), (7, 47, 42)]
    pr = []
    for n, xp, yp in pts:
        x, y = P(xp, yp, *b7)
        pr += [dot(x, y, 24, A if n == 7 else TXT, BG), text(x, y + 10, str(n), 28, BG, 800, 'middle')]
    leg = [('1', 'шея'), ('2', 'лопатки'), ('3', 'поясничный отдел и'), ('', 'двуглавая мышца бедра'), ('', 'через 2 недели'), ('4', 'ягодичные мышцы'),
           ('5', 'стопа'), ('6', 'растяжка'), ('7', 'пресс в конце')]
    pr += [panel(705, 150, 362, 490, 0.8)]
    for i, (n, s_) in enumerate(leg):
        yy = 200 + i * 50
        pr += [text(725, yy, n, 26, A, 800), text(757, yy, s_, 23 if n or i == 3 else 21, A if n == '7' else (TXT if n or i == 3 else MUTED), 800 if n else 700)]
    proto = svg(*b7, *pr)
    b8 = (W, 1350)
    cta = svg(*b8, pill(*P(68, 33, *b8), 'шея?', A, BG, 36), arrow(*P(70, 37.5, *b8), *P(55, 51, *b8), A, 7, 26),
              pill(*P(70, 47, *b8), 'пресс?', A, BG, 36), arrow(*P(71, 51.5, *b8), *P(49, 61, *b8), A, 7, 26))
    return [
        {'layout': 'photo-top', 'photoHeight': 66, 'big': True, 'photo': 'src/c7_cover.jpg', 'focus': '50% 50%',
         'title': 'Качаешь пресс,\nа устаёт шея?', 'body': 'Дело в руках за головой. Моё скручивание с блином.', 'marks': [cover]},
        {'layout': 'photo-top', 'photoHeight': 60, 'photo': 'src/c7_bad.jpg', 'focus': '50% 50%',
         'title': 'Руки за головой тянут шею', 'body': 'Часто подбородок уходит к груди раньше, чем поднимается корпус. Тогда часть движения делает сгибание шейного отдела, а не грудного.', 'marks': [bad]},
        {'layout': 'photo-top', 'photoHeight': 62, 'photo': 'src/c7_phone.jpg', 'focus': '50% 50%',
         'title': 'А шея у многих уже впереди', 'body': 'Телефон, ноутбук, руль. Чем меньше краниовертебральный угол, тем дальше голова впереди. Нижние сегменты шейного отдела и так в сгибании. Тянуть голову руками значит добавлять сгибания.', 'marks': [cva]},
        {'layout': 'photo-top', 'photoHeight': 60, 'photo': 'src/c7_good_side.jpg', 'focus': '50% 50%',
         'title': 'Моё скручивание: блин перед собой', 'body': 'Блин 5-25 кг на прямых руках. Руки заняты, тянуть голову нечем. Шея остаётся нейтральной.', 'marks': [good]},
        {'layout': 'photo-top', 'photoHeight': 60, 'photo': 'src/c7_good_close.jpg', 'focus': '50% 50%',
         'title': 'Амплитуда маленькая', 'body': 'Поднимаю голову и верх грудного отдела: это сгибание позвоночника, его делает прямая мышца живота. Выше не иду. При полном подъёме корпуса растёт доля сгибателей бедра, в том числе подвздошно-поясничной мышцы.', 'marks': [side]},
        {'layout': 'big-number', 'photo': 'src/c7_good_top.jpg', 'focus': '50% 50%', 'number': '20',
         'title': 'Повторений, задержка в последнем', 'body': 'На тренажёре для пресса под углом, голова ниже таза. Нет тренажёра: на полу, ноги согнуты в коленях.', 'marks': [rep]},
        {'layout': 'photo-top', 'photoHeight': 70, 'photo': 'src/c7_protocol.jpg', 'focus': '50% 50%',
         'title': 'Пресс у меня последний', 'body': 'Протокол при переднем наклоне таза идёт сверху вниз.', 'marks': [proto]},
        {'layout': 'cta-photo', 'photo': 'src/c7_cta.jpg', 'focus': '50% 50%',
         'title': 'Проверь на себе', 'body': 'Сделай 20 скручиваний с блином. Где почувствовал: в прессе или в шее? Пиши в комментариях.', 'marks': [cta]},
    ]


if __name__ == '__main__':
    if '--no-prep' not in sys.argv:
        prep()
    p = f'{DIR}/carousels.json'
    d = json.load(open(p))
    new = {'c5_nedosyp': c5(), 'c6_kreatin_protein': c6(), 'c7_skruchivaniya': c7()}
    for c in d:
        if c['id'] in new:
            c['slides'] = new.pop(c['id'])
    for k, v in new.items():
        d.append({'id': k, 'slides': v})
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=2)
    sub = [c for c in d if c['id'] in ('c5_nedosyp', 'c6_kreatin_protein', 'c7_skruchivaniya')]
    json.dump(sub, open(f'{SP}/car/new.json', 'w'), ensure_ascii=False)
    print('ok')
