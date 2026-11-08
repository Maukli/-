# Водяной знак: значок Instagram (контур) и ник под ним, белым с мягкой тенью.
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = 4  # рисуем крупно и уменьшаем для гладких краёв
icon, pad = 72, 14
font = ImageFont.truetype('fonts2/SofiaXC.ttf', 54 * S)
text = sys.argv[1] if len(sys.argv) > 1 else '@MIKO_OLOO'
tw = font.getbbox(text)[2]
W = max(icon * S, tw) + 2 * pad * S
H = (icon + 10 + 62) * S + 2 * pad * S
fg = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(fg)
x0, y0, s = pad * S, pad * S, icon * S
lw = int(s * 0.085)
d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=int(s * 0.28), outline=255, width=lw)
c, r = (x0 + s / 2, y0 + s / 2), s * 0.22
d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=255, width=lw)
dr = s * 0.055
d.ellipse([x0 + s * 0.75 - dr, y0 + s * 0.25 - dr, x0 + s * 0.75 + dr, y0 + s * 0.25 + dr], fill=255)
d.text((x0, y0 + s + 10 * S - font.getbbox(text)[1] + 4 * S), text, font=font, fill=255)
shadow = fg.filter(ImageFilter.GaussianBlur(6 * S)).point(lambda v: min(255, int(v * 1.6)))
out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
out.paste(Image.new('RGBA', (W, H), (0, 0, 0, 255)), (0, 0), shadow.point(lambda v: int(v * 0.55)))
out.paste(Image.new('RGBA', (W, H), (255, 255, 255, 255)), (0, 0), fg.point(lambda v: int(v * 0.9)))
out = out.resize((W // S, H // S), Image.LANCZOS)
out.save(sys.argv[2] if len(sys.argv) > 2 else 'wm.png')
print(out.size)
