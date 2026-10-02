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


def apply(P, logo_png, mon_png, mon_cols):
    """P = patch.Patch. mon_cols = 스프라이트 색 3개 (밝은 → 어두운), 그림 색은 가장 가까운 것으로"""
    d = bytes(P.d)
    (p1, b1), a1, (p3, b3), a3 = find(d)
    if logo_png:                                                          # None 이면 1.4 로고(デジモンアドベンチャー) 그대로
        g = gblz.decompress(d, a1); g = bytearray(g[0] if isinstance(g, tuple) else g)
        data = gblz.compress(bytes(logo_tiles(g, logo_png)))
        bank, p = P.sp.take(len(data), banks=[0x13, 0x11, 0x0b]); P.put(dmrom.addr(bank, p), data)
        P.put(p1, struct.pack('<H', p)); P.put(b1, bytes([bank]))
    # 칠색조 → 디지몬: 타일
    pieces, tiles = sprite_layout(mon_png, mon_cols)
    assert len(pieces) <= 30, '조각이 너무 많음 %d' % len(pieces)
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
    # 스프라이트 팔레트 0 (제목 화면 앞 팔레트: 흰·어두운×3 → 그림 색)
    pal = d.find(b'\xff\x7f\xc7\x0c\xc7\x0c\xc7\x0c\xff\x7f')
    P.put(pal, struct.pack('<4H', 0x7fff, *(rgb555(c) for c in mon_cols)))
    return len(pieces)
