import sys, struct, subprocess, os, json
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS, NARC
S='/tmp/claude-0/-home-user/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/'
E_='/tmp/claude-0/-home-user-home/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/emu/'
shard,n=map(int,sys.argv[1].split('/')); step=int(sys.argv[2])
raw=bytearray(open(S+os.environ.get('ROMF','final_new.nds')+'','rb').read()); rom=NDS(bytes(raw))
ev=NARC(rom.get(hg1.NARC_PATHS['zone_event'])).files
sc=NARC(rom.get('a/0/1/2')).files[843]
base=bytes(raw).find(sc[:96]); assert base>=0 and bytes(raw).find(sc[:96],base+1)<0
entries=[]; p=0
while p+4<=len(sc):
    v=struct.unpack_from('<I',sc,p)[0]
    if (v&0xFFFF)==0xFD13: break
    tg=p+4+v
    if 0<tg<len(sc)-16: entries.append(tg)
    p+=4
def warp0(f):
    o=0; nb=struct.unpack_from('<I',f,o)[0]; o+=4+20*nb
    no=struct.unpack_from('<I',f,o)[0]; o+=4+32*no
    nw=struct.unpack_from('<I',f,o)[0]; o+=4
    return struct.unpack_from('<HHHH',f,o)[:2] if nw and o+12<=len(f) else None
maps=[m for m in range(1,len(ev)) if warp0(ev[m])]
sel=maps[::step]; print(len(maps),'maps with warps; sampling',len(sel),flush=True)
res=[]
for k,m in enumerate(sel):
    if k%n!=shard: continue
    x,y=warp0(ev[m]); code=struct.pack('<7H',176,m,0,x,y,1,2)   # Warp m,0,x,y,dir=1 ; End
    img=bytearray(raw)
    for tg in entries: img[base+tg:base+tg+len(code)]=code
    p=E_+'mp_%s_%d.nds'%(os.environ.get('OUT','mapout'),shard); open(p,'wb').write(img)
    d=E_+os.environ.get('OUT','mapout')+'/m%03d'%m; os.makedirs(d,exist_ok=True)
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    out=subprocess.run(['python3',E_+'지도_이동시험_촬영.py',p,d],env=env,capture_output=True,text=True,timeout=300).stdout.strip().splitlines()
    print(m,x,y,out[-1] if out else 'NO OUTPUT',flush=True)
