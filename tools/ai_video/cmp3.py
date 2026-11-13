import sys, subprocess, numpy as np, traceback
sys.path.insert(0,'/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad/ai')
from rife_lib import mid
from PIL import Image, ImageDraw, ImageFont
B='/tmp/claude-0/-home-user--/76ce7879-1946-5741-9348-e22c3a72dab4/scratchpad'
src=f'{B}/challenge/raw/C025.mp4'
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
def grab(t, vf, n):
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',src,'-vf',vf,'-frames:v',str(n),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,1920,1080,3)
rows=[]
for t in (75.13, 75.21):
    fr=grab(t,'scale=1080:1920',2); a0,a1=fr[0].copy(),fr[1].copy()
    r=mid(a0,a1)
    mf=grab(t,'scale=1080:1920,minterpolate=fps=47.952:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1',6)
    sc=[]
    for x in mf:
        e0=np.abs(x.astype(int)-a0.astype(int)).mean(); e1=np.abs(x.astype(int)-a1.astype(int)).mean()
        sc.append(abs(e0-e1) if (e0>0.5 and e1>0.5) else 1e9)
    mi=mf[int(np.argmin(sc))]
    crop=(380,250,1080,850)
    row=Image.new('RGB',(4*405,371),'white')
    for i,(n,im) in enumerate([('кадр 1',a0),('старый способ',mi),('RIFE',r),('кадр 2',a1)]):
        row.paste(Image.fromarray(im).crop(crop).resize((400,343)),(i*405,30)); ImageDraw.Draw(row).text((i*405+6,2),f'{n}  {t}',fill='black',font=f)
    rows.append(row)
S=Image.new('RGB',(rows[0].width,sum(r_.height for r_ in rows)),'white'); y=0
for r_ in rows: S.paste(r_,(0,y)); y+=r_.height
S.save(f'{B}/ai/rife_cmp4.png'); print('ok')
