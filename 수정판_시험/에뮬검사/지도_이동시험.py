"""python 지도_이동시험.py <i/n> — 스크립트 Warp 로 모든 지도에 이동해 화면 촬영(환경변수 ROMF 롬 이름, ROMDIR 폴더, STATE, NOLEFT, OUT, MAPS 로 조절). 결과: <OUT>/m<번호>/{a,b,c}.png 와 표준출력 「지도 시도수 (x,y,nonblack …)」"""
import sys, struct, subprocess, os, json
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS, NARC
S=os.environ.get('ROMDIR','')   # 롬 폴더(환경변수 ROMDIR, 끝에 /)
E_=os.path.dirname(os.path.abspath(__file__))+'/'
shard,n=map(int,sys.argv[1].split('/'))
OUT=os.environ.get('OUT','mapall')
raw=bytearray(open(S+os.environ.get('ROMF','final_new.nds'),'rb').read()); rom=NDS(bytes(raw))
ev=NARC(rom.get(hg1.NARC_PATHS['zone_event'])).files
sc=NARC(rom.get('a/0/1/2')).files[843]
base=bytes(raw).find(sc[:96]); assert base>=0
entries=[]; p=0
while p+4<=len(sc):
    v=struct.unpack_from('<I',sc,p)[0]
    if (v&0xFFFF)==0xFD13: break
    tg=p+4+v
    if 0<tg<len(sc)-16: entries.append(tg)
    p+=4
def warps(f):
    o=0; nb=struct.unpack_from('<I',f,o)[0]; o+=4+20*nb
    no=struct.unpack_from('<I',f,o)[0]; o+=4+32*no
    nw=struct.unpack_from('<I',f,o)[0]; o+=4
    return [struct.unpack_from('<HH',f,o+12*i) for i in range(nw)] if o+12*nw<=len(f) else []
maps=[m for m in json.load(open(E_+'allmaps.json')) if m<540]
if os.environ.get('MAPS'): maps=[int(x) for x in os.environ['MAPS'].split(',')]
sw={int(k):v for k,v in json.load(open(E_+'script_warps.json')).items()}
env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
if shard==0: print(len(maps),'maps',flush=True)
for k,m in enumerate(maps):
    if k%n!=shard: continue
    cands=[]
    if m in sw: cands+=[(x,y) for a,x,y,d in sw[m]]
    if m<len(ev): cands+=warps(ev[m])[:3]
    cands+=[(0,0),(8,8),(16,16)]
    seen=[]; res=None
    for (x,y) in cands:
        if (x,y) in seen: continue
        seen.append((x,y))
        code=struct.pack('<7H',176,m,0,x,y,1,2); img=bytearray(raw)
        for tg in entries: img[base+tg:base+tg+len(code)]=code
        p=E_+'mpa_%s_%d.nds'%(OUT,shard); open(p,'wb').write(img)
        d=E_+OUT+'/m%03d'%m; os.makedirs(d,exist_ok=True)
        try: out=subprocess.run(['python3',E_+'지도_이동시험_촬영.py',p,d],env=env,capture_output=True,text=True,timeout=400,cwd=E_).stdout.strip().splitlines()
        except Exception as e: out=['TIMEOUT']
        line=out[-1] if out else 'NO OUTPUT'
        res=(x,y,line)
        try: nz=float(line.split()[1])
        except Exception: nz=0
        if nz>=0.15 or line.startswith(('TIMEOUT','NO')) : break
    print(m,len(seen),res,flush=True)
