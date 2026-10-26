import os, sys, csv, json, collections
sys.path.insert(0,'/home/user/games'); os.chdir('/home/user/games')
import hg1, hg2
from hg1 import NDS, NARC, msg_decode
rom = NDS(open('최종_노래.nds','rb').read())
draft = {r['이름']: r for r in csv.DictReader((l for l in open('NDS_종_초안.tsv', encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
slot = {}; name_of = {}
for l in open('hg2_out/칸표.tsv', encoding='utf-8').read().split('\n')[1:]:
    r = l.split('\t')
    if len(r) >= 2 and r[1].isdigit(): slot[r[0]] = int(r[1]); name_of[int(r[1])] = r[0]
N = NARC(rom.get('a/0/2/7')); MSG = []
for f in N.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM, _, _ = hg1.infer_charmap(MSG, set(draft))
mv = hg2.find_table(MSG, CM, ['몸통박치기', '할퀴기'], (400, 600)) or hg2.find_table(MSG, CM, ['태클', '클로어택'], (400, 600))
MOVES = mv[1]
wf = NARC(rom.get('a/0/1/1')).files
pers = NARC(rom.get('a/0/0/2')).files; learn = NARC(rom.get('a/0/3/3')).files; evo = NARC(rom.get('a/0/3/4')).files
td = NARC(rom.get('a/0/5/5')); tp = NARC(rom.get('a/0/5/6'))
def moves_at(sp, lv):
    ls = [(l,m) for l,m in hg1.learnset(learn[sp]) if l <= lv]
    out=[]
    for l,m in ls:
        if m in out: out.remove(m)
        out.append(m)
    return out[-4:]
trainers = {}
for i in range(len(td.files)):
    d = hg1.trdata(td.files[i])
    if not d or not d['n']: continue
    pk, size = hg1.trpoke(tp.files[i], d['flags'], d['n'])
    if not pk: continue
    mons = []
    for m in pk:
        mvs = m['moves'] if m['moves'] else moves_at(m['sp'], m['lv'])
        mons.append({'sp': name_of.get(m['sp'], '#%d' % m['sp']), 'lv': m['lv'], 'moves': [MOVES[x] for x in mvs if x], 'item': m['item']})
    trainers[i] = mons
json.dump(trainers, open('/tmp/claude-0/-home-user/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/guide/trainers.json','w'), ensure_ascii=False)
# match design table
tsv = [r for r in csv.DictReader(open('NDS_트레이너.tsv', encoding='utf-8'), delimiter='\t')]
res = {}
for r in tsv:
    seq = [t.rsplit(':',1)[0].strip() for t in r['파티'].split(',')]
    hit = [i for i, ms in trainers.items() if [m['sp'] for m in ms] == seq]
    res[r['키']] = hit
for k, v in res.items(): print(k, v[:6])
