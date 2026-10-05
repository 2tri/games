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
SKIP = set()                         # 사용자가 「그대로」라고 한 종
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
        fill, cut, size = r; new = make(did, cut, size)
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
