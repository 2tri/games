"""제목 화면 (사용자 지시 2026-10-02): 로고를 한글 「디지몬스터」로, 칠색조 자리를 디지몬 그림으로
  로고: art/title/logo.png (title_logo.py 가 만듦, 화면 160×48, 색 하늘·주황·검정) → 배경 타일(TitleScreenGFX1) 중 로고 칸만 다시 씀
  칠색조: 날갯짓 5장(OAM 묶음 56~5A, 제목 화면만 씀)을 한 장짜리 그림으로 — 8×16 스프라이트 조각 격자, 타일은 TitleScreenGFX3 자리
  롬 자리는 패턴으로 찾음 (제목 화면 코드: ld hl,GFX1 / ld de,vTiles2 / ld a,BANK / call … 바로 뒤에 GFX3)"""
import os, re, struct
import numpy as np
from PIL import Image
import dmrom, gblz

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
# 제목 화면 배경 지도 0~5줄 (1.4 롬을 에뮬레이터에서 읽은 값, 0x08 = 빈 타일). 로고 타일은 이 칸들에만 있음
LOGO_ROWS = [[0x08] + list(range(0x00, 0x10)) + [0x08] * 3,
             [0x08] + list(range(0x10, 0x20)) + [0x08] * 3,
             [0x08] + list(range(0x20, 0x30)) + [0x50, 0x51, 0x08],
             [0x08] + list(range(0x30, 0x40)) + [0x60, 0x61, 0x08],
             [0x08] + list(range(0x40, 0x50)) + [0x70, 0x71, 0x08],
             [0x08, 0x62, 0x63] + list(range(0x72, 0x7f)) + [0x08] * 4]
LOGO_VAL = {(120, 160, 248): 2, (248, 152, 80): 1, (0, 0, 0): 3, (255, 255, 255): 0}   # 화면 색 → 타일 값 (롬에서 확인)


def find(d):
    m = re.search(rb'\x21(..)\x11\x00\x90\x3e(.)\xcd..\x21(..)\x11\x00\x80\x3e(.)\xcd', d, re.S)
    g1 = (m.start() + 1, m.start() + 7); g3 = (m.start() + 12, m.start() + 18)        # (포인터 자리, 뱅크 자리): 21 lo hi 11 00 90 3e [뱅크] cd lo hi 21 lo hi 11 00 80 3e [뱅크]
    a = lambda pp, bp: dmrom.addr(d[bp], d[pp] | d[pp + 1] << 8)
    return g1, a(*g1), g3, a(*g3)


def tile_bytes(a):
    """8×8 값(0~3) → 2bpp 16바이트"""
    out = bytearray()
    for r in range(8):
        out += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(a[r])), sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(a[r]))])
    return bytes(out)


def logo_tiles(gfx, png):
    """gfx = 풀린 TitleScreenGFX1 (bytearray). 로고 칸을 png 로 다시 씀"""
    im = np.asarray(Image.open(png).convert('RGB')).astype(int)
    val = np.zeros(im.shape[:2], np.uint8)
    for c, v in LOGO_VAL.items(): val[(im == c).all(-1)] = v
    for r, row in enumerate(LOGO_ROWS):
        for c, t in enumerate(row):
            blk = val[r * 8:r * 8 + 8, c * 8:c * 8 + 8]
            if t == 0x08:
                assert (blk == 2).all(), '빈 타일 칸 (%d,%d) 에 그림이 있음' % (r, c)
                continue
            gfx[t * 16:t * 16 + 16] = tile_bytes(blk)
    return gfx


def sprite_layout(png, pal_cols):
    """그림 → (8×16 조각 목록 [(x, y, 타일)], 타일 바이트, 색 3개). 가운데 기준 좌표 (칠색조와 같은 기준점)"""
    im = np.asarray(Image.open(png).convert('RGBA')).astype(int); h, w = im.shape[:2]
    W, H = (w + 7) // 8 * 8, (h + 15) // 16 * 16
    val = np.zeros((H, W), np.uint8); ox = (W - w) // 2; oy = H - h
    for y in range(h):
        for x in range(w):
            if im[y, x, 3] < 128: continue
            c = tuple(im[y, x, :3]); val[oy + y, ox + x] = 1 + int(np.argmin([sum((np.array(c) - np.array(p)) ** 2) for p in pal_cols]))
    pieces, tiles = [], bytearray()
    for cy in range(H // 16):
        for cx in range(W // 8):
            blk = val[cy * 16:cy * 16 + 16, cx * 8:cx * 8 + 8]
            if not blk.any(): continue
            t = len(tiles) // 16
            tiles += tile_bytes(blk[:8]) + tile_bytes(blk[8:])
            pieces.append((cx * 8 - W // 2, cy * 16 - H // 2, t))
    return pieces, bytes(tiles)


def rgb555(c): return (c[0] * 31 // 255) | (c[1] * 31 // 255) << 5 | (c[2] * 31 // 255) << 10


def apply(P, logo_png, mon_png, mon_cols, digital=False):
    """P = patch.Patch. mon_cols = 스프라이트 색 3개 (밝은 → 어두운), 그림 색은 가장 가까운 것으로"""
    d = bytes(P.d)
    (p1, b1), a1, (p3, b3), a3 = find(d)
    g = gblz.decompress(d, a1); g = bytearray(g[0] if isinstance(g, tuple) else g)
    if logo_png: g = logo_tiles(g, logo_png)                               # None 이면 1.4 로고(デジモンアドベンチャー) 그대로
    bg_tiles, nbg = digital_background(P, d, g) if digital else (b'', 0)
    if logo_png or digital:
        data = gblz.compress(bytes(g))
        bank, p = P.sp.take(len(data), banks=[0x13, 0x11, 0x0b]); P.put(dmrom.addr(bank, p), data)
        P.put(p1, struct.pack('<H', p)); P.put(b1, bytes([bank]))
    # 칠색조 → 디지몬: 타일
    pieces, tiles = sprite_layout(mon_png, mon_cols)
    assert len(pieces) <= 32 and len(tiles) <= 0x800, '조각이 너무 많음 %d' % len(pieces)
    if bg_tiles: tiles = tiles + bytes(0x800 - len(tiles)) + bg_tiles        # vTiles0 를 채우고 넘쳐서 vTiles1 = 배경 0x80~
    data = gblz.compress(tiles)
    bank, p = P.sp.take(len(data), banks=[0x13, 0x11, 0x0b]); P.put(dmrom.addr(bank, p), data)
    P.put(p3, struct.pack('<H', p)); P.put(b3, bytes([bank]))
    # OAM 묶음: 칠색조 1장(19조각, 첫 두 조각 F8 E0 00 00 / F0 E8 02 00)에서 5장 자리(이어져 있음)를 한 장으로 덮고 5장 모두 거기를 가리킴
    o1 = d.find(b'\x13\xf8\xe0\x00\x00\xf0\xe8\x02\x00')
    room = 1 + 4 * (19 + 16 + 15 + 17 + 17)
    blk = bytes([len(pieces)]) + b''.join(bytes([y & 0xff, x & 0xff, t, 0]) for x, y, t in pieces)      # t = 위 타일 번호(짝수)
    assert len(blk) <= room
    P.put(o1, blk)
    bk = o1 // 0x4000; ptr = struct.pack('<H', 0x4000 + o1 % 0x4000)
    tab = d.find(b'\x00' + ptr, bk * 0x4000, (bk + 1) * 0x4000)
    old = [d[tab + 3 * k + 1] | d[tab + 3 * k + 2] << 8 for k in range(5)]
    assert all(0x4000 <= q < 0x8000 for q in old) and old == sorted(old), 'OAM 표 확인 실패 %s' % old
    for k in range(5): P.put(tab + 3 * k, b'\x00' + ptr)
    # 스프라이트 팔레트 0 (제목 화면 앞 팔레트: 흰·어두운×3 → 그림 색), 디지털 배경이면 팔레트 1(빛 가루 노랑·금)도 하늘빛으로
    pal = d.find(b'\xff\x7f\xc7\x0c\xc7\x0c\xc7\x0c\xff\x7f')
    P.put(pal, struct.pack('<4H', 0x7fff, *(rgb555(c) for c in mon_cols)))
    if digital: P.put(pal + 8, struct.pack('<4H', 0x7fff, rgb555((176, 240, 255)), rgb555(CYAN), 0))
    return len(pieces), nbg


# ── 디지털 배경 (사용자 2026-10-02: 「어둡게, 디지털 느낌, 오메가몬 쪽이 빛나게」) ──
# 칸 팔레트는 코드(FillTitleScreenPals)가 정함: 0~17줄 팔레트 0, 로고 1·2·3, 12~16줄 팔레트 4 (화면 줄 95~134 는 옆으로 흐름)
# 새 배경 타일은 칠색조 자리 그림(GFX3) 뒤에 붙임: vTiles0(스프라이트 128칸)을 넘치면 vTiles1 = 배경 0x80~ 칸 (그 뒤 0xF8~ 는 빛 가루가 덮음)
NAVY, DEEP, CYAN, WHITE = (8, 10, 36), (40, 64, 136), (96, 208, 248), (232, 248, 255)


def rle_decode(d, a):
    out = []
    while d[a] != 0xff:
        n = d[a]; v = d[a + 1]; a += 2
        if n & 0x80: out += [(v + k) & 0xff for k in range(n & 0x7f)]
        else: out += [v] * n
    return out


def rle_encode(t):
    out = bytearray(); i = 0
    while i < len(t):
        r = 1
        while i + r < len(t) and t[i + r] == t[i] and r < 127: r += 1
        q = 1
        while i + q < len(t) and t[i + q] == (t[i] + q) & 0xff and q < 127: q += 1
        if q > r: out += bytes([0x80 | q, t[i]]); i += q
        else: out += bytes([r, t[i]]); i += r
    return bytes(out) + b'\xff'


def digital_canvas(cx=76, cy=78):
    """화면 6~17줄(y 48~143) 값(0 짙은 파랑 · 1 하늘빛 · 2 남색 · 3 흰빛). 6~11줄 = 빛 번짐 + 숫자, 12~16줄 = 흐르는 격자(16칸 주기), 17줄 = 남색"""
    H = np.full((144, 256), 2, np.uint8)
    for y in range(48, 94):                                       # 빛 번짐 (y 94·95 는 흐르는 줄과 닿아 남색으로 둠)
        for x in range(160):
            dx, dy = (x - cx) / 44.0, (y - cy) / 24.0; r = (dx * dx + dy * dy) ** 0.5
            chk = (x + y) & 1
            if r < 0.42: v = 1
            elif r < 0.62: v = 1 if chk else 0
            elif r < 0.85: v = 0
            elif r < 1.0: v = 0 if chk else 2
            else: continue
            H[y, x] = v
    for k in range(12):                                           # 빛줄기 12갈래
        ang = k * np.pi / 6 + np.pi / 12
        for t in np.arange(0.3, 1.25, 0.02):
            x = int(round(cx + np.cos(ang) * 44 * t)); y = int(round(cy + np.sin(ang) * 24 * t))
            if 48 <= y < 94 and 0 <= x < 160: H[y, x] = 3 if t < 0.8 else 1
    digits = {'0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111']}
    rng = np.random.RandomState(7)
    for col in list(range(0, 3)) + list(range(17, 20)):            # 양옆 숫자 비 (짙은 파랑)
        for row in range(6, 12):
            if rng.rand() < 0.55:
                g = digits['01'[rng.randint(2)]]; ox, oy = col * 8 + 2, row * 8 + 1
                for yy, line in enumerate(g):
                    for xx, ch in enumerate(line):
                        if ch == '1' and oy + yy < 94: H[oy + yy, ox + xx] = 0
    lines = {96: 1, 97: 0, 100: 0, 104: 0, 109: 1, 115: 0, 122: 0, 130: 1}       # 바닥: 원근처럼 벌어지는 가로줄
    for y, v in lines.items(): H[y, :] = v
    for y in range(98, 135):                                      # 세로줄 16칸마다 (흐르는 줄이라 주기 맞춤)
        for x in range(0, 256, 16):
            if H[y, x] == 2: H[y, x] = 0
    return H


def tile_of(H, y, x):
    return tile_bytes(H[y:y + 8, x:x + 8])


def digital_background(P, d, gfx1):
    """gfx1 = 풀린 TitleScreenGFX1 (bytearray, 바꿈). → (배경 타일 바이트(0x80~), 새 타일맵 RLE)"""
    m = re.search(rb'\x21(..)\x11\x00\x98\x3e(.)\xcd', d, re.S)
    tm_ptr, tm_bank = m.start() + 1, m.start() + 7
    old = rle_decode(d, dmrom.addr(d[tm_bank], d[tm_ptr] | d[tm_ptr + 1] << 8))
    tmap = list(old) + [0x08] * max(0, 32 * 18 - len(old))
    H = digital_canvas()
    blank = np.full((8, 8), 2, np.uint8); blank[3, 3] = 0           # 0x08 = 남색 + 점 하나 (점 격자)
    gfx1[0x08 * 16:0x08 * 16 + 16] = tile_bytes(blank)
    H6 = H.copy()
    for y in range(48, 144):                                      # 비어 있는 칸에도 점 격자 (바닥 위)
        for x in range(0, 256):
            if y < 94 and H6[y, x] == 2 and (x % 8, y % 8) == (3, 3): H6[y, x] = 0
    extra = []; cache = {tile_bytes(blank): 0x08}
    floor_idx = iter(list(range(0x64, 0x70)) + [0x5f] + list(range(0x52, 0x5f)))       # 구름·밑줄 칸을 바닥 타일로
    for row in range(6, 18):
        for col in range(32):
            y, x = row * 8, col * 8
            src = H6 if row < 12 else H
            tb = tile_bytes(src[y:y + 8, x:x + 8]) if (row >= 12 or x < 160) else tile_bytes(blank)
            if row == 17: tb = tile_bytes(blank)
            if tb not in cache:
                if 12 <= row <= 16: t = next(floor_idx); gfx1[t * 16:t * 16 + 16] = tb
                else:
                    t = 0x80 + len(extra); extra.append(tb)
                    assert t < 0xf8, '배경 타일이 모자람'
                cache[tb] = t
            tmap[row * 32 + col] = cache[tb]
    data = rle_encode(tmap[:32 * 18])
    bank, p = P.sp.take(len(data), banks=[0x13, 0x11, 0x0b]); P.put(dmrom.addr(bank, p), data)
    P.put(tm_ptr, struct.pack('<H', p))
    # 같은 루틴 안의 ld a, BANK(TitleScreenTilemap) 3곳
    k = m.start(); hits = [i for i in range(k, k + 0x40) if d[i] == 0x3e and d[i + 1] == d[tm_bank] and d[i + 2] == 0xcd]
    assert len(hits) == 3, hits
    for i in hits: P.put(i + 1, bytes([bank]))
    # 배경 팔레트 0~4 (1.4 값: 흰·하늘·…) → 남색 계열. 로고 팔레트는 바탕(2)·안 쓰는 0 만 바꿈
    pa = d.find(bytes.fromhex('ff7ff27e8f7e0000ff7f7f2a8f7e0000'))
    def c(rgb): return struct.pack('<H', rgb555(rgb))
    for k_ in range(5):
        cur = [d[pa + 8 * k_ + 2 * j] | d[pa + 8 * k_ + 2 * j + 1] << 8 for j in range(4)]
        if k_ in (0, 4): new = c(DEEP) + c(CYAN) + c(NAVY) + c(WHITE)
        else: new = c(DEEP) + struct.pack('<H', cur[1]) + c(NAVY) + struct.pack('<H', cur[3])
        P.put(pa + 8 * k_, new)
    return b''.join(extra), len(extra)
