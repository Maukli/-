# Только MediaPipe-маски для кадров клипа, в отдельном процессе. Сохраняет mp_<clip>.npy
import sys, subprocess, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
B = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
clip, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 540, 960
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/posture/raw/IMG_{clip} (1).MOV', '-vf', f'scale={W}:{H},fps=30',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=f'{B}/models/pose_heavy.task'),
       running_mode=vision.RunningMode.VIDEO, num_poses=1, output_segmentation_masks=True))
out = np.zeros((len(fr), H, W), np.float32)
for i, f in enumerate(fr):
    r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)), int(i * 1000 / 30))
    if r.segmentation_masks:
        out[i] = np.array(r.segmentation_masks[0].numpy_view(), copy=True).squeeze()
np.save(f'{B}/ai/mp_{clip}.npy', out)
print('saved', out.shape)
