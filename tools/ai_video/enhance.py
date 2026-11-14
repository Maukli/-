# Улучшение исходников для рилса: каждый чётный кадр Real-ESRGAN general x4v3 (540x960 -> 2160x3840, затем в 1080x1920),
# нечётные кадры дорисовывает RIFE между улучшенными соседями. Результат: enh/s<номер кадра монтажа>.mp4, те же кадры и длина, что в монтаже.
import sys, os, json, subprocess, time, numpy as np, torch
sys.path.insert(0, '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/ai')
from sr_lib import load
from rife_lib import mid
from PIL import Image
B = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
OUT = f'{B}/posture/enh'
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
BLEND = 0.2  # доля исходника: оставляет живую фактуру, без "пластика"
m = load('general_x4v3')


def sr(a):
    small = np.asarray(Image.fromarray(a).resize((W // 2, H // 2), Image.LANCZOS))
    x = torch.from_numpy(small.copy()).permute(2, 0, 1).float().unsqueeze(0) / 255
    with torch.no_grad():
        y = m(x)
    big = y.clamp(0, 1)
    down = torch.nn.functional.interpolate(big, size=(H, W), mode='bicubic', antialias=True, align_corners=False).clamp(0, 1)
    e = (down[0].permute(1, 2, 0).numpy() * 255)
    return np.clip(e * (1 - BLEND) + a.astype(np.float32) * BLEND, 0, 255).astype(np.uint8)


shots = json.load(open(f'{B}/ai/shots.json'))
only = [int(x) for x in sys.argv[1:]]
order = [i for i, sh in enumerate(shots) if sh[0] == 'clip' and (not only or i in only)]
for i in order:
    kind, src, s, e, pre = shots[i]
    out = f'{OUT}/s{i:02d}.mp4'
    if os.path.exists(out):
        continue
    t0 = time.time()
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/posture/raw/IMG_{src} (1).MOV', '-vf',
                          f'{pre}scale={W}:{H}:flags=lanczos,fps=30', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    n = len(fr)
    enh = [None] * n
    for k in range(0, n, 2):
        enh[k] = sr(fr[k])
    if n % 2 == 0:
        enh[n - 1] = sr(fr[n - 1])
    for k in range(1, n - 1, 2):
        if enh[k] is None:
            enh[k] = mid(enh[k - 1], enh[k + 1])
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', out + '.part.mp4'], stdin=subprocess.PIPE)
    for a in enh:
        enc.stdin.write(a.tobytes())
    enc.stdin.close(); enc.wait()
    os.replace(out + '.part.mp4', out)
    print(i, src, n, 'frames', round(time.time() - t0), 's', flush=True)
print('enhance done', flush=True)
