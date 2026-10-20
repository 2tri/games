import sys, os, subprocess
S='/tmp/claude-0/-home-user/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/'; E='/tmp/claude-0/-home-user-home/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/emu/'
os.chdir(E); base, name, slot, move, outdir = sys.argv[1:6]; tag='v%s'%slot
env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'); os.makedirs(outdir,exist_ok=True)
rom=E+'meas/%s.nds'%tag
subprocess.run(['python3','mkanim.py',base,rom,name,move],env=env,stdout=subprocess.DEVNULL,check=True)
subprocess.run(['python3','walk.py',rom,'ag4.dst','meas/%s.dst'%tag,'L1 A1 W300 R1 U1 A1 W400','meas/%s_w.png'%tag],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['python3','anim.py',rom,'meas/%s.dst'%tag,'meas/o_%s'%tag,'740','12','700'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
from PIL import Image
Image.open('meas/o_%s/first.png'%tag).crop((0,0,256,192)).save('%s/%s_%s.png'%(outdir,slot,name))
for p in (rom,'meas/%s.dst'%tag):
    try: os.remove(p)
    except Exception: pass
