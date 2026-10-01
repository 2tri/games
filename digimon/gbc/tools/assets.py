"""이미지 AI 배경 그림에서 지도 조각 잘라내기 (16×16 칸 단위).
- 바닥(풀·길 등): 그림에서 가장 고른 16×16 조각을 자동으로 고름
- 물건(집·나무·표지판…): 상자로 잘라 w×h 칸 크기에 바닥 가운데 맞춤.
  바깥(가장자리에서 이어진 바닥색)은 정해진 바닥 조각 무늬로 갈아 끼워 이음매가 없게
좌표는 '원래 도트' 기준 (tools/scene.py native)."""
import os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(os.path.dirname(HERE))
import sys
sys.path.insert(0, os.path.join(WEB, 'tools'))
import scene

CACHE = os.path.join(os.path.dirname(HERE), 'build', 'assets')


def load_native(name, cell=None, off=None):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name + '.npy')
    src = os.path.join(WEB, 'art', 'src', 'bg', name + '_ai.png')
    if os.path.exists(p) and os.path.getmtime(p) > os.path.getmtime(src): return np.load(p)
    img, _ = scene.native(src, cell, off)
    np.save(p, img); return img


def pick_ground(img, region, kind, need=0.97):
    """region 안에서 kind('green'·'tan'·'brown'·'purple'·'wood') 색이 가장 고르게 꽉 찬 16×16"""
    x0, y0, x1, y1 = region
    best = None
    for y in range(y0, y1 - 15, 2):
        for x in range(x0, x1 - 15, 2):
            b = img[y:y + 16, x:x + 16].reshape(-1, 3).astype(int)
            r, g, bl = b[:, 0], b[:, 1], b[:, 2]
            if kind == 'green': ok = (g > r + 15) & (g > bl + 15)
            elif kind == 'tan': ok = (r > 170) & (r > g) & (g > bl + 20)
            elif kind == 'brown': ok = (r > 110) & (r < 200) & (r > g + 20) & (g > bl)
            elif kind == 'purple': ok = (bl > g + 10) & (r > g)
            elif kind == 'wood': ok = (r > 150) & (r > g + 15) & (g > bl + 15)
            else: ok = np.ones(len(b), bool)
            if ok.mean() < need: continue
            u, c = np.unique(b, axis=0, return_counts=True)
            score = -c.max() / len(b) + len(u) * 0.004          # 한 색이 많고 색 수가 적을수록
            if best is None or score < best[0]: best = (score, x, y)
    if best is None: raise ValueError('바닥 못 찾음: %s %s' % (kind, region))
    _, x, y = best
    return img[y:y + 16, x:x + 16].copy(), (x, y)


def ground_hsv(px, kinds=('green', 'tan', 'brown')):
    a = px.astype(float) / 255; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    sat = d / (mx + 1e-6); v = mx
    m = np.zeros(px.shape[:2], bool)
    if 'green' in kinds: m |= (h > 60) & (h < 165) & (sat > 0.18) & (v > 0.42)
    if 'tan' in kinds: m |= (h > 18) & (h < 48) & (sat > 0.2) & (sat < 0.62) & (v > 0.72)
    if 'brown' in kinds: m |= (h > 12) & (h < 40) & (sat > 0.3) & (v > 0.38) & (v < 0.78)
    return m


def near_any(px, cols, tol):
    if isinstance(cols, tuple): return ground_hsv(px, cols)
    if len(cols) == 0: return np.zeros(px.shape[:2], bool)
    d = ((px[:, :, None, :].astype(int) - cols[None, None].astype(int)) ** 2).sum(3)
    return d.min(2) <= tol * tol


def stamp(img, box, wt, ht, ground, bgcols, tol=18, fill=True, align='bottom'):
    """box 영역을 wt×ht 칸으로. 가장자리에서 이어진 바닥색은 ground 무늬로 바꿈"""
    x0, y0, x1, y1 = box
    obj = img[y0:y1, x0:x1].copy(); h, w = obj.shape[:2]
    W, H = wt * 16, ht * 16
    canvas = np.tile(ground, (ht, wt, 1)) if ground is not None else np.zeros((H, W, 3), np.uint8)
    ox = (W - w) // 2; oy = H - h if align == 'bottom' else (H - h) // 2
    if not fill:
        canvas[max(0, oy):oy + h, max(0, ox):ox + w] = obj[max(0, -oy):, max(0, -ox):][:H, :W]
        return canvas
    bgm = near_any(obj, bgcols, tol)
    seen = np.zeros((h, w), bool); st = []
    for x in range(w):
        for y in (0, h - 1):
            if bgm[y, x]: st.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bgm[y, x]: st.append((y, x))
    while st:
        y, x = st.pop()
        if seen[y, x] or not bgm[y, x]: continue
        seen[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h and 0 <= X < w and not seen[Y, X] and bgm[Y, X]: st.append((Y, X))
    for y in range(h):
        for x in range(w):
            if not seen[y, x]:
                Y, X = oy + y, ox + x
                if 0 <= Y < H and 0 <= X < W: canvas[Y, X] = obj[y, x]
    return canvas


def wipe(arr, ground, rects):
    """조각 안의 군더더기(옆 울타리·덤불 조각)를 바닥 무늬로 덮음. rects: (x0, y0, x1, y1) 조각 기준 화소"""
    g = np.tile(ground, (arr.shape[0] // 16 + 1, arr.shape[1] // 16 + 1, 1))[:arr.shape[0], :arr.shape[1]]
    for x0, y0, x1, y1 in rects: arr[y0:y1, x0:x1] = g[y0:y1, x0:x1]
    return arr


def bbox_near(img, pt, bgcols, tol=18, maxr=40):
    """pt 에서 시작해 바닥색이 아닌 화소로 이어진 덩어리의 상자 (maxr 안에서만)"""
    x, y = pt; H, W = img.shape[:2]
    x0, y0, x1, y1 = max(0, x - maxr), max(0, y - maxr), min(W, x + maxr), min(H, y + maxr)
    sub = img[y0:y1, x0:x1]; fg = ~near_any(sub, bgcols, tol)
    sy, sx = y - y0, x - x0
    if not fg[sy, sx]:
        ys, xs = np.nonzero(fg); k = np.argmin((ys - sy) ** 2 + (xs - sx) ** 2); sy, sx = ys[k], xs[k]
    seen = np.zeros_like(fg); st = [(sy, sx)]
    while st:
        a, b = st.pop()
        if seen[a, b] or not fg[a, b]: continue
        seen[a, b] = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                A2, B2 = a + dy, b + dx
                if 0 <= A2 < fg.shape[0] and 0 <= B2 < fg.shape[1] and not seen[A2, B2] and fg[A2, B2]: st.append((A2, B2))
    ys, xs = np.nonzero(seen)
    return (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)


def auto(img, pt, ground, bgcols, tol=18, maxr=40, size=None):
    """점 하나로 물건 찾아 칸 크기에 맞춰 자르기"""
    b = bbox_near(img, pt, bgcols, tol, maxr)
    w, h = b[2] - b[0], b[3] - b[1]
    wt, ht = size if size else ((w + 15) // 16, (h + 15) // 16)
    return stamp(img, b, wt, ht, ground, bgcols, tol), b


def colors_of(*tiles):
    return np.unique(np.concatenate([t.reshape(-1, 3) for t in tiles]), axis=0)


# ───────── 장면마다 조각 정의 ─────────
def build_all():
    A = {}       # 이름 → (RGB 배열 H×W, (칸 w, 칸 h), 성질)
    def put(name, arr, solid=True, extra=None):
        A[name] = {'img': arr, 'w': arr.shape[1] // 16, 'h': arr.shape[0] // 16, 'solid': solid, **(extra or {})}

    # ── 주인공 동네 (town) ──   바닥 판정은 색상 규칙 (G: 풀, GP: 풀+길+흙)
    G = ('green',); GP = ('green', 'tan', 'brown')
    T = load_native('town')
    grass, _ = pick_ground(T, (16, 32, 304, 260), 'green')
    path, _ = pick_ground(T, (16, 32, 304, 260), 'tan')
    dirt, _ = pick_ground(T, (16, 180, 160, 260), 'brown')
    garden = T[128:144, 80:96].copy()
    put('t_grass', grass, False); put('t_path', path, False); put('t_dirt', dirt, False); put('t_garden', garden, False)
    def A_(name, pt, maxr, solid=True, extra=None, cols=GP, size=None):
        arr, box = auto(T, pt, grass, cols, 0, maxr, size); put(name, arr, solid, extra); A[name]['box'] = box
    put('t_tree', T[31:63, 224:240].copy())                 # 나무 1×2 (배경 풀째로)
    put('t_forest', T[96:112, 273:289].copy())              # 빽빽한 숲 (바깥 테두리용, 이어 붙여도 자연스러움)
    put('t_fence_h', stamp(T, (64, 192, 80, 208), 1, 1, grass, G))
    put('t_fence_v', stamp(T, (64, 96, 80, 112), 1, 1, grass, G))
    put('t_flowers', T[96:112, 79:95].copy(), False)
    # 건물: 문이 한 칸 가운데 오도록 상자를 맞춤
    put('t_house', wipe(stamp(T, (91, 62, 155, 142), 4, 5, grass, GP), grass, [(0, 0, 64, 4), (0, 0, 5, 80)]), extra={'door': (1, 4)})
    put('t_house2', wipe(stamp(T, (183, 79, 247, 111), 4, 2, grass, GP), grass, [(0, 0, 9, 32), (58, 0, 64, 32)]), extra={'door': (1, 1)})
    put('t_shop', stamp(T, (223, 135, 287, 183), 4, 3, grass, GP), extra={'door': (1, 2)})
    put('t_shopsign', stamp(T, (272, 156, 288, 188), 1, 2, grass, GP))
    put('t_sign', stamp(T, (256, 31, 272, 47), 1, 1, grass, GP))
    put('t_sign2', stamp(T, (240, 113, 256, 129), 1, 1, grass, GP))
    A_('t_flowerbed', (150, 152), 30)

    # ── 여름 캠프장 (camp) ──
    C = load_native('camp')
    cgrass, _ = pick_ground(C, (16, 32, 304, 260), 'green')
    cpath, _ = pick_ground(C, (160, 100, 304, 260), 'tan')
    cdirt, _ = pick_ground(C, (16, 190, 160, 260), 'brown')
    put('c_grass', cgrass, False); put('c_path', cpath, False); put('c_dirt', cdirt, False)
    def B_(name, pt, maxr, solid=True, extra=None, cols=GP, size=None):
        arr, box = auto(C, pt, cgrass, cols, 0, maxr, size); put(name, arr, solid, extra); A[name]['box'] = box
    put('c_tree', T[31:63, 224:240].copy())
    put('c_forest', C[96:112, 276:292].copy())
    put('c_shrine', stamp(C, (32, 32, 80, 112), 3, 5, cgrass, GP), extra={'walk': [(1, 2), (1, 3), (1, 4)], 'door': (1, 1)})
    put('c_stairs', C[128:144, 48:64].copy(), False)
    put('c_lodge', wipe(stamp(C, (92, 62, 156, 142), 4, 5, cgrass, GP), cgrass, [(0, 0, 64, 4), (0, 0, 4, 80)]), extra={'door': (1, 4)})
    put('c_office', stamp(C, (183, 79, 247, 111), 4, 2, cgrass, GP), extra={'door': (1, 1)})
    put('c_table', stamp(C, (166, 112, 198, 128), 2, 1, cgrass, G))
    put('c_fire', stamp(C, (136, 152, 164, 176), 2, 2, cgrass, GP))
    for i, bx in enumerate([(224, 144, 240, 160), (256, 144, 272, 160), (256, 160, 272, 176), (224, 176, 240, 192), (256, 176, 272, 192)]):
        put('c_tent%d' % (i + 1), stamp(C, bx, 1, 1, cgrass, G))
    put('c_stump', stamp(C, (240, 161, 256, 177), 1, 1, cgrass, G))
    put('c_sign', stamp(C, (228, 112, 260, 128), 2, 1, cgrass, GP))

    # ── 행복의 마을 (village) ──
    V = load_native('village')
    vgrass, _ = pick_ground(V, (16, 0, 304, 270), 'green')
    vpath, _ = pick_ground(V, (130, 80, 240, 270), 'brown')
    vbg = colors_of(vgrass, vpath, V[150:166, 160:176], V[90:106, 50:66])
    put('v_grass', vgrass, False); put('v_path', vpath, False)
    sea = V[96:112, 304:319]; put('v_sea', np.concatenate([sea, sea[:, :1]], 1))
    put('v_center', stamp(V, (126, 0, 206, 78), 5, 5, vgrass, np.concatenate([vbg, colors_of(V[0:6, 126:132], V[0:6, 200:206])]), 30), extra={'door': (2, 4)})
    put('v_shop', stamp(V, (222, 30, 286, 78), 4, 3, vgrass, vbg), extra={'door': (1, 2)})
    put('v_house', stamp(V, (175, 96, 223, 144), 3, 3, vgrass, vbg), extra={'door': (1, 2)})
    put('v_block1', stamp(V, (15, 10, 111, 74), 6, 4, vgrass, vbg))
    put('v_block2', stamp(V, (15, 150, 63, 214), 3, 4, vgrass, vbg))
    put('v_block3', stamp(V, (78, 148, 126, 212), 3, 4, vgrass, vbg))
    put('v_block4', stamp(V, (78, 98, 142, 146), 4, 3, vgrass, vbg))
    put('v_block5', stamp(V, (256, 84, 304, 196), 3, 7, vgrass, vbg))
    put('v_block6', stamp(V, (78, 222, 126, 270), 3, 3, vgrass, vbg))
    put('v_block7', stamp(V, (190, 224, 222, 256), 2, 2, vgrass, vbg))
    put('v_egg1', stamp(V, (24, 108, 56, 140), 2, 2, vgrass, vbg))
    put('v_egg2', stamp(V, (192, 164, 224, 196), 2, 2, vgrass, vbg))
    put('v_crib', stamp(V, (16, 206, 32, 222), 1, 1, vgrass, vbg))
    put('v_tree', stamp(V, (174, 172, 190, 204), 1, 2, vgrass, vbg))
    put('v_pond', stamp(V, (256, 226, 304, 274), 3, 3, vgrass, vbg))

    # ── 집 안 (house) ──
    Hn = load_native('house', 4.1, (1.5, 0.0))
    floor, _ = pick_ground(Hn, (110, 150, 200, 215), 'wood', 0.85)
    wtop, _ = pick_ground(Hn, (36, 26, 160, 52), 'purple', 0.85)
    put('h_floor', floor, False); put('h_wall', wtop)
    put('h_wallb', Hn[128:144, 40:56].copy())
    put('h_plant', Hn[42:74, 38:54].copy())
    put('h_desk', Hn[28:76, 50:98].copy())
    put('h_bed', Hn[42:106, 125:157].copy())
    put('h_tv', Hn[76:108, 65:97].copy())
    put('h_console', Hn[68:100, 37:53].copy())
    put('h_window', stamp(Hn, (99, 30, 123, 46), 2, 1, wtop, None, fill=False))
    put('h_tv2', Hn[126:158, 63:111].copy())
    put('h_table', stamp(Hn, (70, 168, 103, 197), 2, 2, floor, colors_of(floor)))
    put('h_stool', stamp(Hn, (53, 180, 67, 192), 1, 1, floor, colors_of(floor)))
    put('h_plant2', stamp(Hn, (154, 122, 170, 155), 1, 2, floor, colors_of(floor)))
    put('h_shelf', stamp(Hn, (156, 175, 174, 223), 1, 3, floor, colors_of(floor)))
    put('h_kitchen', stamp(Hn, (200, 175, 218, 223), 1, 3, floor, colors_of(floor)))
    put('h_stairs', Hn[80:96, 172:188].copy(), False)
    put('h_void', np.zeros((16, 16, 3), np.uint8))
    put('h_mat', stamp(Hn, (111, 213, 137, 227), 2, 1, floor, colors_of(floor)), solid=False)
    # ── 길·숲·해변 타일 (A6: tiles_ai.png, 흰 바탕) ──
    R = load_native('tiles')
    white = colors_of(R[62:66, 52:95], R[165:169, 100:190], R[62:66, 160:199])
    rg = R[4:20, 4:20].copy(); rg2 = R[4:20, 54:70].copy()
    put('r_grass', rg, False); put('r_grass2', rg2, False)
    put('r_tall', R[12:28, 104:120].copy(), False, extra={'grass': True})
    put('r_tall2', R[14:30, 156:172].copy(), False, extra={'grass': True})
    put('r_path', R[107:123, 12:28].copy(), False)
    put('r_sand', R[143:159, 4:20].copy(), False)
    put('r_sand2', R[143:159, 32:48].copy(), False)
    put('r_shore', R[143:159, 80:96].copy())
    put('r_sea', R[143:159, 104:120].copy())
    put('r_deep', R[143:159, 134:150].copy())
    put('r_wave', R[142:158, 164:180].copy())
    # 나무·야자수는 2×2 칸 (풀 바탕)
    for name, box in [('r_tree', (0, 68, 25, 99)), ('r_tree2', (25, 68, 50, 99)), ('r_bush', (50, 68, 78, 99)), ('r_bush2', (78, 68, 101, 99)),
                      ('r_jungle', (100, 68, 124, 99)), ('r_palm', (124, 68, 150, 99)), ('r_palm2', (150, 68, 175, 99))]:
        put(name, stamp(R, box, 2, 2, rg, white, 30))
    put('r_cliff', stamp(R, (108, 101, 140, 133), 2, 2, rg, white, 30))
    put('r_rock', stamp(R, (98, 171, 132, 205), 2, 2, rg, white, 30))
    put('r_stone', stamp(R, (99, 39, 120, 59), 1, 1, rg, white, 30) if False else stamp(R, (101, 40, 117, 56), 1, 1, rg, white, 30))
    put('r_rocks', stamp(R, (150, 40, 169, 59), 1, 1, rg, white, 30))
    put('r_sign', stamp(R, (178, 42, 196, 59), 1, 1, rg, white, 30))
    def unwhite(arr):       # 갇힌 흰 바탕(울타리 사이 등)도 풀로
        m = near_any(arr, white, 30); arr[m] = np.tile(rg, (arr.shape[0] // 16, arr.shape[1] // 16, 1))[m]; return arr
    put('r_fence', unwhite(stamp(R, (12, 38, 28, 54), 1, 1, rg, white, 30)))
    put('r_flowers', unwhite(stamp(R, (6, 176, 22, 192), 1, 1, rg, white, 30)), False)
    put('r_flowers2', stamp(R, (30, 178, 46, 194), 1, 1, rg, white, 30))
    put('r_booth', stamp(R, (62, 172, 78, 205), 1, 2, R[143:159, 4:20].copy(), white, 30))
    # 임시 한쪽 턱 (A11 받으면 교체): 풀 위에 아래로 떨어지는 턱 모서리
    ld = rg.copy().astype(int)
    ld[9:12] = (ld[9:12] * 0.55).astype(int); ld[12:16] = (ld[12:16] * 0.8).astype(int); ld[8] = np.minimum(ld[8] + 40, 255); ld[11] = (30, 70, 30)
    put('r_ledge', ld.astype(np.uint8), False, extra={'ledge': True})
    # 숲 테두리: 정글 나무 우듬지 (이어 붙임)
    put('r_canopy', R[72:88, 4:20].copy())
    return A


def load_all():
    """build_all 결과를 build/assets/all.pkl 에 저장해 두고 씀 (그림·이 파일이 바뀌면 다시)"""
    import pickle
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, 'all.pkl')
    srcs = [os.path.abspath(__file__)] + [os.path.join(WEB, 'art', 'src', 'bg', n + '_ai.png') for n in ('town', 'camp', 'village', 'house', 'tiles')]
    if os.path.exists(p) and os.path.getmtime(p) > max(os.path.getmtime(f) for f in srcs):
        return pickle.load(open(p, 'rb'))
    A = build_all(); pickle.dump(A, open(p, 'wb')); return A


def preview(A, path, scale=3):
    names = list(A); W = 0; H = 0; x = 0; rows = []; cur = []; rw = 0
    for n in names:
        a = A[n]['img']
        if rw + a.shape[1] + 4 > 300: rows.append(cur); cur = []; rw = 0
        cur.append(n); rw += a.shape[1] + 4
    rows.append(cur)
    hs = [max(A[n]['img'].shape[0] for n in r) + 12 for r in rows]
    out = np.full((sum(hs), 304, 3), 60, np.uint8)
    y = 0
    for r, h in zip(rows, hs):
        x = 0
        for n in r:
            a = A[n]['img']; out[y + 10:y + 10 + a.shape[0], x:x + a.shape[1]] = a; x += a.shape[1] + 4
        y += h
    im = Image.fromarray(out).resize((out.shape[1] * scale, out.shape[0] * scale), Image.NEAREST)
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); y = 0
    for r, h in zip(rows, hs):
        x = 0
        for n in r:
            d.text((x * scale, y * scale), n, fill=(255, 255, 0)); x += A[n]['img'].shape[1] + 4
        y += h
    im.save(path)


if __name__ == '__main__':
    A = build_all()
    preview(A, sys.argv[1] if len(sys.argv) > 1 else '/tmp/assets.png')
    print(len(A), 'assets')
