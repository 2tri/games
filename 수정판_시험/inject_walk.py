#!/usr/bin/env python3
"""남자 주인공 필드 걷기 그림을 태일이로 바꾼 롬을 만든다. 롬은 읽기만 하고 새 파일로 저장한다. (Claude 작성, 2026-10-13)
사용:   python inject_walk.py <입력 롬.nds> <출력 롬.nds> [--sheet 걷기시트.png] [--preview 폴더]
위치:   a/0/8/1 의 69번 파일('hero', BTX0, 32x32 텍스처 32장 + 16색 팔레트 1개)
        텍스처 이름 hero.N: 걷기 — 위(뒤) 1~4, 아래(앞) 5~8, 왼쪽 9~12, 오른쪽 13~16
                           뛰기 — 위 17~20, 아래 21~24, 왼쪽 25~28, 오른쪽 29~32   (눈으로 확인)
        방향마다 4장 = [서기, 걸음1, 서기, 걸음2] 로 채운다. 뛰기도 같은 그림.
        자전거(71)·낚시(79)·파도타기(77) 등 다른 모습은 아직 에단 그대로.
원본: games/digimon/art/src/people/taichi_ai.png (3행: 앞 / 뒤 / 왼쪽, 한 줄 3컷)"""
import sys, os, struct, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC
from PIL import Image, ImageOps

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--sheet', default=os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'people', 'taichi_walk_ds_ai.png'))
ap.add_argument('--layout', default='ds', help="ds = 4줄(아래·위·왼쪽·오른쪽)×3칸(걷기 시트 10/14), old = 3줄×4칸(옛 시트), tile = sheet_cut.py 결과(96x128)")
ap.add_argument('--target', type=int, default=69, help='a/0/8/1 의 멤버 번호(남 69)')
ap.add_argument('--preview', default=None)
ap.add_argument('--height', type=int, default=25, help='그림 높이(픽셀). 원래 에단은 23')
A = ap.parse_args()

TILE = (A.layout == 'tile')      # 10/15: sheet_cut.py 가 만든 96x128(32x32 칸, 줄 = 아래·위·왼·오른쪽, 칸 = 서기·걸음1·걸음2) — 다시 자르거나 줄이지 않고 그대로 씀
CW, CH, BOTTOM = 32, 32, 30
if TILE:
    _sh = Image.open(A.sheet).convert('RGBA'); assert _sh.size == (96, 128), '타일 시트는 96x128 이어야 함: %s' % (_sh.size,)
    placed = {d: [_sh.crop((i * 32, r * 32, i * 32 + 32, r * 32 + 32)) for i in range(3)] for r, d in enumerate(('down', 'up', 'left', 'right'))}
else:
    # ---------- 원본 시트에서 컷 뽑기
    sheet = Image.open(A.sheet).convert('RGB')
    W, H = sheet.size
    def cut(row, col):
        """3행 4열 격자의 칸 하나를 잘라 배경을 투명으로(가장자리와 이어진 밝은 색) → RGBA, 그림 영역"""
        cw, ch = (W // 3, H // 4) if A.layout == 'ds' else (W // 4, H // 3)
        c = sheet.crop((col * cw + 8, row * ch + 8, (col + 1) * cw - 8, (row + 1) * ch - 8))
        w, h = c.size; px = c.load()
        def dark(p): return max(p) < 175 and max(p) - min(p) <= 30
        D = [[dark(px[x, y]) for x in range(w)] for y in range(h)]
        hrun = [[0] * w for _ in range(h)]; vrun = [[0] * w for _ in range(h)]
        for y in range(h):
            x = 0
            while x < w:
                if D[y][x]:
                    x2 = x
                    while x2 < w and D[y][x2]: x2 += 1
                    for k in range(x, x2): hrun[y][k] = x2 - x
                    x = x2
                else: x += 1
        for x in range(w):
            y = 0
            while y < h:
                if D[y][x]:
                    y2 = y
                    while y2 < h and D[y2][x]: y2 += 1
                    for k in range(y, y2): vrun[k][x] = y2 - y
                    y = y2
                else: y += 1
        for y in range(h):
            for x in range(w):
                if D[y][x] and ((hrun[y][x] <= 3 and vrun[y][x] >= 30) or (vrun[y][x] <= 3 and hrun[y][x] >= 30)):
                    px[x, y] = (255, 255, 255)
        mask = Image.new('L', (w, h), 255); mp = mask.load()
        stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
        seen = set()
        def bg(p): return min(p) >= 150 and max(p) - min(p) <= 40
        while stack:
            x, y = stack.pop()
            if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not bg(px[x, y]): continue
            seen.add((x, y)); mp[x, y] = 0
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        rgba = c.convert('RGBA'); rgba.putalpha(mask)
        bb = rgba.getbbox()
        return rgba.crop(bb) if bb else None
    # (행, 열) : 앞 = 0행, 뒤 = 1행, 왼쪽 = 2행 (각 0~2열). 3행 3열은 뒷모습 한 컷(안 씀)
    if A.layout == 'ds':
        # 줄 = 아래(정면)·위(뒷모습)·왼쪽·오른쪽, 칸 3개. 옆 컷은 얼굴도 걷는 쪽을 봄(오른쪽은 시트의 오른쪽 줄을 그대로 씀)
        frames = {'down': [cut(0, i) for i in range(3)], 'up': [cut(1, i) for i in range(3)],
                  'left': [cut(2, i) for i in range(3)], 'right': [cut(3, i) for i in range(3)]}
    else:
        frames = {'down': [cut(0, i) for i in range(3)], 'up': [cut(1, i) for i in range(3)], 'left': [cut(2, i) for i in range(3)]}
        frames['right'] = [ImageOps.mirror(f) for f in frames['left']]
    allf = [f for v in frames.values() for f in v]
    assert all(f is not None for f in allf), '칸을 못 찾음'
    tallest = max(f.height for f in allf)
    s = A.height / tallest                                      # 모든 컷에 같은 배율(키 차이 유지)
    def small(f):
        w, h = max(1, round(f.width * s)), max(1, round(f.height * s))
        return f.resize((w, h), Image.BOX)
    CW, CH, BOTTOM = 32, 32, 30                                # 텍스처 32x32, 발 밑 = 30번째 줄(원래 에단과 같음)
    def place(f):
        im = Image.new('RGBA', (CW, CH), (0, 0, 0, 0)); sm = small(f)
        im.paste(sm, (15 - sm.width // 2, BOTTOM + 1 - sm.height), sm)
        return im
    placed = {d: [place(f) for f in fs] for d, fs in frames.items()}
# 팔레트: 컷들의 색을 빈도의 제곱근으로 가중해 15색으로 줄인다(작은 영역인 피부·별 무늬도 살리기 위해)
import math, collections
hist = collections.Counter()
for d in ('up', 'down', 'left', 'right'):
    for fr_ in placed[d]:
        px_ = fr_.load()
        for y in range(CH):
            for x in range(CW):
                if px_[x, y][3] >= 128: hist[px_[x, y][:3]] += 1
strip = []
for col, n in hist.items(): strip += [col] * (1 + int(math.sqrt(n)))
sw = 64; sh = (len(strip) + sw - 1) // sw
simg = Image.new('RGB', (sw, sh), (0, 0, 0)); simg.putdata(strip + [strip[0]] * (sw * sh - len(strip)))
pq = simg.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
pp_ = pq.getpalette()[:45]; cols = [tuple(pp_[i * 3:i * 3 + 3]) for i in range(15)]
def nearest(c):
    best = 0; bd = 1 << 30
    for i, p in enumerate(cols):
        d = (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2
        if d < bd: bd, best = d, i
    return 1 + best
keys = [(d, i) for d in ('up', 'down', 'left', 'right') for i in range(3)]
IDX = {}
for d, i in keys:
    fr_ = placed[d][i]; px_ = fr_.load(); rows = []
    for y in range(CH):
        rows.append([nearest(px_[x, y][:3]) if px_[x, y][3] >= 128 else 0 for x in range(CW)])
    IDX[(d, i)] = rows

# ---------- 롬에 쓰기: 69번 파일
def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)
rom = NDS(open(A.rom, 'rb').read())
nar = NARC(rom.get('a/0/8/1')); files = list(nar.files)
buf = bytearray(files[A.target])
# BTX0 해석(바이트 위치만 필요) — 텍스처 이름 → 데이터 위치, 팔레트 위치
t = struct.unpack_from('<I', buf, 0x10)[0]
assert buf[t:t + 4] == b'TEX0'
def dict3d(o):
    n = buf[o + 1]; p = o + 8 + (n + 1) * 4
    esz, blk = struct.unpack_from('<HH', buf, p); p += 4
    ents = [bytes(buf[p + i * esz:p + (i + 1) * esz]) for i in range(n)]
    p += n * esz
    names = [bytes(buf[p + i * 16:p + (i + 1) * 16]).rstrip(b'\0').decode('latin1') for i in range(n)]
    return ents, names
texdata = struct.unpack_from('<I', buf, t + 0x14)[0]; paldata = struct.unpack_from('<I', buf, t + 0x38)[0]
tex_ents, tex_names = dict3d(t + struct.unpack_from('<H', buf, t + 0x0E)[0])
pal_ents, pal_names = dict3d(t + struct.unpack_from('<I', buf, t + 0x34)[0])
assert pal_names[0] in ('hero', 'heroine') and len(tex_names) == 32, (pal_names, len(tex_names))
tex_off = {int(nm.split('.')[-1]): t + texdata + (struct.unpack_from('<H', e, 0)[0] << 3) for e, nm in zip(tex_ents, tex_names)}
pal_off = t + paldata + (struct.unpack_from('<H', pal_ents[0], 0)[0] << 3)
struct.pack_into('<H', buf, pal_off, 0)
for i, col in enumerate(cols): struct.pack_into('<H', buf, pal_off + 2 * (1 + i), bgr555(col))
ORDER = [0, 1, 0, 2]                                      # [서기, 걸음1, 서기, 걸음2] — 시트의 가운데 컷(1)을 서기로 쓴다
ORDER = [1, 0, 1, 2]
if TILE: ORDER = [0, 1, 0, 2]                               # 타일 시트는 칸 0 = 서기
BASE = {'up': 1, 'down': 5, 'left': 9, 'right': 13}
for d, b0 in BASE.items():
    for run in (0, 16):
        for k in range(4):
            rows = IDX[(d, ORDER[k])]
            o = tex_off[b0 + run + k]
            for y in range(CH):
                for x in range(0, CW, 2):
                    buf[o + y * 16 + x // 2] = rows[y][x] | (rows[y][x + 1] << 4)
files[A.target] = bytes(buf); nar.files = files
print('쓰기:', rom.put('a/0/8/1', nar.build()))
open(A.out, 'wb').write(bytes(rom.d)); print('저장:', A.out)
if A.preview:
    os.makedirs(A.preview, exist_ok=True)
    out = Image.new('RGB', (4 * 36, 4 * 36), (200, 200, 200)); pp = out.load()
    for r, d in enumerate(('up', 'down', 'left', 'right')):
        for k in range(4):
            rows = IDX[(d, ORDER[k])]
            for y in range(CH):
                for x in range(CW):
                    if rows[y][x]: pp[k * 36 + 2 + x, r * 36 + 2 + y] = cols[rows[y][x] - 1]
    out.resize((out.width * 4, out.height * 4), Image.NEAREST).save(os.path.join(A.preview, '미리보기_걷기.png'))
