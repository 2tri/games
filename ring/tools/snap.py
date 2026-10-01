#!/usr/bin/env python3
"""'도트풍' 그림(이미지 AI가 만든 픽셀아트, 확대된 도트 캡처 등)을 진짜 도트 칸에 맞춰 정리.
1) 배경 제거 2) 한 칸 크기 자동 추정(칸 안 색 분산이 가장 작은 크기) 3) 칸마다 가운데 색(중앙값)
4) 밝기로 게임보이 4단계 묶기(k-평균) 5) 원하는 크기(예: 56) 칸 안에 바닥 맞춰 앉히기
사용: python3 snap.py 그림.png 결과.png [--cell 자동] [--size 56] [--scale 6]"""
import argparse
import numpy as np
from PIL import Image
from pixelize import flood_bg, to_image

def est_cell(g, lo=3, hi=24):
    best = None
    for c in range(lo, hi + 1):
        h, w = (g.shape[0] // c) * c, (g.shape[1] // c) * c
        if h < c * 8 or w < c * 8: break
        for ox in range(0, c, max(1, c // 4)):
            for oy in range(0, c, max(1, c // 4)):
                b = g[oy:oy + h - c, ox:ox + w - c]
                hh, ww = (b.shape[0] // c) * c, (b.shape[1] // c) * c
                blk = b[:hh, :ww].reshape(hh // c, c, ww // c, c)
                v = blk.var(axis=(1, 3)).mean() + 0.02 * c   # 큰 칸에 약간 벌점
                if best is None or v < best[0]: best = (v, c, ox, oy)
    return best[1:]

def grid(g):
    """도트 칸 크기(소수 허용)와 시작 위치: 밝기 경계의 반복 주기(FFT)로 찾음"""
    res = []
    for axis in (1, 0):
        d = np.abs(np.diff(g, axis=axis)).sum(axis=1 - axis); d = d - d.mean(); n = len(d)
        F = np.abs(np.fft.rfft(d)); fr = np.fft.rfftfreq(n); m = (fr > 1 / 40) & (fr < 1 / 3)
        p = 1 / fr[np.argmax(F * m)]
        dd = np.abs(np.diff(g, axis=axis)).sum(axis=1 - axis)
        o = max(np.arange(0, p, 0.25), key=lambda o: sum(dd[int(round(o + k * p))] for k in range(int((n - o) / p)) if int(round(o + k * p)) < n))
        res.append((p, o))
    return res  # [(칸폭, x시작), (칸높이, y시작)]

def snap(img, size=None, tol=20):
    g = np.asarray(img.convert('L')).astype(float)
    (pw, ox), (ph, oy) = grid(g)
    nx, ny = int((g.shape[1] - ox) / pw), int((g.shape[0] - oy) / ph)
    cells = np.zeros((ny, nx))
    for j in range(ny):
        for i in range(nx):
            x0, x1 = int(ox + i * pw + pw * .3), int(ox + (i + 1) * pw - pw * .3)
            y0, y1 = int(oy + j * ph + ph * .3), int(oy + (j + 1) * ph - ph * .3)
            cells[j, i] = np.median(g[y0:y1 + 1, x0:x1 + 1])
    bg = flood_bg(cells.astype(np.uint8), True, tol)
    v = cells[~bg]; c = np.percentile(v, [5, 35, 65, 95])
    for _ in range(20):
        lab = np.argmin(np.abs(v[:, None] - c[None]), 1)
        c = np.array([v[lab == k].mean() if (lab == k).any() else c[k] for k in range(4)])
    c = np.sort(c)[::-1]
    t = np.argmin(np.abs(cells[..., None] - c[None, None]), 2); t = np.where(bg, -1, t)
    ys, xs = np.where(t >= 0); t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return t, (pw, ph)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--scale', type=int, default=6); ap.add_argument('--crop', type=int, help='아래를 잘라 이 높이로')
    a = ap.parse_args()
    t, c = snap(Image.open(a.src))
    if a.crop and t.shape[0] > a.crop:
        t = t[:a.crop].copy(); t[-1] = np.where(t[-1] >= 0, 3, -1)
    to_image(t, a.scale, bg=(248, 248, 240)).save(a.dst); np.save(a.dst.rsplit('.', 1)[0] + '.npy', t)
    print('칸 크기', c, '도트', t.shape, '→', a.dst)

def shrink(t, maxw, maxh, line_bias=0.28):
    """도트 그림 줄이기: 칸 덩어리마다 검정 비율이 line_bias 넘으면 검정(선 보존), 아니면 다수결"""
    h, w = t.shape; k = min(1.0, maxw / w, maxh / h)
    if k >= 1: return t
    th, tw = max(1, round(h * k)), max(1, round(w * k))
    out = -np.ones((th, tw), int)
    for j in range(th):
        for i in range(tw):
            y0, y1 = int(j / k), max(int(j / k) + 1, int((j + 1) / k)); x0, x1 = int(i / k), max(int(i / k) + 1, int((i + 1) / k))
            b = t[y0:y1, x0:x1].ravel(); fg = b[b >= 0]
            if len(fg) < 0.5 * len(b): continue
            if (fg == 3).mean() >= line_bias: out[j, i] = 3
            else:
                vals, cnt = np.unique(fg, return_counts=True); out[j, i] = vals[np.argmax(cnt)]
    return out
