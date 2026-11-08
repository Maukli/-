# Челлендж-рилс v4 (08.11). Запуск: python3 render4.py
# Цвет берётся из кэша v3 (seg3/g*.mp4, считает render3.py grade). Здесь только надписи, ник Instagram и финальный файл.
# Шрифты (Google Fonts) в fonts2/: Bebas Neue (заголовок, чек-лист, метки, ник в значке), Permanent Marker (имя).
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textpng import text_png
B = os.path.dirname(os.path.abspath(__file__))
T = f'{B}/txt4'
HI = '4k60' in sys.argv  # 4K 60 кадров: цвет с дорисованными кадрами из seg60 (interp60.py), увеличение до 2160x3840 в финале
G = f'{B}/seg60' if HI else f'{B}/seg3'   # готовый цвет
OUT = f'{B}/seg4k60' if HI else f'{B}/seg4'
F_LAB = f'{B}/fonts2/Bebas.ttf'
F_SYM = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
YELLOW = (255, 210, 31)
# Всё на английском (решение 08.11). На экране только NEW CHALLENGE и ник, без возраста и веса.
# Стиль B с жёлтым заголовком (выбор Микаела 08.11): NEW CHALLENGE Bebas Neue жёлтым с разрядкой, ник маркером Permanent Marker белым.
TITLE = ('NEW CHALLENGE', f'{B}/fonts2/Bebas.ttf', 150, YELLOW, 10)
NAMES = {'ox': ('OXMEDO', f'{B}/fonts2/Marker.ttf', 92, (255, 255, 255), 2), 'mi': ('MIKO', f'{B}/fonts2/Marker.ttf', 92, (255, 255, 255), 2)}
TITLE_Y = 1330
WM_STEP = 6
WM_POS = [('60', '1050'), ('W-w-60', '330'), ('60', '520'), ('W-w-60', '1000')]
CHECKS = {'ox': [17.3, 22.9, 27.7, 35.4, 45.3], 'mi': [48.4, 61.4, 76.2, 91.1, 114.2]}
# Те же куски, что в v3, без концовки (индексы совпадают с seg3/g*.mp4).
SEG = [
    ('C022', 54.0, 57.4, 1, None, None),
    ('C023', 46.6, 49.4, 1, None, None),
    ('C026', 6, 14.6, 3, 'ox', 'x3'), ('C026', 14.6, 18.2, 1, 'ox', None), ('C026', 18.2, 21.2, 2, 'ox', 'x2'),
    ('C026', 21.2, 23.7, 1, 'ox', None), ('C026', 23.7, 25.5, 2, 'ox', 'x2'), ('C026', 25.5, 28.5, 1, 'ox', None),
    ('C026', 28.5, 32.8, 2, 'ox', 'x2'), ('C026', 32.8, 36.2, 1, 'ox', None), ('C026', 36.2, 42.8, 3, 'ox', 'x3'),
    ('C026', 42.8, 46.1, 1, 'ox', None), ('C026', 46.1, 59.5, 2, 'ox', 'x2'),
    ('C025', 25, 43.2, 3, 'mi', 'x3'), ('C025', 43.2, 49.2, 1, 'mi', None), ('C025', 49.2, 57.4, 3, 'mi', 'x3'),
    ('C025', 57.4, 62.2, 1, 'mi', None), ('C025', 62.2, 71.6, 3, 'mi', 'x3'), ('C025', 71.6, 77.0, 1, 'mi', None),
    ('C025', 77.0, 84.4, 3, 'mi', 'x3'), ('C025', 84.4, 88.6, 2, 'mi', 'x2'), ('C025', 88.6, 91.9, 1, 'mi', None),
    ('C025', 91.9, 95.5, 3, 'mi', 'x3'), ('C025', 95.5, 109.4, 4, 'mi', 'x4'), ('C025', 109.4, 115.0, 1, 'mi', None),
    ('C025', 115.0, 117.0, 2, 'mi', 'x2'), ('C025', 117.0, 120.6, 1, 'mi', None),
]
WM_OWNER = {'C022': 'ox', 'C026': 'ox', 'C023': 'mi', 'C025': 'mi'}

os.makedirs(OUT, exist_ok=True)
title_img = text_png(*TITLE, out=f'{OUT}/title.png')
NAME_Y = {}
for k, v in NAMES.items():
    im = text_png(*v, out=f'{OUT}/name_{k}.png')
    NAME_Y[k] = TITLE_Y + title_img.height - int(im.height * 0.22)  # роспись слегка заходит на заголовок


def dtext(fn, font, size, x, y, color='white', extra='', border=0):
    return (f"drawtext=fontfile={font}:textfile={T}/{fn}:fontsize={size}:fontcolor={color}:x={x}:y={y}:borderw={border}:bordercolor=black@0.5"
            f":shadowcolor=black@0.5:shadowx=0:shadowy=4{extra}")


def checklist(s, e, sp, who):
    tx = ["drawbox=x=iw-400:y=535:w=360:h=410:color=black@0.30:t=fill"]
    for k, ev in enumerate(CHECKS[who]):
        y = 560 + k * 78
        done_from = 0.0 if ev < s else ((ev - s) / sp if ev < e else None)
        dim = [dtext(f'l{k}.txt', F_LAB, 58, 'w-200-text_w', y, 'white@0.68'), dtext('circ.txt', F_SYM, 46, 'w-170', y + 2, 'white@0.68')]
        if done_from is None:
            tx += dim
            continue
        pre, post = f":enable='lt(t,{done_from:.2f})'", f":enable='gte(t,{done_from:.2f})'"
        if done_from > 0:
            tx += [dtext(f'l{k}.txt', F_LAB, 58, 'w-200-text_w', y, 'white@0.68', pre), dtext('circ.txt', F_SYM, 46, 'w-170', y + 2, 'white@0.68', pre)]
        tx += [dtext(f'l{k}.txt', F_LAB, 58, 'w-200-text_w', y, 'white', post), dtext('chk.txt', F_SYM, 48, 'w-172', y, '0x3DDC84', post)]
    return tx


def render(i):
    c, s, e, sp, who, badge = SEG[i]
    src, out = f'{G}/g{i:02d}.mp4', f'{OUT}/s{i:02d}.mp4'
    ins = ['-i', src, '-loop', '1', '-i', f'{OUT}/title.png']
    fc = f"[0:v][1:v]overlay=x=(W-w)/2:y={TITLE_Y}:shortest=1[a0]"
    last, n = 'a0', 2
    if who:
        ins += ['-loop', '1', '-i', f'{OUT}/name_{who}.png']
        fc += f";[{last}][{n}:v]overlay=x=(W-w)/2:y={NAME_Y[who]}:shortest=1[a1]"
        last, n = 'a1', n + 1
    tx = checklist(s, e, sp, who) if who else []
    if badge:
        tx.append(f"drawtext=fontfile={F_LAB}:textfile={T}/{badge}.txt:fontsize=66:fontcolor=black:x=50:y=1240:box=1:boxcolor=white@0.9:boxborderw=12")
    fc += f";[{last}]{','.join(tx) if tx else 'null'}[v]"
    cmd = ['ffmpeg', '-v', 'error', '-y', *ins, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc,
           '-map', '[v]', '-map', f'{n}:a', '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '128k', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, ('ok' if r.returncode == 0 else r.stderr[-800:])


def dur_of(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


def pos_expr(k):
    idx = f'mod(floor(t/{WM_STEP}),{len(WM_POS)})'
    e = WM_POS[-1][k]
    for j in range(len(WM_POS) - 2, -1, -1):
        e = f'if(eq({idx},{j}),{WM_POS[j][k]},{e})'
    return e


if __name__ == '__main__':
    if '--final' in sys.argv:  # надписи уже наложены, пересобрать только финал
        res = [(f'{OUT}/s{i:02d}.mp4', 'ok') for i in range(len(SEG))]
    else:
        with ThreadPoolExecutor(max_workers=4) as ex:
            res = list(ex.map(render, range(len(SEG))))
    for i, (p, st) in enumerate(res):
        if st != 'ok':
            print('fail', i, st); sys.exit(1)
    parts = [p for p, _ in res]
    open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
    spans, t0 = {'ox': [], 'mi': []}, 0.0
    for i, p in enumerate(parts):
        d = dur_of(p)
        spans[WM_OWNER[SEG[i][0]]].append((t0, t0 + d))
        t0 += d
    en = {k: '+'.join(f'gte(t,{a:.3f})*lt(t,{b:.3f})' for a, b in v) for k, v in spans.items()}
    final = f'{B}/challenge_v4_4k60.mp4' if HI else f'{B}/challenge_v4.mp4'
    # Сглаживание полос на тёмных градиентах (потолок) и тонкое зерно поверх, чтобы ступеньки не вернулись при сжатии.
    up = (',scale=2160:3840:flags=lanczos,unsharp=5:5:0.35:5:5:0.0,noise=alls=3:allf=t' if HI else ',noise=alls=2:allf=t')
    fc = (f"[1:v]format=rgba[wo];[2:v]format=rgba[wi];[0:v]deband=1thr=0.03:2thr=0.03:3thr=0.03:range=22:blur=1[d0];"
          f"[d0][wo]overlay=x='{pos_expr(0)}':y='{pos_expr(1)}':enable='{en['ox']}':shortest=1:format=auto[v1];"
          f"[v1][wi]overlay=x='{pos_expr(0)}':y='{pos_expr(1)}':enable='{en['mi']}':shortest=1:format=auto{up},format=yuv420p[v]")
    enc = (['-c:v', 'libx265', '-preset', 'fast', '-crf', '19', '-x265-params', 'vbv-maxrate=35000:vbv-bufsize=70000:aq-mode=3:log-level=error',
            '-tag:v', 'hvc1'] if HI else
           ['-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M', '-tune', 'grain', '-aq-mode', '3'])
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt',
                    '-loop', '1', '-i', f'{B}/wm_ox.png', '-loop', '1', '-i', f'{B}/wm_mi.png', '-filter_complex', fc,
                    '-map', '[v]', '-map', '0:a', *enc, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', final], check=True)
    print('final', final, dur_of(final))
