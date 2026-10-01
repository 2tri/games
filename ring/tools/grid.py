#!/usr/bin/env python3
"""참고 사진 위에 N×N 칸 격자를 겹쳐 보여 줌 (좌표 읽기용). 사용: grid.py 사진 결과.png --size 56 [--box x0,y0,x1,y1] [--scale 12]"""
import argparse
from PIL import Image, ImageDraw
from pixelize import flood_bg
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--size', type=int, default=56)
ap.add_argument('--box'); ap.add_argument('--scale', type=int, default=12); ap.add_argument('--pad', type=int, default=1)
a = ap.parse_args()
im = Image.open(a.src).convert('RGB')
if a.box: im = im.crop(tuple(int(v) for v in a.box.split(',')))
else:
    bg = flood_bg(np.asarray(im.convert('L')), True, 10); ys, xs = np.where(~bg)
    im = im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
N, S = a.size, a.scale; inner = N - 2 * a.pad
k = inner / max(im.size); w, h = round(im.width * k), round(im.height * k)
can = Image.new('RGB', (N * S, N * S), 'white')
can.paste(im.resize((w * S, h * S), Image.LANCZOS), (((N - w) // 2) * S, (N - a.pad - h) * S))
d = ImageDraw.Draw(can)
for i in range(N + 1):
    c = (255, 0, 0) if i % 8 == 0 else (0, 160, 255) if i % 4 == 0 else (200, 200, 200)
    d.line([(i * S, 0), (i * S, N * S)], fill=c, width=1); d.line([(0, i * S), (N * S, i * S)], fill=c, width=1)
    if i % 4 == 0 and i < N:
        d.text((i * S + 2, 1), str(i), fill=(255, 0, 0)); d.text((1, i * S + 2), str(i), fill=(255, 0, 0))
can.save(a.dst); print(a.dst, (w, h))
