"""받은 그림 → 롬에 넣을 4색 도트 (art/<id>-f.png · -b.png)
  주문문 v3 (앞·뒤 따로, 회색 4톤):
    python3 ingest.py 받은그림.png kuwagamon --side f        앞모습
    python3 ingest.py 받은그림.png kuwagamon --side b        뒷모습
    python3 ingest.py 받은그림.png kuwagamon --side f --flat 평면 그림(격자 없음)으로 받은 것
    python3 ingest.py 받은그림.png kuwagamon --side f --sketch ../art/sketch/kuwagamon.png   밑그림 주문문으로 받은 것 (실루엣 맞춤·일치율)
  옛 방식 (한 장에 왼쪽 앞 · 오른쪽 뒤):
    python3 ingest.py 받은그림.png metalgreymon --side sheet --grade 완전체
등급·색은 order/specs.py 에서 읽는다 (--grade, --pal 로 바꿀 수 있음).
앞모습 크기는 등급으로: 유아기·유년기 40, 성장기 48, 성숙기 이상 56 (디지몬스터 칸 크기 5·6·7). 뒷모습은 48.
회색 그림이면 밝기로 4톤(흰·밝은·어두운·검정)을 나누고, specs 의 몸 색 두 개를 입힌다 (앞·뒤가 팔레트 하나를 같이 쓰므로 같은 색).
손으로 고칠 칸은 art/fix/<id>-<f|b>.txt 에 적어 두면 변환 뒤에 덮어씀 (다시 변환해도 유지):
  첫 줄 「x y」(고칠 곳 왼쪽 위), 다음 줄부터 한 칸에 한 글자 — 빈칸 그대로, . 배경, W 흰, l 밝은, d 어두운, # 검정"""
import argparse, os, sys, shutil
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WEB, 'tools')); sys.path.insert(0, os.path.join(HERE, 'order'))
import snapc, specs

FRONT = {'유아기Ⅰ': 40, '유아기Ⅱ': 40, '유년기Ⅰ': 40, '유년기Ⅱ': 40, '유년기': 40, '성장기': 48}


def split(im):
    """한 장(왼쪽 앞 · 오른쪽 뒤)을 두 그림 사이의 흰 세로 띠에서 나눔 (없으면 가운데)"""
    a = np.asarray(im.convert('L')).astype(int); h, w = a.shape
    ink = (a < 235).sum(0)
    mid = range(int(w * .3), int(w * .7))
    empty = [x for x in mid if ink[x] <= h * 0.002]
    if empty:
        runs, s = [], empty[0]
        for p, q in zip(empty, empty[1:] + [None]):
            if q != p + 1: runs.append((s, p)); s = q
        s, e = max(runs, key=lambda r: r[1] - r[0]); cut = (s + e) // 2
    else: cut = w // 2
    return im.crop((0, 0, cut, h)), im.crop((cut, 0, w, h))


def is_gray(im):
    """흰 배경을 뺀 그림 부분의 채도가 낮으면 회색 4톤 그림"""
    a = np.asarray(im.convert('RGB')).astype(int)
    ink = a[a.min(2) < 230]
    if len(ink) == 0: return True
    return float((ink.max(1) - ink.min(1)).mean()) < 18


def gray4(img, flat, maxs, tol=24):
    """회색 4톤 그림 → 칸 배열 (-1 배경, 0 흰, 1 밝은 회색, 2 어두운 회색, 3 검정)
    flat=False: 도트 격자를 찾아 칸마다 가운데 값. flat=True: 격자 없이 목표 크기의 4배로 줄여 칸으로 씀"""
    rgb = np.asarray(img.convert('RGB')).astype(float)
    if flat:
        k = maxs * 4 / max(rgb.shape[:2])
        if k < 1: rgb = np.asarray(img.convert('RGB').resize((max(1, round(rgb.shape[1] * k)), max(1, round(rgb.shape[0] * k))), Image.BOX)).astype(float)
        cells = rgb
    else:
        (pw, ox), (ph, oy) = snapc.grid(snapc.lum(rgb))
        nx, ny = int((rgb.shape[1] - ox) / pw), int((rgb.shape[0] - oy) / ph)
        cells = np.zeros((ny, nx, 3))
        for j in range(ny):
            for i in range(nx):
                x0, x1 = int(ox + i * pw + pw * .3), int(ox + (i + 1) * pw - pw * .3)
                y0, y1 = int(oy + j * ph + ph * .3), int(oy + (j + 1) * ph - ph * .3)
                cells[j, i] = np.median(rgb[y0:y1 + 1, x0:x1 + 1].reshape(-1, 3), 0)
    bg = snapc.flood_bg(cells, tol)
    L = snapc.lum(cells); v = L[~bg]
    c = np.array([250., 175., 95., 20.])                           # 흰·밝은·어두운·검정에서 시작하는 1차원 k-평균
    for _ in range(30):
        lab = np.argmin(np.abs(v[:, None] - c[None]), 1)
        c = np.array([v[lab == m].mean() if (lab == m).any() else c[m] for m in range(4)])
    t = -np.ones(L.shape, int)
    t[~bg] = np.argmin(np.abs(L[~bg][:, None] - c[None]), 1)
    ys, xs = np.where(t >= 0)
    return t[ys.min():ys.max() + 1, xs.min():xs.max() + 1], tuple(round(x) for x in c)


def convert(part, maxs, pal, flat=False, fixed=None):
    """→ (칸 배열, 4색 팔레트). 회색 그림이면 pal(specs) 색을 입힘. 색 그림이면 그림에서 몸 색 두 개를 고르고(fixed 가 있으면 그 색으로)"""
    if is_gray(part) or flat:
        t, lv = gray4(part, flat, maxs)
        print('  회색 4톤 밝기', lv)
        body = fixed or pal                                          # 뒷모습만 따로 받으면 이미 넣은 앞모습 색으로
        p4 = [(248, 248, 248), tuple(body[0]), tuple(body[1]), (24, 24, 24)]
    else:
        t, p4, cell = snapc.snap(part, accent=False, fixed=fixed, mids_only=True)
        print('  색 그림 도트 칸', tuple(round(x, 2) for x in cell))
    t = snapc.drop_small(t, 8); t = snapc.shrink2(t, maxs, maxs); t = snapc.drop_small(t, 3)
    return t, p4


def apply_fix(t, path):
    """art/fix 의 손질 글을 칸 배열에 덮어씀"""
    if not os.path.exists(path): return t, 0
    lines = open(path, encoding='utf-8').read().split('\n')
    x0, y0 = map(int, lines[0].split()); t = t.copy(); n = 0
    code = {'.': -1, 'W': 0, 'l': 1, 'd': 2, '#': 3}
    for j, row in enumerate(lines[1:]):
        for i, ch in enumerate(row):
            if ch in code and 0 <= y0 + j < t.shape[0] and 0 <= x0 + i < t.shape[1]:
                n += t[y0 + j, x0 + i] != code[ch]; t[y0 + j, x0 + i] = code[ch]
    return t, n


def front_colors(did):
    """이미 넣은 앞모습의 몸 색 두 개 (뒷모습만 따로 받을 때 같은 팔레트로)"""
    p = os.path.join(WEB, 'art', did + '-f.png')
    if not os.path.exists(p): return None
    a = np.asarray(Image.open(p).convert('RGBA')).reshape(-1, 4)
    cols = sorted({tuple(int(v) for v in x[:3]) for x in a if x[3] > 128 and 40 < max(x[:3]) and min(x[:3]) < 235}, key=lambda c: -sum(c))
    return [list(cols[0]), list(cols[-1])] if len(cols) >= 2 else None


def fit_sketch(t, sketch):
    """밑그림 실루엣에 맞추기: 받은 그림 칸 배열을 밑그림 크기로 맞춘 뒤, 실루엣 밖 칸은 지우고 안쪽 빈 곳은 밝은 톤으로.
    → (새 배열, 실루엣 일치율 % = 겹친 칸 / (그림 ∪ 밑그림))"""
    a = np.asarray(Image.open(sketch).convert('L')) < 235
    ys, xs = np.where(a); S = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = S.shape; th, tw = t.shape
    yi = np.minimum((np.arange(h) * th / h).astype(int), th - 1); xi = np.minimum((np.arange(w) * tw / w).astype(int), tw - 1)
    r = t[yi][:, xi]; T = r >= 0
    rate = 100.0 * (T & S).sum() / max(1, (T | S).sum())
    r[~S] = -1; r[S & ~T] = 1
    p = np.pad(S, 1); r[S & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])] = 3
    return r, rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('id')
    ap.add_argument('--side', choices=['f', 'b', 'sheet'], default='f')
    ap.add_argument('--grade'); ap.add_argument('--flat', action='store_true')
    ap.add_argument('--pal', nargs=2, help='몸 색 두 개 예: 232,96,48 136,96,176')
    ap.add_argument('--sketch', help='밑그림 png (tools/lcd2sketch.py → art/sketch/<id>.png). 앞모습을 그 실루엣에 맞추고 일치율을 알림')
    a = ap.parse_args()
    sp = specs.by_id(a.id) or {}
    grade = a.grade or sp.get('grade') or '성숙기'
    pal = [tuple(int(v) for v in x.split(',')) for x in a.pal] if a.pal else sp.get('pal')
    if pal is None: raise SystemExit('specs.py 에 %s 가 없음: --pal 로 몸 색 두 개를 알려 주세요' % a.id)
    im = Image.open(a.src)
    tag = {'f': '-f', 'b': '-b', 'sheet': ''}[a.side]
    keep = os.path.join(WEB, 'art', 'src', a.id + tag + '_ai' + os.path.splitext(a.src)[1])
    if os.path.abspath(a.src) != os.path.abspath(keep): shutil.copy(a.src, keep)
    parts = list(zip(split(im), ('f', 'b'))) if a.side == 'sheet' else [(im, a.side)]
    body = front_colors(a.id) if a.side == 'b' else None
    for part, side in parts:
        maxs = FRONT.get(grade, 56) if side == 'f' else 48
        t, p4 = convert(part, maxs, pal, a.flat, body)
        if a.sketch and side == 'f':
            t, rate = fit_sketch(t, a.sketch)
            print('  실루엣 일치율 %.0f%%%s' % (rate, '' if rate >= 80 else '  → 80% 아래: 다시 받기'))
        t, nfix = apply_fix(t, os.path.join(WEB, 'art', 'fix', '%s-%s.txt' % (a.id, side)))
        if nfix: print('  손질 %d칸 (art/fix/%s-%s.txt)' % (nfix, a.id, side))
        body = [list(p4[1]), list(p4[2])]                           # 롬은 앞·뒤가 팔레트 하나 → 뒷모습은 앞모습 몸 색으로
        snapc.to_image(t, p4).save(os.path.join(WEB, 'art', '%s-%s.png' % (a.id, side)))
        snapc.to_image(t, p4, 6, (248, 248, 248)).save(os.path.join(WEB, 'art', '_%s-%s_x6.png' % (a.id, side)))
        print(side, '→', t.shape[::-1], '색', p4[1:3])


if __name__ == '__main__':
    main()
