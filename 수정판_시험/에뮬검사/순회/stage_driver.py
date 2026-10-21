"""스테이지 순회: python3 stage_driver.py [시작인덱스 끝인덱스] — stages.json 의 장면을 4개씩 병렬로 실행. 결과 stages_out/<번호>/ , 요약 stages_out/summary.jsonl"""
import sys,os,json,struct,subprocess,shutil,time
from multiprocessing import Pool
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS,NARC
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
raw=bytearray(open('rom.nds','rb').read()); rom=NDS(bytes(raw))
sc=NARC(rom.get('a/0/1/2')).files[843]; base=bytes(raw).find(sc[:96]); assert base>=0
entries=[]; p=0
while p+4<=len(sc):
    v=struct.unpack_from('<I',sc,p)[0]
    if (v&0xFFFF)==0xFD13: break
    tg=p+4+v
    if 0<tg<len(sc)-40: entries.append(tg)
    p+=4
stages=json.load(open('stages.json'))
CAND=((0,1,'U'),(1,0,'L'),(-1,0,'R'),(0,-1,'D'))
def work(i):
    s=stages[i]; d='stages_out/%03d'%i; os.makedirs(d,exist_ok=True)
    best=None
    for ci,(dx,dy,key) in enumerate(CAND):
        code=(struct.pack('<HH',0x1f,s['hide']) if s['hide'] else b'')+struct.pack('<6H',176,s['map'],0,s['x']+dx,s['y']+dy,1)+struct.pack('<H',2)
        img=bytearray(raw)
        for tg in entries: img[base+tg:base+tg+len(code)]=code
        rp='%s/rom.nds'%d; open(rp,'wb').write(img)
        od='%s/c%d'%(d,ci)
        try: r=subprocess.run(['python3','stage_play.py',rp,'start.dst',od,key,'400'],capture_output=True,text=True,timeout=420,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
        except Exception as e: continue
        try: res=json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: continue
        res['cand']=ci; res['key']=key
        if best is None or res['pages']+res['battles']>best['pages']+best['battles']: best=res
        if res['pages']>0 or res['battles']>0: break
    os.remove('%s/rom.nds'%d) if os.path.exists('%s/rom.nds'%d) else None
    out=dict(i=i,map=s['map'],obj=s['obj'],xy=(s['x'],s['y']),feat=s['feat'],res=best)
    open('stages_out/summary.jsonl','a').write(json.dumps(out,ensure_ascii=False)+'\n')
    return out
if __name__=='__main__':
    a=int(sys.argv[1]) if len(sys.argv)>1 else 0; b=int(sys.argv[2]) if len(sys.argv)>2 else len(stages)
    os.makedirs('stages_out',exist_ok=True)
    with Pool(4) as pool:
        for o in pool.imap_unordered(work,range(a,b)): print(o['i'],o['map'],o['obj'],(o['res'] or {}).get('pages'),(o['res'] or {}).get('battles'),flush=True)
