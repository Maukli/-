# Кинематографичный цвет как в образце: глубокие чёрные, бирюзовые тени, тёплая кожа, тёмный фон,
# человек выделен (маска сегментации MediaPipe). Плюс приёмы: слово позади человека, белый силуэт-вспышка, подсветка мышц по силуэту.
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from gfx import FONT, W, H, B
BIGFONT = f'{B}/../challenge/fonts2/SofiaXC.ttf'

GRADE3 = ("eq=contrast=1.16:brightness=-0.045:saturation=0.84,"
          "curves=r='0/0 0.12/0.07 0.5/0.50 0.85/0.88 1/0.98':g='0/0.01 0.12/0.085 0.5/0.49 0.85/0.86 1/0.97':b='0/0.035 0.12/0.11 0.5/0.48 0.85/0.83 1/0.94',"
          "colorbalance=rs=-0.05:gs=-0.01:bs=0.05:rm=0.03:gm=0.0:bm=-0.02:rh=0.05:gh=0.02:bh=-0.03,"
          "unsharp=5:5:0.75:5:5:0.0")


def finish(arr, mask, t=None, flash=0.0):
    """arr: HxWx3 float 0..255 после ffmpeg-цвета. mask: HxW 0..1 (человек). Фон темнее и холоднее, человек чуть светлее."""
    m = mask[..., None]
    lum = arr.mean(2, keepdims=True)
    bg = (arr * 0.62 + lum * 0.08) * np.array([0.92, 0.98, 1.04])  # фон: темнее, чуть бирюзовее, менее насыщен
    fg = arr * 1.04
    out = fg * m + bg * (1 - m)
    # виньетка
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.38 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
    out *= np.clip(v, 0.45, 1)[..., None]
    if flash > 0:
        out = out * (1 - m * flash) + 255 * m * flash
    return out


_VIG = None


def vignette():
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = 1 - 0.38 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        _VIG = np.clip(v, 0.45, 1)[..., None].astype(np.float32)
    return _VIG


def finish_fast(arr, mask, flash=0.0):
    m = mask[..., None]
    lum = arr.mean(2, keepdims=True)
    bg = (arr * 0.46 + lum * 0.07) * np.array([0.90, 0.98, 1.06], dtype=np.float32)
    out = arr * 1.04 * m + bg * (1 - m)
    out *= vignette()
    if flash > 0:
        out = out * (1 - m * flash) + 255 * m * flash
    return out


def big_word(word, size, color=(255, 210, 31), y=520, tracking=0):
    """Слово огромным шрифтом во всю ширину кадра: альфа-маска и цвет."""
    FONT = BIGFONT
    f = ImageFont.truetype(FONT, size)
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    wtxt = f.getlength(word)
    while wtxt > W * 0.94 and size > 60:
        size -= 8; f = ImageFont.truetype(FONT, size); wtxt = f.getlength(word)
    d.text((W / 2, y), word, font=f, fill=255, anchor='mm')
    return np.asarray(img, dtype=np.float32) / 255.0


def behind(out, word_alpha, mask, color, a=1.0):
    """Слово позади человека: видно только там, где нет человека."""
    k = (word_alpha * (1 - mask) * a)[..., None]
    return out * (1 - k) + np.array(color, dtype=np.float32) * k


def capsule(p0, p1, r, n=24):
    import math
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    pts = []
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((p0[0] + r * (math.cos(a) * ux - math.sin(a) * nx * -1) if False else p0[0] + r * (ux * math.cos(a) + nx * math.sin(a)),
                    p0[1] + r * (uy * math.cos(a) + ny * math.sin(a))))
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((p1[0] + r * (ux * math.cos(a) + nx * math.sin(a)), p1[1] + r * (uy * math.cos(a) + ny * math.sin(a))))
    return pts


def glow_map(blobs=(), segs=(), blur=14):
    """Подсветка мышцы: капсулы вдоль мышцы (p0, p1, радиус) и эллипсы (x, y, rx, ry), сильно размытые."""
    sm = Image.new('L', (W // 4, H // 4), 0)
    d = ImageDraw.Draw(sm)
    for x, y, rx, ry in blobs:
        d.ellipse([(x - rx) / 4, (y - ry) / 4, (x + rx) / 4, (y + ry) / 4], fill=255)
    for p0, p1, r in segs:
        d.polygon([(px / 4, py / 4) for px, py in capsule(p0, p1, r)], fill=255)
    sm = sm.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(sm.resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0


def add_glow(out, g, mask, color, strength):
    """Мышца "загорается": свечение цвета мышцы поверх тела, только внутри силуэта. Видно и на тёмной, и на светлой ткани."""
    k = (g * mask * strength)[..., None]
    col = np.array(color, dtype=np.float32)
    lum = out.mean(2, keepdims=True)
    emit = 0.30 * lum + 0.85 * col  # свет мышцы с фактурой ткани
    return out * (1 - k) + emit * k
