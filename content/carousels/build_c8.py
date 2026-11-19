# Карусель c8 "Наклон таза" (19.11, осанка главная тема): чертежи таза (движок схем из рилса tools/posture_reel/pelvis.py),
# кадры Микаела (тест у стены, вид сбоку), шкала нормы, пара сил при заднем наклоне, протокол Микаела из базы «Осанка».
# Запуск: python3 content/carousels/build_c8.py [--no-prep]
import importlib.util, json, math, os, sys
from PIL import Image, ImageFilter

DIR = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('b1811', f'{DIR}/build_18-11.py'); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
A, TXT, SOFT, MUTED, BG, RED = b.A, b.TXT, b.SOFT, b.MUTED, b.BG, b.RED
BLUE = '#6FB7FF'
pill, text, line, arrow, dot, arc, panel, svg, P, topfade = b.pill, b.text, b.line, b.arrow, b.dot, b.arc, b.panel, b.svg, b.P, b.topfade
SRC, SP = b.SRC, b.SP
SEL = f'{SP}/car/sel8'
POSTURE = f'{SP}/posture'  # gfx.py и pelvis.py со шрифтами (копия tools/posture_reel)


def portrait(src, out, ratio, top, blur=22):
    """Фон размыт по маске человека (MediaPipe), чтобы убрать людей на заднем плане."""
    sys.path.insert(0, f'{DIR}/img'); import glow
    im = Image.open(src).convert('RGB'); mask, _ = glow.pose(im)
    m = Image.fromarray((mask.clip(0, 1) * 255).astype('uint8')).resize(im.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    im = Image.composite(im, im.filter(ImageFilter.GaussianBlur(blur)), m)
    W, H = im.size; ch = int(W / ratio); t = max(0, min(int(H * top), H - ch))
    im.crop((0, t, W, t + ch)).resize((1620, int(1620 / ratio)), Image.LANCZOS).save(out, quality=90)


def schematics():
    """Три схемы таза без подписей: 20 (передний), 7 (нейтральный), -6 (задний) градусов."""
    sys.path.insert(0, POSTURE)
    from gfx import Layer
    import pelvis as Pv
    out = {}
    for th in (20, 7, -6):
        L = Layer(); Pv.draw_skeleton(L, th, 1.0, 1.0, labels=False); Pv.body_outline(L, th, 1.0)
        im = L.out(); bgim = Image.new('RGBA', im.size, (13, 27, 43, 255)); bgim.alpha_composite(im)
        out[th] = bgim.convert('RGB')
    return out


def wall_prep():
    """Тест у стены: колонна должна остаться резкой, размываем только людей слева от Микаела."""
    im = Image.open(f'{SEL}/wall_7.3_sr.png').convert('RGB'); W, H = im.size
    box = (0, int(H * 0.38), int(W * 0.36), int(H * 0.95))
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(24)), box[:2])
    r = 1080 / 1026; ch = int(W / r); t = int(H * 0.31)
    im.crop((0, t, W, t + ch)).resize((1620, int(1620 / r)), Image.LANCZOS).save(f'{SRC}/c8_wall.jpg', quality=90)


def prep():
    portrait(f'{SEL}/side_2.5_sr.png', f'{SRC}/c8_cover.jpg', 0.5625, 0.0)
    wall_prep()
    portrait(f'{SEL}/calm_9.6_sr.png', f'{SRC}/c8_cta.jpg', 0.8, 0.244)
    sc = schematics()
    # нейтральный таз крупно: кадр 1080x837 из схемы 1080x1920, y 640-1477
    sc[7].crop((0, 640, 1080, 1477)).resize((1620, 1256), Image.LANCZOS).save(f'{SRC}/c8_neutral.jpg', quality=92)
    # три таза рядом: каждая панель x 130-1000, y 330-1490 (870x1160), в 540x720
    tri = Image.new('RGB', (1620, 1296), (13, 27, 43))
    for i, th in enumerate((20, 7, -6)):
        tri.paste(sc[th].crop((130, 330, 1000, 1490)).resize((540, 720), Image.LANCZOS), (i * 540, 230))
    tri.save(f'{SRC}/c8_three.jpg', quality=92)
    # задний наклон для пары сил: кадр 1080x891 (photo-top 66), y 640-1531
    sc[-6].crop((0, 640, 1080, 1531)).resize((1620, 1336), Image.LANCZOS).save(f'{SRC}/c8_force.jpg', quality=92)
    sc[20].crop((180, 560, 900, 1760)).resize((1080, 1800), Image.LANCZOS).save(f'{SRC}/c8_cover_sch.jpg', quality=92)


def slides():
    W = 1080
    # 1. обложка: таз как ведро с наклоном вперёд
    b1 = (W, 891); cx, cy = 536 * 0.575, 0.736 * 953 - 31
    bucket = (f'<g transform="rotate(-16 {cx:.0f} {cy:.0f})" {b.SH}>'
              f'<path d="M{cx - 105:.0f} {cy - 60:.0f} L{cx + 105:.0f} {cy - 60:.0f} L{cx + 78:.0f} {cy + 62:.0f} L{cx - 78:.0f} {cy + 62:.0f} Z" fill="{A}" fill-opacity=".18" stroke="{A}" stroke-width="8" stroke-linejoin="round"/>'
              f'<path d="M{cx - 105:.0f} {cy - 60:.0f} Q{cx:.0f} {cy - 112:.0f} {cx + 105:.0f} {cy - 60:.0f}" fill="none" stroke="{A}" stroke-width="6" stroke-dasharray="14 10"/></g>')
    drops = ''.join(f'<path d="M{x:.0f} {y:.0f} q-9 16 0 24 q9 -8 0 -24z" fill="{BLUE}" {b.SH}/>' for x, y in ((cx - 130, cy - 10), (cx - 150, cy + 30), (cx - 128, cy + 66)))
    cover = svg(*b1, bucket, drops, pill(560, 150, 'передний наклон таза', A, BG, 30), pill(560, 210, 'схема', BG, SOFT, 30))
    # 2. ориентиры на нейтральном тазу (блок 1080x837, схема y 640-1477)
    b2 = (W, 837)
    s = lambda x, y: (x, (y - 640))
    asis, psis = s(410, 1072), s(733, 1013)
    a_line = (math.degrees(math.atan2(-(asis[1] - psis[1]), asis[0] - psis[0])) + 360) % 360
    lm = svg(*b2, line(psis[0], psis[1], psis[0] - 420, psis[1], SOFT, 4, '12 10'), line(*psis, *asis, A, 8),
             arc(psis[0], psis[1], 200, 180, a_line, A, 6),
             dot(*asis, 15, A, BG), dot(*psis, 15, A, BG),
             pill(asis[0] + 60, asis[1] + 40, 'передняя верхняя подвздошная ость', A, BG, 30, 'middle'),
             pill(1050, psis[1] - 150, 'задняя верхняя', A, BG, 30, 'end'), pill(1050, psis[1] - 95, 'подвздошная ость', A, BG, 30, 'end'),
             line(psis[0] + 10, psis[1] - 45, psis[0], psis[1] - 12, A, 5),
             pill(40, psis[1] - 110, 'угол наклона таза', BG, A, 30), arrow(250, psis[1] - 50, psis[0] - 215, psis[1] + 12, A, 5, 20))
    # 3. норма: шкала угла
    sx = lambda d: 110 + d * 34.4
    nm = [b.panel(70, 150, 940, 330), text(110, 215, 'угол наклона таза, градусов', 32, SOFT, 800),
          f'<rect x="{sx(0):.0f}" y="250" width="{sx(23) - sx(0):.0f}" height="70" rx="16" fill="{A}" fill-opacity=".22"/>',
          text(sx(11.5), 297, 'нейтраль у разных тазов: 0-23', 30, A, 800, 'middle'), line(sx(0), 360, sx(25), 360, MUTED, 4)]
    for d_ in (0, 5, 10, 15, 20, 25):
        nm += [line(sx(d_), 350, sx(d_), 370, MUTED, 4), text(sx(d_), 405, str(d_), 30, SOFT, 800, 'middle')]
    nm += [dot(sx(9.6), 360, 16, A, BG), dot(sx(11.7), 360, 16, SOFT, BG),
           pill(sx(9.6) - 20, 420, 'мужчины 9,6', A, BG, 32, 'end'), pill(sx(11.7) + 20, 420, 'женщины 11,7', SOFT, BG, 32),
           b.panel(70, 500, 455, 175), text(100, 555, 'передний наклон', 32, TXT, 800), text(100, 603, '85% мужчин', 34, A, 800), text(100, 650, '75% женщин', 34, A, 800),
           b.panel(555, 500, 455, 175), text(585, 555, 'задний наклон', 32, TXT, 800), text(585, 603, '6-7%', 34, A, 800), text(585, 650, 'Herrington 2011', 30, MUTED, 800)]
    norm = svg(W, 1350, *nm)
    # 4. три таза (блок 1080x864, картинка 1620x1296: панели y 230-950 в пикселях картинки)
    k = 1080 / 1620
    tri = [pill((i * 540 + 270) * k, 975 * k, n, A if i != 1 else SOFT, BG, 32, 'middle') for i, n in enumerate(('передний', 'нейтральный', 'задний'))]
    three = svg(W, 864, topfade(W, 200), *tri)
    # 5. тест у стены
    b5 = (W, 1026)
    wall = svg(*b5, topfade(W), arrow(*P(31, 71, *b5), *P(70.5, 83.5, *b5), A, 8, 30), pill(*P(3, 63, *b5), 'ладонь в просвете', A, BG, 32),
               pill(*P(66, 26, *b5), 'пятки, ягодицы,', BG, TXT, 30), pill(*P(66, 34, *b5), 'лопатки у стены', BG, TXT, 30))
    # 6. пара сил при заднем наклоне (схема -6, кадр y 330-1680 в 1080x1350)
    f = lambda x, y: (x, y - 640)
    pub, isch, aiis, psis6 = f(466, 1285), f(643, 1364), f(455, 1127), f(767, 1047)
    fc = [line(*pub, pub[0] - 25, pub[1] - 380, RED, 12), arrow(pub[0] - 12, pub[1] - 170, pub[0] - 20, pub[1] - 300, RED, 9, 30),
          line(*isch, 742, 768, RED, 12), arrow(isch[0] + 20, isch[1] + 4, isch[0] + 75, isch[1] + 28, RED, 9, 28),
          line(psis6[0] + 10, psis6[1] + 40, 705, 585, RED, 12),
          f'<path d="M600 150 Q450 420 640 680" fill="none" stroke="{BLUE}" stroke-width="10" stroke-dasharray="18 12" stroke-linecap="round" {b.SH}/>',
          line(psis6[0] - 15, psis6[1] - 40, 712, 40, BLUE, 10, '18 12'),
          pill(pub[0] - 50, pub[1] - 250, 'прямая мышца живота', RED, TXT, 30, 'end'),
          pill(1060, 600, 'двуглавая мышца бедра', RED, TXT, 30, 'end'), line(830, 650, 700, 748, RED, 4),
          pill(1060, 470, 'большая ягодичная', RED, TXT, 30, 'end'), line(800, 518, 745, 545, RED, 4),
          pill(430, 700, 'подвздошно-поясничная', BLUE, BG, 30, 'end'), line(430, 724, 628, 676, BLUE, 4),
          pill(1050, 200, 'выпрямляющая позвоночник', BLUE, BG, 30, 'end'),
          pill(40, 165, 'укорочены', RED, TXT, 30), pill(40, 230, 'ослаблены', BLUE, BG, 30), pill(40, 295, 'клиническая модель', BG, SOFT, 30)]
    force = svg(W, 891, topfade(W, 220), *fc)
    # 7. протокол Микаела (из базы, его слова)
    pr = [b.panel(60, 150, 960, 720), pill(100, 180, 'укрепляю', A, BG, 32), pill(560, 180, 'растягиваю', SOFT, BG, 32)]
    left = ['разгибание ног', 'сведение бёдер', 'становая тяга', '(гиперэкстензия)', 'тяга горизонтального', 'блока широким', 'хватом']
    nums_l = ['1', '2', '3', '', '4', '', '']
    for i, (n, sline) in enumerate(zip(nums_l, left)):
        y = 290 + i * 52
        pr += [text(100, y, n, 30, A, 800), text(135, y, sline, 30, TXT if n or i in (3, 5, 6) else TXT, 800)]
    right = [('5', 'проводки с палкой'), ('', '2 по 10'), ('6', 'собака мордой вниз'), ('7', 'кошка'), ('8', 'ягодичные'), ('9', 'наклоны'), ('10', 'икроножная')]
    for i, (n, sline) in enumerate(right):
        y = 290 + i * 52
        pr += [text(560, y, n, 30, SOFT, 800), text(605, y, sline, 30, TXT, 800)]
    proto = svg(W, 1350, *pr)
    # 8. добавлено по данным
    ad = [b.panel(60, 150, 960, 600), pill(100, 185, 'добавлено по данным', MUTED, BG, 30),
          text(100, 320, 'растяжка', 34, A, 800), text(100, 370, 'в программах до 8 недель растит', 32, TXT, 800),
          text(100, 415, 'терпимость к растяжению, а не длину', 32, TXT, 800), text(100, 462, 'Weppler, Magnusson 2010', 30, MUTED, 800),
          text(100, 560, 'сила мышц живота и длина', 34, A, 800), text(100, 610, 'сгибателей бедра объясняют угол', 32, TXT, 800), text(100, 655, 'таза слабо', 32, TXT, 800),
          text(100, 702, 'Walker 1987, Youdas 1996', 30, MUTED, 800)]
    added = svg(W, 1350, *ad)
    return [
        {'layout': 'photo-top', 'photoHeight': 66, 'big': True, 'photo': 'src/c8_cover.jpg', 'focus': '50% 50%', 'photo2': 'src/c8_cover_sch.jpg', 'focus2': '50% 45%',
         'title': 'Таз как ведро:\nкуда льётся вода?', 'body': 'Передний, нейтральный, задний наклон. Как отличить и что делать при заднем.', 'marks': [cover]},
        {'layout': 'photo-top', 'photoHeight': 62, 'photo': 'src/c8_neutral.jpg', 'focus': '50% 50%',
         'title': 'Ориентиры: две подвздошные ости', 'body': 'Передняя верхняя подвздошная ость прощупывается спереди на крыле таза, задняя верхняя под ямочками над крестцом. Угол между линией от задней ости к передней и горизонталью и есть наклон таза.', 'marks': [lm]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%',
         'title': 'Лёгкий передний наклон это норма', 'body': 'Молодые люди без боли. Средний угол: 9,6 градуса у мужчин, 11,7 у женщин (Medina McKeon, Hertel, 2009). Нейтраль по форме кости у всех разная (Preece, 2008), поэтому сравнивай себя с собой.', 'marks': [norm]},
        {'layout': 'photo-top', 'photoHeight': 64, 'photo': 'src/c8_three.jpg', 'focus': '50% 50%',
         'title': 'Сбоку: лордоз, живот, ягодицы', 'body': 'Передний наклон часто сочетается с усиленным поясничным лордозом: выступающий живот, ягодичная область отведена назад. Задний: лордоз сглажен, поясница плоская, ягодичная область уплощена.', 'marks': [three]},
        {'layout': 'photo-top', 'photoHeight': 76, 'photo': 'src/c8_wall.jpg', 'focus': '50% 50%',
         'title': 'Самотест у стены: лордоз', 'body': 'Больше ладони под поясницей: лордоз усилен. Ладонь не проходит: лордоз сглажен.', 'marks': [wall]},
        {'layout': 'photo-top', 'photoHeight': 66, 'photo': 'src/c8_force.jpg', 'focus': '50% 50%',
         'title': 'Задний наклон: у кого и почему', 'body': 'По моей практике чаще у активных: бег, прыжки, игровые виды, спорт с детства. Клиническая модель: укороченные мышцы тянут лобок вверх, а седалищный бугор вниз.', 'marks': [force]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%',
         'title': 'Мой протокол при заднем наклоне', 'body': 'Укрепляю ослабленные, растягиваю укороченные.', 'marks': [proto]},
        {'layout': 'big-number', 'photo': 'src/bg_grid.jpg', 'focus': '50% 50%',
         'title': 'Что добавляют данные', 'body': 'Протокол это не отменяет: он работает на силу, подвижность и контроль таза в движении.', 'marks': [added]},
        {'layout': 'cta-photo', 'photo': 'src/c8_cta.jpg', 'focus': '50% 50%',
         'title': 'Какой наклон у тебя?', 'body': 'Сделай тест у стены и напиши в комментариях: больше ладони, ладонь или меньше.'},
    ]


if __name__ == '__main__':
    if '--no-prep' not in sys.argv:
        prep()
    p = f'{DIR}/carousels.json'; d = json.load(open(p))
    new = slides()
    for c in d:
        if c['id'] == 'c8_naklon_taza':
            c['slides'] = new; break
    else:
        d.append({'id': 'c8_naklon_taza', 'slides': new})
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=2)
    json.dump([c for c in d if c['id'] == 'c8_naklon_taza'], open(f'{SP}/car/c8.json', 'w'), ensure_ascii=False)
    print('ok')
