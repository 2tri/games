#!/usr/bin/env python3
"""못 구한 우리 종마다 Dawn/Dusk MCHR 중 색이 비슷한 후보 8개를 비교판으로 (2026-10-16, Claude 작성) — 눈으로 고르는 보조
사용: python ds_추출/dawn_match.py "<Dawn 롬>" 종,종,… --out 폴더 [--lo 114 --hi 548]"""
import os, sys, struct, argparse, colorsys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1, ds_mchr
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('names'); ap.add_argument('--out', default='_scratch/dawn_cand'); ap.add_argument('--lo', type=int, default=114); ap.add_argument('--hi', type=int, default=548); ap.add_argument('--k', type=int, default=8)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
rom = hg1.NDS(open(A.rom, 'rb').read())
def pak(name):
    d = rom.get('dat/%s.PAK' % name); n = struct.unpack_from('<I', d, 0)[0]
    ents = [struct.unpack_from('<II', d, 4 + 8 * i) for i in range(n)]
    return [d[off:(ents[i + 1][0] if i + 1 < n else len(d))] for i, (off, sz) in enumerate(ents)]
def dec(b): return ds_mchr.rle(b) if b and b[0] == 0x30 else b
CH = pak('MCHR_CHR'); PL = pak('MCHR_PAL')
def hist(im):
    im = im.convert('RGBA'); h = [0.0] * (12 * 3 + 4); n = 0
    for r, g, b, a in im.getdata():
        if a < 128: continue
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); n += 1
        if vv < 0.2: h[36] += 1
        elif ss < 0.15: h[37 if vv > 0.7 else 38] += 1
        else: h[int(hh * 12) % 12 * 3 + (0 if vv < 0.5 else (1 if vv < 0.8 else 2))] += 1
    return [x / max(n, 1) for x in h], n
def aspect(im):
    bb = im.getchannel('A').point(lambda v: 255 if v >= 128 else 0).getbbox()
    return ((bb[2] - bb[0]) / max(1, bb[3] - bb[1])) if bb else 1
cands = []
for i in range(A.lo, min(A.hi, len(CH))):
    x = dec(CH[i])
    if len(x) < 8: continue
    c, s = struct.unpack_from('<II', x, 0)
    if c == 0 or 8 + c * s != len(x) or c < 6: continue
    fr = [x[8 + k * s:8 + (k + 1) * s] for k in range(c)]
    cols = ds_mchr.palette(PL[i]); tw = ds_mchr.tiles_wide(s, 'tall')
    im = ds_mchr.frame_image(fr[3 if c > 3 else 0], cols, tw)
    if im.getchannel('A').getbbox() is None: continue
    cands.append((i, im, hist(im)[0], aspect(im)))
try: font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)
except Exception: font = ImageFont.load_default()
S = 3; cw = 32 * S + 8; rh = 64 * S + 20
names = A.names.split(',')
for pg in range(0, len(names), 6):
    chunk = names[pg:pg + 6]
    page = Image.new('RGBA', (210 + A.k * cw, rh * len(chunk)), (24, 24, 24, 255)); dr = ImageDraw.Draw(page)
    for r, nm in enumerate(chunk):
        d = glob.glob('nds_art/*_' + nm)
        front = Image.open(os.path.join(d[0], 'front.png')).convert('RGBA')
        hf = hist(front)[0]; af = aspect(front); y0 = r * rh
        sc = sorted(((sum(min(a, b) for a, b in zip(hf, h2)) - 0.15 * abs(af - a2)), i) for i, im, h2, a2 in cands)[::-1][:A.k]
        dr.text((4, y0 + 2), nm, fill=(255, 255, 255, 255), font=font)
        f2 = front.resize((160, 160), Image.NEAREST); bg = Image.new('RGBA', f2.size, (60, 60, 70, 255)); bg.alpha_composite(f2); page.alpha_composite(bg, (4, y0 + 22))
        byi = {i: im for i, im, _, _ in cands}
        for j, (s_, i) in enumerate(sc):
            x0 = 200 + j * cw
            dr.rectangle([x0, y0 + 20, x0 + cw - 4, y0 + rh - 2], fill=(40, 60, 90, 255))
            dr.text((x0 + 2, y0 + 3), str(i), fill=(255, 255, 0, 255), font=font)
            im = byi[i].resize((byi[i].width * S, byi[i].height * S), Image.NEAREST); page.alpha_composite(im, (x0 + 2, y0 + 22 + max(0, 64 * S - im.height)))
    page.save(os.path.join(A.out, 'm%02d.png' % (pg // 6 + 1)))
print('저장', (len(names) + 5) // 6, '장')
