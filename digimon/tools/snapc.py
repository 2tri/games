#!/usr/bin/env python3
"""이미지 AI가 만든 '도트풍' 그림 → 금판(GBC)식 4색 도트 (흰색·밝은 색·어두운 색·검정)
반지 원정 tools/snap.py 의 칸 찾기 방식을 색 그림용으로 고친 것.
1) 도트 한 칸 크기·시작점 찾기(밝기 경계의 반복 주기) 2) 칸마다 가운데 색(중앙값)
3) 테두리에서 이어진 흰 배경 지우기 4) 검정·흰색을 빼고 나머지를 2색으로 묶기(k-평균)
5) 최대 크기 안으로 줄이기(검은 선 보존) 6) 작은 잡티 지우기
사용: python3 snapc.py 원본.png 결과이름 --max 56 [--line 0.28] [--k 2]
  → art/결과이름.png (실제 크기, 배경 투명), art/_결과이름_x6.png (확대 확인용)"""
import argparse, os
import numpy as np
from PIL import Image

def grid(g):
    res = []
    for axis in (1, 0):
        d = np.abs(np.diff(g, axis=axis)).sum(axis=1 - axis); d = d - d.mean(); n = len(d)
        F = np.abs(np.fft.rfft(d)); fr = np.fft.rfftfreq(n); m = (fr > 1 / 40) & (fr < 1 / 3)
        p = 1 / fr[np.argmax(F * m)]
        dd = np.abs(np.diff(g, axis=axis)).sum(axis=1 - axis)
        o = max(np.arange(0, p, 0.25), key=lambda o: sum(dd[int(round(o + k * p))] for k in range(int((n - o) / p)) if int(round(o + k * p)) < n))
        res.append((p, o))
    (pw, ox), (ph, oy) = res
    if max(pw, ph) / min(pw, ph) > 1.5:          # 한쪽이 잔무늬 때문에 절반으로 잡히면 큰 칸에 맞춤
        p = max(pw, ph); res = []
        for axis in (1, 0):
            dd = np.abs(np.diff(g, axis=axis)).sum(axis=1 - axis); n = len(dd)
            o = max(np.arange(0, p, 0.25), key=lambda o: sum(dd[int(round(o + k * p))] for k in range(int((n - o) / p)) if int(round(o + k * p)) < n))
            res.append((p, o))
    return res

def flood_bg(cells, tol):
    h, w, _ = cells.shape
    near = (cells.min(2) >= 255 - tol)
    bg = np.zeros((h, w), bool); st = [(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)]
    while st:
        y, x = st.pop()
        if y < 0 or x < 0 or y >= h or x >= w or bg[y, x] or not near[y, x]: continue
        bg[y, x] = True; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return bg

def lum(c): return c @ np.array([0.299, 0.587, 0.114])

def hue_gap(a, b):
    import colorsys
    ha = colorsys.rgb_to_hsv(*(a / 255))[0] * 360; hb = colorsys.rgb_to_hsv(*(b / 255))[0] * 360
    d = abs(ha - hb) % 360; return min(d, 360 - d)

def snap(img, tol=24, k=6, accent=True):
    rgb = np.asarray(img.convert('RGB')).astype(float)
    (pw, ox), (ph, oy) = grid(lum(rgb))
    nx, ny = int((rgb.shape[1] - ox) / pw), int((rgb.shape[0] - oy) / ph)
    cells = np.zeros((ny, nx, 3))
    for j in range(ny):
        for i in range(nx):
            x0, x1 = int(ox + i * pw + pw * .3), int(ox + (i + 1) * pw - pw * .3)
            y0, y1 = int(oy + j * ph + ph * .3), int(oy + (j + 1) * ph - ph * .3)
            cells[j, i] = np.median(rgb[y0:y1 + 1, x0:x1 + 1].reshape(-1, 3), 0)
    bg = flood_bg(cells, tol)
    L = lum(cells); sat = cells.max(2) - cells.min(2)
    black = (L < 58) & ~bg
    white = (L > 222) & (sat < 30) & ~bg
    rest = ~bg & ~black & ~white
    v = cells[rest]
    # 색 묶기: k개 무리로 나눈 뒤 칸 수가 가장 많은 2개를 몸 색으로 (눈 같은 작은 색은 가까운 색으로 흡수)
    idx = np.argsort(lum(v)); c = np.array([v[idx[int(len(v) * q)]] for q in np.linspace(.1, .9, k)])
    for _ in range(30):
        lab = np.argmin(((v[:, None] - c[None]) ** 2).sum(2), 1)
        c = np.array([v[lab == m].mean(0) if (lab == m).any() else c[m] for m in range(k)])
    cnt = np.bincount(lab, minlength=k).astype(float)
    groups = []                                                   # 거의 같은 색 무리는 합침
    for m in np.argsort(-cnt):
        if cnt[m] == 0: continue
        for gr in groups:
            if np.sqrt(((gr[0] - c[m]) ** 2).sum()) < 48: gr[0] = (gr[0] * gr[1] + c[m] * cnt[m]) / (gr[1] + cnt[m]); gr[1] += cnt[m]; break
        else: groups.append([c[m].copy(), cnt[m]])
    groups.sort(key=lambda gr: -gr[1])
    c = np.array([gr[0] for gr in groups[:2]])
    if len(c) < 2: c = np.array([c[0], c[0] * 0.68])               # 한 색뿐이면 어두운 쪽을 만들어 줌
    c = c[np.argsort(-lum(c))]                                    # 1 = 밝은 색, 2 = 어두운 색
    pal4 = [[248, 248, 248], c[0], c[1], [24, 24, 24]]
    if accent:                                                    # 눈처럼 색상이 확 다른 작은 색 하나는 5번째 색(4)으로 남김
        for gr in groups[2:]:
            if gr[1] >= 3 and gr[0].max() - gr[0].min() > 60 and min(hue_gap(gr[0], c[0]), hue_gap(gr[0], c[1])) > 50:
                pal4.append(gr[0]); break
    pal4 = np.array(pal4, float)
    t = -np.ones((ny, nx), int); t[white] = 0; t[black] = 3
    near = np.argmin(((cells[..., None, :] - pal4[None, None]) ** 2).sum(3), 2)
    t[rest] = near[rest]
    ys, xs = np.where(t >= 0); t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    pal = [tuple(int(x) for x in cc) for cc in pal4]; pal[0] = (248, 248, 248); pal[3] = (24, 24, 24)
    return t, pal, (pw, ph)

def shrink(t, maxw, maxh, line_bias=0.28):
    h, w = t.shape; k = min(1.0, maxw / w, maxh / h)
    if k >= 1: return t
    th, tw = max(1, round(h * k)), max(1, round(w * k)); out = -np.ones((th, tw), int)
    for j in range(th):
        for i in range(tw):
            y0, y1 = int(j / k), max(int(j / k) + 1, int((j + 1) / k)); x0, x1 = int(i / k), max(int(i / k) + 1, int((i + 1) / k))
            b = t[y0:y1, x0:x1].ravel(); fg = b[b >= 0]
            if len(fg) < 0.5 * len(b): continue
            if (fg == 3).mean() >= line_bias: out[j, i] = 3
            else: vals, cnt = np.unique(fg, return_counts=True); out[j, i] = vals[np.argmax(cnt)]
    return out

def shrink2(t, maxw, maxh, line_in=0.42, ss=4):
    """줄이기: 새 칸마다 원래 칸을 ss×ss 점으로 찍어 다수결 (검정은 line_in 넘을 때만).
    바깥 테두리는 1칸 검은 선으로 다시 그림 (금판 그림처럼)."""
    h, w = t.shape; k = min(1.0, maxw / w, maxh / h)
    if k >= 1: return t
    th, tw = max(1, round(h * k)), max(1, round(w * k)); out = -np.ones((th, tw), int)
    for j in range(th):
        for i in range(tw):
            ys = np.clip(((j + (np.arange(ss) + .5) / ss) / k).astype(int), 0, h - 1)
            xs = np.clip(((i + (np.arange(ss) + .5) / ss) / k).astype(int), 0, w - 1)
            b = t[np.ix_(ys, xs)].ravel(); fg = b[b >= 0]
            if len(fg) < 0.5 * len(b): continue
            if (fg == 3).mean() >= line_in or not (fg != 3).any(): out[j, i] = 3
            else: vals, cnt = np.unique(fg[fg != 3], return_counts=True); out[j, i] = vals[np.argmax(cnt)]
    m = out >= 0; p = np.pad(m, 1)
    out[m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])] = 3
    return out

def drop_small(t, min_cells=8):
    h, w = t.shape; seen = np.zeros_like(t, bool); out = t.copy()
    for y in range(h):
        for x in range(w):
            if t[y, x] < 0 or seen[y, x]: continue
            st = [(y, x)]; comp = []; seen[y, x] = True
            while st:
                a, b = st.pop(); comp.append((a, b))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    Y, X = a + dy, b + dx
                    if 0 <= Y < h and 0 <= X < w and not seen[Y, X] and t[Y, X] >= 0: seen[Y, X] = True; st.append((Y, X))
            if len(comp) < min_cells:
                for a, b in comp: out[a, b] = -1
    ys, xs = np.where(out >= 0); return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def to_image(t, pal, scale=1, bg=None):
    h, w = t.shape; a = np.zeros((h, w, 4), np.uint8)
    for i, c in enumerate(pal): a[t == i] = (*c, 255)          # 0 흰 1 밝은 색 2 어두운 색 3 검정 4 강조색
    if bg: a[t < 0] = (*bg, 255)
    im = Image.fromarray(a, 'RGBA')
    return im.resize((w * scale, h * scale), Image.NEAREST) if scale > 1 else im

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('name')
    ap.add_argument('--max', type=int, default=56); ap.add_argument('--line', type=float, default=0.42); ap.add_argument('--mode', type=int, default=2, help='줄이기 1=반지 원정식 2=테두리 다시 그리기'); ap.add_argument('--k', type=int, default=6, help='처음 나눌 색 무리 수 (그중 큰 2개를 씀)')
    a = ap.parse_args()
    t, pal, cell = snap(Image.open(a.src), k=a.k)
    t = drop_small(t, 8)
    t = shrink2(t, a.max, a.max, a.line) if a.mode == 2 else shrink(t, a.max, a.max, a.line)
    t = drop_small(t, 3)
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'art')
    to_image(t, pal).save(os.path.join(here, a.name + '.png'))
    to_image(t, pal, 6, (248, 248, 248)).save(os.path.join(here, '_' + a.name + '_x6.png'))
    print('칸', tuple(round(x, 2) for x in cell), '→ 도트', t.shape[::-1], '색', pal)
