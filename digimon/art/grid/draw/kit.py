"""도형으로 4톤 초안 그리기 (값: -1 배경, 0 흰, 1 밝은, 2 어두운, 3 검정)"""
import numpy as np
from PIL import Image, ImageDraw
import sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import grid


class C:
    def __init__(s, w, h):
        s.w, s.h = w, h; s.t = -np.ones((h, w), int)

    def _mask(s, fn):
        im = Image.new('L', (s.w, s.h), 0); fn(ImageDraw.Draw(im)); return np.asarray(im) > 0

    def ell(s, x0, y0, x1, y1, v=1):
        m = s._mask(lambda d: d.ellipse((x0, y0, x1, y1), fill=1)); s.t[m] = v; return m

    def poly(s, pts, v=1):
        m = s._mask(lambda d: d.polygon(pts, fill=1)); s.t[m] = v; return m

    def rect(s, x0, y0, x1, y1, v=1):
        s.t[y0:y1 + 1, x0:x1 + 1] = v

    def line(s, pts, v=3, w=1):
        m = s._mask(lambda d: d.line(pts, fill=1, width=w)); s.t[m] = v; return m

    def px(s, pts, v):
        for x, y in pts: s.t[y, x] = v

    def body(s): return s.t >= 0

    def shade(s, d=3, v=2, only=(1,), side=2):
        """오른쪽·아래 가장자리 띠를 어두운 톤으로 (빛은 왼쪽 위). side: 오른쪽 띠 두께, d: 대각·아래 띠 두께"""
        b = s.body(); out = s.t.copy()
        offs = [(k, k) for k in range(1, d + 1)] + [(k, 0) for k in range(1, side + 1)] + [(0, k) for k in range(1, d)]
        for y in range(s.h):
            for x in range(s.w):
                if s.t[y, x] in only:
                    for dx, dy in offs:
                        X, Y = x + dx, y + dy
                        if not (0 <= X < s.w and 0 <= Y < s.h) or not b[Y, X]: out[y, x] = v; break
        s.t = out

    def outline(s):
        b = s.body(); p = np.pad(b, 1)
        e = b & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]); s.t[e] = 3

    def txt(s): return grid.arr2txt(s.t)

    def save(s, path): open(path, 'w').write(s.txt())
