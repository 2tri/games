"""디지몬 세션 그리기 방식(DigiPix)을 게임보이 4단계로 옮긴 파이썬판.
부위를 뒤→앞 순서로 올리고, 부위마다 바깥 테두리에 검은 선(앞 부위 선이 뒤 부위 위에 얹힘),
안은 단색, 그늘은 테두리 띠 + 빗금, 반사광은 점. 톤 0 흰 1 밝은회 2 어두운회 3 검정, -1 비움."""
import numpy as np
K = 3
class Pic:
    def __init__(s, w, h): s.w, s.h = w, h; s.p = -np.ones((h, w), int)
    def px(s, x, y, c):
        if 0 <= x < s.w and 0 <= y < s.h: s.p[y, x] = c
def E(cx, cy, rx, ry): return lambda x, y: ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1
def R(x0, y0, w, h): return lambda x, y: x0 <= x < x0 + w and y0 <= y < y0 + h
def P(pts):
    def f(x, y):
        X, Y, ins = x + .5, y + .5, False
        for i in range(len(pts)):
            (xi, yi), (xj, yj) = pts[i], pts[i - 1]
            if (yi > Y) != (yj > Y) and X < (xj - xi) * (Y - yi) / (yj - yi) + xi: ins = not ins
        return ins
    return f
def L(x0, y0, x1, y1, r0, r1=None):
    r1 = r0 if r1 is None else r1; vx, vy = x1 - x0, y1 - y0; l2 = vx * vx + vy * vy or 1
    def f(x, y):
        X, Y = x + .5, y + .5; t = max(0, min(1, ((X - x0) * vx + (Y - y0) * vy) / l2))
        dx, dy, r = X - (x0 + t * vx), Y - (y0 + t * vy), r0 + (r1 - r0) * t; return dx * dx + dy * dy <= r * r
    return f
def C(pts):
    segs = [L(*pts[i - 1][:2], *pts[i][:2], pts[i - 1][2], pts[i][2]) for i in range(1, len(pts))]
    return lambda x, y: any(g(x, y) for g in segs)
def U(*fs): return lambda x, y: any(g(x, y) for g in fs)
def D(a, *bs): return lambda x, y: a(x, y) and not any(b(x, y) for b in bs)
def mask(s, f): return np.array([[bool(f(x, y)) for x in range(s.w)] for y in range(s.h)])
def _in(m, x, y): return 0 <= x < m.shape[1] and 0 <= y < m.shape[0] and m[y, x]
def part(s, f, col, line=True, shade=None, hi=None):
    m = mask(s, f) if callable(f) else f
    if line:
        for y in range(s.h):
            for x in range(s.w):
                if not m[y, x] and (_in(m, x + 1, y) or _in(m, x - 1, y) or _in(m, x, y + 1) or _in(m, x, y - 1)): s.p[y, x] = K
    s.p[m] = col
    if shade:
        dx, dy, c = shade
        for y in range(s.h):
            for x in range(s.w):
                if m[y, x] and not _in(m, x + dx, y + dy): s.p[y, x] = c
    if hi:
        dx, dy, c = hi
        for y in range(s.h):
            for x in range(s.w):
                if m[y, x] and not _in(m, x - dx, y - dy): s.p[y, x] = c
    return m
def hatch(s, m, dx, dy, period, direction, c=K):
    for y in range(s.h):
        for x in range(s.w):
            if not m[y, x] or _in(m, x + dx, y + dy): continue
            k = ((x - y) if direction == -1 else (x + y)) % period
            if k == 0: s.p[y, x] = c
def fill(s, f, c):
    for y in range(s.h):
        for x in range(s.w):
            if f(x, y): s.p[y, x] = c
def paint(s, f, c):
    for y in range(s.h):
        for x in range(s.w):
            if s.p[y, x] >= 0 and s.p[y, x] != K and f(x, y): s.p[y, x] = c
def dots(s, x0, y0, rows, mp=None):
    mp = mp or {}
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in '0123': s.px(x0 + i, y0 + j, int(ch))
            elif ch in mp: s.px(x0 + i, y0 + j, mp[ch])
