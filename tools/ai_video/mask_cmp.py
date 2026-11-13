import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
B = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
clip, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 540, 960
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/posture/raw/IMG_{clip} (1).MOV', '-vf', f'scale={W}:{H},fps=30',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
sam = np.load(f'{B}/ai/sam_{clip}.npy')
mpm = np.load(f'{B}/ai/mp_{clip}.npy')

def flicker(m):
    b = (m > 0.5).astype(np.float32)
    edge = np.abs(np.diff(b, axis=0))  # пиксели, сменившие состояние
    return edge.sum((1, 2)).mean()
print('pixels flipping per frame  mediapipe', round(flicker(mpm)), ' sam2', round(flicker(sam)))
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
tiles = []
for k in (20, 75, 130):
    for name, m in (('MediaPipe', mpm[k]), ('SAM 2', sam[k])):
        im = Image.fromarray(fr[k]).convert('RGB')
        b = Image.fromarray(((m > 0.5) * 255).astype(np.uint8))
        edge = b.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
        col = Image.new('RGB', (W, H), (255, 60, 60) if name == 'MediaPipe' else (60, 255, 120))
        im.paste(col, (0, 0), edge)
        ImageDraw.Draw(im).text((8, 8), f'{name}  кадр {k}', fill='yellow', font=f)
        tiles.append(im.crop((60, 180, 480, 900)))
S = Image.new('RGB', (420 * 6, 720))
for i, t in enumerate(tiles): S.paste(t, (i * 420, 0))
S.save(f'{B}/ai/mask_cmp_{clip}.png')
