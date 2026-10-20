"""python walk.py rom in.dst out.dst "R4 D2 A A" shot.png  — 글자=방향(UDLR)/A/B/S(start), 숫자=칸 수(걸음 16프레임)"""
import sys, re
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, si, so, seq, shot = sys.argv[1:6]
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(si)
def run(n):
    for _ in range(n): emu.cycle(False)
K = {'d': Keys.KEY_DOWN, 'u': Keys.KEY_UP, 'U': Keys.KEY_UP, 'D': Keys.KEY_DOWN, 'L': Keys.KEY_LEFT, 'R': Keys.KEY_RIGHT, 'A': Keys.KEY_A, 'B': Keys.KEY_B, 'S': Keys.KEY_START}
run(5)
import struct
for tok in seq.split():
    if tok.startswith('W'): run(int(tok[1:])); continue
    if tok.startswith('M'):   # M주소=값(u16)
        a, v = tok[1:].split('='); a = int(a, 16); v = int(v)
        emu.memory.unsigned[a] = v & 255; emu.memory.unsigned[a + 1] = v >> 8; continue
    if tok.startswith('X'):   # X도착지도 : 지금 지도 워프 표에서 (3,4,63,1) 줄을 찾아 도착지를 바꿈
        ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); h = ram.find(struct.pack('<4H', 3, 4, 63, 1))
        print('warp', hex(0x02000000 + h)); a = 0x02000000 + h + 4; v = int(tok[1:])
        emu.memory.unsigned[a] = v & 255; emu.memory.unsigned[a + 1] = v >> 8; emu.memory.unsigned[a + 2] = 0; emu.memory.unsigned[a + 3] = 0; continue
    if tok == 'P':
        print('pos', struct.unpack('<5i', bytes(emu.memory.unsigned[0x0227DF14:0x0227DF28]))); continue
    if tok.startswith('T'):
        x, y = map(int, tok[1:].split(',')); emu.input.touch_set_pos(x, y); run(8); emu.input.touch_release(); run(40); continue
    k = tok[0]; n = int(tok[1:]) if len(tok) > 1 else 1
    m = keymask(K[k])
    if k in 'UDLR':
        emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
    else:
        for _ in range(n): emu.input.keypad_add_key(m); run(4); emu.input.keypad_rm_key(m); run(40)
run(30)
emu.screenshot().save(shot); emu.savestate.save_file(so)
