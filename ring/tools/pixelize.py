#!/usr/bin/env python3
"""원화 → 게임보이 4단계 도트 변환기 (「반지 원정」)
사용: python3 pixelize.py 원화.png 결과.png --size 56 [--box x0,y0,x1,y1] [--bg white|black|none] [--gamma 1.0] [--dither 0.5]
1) 배경 제거(테두리에서 이어진 흰/검은 배경) 2) 대상만 잘라 size×size 안에 맞춰 축소(면적 평균)
3) 밝기를 4단계(흰·밝은회·어두운회·검정)로, 단계 사이는 2×2 바둑판 점묘 4) 1픽셀 검은 외곽선 5) 외톨이 점 정리
"""
import argparse
import numpy as np
from PIL import Image

GB = np.array([[248, 248, 240], [176, 176, 168], [96, 96, 96], [24, 24, 24]], dtype=np.uint8)
BAYER = np.array([[0.25, 0.75], [1.0, 0.5]])


def flood_bg(gray, light=True, tol=28):
    h, w = gray.shape
    ref = 255 if light else 0
    near = np.abs(gray.astype(int) - ref) <= tol
    bg = np.zeros_like(near)
    stack = [(y, x) for x in range(w) for y in (0, h - 1)] + [(y, x) for y in range(h) for x in (0, w - 1)]
    while stack:
        y, x = stack.pop()
        if y < 0 or x < 0 or y >= h or x >= w or bg[y, x] or not near[y, x]:
            continue
        bg[y, x] = True
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return bg


def pixelize(img, size=56, bg='white', gamma=1.0, dither=0.5, outline=True, lo=2, hi=98, tol=12, edges=0.0):
    rgb = img.convert('RGB')
    gray = np.asarray(rgb.convert('L'))
    if bg == 'none':
        mask = np.ones_like(gray, dtype=bool)
    else:
        # 큰 그림은 줄여서 배경 판정 (속도)
        k = max(1, max(gray.shape) // 600)
        small = gray[::k, ::k]
        bgm = flood_bg(small, light=(bg == 'white'), tol=tol)
        mask = ~np.asarray(Image.fromarray(bgm.astype(np.uint8) * 255).resize(gray.shape[::-1], Image.NEAREST)).astype(bool)
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    g = gray[y0:y1, x0:x1].astype(float) / 255
    m = mask[y0:y1, x0:x1].astype(float)
    hgt, wid = g.shape
    sc = (size - 2) / max(hgt, wid)
    tw, th = max(1, round(wid * sc)), max(1, round(hgt * sc))
    gi = np.asarray(Image.fromarray((g * m * 255 + (1 - m) * 255).astype(np.uint8)).resize((tw, th), Image.BOX)).astype(float) / 255
    mi = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((tw, th), Image.BOX)).astype(float) / 255
    alpha = mi > 0.45
    # 안쪽 윤곽선: 4배 해상도에서 밝기 경사를 구해 칸마다 최댓값 → 강한 곳은 검은 선
    edge = np.zeros((th, tw))
    if edges > 0:
        g4 = np.asarray(Image.fromarray((g * m * 255 + (1 - m) * 255).astype(np.uint8)).resize((tw * 4, th * 4), Image.BOX)).astype(float) / 255
        gx = np.zeros_like(g4); gy = np.zeros_like(g4)
        gx[:, 1:-1] = g4[:, 2:] - g4[:, :-2]; gy[1:-1, :] = g4[2:, :] - g4[:-2, :]
        mag = np.hypot(gx, gy)
        edge = mag.reshape(th, 4, tw, 4).max(axis=(1, 3))
    # 대비 늘리기 (대상 안쪽 밝기 분포 기준)
    vals = gi[alpha]
    a, b = np.percentile(vals, lo), np.percentile(vals, hi)
    v = np.clip((gi - a) / max(1e-3, b - a), 0, 1) ** gamma
    # 0(검정)~1(흰) → 톤 3..0, 사이 점묘
    t = (1 - v) * 3
    base = np.floor(t)
    frac = t - base
    yy, xx = np.mgrid[0:th, 0:tw]
    thr = 0.5 + (BAYER[yy % 2, xx % 2] - 0.625) * dither * 1.6
    tone = np.clip(base + (frac > thr), 0, 3).astype(int)
    if edges > 0:
        tone = np.where((edge > edges) & alpha, 3, tone)
    out = -np.ones((size, size), int)
    oy, ox = (size - th) // 2, (size - tw) // 2
    if size - th > 2:
        oy = size - th - 1   # 바닥에 붙이기
    sub = np.where(alpha, tone, -1)
    out[oy:oy + th, ox:ox + tw] = sub
    # 외톨이 점 정리
    o2 = out.copy()
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            c = out[y, x]
            if c < 0:
                continue
            nb = [out[y + 1, x], out[y - 1, x], out[y, x + 1], out[y, x - 1]]
            if all(n != c for n in nb) and nb.count(nb[0]) >= 3 and nb[0] >= 0:
                o2[y, x] = nb[0]
    out = o2
    if outline:
        o3 = out.copy()
        for y in range(size):
            for x in range(size):
                if out[y, x] >= 0:
                    continue
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    Y, X = y + dy, x + dx
                    if 0 <= Y < size and 0 <= X < size and out[Y, X] >= 0:
                        o3[y, x] = 3
                        break
        out = o3
    return out


def to_image(tones, scale=1, bg=None):
    h, w = tones.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    for t in range(4):
        rgba[tones == t, :3] = GB[t]
        rgba[tones == t, 3] = 255
    if bg is not None:
        rgba[tones < 0] = list(bg) + [255]
    im = Image.fromarray(rgba, 'RGBA')
    return im.resize((w * scale, h * scale), Image.NEAREST) if scale > 1 else im


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--size', type=int, default=56)
    ap.add_argument('--box', default=None)
    ap.add_argument('--bg', default='white')
    ap.add_argument('--gamma', type=float, default=1.0)
    ap.add_argument('--dither', type=float, default=0.5)
    ap.add_argument('--scale', type=int, default=1)
    ap.add_argument('--tol', type=int, default=12)
    ap.add_argument('--edges', type=float, default=0.0)
    ap.add_argument('--hi', type=float, default=98)
    ap.add_argument('--lo', type=float, default=2)
    a = ap.parse_args()
    im = Image.open(a.src)
    if a.box:
        im = im.crop(tuple(int(v) for v in a.box.split(',')))
    t = pixelize(im, a.size, a.bg, a.gamma, a.dither, tol=a.tol, edges=a.edges, lo=a.lo, hi=a.hi)
    to_image(t, a.scale, bg=(248, 248, 240)).save(a.dst)
    print('saved', a.dst)
