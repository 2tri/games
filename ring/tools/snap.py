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

def snap(img, cell=None, size=56, tol=14):
    rgb = np.asarray(img.convert('RGB')).astype(float); g = rgb @ [0.299, 0.587, 0.114]
    bg = flood_bg(g.astype(np.uint8), True, tol)
    if bg.mean() < 0.05: bg = flood_bg(g.astype(np.uint8), False, tol)
    ys, xs = np.where(~bg); g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; bg = bg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    if cell is None: cell, ox, oy = est_cell(g)
    else: ox = oy = 0
    H, W = (g.shape[0] - oy) // cell, (g.shape[1] - ox) // cell
    G = g[oy:oy + H * cell, ox:ox + W * cell].reshape(H, cell, W, cell)
    B = bg[oy:oy + H * cell, ox:ox + W * cell].reshape(H, cell, W, cell)
    m = 1 - B.mean(axis=(1, 3)) > 0.5
    v = np.median(G.reshape(H, cell, W, cell).transpose(0, 2, 1, 3).reshape(H, W, -1), axis=2)
    # 4단계 k-평균 (밝기)
    vals = v[m]; c = np.percentile(vals, [5, 35, 65, 95])
    for _ in range(20):
        lab = np.argmin(np.abs(vals[:, None] - c[None]), 1)
        c = np.array([vals[lab == k].mean() if (lab == k).any() else c[k] for k in range(4)])
    order = np.argsort(-c)   # 밝은 것 → 톤 0
    tone_of = {int(k): i for i, k in enumerate(order)}
    lab_all = np.argmin(np.abs(v[..., None] - c[None, None]), 2)
    t = np.vectorize(lambda k: tone_of[int(k)])(lab_all); t = np.where(m, t, -1)
    if max(t.shape) > size:  # 너무 크면 최근접 축소
        k = size / max(t.shape); idx_y = (np.arange(int(t.shape[0] * k)) / k).astype(int); idx_x = (np.arange(int(t.shape[1] * k)) / k).astype(int)
        t = t[idx_y][:, idx_x]
    out = -np.ones((size, size), int); oy2 = size - t.shape[0]; ox2 = (size - t.shape[1]) // 2
    out[oy2:, ox2:ox2 + t.shape[1]] = t
    return out, cell

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--cell', type=int); ap.add_argument('--size', type=int, default=56); ap.add_argument('--scale', type=int, default=6)
    a = ap.parse_args()
    t, c = snap(Image.open(a.src), a.cell, a.size)
    to_image(t, a.scale, bg=(248, 248, 240)).save(a.dst); np.save(a.dst.rsplit('.', 1)[0] + '.npy', t)
    print('칸 크기', c, '→', a.dst)
