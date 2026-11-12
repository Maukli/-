# Черновой монтаж рилса "Живот выпирает, хотя жира мало" (12.11).
# Голоса ещё нет: субтитрами идёт будущий текст голоса, по нему видно, какой кадр под какой фразой.
# Когда придёт голос, длины кадров подгоняются под реальные фразы (BLOCKS), и субтитры ставятся по голосу.
# Запуск: python3 render_posture.py  (исходники в raw/, фото в photos/)
import subprocess, os, sys, textwrap
B = os.path.dirname(os.path.abspath(__file__))
OUT = f'{B}/seg'
FONT = f'{B}/../challenge/fonts/Oswald.ttf'
YEL = '0xFFD21F'
GRADE = ("eq=contrast=1.05:saturation=0.96:brightness=0.01,"
         "colorbalance=rs=-0.02:bs=0.02:rh=0.04:bh=-0.03,unsharp=5:5:0.5:5:5:0.0,vignette=angle=PI/6,noise=alls=2:allf=t")
ZOOM_9673 = 'crop=675:1200:172:500,'  # дальний план 9673 приблизить: торс и таз сбоку

def clip(n, s, e, pre=''):
    return ('clip', n, s, e, pre)

def still(n, dur):
    return ('still', n, dur)

# Блоки: текст голоса (фразы через |), кадры, надписи на экране (текст, начало и конец внутри блока, крупно или нет)
BLOCKS = [
    ("Жира мало, а живот всё равно выпирает?|Первая мысль: качать пресс.|Не поможет.",
     [clip('9675', 0.0, 2.6), clip('9691', 2.5, 5.5)], []),
    ("Часто дело в переднем наклоне таза.|Поясница прогибается, и живот выходит вперёд.",
     [clip('9673', 0.3, 5.3, ZOOM_9673)], []),
    ("В исследовании 1996 года у мужчин сила пресса с углом таза не была связана совсем.|А в эксперименте 1997 года пресс стал сильнее,|а угол таза остался прежним.",
     [clip('9671', 0.0, 4.6), still('IMG_9700', 2.7), clip('9672', 0.0, 3.5)],
     [("1996: ПРЕСС И ТАЗ НЕ СВЯЗАНЫ", 0.2, 4.6), ("1997: ПРЕСС СИЛЬНЕЕ, ТАЗ ТОТ ЖЕ", 5.0, 10.6)]),
    ("И это не болезнь.|Лёгкий передний наклон нашли у 85% здоровых мужчин.|Просто на сушке, когда уходит жир, его становится видно.",
     [clip('9674', 0.0, 5.0), clip('9675', 3.0, 6.9)], [("85% ЗДОРОВЫХ МУЖЧИН", 1.0, 5.0)]),
    ([("Поэтому я начинаю не с живота, а с шеи.", 0.0, 3.0), ("Мой протокол идёт сверху вниз. Шея.", 3.0, 6.0), ("Лопатки.", 6.0, 8.5),
      ("Через 2 недели поясница и бицепс бедра.", 8.5, 11.0), ("Ягодичные.", 11.0, 12.6), ("Стопа.", 12.6, 14.2),
      ("Растяжка.", 14.2, 16.6), ("И только в конце пресс.", 16.6, 18.8)],
     [clip('9667', 6.0, 9.0), clip('9668', 3.0, 6.0), clip('9679', 14.0, 15.5), clip('9680', 3.0, 4.0),
      clip('9681', 9.0, 11.5), clip('9689', 13.0, 14.6), clip('9687', 3.0, 4.6), clip('9690', 14.5, 15.9), clip('9688', 4.5, 5.5),
      clip('9691', 11.5, 13.7)],
     [("1. ШЕЯ", 0.0, 6.0), ("2. ЛОПАТКИ", 6.0, 8.5), ("3. ПОЯСНИЦА И БИЦЕПС БЕДРА", 8.5, 11.0), ("4. ЯГОДИЧНЫЕ", 11.0, 12.6),
      ("5. СТОПА", 12.6, 14.2), ("6. РАСТЯЖКА", 14.2, 16.6), ("7. ПРЕСС", 16.6, 18.8)]),
    ("Проверить свой таз за 30 секунд:|пиши в комментариях ОСАНКА.",
     [clip('9673', 11.5, 15.9)], [("ОСАНКА", 1.6, 4.4)]),
]


def render_shot(i, sh):
    out = f'{OUT}/s{i:02d}.mp4'
    if os.path.exists(out) and '--force' not in sys.argv:
        return out, None
    if sh[0] == 'clip':
        _, n, s, e, pre = sh
        src = f'{B}/raw/IMG_{n} (1).MOV'
        vf = f"{pre}scale=1080:1920:flags=lanczos,fps=30,{GRADE},format=yuv420p"
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-to', str(e), '-i', src, '-vf', vf, '-an',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', out]
        dur = e - s
    else:
        _, n, dur = sh
        frames = int(dur * 30)
        vf = (f"crop=2268:4032:378:0,scale=2160:3840,zoompan=z='1+0.0015*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,"
              f"{GRADE},format=yuv420p")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', f'{B}/photos/{n}.jpg', '-vf', vf, '-frames:v', str(frames), '-an',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(i, sh, r.stderr[-600:]); sys.exit(1)
    return out, dur


def dur_of(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


os.makedirs(OUT, exist_ok=True)
os.makedirs(f'{B}/txt', exist_ok=True)
parts, draws, t0, k, n_txt = [], [], 0.0, 0, 0
for text, shots, labels in BLOCKS:
    start = t0
    for sh in shots:
        p, _ = render_shot(k, sh); k += 1
        parts.append(p); t0 += dur_of(p)
    bd = t0 - start
    # субтитры: фразы делят блок по числу слов
    if isinstance(text, list):  # фразы с заданным временем (под надписи шагов)
        timed = [(ph, start + a, min(b, bd) - a) for ph, a, b in text]
    else:
        phrases = text.split('|')
        words = [len(p.split()) for p in phrases]
        timed, acc = [], start
        for ph, w in zip(phrases, words):
            timed.append((ph, acc, bd * w / sum(words))); acc += bd * w / sum(words)
    for ph, tt, d in timed:
        f = f'{B}/txt/t{n_txt:02d}.txt'; n_txt += 1
        open(f, 'w').write('\n'.join(textwrap.wrap(ph, 26)))
        draws.append(f"drawtext=fontfile={FONT}:expansion=none:textfile={f}:fontsize=62:fontcolor=white:text_align=C:line_spacing=10"
                     f":x=(w-text_w)/2:y=1380:borderw=3:bordercolor=black@0.55:shadowcolor=black@0.5:shadowx=0:shadowy=4"
                     f":enable='between(t,{tt:.2f},{tt + d - 0.04:.2f})'")
    for lab, a, b in labels:
        f = f'{B}/txt/t{n_txt:02d}.txt'; n_txt += 1
        open(f, 'w').write(lab)
        big = lab == 'ОСАНКА'
        draws.append(f"drawtext=fontfile={FONT}:expansion=none:textfile={f}:fontsize={110 if big else (72 if len(lab) <= 20 else 58)}:fontcolor={'black' if big else YEL}"
                     f":x=(w-text_w)/2:y={1180 if big else 300}:borderw={0 if big else 3}:bordercolor=black@0.6"
                     + (f":box=1:boxcolor={YEL}:boxborderw=22" if big else ":shadowcolor=black@0.5:shadowx=0:shadowy=4")
                     + f":enable='between(t,{start + a:.2f},{min(start + b, t0) - 0.04:.2f})'")
open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
draws.append(f"drawtext=fontfile={FONT}:text='ЧЕРНОВИК\\: СУБТИТРЫ \\= БУДУЩИЙ ГОЛОС':fontsize=34:fontcolor=white@0.8:x=(w-text_w)/2:y=110:box=1:boxcolor=black@0.45:boxborderw=12")
final = f'{B}/posture_draft_v1.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt',
                '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-vf', ','.join(draws), '-map', '0:v', '-map', '1:a', '-shortest',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', final], check=True)
print('final', final, round(dur_of(final), 2), 'shots', len(parts))
