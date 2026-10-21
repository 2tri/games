"""한 장면 실행: python3 stage_play.py <롬> <상태.dst> <출력폴더> <얼굴 U/D/L/R> [최대반복]
연구소 NPC(위+A)로 롬 안 워프 스크립트를 돌려 현장에 도착 → 방향키로 NPC 쪽을 보고 → A 로 대화·전투를 끝까지 진행(전투는 Lv100 파티로 자동)
결과 JSON(<출력폴더>/res.json) + 대화 쪽마다 화면(<출력폴더>/pNN.png)"""
import sys,os,struct,json,hashlib
sys.path.insert(0,'/home/user/games'); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pkm,hg1
from hg1 import NDS,NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image
rom,state,out,face=sys.argv[1:5]; MAXIT=int(sys.argv[5]) if len(sys.argv)>5 else 400
os.makedirs(out,exist_ok=True)
R=NDS(open(rom,'rb').read()); personal=NARC(R.get(hg1.NARC_PATHS['personal'])).files
W=NARC(R.get('a/0/1/1')).files; PPD={i:W[i][6] for i in range(len(W)) if len(W[i])>6}
emu=DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(state)
KEYS={'U':Keys.KEY_UP,'D':Keys.KEY_DOWN,'L':Keys.KEY_LEFT,'R':Keys.KEY_RIGHT,'A':Keys.KEY_A,'B':Keys.KEY_B}
def run(n):
    for _ in range(n): emu.cycle(False)
def hold(k,fr,gap=4):
    m=keymask(k); emu.input.keypad_add_key(m); run(fr); emu.input.keypad_rm_key(m); run(gap)
def touch(x,y,h=8,g=40):
    emu.input.touch_set_pos(x,y); run(h); emu.input.touch_release(); run(g)
def is_dialog(im):
    t=im.crop((10,155,246,185)).convert('L'); d=list(t.getdata()); return sum(1 for v in d if v>225)/len(d)>0.55
def is_field(im):
    p=im.getpixel((128,300)); return abs(p[0]-24)<20 and abs(p[1]-200)<20 and abs(p[2]-112)<20
def is_menu(im):
    p=im.crop((0,192,256,384)).convert('RGB').getpixel((128,70)); return p[0]>180 and p[1]<90 and p[2]<90
u=lambda a: struct.unpack('<I',bytes(emu.memory.unsigned[a:a+4]))[0]
def pos(): return (u(0x0227de84),u(0x0227de8c),u(0x0227de90))
def find_party():
    ram=bytes(emu.memory.unsigned[0x02000000:0x02400000]); hits=[]
    for off in range(0,len(ram)-236,4):
        pid,_,ck=struct.unpack_from('<IHH',ram,off)
        if pid==0: continue
        try: d=pkm.decode(ram[off:off+236])
        except Exception: continue
        raw=b''.join(d['blocks'][c] for c in 'ABCD')
        if (sum(struct.unpack('<64H',raw))&0xFFFF)==ck and 0<pkm.species(d)<600 and 0<pkm.level(d)<=100: hits.append((0x02000000+off,pkm.species(d),pkm.level(d)))
    return hits
run(5)
hits=find_party()
if hits:
    tmpl=bytes(emu.memory.unsigned[hits[0][0]:hits[0][0]+236])
    new=pkm.make_mon(tmpl,252,100,[354,391,401,12],personal,0,pp=PPD)
    for a,_,_ in hits:
        for i,b in enumerate(new): emu.memory.unsigned[a+i]=b
# 워프 스크립트 돌리기(연구소 위쪽 NPC)
hold(Keys.KEY_UP,3,20); hold(Keys.KEY_A,4,60); run(300)
res={'map_after_warp':pos()}
if face=='-': run(120)              # 자동 장면: 도착만 하고 기다림
elif face[0]=='S': hold(KEYS[face[1]],18,30); run(60)     # 칸 밟기: 한 칸 걸어 들어감
else:
    hold(KEYS[face],6,10)           # 막혀서 제자리 → 방향만 돌림
    hold(Keys.KEY_A,4,40)
shots=[]; last=None; idle=0; battles=0; maxdlg=0; it=0; busy=0
for it in range(MAXIT):
    im=emu.screenshot().convert('RGB')
    if is_menu(im):
        battles+=1; touch(128,70,8,30); touch(64,55,8,60); run(120); idle=0; busy=0; continue
    if is_dialog(im):
        idle=0
        h=hashlib.md5(im.crop((0,140,256,192)).tobytes()).hexdigest()
        if h!=last and len(shots)<60:
            im.crop((0,0,256,192)).save('%s/p%02d.png'%(out,len(shots))); shots.append(it); last=h
        hold(Keys.KEY_A,4); run(45)
    elif is_field(im):
        idle+=1; busy=0
        if idle>=6: break
        run(40)
    else:                              # 전환·전투 연출·선택 화면: 기다림(가끔 A)
        busy+=1; idle=0
        if busy>150: break
        if busy%4==0: hold(Keys.KEY_A,4); run(20)
        else: run(40)
im=emu.screenshot().convert('RGB'); im.save('%s/end.png'%out)
res.update(pages=len(shots),battles=battles,iters=it+1,end_dialog=is_dialog(im),end_menu=is_menu(im),pos_end=pos(),party=[(s,l) for _,s,l in find_party()])
json.dump(res,open('%s/res.json'%out,'w'))
print(json.dumps(res))
