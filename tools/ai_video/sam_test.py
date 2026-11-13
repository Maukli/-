# SAM 2.1 small: маска человека по видео (подсказки: точки суставов из MediaPipe на первом кадре). Сравнение с маской MediaPipe.
import os, sys, time, json, subprocess, numpy as np, torch
os.environ['HF_HOME'] = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/models/hf'
from transformers import Sam2VideoModel, Sam2VideoProcessor
from PIL import Image
torch.set_num_threads(4)
B = '/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
clip, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 540, 960
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-to', str(e), '-i', f'{B}/posture/raw/IMG_{clip} (1).MOV', '-vf', f'scale={W}:{H},fps=30',
                      '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
frames = [f for f in np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)]
pose = json.load(open(f'{B}/posture/pose/{clip}_{s}_{e}.json'))
lm = pose[0]
pts = [[lm[j][0] * W, lm[j][1] * H] for j in (11, 12, 23, 24, 25, 26) if lm[j][2] > 0.5]
name = 'facebook/sam2.1-hiera-small'
model = Sam2VideoModel.from_pretrained(name).eval()
proc = Sam2VideoProcessor.from_pretrained(name)
t0 = time.time()
sess = proc.init_video_session(video=frames, inference_device='cpu', dtype=torch.float32)
proc.add_inputs_to_inference_session(inference_session=sess, frame_idx=0, obj_ids=1, input_points=[[pts]], input_labels=[[[1] * len(pts)]])
with torch.no_grad():
    model(inference_session=sess, frame_idx=0)
    masks = {}
    for out in model.propagate_in_video_iterator(sess):
        m = proc.post_process_masks([out.pred_masks], original_sizes=[[sess.video_height, sess.video_width]], binarize=False)[0]
        masks[out.frame_idx] = torch.sigmoid(m[0, 0]).numpy() if m.dim() == 4 else torch.sigmoid(m[0]).numpy()
dt = time.time() - t0
print('frames', len(frames), 'sec total', round(dt, 1), 'sec per frame', round(dt / len(frames), 2))
arr = np.stack([masks[i] for i in sorted(masks)]).astype(np.float32)
np.save(f'{B}/ai/sam_{clip}.npy', arr)
