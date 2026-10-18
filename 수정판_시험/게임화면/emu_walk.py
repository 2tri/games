#!/usr/bin/env python3
"""에뮬레이터 걷기 도구 — 저장 상태에서 시작해 입력 줄을 실행하고 화면을 저장한다. (Claude 작성, 2026-10-15)
사용:   python emu_walk.py <롬> <시작 상태.dst|boot> <끝 상태.dst> "<입력 줄>" [화면.png]
입력:   U3 D2 L1 R4 = 방향키를 n 칸만큼(칸당 17프레임)  /  A B S(시작) X Y(키) = 한 번 누름  /  A*5 = 5번 누름(30프레임 간격)
        GX9 / GY3 = 플레이어 칸 좌표가 그 값이 될 때까지 걷기(pos = 현재 좌표 출력)
        W60 = 60프레임 기다림  /  T130,150 = 아래 화면 터치  /  AUTO30 = A 를 30번(40프레임 간격) — 대사 넘기기
        shot = 그때 화면 저장(shot_<번호>.png, 화면 인자가 있을 때 폴더로)
시작 상태가 boot 이면 s_boot.dst(전원 직후)에서 시작."""
import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
HERE = os.path.dirname(os.path.abspath(__file__))
rom, st_in, st_out, script = sys.argv[1:5]
shot = sys.argv[5] if len(sys.argv) > 5 else None
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
emu.savestate.load_file(os.path.join(HERE, 's_boot.dst') if st_in == 'boot' else st_in)
def run(n):
    for _ in range(n): emu.cycle(False)
KEY = {'U': Keys.KEY_UP, 'D': Keys.KEY_DOWN, 'L': Keys.KEY_LEFT, 'R': Keys.KEY_RIGHT, 'A': Keys.KEY_A, 'B': Keys.KEY_B, 'S': Keys.KEY_START, 'X': Keys.KEY_X, 'Y': Keys.KEY_Y}
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def hold_dir(k, tiles):
    m = keymask(k); emu.input.keypad_add_key(m); run(int(17 * tiles)); emu.input.keypad_rm_key(m); run(10)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(30)
def rd16(a): return emu.memory.unsigned[a] | (emu.memory.unsigned[a + 1] << 8)
XA, YA = 0x0227DEE4, 0x0227DEE8          # 플레이어 칸 좌표(지도 안 좌표, 10/15 에뮬레이터로 찾음: 한 칸 걸을 때마다 1 변함. 0x021DAF7E 쪽은 NPC 위치도 섞임)
def pos(): return rd16(XA), rd16(YA)
def goto(axis, target, limit=40):
    # 축 방향으로 target 칸이 될 때까지 한 칸씩(막히면 그만)
    key = {'X': (Keys.KEY_RIGHT, Keys.KEY_LEFT), 'Y': (Keys.KEY_DOWN, Keys.KEY_UP)}[axis]
    for _ in range(limit):
        cur = pos()[0 if axis == 'X' else 1]
        if cur == target: return True
        k = key[0] if target > cur else key[1]
        m = keymask(k); emu.input.keypad_add_key(m); run(17); emu.input.keypad_rm_key(m); run(8)
        if pos()[0 if axis == 'X' else 1] == cur:     # 안 움직임(막힘/방향만 돎) → 한 번 더
            m = keymask(k); emu.input.keypad_add_key(m); run(17); emu.input.keypad_rm_key(m); run(8)
            if pos()[0 if axis == 'X' else 1] == cur: return False
    return False
n_shot = 0
for tok in script.split():
    if tok == 'shot':
        n_shot += 1
        if shot: emu.screenshot().save(shot.replace('.png', '_%d.png' % n_shot))
        continue
    if tok == 'pos': print('pos', pos()); continue
    if tok[:2] in ('GX', 'GY'):
        ok = goto(tok[1], int(tok[2:])); print('goto', tok, ok, pos()); continue
    if tok.startswith('AUTO'):
        for _ in range(int(tok[4:] or 20)): press(Keys.KEY_A, 4, 40)
        continue
    if tok.startswith('W'): run(int(tok[1:])); continue
    if tok.startswith('T') and ',' in tok:
        x, y = tok[1:].split(','); touch(int(x), int(y)); continue
    if '*' in tok:
        k, c = tok.split('*')
        for _ in range(int(c)): press(KEY[k], 4, 30)
        continue
    k, c = tok[0], tok[1:]
    if k in 'UDLR' and c: hold_dir(KEY[k], float(c)); continue
    if k in KEY: press(KEY[k], 4, 30); continue
    sys.exit('모르는 입력: ' + tok)
emu.savestate.save_file(st_out)
if shot and n_shot == 0: emu.screenshot().save(shot)
print('끝')
