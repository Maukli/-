# Подсветка работающей мышцы на фото для каруселей (как в рилсе): капсулы вдоль мышцы, сильное размытие,
# свечение только внутри силуэта человека (маска MediaPipe Pose). Плюс вывод суставов в процентах кадра,
# чтобы ставить пометки точно на тело.
# Запуск: python3 glow.py <вход> <выход> '<json капсул>' [цвет #RRGGBB] [сила]
#   капсула: [x0, y0, x1, y1, r] в процентах ширины и высоты кадра (r в процентах ширины)
#   без капсул (пустой список) только печатает суставы.
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MODEL = os.environ.get('POSE_MODEL', '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/models/pose_heavy.task')
NAMES = {0: 'нос', 7: 'ухо Л', 8: 'ухо П', 11: 'плечо Л', 12: 'плечо П', 23: 'таз Л', 24: 'таз П', 25: 'колено Л', 26: 'колено П', 27: 'лодыжка Л', 28: 'лодыжка П'}


def pose(img):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.IMAGE, num_poses=1, output_segmentation_masks=True))
    small = img.copy(); small.thumbnail((960, 960))
    r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(np.asarray(small))))
    mask = np.array(r.segmentation_masks[0].numpy_view(), copy=True).squeeze() if r.segmentation_masks else np.ones((small.height, small.width), np.float32)
    pts = {}
    if r.pose_landmarks:
        for i, n in NAMES.items():
            p = r.pose_landmarks[0][i]
            pts[n] = (round(p.x * 100, 1), round(p.y * 100, 1), round(p.visibility, 2))
    return mask, pts


def glow(img, caps, color, strength, mask):
    W, H = img.size
    g = Image.new('L', (W // 4, H // 4), 0); d = ImageDraw.Draw(g)
    for x0, y0, x1, y1, r in caps:
        p0 = (x0 * W / 400, y0 * H / 400); p1 = (x1 * W / 400, y1 * H / 400); rr = r * W / 400
        d.line([p0, p1], fill=255, width=int(rr * 2)); d.ellipse([p0[0] - rr, p0[1] - rr, p0[0] + rr, p0[1] + rr], fill=255)
        d.ellipse([p1[0] - rr, p1[1] - rr, p1[0] + rr, p1[1] + rr], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(max(4, W / 160))).resize((W, H), Image.BILINEAR)
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
    k = (np.asarray(g, np.float32) / 255 * np.asarray(m, np.float32) / 255 * strength)[..., None]
    a = np.asarray(img, np.float32)
    col = np.array([int(color[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    emit = 0.30 * a.mean(2, keepdims=True) + 0.85 * col
    return Image.fromarray(np.clip(a * (1 - k) + emit * k, 0, 255).astype(np.uint8))


if __name__ == '__main__':
    src, dst, caps = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
    color = sys.argv[4] if len(sys.argv) > 4 else '#FF9F5A'
    strength = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
    img = Image.open(src).convert('RGB')
    mask, pts = pose(img)
    print(json.dumps(pts, ensure_ascii=False))
    if caps:
        glow(img, caps, color, strength, mask).save(dst, quality=92)
