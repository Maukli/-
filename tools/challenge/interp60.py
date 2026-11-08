# 24 -> 60 кадров в секунду: дорисовка промежуточных кадров (minterpolate, компенсация движения) по готовому цвету seg3/g*.mp4.
import subprocess, os
from concurrent.futures import ThreadPoolExecutor
B = os.path.dirname(os.path.abspath(__file__))
def run(i):
    src, out = f'{B}/seg3/g{i:02d}.mp4', f'{B}/seg60/g{i:02d}.mp4'
    if os.path.exists(out): return i, 'cached'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf',
                        'minterpolate=fps=60000/1001:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', out + '.part.mp4'], capture_output=True, text=True)
    if r.returncode == 0: os.replace(out + '.part.mp4', out)
    return i, 'ok' if r.returncode == 0 else r.stderr[-500:]
# Сначала длинные куски, чтобы потоки закончили примерно вместе.
order = sorted(range(27), key=lambda i: -os.path.getsize(f'{B}/seg3/g{i:02d}.mp4'))
with ThreadPoolExecutor(max_workers=4) as ex:
    for i, st in ex.map(run, order):
        print(i, st, flush=True)
print('interp done')
