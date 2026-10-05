"""뒷모습을 「상반신만 크게」로 다시 만들기 (2026-10-05 사용자: 몸 전체가 나와 게임에서 너무 작음 → 상반신 정도만)
    python3 backcrop.py                 art/src/<id>-b_ai.* 가 있는 뒷모습 전부 → art/src/backcrop/<id>-b.png + _compare.png (art/ 은 안 건드림)
    python3 backcrop.py --install        위 결과를 art/<id>-b.png 로
    python3 backcrop.py --only chibimon --frac 0.55
받은 원본(art/src/<id>-b_ai)에서 그림 부분의 위쪽 frac 만 잘라(납작한 종 0.8, 나머지 0.6) 48칸에 맞춤 → 칸이 꽉 참.
잘린 아래 가장자리는 검은 테두리를 지움(금판 뒷모습처럼 화면 아래로 이어지게). 색은 지금 뒷모습의 몸 색 그대로,
지금 뒷모습이 좌우 뒤집혀 들어가 있으면(롬 세션이 뒤집은 것) 같게 뒤집음."""
import argparse, glob, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WEB, 'romhack')); sys.path.insert(0, HERE)
import ingest, snapc

OUT = os.path.join(WEB, 'art', 'src', 'backcrop')


def body_cols(path):
    a = np.asarray(Image.open(path).convert('RGBA')).reshape(-1, 4)
    cols = sorted({tuple(int(v) for v in x[:3]) for x in a if x[3] > 128 and 40 < max(x[:3]) and min(x[:3]) < 235}, key=lambda c: -sum(c))
    return [list(cols[0]), list(cols[-1])] if len(cols) >= 2 else None


def mask_of(t): return (t >= 0)


def iou(a, b):
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    a, b = a[:h, :w], b[:h, :w]; u = (a | b).sum()
    return (a & b).sum() / u if u else 0


SKIP = {'bakemon', 'salamon', 'tokomon', 'gomamon', 'metalgarurumon'}   # 다시 바꾸면 색·모양이 망가지는 것 (흰 몸·원본이 이미 납작) → 그대로


UPPER = {'metalseadramon', 'imperialdramondragonmode', 'andromon'}   # 이미 상반신으로 받은 것 → 자르지 않고 48칸에 맞춤만


BABY = {'chibimon', 'koromon', 'poromon'}   # 유년기: 자르지 않음 — 몸 전체 그대로(예전 그림, 2026-10-05 사용자 「작은 애들은 크기에 맞게」)
ROOKIE = {'agumon', 'gabumon', 'gazimon', 'gottsumon', 'palmon', 'patamon', 'piyomon', 'tentomon'}   # 성장기: 조금만 (위 80%, 창 1.6배)


def make(did, frac=None, ref=None, pal=None):
    if did in SKIP or did in BABY: return None
    src = next(iter(glob.glob(os.path.join(WEB, 'art', 'src', did + '-b_ai.*'))), None)
    cur = ref or os.path.join(WEB, 'art', did + '-b.png')
    if not src or not os.path.exists(cur): return None
    im = Image.open(src).convert('RGB'); a = np.asarray(im.convert('L')).astype(int)
    ys, xs = np.where(a < 235); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    if frac is None: frac = 1.0 if did in UPPER else (0.8 if did in ROOKIE or (y1 - y0) / (x1 - x0) < 0.9 else 0.6)
    yc = im.height if frac >= 1 else y0 + int((y1 - y0) * frac)
    # 가로도 정사각형 창으로 (금판 뒷모습처럼 크게 — 날개·꼬리 끝은 칸 밖으로 잘려도 됨). 창 가운데 = 잘린 부분의 무게중심
    hh = yc - y0; fgc = (a[y0:yc] < 235)
    cx = int(np.average(np.arange(a.shape[1]), weights=fgc.sum(0) + 1e-6)) if fgc.any() else (x0 + x1) // 2
    ww = max(int(hh * (1.6 if did in ROOKIE else 1.3)), 1)                                           # 1.0 이면 너무 확대(두리몬·포로몬), 1.3 = 어깨·날개 시작까지
    xa, xb = (max(0, cx - ww // 2), min(im.width, cx + ww // 2)) if (x1 - x0) > ww else (0, im.width)
    part = im.crop((xa, 0, xb, yc))
    pal = pal or body_cols(cur) or ingest.front_colors(did) or [[200, 200, 200], [120, 120, 120]]
    t, p4 = ingest.convert(part, 48, pal, False, pal)
    if max(t.shape) < 44: t, p4 = ingest.convert(part, 48, pal, True, pal)          # 원본 도트 칸이 작으면(포로몬 등) 격자 없이 48칸으로
    # 잘린 아래 줄: 검정 테두리 → 바로 위 칸 색
    h = t.shape[0]
    for x in range(t.shape[1]):
        if t[h - 1, x] == 3 and h > 1 and t[h - 2, x] in (0, 1, 2): t[h - 1, x] = t[h - 2, x]
    # 지금 그림이 뒤집혀 있으면 같게
    old = np.asarray(Image.open(cur).convert('RGBA'))[..., 3] > 128
    oh = max(1, int(old.shape[0] * frac)); old = old[:oh]
    new = mask_of(t)
    o = np.asarray(Image.fromarray(old.astype(np.uint8) * 255).resize(new.shape[::-1], Image.NEAREST)) > 0
    if iou(np.fliplr(new), o) > iou(new, o) + 0.05: t = np.fliplr(t)
    return t, p4, frac


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--frac', type=float); ap.add_argument('--install', action='store_true')
    a = ap.parse_args(); os.makedirs(OUT, exist_ok=True)
    ids = [os.path.basename(p)[:-6] for p in sorted(glob.glob(os.path.join(WEB, 'art', '*-b.png')))]
    done = []
    for did in ids:
        if a.only and did != a.only: continue
        if a.install:
            p = os.path.join(OUT, did + '-b.png')
            if os.path.exists(p): Image.open(p).save(os.path.join(WEB, 'art', did + '-b.png')); print('→ art/%s-b.png' % did)
            continue
        r = make(did, a.frac)
        if not r: continue
        t, p4, frac = r
        img = snapc.to_image(t, p4); img.save(os.path.join(OUT, did + '-b.png')); done.append((did, img, frac))
        print('%-16s frac %.2f → %dx%d' % (did, frac, img.width, img.height))
    if done:                                                          # 전·후 비교 (×3, 게임처럼 48칸 아래 맞춤)
        from PIL import ImageDraw
        cols = 6; cw = 2 * 150 + 20; ch = 170; rows = (len(done) + cols - 1) // cols
        sh = Image.new('RGB', (cols * cw, rows * ch), (232, 240, 232)); d = ImageDraw.Draw(sh)
        for i, (did, img, frac) in enumerate(done):
            x, y = (i % cols) * cw, (i // cols) * ch
            for j, im in enumerate((Image.open(os.path.join(WEB, 'art', did + '-b.png')).convert('RGBA'), img.convert('RGBA'))):
                box = Image.new('RGBA', (144, 144), (255, 255, 255, 255)); big = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
                box.alpha_composite(big, ((144 - big.width) // 2, 144 - big.height)); sh.paste(box, (x + 4 + j * 150, y + 18))
            d.text((x + 4, y + 2), '%s  (전 | 후)' % did, fill=(0, 0, 0))
        sh.save(os.path.join(OUT, '_compare.png')); print('→', os.path.join(OUT, '_compare.png'))


if __name__ == '__main__':
    main()
