# Выравнивание резкости после enhance.py: нечётные кадры (RIFE) мягче чётных (Real-ESRGAN) на 15-20%,
# через кадр это даёт "дрожание" резкости. Каждому нечётному кадру подбираем лёгкий unsharp,
# чтобы высокочастотная энергия (дисперсия лапласиана) совпала со средним соседей.
# Запуск: python3 match_sharp.py <папка enh> <новая папка>
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import laplace

W, H = 1080, 1920
SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)


def lv(a):
    g = a.astype(np.float32).mean(2)
    return laplace(g[::2, ::2]).var()


def sharp(a, pc):
    return np.asarray(Image.fromarray(a).filter(ImageFilter.UnsharpMask(1.0, int(round(pc)), 0)))


def fix(name):
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', f'{SRC}/{name}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    fr = []
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        fr.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
    out, pcs = list(fr), []
    for k in range(1, len(fr) - 1, 2):
        target = (lv(fr[k - 1]) + lv(fr[k + 1])) / 2
        l0, l20 = lv(fr[k]), lv(sharp(fr[k], 20))
        pc = 0.0 if l20 <= l0 else float(np.clip(20 * (target - l0) / (l20 - l0), 0, 45))
        pcs.append(pc)
        if pc > 0.5:
            out[k] = sharp(fr[k], pc)
    tmp = f'{DST}/{name}.part.mp4'
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    for a in out:
        enc.stdin.write(a.tobytes())
    enc.stdin.close(); enc.wait()
    os.replace(tmp, f'{DST}/{name}')
    print(name, len(fr), 'unsharp %% в среднем %.1f' % (np.mean(pcs) if pcs else 0), flush=True)


if __name__ == '__main__':
    from multiprocessing import Pool
    names = sorted(n for n in os.listdir(SRC) if n.endswith('.mp4') and '.part' not in n)
    with Pool(4) as p:
        p.map(fix, names)
