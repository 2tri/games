import struct, os, sys, json, collections, hashlib
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, start = sys.argv[1], sys.argv[2]
emu=DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
u=lambda a: struct.unpack('<I',bytes(emu.memory.unsigned[a:a+4]))[0]
def pos(): return (u(0x0227de78), u(0x0227de58), u(0x0227de5c))
def is_field(im):
    p=im.getpixel((128,300)); return abs(p[0]-24)<20 and abs(p[1]-200)<20 and abs(p[2]-112)<20
def is_menu(im):
    p=im.crop((0,192,256,384)).convert('RGB').getpixel((128,70)); return p[0]>180 and p[1]<90 and p[2]<90
def touch(x,y):
    emu.input.touch_set_pos(x,y); run(8); emu.input.touch_release(); run(40)
def press(k,h=4,g=30):
    m=keymask(k); emu.input.keypad_add_key(m); run(h); emu.input.keypad_rm_key(m); run(g)
def settle():
    # 미끄러짐·전투·대화가 끝날 때까지
    last=None; same=0; battles=0
    for it in range(400):
        run(20); im=emu.screenshot().convert('RGB')
        if is_menu(im): battles+=1; touch(128,70); touch(64,55); run(100); same=0; continue
        if not is_field(im):
            if it%3==0: press(Keys.KEY_A)
            same=0; continue
        p=pos()
        if p==last: same+=1
        else: same=0; last=p
        if same>=3: return p, battles
    return pos(), battles
D={'U':Keys.KEY_UP,'D':Keys.KEY_DOWN,'L':Keys.KEY_LEFT,'R':Keys.KEY_RIGHT}
emu.savestate.load_file(start); run(10)
p0,_=settle(); print('start',p0,flush=True)
# 돌판 상태까지 구분: 지도 오브젝트 영역 해시 대신 RAM 일부 해시(위치 제외)는 불확실 → 위치+경로 길이 제한 BFS
seen={p0:('',None)}; Q=collections.deque([(p0,'')]); n=0
emu.savestate.save_file('gx/0.dst'); sid={p0:'gx/0.dst'}
best=p0
while Q:
    p,path=Q.popleft()
    for d in 'ULRD':
        emu.savestate.load_file(sid[p]); run(2)
        m=keymask(D[d]); emu.input.keypad_add_key(m); run(16); emu.input.keypad_rm_key(m)
        q,b=settle()
        if q[0]!=p0[0] or q[2]>=87: continue
        if q not in seen:
            n+=1; f='gx/%d.dst'%n; emu.savestate.save_file(f); sid[q]=f; seen[q]=(path+d,p); Q.append((q,path+d))
            if q[2]<best[2]: best=q; print('new best',q,path+d,flush=True); emu.screenshot().save('gx/best.png')
            if q[2]<=4: print('GOAL',q,path+d,flush=True); json.dump({'path':path+d},open('gx/goal.json','w')); sys.exit(0)
    if n%10==0: print('nodes',n,'queue',len(Q),flush=True)
print('NO PATH; visited',len(seen),'best',best,seen[best][0],flush=True)
json.dump({str(k):v[0] for k,v in seen.items()},open('gx/seen.json','w'))
