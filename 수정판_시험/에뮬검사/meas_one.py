import sys, os, subprocess, json
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS,NARC
from PIL import Image, ImageChops
name, slot, move = sys.argv[1], int(sys.argv[2]), sys.argv[3]
S='/tmp/claude-0/-home-user/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/'; E='/tmp/claude-0/-home-user-home/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/emu/'
os.chdir(E); tag='s%d'%slot; src=E+'meas/%s_a.nds'%tag; rom=E+'meas/%s.nds'%tag
r=NDS(open(S+'anim_final.nds','rb').read()); n=NARC(r.get('a/0/0/5')); f=list(n.files)
v=int(sys.argv[4]) if len(sys.argv)>4 else 0
f[slot*4+2]=bytes([v]); f[slot*4+3]=bytes([v]); n.files=f; r.put('a/0/0/5',n.build()); open(src,'wb').write(bytes(r.d))
env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
subprocess.run(['python3','mkanim.py',src,rom,name,move],env=env,stdout=subprocess.DEVNULL,check=True)
subprocess.run(['python3','walk.py',rom,'ag4.dst','meas/%s.dst'%tag,'L1 A1 W300 R1 U1 A1 W400','meas/%s_w.png'%tag],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['python3','anim.py',rom,'meas/%s.dst'%tag,'meas/o_%s'%tag,'740','12','700'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
im=Image.open('meas/o_%s/first.png'%tag).crop((135,0,256,92)).convert('RGB')
base=Image.open('anim/co_m120/first.png').crop((135,0,256,92)).convert('RGB')
d=ImageChops.difference(im,base).convert('L').point(lambda p:255 if p>30 else 0); bb=d.getbbox()
res={'name':name,'slot':slot,'v':v,'bbox':[bb[0]+135,bb[1],bb[2]+135,bb[3]] if bb else None}
open('meas/res_%s.json'%tag,'w').write(json.dumps(res,ensure_ascii=False))
for p in (src,rom,E+'meas/%s.dst'%tag): 
    try: os.remove(p)
    except Exception: pass
print(json.dumps(res,ensure_ascii=False))
