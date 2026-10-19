#!/usr/bin/env python3
"""에뮬레이터 RAM 의 파티를 바꾸고 화면을 저장한다. (Claude 작성, 2026-10-15)
사용:   python emu_party.py <롬> <상태.dst> <출력 이름표> <종 칸 목록(쉼표)> [동작...]
동작:   party = 「디지몬」 터치 → 파티 화면 캡처, 닫기 / menu / field N = N 프레임 뒤 캡처 / sum = 첫 칸 요약 화면(앞모습) / walk = 위·아래·왼·오 한 칸씩 캡처
        결과 = <출력 이름표>_<동작>.png"""
import sys, os, struct
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
import pk4
rom, st, tag, spl = sys.argv[1:5]; acts = sys.argv[5:]
SP = [int(x) for x in spl.split(',')]
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(st)
def run(n):
    for _ in range(n): emu.cycle(False)
run(10)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); pat = struct.pack('<II', 6, 1); o = ram.find(pat)
while o >= 0:
    d = pk4.decode(ram[o + 8:o + 244]); body = b''.join(d['blocks'][c] for c in d['order'])
    if sum(struct.unpack('<64H', body)) & 0xFFFF == struct.unpack_from('<H', ram, o + 14)[0]: break
    o = ram.find(pat, o + 4)
assert o >= 0, '파티를 못 찾음'
base = 0x02000000 + o; first = ram[o + 8:o + 244]
def wr(addr, data):
    for i, b in enumerate(data): emu.memory.unsigned[addr + i] = b
for i, s in enumerate(SP[:6]):
    raw = pk4.with_species(first, s)
    # PID 를 칸마다 조금 바꿔 서로 다른 개체로(같은 PID 면 게임이 같은 것으로 볼 수 있음)
    d = pk4.decode(raw); d['pid'] = (d['pid'] + 0x10001 * i) & 0xFFFFFFFF
    wr(base + 8 + 236 * i, pk4.encode(d))
wr(base + 4, struct.pack('<I', min(6, len(SP))))
run(5)
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(40)
def shot(name): emu.screenshot().save('%s_%s.png' % (tag, name))
for a in acts:
    if a == 'party': touch(50, 76); run(60); shot('party'); press(Keys.KEY_B, 4, 60)
    elif a == 'field': run(60); shot('field')
    elif a.startswith('wait'): run(int(a[4:]))
    elif a == 'sum': touch(50, 76); run(60); press(Keys.KEY_A, 4, 40); press(Keys.KEY_A, 4, 60); shot('sum'); press(Keys.KEY_B, 4, 40); press(Keys.KEY_B, 4, 40); press(Keys.KEY_B, 4, 40)
    elif a == 'walk':
        for nm, k in (('U', Keys.KEY_UP), ('D', Keys.KEY_DOWN), ('L', Keys.KEY_LEFT), ('R', Keys.KEY_RIGHT)):
            m = keymask(k); emu.input.keypad_add_key(m); run(20); emu.input.keypad_rm_key(m); run(8); shot('walk' + nm)
if acts and acts[-1].startswith('save='): emu.savestate.save_file(acts[-1][5:])
print('끝', SP)
