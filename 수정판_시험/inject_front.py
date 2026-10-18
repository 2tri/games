#!/usr/bin/env python3
"""남자 주인공 정면 그림 두 곳을 태일이로 바꾼 시험 롬을 만든다. 롬은 읽기만 하고 새 파일로 저장한다. (Claude 작성, 2026-10-13)
사용:   python inject_front.py <입력 롬.nds> <출력 롬.nds> [--portrait 그림.png] [--preview 폴더]
바꾸는 곳
  1) 성별 선택·확인 화면의 남자 카드  a/1/2/0 멤버 12~15 (4bpp, 8x16 타일 = 64x128) + 팔레트 멤버 16 (15색 + 투명)
  2) 트레이너 카드(메뉴 「케이」)의 그림 a/0/4/9 멤버 44 (8bpp, 화면에서는 5x9 타일 = 40x72) + 카드 팔레트들의 65~95번 색
     (타일 번호 배치는 에뮬레이터에서 BG3 의 타일 지도를 읽어 확인한 것)
원본 그림: games/digimon/art/src/people/taichi_portrait_ai.png (정면 전신, 색 있음)"""
import sys, os, struct, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--portrait', default=os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'people', 'taichi_portrait_ai.png'))
ap.add_argument('--preview', default=None)
ap.add_argument('--members', default='12,13,14,15', help='성별 카드 그림 멤버(남 12~15, 여 17~20)')
ap.add_argument('--pal', type=int, default=16, help='성별 카드 팔레트 멤버(남 16, 여 21)')
ap.add_argument('--no-card', action='store_true', help='트레이너 카드는 안 바꿈(여자 카드 자리 미확인)')
A = ap.parse_args()

def figure(path):
    """배경(가장자리와 이어진 흰색)을 투명으로 → RGBA, 그림 영역만 잘라냄"""
    im = Image.open(path).convert('RGB'); w, h = im.size; px = im.load()
    mask = Image.new('L', (w, h), 255); mp = mask.load()
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    def white(p): return p[0] >= 235 and p[1] >= 235 and p[2] >= 235
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not white(px[x, y]): continue
        seen.add((x, y)); mp[x, y] = 0
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    rgba = im.convert('RGBA'); rgba.putalpha(mask)
    return rgba.crop(rgba.getbbox())

def to_indexed(fig, w, h, n_colors, first_index, box):
    """fig 를 (w,h) 칸 안에 맞춰(box = 칸 안에서 그림이 들어갈 영역 w0,h0) 줄이고 n_colors 색으로 → (인덱스 행렬, 팔레트 RGB 목록)"""
    bw, bh = box
    s = min(bw / fig.width, bh / fig.height)
    tw, th = max(1, round(fig.width * s)), max(1, round(fig.height * s))
    small = fig.resize((tw, th), Image.BOX)                  # RGBA 는 알파를 곱해서 줄인다
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canvas.paste(small, ((w - tw) // 2, h - th - (h - bh)), small)
    a = canvas.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.new('RGB', (w, h), (0, 0, 0)); rgb.paste(canvas.convert('RGB'), (0, 0), a)
    q = rgb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:n_colors * 3]
    qp = q.load(); ap_ = a.load()
    rows = [[(first_index + qp[x, y]) if ap_[x, y] else 0 for x in range(w)] for y in range(h)]
    cols = [tuple(pal[i * 3:i * 3 + 3]) for i in range(n_colors)]
    return rows, cols

def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)

rom = NDS(open(A.rom, 'rb').read())
fig = figure(A.portrait)
report = []

# ---- 1) 성별 선택 카드: 64x128, 4bpp, 색 15 + 투명
sel = NARC(rom.get('a/1/2/0')); f = list(sel.files)
rows, cols = to_indexed(fig, 64, 128, 15, 1, (60, 124))
tile = bytearray()
for t in range(8 * 16):
    tx, ty = (t % 8) * 8, (t // 8) * 8
    for y in range(8):
        for x in range(0, 8, 2):
            tile.append(rows[ty + y][tx + x] | (rows[ty + y][tx + x + 1] << 4))
assert len(tile) == 4096
for mem in [int(x) for x in A.members.split(',')]:
    m = bytearray(f[mem]); c = m.find(b'RAHC') + 0x20
    m[c:c + 4096] = tile; f[mem] = bytes(m)
pm = bytearray(f[A.pal]); t0 = pm.find(b'TTLP') + 0x18
struct.pack_into('<H', pm, t0, 0)                                    # 0번(투명)
for i, col in enumerate(cols): struct.pack_into('<H', pm, t0 + 2 * (1 + i), bgr555(col))
f[A.pal] = bytes(pm); sel.files = f
report.append('성별 선택 카드: 멤버 12~15 에 64x128 그림, 팔레트 멤버 16 의 1~15번 색 교체 (%s)' % rom.put('a/1/2/0', sel.build()))
prev_sel = Image.new('RGB', (64, 128), (160, 100, 40)); pp = prev_sel.load()
for y in range(128):
    for x in range(64):
        if rows[y][x]: pp[x, y] = cols[rows[y][x] - 1]

if A.no_card:
    open(A.out, 'wb').write(bytes(rom.d)); print(chr(10).join(report)); print('저장:', A.out)
    if A.preview:
        os.makedirs(A.preview, exist_ok=True)
        prev_sel.resize((256, 512), Image.NEAREST).save(os.path.join(A.preview, '미리보기_성별선택_여.png'))
    sys.exit(0)
# ---- 2) 트레이너 카드: 5x9 타일(40x72), 8bpp, 색 번호 65~95
card = NARC(rom.get('a/0/4/9')); g = list(card.files)
TILEMAP = [[17, 18, 19, 20, 21], [49, 50, 51, 52, 53], [81, 82, 83, 84, 85], [113, 114, 115, 116, 117],
           [23, 24, 25, 26, 27], [55, 56, 57, 58, 59], [87, 88, 89, 90, 91], [119, 120, 121, 122, 123], [107, 108, 109, 110, 111]]
rows2, cols2 = to_indexed(fig, 40, 72, 31, 65, (38, 72))
m44 = bytearray(g[44]); d0 = m44.find(b'RAHC') + 0x20
for cy, line in enumerate(TILEMAP):
    for cx, n in enumerate(line):
        for y in range(8):
            for x in range(8):
                m44[d0 + n * 64 + y * 8 + x] = rows2[cy * 8 + y][cx * 8 + x]
g[44] = bytes(m44)
# 카드 팔레트: 원래 에단 색(65~95)과 같은 칸을 가진 팔레트 전부의 65~95번을 새 색으로
ref = None; changed = []
for i, mm in enumerate(g):
    if mm[:4] != b'RLCN': continue
    t = mm.find(b'TTLP') + 0x18
    cur = [struct.unpack_from('<H', mm, t + 2 * k)[0] for k in range(65, 96)]
    if ref is None and i == 24: ref = cur
for i, mm in enumerate(g):
    if mm[:4] != b'RLCN' or ref is None: continue
    b = bytearray(mm); t = b.find(b'TTLP') + 0x18
    cur = [struct.unpack_from('<H', b, t + 2 * k)[0] for k in range(65, 96)]
    if cur != ref: continue
    for k, col in enumerate(cols2): struct.pack_into('<H', b, t + 2 * (65 + k), bgr555(col))
    g[i] = bytes(b); changed.append(i)
card.files = g
report.append('트레이너 카드: 멤버 44 의 40x72 그림 교체, 카드 팔레트 %d개(%s)의 65~95번 색 교체 (%s)' % (len(changed), changed[:6], rom.put('a/0/4/9', card.build())))
prev_card = Image.new('RGB', (40, 72), (200, 90, 80)); pc = prev_card.load()
for y in range(72):
    for x in range(40):
        if rows2[y][x]: pc[x, y] = cols2[rows2[y][x] - 65]

open(A.out, 'wb').write(bytes(rom.d))
print('\n'.join(report)); print('저장:', A.out)
if A.preview:
    os.makedirs(A.preview, exist_ok=True)
    prev_sel.resize((256, 512), Image.NEAREST).save(os.path.join(A.preview, '미리보기_성별선택.png'))
    prev_card.resize((240, 432), Image.NEAREST).save(os.path.join(A.preview, '미리보기_트레이너카드.png'))
