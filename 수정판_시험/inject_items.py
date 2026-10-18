#!/usr/bin/env python3
"""가방 도구 아이콘(a/0/1/8)에 디지볼·문장·디지멘탈 그림을 넣는다. 롬은 읽기만 하고 새 파일로 저장. (Claude 작성, 2026-10-14)
사용:   python inject_items.py <입력 롬.nds> <출력 롬.nds> [--preview 폴더]
위치:   a/0/1/8 의 RGCN(560바이트, 4bpp 32x32 = 8x8 타일 4x4) + 바로 다음 멤버 RLCN(16색, 0번 투명).
        도구 번호 → 멤버 번호 표는 못 찾아 그림을 눈으로 보고 골랐다(아래 ITEMS)
넣는 것: 볼 4 · 돌 9(디지멘탈) · 심해의이빨·비늘(문장). 희망의 디지멘탈 그림은 없어 각성의돌은 그대로 둠."""
import sys, os, struct, argparse, collections
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC
from PIL import Image

UI = os.path.join(PROJ, 'games', 'digimon', 'art', 'src', 'ui')
BALLS = os.path.join(PROJ, 'balls_out')
# 도구 번호: (그림 파일, a/0/1/8 의 RGCN 멤버 번호). 멤버 번호는 롬 그림을 하나씩 그려 보고 고름(번호 규칙 표를 못 찾음):
#  볼 4종 = 멤버 2·4·6·8 / 돌 = 태양 115·달 117·불꽃 119·천둥 121·물 123·리프 125 (연속 6개, 아이템 번호 80~85 순서)
#  빛나는 돌 480·어둠 482·각성 484·동글동글 486 / 심해의이빨 258·비늘 260
ITEMS = {
    1: ('BALL:0.78', 2), 2: ('BALL:0.14', 4), 3: ('BALL:None', 6), 4: ('BALL:0.02', 8),   # 마스터 보라·하이퍼 노랑·수퍼 파랑(원본)·디지볼 빨강
    82: (os.path.join(UI, 'digimental_courage_ai.png'), 119),      # 불꽃의돌 = 용기
    83: (os.path.join(UI, 'digimental_friendship_ai.png'), 121),   # 천둥의돌 = 우정
    80: (os.path.join(UI, 'digimental_love_ai.png'), 115),         # 태양의돌 = 사랑
    85: (os.path.join(UI, 'digimental_purity_ai.png'), 125),       # 리프의돌 = 순수
    81: (os.path.join(UI, 'digimental_knowledge_ai.png'), 117),    # 달의돌 = 지식
    84: (os.path.join(UI, 'digimental_sincerity_ai.png'), 123),    # 물의돌 = 성실
    107: (os.path.join(UI, 'digimental_light_ai.png'), 480),       # 빛의돌(빛나는 돌) = 빛
    110: (os.path.join(UI, 'digimental_miracle_ai.png'), 486),     # 동글동글돌 = 기적
    226: (os.path.join(UI, 'crest_courage_ai.png'), 258),          # 심해의이빨 = 용기의 문장
    227: (os.path.join(UI, 'crest_hope_ai.png'), 260),             # 심해의비늘 = 희망의 문장
}

def cutout(path):
    """제미나이 그림은 투명이 아니라 체크무늬 배경이 박혀 있다 → 가장자리와 이어진 「채도 낮고 가장자리 밝기 범위 안」 픽셀을 투명으로"""
    im = Image.open(path).convert('RGBA'); w, h = im.size; px = im.load()
    if im.getchannel('A').getextrema()[0] < 255:
        return im
    vs = []
    for x in range(0, w, 2):
        for y in (0, 1, h - 2, h - 1): vs.append(max(px[x, y][:3]))
    for y in range(0, h, 2):
        for x in (0, 1, w - 2, w - 1): vs.append(max(px[x, y][:3]))
    vs.sort(); lo = vs[int(len(vs) * 0.02)] - 14; hi = vs[int(len(vs) * 0.98)] + 14
    def isbg(p):
        return max(p[:3]) - min(p[:3]) <= 24 and lo <= max(p[:3]) <= hi
    seen = bytearray(w * h); stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]: continue
        if not isbg(px[x, y]): continue
        seen[y * w + x] = 1; px[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im

def ball_variant(path, hue):
    """디지볼 그림(파랑 회로)의 채도 높은 부분 색상을 돌려 볼 4종 색을 만듦(make_balls 는 주황 그림 전용이라 파랑 그림은 4종이 같아짐)"""
    import colorsys, tempfile
    im = cutout(path); px = im.load(); w, h = im.size
    if hue is not None:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if not a: continue
                hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                if ss > 0.35 and 0.45 <= hh <= 0.72 and 0.12 < ll < 0.9:
                    r2, g2, b2 = colorsys.hls_to_rgb(hue, ll, ss); px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    fn = os.path.join(tempfile.gettempdir(), 'ball_%s.png' % ('x' if hue is None else int(hue * 100)))
    im.save(fn); return fn

def to_icon(path, size=32, ncol=15):
    im = cutout(path); bb = im.getchannel('A').getbbox(); im = im.crop(bb)
    s = (size - 2) / max(im.size); nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((nw, nh), Image.BOX)
    can = Image.new('RGBA', (size, size), (0, 0, 0, 0)); can.paste(im, ((size - nw) // 2, (size - nh) // 2), im)
    a = can.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
    rgb = Image.new('RGB', (size, size), (0, 0, 0)); rgb.paste(can.convert('RGB'), (0, 0), a)
    q = rgb.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:ncol * 3]; cols = [tuple(pal[i * 3:i * 3 + 3]) for i in range(ncol)]
    idx = [[(q.getpixel((x, y)) + 1) if a.getpixel((x, y)) else 0 for x in range(size)] for y in range(size)]
    return idx, cols

def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--preview', default=None)
    A = ap.parse_args()
    rom = NDS(open(A.rom, 'rb').read()); nar = NARC(rom.get('a/0/1/8')); f = list(nar.files)
    sheet = Image.new('RGBA', (len(ITEMS) * 34, 34), (90, 90, 90, 255)); k = 0
    for n, (path, gm) in ITEMS.items():
        if path.startswith('BALL:'):
            hv = path[5:]; path = ball_variant(os.path.join(UI, 'digiball_ai.png'), None if hv == 'None' else float(hv))
        idx, cols = to_icon(path)
        g = bytearray(f[gm]); p = bytearray(f[gm + 1])
        assert g[:4] == b'RGCN' and p[:4] == b'RLCN' and len(g) == 560, (n, gm, len(g))
        c = g.find(b'RAHC') + 0x20
        for t in range(16):
            ox, oy = (t % 4) * 8, (t // 4) * 8
            for y in range(8):
                for x in range(0, 8, 2):
                    g[c + t * 32 + y * 4 + x // 2] = idx[oy + y][ox + x] | (idx[oy + y][ox + x + 1] << 4)
        t0 = p.find(b'TTLP') + 0x18
        struct.pack_into('<H', p, t0, 0)
        for i, col in enumerate(cols): struct.pack_into('<H', p, t0 + 2 * (1 + i), bgr555(col))
        f[gm] = bytes(g); f[gm + 1] = bytes(p)
        im = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); ip = im.load()
        for y in range(32):
            for x in range(32):
                if idx[y][x]: ip[x, y] = cols[idx[y][x] - 1] + (255,)
        sheet.alpha_composite(im, (k * 34 + 1, 1)); k += 1
    nar.files = f
    print('쓰기:', rom.put('a/0/1/8', nar.build()))
    open(A.out, 'wb').write(bytes(rom.d)); print('저장:', A.out, '도구', len(ITEMS), '개')
    if A.preview:
        os.makedirs(A.preview, exist_ok=True)
        sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(A.preview, '미리보기_도구아이콘.png'))
