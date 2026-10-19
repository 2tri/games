#!/usr/bin/env python3
"""제미나이로 받은 걷기 그림을 게임용 2x2 시트로 합친다. 입력은 <id>-grid.png(2x2 한 장, 구분선이 있어도 됨) 또는 <id>-a.png + <id>-b.png. (Claude 작성, 2026-10-16)
사용:   python 걷기_합치기.py [받은그림 폴더=걷기_받은그림] [내보낼 폴더=games/digimon/art/src]
받은 그림 이름:  <영문id>-a.png = 앞모습·뒷모습 두 마리가 나란히(한 줄) / <영문id>-b.png = 왼쪽 옆모습 한 마리(정확한 90도 옆모습)
                 (옆모습을 잘못 받으면 <영문id>-b.png 만 다시 받아 덮어쓰면 됨)
결과:   <영문id>-ow.png = 2x2 시트(왼쪽 위 앞 · 오른쪽 위 뒤 · 왼쪽 아래 왼쪽 옆 · 오른쪽 아래 오른쪽 옆 = 왼쪽 옆을 좌우 뒤집음), 배경 투명
방법:   모서리 색(회색)과 비슷하고 가장자리에 이어진 칸을 배경으로 지우고, 덩어리(불투명 칸이 이어진 것)로 몸을 찾음. 가까운 덩어리는 한 마리로 합침.
        -a 에서 덩어리가 둘이 아니거나 -b 에서 하나가 아니면 그 종은 건너뛰고 이유를 적음(다시 받기)."""
import sys, os, glob
from PIL import Image, ImageOps
src = sys.argv[1] if len(sys.argv) > 1 else '걷기_받은그림'; dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join('games', 'digimon', 'art', 'src')
os.makedirs(dst, exist_ok=True)

def cut_bg(im):
    im = im.convert('RGBA'); w, h = im.size; px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg = min(corners, key=lambda c: sum(c[:3]))      # 가장 어두운 모서리 = 회색 바탕(오른쪽 아래 반짝이 피하기)
    bg = sorted(corners, key=lambda c: sum(c[:3]))[len(corners) // 2]
    near = lambda p: p[3] < 20 or sum((a - b) ** 2 for a, b in zip(p[:3], bg[:3])) < 34 ** 2 or (max(p[:3]) - min(p[:3]) < 12 and abs(sum(p[:3]) / 3 - sum(bg[:3]) / 3) < 26)
    seen = bytearray(w * h); st = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while st:
        x, y = st.pop(); i = y * w + x
        if seen[i] or not near(px[x, y]): continue
        seen[i] = 1; px[x, y] = (0, 0, 0, 0)
        if x > 0: st.append((x - 1, y))
        if x < w - 1: st.append((x + 1, y))
        if y > 0: st.append((x, y - 1))
        if y < h - 1: st.append((x, y + 1))
    return im

def bodies(im, min_frac=0.0015):
    w, h = im.size; a = im.getchannel('A').load(); seen = bytearray(w * h); out = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or a[x0, y0] < 128: continue
            st = [(x0, y0)]; seen[y0 * w + x0] = 1; xs = [x0, x0]; ys = [y0, y0]; n = 0
            while st:
                x, y = st.pop(); n += 1
                xs[0] = min(xs[0], x); xs[1] = max(xs[1], x); ys[0] = min(ys[0], y); ys[1] = max(ys[1], y)
                for dx in (-2, -1, 0, 1, 2):
                    for dy in (-2, -1, 0, 1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and a[nx, ny] >= 128: seen[ny * w + nx] = 1; st.append((nx, ny))
            out.append([xs[0], ys[0], xs[1] + 1, ys[1] + 1, n])
    big = max((b[4] for b in out), default=0)
    out = [b for b in out if b[4] >= big * 0.04 and b[4] >= w * h * min_frac]
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a_, b_ = out[i], out[j]
                gap_x = max(a_[0] - b_[2], b_[0] - a_[2]); gap_y = max(a_[1] - b_[3], b_[1] - a_[3])
                # 한 몸의 떨어진 조각(손·꼬리·불꽃): 가로로 아주 가까우면 합침. 앞·뒤처럼 나란한 두 마리는 사이가 넓음
                if gap_x < max(w, h) * 0.015 and gap_y < max(w, h) * 0.05:
                    out[i] = [min(a_[0], b_[0]), min(a_[1], b_[1]), max(a_[2], b_[2]), max(a_[3], b_[3]), a_[4] + b_[4]]; out.pop(j); merged = True; break
            if merged: break
    return out

def sheet_from(f, k, s, out_path, name):
    if abs(s.height - f.height) > f.height * 0.15: s = s.resize((max(1, round(s.width * f.height / s.height)), f.height), Image.NEAREST)
    cw = max(f.width, k.width, s.width) + 8; ch = max(f.height, k.height, s.height) + 8
    sheet = Image.new('RGBA', (cw * 2, ch * 2), (0, 0, 0, 0))
    def put(im, cx, cy): sheet.alpha_composite(im, (cx * cw + (cw - im.width) // 2, cy * ch + ch - 4 - im.height))
    put(f, 0, 0); put(k, 1, 0); put(s, 0, 1); put(ImageOps.mirror(s), 1, 1)
    sheet.save(out_path); print('%s: 합침 → %s-ow.png (칸 %dx%d)' % (name, name, cw, ch))

# 2x2 한 장짜리(<영문id>-grid.png): 네 등분해서 칸 가장자리(구분선)를 잘라내고 칸마다 가장 큰 몸 하나만 씀. 왼쪽 아래 = 왼쪽 옆모습(오른쪽 아래는 무시하고 왼쪽 옆을 뒤집어 씀)
okg = 0
for pg in sorted(glob.glob(os.path.join(src, '*-grid.png'))):
    i = os.path.basename(pg)[:-9]; G = Image.open(pg).convert('RGBA'); w, h = G.size; cells = []
    for (cx, cy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        m = int(min(w, h) * 0.025)
        c = cut_bg(G.crop((cx * w // 2 + m, cy * h // 2 + m, (cx + 1) * w // 2 - m, (cy + 1) * h // 2 - m)))
        bs = sorted(bodies(c), key=lambda b: -b[4])
        cells.append(c.crop(tuple(bs[0][:4])) if bs else None)
    if None in cells: print('%s: -grid 네 칸 중 빈 칸이 있음 — 다시 받기' % i); continue
    sheet_from(cells[0], cells[1], cells[2], os.path.join(dst, i + '-ow.png'), i); okg += 1

ids = sorted({os.path.basename(f)[:-6] for f in glob.glob(os.path.join(src, '*-a.png'))} | {os.path.basename(f)[:-6] for f in glob.glob(os.path.join(src, '*-b.png'))})
ids = [x for x in ids if not x.endswith('-grid')]
ok = 0
for i in ids:
    pa, pb = os.path.join(src, i + '-a.png'), os.path.join(src, i + '-b.png')
    if not (os.path.exists(pa) and os.path.exists(pb)): print('%s: -a(앞·뒤)와 -b(옆) 둘 다 있어야 함' % i); continue
    A = cut_bg(Image.open(pa)); B = cut_bg(Image.open(pb))
    ba = sorted(bodies(A), key=lambda b: b[0]); bb = bodies(B)
    if len(ba) != 2: print('%s: -a 에서 몸이 %d개로 읽힘(앞·뒤 둘이어야 함) — 다시 받기' % (i, len(ba))); continue
    if len(bb) != 1: print('%s: -b 에서 몸이 %d개로 읽힘(옆모습 한 마리여야 함, 겹치거나 둘이면 다시 받기)' % (i, len(bb))); continue
    f, k = [A.crop(tuple(b[:4])) for b in ba]; s = B.crop(tuple(bb[0][:4]))
    sheet_from(f, k, s, os.path.join(dst, i + '-ow.png'), i); ok += 1
print('끝: -a/-b %d / %d, -grid %d' % (ok, len(ids), okg))
