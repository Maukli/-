import subprocess
from PIL import ImageFont
F = [('1', 'fonts2/SofiaXC.ttf'), ('2', 'fonts2/Unbounded.ttf'), ('3', 'fonts2/FiraXC.ttf'), ('4', 'fonts2/InterTight.ttf'),
     ('5', 'fonts2/Dela.ttf'), ('6', 'fonts2/Alumni.ttf'), ('7', 'fonts2/Montserrat.ttf'), ('0', 'fonts/Rubik.ttf')]
SYM = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def fit(font, text, width):
    s = 200
    while ImageFont.truetype(font, s).getbbox(text)[2] > width: s -= 2
    return s
def esc(t): return t.replace(':', '\\:')
outs = []
for lab, font in F:
    ts, ns, ag, ls = fit(font, 'НОВЫЙ ЧЕЛЛЕНДЖ', 800), fit(font, 'OXMEDO', 330), fit(font, '15 ЛЕТ', 170), fit(font, 'СИДЯ', 120)
    st = ':borderw=2:bordercolor=black@0.55:shadowcolor=black@0.45:shadowx=0:shadowy=5'
    d = [f"drawtext=fontfile={font}:text='НОВЫЙ ЧЕЛЛЕНДЖ':fontsize={ts}:fontcolor=white:x=(w-text_w)/2:y=1415{st}",
         f"drawtext=fontfile={font}:text='OXMEDO':fontsize={ns}:fontcolor=white:x=(w-text_w)/2:y=1415+{int(ts*1.15)}{st}",
         f"drawtext=fontfile={font}:text='15 ЛЕТ':fontsize={ag}:fontcolor=white@0.9:x=(w-text_w)/2:y=1415+{int(ts*1.15)+int(ns*1.15)}{st}"]
    for k, (l, done) in enumerate([('ЛЁЖА', 1), ('СИДЯ', 1), ('СТОЯ', 0)]):
        y = 560 + k * 78
        d.append(f"drawtext=fontfile={font}:text='{l}':fontsize={ls}:fontcolor=white{'' if done else '@0.55'}:x=w-200-text_w:y={y}{st}")
        d.append(f"drawtext=fontfile={SYM}:text='{'✔' if done else '○'}':fontsize=50:fontcolor={'0x3DDC84' if done else 'white@0.55'}:x=w-172:y={y-4}{st}")
    d.append(f"crop=1080:1300:0:480,scale=432:-1,drawtext=fontfile={SYM}:text='{lab}':fontsize=44:fontcolor=yellow:x=12:y=10:box=1:boxcolor=black@0.7:boxborderw=8")
    o = f'gt/font_{lab}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'gt/B_C026_25.0_j.png', '-vf', ','.join(d), o], check=True)
    outs.append(o)
args = []
for o in outs: args += ['-i', o]
subprocess.run(['ffmpeg', '-v', 'error', '-y', *args, '-filter_complex', f"{''.join(f'[{i}]' for i in range(len(outs)))}xstack=inputs={len(outs)}:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0", 'gt/fontsheet.png'], check=True)
print('ok')
