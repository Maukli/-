# Надпись в PNG: трекинг, мягкая тень, необязательная обводка. Для заголовка и имени (статичные надписи).
from PIL import Image, ImageDraw, ImageFont, ImageFilter
def text_png(text, font, size, color=(255, 255, 255), tracking=0, shadow=(0, 6, 10, 150), stroke=0, stroke_color=(0, 0, 0), out=None):
    S = 2
    f = ImageFont.truetype(font, size * S)
    widths = [f.getbbox(ch)[2] - f.getbbox(ch)[0] if ch != ' ' else f.getlength(' ') for ch in text]
    asc, desc = f.getmetrics()
    pad = (40 + stroke * 2) * S
    W = int(sum(f.getlength(ch) for ch in text) + tracking * S * (len(text) - 1) + 2 * pad)
    H = int(asc + desc + 2 * pad)
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    smask = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(smask)
    x = pad
    for ch in text:
        d.text((x, pad), ch, font=f, fill=255)
        if stroke: sd.text((x, pad), ch, font=f, fill=255, stroke_width=stroke * S, stroke_fill=255)
        x += f.getlength(ch) + tracking * S
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if shadow:
        dx, dy, blur, a = shadow
        base = smask if stroke else mask
        sh = base.filter(ImageFilter.GaussianBlur(blur * S)).point(lambda v: v * a // 255)
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 255)); tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        tmp.paste(layer, (dx * S, dy * S), sh); img = Image.alpha_composite(img, tmp)
    if stroke:
        img.paste(Image.new('RGBA', (W, H), stroke_color + (255,)), (0, 0), smask)
    col = Image.new('RGBA', (W, H), tuple(color) + (255,))
    img.paste(col, (0, 0), mask)
    img = img.crop(img.getbbox()).resize((max(1, img.getbbox()[2] - img.getbbox()[0]) // S, max(1, img.getbbox()[3] - img.getbbox()[1]) // S), Image.LANCZOS) if img.getbbox() else img
    if out: img.save(out)
    return img
