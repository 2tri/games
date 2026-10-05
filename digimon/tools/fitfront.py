"""앞모습이 칸에 비해 작아 보이는 종을 키우기 (2026-10-05 사용자: 「세라피몬·켄터스몬처럼 원본 대비 작은 애들은 알아서 키워 — 공통 사항」)
    python3 fitfront.py            → 후보와 결과 미리보기 art/src/fitfront/_compare.png (art/ 은 안 건드림)
    python3 fitfront.py --install  → art/<id>-f.png 를 키운 것으로 (원래 것은 art/src/fitfront/<id>-f_orig.png)
규칙: 칸 크기(유년기 40·성장기 48·그 위 56) 대비 그림 칸 비율 fill 이 기준(MIN_FILL)보다 작고, 세로로 길쭉해서(가로 < 칸) 키울 여지가 있으면
      아래(다리·옷자락)를 최대 MAX_CUT 까지 잘라 가로세로를 맞춘 뒤 칸 높이로 키움 (enlarge14 — 4색 그대로, 검정 선 우선).
      유년기는 몸 전체가 보여야 하므로 안 함. 롬 세션의 확대(1.4 그림)와 같은 방식."""
import argparse, glob, json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import enlarge14 as E

SIZE = {'성장기': 48}
MIN_FILL = {'성장기': 0.36}; MIN_FILL_DEF = 0.37
MAX_CUT = 0.22                       # 아래로 최대 22% 까지만 자름 (발·옷자락 정도)
BABY = ('유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ')
SKIP = set()
STRICT = {'leomon'}                 # 손으로 칠한 검정·흰 자리까지 옮길 종 (레오몬 바지·갈기)                         # 사용자가 「그대로」라고 한 종
OUT = os.path.join(WEB, 'art', 'src', 'fitfront')


def grades():
    L = json.load(open(os.path.join(WEB, 'romhack', 'order', 'allmons.json')))
    return {x['id']: x['grade'] for x in L if x['id']}


def plan(did, grade):
    if grade in BABY or did in SKIP: return None
    p = os.path.join(WEB, 'art', did + '-f.png'); im = Image.open(p).convert('RGBA')
    a = np.asarray(im)[..., 3] > 128; size = SIZE.get(grade, 56)
    fill = a.sum() / size ** 2
    if fill >= MIN_FILL.get(grade, MIN_FILL_DEF): return None
    ys, xs = np.where(a); h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
    if w >= size - 2: return None                                    # 이미 가로가 꽉 참
    cut = min(MAX_CUT, max(0.0, 1 - w / (h * 0.92)))                # 가로:세로 ≈ 0.92 가 되게
    if cut < 0.06: return None
    return fill, cut, size


def make(did, cut, size):
    im = Image.open(os.path.join(WEB, 'art', did + '-f.png')).convert('RGBA')
    a = np.asarray(im); al = a[..., 3] > 128; ys = np.where(al.any(1))[0]
    y1 = ys.min() + int((ys.max() - ys.min() + 1) * (1 - cut))
    a, al = a[:y1], al[:y1]
    # 4색 번호: 0 흰(배경 포함)·1 밝은·2 어두운·3 검정 (enlarge14 와 같은 순서)
    cs = sorted({tuple(int(v) for v in c) for c in a[al][:, :3]}, key=lambda c: -sum(c))
    blk = min(cs, key=sum); wht = max(cs, key=sum) if max(sum(c) for c in cs) > 700 else (248, 248, 248)
    mid = [c for c in cs if c not in (blk, wht)][:2]
    cols = [wht] + (mid + mid[-1:] * 2)[:2] + [blk]
    t = np.zeros(al.shape, int)
    for i, c in enumerate(cols):
        if i: t[al & (a[..., :3] == c).all(-1)] = i
    r = E.enlarge(t, size, 'nearest')
    r = r[:size, :size]
    o = np.zeros(r.shape + (4,), np.uint8); pal = np.array([tuple(c) + (255,) for c in cols], np.uint8); o[r >= 0] = pal[r[r >= 0]]
    # 잘린 아래 줄의 검정 테두리 → 바로 위 색 (화면 아래로 이어지게)
    return Image.fromarray(o, 'RGBA')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--install', action='store_true'); ap.add_argument('--only'); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); G = grades(); done = []
    for p in sorted(glob.glob(os.path.join(WEB, 'art', '*-f.png'))):
        did = os.path.basename(p)[:-6]
        if a.only and did != a.only: continue
        if did not in G: continue
        r = plan(did, G[did])
        if not r: continue
        fill, cut, size = r
        new = refit(did, cut, size, strict=did in STRICT)[0] if glob.glob(os.path.join(WEB, 'art', 'src', did + '-f_ai.*')) else make(did, cut, size)   # 원본이 있으면 원본에서 다시 (키우면 뭉개짐)
        nf = (np.asarray(new)[..., 3] > 128).sum() / size ** 2
        print('%-24s %-4s fill %.2f → %.2f (아래 %d%% 자름)' % (did, G[did], fill, nf, cut * 100))
        if a.install:
            Image.open(p).save(os.path.join(OUT, did + '-f_orig.png')); new.save(p)
        done.append((did, Image.open(os.path.join(OUT, did + '-f_orig.png')) if a.install else Image.open(p), new))
    if done:
        from PIL import ImageDraw
        cols = 4; cw = 2 * 175 + 20; ch = 195; rows = (len(done) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cw, rows * ch), (232, 240, 232)); d = ImageDraw.Draw(sh)
        for i, (did, o, n) in enumerate(done):
            x, y = (i % cols) * cw, (i // cols) * ch
            for j, im in enumerate((o.convert('RGBA'), n)):
                box = Image.new('RGBA', (168, 168), 'white'); b = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
                box.alpha_composite(b, ((168 - b.width) // 2, 168 - b.height)); sh.paste(box, (x + 4 + j * 175, y + 20))
            d.text((x + 4, y + 4), '%s (before | after)' % did, fill=(0, 0, 0))
        sh.save(os.path.join(OUT, '_compare.png')); print('→', os.path.join(OUT, '_compare.png'))


if __name__ == '__main__':
    main()


# 2026-10-05 사용자: 「억지로 키워서 뭉개짐 — 내가 준 이미지 그대로 넣으면 괜찮지 않았나」
# → 작은 도트 그림을 키우지 않고, 받은 원본(art/src/<id>-f_ai)에서 아래를 잘라 그 크기로 바로 도트화. 색은 원래 art 의 같은 자리 색을 옮김(손본 색 유지)
def refit(did, cut, size, strict=False):
    """strict=True: 옛 그림에서 손으로 칠한 검정·흰 자리 색까지 옮김(레오몬 바지·갈기). 기본은 몸 색만"""
    sys.path.insert(0, os.path.join(WEB, 'romhack'))
    import ingest, snapc
    orig = os.path.join(OUT, did + '-f_orig.png')
    if not os.path.exists(orig): orig = os.path.join(WEB, 'art', did + '-f.png')
    o = np.asarray(Image.open(orig).convert('RGBA'))
    src = next(iter(glob.glob(os.path.join(WEB, 'art', 'src', did + '-f_ai.*'))))
    im = Image.open(src).convert('RGB'); g = np.asarray(im.convert('L')).astype(int)
    ys, xs = np.where(g < 235); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    part = im.crop((max(0, x0 - 4), max(0, y0 - 4), min(im.width, x1 + 4), y0 + int((y1 - y0) * (1 - cut))))
    oc = [c for c in {tuple(int(v) for v in p[:3]) for p in o.reshape(-1, 4) if p[3] > 128} if 40 < max(c) and min(c) < 235]
    oc = sorted(oc, key=lambda c: -sum(c)); pal = [list(oc[0]), list(oc[-1])] if len(oc) >= 2 else [list(oc[0])] * 2
    t, p4 = ingest.convert(part, size, pal, False, pal)
    new = np.asarray(snapc.to_image(t, p4).convert('RGBA')).copy()
    # 원래 art 의 위쪽(1-cut) 부분과 자리 맞추기 (가로 뒤집힘도 확인)
    oa = o[..., 3] > 128; oys, oxs = np.where(oa); oy0, oy1, ox0, ox1 = oys.min(), oys.max() + 1, oxs.min(), oxs.max() + 1
    oy1 = oy0 + int((oy1 - oy0) * (1 - cut))
    na = new[..., 3] > 128; nys, nxs = np.where(na); ny0, ny1, nx0, nx1 = nys.min(), nys.max() + 1, nxs.min(), nxs.max() + 1
    def look(flip):
        yy = oy0 + ((np.arange(new.shape[0]) - ny0) * (oy1 - oy0) / max(1, ny1 - ny0)).astype(int)
        xx = ((np.arange(new.shape[1]) - nx0) * (ox1 - ox0) / max(1, nx1 - nx0)).astype(int)
        xx = (ox1 - 1 - xx) if flip else (ox0 + xx)
        return np.clip(yy, 0, o.shape[0] - 1), np.clip(xx, 0, o.shape[1] - 1)
    best = None
    for flip in (False, True):
        yy, xx = look(flip); m = oa[yy][:, xx]; s = (m & na).sum() / max(1, (m | na).sum())
        if best is None or s > best[0]: best = (s, flip)
    if best[1]: new = new[:, ::-1].copy(); na = new[..., 3] > 128; nys, nxs = np.where(na); nx0, nx1 = nxs.min(), nxs.max() + 1
    yy, xx = look(False)
    blk = (new[..., :3].astype(int).sum(-1) < 120)
    from collections import Counter
    for y in range(new.shape[0]):
        for x in range(new.shape[1]):
            if not na[y, x] or blk[y, x]: continue
            Y, X = yy[y], xx[x]
            nb = [tuple(int(v) for v in o[min(max(Y + dy, 0), o.shape[0] - 1), min(max(X + dx, 0), o.shape[1] - 1), :3])
                  for dy in (-1, 0, 1) for dx in (-1, 0, 1) if o[min(max(Y + dy, 0), o.shape[0] - 1), min(max(X + dx, 0), o.shape[1] - 1), 3] > 128]
            if not nb: continue
            cnt = Counter(nb); k = sum(cnt.values())
            dark = [c for c in cnt if sum(c) < 120]
            if strict and dark and cnt[dark[0]] >= 6: new[y, x, :3] = dark[0]; continue    # 옛 그림에서 검게 칠한 곳(레오몬 바지)
            body = [(c, n) for c, n in cnt.most_common() if sum(c) >= 120]
            if not body: continue
            c0 = body[0][0]
            white_new = min(new[y, x, :3]) > 235
            if white_new and not strict: continue
            if white_new and min(c0) > 235: continue                    # 흰 곳은 흰색
            if white_new and body[0][1] < 5: continue
            new[y, x, :3] = c0
    return Image.fromarray(new), best[0]
