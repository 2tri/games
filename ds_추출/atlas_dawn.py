#!/usr/bin/env python3
"""Digimon World Dawn/Dusk 의 MCHR PAK(MCHR_CHR·MCHR_PAL) 큰 모음 — 번호마다 컷 3(없으면 0)을 3배로 (2026-10-16, Claude 작성)
사용: python ds_추출/atlas_dawn.py "<Dawn 롬>" --lo 0 --hi 120 --out ds_추출/atlas_dawn [--palshift N]"""
import os, sys, struct, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1, ds_mchr
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--lo', type=int, default=0); ap.add_argument('--hi', type=int, default=120); ap.add_argument('--out', default='ds_추출/atlas_dawn')
ap.add_argument('--per', type=int, default=40); ap.add_argument('--cols', type=int, default=10); ap.add_argument('--palshift', type=int, default=0)
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
rom = hg1.NDS(open(A.rom, 'rb').read())
def pak(name):
    d = rom.get('dat/%s.PAK' % name); n = struct.unpack_from('<I', d, 0)[0]
    ents = [struct.unpack_from('<II', d, 4 + 8 * i) for i in range(n)]
    return [d[off:(ents[i + 1][0] if i + 1 < n else len(d))] for i, (off, sz) in enumerate(ents)]
def dec(b): return ds_mchr.rle(b) if b and b[0] == 0x30 else b
CH = pak('MCHR_CHR'); PL = pak('MCHR_PAL')
S = 2; cw, ch = 32 * S + 6, 64 * S + 16
cells = []
for i in range(A.lo, min(A.hi, len(CH))):
    x = dec(CH[i])
    if len(x) < 8: continue
    c, s = struct.unpack_from('<II', x, 0)
    if c == 0 or 8 + c * s != len(x): continue
    fr = [x[8 + k * s:8 + (k + 1) * s] for k in range(c)]
    j = i + A.palshift
    cols = ds_mchr.palette(PL[j]) if 0 <= j < len(PL) else [(255, 0, 255)] * 16
    tw = ds_mchr.tiles_wide(s, 'tall')
    im = ds_mchr.frame_image(fr[3 if c > 3 else 0], cols, tw)
    cells.append((i, c, s, im))
for pg in range(0, len(cells), A.per):
    ch_ = cells[pg:pg + A.per]; rows = (len(ch_) + A.cols - 1) // A.cols
    page = Image.new('RGBA', (A.cols * cw, rows * ch), (20, 20, 20, 255)); dr = ImageDraw.Draw(page)
    for k, (i, c, s, im) in enumerate(ch_):
        x0, y0 = (k % A.cols) * cw, (k // A.cols) * ch
        dr.rectangle([x0, y0 + 14, x0 + cw - 3, y0 + ch - 2], fill=(40, 60, 90, 255))
        dr.text((x0 + 2, y0 + 1), '%d (%d컷,%d)' % (i, c, s), fill=(255, 255, 0, 255))
        im = im.resize((im.width * S, im.height * S), Image.NEAREST)
        page.alpha_composite(im, (x0 + 2, y0 + 15 + max(0, 64 * S - im.height)))
    page.save(os.path.join(A.out, 'p_%04d.png' % (A.lo + pg)))
print('칸', len(cells), 'CH', len(CH), 'PL', len(PL))
