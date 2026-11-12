# Отслеживание суставов (MediaPipe Pose Landmarker) по кадрам клипа, результат в pose/<имя>.json
# Запуск: python3 pose.py <клип> <начало> <конец> [crop-фильтр]
import sys, os, json, subprocess
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

B = os.path.dirname(os.path.abspath(__file__))
MODEL = f'{B}/../models/pose_heavy.task'
W, H = 540, 960


def frames(clip, s, e, pre=''):
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/raw/IMG_{clip} (1).MOV',
           '-vf', f'{pre}scale={W}:{H},fps=30', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(H, W, 3)


def run(clip, s, e, pre='', tag=None):
    tag = tag or f'{clip}_{s}_{e}'
    out = f'{B}/pose/{tag}.json'
    if os.path.exists(out):
        return json.load(open(out))
    opts = vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=MODEL),
                                        running_mode=vision.RunningMode.VIDEO, num_poses=1,
                                        min_pose_detection_confidence=0.4, min_tracking_confidence=0.4)
    res = []
    with vision.PoseLandmarker.create_from_options(opts) as lm:
        for i, f in enumerate(frames(clip, s, e, pre)):
            r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)), int(i * 1000 / 30))
            if r.pose_landmarks:
                res.append([[round(p.x, 4), round(p.y, 4), round(p.visibility or 0, 2)] for p in r.pose_landmarks[0]])
            else:
                res.append(None)
    os.makedirs(f'{B}/pose', exist_ok=True)
    json.dump(res, open(out, 'w'))
    return res


if __name__ == '__main__':
    clip, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    pre = sys.argv[4] if len(sys.argv) > 4 else ''
    r = run(clip, s, e, pre)
    ok = sum(1 for x in r if x)
    print(clip, s, e, 'frames', len(r), 'detected', ok)
