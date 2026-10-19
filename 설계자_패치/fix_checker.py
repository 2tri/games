#!/usr/bin/env python3
"""제미나이가 그림에 박아 넣은 체크무늬(투명 표시) 배경을 지운 투명 PNG 를 만든다. (Claude 작성, 2026-10-15)
사용:   python fix_checker.py <입력.png> [<입력2.png> …] --out 그림_보충
방법:   가장자리에서 시작해 「밝고 채도 낮은 색」(체크무늬의 두 가지 회색·흰색)으로 이어진 칸을 투명으로(4방향). 안쪽의 흰 눈·붕대는 윤곽선에 막혀 남음.
        가장자리 한 줄이 이미 투명이면 그대로 둠. 같은 이름으로 저장하므로 art_nds 에 이 폴더를 앞에 두면 먼저 읽힘."""
import sys, os, argparse
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--out', default='그림_보충'); ap.add_argument('--lo', type=int, default=185)
A = ap.parse_args()
os.makedirs(A.out, exist_ok=True)
for f in A.files:
    im = Image.open(f).convert('RGBA'); w, h = im.size; px = im.load()
    def bg(p): return p[3] > 0 and min(p[:3]) >= A.lo and max(p[:3]) - min(p[:3]) <= 28
    seen = bytearray(w * h); st = []
    for x in range(w):
        st += [(x, 0), (x, h - 1)]
    for y in range(h):
        st += [(0, y), (w - 1, y)]
    n = 0
    while st:
        x, y = st.pop()
        i = y * w + x
        if seen[i] or not bg(px[x, y]): continue
        seen[i] = 1; px[x, y] = (0, 0, 0, 0); n += 1
        if x > 0: st.append((x - 1, y))
        if x < w - 1: st.append((x + 1, y))
        if y > 0: st.append((x, y - 1))
        if y < h - 1: st.append((x, y + 1))
    # 남은 가장자리 부스러기(밝은 한두 칸짜리 점) 지우기: 투명 칸에 둘러싸인 밝은 점
    px2 = im.load(); cnt = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            p = px2[x, y]
            if p[3] and min(p[:3]) >= A.lo and max(p[:3]) - min(p[:3]) <= 28:
                nb = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if px2[x + dx, y + dy][3] == 0)
                if nb >= 3: px2[x, y] = (0, 0, 0, 0); cnt += 1
    out = os.path.join(A.out, os.path.basename(f)); im.save(out)
    print('%s: 지운 칸 %d + 점 %d → %s' % (os.path.basename(f), n, cnt, out))
