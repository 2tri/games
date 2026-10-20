#!/usr/bin/env python3
"""도감 화면(도감 등록·도감 상세)의 타입 칩 그림 11장을 새 타입 이름으로 바꾼다. (2026-10-20, 에뮬에서 도감 등록 화면을 띄워 발견)
사용:   python inject_dexchips.py <입력 롬> <출력 롬>
        python inject_dexchips.py --render <입력 롬>      → 글꼴(WenQuanYi Zen Hei)로 그려 dex_chips.json 과 dex_chips_확인.png 를 다시 만듦
왜:     전투·요약 화면의 타입 글자판(a/0/0/8, inject_typeicons.py)과 별개로 도감 쪽 칩(a/0/6/8)이 따로 있어 「드래곤」「강철」「불꽃」이 그대로 보였음.
구조:   a/0/6/8 의 36~52·123번(LZ10, 풀면 432바이트 = 헤더 0x30 + 타일 12개). 도감 화면의 OAM 에서 확인: 32×16 블록(타일 0~7, 가로 4칸 순서) + 오른쪽 16×16 블록(타일 8~11, 2×2) = 가로 48 × 세로 16.
        칩 바탕 색 번호는 줄마다 다르고, 글자는 15(흰색)+14(그림자: 글자 오른쪽·아래 1칸) — 바꾸는 것은 글자 픽셀뿐.
바꾸는 11종: 52 드래곤→용, 40 전기→번개, 48 악→암흑, 37 불꽃→화염, 50 비행→바람, 44 땅→대지, 47 벌레→곤충, 38 풀→식물, 123 페어리→빛, 41 바위→암석, 45 강철→기계."""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..'))); sys.path.insert(0, H)
import hg1, lz10
from hg1 import NDS, NARC
NEW = {52: '용', 40: '번개', 48: '암흑', 37: '화염', 50: '바람', 44: '대지', 47: '곤충', 38: '식물', 123: '빛', 41: '암석', 45: '기계'}
JS = os.path.join(H, 'dex_chips.json')
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
W, HGT = 48, 16

def decode(x):
    t = x[0x30:]; rows = [[0] * W for _ in range(HGT)]
    def put(k, bx, by):
        for y in range(8):
            for xx in range(4):
                b = t[k * 32 + y * 4 + xx]
                for j, v in enumerate((b & 15, b >> 4)): rows[by + y][bx + xx * 2 + j] = v
    for k in range(8): put(k, (k % 4) * 8, (k // 4) * 8)
    for k in range(4): put(8 + k, 32 + (k % 2) * 8, (k // 2) * 8)
    return rows

def encode(hdr, rows):
    out = bytearray(hdr)
    def get(k, bx, by):
        for y in range(8):
            for xx in range(4):
                out.append(rows[by + y][bx + xx * 2] | (rows[by + y][bx + xx * 2 + 1] << 4))
    for k in range(8): get(k, (k % 4) * 8, (k // 4) * 8)
    for k in range(4): get(8 + k, 32 + (k % 2) * 8, (k // 2) * 8)
    return bytes(out)

def render(src, text):
    from PIL import Image, ImageDraw, ImageFont
    rows = [r[:] for r in src]
    for y in range(2, 14):
        fill = src[y][4] if src[y][4] not in (14, 15) else src[y][3]
        for x in range(4, 44):
            if rows[y][x] in (14, 15): rows[y][x] = fill
    size = 14 if len(text) == 1 else 12
    f = ImageFont.truetype(FONT, size); m = Image.new('L', (W, HGT), 0); d = ImageDraw.Draw(m); d.fontmode = '1'
    bb = d.textbbox((0, 0), text, font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((W - w) // 2 - bb[0], 3 - bb[1] + max(0, (9 - h) // 2)), text, font=f, fill=255)
    px = m.load()
    for y in range(HGT):
        for x in range(W):
            if px[x, y] > 127:
                rows[y][x] = 15
                for ex, ey in ((x + 1, y), (x, y + 1)):
                    if 4 <= ex < 44 and 2 <= ey < 14 and px[ex, ey] <= 127: rows[ey][ex] = 14
    for y in range(HGT):
        for x in range(W):
            if px[x, y] > 127: rows[y][x] = 15
    return rows

def main():
    a = sys.argv[1:]
    if a and a[0] == '--render':
        rom = NDS(open(a[1], 'rb').read()); L = NARC(rom.get('a/0/6/8')).files
        out = {}
        for i, t in NEW.items(): out[str(i)] = [''.join('0123456789abcdef'[v] for v in r) for r in render(decode(lz10.decompress(L[i])), t)]
        json.dump(out, open(JS, 'w'), ensure_ascii=False, indent=0)
        from PIL import Image
        sh = Image.new('L', (W * 4 * 2 + 8, 64 * len(NEW)), 0)
        for r, (i, t) in enumerate(NEW.items()):
            for c, rows in enumerate((decode(lz10.decompress(L[i])), [[int(ch, 16) for ch in s] for s in out[str(i)]])):
                im = Image.new('L', (W, HGT)); px = im.load()
                for y in range(HGT):
                    for x in range(W): px[x, y] = min(255, rows[y][x] * 17)
                sh.paste(im.resize((W * 4, 64), Image.NEAREST), (c * (W * 4 + 8), r * 64))
        sh.save(os.path.join(H, 'dex_chips_확인.png')); print('dex_chips.json', len(out)); return
    src, dst = a[0], a[1]
    rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/6/8')); L = list(nar.files)
    data = json.load(open(JS, encoding='utf-8'))
    for i_, rws in data.items():
        i = int(i_); x = lz10.decompress(L[i]); assert x and x[:4] == b'RGCN' and len(x) == 432, '도감 칩 모양이 다름 %d' % i
        rows = [[int(ch, 16) for ch in s] for s in rws]
        assert len(rows) == HGT and all(len(r) == W for r in rows)
        nx = encode(x[:0x30], rows); assert decode(nx) == rows
        L[i] = lz10.compress(nx); assert lz10.decompress(L[i]) == nx
    nar.files = L; how = rom.put('a/0/6/8', nar.build())
    open(dst, 'wb').write(bytes(rom.d)); print('도감 타입 칩 %d장 바꿈 (%s)' % (len(data), how))
main()
