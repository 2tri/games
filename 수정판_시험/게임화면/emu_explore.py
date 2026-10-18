#!/usr/bin/env python3
"""에뮬레이터 칸 탐색 — 시작 상태에서 한 칸씩 걸어 갈 수 있는 칸·이동(문·계단) 칸을 찾는다. (Claude 작성, 2026-10-15)
사용:   python emu_explore.py <롬> <시작 상태.dst> <출력 폴더> [최대 칸 수=60]
출력:   <폴더>/tiles.txt (칸 → 갈 수 있는 방향, 이동 칸 → 이동 뒤 좌표·화면 밝기), 칸마다 t_<x>_<y>.dst
좌표:   RAM 0x0227DEE4(X)·0x0227DEE8(Y) — 한 칸 걸을 때마다 1 변함(10/15 확인)"""
import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, st0, out = sys.argv[1:4]; MAXN = int(sys.argv[4]) if len(sys.argv) > 4 else 60
os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def rd16(a): return emu.memory.unsigned[a] | (emu.memory.unsigned[a + 1] << 8)
def pos(): return rd16(0x0227DEE4), rd16(0x0227DEE8)
DIRS = {'U': (Keys.KEY_UP, 0, -1), 'D': (Keys.KEY_DOWN, 0, 1), 'L': (Keys.KEY_LEFT, -1, 0), 'R': (Keys.KEY_RIGHT, 1, 0)}
def bright():
    im = emu.screenshot().convert('L').crop((0, 0, 256, 192)); return sum(im.getdata()) / (256 * 192)
emu.savestate.load_file(st0); run(10)
start = pos(); seen = {start: st0}; frontier = [start]; log = []
while frontier and len(seen) < MAXN:
    t = frontier.pop(0)
    for dn, (k, dx, dy) in DIRS.items():
        emu.savestate.load_file(seen[t]); run(6)
        if pos() != t:
            run(12)
            if pos() != t: continue
        m = keymask(k); emu.input.keypad_add_key(m); run(10); emu.input.keypad_rm_key(m); run(26)
        b1 = bright(); p = pos()
        if p == t:
            # 방향만 돌았거나 막힘 — 한 번 더
            m = keymask(k); emu.input.keypad_add_key(m); run(10); emu.input.keypad_rm_key(m); run(26); p = pos(); b1 = bright()
        if p == t: log.append('%s %s 막힘' % (t, dn)); continue
        if (abs(p[0] - t[0]) + abs(p[1] - t[1])) == 1 and p == (t[0] + dx, t[1] + dy):
            log.append('%s %s → %s' % (t, dn, p))
            if p not in seen:
                f = os.path.join(out, 't_%d_%d.dst' % p); emu.savestate.save_file(f); seen[p] = f; frontier.append(p)
        else:
            run(60); b2 = bright(); p2 = pos()
            f = os.path.join(out, 'warp_%d_%d_%s.dst' % (t[0], t[1], dn)); emu.savestate.save_file(f)
            emu.screenshot().save(os.path.join(out, 'warp_%d_%d_%s.png' % (t[0], t[1], dn)))
            log.append('%s %s 이동! → %s (밝기 %.0f/%.0f) %s' % (t, dn, p2, b1, b2, os.path.basename(f)))
open(os.path.join(out, 'tiles.txt'), 'w', encoding='utf-8').write('\n'.join(log) + '\n')
print('칸 %d, 기록 %d줄' % (len(seen), len(log)))
for l in log:
    if '이동' in l: print(l)
