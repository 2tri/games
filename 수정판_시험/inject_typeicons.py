#!/usr/bin/env python3
"""타입 표시 그림(전투 기술 메뉴·요약 화면의 작은 글자판)을 용어표의 새 타입 이름으로 바꾼다. (2026-10-20)
사용:   python inject_typeicons.py <입력 롬> <출력 롬>            → type_labels.json 의 그림을 a/0/0/8 에 씀
        python inject_typeicons.py --render <입력 롬>            → 글꼴(WenQuanYi Zen Hei)로 새 글자판을 그려 type_labels.json 을 다시 만듦(그림 확인용 type_labels_확인.png 도 저장)
왜:     타입 이름 글(용어표)은 바뀌었지만 이 글자판은 이미지라 원래 이름(불꽃·풀·땅·비행·벌레·바위·강철·악·드래곤·전기·페어리)이 그대로 보였음(10/20 에뮬 시험에서 발견).
구조:   a/0/0/8 의 219~241번(LZ10 압축, 풀면 304바이트 = 헤더 0x30 + 32×16 픽셀 4비트 타일 8개, 가로 4칸 순서). 칠한 색 번호는 타입마다 다르고(칩 바탕·테두리),
        글자는 15(흰색)+14(그림자, 글자 오른쪽·아래 1칸). 바꾸는 것은 글자 픽셀(14·15)뿐 — 칩 색은 원래 그림 것을 그대로 씀.
바꾸는 11종: 219~241 중 221 드래곤→용, 222 전기→번개, 224 악→암흑, 226 불꽃→화염, 227 비행→바람, 229 땅→대지, 231 벌레→곤충, 233 풀→식물, 236 페어리→빛, 237 바위→암석, 238 강철→기계.
        (그대로 두는 것: 노말·격투·독·고스트·에스퍼·얼음·물 = 새 이름과 같음. 232 슬기로움·239 강인함·240 근사함·219 아름다움·220 귀여움은 콘테스트용.)"""
import sys, os, json
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..'))); sys.path.insert(0, H)
import hg1, lz10
from hg1 import NDS, NARC
NEW = {221: '용', 222: '번개', 224: '암흑', 226: '화염', 227: '바람', 229: '대지', 231: '곤충', 233: '식물', 236: '빛', 237: '암석', 238: '기계'}
JS = os.path.join(H, 'type_labels.json')
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'

def decode(x):
    d = x[0x30:]; rows = [[0] * 32 for _ in range(16)]
    for t in range(8):
        for y in range(8):
            for xx in range(4):
                b = d[t * 32 + y * 4 + xx]
                for k, v in enumerate((b & 15, b >> 4)): rows[(t // 4) * 8 + y][(t % 4) * 8 + xx * 2 + k] = v
    return rows

def encode(hdr, rows):
    out = bytearray(hdr)
    for t in range(8):
        for y in range(8):
            for xx in range(4):
                out.append(rows[(t // 4) * 8 + y][(t % 4) * 8 + xx * 2] | (rows[(t // 4) * 8 + y][(t % 4) * 8 + xx * 2 + 1] << 4))
    return bytes(out)

def render(src, text):
    from PIL import Image, ImageDraw, ImageFont
    rows = [r[:] for r in src]
    for y in range(2, 14):
        fill = src[y][2] if src[y][2] not in (14, 15) else src[y][1]
        for x in range(2, 30):
            if rows[y][x] in (14, 15): rows[y][x] = fill
    size = 14 if len(text) == 1 else 12
    f = ImageFont.truetype(FONT, size); m = Image.new('L', (32, 16), 0); d = ImageDraw.Draw(m); d.fontmode = '1'
    bb = d.textbbox((0, 0), text, font=f); w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((32 - w) // 2 - bb[0], 3 - bb[1] + max(0, (9 - h) // 2)), text, font=f, fill=255)
    px = m.load()
    for y in range(16):
        for x in range(32):
            if px[x, y] > 127:
                rows[y][x] = 15
                for ex, ey in ((x + 1, y), (x, y + 1)):
                    if 2 <= ex < 30 and 2 <= ey < 14 and px[ex, ey] <= 127: rows[ey][ex] = 14
    # 그림자 칸이 글자 칸을 덮지 않게 한 번 더
    for y in range(16):
        for x in range(32):
            if px[x, y] > 127: rows[y][x] = 15
    return rows

def main():
    a = sys.argv[1:]
    if a and a[0] == '--render':
        rom = NDS(open(a[1], 'rb').read()); L = NARC(rom.get('a/0/0/8')).files
        out = {}
        for i, t in NEW.items(): out[str(i)] = [''.join('0123456789abcdef'[v] for v in r) for r in render(decode(lz10.decompress(L[i])), t)]
        json.dump(out, open(JS, 'w'), ensure_ascii=False, indent=0)
        from PIL import Image
        sh = Image.new('L', (32 * 4 * 2 + 8, 64 * len(NEW)), 0)
        for r, (i, t) in enumerate(NEW.items()):
            for c, rows in enumerate((decode(lz10.decompress(L[i])), [[int(ch, 16) for ch in s] for s in out[str(i)]])):
                im = Image.new('L', (32, 16)); px = im.load()
                for y in range(16):
                    for x in range(32): px[x, y] = min(255, rows[y][x] * 17)
                sh.paste(im.resize((128, 64), Image.NEAREST), (c * 132, r * 64))
        sh.save(os.path.join(H, 'type_labels_확인.png')); print('type_labels.json', len(out)); return
    src, dst = a[0], a[1]
    rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/0/8')); L = list(nar.files)
    data = json.load(open(JS, encoding='utf-8'))
    for i_, rws in data.items():
        i = int(i_); x = lz10.decompress(L[i]); assert x and x[:4] == b'RGCN' and len(x) == 304, '글자판 모양이 다름 %d' % i
        rows = [[int(ch, 16) for ch in s] for s in rws]
        assert len(rows) == 16 and all(len(r) == 32 for r in rows)
        nx = encode(x[:0x30], rows); assert decode(nx) == rows
        L[i] = lz10.compress(nx); assert lz10.decompress(L[i]) == nx
    nar.files = L; how = rom.put('a/0/0/8', nar.build())
    open(dst, 'wb').write(bytes(rom.d)); print('타입 글자판 %d장 바꿈 (%s)' % (len(data), how))
main()
