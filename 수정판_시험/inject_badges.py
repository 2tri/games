#!/usr/bin/env python3
"""리그 배지 화면(트레이너 카드 위 화면)의 관장 얼굴 16칸을 문장 8 + 디지멘탈 8 그림으로 바꾼다. 롬은 읽기만 하고 새 파일로 저장. (Claude 작성, 2026-10-14)
사용:   python inject_badges.py <입력 롬.nds> <출력 롬.nds> [--preview 폴더]
위치:   a/0/4/9 멤버 43(RGCN 4bpp 256x256 타일 글자) + 타일 지도 멤버 51(성도 8칸만 보이는 화면)·52(성도+관동 16칸) + 팔레트 멤버 27·28·29
        얼굴 칸 = 지도에서 5x4 타일(40x32px), 칸마다 타일 20개가 따로(반복 아님), 팔레트 줄 3~11 을 나눠 씀(줄 12~15 는 비어 있음)
순서:   성도 8칸(위 두 줄, 왼쪽부터) = 문장 [용기 우정 사랑 지식 순수 성실 희망 빛]  /  관동 8칸(아래 두 줄) = 디지멘탈 [용기 우정 사랑 지식 성실 순수 빛 기적]
        (사용자 지시 「10c ②」의 나열 순서 그대로. 순서가 다르면 아래 JOHTO·KANTO 만 고치면 됨)
팔레트: 성도 8칸은 줄 3·4·5·6·7 을 둘씩 나눠 씀(문장은 색이 적음), 관동 8칸(디지멘탈은 색 많음)은 줄 8~15 를 하나씩"""
import sys, os, struct, argparse, collections
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ); sys.path.insert(0, HERE)
import hg1
from hg1 import NDS, NARC
from PIL import Image
import inject_items

UI = os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'ui')
JOHTO = ['crest_courage', 'crest_friendship', 'crest_love', 'crest_knowledge', 'crest_purity', 'crest_sincerity', 'crest_hope', 'crest_light']
KANTO = ['digimental_courage', 'digimental_friendship', 'digimental_love', 'digimental_knowledge', 'digimental_sincerity', 'digimental_purity', 'digimental_light', 'digimental_miracle']
JOHTO_ROWS = [3, 3, 4, 4, 5, 6, 6, 7]          # 지도 51 이 원래 쓰던 줄 배정과 같은 묶음(둘씩 나눔)
KANTO_ROWS = [8, 9, 10, 11, 12, 13, 14, 15]
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--preview', default=None)
A = ap.parse_args()

def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)
rom = NDS(open(A.rom, 'rb').read()); nar = NARC(rom.get('a/0/4/9')); f = list(nar.files)

def maps(mi):
    s = bytearray(f[mi]); o = s.find(b'NRCS'); w, h = struct.unpack_from('<HH', s, o + 8)
    return s, o + 0x14, w // 8, h // 8
FACE_ROWS = range(3, 12)
s52, e52, W8, H8 = maps(52)
ents52 = list(struct.unpack_from('<%dH' % (W8 * H8), s52, e52))
cnt = collections.Counter(e & 0x3FF for e in ents52)
isface = lambda e: (e >> 12) in FACE_ROWS and cnt[e & 0x3FF] == 1
corners = []
for ty in range(H8):
    for tx in range(W8):
        if not isface(ents52[ty * W8 + tx]): continue
        if tx > 0 and isface(ents52[ty * W8 + tx - 1]): continue
        if ty > 0 and isface(ents52[(ty - 1) * W8 + tx]): continue
        corners.append((tx, ty))
assert len(corners) == 16, ('얼굴 칸을 16개 못 찾음', corners)
corners.sort(key=lambda p: (p[1], p[0]))          # 위→아래, 왼→오 : 앞 8 = 성도, 뒤 8 = 관동
blocks = []
for (tx, ty) in corners:
    idx = [[ents52[(ty + r) * W8 + tx + c] & 0x3FF for c in range(5)] for r in range(4)]
    assert all(isface(ents52[(ty + r) * W8 + tx + c]) for r in range(4) for c in range(5)), ('5x4 가 아님', tx, ty)
    blocks.append((tx, ty, idx))

# 새 그림 만들기 -------------------------------------------------------------
def crop_symbol(path, inner):
    im = inject_items.cutout(path); bb = im.getchannel('A').getbbox(); im = im.crop(bb)
    if inner:                                    # 문장: 금테를 빼고 「어두운 회색 판」만 잘라 판 가운데에 상징이 오게 함
        w, h = im.size; im = im.crop((int(w * .10), int(h * .10), int(w * .90), int(h * .90))).convert('RGBA')
        px = im.load(); W_, H_ = im.size
        isplate = lambda p: p[3] and max(p[:3]) - min(p[:3]) <= 22 and 20 <= max(p[:3]) <= 120
        rows = [sum(1 for x in range(W_) if isplate(px[x, y])) for y in range(H_)]
        cols = [sum(1 for y in range(H_) if isplate(px[x, y])) for x in range(W_)]
        ys = [y for y in range(H_) if rows[y] >= W_ * 0.35]; xs = [x for x in range(W_) if cols[x] >= H_ * 0.35]
        if xs and ys:
            im = im.crop((min(xs) + 3, min(ys) + 3, max(xs) - 2, max(ys) - 2))
    return im
GAIN = {'crest_friendship': 1.22, 'crest_knowledge': 1.22}      # 10/16 사용자: 우정·지식 문장이 어두워 조금 밝게(어두운 그림 자동 밝힘 뒤에 한 번 더 곱함)
def make_face(im, ncol, first_idx, bg_idx=2, frame_idx=1, gain=1.0):
    """40x32 안에 흰 테두리 + 어두운 바탕 + 그림. 반환: (색 번호 40x32, 색 목록 ncol)"""
    inner = Image.new('RGBA', (36, 28), (0, 0, 0, 0))
    s = min(34 / im.width, 26 / im.height); nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    sm = im.resize((nw, nh), Image.BOX); inner.paste(sm, ((36 - nw) // 2, (28 - nh) // 2), sm)
    a = inner.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.new('RGB', (36, 28), (24, 28, 36)); rgb.paste(inner.convert('RGB'), (0, 0), a)
    pk = max((max(p) for p in inner.convert('RGB').getdata() if p != (0, 0, 0)), default=255)
    if pk < 225:                                  # 어두운 그림(순수의 회색 십자 등)은 어두운 바탕에 묻히므로 밝게
        k = min(2.6, 235 / max(pk, 1)); px = rgb.load()
        for y in range(28):
            for x in range(36):
                if a.getpixel((x, y)): r, g, b = px[x, y]; px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)))
    if gain != 1.0:
        px = rgb.load()
        for y in range(28):
            for x in range(36):
                if a.getpixel((x, y)): r, g, b_ = px[x, y]; px[x, y] = (min(255, int(r * gain)), min(255, int(g * gain)), min(255, int(b_ * gain)))
    q = rgb.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:ncol * 3]; cols = [tuple(pal[i * 3:i * 3 + 3]) for i in range(ncol)]
    grid = [[bg_idx] * 40 for _ in range(32)]
    for y in range(32):
        for x in range(40):
            edge = x in (0, 39) or y in (0, 31)
            corner = (x in (0, 39)) and (y in (0, 31))
            if edge and not corner: grid[y][x] = frame_idx
    for y in range(28):
        for x in range(36): grid[2 + y][2 + x] = first_idx + q.getpixel((x, y))
    return grid, cols

faces = []          # (grid 40x32 번호, 줄 번호, 색 {번호: RGB})
johto_pairs = {}    # 줄 → [얼굴 번호들]
for k, r in enumerate(JOHTO_ROWS): johto_pairs.setdefault(r, []).append(k)
row_colors = {}     # 줄 → {색 번호: RGB}
grids = {}
for r, ks in johto_pairs.items():
    n = len(ks); per = 13 // n                    # 둘이 나눠 쓰면 6·6 (3~8, 9~14), 혼자면 13
    first = 3
    for j, k in enumerate(ks):
        cols_n = per if n > 1 else 13
        grid, cols = make_face(crop_symbol(os.path.join(UI, JOHTO[k] + '_ai.png'), True), cols_n, first, gain=GAIN.get(JOHTO[k], 1.0))
        grids[k] = (grid, r); row_colors.setdefault(r, {})
        for i, c in enumerate(cols): row_colors[r][first + i] = c
        first += cols_n
for j, k in enumerate(range(8, 16)):
    r = KANTO_ROWS[j]
    grid, cols = make_face(crop_symbol(os.path.join(UI, KANTO[j] + '_ai.png'), False), 13, 3)
    grids[k] = (grid, r); row_colors[r] = {3 + i: c for i, c in enumerate(cols)}
for r in row_colors:
    row_colors[r][1] = (255, 255, 255); row_colors[r][2] = (24, 28, 36)

# 쓰기 -----------------------------------------------------------------------
m = bytearray(f[43]); c0 = m.find(b'RAHC') + 0x20
for k, (tx, ty, idx) in enumerate(blocks):
    grid, row = grids[k]
    for r in range(4):
        for c in range(5):
            t = idx[r][c]
            for y in range(8):
                for x in range(0, 8, 2):
                    m[c0 + t * 32 + y * 4 + x // 2] = grid[r * 8 + y][c * 8 + x] | (grid[r * 8 + y][c * 8 + x + 1] << 4)
f[43] = bytes(m)
face_pos = {}
for k, (tx, ty, idx) in enumerate(blocks):
    for r in range(4):
        for c in range(5): face_pos[(tx + c, ty + r)] = grids[k][1]
for mi in (51, 52):
    s, eo, w8, h8 = maps(mi)
    for ty in range(h8):
        for tx in range(w8):
            if (tx, ty) in face_pos or mi == 51:
                o = eo + 2 * (ty * w8 + tx); e = struct.unpack_from('<H', s, o)[0]
                if (tx, ty) in face_pos: struct.pack_into('<H', s, o, (e & 0x0FFF) | (face_pos[(tx, ty)] << 12))
    if mi == 51:     # 지도 51(성도만): 같은 타일 번호를 쓰는 칸의 줄을 지도 52 의 같은 타일의 줄로
        tile_row = {}
        for k, (tx, ty, idx) in enumerate(blocks):
            for r in range(4):
                for c in range(5): tile_row[idx[r][c]] = grids[k][1]
        for ty in range(h8):
            for tx in range(w8):
                o = eo + 2 * (ty * w8 + tx); e = struct.unpack_from('<H', s, o)[0]
                if (e & 0x3FF) in tile_row and (e >> 12) in FACE_ROWS:
                    struct.pack_into('<H', s, o, (e & 0x0FFF) | (tile_row[e & 0x3FF] << 12))
    f[mi] = bytes(s)
for pi in (27, 28, 29):
    p = bytearray(f[pi]); t0 = p.find(b'TTLP') + 0x18
    for r, cd in row_colors.items():
        struct.pack_into('<H', p, t0 + 2 * (r * 16), 0)
        for i in range(1, 16): struct.pack_into('<H', p, t0 + 2 * (r * 16 + i), bgr555(cd.get(i, (24, 28, 36))))
    f[pi] = bytes(p)
nar.files = f
print('쓰기:', rom.put('a/0/4/9', nar.build())); open(A.out, 'wb').write(bytes(rom.d)); print('저장:', A.out, '얼굴 칸', len(blocks))
if A.preview:
    os.makedirs(A.preview, exist_ok=True)
    pv = Image.new('RGB', (4 * 44, 4 * 36), (60, 90, 90)); pp = pv.load()
    for k in range(16):
        grid, row = grids[k]; ox, oy = (k % 4) * 44 + 2, (k // 4) * 36 + 2
        for y in range(32):
            for x in range(40): pp[ox + x, oy + y] = row_colors[row].get(grid[y][x], (0, 0, 0))
    pv.resize((pv.width * 3, pv.height * 3), Image.NEAREST).save(os.path.join(A.preview, '미리보기_배지.png'))
