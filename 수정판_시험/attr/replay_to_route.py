"""전원부터 스타팅 받고 풀숲 지도 38 까지 (이 롬에서 새로 만든 상태) — python3 replay.py <rom> <out.dst>"""
import sys, os, struct
os.environ.setdefault('SDL_VIDEODRIVER','dummy'); os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
KM = {k: getattr(Keys, 'KEY_'+k) for k in 'A B X Y L R START SELECT UP DOWN LEFT RIGHT'.split()}
rom, out = sys.argv[1:3]
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def do(acts):
    for tok in acts.split():
        if tok[0]=='w' and tok[1:].isdigit(): run(int(tok[1:])); continue
        if tok[0]=='t' and ',' in tok:
            x,y = map(int, tok[1:].split(',')); emu.input.touch_set_pos(x,y); run(6); emu.input.touch_release(); run(20); continue
        rep=1
        if '*' in tok: tok,r = tok.split('*'); rep=int(r)
        hold,gap=4,16
        if ':' in tok:
            tok,h = tok.split(':')
            if '/' in h: h,g=h.split('/'); gap=int(g)
            hold=int(h)
        k = keymask(KM[tok.upper()])
        for _ in range(rep):
            emu.input.keypad_add_key(k); run(hold); emu.input.keypad_rm_key(k); run(gap)
LOC = [None]
def loc():
    if LOC[0] is None:
        ram = bytes(emu.memory.unsigned[0x02270000:0x02290000]); h = ram.find(struct.pack('<4I', 64, 0xFFFFFFFF, 6, 6))
        if h < 0: return (0, 0, 0, 0, 0)
        LOC[0] = 0x02270000 + h; print('위치 구조', hex(LOC[0]), flush=True)
    return struct.unpack('<5I', bytes(emu.memory.unsigned[LOC[0]:LOC[0] + 20]))
STEPS = [
 ("w900 A w200 A w200 A w300", None),
 ("t128,155 w60 A w60 A*10 w100", None),
 ("A*40 w60 A*40 w60", None),
 ("START w60 A w60 A*60 w60 A*60 w60", (64,)),
 ("UP:16/4 LEFT:16/4*6 w150 LEFT:16/4 w60 LEFT:16/4 w200", (64, None, 3, 5)),
 ("UP:20/4 w200", (64, None, 3, 4)),
 ("LEFT:20/4 w250", (63,)),
 ("w60 A*40 w100", (63,)),
 ("B w20 DOWN:130/4 w250", (60,)),
 ("A w60 A*10 w60 LEFT:16/4*3 w30 w200 A*30 w100 A*30 w100", (60,)),
 ("DOWN:16/4 LEFT:16/4 LEFT:16/4 w30", (60, None, 693, 398)),
 ("LEFT:16/4*9 w10 UP:16/4*5 w200", (61,)),
 ("w100 A*80 w100 UP:16/4*3 w60 A*60 w100 UP:16/4*4 w60 A*80 w100", (61, None, 4, 7)),
 ("A:4/30*120 w100 RIGHT:16/4*4 UP:16/4 w30 A w100", (61, None, 8, 6)),
 ("UP:16/4 w20 A w300 A w60 t128,110 w150 t130,151 w150 w60 t118,95 w150 A w100", None),
 ("A:4/30*16 START w30 A w100 A:4/30*80", (61, None, 4, 7)),
]
for i, (acts, want) in enumerate(STEPS):
    do(acts); l = loc()
    ok = want is None or all(w is None or w == v for w, v in zip(want, l))
    print(i, l, 'ok' if ok else 'MISMATCH want %s' % (want,), flush=True)
    if not ok: emu.screenshot().save('replay_fail.png'); os._exit(1)
# 연구소 문 워프를 지도 38 로
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); h = ram.find(struct.pack('<HHHH', 4, 14, 60, 0))
for j, v in enumerate(struct.pack('<HH', 38, 0)): emu.memory.unsigned[0x02000000 + h + 4 + j] = v
do("DOWN:128/4 w300 A:4/30*25 DOWN:16/4*4 w300 DOWN:16/4*3 w300")
print('end', loc(), flush=True)
emu.savestate.save_file(out); emu.screenshot().save('replay_end.png')
os._exit(0 if loc()[0] == 38 else 1)
