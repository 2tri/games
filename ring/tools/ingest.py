#!/usr/bin/env python3
"""이미지 AI 그림 → 게임 도트 한 번에: 칸 맞춤 → 잡티 제거 → 크기 맞춤 → ai/<이름>.npy, sprites.js 갱신
사용: python3 ingest.py 이름 원본.png 최대가로 최대세로 [선우선=0.28] [아래자르기칸=0]"""
import sys, json
import numpy as np
from PIL import Image
from snap import snap, shrink

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

def ingest(name, src, mw, mh, lb=0.28, crop=0):
    t, c = snap(Image.open(src)); t = drop_small(t, 10)
    if crop and t.shape[0] > crop: t = t[:crop].copy(); t[-1] = np.where(t[-1] >= 0, 3, -1)
    f = shrink(t, mw, mh, line_bias=lb)
    np.save(f'../ai/{name}.npy', f)
    js = '../ai/sprites.js'; d = json.loads(open(js).read()[len('window.AISPR='):-1]); d[name] = f.tolist()
    open(js, 'w').write('window.AISPR=' + json.dumps(d, separators=(',', ':')) + ';')
    print(name, '칸', [round(float(v), 1) for v in c], t.shape, '->', f.shape)
    return f

if __name__ == '__main__':
    a = sys.argv[1:]
    ingest(a[0], a[1], int(a[2]), int(a[3]), float(a[4]) if len(a) > 4 else 0.28, int(a[5]) if len(a) > 5 else 0)
