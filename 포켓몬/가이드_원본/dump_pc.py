# -*- coding: utf-8 -*-
"""python dump_pc.py <롬.nds> — Windows 용: 롬에서 트레이너 파티(trainers.json)·이름(trnames.json)을 다시 뽑는다 (2026-10-28, 2부 공략집용)
dump.py 는 옛 리눅스 경로 판이라 따로 만듦. 종 이름 = 글 233, 기술 이름 = 글 묶음에서 hg2.find_table 로 찾은 표."""
import os, sys, csv, json, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, ROOT)
import hg1, hg2
from hg1 import NDS, NARC, msg_decode
OUT = os.path.dirname(os.path.abspath(__file__))
rom = NDS(open(sys.argv[1], 'rb').read())
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
N = NARC(rom.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in N.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM, _, _ = hg1.infer_charmap(MSG, draft)
clean = lambda s: re.sub(r'\{01DE\}', ' ', CM.dec(s)).strip()
SPN = [clean(e) for e in MSG[233][1]]
mv = hg2.find_table(MSG, CM, ['몸통박치기', '할퀴기'], (400, 600)) or hg2.find_table(MSG, CM, ['태클', '클로어택'], (400, 600))
MOVES = [re.sub(r'\{01DE\}', ' ', m) for m in mv[1]]
learn = NARC(rom.get(hg1.NARC_PATHS['learn'])).files
td = NARC(rom.get(hg1.NARC_PATHS['trdata'])); tp = NARC(rom.get(hg1.NARC_PATHS['trpoke']))
def moves_at(sp, lv):
    out = []
    for l, m in hg1.learnset(learn[sp]):
        if l <= lv:
            if m in out: out.remove(m)
            out.append(m)
    return out[-4:]
trainers = {}
for i in range(len(td.files)):
    d = hg1.trdata(td.files[i])
    if not d or not d['n']: continue
    pk, size = hg1.trpoke(tp.files[i], d['flags'], d['n'])
    if not pk: continue
    trainers[i] = [{'sp': SPN[m['sp']], 'lv': m['lv'], 'moves': [MOVES[x] for x in (m['moves'] if m['moves'] else moves_at(m['sp'], m['lv'])) if x], 'item': m['item']} for m in pk]
json.dump(trainers, open(os.path.join(OUT, 'trainers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
names = [clean(e) for e in MSG[723][1]]
json.dump(names, open(os.path.join(OUT, 'trnames.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('trainers', len(trainers), 'names', len(names))
for t in (255, 258, 254, 256, 257, 259, 253, 261, 340, 260):
    print(t, names[t], [(m['sp'], m['lv']) for m in trainers[t]])
