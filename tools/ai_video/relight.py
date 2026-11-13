# "Виртуальный свет": карта глубины (Depth Anything V2 small) -> нормали -> ключевой тёплый свет спереди-сбоку и холодный контровой сзади,
# маска человека SAM 2 по точкам суставов, фон притушен. Работает поверх нашего цвета.
import os, sys, json, subprocess, numpy as np, torch
os.environ['HF_HOME'] = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/models/hf'
from transformers import AutoImageProcessor, AutoModelForDepthEstimation, Sam2Processor, Sam2Model
from PIL import Image, ImageFilter, ImageDraw, ImageFont
torch.set_num_threads(4)
B = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
sys.path.insert(0, f'{B}/posture')
from look import GRADE3
W, H = 1080, 1920
DA = 'depth-anything/Depth-Anything-V2-Small-hf'; SM = 'facebook/sam2.1-hiera-small'
dproc, dmod = AutoImageProcessor.from_pretrained(DA), AutoModelForDepthEstimation.from_pretrained(DA).eval()
sproc, smod = Sam2Processor.from_pretrained(SM), Sam2Model.from_pretrained(SM).eval()


def frame(clip, t, pre=''):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', f'{B}/posture/raw/IMG_{clip} (1).MOV', '-vf', f'{pre}scale={W}:{H},{GRADE3}',
                          '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()


def person_mask(img, pts):
    inp = sproc(images=Image.fromarray(img), input_points=[[pts]], input_labels=[[[1] * len(pts)]], return_tensors='pt')
    with torch.no_grad():
        out = smod(**inp, multimask_output=False)
    m = sproc.post_process_masks(out.pred_masks, inp['original_sizes'])[0]
    from scipy.ndimage import gaussian_filter
    return np.clip(gaussian_filter(m.reshape(-1, H, W)[0].float().numpy(), 2.5), 0, 1)  # мягкий край маски


def depth(img):
    inp = dproc(images=Image.fromarray(img), return_tensors='pt')
    with torch.no_grad():
        d = dmod(**inp).predicted_depth
    d = torch.nn.functional.interpolate(d[:, None], size=(H, W), mode='bicubic', align_corners=False)[0, 0].numpy()
    return (d - d.min()) / (d.max() - d.min() + 1e-6)  # больше = ближе


def relight(img, m, d, key=(-0.55, -0.45, 0.70), rim=(0.85, -0.25, -0.45), key_col=(1.0, 0.86, 0.72), rim_col=(0.70, 0.85, 1.0)):
    ds = np.asarray(Image.fromarray((d * 65535).astype(np.uint16)).filter(ImageFilter.GaussianBlur(6)), dtype=np.float32) / 65535 if False else d
    from scipy.ndimage import gaussian_filter
    ds = gaussian_filter(d, 5)
    gy, gx = np.gradient(ds)
    k = 260.0
    n = np.dstack([-gx * k, -gy * k, np.ones_like(ds)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array(key) / np.linalg.norm(key); R = np.array(rim) / np.linalg.norm(rim)
    kd = np.clip((n * L).sum(2), 0, 1)
    # контровой: края силуэта со стороны источника
    mb = gaussian_filter(m, 10)
    my, mx = np.gradient(mb)
    edge = np.clip(np.hypot(mx, my) * 18, 0, 1) ** 1.5
    side = np.clip(-(mx * R[0] + my * R[1]) / (np.hypot(mx, my) + 1e-6), 0, 1)
    rim_amt = edge * side * m
    f = img.astype(np.float32) / 255
    lin = f ** 2.2
    mm = m[..., None]
    light = 0.60 + 0.95 * kd[..., None] * np.array(key_col)
    out = lin * (light * mm + (1 - mm) * 0.55)
    out += (rim_amt[..., None] * 0.22) * np.array(rim_col)
    out = np.clip(out, 0, 1) ** (1 / 2.2)
    return (out * 255).astype(np.uint8)


def pts_from_pose(clip, s, e, idx, pre_scale=1.0):
    P = json.load(open(f'{B}/posture/pose/{clip}_{s}_{e}.json'))[idx]
    return [[P[j][0] * W, P[j][1] * H] for j in (0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28) if P[j][2] > 0.6]


f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
tiles = []
for clip, s, e, t, pre in [('9675', 0.0, 6.9, 2.0, ''), ('9673', 0.3, 15.9, 1.5, ''), ('9667', 12.0, 16.0, 13.5, '')]:
    img = frame(clip, t, pre)
    pts = pts_from_pose(clip, s, e, int((t - s) * 30))
    m = person_mask(img, pts)
    d = depth(img)
    out = relight(img, m, d)
    for name, im in (('сейчас', img), ('виртуальный свет', out)):
        p = Image.fromarray(im).resize((540, 960)); ImageDraw.Draw(p).text((14, 14), name, fill='yellow', font=f)
        tiles.append(p)
    Image.fromarray((d * 255).astype(np.uint8)).resize((270, 480)).save(f'{B}/ai/depth_{clip}.png')
S = Image.new('RGB', (540 * 6, 960))
for i, t in enumerate(tiles): S.paste(t, (i * 540, 0))
S.save(f'{B}/ai/relight_cmp.png'); print('ok')
