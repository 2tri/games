#!/usr/bin/env python3
"""지도 순회(워프) — 지도 번호를 하나씩 정해 그 지도로 들어가 화면을 찍는다. (Claude 작성, 2026-10-16)
사용:   python map_sweep.py <롬> <문 앞 상태.dst> <출력 폴더> <처음> <끝> [<간격>]
방법:   시작 마을(지도 60)의 연구소 문 앞(684,394)에서 시작한 상태를 불러, RAM 에 올라온 그 문의 「워프 표」(x 684 · y 393 · 도착 지도 61 · 도착 문 0)의
        도착 지도 칸만 N 으로 바꾸고 위로 한 칸 걸어 문에 들어간다 → 3~4초 뒤 화면·현재 위치(RAM 0x0227DEDC: 지도·문·x·y·방향)를 저장.
        도착 문 0 = 그 지도 워프 표의 0번 문 앞에 나옴(워프 표가 없는 지도는 엉뚱한 곳 → 「워프 없음」으로 기록).
결과:   <폴더>/m<번호>.png(위·아래 화면), <폴더>/결과_<처음>.tsv(번호 / 도착 지도 / x / y / 상태 / 화면 변화)"""
import sys, os, struct
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageChops
rom, st, out, a, b = sys.argv[1:6]; step = int(sys.argv[6]) if len(sys.argv) > 6 else 1
a, b = int(a), int(b); os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def rd(addr, n): return bytes(emu.memory.unsigned[addr:addr + n])
LOC = 0x0227DEDC
WARP = struct.pack('<HHHHHH', 684, 393, 61, 0, 0, 0)
# 뒤에서 읽을 지도 머리말(워프 표 개수) 은 호출하는 쪽에서 안 씀 — 결과 표에 도착 위치만 적는다
emu.savestate.load_file(st); run(5)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); h = ram.find(WARP)
if h < 0: sys.exit('워프 표를 RAM 에서 못 찾음')
H = 0x02000000 + h
lines = []
for n in range(a, b, step):
    emu.savestate.load_file(st); run(3)
    for j, v in enumerate(struct.pack('<HH', n, 0)): emu.memory.unsigned[H + 4 + j] = v
    m = keymask(Keys.KEY_UP); emu.input.keypad_add_key(m); run(24); emu.input.keypad_rm_key(m)
    run(200)
    s1 = emu.screenshot().copy(); loc = struct.unpack('<5I', rd(LOC, 20))
    run(120); s2 = emu.screenshot().copy()
    diff = ImageChops.difference(s1.convert('RGB'), s2.convert('RGB')).getbbox() is not None
    black = s2.convert('L').getextrema()[1] < 12
    state = '도착' if loc[0] == n else ('다른 지도 %d' % loc[0])
    if black: state += ' / 화면 검정'
    s2.save(os.path.join(out, 'm%03d.png' % n))
    lines.append('%d\t%d\t%d\t%d\t%s\t%s' % (n, loc[0], loc[2], loc[3], state, '움직임 있음' if diff else '화면 그대로'))
    open(os.path.join(out, '결과_%03d.tsv' % a), 'w', encoding='utf-8').write('번호\t도착 지도\tx\ty\t상태\t화면 변화\n' + '\n'.join(lines) + '\n')
print('끝', a, b, flush=True); os._exit(0)
