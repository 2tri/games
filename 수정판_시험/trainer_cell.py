"""트레이너 전투 그림(a/0/5/8 직업별 파일 0번 + 파일 2번 RECN) 셀(OAM) 조립·분해 (2026-10-19 v1.1)
배경: 파일 0번은 8x8 타일을 「조각(OAM)」 단위로 모아 둔 자료 — 조각 6개(64x64 · 16x32 · 16x32 · 32x16 · 32x16 · 16x16)가 모여 80x80 한 장이 된다.
      셀이 3개인 직업(9648바이트 = 3200x3)은 프레임마다 3200바이트씩. 셀 1개 직업은 3200바이트.
      v1 의 hg4_trainer 는 이 자료를 한 줄씩 이어진 그림처럼 덮어 써서 전투에서 그림이 깨졌다(소라 등).
RECN(NCER): KBEC 머리(+8 셀 수, +10 종류, +12 셀표 위치, +16 타일 경계(0:32B 1:64B 2:128B 3:256B), +20 VRAM 전송표 위치),
            셀표 = 셀마다 16바이트(조각 수 u16, 속성 u16, 조각 자료 위치 u32(셀표 끝 기준), 범위 8B), 조각 = attr0·attr1·attr2 (u16 3개)."""
import struct

SHAPE = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
         (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
         (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}

def parse_ncer(recn):
    k = recn.find(b'KBEC')
    if k < 0: raise ValueError('KBEC 없음')
    ncell, kind, cell_off, mapping, vram_off = struct.unpack_from('<HHIII', recn, k + 8)[0:5] if False else (
        struct.unpack_from('<H', recn, k + 8)[0], struct.unpack_from('<H', recn, k + 10)[0], struct.unpack_from('<I', recn, k + 12)[0],
        struct.unpack_from('<I', recn, k + 16)[0], struct.unpack_from('<I', recn, k + 20)[0])
    cell_sz = 16 if kind == 1 else 8
    base = k + 8 + cell_off; data0 = base + ncell * cell_sz
    cells = []
    for i in range(ncell):
        n, attr, off = struct.unpack_from('<HHI', recn, base + i * cell_sz)
        oams = []
        for j in range(n):
            a0, a1, a2 = struct.unpack_from('<3H', recn, data0 + off + j * 6)
            y = a0 & 0xFF; y = y - 256 if y >= 128 else y
            x = a1 & 0x1FF; x = x - 512 if x >= 256 else x
            w, h = SHAPE[((a0 >> 14) & 3, (a1 >> 14) & 3)]
            oams.append(dict(x=x, y=y, w=w, h=h, tile=a2 & 0x3FF, hflip=bool(a1 & 0x1000), vflip=bool(a1 & 0x2000)))
        cells.append(oams)
    transfers = []
    if vram_off:
        t0 = k + 8 + vram_off
        # 전송표: [최대 크기 u32][머리 크기 u32=8][(원본 위치 u32, 크기 u32) × 셀 수]
        for i in range(ncell):
            src, size = struct.unpack_from('<II', recn, t0 + 8 + i * 8)
            transfers.append((src, size))
    return dict(cells=cells, mapping=mapping, transfers=transfers)

def _px(data):
    p = []
    for b in data: p += [b & 15, b >> 4]
    return p

def _unpx(p):
    return bytes(p[i] | (p[i + 1] << 4) for i in range(0, len(p), 2))

def cell_region(ncgr_body, info, ci):
    """셀 ci 가 쓰는 타일 자료 구간(바이트)"""
    if info['transfers']:
        src, size = info['transfers'][ci]
        return src, size
    return 0, len(ncgr_body)

def cell_origin(info, ci):
    """셀마다 그림 왼쪽 위 기준점: 조각 맨 왼쪽·맨 위가 80x80 의 (0,0) 이 되게(프레임이 옆으로 치우친 셀도 같은 80x80 로 다룸). 빈 셀은 None"""
    c = info['cells'][ci]
    if not c: return None
    return (-min(o['x'] for o in c), -min(o['y'] for o in c))

def assemble(ncgr_body, info, ci, size=80, origin=None):
    """→ size x size 색 번호 행렬(0 = 투명)"""
    src, n = cell_region(ncgr_body, info, ci)
    og = origin if origin is not None else cell_origin(info, ci)
    if og is None: return [[0] * size for _ in range(size)]
    ox, oy = og if isinstance(og, tuple) else (og, og)
    tiles = _px(ncgr_body[src:src + n]); unit = 32 << info['mapping']; img = [[0] * size for _ in range(size)]
    for o in info['cells'][ci]:
        tw, th = o['w'] // 8, o['h'] // 8; first = o['tile'] * unit // 32
        for ty in range(th):
            for tx in range(tw):
                t = first + ty * tw + tx
                for yy in range(8):
                    for xx in range(8):
                        i = t * 64 + yy * 8 + xx
                        v = tiles[i] if i < len(tiles) else 0
                        px_, py_ = tx * 8 + xx, ty * 8 + yy
                        if o['hflip']: px_ = o['w'] - 1 - px_
                        if o['vflip']: py_ = o['h'] - 1 - py_
                        X, Y = o['x'] + px_ + ox, o['y'] + py_ + oy
                        if 0 <= X < size and 0 <= Y < size and v: img[Y][X] = v
    return img

def disassemble(ncgr_body, info, ci, img, origin=None):
    """색 번호 행렬 img → 셀 ci 구간 타일 자료만 바꾼 새 ncgr_body"""
    src, n = cell_region(ncgr_body, info, ci)
    og = origin if origin is not None else cell_origin(info, ci)
    if og is None: return bytes(ncgr_body)
    ox, oy = og if isinstance(og, tuple) else (og, og)
    tiles = _px(ncgr_body[src:src + n]); unit = 32 << info['mapping']; size = len(img)
    for o in info['cells'][ci]:
        tw, th = o['w'] // 8, o['h'] // 8; first = o['tile'] * unit // 32
        for ty in range(th):
            for tx in range(tw):
                t = first + ty * tw + tx
                for yy in range(8):
                    for xx in range(8):
                        i = t * 64 + yy * 8 + xx
                        if i >= len(tiles): continue
                        px_, py_ = tx * 8 + xx, ty * 8 + yy
                        if o['hflip']: px_ = o['w'] - 1 - px_
                        if o['vflip']: py_ = o['h'] - 1 - py_
                        X, Y = o['x'] + px_ + ox, o['y'] + py_ + oy
                        tiles[i] = img[Y][X] if 0 <= X < size and 0 <= Y < size else 0
    out = bytearray(ncgr_body); out[src:src + n] = _unpx(tiles)
    return bytes(out)
