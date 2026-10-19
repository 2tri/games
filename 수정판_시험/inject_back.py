#!/usr/bin/env python3
"""남자 주인공 전투 뒷모습을 태일이로 바꾼 롬을 만든다. 롬은 읽기만 하고 새 파일로 저장한다. (Claude 작성, 2026-10-13)
사용:   python inject_back.py <입력 롬.nds> <출력 롬.nds> [--back 그림.png] [--preview 폴더]
위치:   a/0/0/6 — 5개씩 한 묶음 [움직임용 큰 그림(RGCN), 팔레트(RLCN), 셀(RECN), 애니(RNAN), 정지 그림(RGCN 160x80)]
        묶음 15(멤버 75~79)가 전투에서 쓰이는 에단 뒷모습(화면으로 확인), 묶음 0(멤버 0~4)도 에단이라 같이 바꿈.
        큰 그림 = 80x80 프레임 8장(타일 100개씩, 던지는 동작). 프레임 하나는 OAM 조각 6개:
        64x64@타일0 · 16x32@64 · 16x32@72 · 32x16@80 · 32x16@88 · 16x16@96 (캔버스 80x80)
        프레임 8장 모두 같은 그림(움직임 없이)으로 채운다. 정지 그림(160x80)은 좌우 같은 그림, 원래 암호 방식 그대로 다시 암호화.
원본 그림: games/digimon/art/src/people/taichi_back_ds_ai.png"""
import sys, os, struct, random, argparse, inspect
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC
from PIL import Image

# 원본 hg1.ncgr_rows 는 이 롬에서 크기 칸이 0 이라 못 읽는다(수정 제안 diff 와 같은 한 줄) — 메모리에서만 바꿔 쓴다
_src = inspect.getsource(hg1.ncgr_rows)
exec(_src.replace("px = data[c + 0x20:c + size]", "px = data[c + 0x20:c + 0x20 + 6400]"), hg1.__dict__)

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--back', default=os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'people', 'taichi_back_ds_ai.png'))
ap.add_argument('--preview', default=None)
ap.add_argument('--groups', default='15,0', help='바꿀 묶음(남 15,0 · 여 16,1)')
ap.add_argument('--box', default='72,74', help='그림이 들어갈 칸 너비,높이(80x80 안, 아래·가운데 맞춤)')
A = ap.parse_args()
BOXW, BOXH = (int(v) for v in A.box.split(','))

def remove_checker(im):
    """제미나이 그림에 박힌 체크무늬(가짜 투명)를 지운 마스크(0 = 지움)를 돌려줌. 체크무늬가 아니면 None.
    방법: 위쪽 줄의 두 색(흰색·회색 ≈180)을 찾고, 그 색에 가까운 칸이 이어진 덩어리 중 「회색이 30% 이상 섞인 큰 덩어리」만 배경으로(흰 장갑처럼 흰색뿐인 덩어리는 남김).
    칸 크기가 정수가 아니라(≈20.5칸) 격자 무늬 맞춤 대신 색 구성으로 가름. 경계에 남는 번짐 한두 칸은 지운 칸에 붙은 밝은 칸을 두 번 더 지움."""
    w, h = im.size; px = im.load()
    import collections
    top = collections.Counter(px[x, y] for y in range(0, min(h, 90)) for x in range(0, w, 2))
    cols = [c for c, n in top.most_common(8) if min(c) >= 170 and max(c) - min(c) <= 30]
    if len(cols) < 2: return None
    t1 = max(cols, key=lambda c: sum(c)); t2l = [c for c in cols if sum(t1) - sum(c) >= 15]
    if not t2l: return None
    t2 = t2l[0]
    # 회색은 위(≈182)에서 아래(≈167)로 조금씩 달라지므로 고정 색 대신 범위로: 흰색 = 모든 값 ≥ 240, 회색 = 150~200 이고 R·G·B 차이 ≤ 8
    near1 = lambda p: min(p) >= 240
    near2 = lambda p: 150 <= min(p) and max(p) <= 200 and max(p) - min(p) <= 8
    # 위쪽 줄이 정말 체크무늬인지: 두 색이 둘 다 25% 이상
    n1 = sum(1 for y in range(0, 60) for x in range(0, w, 3) if near1(px[x, y])); n2 = sum(1 for y in range(0, 60) for x in range(0, w, 3) if near2(px[x, y]))
    tot = 60 * len(range(0, w, 3))
    if n1 < tot * 0.25 or n2 < tot * 0.25: return None
    # 후보 = 흰색·회색 + 둘 사이 번짐(150 이상, 색 차이 ≤ 8). 번짐까지 넣어야 칸들이 한 덩어리로 이어짐
    cand = [[False] * w for _ in range(h)]; grey = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            pp = px[x, y]
            if min(pp) >= 150 and max(pp) - min(pp) <= 8:
                cand[y][x] = True; grey[y][x] = near2(pp)
    seen = [[False] * w for _ in range(h)]; mask = Image.new('L', (w, h), 255); mp = mask.load()
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0][x0] or not cand[y0][x0]: continue
            comp = []; st = [(x0, y0)]; seen[y0][x0] = True; border = False
            while st:
                x, y = st.pop(); comp.append((x, y))
                if x == 0 or y == 0 or x == w - 1 or y == h - 1: border = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and cand[ny][nx] and not seen[ny][nx]: seen[ny][nx] = True; st.append((nx, ny))
            g = sum(1 for x, y in comp if grey[y][x]) / len(comp)
            # 가장자리에 닿은 덩어리 = 배경. 안에 갇힌 덩어리는 3000칸 미만이고 회색이 30% 이상 섞인 것만(팔·몸 사이 틈) — 큰 것(흰 장갑)·회색 없는 것(눈 하이라이트)은 남김
            if (border and len(comp) >= 100) or (len(comp) < 3000 and len(comp) >= 40 and g >= 0.30):
                for x, y in comp: mp[x, y] = 0
    for _ in range(2):
        add = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if mp[x, y] == 0: continue
                pp = px[x, y]
                if min(pp) >= 150 and max(pp) - min(pp) <= 30 and any(mp[x + dx, y + dy] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): add.append((x, y))
        for x, y in add: mp[x, y] = 0
    return mask

def figure(path):
    im = Image.open(path).convert('RGB'); w, h = im.size; px = im.load()
    mask = remove_checker(im)
    if mask is not None:
        rgba = im.convert('RGBA'); rgba.putalpha(mask)
        return rgba.crop(rgba.getbbox())
    mask = Image.new('L', (w, h), 255); mp = mask.load()
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h): continue
        p = px[x, y]
        if not (p[0] >= 235 and p[1] >= 235 and p[2] >= 235): continue
        seen.add((x, y)); mp[x, y] = 0
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    rgba = im.convert('RGBA'); rgba.putalpha(mask)
    return rgba.crop(rgba.getbbox())

def to_indexed(fig, w, h, n_colors, box):
    bw, bh = box
    s = min(bw / fig.width, bh / fig.height)
    tw, th = max(1, round(fig.width * s)), max(1, round(fig.height * s))
    small = fig.resize((tw, th), Image.BOX)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canvas.paste(small, ((w - tw) // 2, h - th), small)                   # 아래·가운데 맞춤
    a = canvas.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.new('RGB', (w, h), (0, 0, 0)); rgb.paste(canvas.convert('RGB'), (0, 0), a)
    q = rgb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:n_colors * 3]
    qp = q.load(); ap_ = a.load()
    rows = [[(1 + qp[x, y]) if ap_[x, y] else 0 for x in range(w)] for y in range(h)]
    return rows, [tuple(pal[i * 3:i * 3 + 3]) for i in range(n_colors)]

def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)
PIECES = [(0, 0, 8, 8, 0), (64, 0, 2, 4, 64), (64, 32, 2, 4, 72), (0, 64, 4, 2, 80), (32, 64, 4, 2, 88), (64, 64, 2, 2, 96)]

def frame_bytes(rows):
    """80x80 인덱스 → 타일 100개(32바이트씩, 낮은 4비트가 왼쪽)"""
    out = bytearray(100 * 32)
    for (cx, cy, tw, th, t0) in PIECES:
        for ty in range(th):
            for tx in range(tw):
                t = t0 + ty * tw + tx
                for yy in range(8):
                    for xx in range(4):
                        a = rows[cy + ty * 8 + yy][cx + tx * 8 + xx * 2]
                        b = rows[cy + ty * 8 + yy][cx + tx * 8 + xx * 2 + 1]
                        out[t * 32 + yy * 4 + xx] = a | (b << 4)
    return bytes(out)

def lcg(s): return (s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
def encrypt_rev(words, seed):                 # 끝에서부터(hg1 의 'pt'): 마지막 평문 단어 0
    assert words[-1] == 0
    out = [0] * len(words); s = seed
    for i in range(len(words) - 1, -1, -1):
        out[i] = words[i] ^ (s & 0xFFFF); s = lcg(s)
    return out
def encrypt_fwd(words, seed):                 # 앞에서부터(hg1 의 'dp'): 첫 평문 단어 0
    assert words[0] == 0
    out = []; s = seed
    for w in words:
        out.append(w ^ (s & 0xFFFF)); s = lcg(s)
    return out

rom = NDS(open(A.rom, 'rb').read())
nar = NARC(rom.get('a/0/0/6')); f = list(nar.files)
fig = figure(A.back)
rows, cols = to_indexed(fig, 80, 80, 15, (BOXW, BOXH))
frame = frame_bytes(rows)
report = []
for g in [int(x) for x in A.groups.split(',')]:
    big, plt, st = g * 5, g * 5 + 1, g * 5 + 4
    # 큰 그림: 8프레임
    m = bytearray(f[big]); c = m.find(b'RAHC') + 0x20
    n_frames = (len(m) - c) // 3200
    for b in range(n_frames): m[c + b * 3200:c + (b + 1) * 3200] = frame
    f[big] = bytes(m)
    # 팔레트: 1~15번 + 0번(투명)
    p = bytearray(f[plt]); t0 = p.find(b'TTLP') + 0x18
    struct.pack_into('<H', p, t0, 0)
    for i, col in enumerate(cols): struct.pack_into('<H', p, t0 + 2 * (1 + i), bgr555(col))
    f[plt] = bytes(p)
    # 정지 그림 160x80
    old = f[st]; _, mode = hg1.ncgr_rows(old)
    px = []
    for y in range(80): px += rows[y] + rows[y]
    px[-4:] = [0, 0, 0, 0] if mode == 'pt' else px[-4:]
    if mode == 'dp': px[:4] = [0, 0, 0, 0]
    bts = bytes(px[i] | (px[i + 1] << 4) for i in range(0, len(px), 2))
    words = list(struct.unpack('<3200H', bts))
    if mode == 'pt': enc = encrypt_rev(words, random.randint(1, 0xFFFF))
    elif mode == 'dp': enc = encrypt_fwd(words, random.randint(1, 0xFFFF))
    else: enc = words
    s = bytearray(old); sc = s.find(b'RAHC') + 0x20
    s[sc:sc + 6400] = struct.pack('<3200H', *enc); f[st] = bytes(s)
    report.append('묶음 %d: 큰 그림 프레임 %d장, 팔레트 멤버 %d, 정지 그림 멤버 %d(방식 %s)' % (g, n_frames, plt, st, mode))
nar.files = f
report.append('쓰기: %s' % rom.put('a/0/0/6', nar.build()))
open(A.out, 'wb').write(bytes(rom.d))
print('\n'.join(report)); print('저장:', A.out)
if A.preview:
    os.makedirs(A.preview, exist_ok=True)
    im = Image.new('RGB', (80, 80), (90, 120, 160)); pp = im.load()
    for y in range(80):
        for x in range(80):
            if rows[y][x]: pp[x, y] = cols[rows[y][x] - 1]
    im.resize((320, 320), Image.NEAREST).save(os.path.join(A.preview, '미리보기_전투뒷모습.png'))
