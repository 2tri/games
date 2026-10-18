#!/usr/bin/env python3
"""디지몬 월드 DS MCHR 큰 모음 — 번호(16진)마다 컷 0·3 을 3배로 (2026-10-16, Claude 작성)
사용: python ds_추출/atlas2.py "<DS 롬>" --lo 0x20 --hi 0x160 --out ds_추출/atlas"""
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1, ds_mchr
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--lo', default='0x20'); ap.add_argument('--hi', default='0x160'); ap.add_argument('--out', default='ds_추출/atlas'); ap.add_argument('--per', type=int, default=48); ap.add_argument('--cols', type=int, default=8)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
rom = hg1.NDS(open(A.rom, 'rb').read()); lo, hi = int(A.lo, 16), int(A.hi, 16)
ids = sorted({p.split('/')[-1][:-1] for p in rom.paths if p.startswith('dat/MCHR/') and p[-1] == 'c'}, key=lambda s: int(s, 16))
ids = [n for n in ids if all(ch in '0123456789abcdefABCDEF' for ch in n) and lo <= int(n, 16) <= hi]
BG = (40, 60, 90, 255); S = 3
cells = []
for n in ids:
    try:
        fr, size = ds_mchr.frames(rom.get('dat/MCHR/%sc' % n)); cols = ds_mchr.palette(rom.get('dat/MCHR/%sp' % n))
    except Exception: continue
    if not fr: continue
    tw = ds_mchr.tiles_wide(size, 'tall')
    pick = [0, 3] if len(fr) > 3 else [0]
    ims = [ds_mchr.frame_image(fr[k], cols, tw) for k in pick]
    cells.append((n, len(fr), ims))
cw, ch = 2 * 32 * S + 10, 64 * S + 16
for pg in range(0, len(cells), A.per):
    rows = (min(A.per, len(cells) - pg) + A.cols - 1) // A.cols
    page = Image.new('RGBA', (A.cols * cw, rows * ch), (20, 20, 20, 255)); dr = ImageDraw.Draw(page)
    for k, (n, nc, ims) in enumerate(cells[pg:pg + A.per]):
        x0, y0 = (k % A.cols) * cw, (k // A.cols) * ch
        dr.rectangle([x0, y0 + 14, x0 + cw - 3, y0 + ch - 2], fill=BG)
        dr.text((x0 + 2, y0 + 1), '%s (%d컷)' % (n.upper(), nc), fill=(255, 255, 0, 255))
        for j, im in enumerate(ims):
            im = im.resize((im.width * S, im.height * S), Image.NEAREST)
            page.alpha_composite(im, (x0 + j * 32 * S + 2, y0 + 15 + max(0, 64 * S - im.height)))
    page.save(os.path.join(A.out, '큰모음_%02d.png' % (pg // A.per + 1)))
print('마리', len(cells), '장', (len(cells) + A.per - 1) // A.per)
