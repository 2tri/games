"""글자 격자 ↔ png — Claude 가 픽셀을 글자로 고쳐 그리기 위한 도구
  글자: . 흰  - 밝은 톤  + 어두운 톤  # 검정  _ 배경(투명). 한 줄이 한 행.
    python3 grid.py txt  art/tunomon-f.png  art/grid/tunomon-f.txt         png → txt
    python3 grid.py png  art/grid/tunomon-f.txt art/tunomon-f.png --id tunomon   txt → 롬에 넣을 4색 png (specs 의 몸 색)
    python3 grid.py show art/grid/tunomon-f.txt art/grid/tunomon-b.txt -o _tunomon_x6.png --id tunomon --scale 6   확인용 확대
--id 가 없으면 회색 4톤(248·176·96·24)으로 저장 → ingest.py --flat 으로도 받을 수 있음."""
import argparse, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
CH = '.-+#'                     # 0 흰 1 밝은 2 어두운 3 검정, -1 배경 '_'
GRAY = [(248, 248, 248), (176, 176, 176), (96, 96, 96), (24, 24, 24)]


def lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def png2arr(path):
    """4색 png → 칸 배열 (-1 배경, 0~3). 흰·검정은 밝기 끝, 가운데 색 둘은 밝기 순서로"""
    a = np.asarray(Image.open(path).convert('RGBA')).astype(int)
    op = a[..., 3] > 128
    cols = sorted({tuple(x[:3]) for x in a[op]}, key=lambda c: -lum(c))
    idx = {}
    mids = [c for c in cols if 40 <= lum(c) <= 235]
    for c in cols:
        L = lum(c)
        if L > 235: idx[c] = 0
        elif L < 40: idx[c] = 3
        elif len(mids) >= 2: idx[c] = 1 if L >= (lum(mids[0]) + lum(mids[-1])) / 2 else 2
        else: idx[c] = 1 if L >= 128 else 2
    t = -np.ones(op.shape, int)
    for y, x in zip(*np.where(op)): t[y, x] = idx[tuple(a[y, x, :3])]
    return t


def arr2txt(t):
    return '\n'.join(''.join('_' if v < 0 else CH[v] for v in row) for row in t) + '\n'


def txt2arr(path):
    rows = [r.rstrip('\n') for r in open(path, encoding='utf-8') if r.strip() and not r.startswith(';')]
    w = max(len(r) for r in rows)
    t = -np.ones((len(rows), w), int)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in CH: t[y, x] = CH.index(ch)
            elif ch not in '_ ': raise SystemExit('%s %d행 %d열: 모르는 글자 %r' % (path, y + 1, x + 1, ch))
    return t


def palette(did):
    if not did: return GRAY
    sys.path.insert(0, os.path.join(WEB, 'romhack', 'order')); import specs
    sp = specs.by_id(did)
    if not sp or not sp.get('pal'): raise SystemExit('specs.py 에 %s 의 pal 이 없음' % did)
    return [GRAY[0], tuple(sp['pal'][0]), tuple(sp['pal'][1]), GRAY[3]]


def arr2img(t, pal, scale=1, bg=None):
    h, w = t.shape; a = np.zeros((h, w, 4), np.uint8)
    for i, c in enumerate(pal): a[t == i] = (*c, 255)
    if bg: a[t < 0] = (*bg, 255)
    im = Image.fromarray(a, 'RGBA')
    return im.resize((w * scale, h * scale), Image.NEAREST) if scale > 1 else im


def crop(t):
    ys, xs = np.where(t >= 0)
    return t[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['txt', 'png', 'show']); ap.add_argument('src', nargs='+')
    ap.add_argument('dst', nargs='?'); ap.add_argument('-o'); ap.add_argument('--id'); ap.add_argument('--scale', type=int, default=6)
    a = ap.parse_args()
    if a.cmd == 'txt':
        src, dst = a.src[0], a.src[1] if len(a.src) > 1 else a.dst
        open(dst, 'w', encoding='utf-8').write(arr2txt(png2arr(src))); print(src, '→', dst)
    elif a.cmd == 'png':
        src, dst = a.src[0], a.src[1] if len(a.src) > 1 else a.dst
        t = crop(txt2arr(src)); arr2img(t, palette(a.id)).save(dst); print(src, '→', dst, t.shape[::-1])
    else:                                                       # 여러 장을 나란히 (사이 8칸, 아래 맞춤)
        ts = [txt2arr(p) if p.endswith('.txt') else png2arr(p) for p in a.src]
        H = max(t.shape[0] for t in ts); W = sum(t.shape[1] for t in ts) + 8 * (len(ts) + 1)
        big = -np.ones((H + 16, W), int); x = 8
        for t in ts:
            big[8 + H - t.shape[0]:8 + H, x:x + t.shape[1]] = t; x += t.shape[1] + 8
        arr2img(big, palette(a.id), a.scale, (232, 240, 232)).save(a.o); print('→', a.o)


if __name__ == '__main__':
    main()
