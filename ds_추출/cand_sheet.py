#!/usr/bin/env python3
"""우리 종 앞모습 + DS 걷기 후보(번호 ±3) 비교판 (2026-10-16, Claude 작성)
사용: python ds_추출/cand_sheet.py "<DS 롬>" 종이름[,종이름…] --out 파일.png [--span 3] [--base 이름표.tsv의 번호 쓰기 | --hex 번호]"""
import os, sys, csv, argparse, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1, ds_mchr
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('names'); ap.add_argument('--out', default='ds_추출/cand.png'); ap.add_argument('--span', type=int, default=3)
ap.add_argument('--hex', default=None, help='종=번호,종=번호 (이름표 대신 이 번호 중심)')
A = ap.parse_args()
rom = hg1.NDS(open(A.rom, 'rb').read())
tab = {r[0]: r for r in list(csv.reader(open('dsw_ow/이름표.tsv', encoding='utf-8'), delimiter='\t'))[1:]}
over = dict(x.split('=') for x in A.hex.split(',')) if A.hex else {}
try: font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 14)
except Exception: font = ImageFont.load_default()
S = 3; rows = []
for nm in A.names.split(','):
    cen = over.get(nm) or (tab.get(nm, [None, ''])[1] or '').strip()
    dirs = glob.glob('nds_art/*_' + nm)
    front = Image.open(os.path.join(dirs[0], 'front.png')).convert('RGBA') if dirs else None
    cands = []
    if cen:
        c = int(cen, 16)
        for k in range(c - A.span, c + A.span + 1):
            h = '%X' % k
            try:
                fr, size = ds_mchr.frames(rom.get('dat/MCHR/%sc' % h)); cols = ds_mchr.palette(rom.get('dat/MCHR/%sp' % h))
            except Exception: continue
            if not fr: continue
            tw = ds_mchr.tiles_wide(size, 'tall')
            im = ds_mchr.frame_image(fr[3 if len(fr) > 3 else 0], cols, tw)
            cands.append((h, k == c, im))
    rows.append((nm, front, cands, tab.get(nm, ['', '', '', '', '', ''])))
cw = 32 * S + 8; rh = 64 * S + 20; W = 90 + 200 + (2 * A.span + 1) * cw
page = Image.new('RGBA', (W, rh * len(rows)), (24, 24, 24, 255)); dr = ImageDraw.Draw(page)
for r, (nm, front, cands, t) in enumerate(rows):
    y0 = r * rh
    dr.text((4, y0 + 2), nm + ' (' + (t[2] or '-') + ')', fill=(255, 255, 255, 255), font=font)
    if front: page.alpha_composite(front.resize((160, 160), Image.NEAREST) if False else front.resize((80 * 2, 80 * 2), Image.NEAREST).crop((0, 0, 160, 160)), (0, y0 + 24)) if False else None
    if front:
        fr2 = front.resize((160, 160), Image.NEAREST); bg = Image.new('RGBA', fr2.size, (60, 60, 70, 255)); bg.alpha_composite(fr2); page.alpha_composite(bg, (4, y0 + 22))
    for j, (h, mid, im) in enumerate(cands):
        x0 = 200 + j * cw
        dr.rectangle([x0, y0 + 20, x0 + cw - 4, y0 + rh - 2], fill=(40, 60, 90, 255) if not mid else (70, 90, 50, 255))
        dr.text((x0 + 2, y0 + 3), h + (' *' if mid else ''), fill=(255, 255, 0, 255), font=font)
        im = im.resize((im.width * S, im.height * S), Image.NEAREST)
        page.alpha_composite(im, (x0 + 2, y0 + 22 + max(0, 64 * S - im.height)))
page.save(A.out); print('저장', A.out, len(rows))
