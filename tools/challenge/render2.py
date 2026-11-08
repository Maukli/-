import subprocess, os, sys
B = os.path.dirname(os.path.abspath(__file__))
T = f'{B}/txt2'
F_TITLE = f'{B}/fonts/Rubik.ttf'
F_NAME = f'{B}/fonts/Oswald.ttf'
F_SYM = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
CROP = {'C025': 'crop=900:1600:0:20', 'C023': 'crop=900:1600:0:20', 'C026': 'crop=900:1600:58:20', 'C022': 'crop=900:1600:58:20'}
MASK = {'C025': 'mask_C023', 'C023': 'mask_C023', 'C026': 'mask_C024', 'C022': 'mask_C024'}
GRADE = ("hqdn3d=2:1.5:4:4,curves=master='0/0.04 0.25/0.25 0.5/0.56 0.78/0.86 1/0.98',"
         "colorbalance=rs=-0.04:gs=-0.01:bs=0.06:rm=0.02:gm=0:bm=-0.02:rh=0.06:gh=0.02:bh=-0.05,"
         "eq=saturation=0.92:contrast=1.04,unsharp=5:5:0.8:5:5:0.0")
CHECKS = {'ox': ('C026', [16.5, 22.0, 25.5, 36.0, 47.5]), 'mi': ('C025', [45.5, 56.5, 68.5, 91.5, 116.5])}
SEG = [
    ('C022', 54.0, 57.4, 1, None, None),
    ('C023', 46.6, 49.4, 1, None, None),
    ('C026', 6, 12, 3, 'ox', 'x3'), ('C026', 12, 18, 1, 'ox', None), ('C026', 18, 19.5, 2, 'ox', 'x2'),
    ('C026', 19.5, 23.5, 1, 'ox', None), ('C026', 23.5, 24.5, 2, 'ox', 'x2'), ('C026', 24.5, 29.5, 1, 'ox', None),
    ('C026', 29.5, 31, 2, 'ox', 'x2'), ('C026', 31, 37.5, 1, 'ox', None), ('C026', 37.5, 41, 3, 'ox', 'x3'),
    ('C026', 41, 48.5, 2, 'ox', 'x2'), ('C026', 48.5, 59.5, 2, 'ox', 'x2'),
    ('C025', 25, 42, 3, 'mi', 'x3'), ('C025', 42, 47, 1, 'mi', None), ('C025', 47, 52, 3, 'mi', 'x3'),
    ('C025', 52, 54, 1, 'mi', None), ('C025', 54, 58, 1, 'mi', None), ('C025', 58, 65, 3, 'mi', 'x3'),
    ('C025', 65, 67, 1, 'mi', None), ('C025', 67, 70.5, 1, 'mi', None), ('C025', 70.5, 90, 3, 'mi', 'x3'),
    ('C025', 90, 93, 1, 'mi', None), ('C025', 93, 108, 3, 'mi', 'x3'), ('C025', 108, 117.5, 2, 'mi', 'x2'),
    ('C025', 117.5, 121.5, 1, 'mi', None),
]
def dtext(fn, font, size, x, y, color='white', extra='', border=4):
    return f"drawtext=fontfile={font}:textfile={T}/{fn}:fontsize={size}:fontcolor={color}:x={x}:y={y}:borderw={border}:bordercolor=black@0.8{extra}"
lst = []
for i, (c, s, e, sp, who, badge) in enumerate(SEG):
    out = f'{B}/seg2/s{i:02d}.mp4'; lst.append(out)
    if os.path.exists(out) and '--force' not in sys.argv: continue
    dur = (e - s) / sp
    tx = [dtext('title.txt', F_TITLE, 78, '(w-text_w)/2', 1490)]
    if who:
        tx.append(dtext(f'n_{who}.txt', F_NAME, 54, '(w-text_w)/2', 1588, border=3))
        evs = CHECKS[who][1]
        for k, ev in enumerate(evs):
            y = 560 + k * 78
            if ev < s:
                done_from = 0.0
            elif ev < e:
                done_from = (ev - s) / sp
            else:
                done_from = None
            lab_dim = "fontcolor=white@0.55"
            if done_from is None:
                tx += [dtext(f'l{k}.txt', F_NAME, 44, 'w-200-text_w', y, 'white@0.55', border=2), dtext('circ.txt', F_SYM, 48, 'w-170', y - 2, 'white@0.55', border=2)]
            else:
                pre = f":enable='lt(t,{done_from:.2f})'"; post = f":enable='gte(t,{done_from:.2f})'"
                if done_from > 0:
                    tx += [dtext(f'l{k}.txt', F_NAME, 44, 'w-200-text_w', y, 'white@0.55', pre, 2), dtext('circ.txt', F_SYM, 48, 'w-170', y - 2, 'white@0.55', pre, 2)]
                tx += [dtext(f'l{k}.txt', F_NAME, 44, 'w-200-text_w', y, 'white', post, 2), dtext('chk.txt', F_SYM, 50, 'w-172', y - 4, '0x3DDC84', post, 3)]
                if done_from > 0:
                    pop = f":enable='between(t,{done_from:.2f},{done_from + 0.8:.2f})'"
                    tx.append(dtext('chk.txt', F_SYM, 230, '(w-text_w)/2', 1150, '0x3DDC84', pop, 8))
    if badge:
        tx.append(f"drawtext=fontfile={F_NAME}:textfile={T}/{badge}.txt:fontsize=56:fontcolor=black:x=50:y=1405:box=1:boxcolor=white@0.9:boxborderw=16")
    fc = (f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps=24000/1001,{CROP[c]},scale=1080:1920:flags=lanczos,{GRADE},format=gbrp,split=3[s][b][h];"
          f"[h]curves=all='0/0 0.72/0 1/1',gblur=sigma=25[hg];[b]gblur=sigma=9[bb];[1:v]format=gray[m];[s][m]alphamerge[sa];"
          f"[bb][sa]overlay=format=auto,format=gbrp[c];[c][hg]blend=all_mode=screen:all_opacity=0.35,vignette=angle=PI/5,format=yuv420p,noise=alls=5:allf=t,"
          f"{','.join(tx)}[v]")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/{c}.mp4', '-loop', '1', '-i', f'{B}/{MASK[c]}.png',
           '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-t', f'{dur:.3f}',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(i, c, s, e, sp, 'ok' if r.returncode == 0 else r.stderr[-600:], flush=True)
open(f'{B}/seg2/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in lst))
