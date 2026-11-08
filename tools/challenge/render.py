import subprocess, os, sys
B = os.path.dirname(os.path.abspath(__file__))
FONT = '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'
FONT2 = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
CROP = {'C023': 'crop=900:1600:0:20', 'C024': 'crop=900:1600:58:20'}
ENH = 'hqdn3d=1.5:1.5:4:4,eq=contrast=1.10:brightness=0.02:gamma=1.03,unsharp=5:5:0.9:5:5:0.0'
# (clip, start, end, speed, who, badge, end_card)
SEG = [
    ('C024', 58.6, 61.8, 1, None, None, False),
    ('C023', 46.6, 49.4, 1, None, None, False),
    ('C024', 64, 76, 3, 'ox', 'x3', False),
    ('C024', 76, 80, 1, 'ox', None, False),
    ('C024', 80, 83, 2, 'ox', 'x2', False),
    ('C024', 83, 88.5, 1, 'ox', None, False),
    ('C024', 88.5, 90, 2, 'ox', 'x2', False),
    ('C024', 90, 96.5, 1, 'ox', None, False),
    ('C024', 96.5, 99, 2, 'ox', 'x2', False),
    ('C024', 101, 106, 1, 'ox', None, False),
    ('C024', 106, 118, 3, 'ox', 'x3', False),
    ('C024', 118, 121, 1, 'ox', None, False),
    ('C023', 88, 103, 3, 'mi', 'x3', False),
    ('C023', 103, 111, 1, 'mi', None, False),
    ('C023', 111, 114, 2, 'mi', 'x2', False),
    ('C023', 114, 121, 1, 'mi', None, False),
    ('C023', 121, 131, 2, 'mi', 'x2', False),
    ('C023', 131, 137, 1, 'mi', None, False),
    ('C023', 137, 156, 3, 'mi', 'x3', False),
    ('C023', 156, 161, 1, 'mi', None, True),
]
def dt(f, size, y, font=FONT, x='(w-text_w)/2', extra=''):
    return f"drawtext=fontfile={font}:textfile={B}/txt/{f}:fontsize={size}:fontcolor=white:x={x}:y={y}:borderw=4:bordercolor=black@0.85{extra}"
os.makedirs(f'{B}/seg', exist_ok=True)
lst = []
for i, (c, s, e, sp, who, badge, endc) in enumerate(SEG):
    out = f'{B}/seg/s{i:02d}.mp4'; lst.append(out)
    if os.path.exists(out) and '--force' not in sys.argv: continue
    hide = f":enable='lt(t,{max(0,(e-s)/sp-3.6):.2f})'" if endc else ''
    texts = [dt('title.txt', 76, 1500, extra=hide)]
    if who:
        texts += [dt(f'n_{who}.txt', 54, 1592, font=FONT2, extra=hide)]
    if badge:
        texts += [f"drawtext=fontfile={FONT}:textfile={B}/txt/{badge}.txt:fontsize=58:fontcolor=black:x=50:y=1405:box=1:boxcolor=white@0.9:boxborderw=18"]
    if endc:
        d = (e - s) / sp; t0 = max(0, d - 3.6)
        en = f":enable='gte(t,{t0:.2f})'"
        texts += [f"drawbox=x=0:y=170:w=iw:h=340:color=black@0.6:t=fill{en}",
                  dt('end1.txt', 100, 195, extra=en), dt('end2.txt', 54, 325, font=FONT2, extra=en), dt('end3.txt', 36, 415, font=FONT2, extra=en)]
    fc = (f"[0:v]setpts=(PTS-STARTPTS)/{sp},fps=24000/1001,{CROP[c]},scale=1080:1920:flags=lanczos,{ENH},split[s][b];"
          f"[b]gblur=sigma=9[bb];[1:v]format=gray[m];[s][m]alphamerge[sa];[bb][sa]overlay=format=auto,format=yuv420p,{','.join(texts)}[v]")
    dur = (e - s) / sp
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/{c}.mp4', '-loop', '1', '-i', f'{B}/mask_{c}.png',
           '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-t', f'{dur:.3f}',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(i, c, s, e, sp, 'ok' if r.returncode == 0 else r.stderr[-800:], flush=True)
open(f'{B}/seg/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in lst))
