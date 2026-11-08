import sys; sys.path.insert(0, '.')
from textpng import text_png
from PIL import Image, ImageDraw, ImageFont
Y = (255, 210, 31)
C = {
 'A': [('NEW CHALLENGE', 'fonts2/Anton.ttf', 120, (255, 255, 255), 4, 0), ('oxmedo', 'fonts2/MrDafoe.ttf', 150, Y, 0, 0)],
 'B': [('NEW CHALLENGE', 'fonts2/Bebas.ttf', 150, (255, 255, 255), 10, 0), ('OXMEDO', 'fonts2/Marker.ttf', 84, (255, 255, 255), 2, 0)],
 'C': [('NEW CHALLENGE', 'fonts2/BigShoulders.ttf', 130, (255, 255, 255), 3, 0), ('oxmedo', 'fonts2/Kaushan.ttf', 100, Y, 0, 0)],
 'D': [('NEW CHALLENGE', 'fonts2/Anton.ttf', 120, Y, 4, 0), ('oxmedo', 'fonts2/Yellowtail.ttf', 130, (255, 255, 255), 0, 0)],
}
base = Image.open('gt/B_C026_25.0_j.png').convert('RGBA')
lab = ImageFont.truetype('fonts2/Bebas.ttf', 56); sym = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 46)
tiles = []
for k, ((t, tf, ts, tc, tt, _), (n, nf, ns, nc, nt, _)) in C.items():
    im = base.copy()
    T = text_png(t, tf, ts, tc, tt); N = text_png(n, nf, ns, nc, nt)
    ty = 1330
    im.alpha_composite(T, ((1080 - T.width) // 2, ty))
    im.alpha_composite(N, ((1080 - N.width) // 2, ty + T.height - int(N.height * 0.22)))
    d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle([1080 - 400, 535, 1080 - 40, 945], fill=(0, 0, 0, 77))
    for i, (l, done) in enumerate([('LYING', 1), ('SEATED', 1), ('STANDING', 0), ('SEATED', 0), ('LYING', 0)]):
        y = 560 + i * 78; w = lab.getlength(l)
        d.text((1080 - 200 - w, y), l, font=lab, fill=(255, 255, 255, 255 if done else 175))
        d.text((1080 - 172, y + 2), '✔' if done else '○', font=sym, fill=(61, 220, 132, 255) if done else (255, 255, 255, 175))
    t = im.crop((0, 480, 1080, 1780)).resize((432, 520))
    ImageDraw.Draw(t).text((10, 6), k, font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40), fill=(255, 255, 0))
    tiles.append(t)
sheet = Image.new('RGB', (432 * 4 + 9, 520), 'white')
for i, t in enumerate(tiles): sheet.paste(t, (i * 435, 0))
sheet.save('gt/stylesheet.png'); print('ok')
