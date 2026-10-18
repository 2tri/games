#!/usr/bin/env python3
"""디지몬 월드 Dawn/Dusk 걷기 그림(MCHR PAK)을 번호표(ds_추출/dawn_번호표.tsv)대로 뽑아 dsw_ow\ 에 저장 (2026-10-16, Claude 작성)
번호표 줄: 우리 종 \t MCHR 번호(10진) \t 근거. 결과 파일 이름은 DS 월드판과 같은 꼴(<영문 id>-dsw-ow.png), 이름표.tsv 에는 줄을 더함(「Dawn」 표시)."""
import os, sys, re, json, struct, csv, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import ds_mchr, hg1
import importlib.util as _u
_s = _u.spec_from_file_location("dsm2", os.path.join(HERE, "ds_dsw_make2.py")); _m = _u.module_from_spec(_s); _s.loader.exec_module(_m); walk_groups = _m.walk_groups
from PIL import Image, ImageOps
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default='dsw_ow'); ap.add_argument('--table', default=os.path.join(HERE, 'dawn_번호표.tsv'))
ap.add_argument('--design', default=os.path.join(HERE, '..', 'design.json'))
A = ap.parse_args()
rom = hg1.NDS(open(A.rom, 'rb').read())
def pak(name):
    d = rom.get('dat/%s.PAK' % name); n = struct.unpack_from('<I', d, 0)[0]
    ents = [struct.unpack_from('<II', d, 4 + 8 * i) for i in range(n)]
    return [d[off:(ents[i + 1][0] if i + 1 < n else len(d))] for i, (off, sz) in enumerate(ents)]
def dec(b): return ds_mchr.rle(b) if b and b[0] == 0x30 else b
CH, PL, AN = pak('MCHR_CHR'), pak('MCHR_PAL'), pak('MCHR_ANM')
design = json.load(open(A.design, encoding='utf-8')); en = {s['ko']: s['en'] for s in design['species']}
rows = [r for r in csv.reader(open(A.table, encoding='utf-8'), delimiter=chr(9))][1:]
new = []; done = 0
for ko, num, why in rows:
    i = int(num)
    x = dec(CH[i]); c, s = struct.unpack_from('<II', x, 0)
    fr = [x[8 + k * s:8 + (k + 1) * s] for k in range(c)]; cols = ds_mchr.palette(PL[i]); tw = ds_mchr.tiles_wide(s, 'tall')
    ims = [ds_mchr.frame_image(f, cols, tw) for f in fr]
    g = walk_groups(dec(AN[i]) or b'')
    seqs = []
    for grp in g[:8]:
        if len(grp) == 4 and grp not in seqs: seqs.append(grp)
    if len(seqs) < 2: print('걷기 묶음을 못 읽음:', ko, i, '컷', len(fr), '묶음', [len(x_) for x_ in g][:10]); continue
    A_, B_ = seqs[0], seqs[1]
    single = [grp for grp in g[8:] if len(grp) == 1]
    fc = single[0][0] if single else B_[0]
    def pick(k): return ims[k] if k < len(ims) else ims[0]
    rws = [(fc, fc + 1 if fc + 1 < len(ims) else fc), (A_[0], A_[1]), (B_[0], B_[1]), None]
    w, h = ims[0].size
    sheet = Image.new('RGBA', (2 * w + 4, 4 * h + 12), (0, 0, 0, 0))
    for r in range(4):
        for ci in range(2):
            im = pick(rws[r][ci]) if r < 3 else ImageOps.mirror(pick(rws[2][ci]))
            sheet.alpha_composite(im, (ci * (w + 4), r * (h + 4)))
    e = en.get(ko, '')
    fname = (re.sub(r'[^a-z0-9]+', '-', e.lower()).strip('-') + '-dsw-ow.png') if e else (ko + '_DSW걷기.png')
    sheet.save(os.path.join(A.out, fname)); done += 1
    new.append(chr(9).join((ko, 'Dawn%d' % i, '', '%d컷 %dx%d' % (len(fr), w, h), '상', 'Dawn/Dusk MCHR ' + str(i) + ' / ' + why + ' / 아래=컷 %d·위=컷 %s·옆=컷 %s' % (fc, A_[:2], B_[:2]))))
tp = os.path.join(A.out, '이름표.tsv')
old = [l for l in open(tp, encoding='utf-8').read().split(chr(10)) if l and not l.startswith(tuple(ko + chr(9) for ko, _, _ in rows))]
open(tp, 'w', encoding='utf-8', newline=chr(10)).write(chr(10).join(old + new) + chr(10))
print('Dawn 에서 저장 %d / %d' % (done, len(rows)))
