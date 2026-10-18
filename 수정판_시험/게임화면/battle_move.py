#!/usr/bin/env python3
"""전투에서 우리 디지몬의 필살기를 실제로 써 본다. (Claude 작성, 2026-10-16)
사용:   python battle_move.py <롬> <문 앞 상태.dst> <지도> <종 칸> <레벨> <기술 번호> <출력 폴더>
방법:   워프로 풀숲 지도에 가서(map_sweep 과 같은 방법) 맨 앞 파티를 <종 칸>·<레벨>·기술 <번호> 하나로 바꾸고(체력 크게) 야생 전투가 열릴 때까지 걸은 뒤,
        글을 넘기고 「싸운다」→ 첫 기술을 눌러 연출·데미지가 나는지 화면을 저장(<폴더>/mv_1~8.png)"""
import sys, os, struct, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pk4
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageChops
rom, st, mp, sp, lv, mv, out = sys.argv[1:8]; mp, sp, lv, mv = int(mp), int(sp), int(lv), int(mv); os.makedirs(out, exist_ok=True); random.seed(mp * 7 + 272 + int(os.environ.get("SEED", "0")))
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(70)
emu.savestate.load_file(st); run(3)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); H = 0x02000000 + ram.find(struct.pack('<HHHHHH', 684, 393, 61, 0, 0, 0))
for j, v in enumerate(struct.pack('<HH', mp, 0)): emu.memory.unsigned[H + 4 + j] = v
# 파티 맨 앞 바꾸기. 필드에서는 파티 자료가 풀린 채(머리 4~5바이트 = 06 00, 검산 0)로 RAM 에 있을 수 있음 → 그땐 풀린 자리를 직접 고침(암호 걸린 자료를 쓰면 전투가 멈춤)
o = ram.find(struct.pack('<II', 6, 1)); base = 0x02000000 + o; first = ram[o + 8:o + 244]
dec_mode = struct.unpack_from('<H', first, 6)[0] == 0 and first[4:6] == bytes([6, 0])
pid = struct.unpack_from('<I', first, 0)[0]; order = pk4.ORDERS[((pid >> 13) & 31) % 24]
if os.environ.get('PLAIN_ORDER', '1') == '1' and dec_mode: order = 'ABCD'     # 풀린 파티 자료는 블록이 섞이지 않은 ABCD 순서(10/16 가정, 시험으로 확인)
def wr(off, data):
    for j_, v_ in enumerate(data): emu.memory.unsigned[base + 8 + off + j_] = v_
if dec_mode:
    if sp: wr(8 + 32 * order.index('A'), struct.pack('<H', sp))
    if mv: wr(8 + 32 * order.index('B') + 0, struct.pack('<4H', mv, 0, 0, 0)); wr(8 + 32 * order.index('B') + 8, bytes([30, 0, 0, 0]))
    if lv: wr(136 + 4, bytes([lv]))
    print('풀린 자료 모드', order, flush=True)
else:
    d = pk4.decode(pk4.with_species(first, sp, lv or None))
    if mv:
        b = bytearray(d['blocks']['B']); struct.pack_into('<4H', b, 0, mv, 0, 0, 0); b[8:12] = bytes([30, 0, 0, 0]); d['blocks']['B'] = bytes(b)
    p = bytearray(d['party']); d['party'] = bytes(p)
    raw = pk4.encode(d)
    if sp:
        for j, v in enumerate(raw): emu.memory.unsigned[base + 8 + j] = v
m = keymask(Keys.KEY_UP); emu.input.keypad_add_key(m); run(24); emu.input.keypad_rm_key(m); run(260)
KEYS = [Keys.KEY_UP, Keys.KEY_DOWN, Keys.KEY_LEFT, Keys.KEY_RIGHT]
prev = emu.screenshot().convert('L').crop((0, 0, 256, 192)); battle = False; dirn = random.choice(KEYS)
for i in range(700):
    if i % 6 == 0: dirn = random.choice(KEYS)
    mm = keymask(dirn); emu.input.keypad_add_key(mm); run(16); emu.input.keypad_rm_key(mm); run(4)
    cur = emu.screenshot().convert('L').crop((0, 0, 256, 192)); hist = ImageChops.difference(cur, prev).histogram()
    if sum(hist[40:]) > 256 * 192 * 0.5:
        run(240); px_ = emu.screenshot().convert('RGB').getpixel((30, 330))
        if px_[0] > 200 and px_[1] > 225 and px_[2] > 170: battle = True; break          # 전투 아래 화면(연한 연두 바탕)일 때만 전투
        cur = emu.screenshot().convert('L').crop((0, 0, 256, 192))
    prev = cur
if not battle: print('전투 안 열림'); sys.stdout.flush(); os._exit(0)
run(200); shots = []
for k in range(16):
    press(Keys.KEY_A, 4, 90)
    if k % 2 == 1: shots.append(emu.screenshot().copy())
touch(128, 96); shots.append(emu.screenshot().copy())            # 싸운다
touch(70, 60); run(30); shots.append(emu.screenshot().copy())    # 첫 기술
for k in range(7): run(35); shots.append(emu.screenshot().copy())
for i, s in enumerate(shots): s.save(os.path.join(out, 'mv%d_%d.png' % (sp, i + 1)))
print('끝', len(shots)); sys.stdout.flush(); os._exit(0)
