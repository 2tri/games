"""17판: DS 도트 그림(위키몬 디지몬 스토리 전투 그림) → GBC 4색 그림. ingest(AI 그림의 큰 도트 격자 찾기)와 달리 도트를 그대로 줄여 4톤으로 나눈다.
python3 ds_convert.py 원본.png 결과.png 최대크기 [--pal R,G,B R,G,B]
규칙: 배경(투명 또는 모서리 색) → 투명 / 아주 어두운 선 → 검정 / 아주 밝은 곳 → 흰색 / 나머지 몸은 색 2개로(k-means 2) → 밝은 색·어두운 색.
결과 png 는 patch.png_to_idx 가 읽는 꼴(투명 바탕, 흰·몸색 2·검정)."""
import sys
import numpy as np
from PIL import Image


def load(src):
    im = Image.open(src).convert('RGBA')
    a = np.asarray(im).astype(int)
    if (a[..., 3] < 128).sum() == 0:      # 알파 없음 → 모서리 색을 배경으로
        bg = np.median(np.concatenate([a[0, :, :3], a[-1, :, :3], a[:, 0, :3], a[:, -1, :3]]), axis=0)
        far = np.abs(a[..., :3] - bg).sum(2) > 48
        a[..., 3] = np.where(far, 255, 0)
    return a


def crop(a):
    op = a[..., 3] >= 128
    ys, xs = np.where(op)
    if len(ys) == 0: raise ValueError('그림이 비었음')
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def fit(a, maxs):
    h, w = a.shape[:2]
    s = min(maxs / w, maxs / h)
    if s >= 1: return a      # 작으면 그대로 (키우지 않음)
    im = Image.fromarray(a.astype(np.uint8), 'RGBA')
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    rgb = im.convert('RGB').resize((nw, nh), Image.LANCZOS)
    al = im.getchannel('A').resize((nw, nh), Image.LANCZOS)
    out = np.dstack([np.asarray(rgb).astype(int), np.asarray(al).astype(int)])
    return out


def tones(a, pal=None):
    op = a[..., 3] >= 128
    rgb = a[..., :3]
    L = rgb @ np.array([.299, .587, .114])
    sat = rgb.max(2) - rgb.min(2)
    t = np.full(a.shape[:2], -1, int)
    black = op & (L < 70)
    white = op & (L > 228) & (sat < 40)
    body = op & ~black & ~white
    t[black] = 3
    t[white] = 0
    if pal is None:
        px = rgb[body]
        if len(px) < 2:
            pal = [(200, 200, 200), (120, 120, 120)]
        else:      # k-means 2 (밝기 기준으로 시작)
            lb = L[body]
            hi = lb >= np.median(lb)
            lo = ~hi
            if not lo.any(): lo = hi
            c = np.array([px[hi].mean(0), px[lo].mean(0)])
            for _ in range(12):
                d = ((px[:, None, :] - c[None]) ** 2).sum(2)
                k = d.argmin(1)
                for i in range(2):
                    if (k == i).any(): c[i] = px[k == i].mean(0)
            pal = [tuple(int(v) for v in c[0]), tuple(int(v) for v in c[1])]
    if pal[0][0] * .299 + pal[0][1] * .587 + pal[0][2] * .114 < pal[1][0] * .299 + pal[1][1] * .587 + pal[1][2] * .114:
        pal = pal[::-1]
    c = np.array(pal, float)
    if body.any():
        px = rgb[body]
        d = ((px[:, None, :] - c[None]) ** 2).sum(2)
        t[body] = 1 + d.argmin(1)
    # 몸색이 흰·검정으로 읽히지 않게 (png_to_idx: min>230 → 흰, max<60 → 검정)
    pal = [tuple(max(v, 0) for v in p) for p in pal]
    pal = [p if min(p) <= 230 else tuple(v - (min(p) - 230) for v in p) for p in pal]
    pal = [p if max(p) >= 60 else tuple(v + (60 - max(p)) for v in p) for p in pal]
    return t, pal


def to_png(t, pal, dst):
    h, w = t.shape
    out = np.zeros((h, w, 4), np.uint8)
    cols = {0: (248, 248, 248, 255), 1: tuple(pal[0]) + (255,), 2: tuple(pal[1]) + (255,), 3: (0, 0, 0, 255)}
    for k, col in cols.items(): out[t == k] = col
    Image.fromarray(out, 'RGBA').save(dst)


def convert(src, dst, maxs, pal=None):
    a = fit(crop(load(src)), maxs)
    t, pal = tones(a, pal)
    to_png(t, pal, dst)
    return t.shape[::-1], pal


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    pal = None
    if '--pal' in sys.argv:
        i = sys.argv.index('--pal')
        pal = [tuple(int(v) for v in x.split(',')) for x in sys.argv[i + 1:i + 3]]
        args = [x for x in args if ',' not in x]
    size, pal = convert(args[0], args[1], int(args[2]), pal)
    print(args[1], size, pal)
