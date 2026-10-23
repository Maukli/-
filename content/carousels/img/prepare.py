# Готовит иллюстрации для каруселей из открытой базы free-exercise-db (Unlicense, общественное достояние).
# Скачивает фото, вырезает фон (cutout.py), подрезает и выравнивает цвет. Результат: img/<имя>.png
# Запуск: python3 content/carousels/img/prepare.py
import os, sys, io, urllib.request
from PIL import Image, ImageEnhance
sys.path.insert(0, os.path.dirname(__file__))
from cutout import sess, np

BASE = 'https://cdn.jsdelivr.net/gh/yuhonas/free-exercise-db@main/exercises/'
# имя: (id в базе, кадр, подрезка исходника (x0, y0, x1, y1) или None)
ITEMS = {
    'neck_plate': ('Lying_Face_Up_Plate_Neck_Resistance', 0, (0, 0, 850, 430)),
    'leg_curl':   ('Standing_Leg_Curl', 0, (330, 0, 690, 567)),
    'abduction':  ('Side_Leg_Raises', 1, None),
    'hip_flexor': ('Kneeling_Hip_Flexor', 0, None),
    'cable_row':  ('Seated_Cable_Rows', 0, (0, 0, 640, 567)),
    'bench':      ('Barbell_Bench_Press_-_Medium_Grip', 0, None),
    'squat':      ('Barbell_Squat', 0, None),
    'pullups':    ('Pullups', 0, None),
    'squat_bw':   ('Bodyweight_Squat', 1, (200, 0, 650, 567)),
}
out_dir = os.path.dirname(os.path.abspath(__file__))

def cut(im):
    x = np.asarray(im.resize((1024, 1024)), dtype=np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    y = sess.run(None, {'input_image': x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (1 / (1 + np.exp(-y)) * 255).astype(np.uint8)
    return Image.fromarray(m).resize(im.size)

for name, (eid, frame, box) in ITEMS.items():
    dst = os.path.join(out_dir, name + '.png')
    if os.path.exists(dst) and '--force' not in sys.argv:
        continue
    raw = urllib.request.urlopen(f'{BASE}{eid}/{frame}.jpg').read()
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    if box:
        im = im.crop(box)
    mask = cut(im)
    # спокойнее цвета: чуть меньше насыщенности, чуть больше контраста
    im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(0.8)).enhance(1.08)
    rgba = im.convert('RGBA'); rgba.putalpha(mask)
    rgba = rgba.crop(mask.point(lambda v: 255 if v > 40 else 0).getbbox())
    rgba.save(dst)
    print(name, rgba.size)
