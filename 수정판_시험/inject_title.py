#!/usr/bin/env python3
"""타이틀 로고를 바꾼다. 롬은 읽기만 하고 새 파일로 저장. (Claude 작성, 2026-10-14)
사용:   python inject_title.py <입력 롬.nds> <출력 롬.nds> [--logo 그림.png] [--preview 폴더]
위치:   a/0/4/6 멤버 3 (RGCN 8bpp, 32x12 타일 = 256x96, 타일이 가로로 차례차례) + 팔레트 멤버 4 (RLCN 256색)
        (멤버 3 을 망가뜨리면 타이틀에서 로고만 사라짐 — 에뮬레이터로 확인. 뒷배경 번쩍임은 멤버 34)"""
import sys, os, struct, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ); sys.path.insert(0, HERE)
import hg1
from hg1 import NDS, NARC
from PIL import Image
import inject_items

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--logo', default=os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'ui', 'title_logo_ai.png'))
ap.add_argument('--preview', default=None)
A = ap.parse_args()
im = inject_items.cutout(A.logo); im = im.crop(im.getchannel('A').getbbox())
s = min(256 / im.width, 96 / im.height); nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
im = im.resize((nw, nh), Image.LANCZOS)
can = Image.new('RGBA', (256, 96), (0, 0, 0, 0)); can.paste(im, ((256 - nw) // 2, (96 - nh) // 2), im)
a = can.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
rgb = Image.new('RGB', (256, 96), (0, 0, 0)); rgb.paste(can.convert('RGB'), (0, 0), a)
rom = NDS(open(A.rom, 'rb').read()); nar = NARC(rom.get('a/0/4/6')); f = list(nar.files)
def used(m):
    c = m.find(b'RAHC') + 0x20; return set(m[c:])
# 팔레트 멤버 4 는 뒷배경 번쩍임(멤버 34)과 같이 쓴다 → 원래 로고가 쓰던 색 번호 중 배경이 안 쓰는 것만 새 색으로 바꾼다
SLOTS = sorted(used(f[3]) - used(f[34]) - {0})
q = rgb.quantize(colors=len(SLOTS), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
pal = q.getpalette()[:len(SLOTS) * 3]; cols = [tuple(pal[i * 3:i * 3 + 3]) for i in range(len(SLOTS))]
idx = [[SLOTS[q.getpixel((x, y))] if a.getpixel((x, y)) else 0 for x in range(256)] for y in range(96)]
g = bytearray(f[3]); c = g.find(b'RAHC') + 0x20
for t in range(32 * 12):
    ox, oy = (t % 32) * 8, (t // 32) * 8
    for y in range(8):
        for x in range(8): g[c + t * 64 + y * 8 + x] = idx[oy + y][ox + x]
p = bytearray(f[4]); t0 = p.find(b'TTLP') + 0x18
def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)
for sl, col in zip(SLOTS, cols): struct.pack_into('<H', p, t0 + 2 * sl, bgr555(col))
f[3] = bytes(g); f[4] = bytes(p); nar.files = f
print('쓰기:', rom.put('a/0/4/6', nar.build())); open(A.out, 'wb').write(bytes(rom.d)); print('저장:', A.out)
if A.preview:
    os.makedirs(A.preview, exist_ok=True)
    pv = Image.new('RGB', (256, 96), (120, 70, 20)); pp = pv.load()
    for y in range(96):
        for x in range(256):
            if idx[y][x]: pp[x, y] = cols[SLOTS.index(idx[y][x])]
    pv.resize((768, 288), Image.NEAREST).save(os.path.join(A.preview, '미리보기_타이틀.png'))
