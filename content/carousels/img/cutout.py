# Вырезает фон с фото упражнения (BiRefNet lite, MIT). Запуск: python3 cutout.py in.jpg out.png
import sys, os
import numpy as np, onnxruntime as ort
from PIL import Image
sess = ort.InferenceSession(os.path.expanduser('~/.u2net/birefnet_lite.onnx'))
def cut(src, dst):
    im = Image.open(src).convert('RGB')
    x = np.asarray(im.resize((1024, 1024)), dtype=np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    y = sess.run(None, {'input_image': x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    y = 1 / (1 + np.exp(-y))
    m = Image.fromarray((y * 255).astype(np.uint8)).resize(im.size)
    out = im.convert('RGBA'); out.putalpha(m); out.save(dst)
if __name__ == '__main__':
    cut(sys.argv[1], sys.argv[2])
