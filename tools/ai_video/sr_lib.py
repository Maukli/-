# Увеличение с дорисовкой деталей: Real-ESRGAN (x2plus, x4plus) и realesr-general-x4v3, загрузка через spandrel, обработка плитками.
import numpy as np, torch, spandrel
import torch.nn.functional as F
from safetensors.torch import load_file
torch.set_num_threads(4)
SR = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/models/sr'
_cache = {}


def load(name):
    if name in _cache:
        return _cache[name]
    sd = load_file(f'{SR}/{name}.safetensors')
    if name == 'general_x4v3':  # веса из MLX: свёртки в порядке (out, kh, kw, in)
        sd = {k: (v.permute(0, 3, 1, 2).contiguous() if v.dim() == 4 else v) for k, v in sd.items()}
    m = spandrel.ModelLoader().load_from_state_dict(sd).eval()
    _cache[name] = m
    return m


def upscale(img, name='x2plus', tile=384, pad=16):
    """img: HxWx3 uint8 -> (H*s)x(W*s)x3 uint8"""
    m = load(name); s = m.scale
    x = torch.from_numpy(np.ascontiguousarray(img)).permute(2, 0, 1).float().unsqueeze(0) / 255
    _, _, H, W = x.shape
    out = torch.zeros(1, 3, H * s, W * s)
    with torch.no_grad():
        for y0 in range(0, H, tile):
            for x0 in range(0, W, tile):
                y1, x1 = min(y0 + tile, H), min(x0 + tile, W)
                ya, xa, yb, xb = max(0, y0 - pad), max(0, x0 - pad), min(H, y1 + pad), min(W, x1 + pad)
                o = m.model(x[:, :, ya:yb, xa:xb]) if hasattr(m, 'model') else m(x[:, :, ya:yb, xa:xb])
                out[:, :, y0 * s:y1 * s, x0 * s:x1 * s] = o[:, :, (y0 - ya) * s:(y0 - ya) * s + (y1 - y0) * s, (x0 - xa) * s:(x0 - xa) * s + (x1 - x0) * s]
    return (out[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + 0.5).astype(np.uint8)
