#!/usr/bin/env python3
"""전 종 화면 확인 — 6마리씩 파티에 넣어 파티 아이콘·요약 앞모습·따라 걷기 4방향을 찍는다. (Claude 작성, 2026-10-15)
사용:   python 전종_확인.py <롬> <바탕 상태.dst> <배치 번호 0~> <출력 폴더>      (한 배치 = 칸표.tsv 의 6종)
방법:   에뮬레이터 RAM 의 파티(첫 칸 PK4 236바이트)를 복제해 종 번호만 바꿔 쓰고(pk4.py), 파티 화면·요약 화면·걷기를 찍음.
        첫 칸이 바뀌어야 따라다니는 그림이 갱신되므로 6종 각각을 맨 앞에 두고 상태를 다시 불러와 찍는다.
결과:   <폴더>/배치NN.png (종마다 한 줄: 번호·이름 | 파티 아이콘 | 요약 앞모습 | 아래·위·왼쪽·오른쪽 걷기), 개별 PNG 도 저장"""
import sys, os, struct, csv
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageDraw, ImageFont
import pk4
rom, st, bi, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..', '..'))
rows = list(csv.reader(open(os.path.join(PROJ, 'hg2_out', '칸표.tsv'), encoding='utf-8'), delimiter='\t'))[1:]
rows = sorted(((int(r[1]), r[0]) for r in rows if r[1].isdigit()))
batch = rows[bi * 6:bi * 6 + 6]
if not batch: sys.exit('배치 없음')
sheet_path = os.path.join(out, '배치%02d.png' % bi)
if os.path.exists(sheet_path): print('이미 있음', sheet_path); sys.exit(0)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(40)
def hold(k, f):
    m = keymask(k); emu.input.keypad_add_key(m); run(f); emu.input.keypad_rm_key(m); run(10)
emu.savestate.load_file(st); run(10)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); pat = struct.pack('<II', 6, 1); o = ram.find(pat)
while o >= 0:
    d = pk4.decode(ram[o + 8:o + 244]); body = b''.join(d['blocks'][c] for c in d['order'])
    if sum(struct.unpack('<64H', body)) & 0xFFFF == struct.unpack_from('<H', ram, o + 14)[0]: break
    o = ram.find(pat, o + 4)
assert o >= 0, '파티를 못 찾음'
base = 0x02000000 + o; first = ram[o + 8:o + 244]
def put_party(order):
    for i, (slot, nm) in enumerate(order):
        d = pk4.decode(pk4.with_species(first, slot)); d['pid'] = (d['pid'] + 0x10001 * i) & 0xFFFFFFFF
        raw = pk4.encode(d)
        for j, b in enumerate(raw): emu.memory.unsigned[base + 8 + 236 * i + j] = b
    for j, b in enumerate(struct.pack('<I', len(order))): emu.memory.unsigned[base + 4 + j] = b
R = {}
for rot in range(len(batch)):
    order = batch[rot:] + batch[:rot]
    emu.savestate.load_file(st); run(10); put_party(order); run(5)
    slot, nm = batch[rot]
    # 파티 화면(아이콘) + 요약 앞모습
    touch(50, 76); run(60)
    party = emu.screenshot().copy()
    press(Keys.KEY_A, 4, 50); press(Keys.KEY_A, 4, 90); run(150)      # 요약 화면 들어올 때 일부 종(칸 26·266·294)은 노란 실루엣 효과가 1~2초 감 → 150프레임 기다림(10/16)
    summ = emu.screenshot().copy()
    for _ in range(7): press(Keys.KEY_B, 4, 45)      # 요약 → 파티 → 메뉴 → 필드(여러 번 눌러 확실히 닫음)
    run(90)
    walk = {}
    for nmk, k in (('D', Keys.KEY_DOWN), ('U', Keys.KEY_UP), ('L', Keys.KEY_LEFT), ('R', Keys.KEY_RIGHT)):
        hold(k, 36); run(60)                           # 두 칸 걷고 멈춘 뒤 찍기(따라다니는 쪽은 한 칸 늦게 바뀜 — 10/16 확인)
        walk[nmk] = emu.screenshot().copy()
    R[slot] = (nm, party, summ, walk)
    party.save(os.path.join(out, '%03d_%s_파티.png' % (slot, nm))); summ.save(os.path.join(out, '%03d_%s_요약.png' % (slot, nm)))
    for k2, im in walk.items(): im.save(os.path.join(out, '%03d_%s_걷기%s.png' % (slot, nm, k2)))
# 합친 쪽
try: font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)
except Exception: font = ImageFont.load_default()
W = 340 + 4 * 122 + 6; H = 96
sheet = Image.new('RGB', (W * 1, H * len(R)), (250, 250, 250)); dr = ImageDraw.Draw(sheet)
for r, (slot, (nm, party, summ, walk)) in enumerate(R.items()):
    y = r * H; dr.text((4, y + 4), '%d %s' % (slot, nm), fill=(0, 0, 0), font=font)
    icon = party.crop((0, 192 + 8, 128, 192 + 8 + 40)).resize((128, 40))                # 파티 첫 칸
    sheet.paste(icon, (4, y + 30))
    sfront = summ.crop((165, 40, 255, 140)).resize((90, 90)); sheet.paste(sfront, (140, y + 3))
    pnl = summ.crop((0, 192 + 4, 256, 192 + 100)).resize((100, 38)); sheet.paste(pnl, (235, y + 30))
    for i, k in enumerate('DULR'):
        c = walk[k].crop((67, 40, 187, 130)); sheet.paste(c, (340 + i * 122, y + 3))
sheet.save(sheet_path); print('배치', bi, [s for s, _ in batch], '→', sheet_path)
