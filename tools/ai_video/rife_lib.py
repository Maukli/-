# Дорисовка промежуточного кадра RIFE v4: поток считаем на половинном разрешении, кадры сдвигаем в полном.
import sys, numpy as np, torch
import torch.nn.functional as F
from safetensors.torch import load_file
sys.path.insert(0, '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/ai')
from rife_net import IFNet, warp
torch.set_num_threads(4)
_M = None
def model():
    global _M
    if _M is None:
        _M = IFNet(); _M.load_state_dict(load_file('/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/models/rife/flownet.safetensors'))
        _M.eval(); _M.return_flow = True
    return _M
def T(a): return torch.from_numpy(np.ascontiguousarray(a)).permute(2, 0, 1).float().unsqueeze(0) / 255
def mid(a0, a1, scale=0.5):
    x0, x1 = T(a0), T(a1)
    H, W = x0.shape[2:]
    xs = F.interpolate(torch.cat([x0, x1], 1), scale_factor=scale, mode='bilinear', align_corners=False)
    hh, ww = xs.shape[2:]
    xs = F.pad(xs, (0, (32 - ww % 32) % 32, 0, (32 - hh % 32) % 32), mode='replicate')
    with torch.no_grad():
        flow, mask = model()(xs)
    flow = F.interpolate(flow[:, :, :hh, :ww], size=(H, W), mode='bilinear', align_corners=False) / scale
    mask = F.interpolate(mask[:, :, :hh, :ww], size=(H, W), mode='bilinear', align_corners=False)
    y = warp(x0, flow[:, :2]) * mask + warp(x1, flow[:, 2:4]) * (1 - mask)
    return (y[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + 0.5).astype(np.uint8)
