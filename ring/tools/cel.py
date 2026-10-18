#!/usr/bin/env python3
"""사진/원화 → 재질별 셀 도트 (게임보이 4단계)
1) 배경 제거 2) 머리 키우기(선택) 3) 색으로 재질 나누기 4) 칸마다 다수결로 재질 축소
5) 재질마다 정한 두 단계 명암(원본 밝기 기준) 6) 재질 경계·실루엣에 검은 선
"""
import numpy as np
from PIL import Image, ImageDraw
from pixelize import flood_bg

def load_rgba(path, tol=8):
    src = Image.open(path).convert('RGB')
    bg = flood_bg(np.asarray(src.convert('L')), True, tol)
    im = src.copy(); im.putalpha(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)))
    return im

def big_head(im, box, k, neck_y):
    """box 영역(머리)을 타원 마스크로 오려 k배로 키워 같은 자리에 덮는다. neck_y: 키운 머리 아래끝을 맞출 원본 y"""
    head = im.crop(box)
    m = Image.new('L', head.size, 0); ImageDraw.Draw(m).ellipse((0, 0, head.width - 1, head.height - 1), 255)
    head.putalpha(Image.fromarray(np.minimum(np.asarray(head.split()[3]), np.asarray(m))))
    head = head.resize((int(head.width * k), int(head.height * k)), Image.LANCZOS)
    top = max(0, head.height - neck_y) + 4
    W = max(im.width, head.width) + 8
    can = Image.new('RGBA', (W, im.height + top), (255, 255, 255, 0))
    ox = (W - im.width) // 2
    can.alpha_composite(im, (ox, top))
    cx = ox + (box[0] + box[2]) // 2
    can.alpha_composite(head, (cx - head.width // 2, top + neck_y - head.height))
    return can

def cel(im, classify, tones, size=56, order=None, keep_small=(), line_skip=(), feet=True):
    """classify(r,g,b,lum,y_frac)->재질번호, tones[재질]=(밝은톤, 어두운톤, 문턱 0~1)"""
    a = np.asarray(im.split()[3]) > 128
    rgb = np.asarray(im.convert('RGB')).astype(float)
    ys, xs = np.where(a); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = rgb[y0:y1, x0:x1]; a = a[y0:y1, x0:x1]
    h, w = a.shape
    lum = rgb @ [0.299, 0.587, 0.114]
    yf = np.repeat(np.arange(h)[:, None] / h, w, 1)
    lab = classify(rgb[..., 0], rgb[..., 1], rgb[..., 2], lum, yf)
    lab = np.where(a, lab, -1)
    sc = (size - 2) / max(h, w); tw, th = max(1, round(w * sc)), max(1, round(h * sc))
    out = -np.ones((th, tw), int); L = np.zeros((th, tw))
    for ty in range(th):
        for tx in range(tw):
            ya, yb = int(ty / sc), max(int(ty / sc) + 1, int((ty + 1) / sc)); xa, xb = int(tx / sc), max(int(tx / sc) + 1, int((tx + 1) / sc))
            cell = lab[ya:yb, xa:xb].ravel(); lc = lum[ya:yb, xa:xb].ravel()
            if (cell >= 0).mean() < 0.45: continue
            vals, cnt = np.unique(cell[cell >= 0], return_counts=True)
            best = vals[np.argmax(cnt)]
            for k in keep_small:          # 작은 재질(눈·손·칼자루)은 조금만 있어도 살림
                if k in vals and cnt[list(vals).index(k)] >= 0.22 * len(cell): best = k
            out[ty, tx] = best; L[ty, tx] = lc[cell == best].mean() / 255
    # 재질별 명암
    tone = -np.ones_like(out)
    for k, (lt, dk, thr) in tones.items():
        m = out == k
        if not m.any(): continue
        med = np.median(L[m]) if thr is None else thr
        tone[m] = np.where(L[m] >= med, lt, dk)
    # 재질 경계선: 이웃이 다른 재질이고, 이 칸이 '뒤쪽' 재질이면 검정
    depth = {k: i for i, k in enumerate(order or sorted(tones))}
    t2 = tone.copy()
    for y in range(th):
        for x in range(tw):
            k = out[y, x]
            if k < 0 or k in line_skip: continue
            for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= Y < th and 0 <= X < tw and out[Y, X] >= 0 and out[Y, X] != k and depth.get(out[Y, X], 0) > depth.get(k, 0):
                    t2[y, x] = 3; break
    res = -np.ones((size, size), int)
    oy = size - th - 1 if feet else (size - th) // 2; ox = (size - tw) // 2
    res[oy:oy + th, ox:ox + tw] = t2
    labs = -np.ones((size, size), int); labs[oy:oy + th, ox:ox + tw] = out
    o = res.copy()
    for y in range(size):
        for x in range(size):
            if res[y, x] >= 0: continue
            if any(0 <= y + dy < size and 0 <= x + dx < size and res[y + dy, x + dx] >= 0 for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y, x] = 3
    return o, labs
