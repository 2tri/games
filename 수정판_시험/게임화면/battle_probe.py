#!/usr/bin/env python3
"""워프로 풀숲 있는 지도로 가서 무작위로 걷다가 야생 전투가 열리면 화면을 저장하고 첫 턴까지 진행. (Claude 작성, 2026-10-16)
사용:   python battle_probe.py <롬> <문 앞 상태.dst> <지도 번호> <출력 폴더> [<걸음 수>]
        결과: <폴더>/b<지도>_*.png, <폴더>/b<지도>.dst(전투 시작 직후 상태)"""
import sys, os, struct, random
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageChops
rom, st, mp, out = sys.argv[1:5]; steps = int(sys.argv[5]) if len(sys.argv) > 5 else 500
mp = int(mp); os.makedirs(out, exist_ok=True); random.seed(mp)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
emu.savestate.load_file(st); run(3)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); h = ram.find(struct.pack('<HHHHHH', 684, 393, 61, 0, 0, 0)); H = 0x02000000 + h
for j, v in enumerate(struct.pack('<HH', mp, 0)): emu.memory.unsigned[H + 4 + j] = v
m = keymask(Keys.KEY_UP); emu.input.keypad_add_key(m); run(24); emu.input.keypad_rm_key(m); run(260)
emu.screenshot().save(os.path.join(out, 'b%03d_arrive.png' % mp))
KEYS = [Keys.KEY_UP, Keys.KEY_DOWN, Keys.KEY_LEFT, Keys.KEY_RIGHT]
prev = emu.screenshot().convert('L').crop((0, 0, 256, 192)); battle = False
dirn = random.choice(KEYS)
for i in range(steps):
    if i % 6 == 0: dirn = random.choice(KEYS)
    m = keymask(dirn); emu.input.keypad_add_key(m); run(16); emu.input.keypad_rm_key(m); run(4)
    cur = emu.screenshot().convert('L').crop((0, 0, 256, 192))
    d = ImageChops.difference(cur, prev); hist = d.histogram(); big = sum(hist[40:])
    if big > 256 * 192 * 0.5 or ImageChops.difference(cur, prev).getbbox() is None and False:
        battle = True; break
    prev = cur
if not battle: print('전투 안 열림', mp, flush=True); os._exit(0)
run(300); emu.screenshot().save(os.path.join(out, 'b%03d_1.png' % mp))
for k in range(6): press(Keys.KEY_A, 4, 90)
emu.screenshot().save(os.path.join(out, 'b%03d_2.png' % mp)); emu.savestate.save_file(os.path.join(out, 'b%03d.dst' % mp))
print('전투 열림', mp, 'step', i, flush=True); os._exit(0)
