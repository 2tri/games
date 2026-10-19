#!/usr/bin/env python3
"""제미나이 걷기 시트 → 32×32 칸 4줄×3칸 투명 시트 (2026-10-15)
사용:   python sheet_cut.py "<제미나이 그림.png>" --out taichi_walk_4x3.png [--map "down:0,1,2 up:6,7,8 right:9,10,11 left:flip"] [--height 30]
        python sheet_cut.py "<그림>" --list          → 컷 번호·위치만 적은 미리보기(컷_번호.png)를 만들어 눈으로 번호를 확인
하는 일
 1) 흰(또는 체크무늬·단색) 배경을 투명으로: 가장자리와 이어진 「채도 낮고 밝은」 색을 배경으로 봄.
 2) 세로·가로로 비어 있는 띠를 찾아 격자를 나눈 뒤, 칸마다 불투명 픽셀의 상자를 컷으로(왼쪽 위부터 0, 1, 2 …).
 3) --map 으로 방향마다 컷 3개(서기·걸음1·걸음2)를 고른다. 「flip」은 반대 방향 줄을 좌우로 뒤집음.
 4) 컷을 --height 픽셀 키로 줄여(가로세로 비율 유지, 가장 가까운 이웃) 32×32 칸의 가운데·발 아래 1px 위에 놓는다. 결과 96×128 RGBA.
기본 --map 은 10/15 태일 시트(6칸×3줄) 기준: 0~2 정면, 6~8 뒷모습, 9~11 왼쪽 보는 옆, 15~17 오른쪽 보는 옆(회사 PC 에서 눈으로 확인). 나리 시트는 --list 로 번호를 보고 --map 을 바꿈."""
import os, sys, argparse
from PIL import Image

def is_bg(p):
    r, g, b, a = p
    return a < 16 or (max(r, g, b) - min(r, g, b) < 28 and min(r, g, b) > 200)   # 흰·연회색(체크무늬) = 배경

def key_bg(im):
    """가장자리와 이어진 배경색만 투명으로(인물 안의 흰 장갑은 남김)"""
    im = im.convert('RGBA'); w, h = im.size; px = im.load()
    seen = bytearray(w * h); stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x]: continue
        if not is_bg(px[x, y]): continue
        seen[y * w + x] = 1; px[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im

def bands(mask, n, axis):
    """비어 있지 않은 구간(시작, 끝) 목록 — axis 0: 가로(열 투영), 1: 세로(행 투영)"""
    out = []; cur = None
    for i in range(n):
        if mask[i]:
            if cur is None: cur = i
        elif cur is not None: out.append((cur, i)); cur = None
    if cur is not None: out.append((cur, n))
    return out

def cuts(im, min_size=12):
    w, h = im.size; px = im.load()
    cols = [any(px[x, y][3] > 16 for y in range(h)) for x in range(w)]
    rows = [any(px[x, y][3] > 16 for x in range(w)) for y in range(h)]
    out = []
    for y0, y1 in bands(rows, h, 1):
        if y1 - y0 < min_size: continue
        sub = im.crop((0, y0, w, y1)); sp = sub.load(); sw, sh = sub.size
        scols = [any(sp[x, y][3] > 16 for y in range(sh)) for x in range(sw)]
        for x0, x1 in bands(scols, sw, 0):
            if x1 - x0 < min_size: continue
            cell = sub.crop((x0, 0, x1, sh)); bb = cell.getbbox()
            if bb: out.append(cell.crop(bb))
    return out

PAL = None
def sheet_palette(im, n=15):
    """원본 시트(배경 투명)의 색 15개 — 줄인 뒤 이 색으로만 칠해 도트가 또렷하게"""
    rgb = Image.new('RGB', im.size, (0, 0, 0)); rgb.paste(im, mask=im.split()[3])
    q = rgb.quantize(n + 1, method=Image.MEDIANCUT, dither=Image.NONE); pal = q.getpalette()[:3 * (n + 1)]
    cols = [tuple(pal[3 * i:3 * i + 3]) for i in range(n + 1)]
    return [c for c in cols if c != (0, 0, 0)][:n]

def place(cut, height, flip=False, smooth=True):
    cw, ch = cut.size; s = height / ch; nw = max(1, round(cw * s))
    if smooth and PAL:
        c = cut.resize((nw, height), Image.BOX); px = c.load()
        for y in range(height):
            for x in range(nw):
                r, g, b, a = px[x, y]
                if a < 128: px[x, y] = (0, 0, 0, 0); continue
                px[x, y] = min(PAL, key=lambda q: (q[0] - r) ** 2 + (q[1] - g) ** 2 + (q[2] - b) ** 2) + (255,)
    else: c = cut.resize((nw, height), Image.NEAREST)
    if flip: c = c.transpose(Image.FLIP_LEFT_RIGHT)
    if nw > 32: c = c.crop(((nw - 32) // 2, 0, (nw - 32) // 2 + 32, height)); nw = 32
    tile = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); tile.paste(c, ((32 - nw) // 2, 32 - 1 - height), c)
    return tile

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--out', default='walk_4x3.png')
    ap.add_argument('--map', default='down:0,1,2 up:6,7,8 left:9,10,11 right:15,16,17'); ap.add_argument('--height', type=int, default=30)
    ap.add_argument('--list', action='store_true'); ap.add_argument('--smooth', action='store_true', help='평균으로 줄이고 시트 15색으로 칠함(10/15 태일 시트에서는 가장 가까운 이웃(기본)이 더 또렷했음)'); A = ap.parse_args()
    im = key_bg(Image.open(A.src)); cs = cuts(im)
    global PAL; PAL = sheet_palette(im)
    print('컷 %d개:' % len(cs), ' '.join('%d(%dx%d)' % (i, c.size[0], c.size[1]) for i, c in enumerate(cs)))
    if A.list or not cs:
        cols = min(6, max(1, len(cs))); rows = (len(cs) + cols - 1) // cols; cw = max(c.size[0] for c in cs) + 8; chh = max(c.size[1] for c in cs) + 14
        sheet = Image.new('RGBA', (cols * cw, rows * chh), (255, 255, 255, 255))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(sheet)
        for i, c in enumerate(cs):
            x, y = (i % cols) * cw, (i // cols) * chh; sheet.paste(c, (x + 4, y + 12), c); dr.text((x + 2, y), str(i), fill=(255, 0, 0, 255))
        sheet.save('컷_번호.png'); print('→ 컷_번호.png (번호 확인용)'); return
    spec = {}
    for tok in A.map.split():
        k, v = tok.split(':'); spec[k] = v
    order = ['down', 'up', 'left', 'right']; out = Image.new('RGBA', (96, 128), (0, 0, 0, 0))
    for r, k in enumerate(order):
        v = spec.get(k, 'flip'); flip = False
        if v == 'flip':
            v = spec['right' if k == 'left' else 'left']; flip = True
        idx = [int(x) for x in v.split(',')][:3]
        while len(idx) < 3: idx.append(idx[0])
        for col, i in enumerate(idx):
            if i >= len(cs): raise SystemExit('컷 번호 %d 가 없음(컷 %d개) — --list 로 번호 확인' % (i, len(cs)))
            out.paste(place(cs[i], A.height, flip, A.smooth), (col * 32, r * 32))
    out.save(A.out); print('→ %s (96x128, 키 %dpx)' % (A.out, A.height))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
