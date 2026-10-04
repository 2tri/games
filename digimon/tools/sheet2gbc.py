"""스프라이트 시트(또는 낱장) → 금판 전투 그림 4색 PNG (+ 선택: 2bpp / 금 압축)
    python3 sheet2gbc.py                         input/ → output/  (앞모습 56칸)
    python3 sheet2gbc.py --size 48 --back        뒷모습 48칸
    python3 sheet2gbc.py --names names.csv       파일 이름을 001_Agumon.png 처럼
    python3 sheet2gbc.py --2bpp --lz             롬에 넣을 바이트도 (.2bpp, .lz)

금판 전투 그림 규칙 (pokegold 디스어셈블리·이 저장소 romhack/patch.py 기준):
  - 4색: 0 흰색(배경 겸용) · 1 밝은 몸 색 · 2 어두운 몸 색 · 3 검정. 투명색은 따로 없음 — 흰 배경이 곧 0번.
    여기서는 미리보기 편하라고 0번에 투명(tRNS)을 걸어 둠 (--no-alpha 로 끔). 롬에 넣을 땐 0번 = 흰색.
  - 크기: 앞모습 40·48·56 (5·6·7 타일), 뒷모습 48 (6 타일). 캔버스 안에서 「가운데·아래」에 붙음.
  - 바이트: 2bpp, 타일 순서는 세로 줄 먼저 (romhack/patch.py to_gb_pic 과 같음), 롬에는 금 압축(gblz)으로.
처리 순서: 배경 찾기 → 덩어리(스프라이트) 자르기 → 원래 크기에서 4톤으로 나누기 → 칸 크기로 줄이기(검정 선 우선 다수결)
          → 바깥 테두리 1칸 검정 다시 그리기 → 캔버스 가운데 아래 → 저장. 줄이기 전에 색을 나눠야 도트가 덜 뭉개짐."""
import argparse, csv, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
WHITE, BLACK = (248, 248, 248), (24, 24, 24)


def lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114


# ── 배경 ──
def background(rgba, tol=28):
    """투명 칸이 있으면 알파로, 없으면 네 모서리에서 많이 나온 색과 비슷한 칸을 가장자리부터 채워 배경으로 (안쪽 흰 눈은 남김)"""
    a = rgba.astype(int); h, w = a.shape[:2]
    if (a[..., 3] < 128).any(): return a[..., 3] < 128
    corners = [tuple(a[y, x, :3]) for y in (0, h - 1) for x in (0, w - 1)]
    bgc = np.array(max(set(corners), key=corners.count))
    near = np.abs(a[..., :3] - bgc).max(2) <= tol
    try:
        from scipy import ndimage
        lab, _ = ndimage.label(near)
        edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
        return np.isin(lab, list(edge))
    except ImportError:                                               # scipy 없으면 가장자리부터 채우기
        bg = np.zeros((h, w), bool); st = [(y, x) for y in (0, h - 1) for x in range(w)] + [(y, x) for x in (0, w - 1) for y in range(h)]
        while st:
            y, x = st.pop()
            if 0 <= y < h and 0 <= x < w and near[y, x] and not bg[y, x]:
                bg[y, x] = True; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
        return bg


# ── 시트에서 덩어리 자르기 ──
def sprites(fg, gap=3, min_area=64):
    """전경 칸을 gap 만큼 부풀려 붙은 조각(눈·발톱)을 한 덩어리로 묶고, 덩어리마다 네모 범위. 위→아래, 왼→오른 순서"""
    try:
        from scipy import ndimage
        lab, n = ndimage.label(ndimage.binary_dilation(fg, iterations=gap) if gap else fg, structure=np.ones((3, 3)))
        boxes = ndimage.find_objects(lab)
    except ImportError:
        lab = None; n = 1; ys, xs = np.where(fg); boxes = [(slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))]
    out = []
    for i, sl in enumerate(boxes):
        if sl is None: continue
        m = fg[sl] & ((lab[sl] == i + 1) if lab is not None else True)
        if m.sum() < min_area: continue
        ys, xs = np.where(m); y0, x0 = sl[0].start + ys.min(), sl[1].start + xs.min()
        out.append((y0, x0, sl[0].start + ys.max() + 1, sl[1].start + xs.max() + 1))
    rowh = max(1, int(np.median([b[2] - b[0] for b in out]) * .5)) if out else 1
    return sorted(out, key=lambda b: (b[0] // rowh, b[1]))


# ── 4톤 ──
def kmeans(x, k, it=25):
    c = x[np.linspace(0, len(x) - 1, k).astype(int)].astype(float)
    for _ in range(it):
        lab = np.argmin(((x[:, None] - c[None]) ** 2).sum(2), 1)
        c = np.array([x[lab == j].mean(0) if (lab == j).any() else c[j] for j in range(k)])
    return c, lab


def tones(rgb, fg, pal=None, black=70, white=232):
    """전경 → 0 흰 / 1 밝은 / 2 어두운 / 3 검정. 아주 어두운 칸 = 검정, 아주 밝고 채도 낮은 칸 = 흰색, 나머지는 색 두 무리 (pal 을 주면 그 두 색에 맞춤)"""
    a = rgb.astype(float); L = lum(a); sat = a.max(2) - a.min(2)
    t = -np.ones(fg.shape, int)
    t[fg & (L < black)] = 3; t[fg & (L >= white) & (sat < 24)] = 0
    mid = fg & (t < 0)
    if pal is None:
        if mid.sum() >= 2:
            c, lab = kmeans(a[mid], 2); order = np.argsort(-lum(c))             # 밝은 쪽이 1
            rank = np.empty(2, int); rank[order] = [1, 2]; t[mid] = rank[lab]; pal = [tuple(int(v) for v in c[o]) for o in order]
        else: t[mid] = 1; pal = [(200, 200, 200), (120, 120, 120)]
    else:
        p = np.array(pal, float); t[mid] = 1 + np.argmin(((a[mid][:, None] - p[None]) ** 2).sum(2), 1)
    return t, pal


# ── 줄이기·테두리 ──
def shrink(t, size, line_in=0.4, ss=4):
    """칸마다 원래 칸을 ss×ss 로 찍어 다수결 (검정은 line_in 넘으면 우선). 이미 작으면 정수배로만 키움(최대 3배)"""
    h, w = t.shape; k = min(size / w, size / h)
    if k >= 1:
        n = max(1, min(3, int(k))); return np.kron(t, np.ones((n, n), int)) if n > 1 else t
    th, tw = max(1, round(h * k)), max(1, round(w * k)); out = -np.ones((th, tw), int)
    for j in range(th):
        for i in range(tw):
            ys = np.clip(((j + (np.arange(ss) + .5) / ss) / k).astype(int), 0, h - 1)
            xs = np.clip(((i + (np.arange(ss) + .5) / ss) / k).astype(int), 0, w - 1)
            b = t[np.ix_(ys, xs)].ravel(); f = b[b >= 0]
            if len(f) < .5 * len(b): continue
            if (f == 3).mean() >= line_in or not (f != 3).any(): out[j, i] = 3
            else: v, c = np.unique(f[f != 3], return_counts=True); out[j, i] = v[np.argmax(c)]
    return out


def outline(t):
    m = t >= 0; p = np.pad(m, 1); t = t.copy()
    t[m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])] = 3
    return t


def drop_specks(t, n=3):
    """n 칸보다 작은 외딴 점 지우기"""
    try:
        from scipy import ndimage
        lab, k = ndimage.label(t >= 0, structure=np.ones((3, 3)))
        sizes = ndimage.sum(t >= 0, lab, range(1, k + 1))
        for i, s in enumerate(sizes):
            if s < n: t[lab == i + 1] = -1
    except ImportError: pass
    return t


def place(t, size):
    """캔버스(size×size) 가운데·아래에 붙임 (금 to_gb_pic 과 같은 자리). 빈 곳 = 0(흰)"""
    c = np.zeros((size, size), np.uint8); h, w = t.shape
    oy, ox = size - h, (size - w) // 2; v = np.where(t < 0, 0, t)
    c[oy:oy + h, ox:ox + w] = v
    return c


# ── 바이트 ──
def to_2bpp(idx):
    """금판 그림 바이트: 8×8 타일, 세로 줄 먼저, 줄마다 낮은 비트판·높은 비트판 (romhack/patch.py to_gb_pic 과 같음)"""
    H, W = idx.shape; out = bytearray()
    for tx in range(W // 8):
        for ty in range(H // 8):
            for r in range(8):
                row = idx[ty * 8 + r, tx * 8:tx * 8 + 8]
                out += bytes([sum(((int(v) & 1) << (7 - i)) for i, v in enumerate(row)), sum((((int(v) >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
    return bytes(out)


def save_png(idx, pal, path, alpha=True):
    im = Image.fromarray(idx, 'P'); flat = list(WHITE) + list(pal[0]) + list(pal[1]) + list(BLACK)
    im.putpalette(flat + [0] * (768 - len(flat)))
    im.save(path, transparency=0) if alpha else im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='src', default='input'); ap.add_argument('--out', default='output')
    ap.add_argument('--size', type=int, default=56, choices=[40, 48, 56]); ap.add_argument('--back', action='store_true', help='뒷모습: 48칸')
    ap.add_argument('--names', help='CSV: file,index,no,name (index 는 시트 안 순서 0부터) → 001_Agumon.png')
    ap.add_argument('--gap', type=int, default=3, help='이 칸 수 안에 있는 조각은 한 덩어리로'); ap.add_argument('--min-area', type=int, default=64)
    ap.add_argument('--pal', nargs=2, help='몸 색 두 개 고정 예: 240,192,96 200,96,40')
    ap.add_argument('--no-outline', action='store_true'); ap.add_argument('--no-alpha', action='store_true')
    ap.add_argument('--2bpp', dest='b2', action='store_true'); ap.add_argument('--lz', action='store_true', help='금 압축본(.lz)도 (romhack/gblz.py)')
    a = ap.parse_args()
    size = 48 if a.back else a.size
    pal_fix = [tuple(int(v) for v in s.split(',')) for s in a.pal] if a.pal else None
    names = {}
    if a.names:
        for r in csv.DictReader(open(a.names, encoding='utf-8-sig')): names[(r['file'], int(r['index']))] = '%03d_%s' % (int(r['no']), r['name'])
    gblz = None
    if a.lz: sys.path.insert(0, os.path.join(WEB, 'romhack')); import gblz
    os.makedirs(a.out, exist_ok=True); done = []
    files = sorted(f for f in os.listdir(a.src) if f.lower().endswith(('.png', '.gif', '.webp', '.bmp', '.jpg', '.jpeg')))
    for f in files:
        rgba = np.asarray(Image.open(os.path.join(a.src, f)).convert('RGBA'))
        fg = ~background(rgba)
        boxes = sprites(fg, a.gap, a.min_area)
        stem = os.path.splitext(f)[0]
        for k, (y0, x0, y1, x1) in enumerate(boxes):
            t, pal = tones(rgba[y0:y1, x0:x1, :3], fg[y0:y1, x0:x1], pal_fix)
            t = shrink(t, size)
            t = drop_specks(t)
            if not a.no_outline: t = outline(t)
            idx = place(t, size)
            name = names.get((f, k)) or (stem if len(boxes) == 1 else '%s_%02d' % (stem, k))
            save_png(idx, pal, os.path.join(a.out, name + '.png'), not a.no_alpha)
            if a.b2 or a.lz:
                raw = to_2bpp(idx)
                if a.b2: open(os.path.join(a.out, name + '.2bpp'), 'wb').write(raw)
                if a.lz: open(os.path.join(a.out, name + '.lz'), 'wb').write(gblz.compress(raw))
            done.append((name, idx, pal)); print('%s [%d] %dx%d → %s (%dx%d 안 %dx%d)' % (f, k, x1 - x0, y1 - y0, name, size, size, t.shape[1], t.shape[0]))
    if done:                                                          # 한눈에 보기 (×3)
        cols = min(8, len(done)); rows = (len(done) + cols - 1) // cols; s = size * 3 + 8
        sheet = Image.new('RGB', (cols * s, rows * s), (232, 240, 232))
        for i, (n, idx, pal) in enumerate(done):
            p = np.array([WHITE, pal[0], pal[1], BLACK], np.uint8)[idx]
            sheet.paste(Image.fromarray(p).resize((size * 3, size * 3), Image.NEAREST), ((i % cols) * s + 4, (i // cols) * s + 4))
        sheet.save(os.path.join(a.out, '_preview.png'))
    print('그림 %d장 → %s' % (len(done), a.out))


if __name__ == '__main__':
    main()
