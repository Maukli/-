# Челлендж-рилс v3 (08.11). Запуск: python3 render3.py [--force]
# Исходники в raw/ (C022-C026 с папки на Диске), шрифт fonts2/SofiaXC.ttf (Google Fonts: Sofia Sans Extra Condensed, Black Italic), маски mask_C023.png и mask_C024.png.
# "python3 render3.py grade" считает только цвет; без аргумента: цвет из кэша, надписи, переход, финальный файл.
import subprocess, os, sys
from concurrent.futures import ThreadPoolExecutor
B = os.path.dirname(os.path.abspath(__file__))
T = f'{B}/txt3'
OUT = f'{B}/seg3'
# Шрифт v3: Sofia Sans Extra Condensed Black Italic (Google Fonts, кириллица). Тонкая обводка и мягкая тень вместо толстого контура.
F_TITLE = f'{B}/fonts2/SofiaXC.ttf'
F_NAME = f'{B}/fonts2/SofiaXC.ttf'
F_SYM = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CROP = {'C025': 'crop=900:1600:0:20', 'C023': 'crop=900:1600:0:20', 'C026': 'crop=900:1600:58:20', 'C022': 'crop=900:1600:58:20'}
MASK = {'C025': 'mask_C023', 'C023': 'mask_C023', 'C026': 'mask_C024', 'C022': 'mask_C024'}
# Цвет как в v2 (тил-оранж), плюс детализация через ткань: подняты глубокие тени,
# локальный контраст по яркости (крупный радиус для рельефа, мелкий для фактуры), слабее шумодав.
CB = "colorbalance=rs=-0.02:gs=-0.005:bs=0.03:rm=0.02:gm=0:bm=-0.02:rh=0.06:gh=0.02:bh=-0.05"
# Яркость подняли по просьбе Микаела (пример светлее): средняя яркость кадра около 80 из 255 вместо 36,
# чёрная точка осталась на месте, чтобы картинка не стала молочной. Свечение и виньетка слабее.
GRADE = ("hqdn3d=1.5:1.2:3.5:3.5,curves=master='0/0.015 0.04/0.11 0.12/0.30 0.3/0.56 0.55/0.80 0.8/0.95 1/1',"
         f"{CB},eq=saturation=1.0:contrast=1.03,format=yuv444p,split=3[ca][cb][cc];"
         "[cb]gblur=sigma=10[cbb];[cc]gblur=sigma=3[ccb];"
         "[ca][cbb]blend=c0_expr='clip(A+0.6*(A-B),0,255)':c1_expr=A:c2_expr=A[cd];"
         "[cd][ccb]blend=c0_expr='clip(A+0.28*(A-B),0,255)':c1_expr=A:c2_expr=A,unsharp=3:3:0.3:3:3:0.0[g]")
GLOW, VIGNETTE = 0.22, 'PI/14'
# Значок Instagram с ником всё время в кадре, место меняется каждые WM_STEP секунд (как в примере, и от перезаливов).
WM_STEP = 6
WM_POS = [('60', '1050'), ('W-w-60', '330'), ('60', '520'), ('W-w-60', '1000')]
# Галочка через 0,2 с после того, как рука выпрямилась в конце жима (размечено по кадрам).
CHECKS = {'ox': [17.3, 22.9, 27.7, 35.4, 45.3], 'mi': [48.4, 61.4, 76.2, 91.1, 114.2]}
# (клип, начало, конец, ускорение, кто, метка). Жимы в реальной скорости, переходы ускорены.
SEG = [
    ('C022', 54.0, 57.4, 1, None, None),     # хук: срыв oxmedo
    ('C023', 46.6, 49.4, 1, None, None),     # хук: срыв miko
    ('C026', 6, 14.6, 3, 'ox', 'x3'), ('C026', 14.6, 18.2, 1, 'ox', None), ('C026', 18.2, 21.2, 2, 'ox', 'x2'),
    ('C026', 21.2, 23.7, 1, 'ox', None), ('C026', 23.7, 25.5, 2, 'ox', 'x2'), ('C026', 25.5, 28.5, 1, 'ox', None),
    ('C026', 28.5, 32.8, 2, 'ox', 'x2'), ('C026', 32.8, 36.2, 1, 'ox', None), ('C026', 36.2, 42.8, 3, 'ox', 'x3'),
    ('C026', 42.8, 46.1, 1, 'ox', None), ('C026', 46.1, 59.5, 2, 'ox', 'x2'),
    ('C025', 25, 43.2, 3, 'mi', 'x3'), ('C025', 43.2, 49.2, 1, 'mi', None), ('C025', 49.2, 57.4, 3, 'mi', 'x3'),
    ('C025', 57.4, 62.2, 1, 'mi', None), ('C025', 62.2, 71.6, 3, 'mi', 'x3'), ('C025', 71.6, 77.0, 1, 'mi', None),
    ('C025', 77.0, 84.4, 3, 'mi', 'x3'), ('C025', 84.4, 88.6, 2, 'mi', 'x2'), ('C025', 88.6, 91.9, 1, 'mi', None),
    ('C025', 91.9, 95.5, 3, 'mi', 'x3'), ('C025', 95.5, 109.4, 4, 'mi', 'x4'), ('C025', 109.4, 115.0, 1, 'mi', None),
    ('C025', 115.0, 117.0, 2, 'mi', 'x2'), ('C025', 117.0, 120.6, 1, 'mi', None),
    ('C023', 157.9, 161.3, 1, 'end', None),  # хлопают друг друга по спине, без надписей
]
XFADE = 0.6  # плавный переход в концовку


def dtext(fn, font, size, x, y, color='white', extra='', border=2):
    return (f"drawtext=fontfile={font}:textfile={T}/{fn}:fontsize={size}:fontcolor={color}:x={x}:y={y}:borderw={border}:bordercolor=black@0.55"
            f":shadowcolor=black@0.45:shadowx=0:shadowy=5{extra}")


def texts(s, e, sp, who, badge):
    if who == 'end':
        return []
    tx = [dtext('title.txt', F_TITLE, 112, '(w-text_w)/2', 1380)]
    if who:
        tx.append(dtext(f'n_{who}.txt', F_NAME, 84, '(w-text_w)/2', 1505))
        tx.append(dtext(f's_{who}.txt', F_NAME, 56, '(w-text_w)/2', 1600, 'white@0.92'))
        tx.append("drawbox=x=iw-330:y=535:w=300:h=410:color=black@0.30:t=fill")
        for k, ev in enumerate(CHECKS[who]):
            y = 560 + k * 78
            done_from = 0.0 if ev < s else ((ev - s) / sp if ev < e else None)
            if done_from is None:
                tx += [dtext(f'l{k}.txt', F_NAME, 54, 'w-200-text_w', y, 'white@0.68', border=2),
                       dtext('circ.txt', F_SYM, 48, 'w-170', y - 2, 'white@0.68', border=2)]
                continue
            pre = f":enable='lt(t,{done_from:.2f})'"
            post = f":enable='gte(t,{done_from:.2f})'"
            if done_from > 0:
                tx += [dtext(f'l{k}.txt', F_NAME, 54, 'w-200-text_w', y, 'white@0.68', pre, 2),
                       dtext('circ.txt', F_SYM, 48, 'w-170', y - 2, 'white@0.68', pre, 2)]
            tx += [dtext(f'l{k}.txt', F_NAME, 54, 'w-200-text_w', y, 'white', post, 2),
                   dtext('chk.txt', F_SYM, 50, 'w-172', y - 4, '0x3DDC84', post, 3)]
            if done_from > 0:
                pop = f":enable='between(t,{done_from:.2f},{done_from + 0.8:.2f})'"
                tx.append(dtext('chk.txt', F_SYM, 230, '(w-text_w)/2', 1150, '0x3DDC84', pop, 8))
    if badge:
        tx.append(f"drawtext=fontfile={F_NAME}:textfile={T}/{badge}.txt:fontsize=64:fontcolor=black:x=50:y=1270:box=1:boxcolor=white@0.9:boxborderw=14")
    return tx


def grade(i):
    # Этап 1: цвет, детализация, размытие фона. Без надписей, считается один раз.
    c, s, e, sp, who, badge = SEG[i]
    out = f'{OUT}/g{i:02d}.mp4'
    if os.path.exists(out) and '--regrade' not in sys.argv:
        return out, 'cached'
    dur = (e - s) / sp
    fc = (f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps=24000/1001,{CROP[c]},scale=1080:1920:flags=lanczos,{GRADE};"
          f"[g]format=gbrp,split=3[s][b][h];"
          f"[h]curves=all='0/0 0.72/0 1/1',gblur=sigma=25[hg];[b]gblur=sigma=9[bb];[1:v]format=gray[m];[s][m]alphamerge[sa];"
          f"[bb][sa]overlay=format=auto,format=gbrp[c];[c][hg]blend=all_mode=screen:all_opacity={GLOW},vignette=angle={VIGNETTE},"
          f"format=yuv420p,noise=alls=3:allf=t[v]")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/{c}.mp4', '-loop', '1', '-i', f'{B}/{MASK[c]}.png',
           '-filter_complex', fc, '-map', '[v]', '-t', f'{dur:.3f}', '-an',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out + '.part.mp4']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        os.replace(out + '.part.mp4', out)
    return out, ('ok' if r.returncode == 0 else r.stderr[-800:])


def render(i):
    # Этап 2: надписи поверх готового цвета. Быстро, шрифт можно менять без пересчёта цвета.
    c, s, e, sp, who, badge = SEG[i]
    src, out = f'{OUT}/g{i:02d}.mp4', f'{OUT}/s{i:02d}.mp4'
    tx = texts(s, e, sp, who, badge)
    vf = ','.join(tx) if tx else 'null'
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', src, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-vf', vf,
           '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '128k', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return out, ('ok' if r.returncode == 0 else r.stderr[-800:])


def dur_of(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


os.makedirs(OUT, exist_ok=True)
with ThreadPoolExecutor(max_workers=4) as ex:
    gres = list(ex.map(grade, range(len(SEG))))
for i, (p, st) in enumerate(gres):
    if st not in ('ok', 'cached'):
        print('grade fail', i, st); sys.exit(1)
print('grade done', flush=True)
if 'grade' in sys.argv:
    sys.exit(0)
with ThreadPoolExecutor(max_workers=4) as ex:
    res = list(ex.map(render, range(len(SEG))))
for i, (p, st) in enumerate(res):
    print(i, SEG[i][:4], st, flush=True)
    if st not in ('ok', 'cached'):
        sys.exit(1)
# Последний сегмент miko + концовка: плавный переход.
a, b = res[-2][0], res[-1][0]
joined = f'{OUT}/end_xfade.mp4'
off = dur_of(a) - XFADE
tot = dur_of(a) + dur_of(b) - XFADE
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a, '-i', b, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                '-filter_complex', f'[0:v][1:v]xfade=transition=fade:duration={XFADE}:offset={off:.3f},format=yuv420p[v]',
                '-map', '[v]', '-map', '2:a', '-t', f'{tot:.3f}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                '-c:a', 'aac', '-b:a', '128k', joined], check=True)
parts = [p for p, _ in res[:-2]] + [joined]
open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
print('list ready', len(parts))


def pos_expr(k):
    idx = f'mod(floor(t/{WM_STEP}),{len(WM_POS)})'
    e = WM_POS[-1][k]
    for i in range(len(WM_POS) - 2, -1, -1):
        e = f'if(eq({idx},{i}),{WM_POS[i][k]},{e})'
    return e


# Чей ник в кадре: на частях oxmedo (C022, C026) его аккаунт, на частях miko и в концовке @miko_oloo.
WM_OWNER = {'C022': 'ox', 'C026': 'ox', 'C023': 'mi', 'C025': 'mi'}
spans, t0 = {'ox': [], 'mi': []}, 0.0
for p in parts:
    d = dur_of(p)
    c = SEG[int(os.path.basename(p)[1:3])][0] if os.path.basename(p).startswith('s') else 'C025'
    spans[WM_OWNER[c]].append((t0, t0 + d))
    t0 += d
en = {k: '+'.join(f'gte(t,{a:.3f})*lt(t,{b:.3f})' for a, b in v) for k, v in spans.items()}
final = f'{B}/challenge_v3.mp4'
fc = (f"[1:v]format=rgba[wo];[2:v]format=rgba[wi];"
      f"[0:v][wo]overlay=x='{pos_expr(0)}':y='{pos_expr(1)}':enable='{en['ox']}':shortest=1:format=auto[v1];"
      f"[v1][wi]overlay=x='{pos_expr(0)}':y='{pos_expr(1)}':enable='{en['mi']}':shortest=1:format=auto,format=yuv420p[v]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt',
                '-loop', '1', '-i', f'{B}/wm_ox.png', '-loop', '1', '-i', f'{B}/wm_mi.png', '-filter_complex', fc,
                '-map', '[v]', '-map', '0:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M',
                '-tune', 'grain', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', final], check=True)
print('final', final, dur_of(final))
