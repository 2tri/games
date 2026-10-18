#!/usr/bin/env python3
"""전투 앞·뒷모습 다시 줄이기 — art_nds 가 큰 원본을 80x80 으로 줄일 때 뭉개진 종을 원본에서 다시 만든다. (Claude 작성, 2026-10-15)
사용:   python art_sharpen.py --src 머미몬=games/images/digimon/mummymon-ds-f.png [--src 아마게몬=...] [--side front|back] [--out nds_art] [--preview 폴더]
방법:   nds_art/<번호>_<이름>/front.png 의 불투명 상자(위치·크기)는 그대로 두고, 그 상자 안을 원본(투명 배경 또는 밝은 배경)에서
        ① 배경 지움(가장자리와 이어진 밝은 색) ② 불투명 상자만 잘라 ③ 면적 평균(BOX→LANCZOS)으로 줄임 ④ 알파 128 기준 ⑤ 15색(+투명 0번) 중간값 자르기, 디더 없음
        (art_nds 는 가장 가까운 이웃으로 줄여 가는 선이 끊김). 원래 front.png 는 front_옛.png 로 보관."""
import sys, os, argparse, glob
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('--src', action='append', default=[]); ap.add_argument('--side', default='front')
ap.add_argument('--out', default='nds_art'); ap.add_argument('--preview', default=None)
A = ap.parse_args()

def key_bg(im):
    im = im.convert('RGBA'); w, h = im.size; px = im.load()
    if any(px[x, y][3] < 128 for x in range(w) for y in (0, h - 1)) or im.getchannel('A').getextrema()[0] < 255: return im
    def isbg(p): return min(p[:3]) >= 200 and max(p[:3]) - min(p[:3]) <= 30
    seen = set(); st = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not isbg(px[x, y]): continue
        seen.add((x, y)); px[x, y] = (0, 0, 0, 0); st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im

def bbox_of(im):
    a = im.getchannel('A').point(lambda v: 255 if v >= 128 else 0); return a.getbbox()

for item in A.src:
    name, path = item.split('=', 1)
    d = [x for x in glob.glob(os.path.join(A.out, '*_' + name)) if os.path.isdir(x)]
    if not d: print('폴더 없음', name); continue
    d = d[0]; tgt = os.path.join(d, A.side + '.png')
    keep0 = os.path.join(d, A.side + '_옛.png')
    old = Image.open(keep0 if os.path.exists(keep0) else tgt).convert('RGBA'); ob = bbox_of(old)
    if ob is None: print('빈 그림', name); continue
    src = key_bg(Image.open(path)); sb = bbox_of(src)
    crop = src.crop(sb); tw, th = ob[2] - ob[0], ob[3] - ob[1]
    # 비율 유지: 상자 안에 넣고 가운데·아래 맞춤
    r = min(tw / crop.width, th / crop.height); nw, nh = max(1, round(crop.width * r)), max(1, round(crop.height * r))
    # 원본을 먼저 15색으로 줄이고(색이 번지지 않게), 목표 칸마다 원본 칸들의 「가장 많은 색」을 고름(다수결) → 선·색이 또렷
    a = crop.getchannel('A'); rgb = Image.new('RGB', crop.size, (0, 0, 0)); rgb.paste(crop.convert('RGB'), (0, 0), a)
    flat = Image.new('RGB', crop.size, (0, 0, 0)); flat.paste(rgb, (0, 0), a.point(lambda v: 255 if v >= 128 else 0))
    # 앞·뒤가 한 팔레트(16색)를 같이 쓰므로 art_nds 가 이미 만든 앞·뒷모습의 색 모음을 그대로 쓰고, 원본 색은 가장 가까운 그 색으로(10/16: 따로 줄이면 합친 색이 16 을 넘어 hg4 가 28% 를 다른 색으로 바꿈)
    pal_cols = []
    for nm_ in ('front', 'back'):
        pth = os.path.join(d, nm_ + '_옛.png')
        if not os.path.exists(pth): pth = os.path.join(d, nm_ + '.png')
        for r_, g_, b_, a_ in Image.open(pth).convert('RGBA').getdata():
            if a_ >= 128 and (r_, g_, b_) not in pal_cols: pal_cols.append((r_, g_, b_))
    cols = pal_cols[:15] if pal_cols else [(1, 1, 1)]
    near = {}
    def nearest(c):
        if c not in near: near[c] = min(range(len(cols)), key=lambda i: (cols[i][0] - c[0]) ** 2 + (cols[i][1] - c[1]) ** 2 + (cols[i][2] - c[2]) ** 2)
        return near[c]
    q = Image.new('P', flat.size); qp = q.load(); fp_ = flat.load()
    for yy in range(flat.height):
        for xx in range(flat.width): qp[xx, yy] = nearest(fp_[xx, yy])
    qa = a.load(); qi = q.load(); sw, sh = crop.size
    canvas = Image.new('RGBA', old.size, (0, 0, 0, 0)); ox = ob[0] + (tw - nw) // 2; oy = ob[3] - nh
    import collections
    for y in range(nh):
        y0, y1 = int(y * sh / nh), max(int(y * sh / nh) + 1, int((y + 1) * sh / nh))
        for x in range(nw):
            x0, x1 = int(x * sw / nw), max(int(x * sw / nw) + 1, int((x + 1) * sw / nw))
            cnt = collections.Counter(); opq = 0; tot = 0
            for yy in range(y0, min(y1, sh)):
                for xx in range(x0, min(x1, sw)):
                    tot += 1
                    if qa[xx, yy] >= 128: opq += 1; cnt[qi[xx, yy]] += 1
            if tot and opq * 2 >= tot and cnt:
                canvas.putpixel((ox + x, oy + y), cols[cnt.most_common(1)[0][0]] + (255,))
    # 검정 불투명은 (1,1,1) 로(hg4 의 번호 밀림 버그 우회)
    px = canvas.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            p = px[x, y]
            if p[3] and p[:3] == (0, 0, 0): px[x, y] = (1, 1, 1, 255)
    keep = os.path.join(d, A.side + '_옛.png')
    if not os.path.exists(keep): old.save(keep)
    # P 모드로 저장(0번 투명)
    pimg = canvas.convert('RGB').quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) if False else None
    canvas.save(tgt)
    print('다시 만듦', name, A.side, '상자', ob, '→', (ox, oy, nw, nh))
    if A.preview:
        os.makedirs(A.preview, exist_ok=True)
        s = Image.new('RGB', (80 * 2 * 2 + 12, 160), (190, 190, 200))
        for i, im in enumerate((old, canvas)):
            t = Image.new('RGBA', im.size, (190, 190, 200, 255)); t.paste(im, (0, 0), im); s.paste(t.convert('RGB').resize((160, 160), Image.NEAREST), (i * 172, 0))
        s.save(os.path.join(A.preview, '%s_%s_비교.png' % (name, A.side)))
