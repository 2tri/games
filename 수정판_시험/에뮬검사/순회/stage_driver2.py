"""장면·칸 이벤트 순회: python3 stage_driver2.py [시작 끝] — stages2.json (레벨 스크립트 장면 109 + 칸 이벤트 197). 변수 미리 세팅 → 도착 → 자동 진행. 결과 stages2_out/"""
import sys,os,json,struct,subprocess
from multiprocessing import Pool
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS,NARC
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
raw=bytearray(open('rom.nds','rb').read()); rom=NDS(bytes(raw))
sc=NARC(rom.get('a/0/1/2')).files[843]; base=bytes(raw).find(sc[:96])
entries=[]; p=0
while p+4<=len(sc):
    v=struct.unpack_from('<I',sc,p)[0]
    if (v&0xFFFF)==0xFD13: break
    tg=p+4+v
    if 0<tg<len(sc)-60: entries.append(tg)
    p+=4
ev=NARC(rom.get(hg1.NARC_PATHS['zone_event'])).files; H=json.load(open('../hdr.json'))
S2=json.load(open('stages2.json'))
def spots(mp):
    e=H[mp]['event']; g=ev[e]; o=0; nb=struct.unpack_from('<I',g,o)[0]; o+=4+20*nb; no=struct.unpack_from('<I',g,o)[0]; o+=4
    obj=[struct.unpack_from('<16H',g,o+32*i) for i in range(no)]; o+=32*no
    nw=struct.unpack_from('<I',g,o)[0]; o+=4; wp=[struct.unpack_from('<HHHHI',g,o+12*i) for i in range(nw)]
    return obj,wp
def work(i):
    s=S2[i]; d='stages2_out/%03d'%i; os.makedirs(d,exist_ok=True)
    pre=struct.pack('<HHH',0x29,s['var'],s['val']) if s['var'] else b''
    if s['kind']=='칸':
        x,y,w,h=s['x'],s['y'],s.get('w',1),s.get('h',1)
        cands=[((x,y+h),'SU'),((x,y-1),'SD'),((x-1,y),'SR'),((x+w,y),'SL')]
    else:
        try: obj,wp=spots(s['map'])
        except Exception: obj,wp=[],[]
        if wp: cands=[((wp[0][0],wp[0][1]-1),'-'),((wp[0][0],wp[0][1]+1),'-')]
        elif obj: cands=[((obj[0][12],obj[0][13]+1),'-')]
        else: cands=[((8,8),'-')]
    best=None
    for ci,((ax,ay),key) in enumerate(cands):
        code=pre+struct.pack('<6H',176,s['map'],0,ax,ay,1)+struct.pack('<H',2)
        img=bytearray(raw)
        for tg in entries: img[base+tg:base+tg+len(code)]=code
        rp='%s/rom.nds'%d; open(rp,'wb').write(img); od='%s/c%d'%(d,ci)
        try: r=subprocess.run(['python3','stage_play.py',rp,'start.dst',od,key,'400'],capture_output=True,text=True,timeout=420,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
        except Exception: continue
        try: res=json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: continue
        res['cand']=ci; res['key']=key
        if best is None or res['pages']+res['battles']>best['pages']+best['battles']: best=res
        if res['pages']>0 or res['battles']>0: break
    if os.path.exists('%s/rom.nds'%d): os.remove('%s/rom.nds'%d)
    out=dict(i=i,**{k:v for k,v in s.items()},res=best)
    open('stages2_out/summary.jsonl','a').write(json.dumps(out,ensure_ascii=False)+'\n'); return out
if __name__=='__main__':
    a=int(sys.argv[1]) if len(sys.argv)>1 else 0; b=int(sys.argv[2]) if len(sys.argv)>2 else len(S2)
    os.makedirs('stages2_out',exist_ok=True)
    with Pool(4) as pool:
        for o in pool.imap_unordered(work,range(a,b)): print(o['i'],o['kind'],o['map'],(o['res'] or {}).get('pages'),(o['res'] or {}).get('battles'),flush=True)
