"""이미지 AI 걷기 그림(art/src/people/<아이>_ai.png) → GBC 걷기 그림 16×32 (OBJ 3색 + 투명)
시트: 3줄(앞·뒤·옆) × 칸 4개, 흰 바탕. 옆모습은 왼쪽을 봄 (오른쪽은 뒤집어서 씀).
색: 칸마다 대표색에 가장 가까운 '자리'로 — 0 투명 1 밝은색(피부·흰색·금발) 2 주색(옷) 3 어두운색(외곽선·갈색 머리)"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(WEB, 'tools'))
import scene

# 아이마다: 쓸 칸 (줄, 칸) 6개 = 앞0 앞1 뒤0 뒤1 옆0 옆1, 팔레트(밝은·주·어두운), 대표색 → 자리
PEOPLE = {
    'taichi': dict(frames=[(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                   pal=[(248, 208, 168), (56, 96, 200), (56, 32, 24)],
                   proto=[((245, 205, 170), 1), ((250, 250, 250), 1), ((200, 200, 210), 1),
                          ((60, 100, 200), 2), ((40, 70, 150), 2), ((90, 120, 190), 2),
                          ((30, 25, 25), 3), ((90, 60, 40), 3), ((120, 80, 50), 3), ((60, 40, 30), 3)]),
    'yamato': dict(frames=[(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
                   pal=[(248, 216, 136), (40, 136, 104), (24, 24, 32)],
                   proto=[((245, 205, 170), 1), ((250, 250, 250), 1), ((235, 205, 90), 1), ((250, 235, 150), 1), ((200, 160, 60), 1),
                          ((40, 140, 100), 2), ((40, 120, 140), 2), ((30, 100, 90), 2), ((60, 160, 150), 2),
                          ((25, 25, 30), 3), ((70, 60, 40), 3)]),
}


def sheet_cells(img, rows=3, cols=4):
    H, W = img.shape[:2]
    ch, cw = H / rows, W / cols
    return [[img[int(r * ch):int((r + 1) * ch), int(c * cw):int((c + 1) * cw)] for c in range(cols)] for r in range(rows)]


def figure_mask(cell):
    """바탕(흰색·옅은 회색 격자선, 가장자리와 이어진 것)이 아닌 화소"""
    c = cell.astype(int)
    light = (c.min(2) > 200) | ((np.abs(c[..., 0] - c[..., 1]) < 12) & (np.abs(c[..., 1] - c[..., 2]) < 12) & (c.min(2) > 150))
    h, w = light.shape; bg = np.zeros_like(light); st = []
    for x in range(w): st += [(0, x), (h - 1, x)]
    for y in range(h): st += [(y, 0), (y, w - 1)]
    while st:
        y, x = st.pop()
        if not (0 <= y < h and 0 <= x < w) or bg[y, x] or not light[y, x]: continue
        bg[y, x] = True; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    m = ~bg
    # 떨어진 작은 점(격자선 조각·워터마크) 지우기: 가장 큰 덩어리만
    lab = np.zeros((h, w), int); n = 0; sizes = {}
    for y in range(h):
        for x in range(w):
            if m[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; cnt = 0
                while st:
                    a, b = st.pop()
                    if not (0 <= a < h and 0 <= b < w) or lab[a, b] or not m[a, b]: continue
                    lab[a, b] = n; cnt += 1; st += [(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1), (a + 1, b + 1), (a - 1, b - 1), (a + 1, b - 1), (a - 1, b + 1)]
                sizes[n] = cnt
    if not sizes: return m
    big = max(sizes, key=sizes.get)
    return lab == big


def to_frame(cell, proto):
    m = figure_mask(cell)
    ys, xs = np.nonzero(m)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = cell[y0:y1, x0:x1].astype(int); mk = m[y0:y1, x0:x1]
    # 16 칸보다 넓으면 덜 찬 쪽 열부터 깎기
    while crop.shape[1] > 16:
        if mk[:, 0].sum() <= mk[:, -1].sum(): crop, mk = crop[:, 1:], mk[:, 1:]
        else: crop, mk = crop[:, :-1], mk[:, :-1]
    while crop.shape[0] > 32: crop, mk = crop[1:], mk[1:]
    P = np.array([p for p, _ in proto], float); S = np.array([s for _, s in proto])
    d = ((crop[..., None, :] - P[None, None]) ** 2 * np.array([3, 4, 2])).sum(-1)
    idx = S[d.argmin(-1)]
    idx[~mk] = 0
    out = np.zeros((32, 16), np.uint8)
    h, w = idx.shape; ox = (16 - w) // 2; oy = 32 - h
    out[oy:oy + h, ox:ox + w] = idx
    return out


def frames(kid):
    """→ (6장 [32×16 색번호], 팔레트 [투명, 밝은, 주, 어두운]) 또는 None (그림 없음)"""
    if kid not in PEOPLE: return None
    p = os.path.join(WEB, 'art', 'src', 'people', kid + '_ai.png')
    if not os.path.exists(p): return None
    img, _ = scene.native(p)
    cells = sheet_cells(img)
    sp = PEOPLE[kid]
    fr = [to_frame(cells[r][c], sp['proto']) for (r, c) in sp['frames']]
    return fr, [(255, 255, 255)] + sp['pal']


if __name__ == '__main__':
    from PIL import Image
    out = []
    for k in PEOPLE:
        r = frames(k)
        if not r: continue
        fr, pal = r; pa = np.array(pal, np.uint8); pa[0] = (120, 160, 120)
        out.append(np.concatenate([np.pad(pa[f], ((2, 2), (2, 2), (0, 0)), constant_values=60) for f in fr], 1))
    im = np.concatenate(out, 0)
    Image.fromarray(im).resize((im.shape[1] * 8, im.shape[0] * 8), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else '/tmp/people.png')
