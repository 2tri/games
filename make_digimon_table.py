#!/usr/bin/env python3
"""디지몬 종 표 자료 뽑기 (2026-10-19) — 만든 롬에서 종별 능력치·타입·속성·진화·배우는 기술·출현 장소를 JSON 으로. 롬은 읽기만.
사용:   python make_digimon_table.py <롬.nds> [--out 포켓몬/디지몬_표_자료.json]
읽는 곳: 종 이름·기술 이름·특성·도구·타입 이름표(글), 능력치(a/0/0/2), 진화(a/0/3/4), 레벨 기술(a/0/3/3), 기술 자료(a/0/1/1), 속성표(오버레이 12),
        단계·출처(NDS_종_초안.tsv), 프리/언노운 원래 표기(wikimon_속성.tsv·NDS_속성_고침.tsv), 출현(야생_장소별.md ← 야생_검토.py, NDS_이벤트표.tsv, NDS_트레이너.tsv)"""
import os, sys, re, csv, json, argparse, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import hg1, hg2, hg_attr
from hg1 import NDS, NARC
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default=os.path.join(H, '포켓몬', '디지몬_표_자료.json')); A = ap.parse_args()
rom = NDS(open(A.rom, 'rb').read())
def narc(k): return NARC(rom.get(hg1.NARC_PATHS[k])).files
MSG = []
for f in narc('msg'):
    try: MSG.append(hg1.msg_decode(f))
    except Exception: MSG.append((0, []))
draft = list(csv.DictReader(open(os.path.join(H, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t'))
CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
for fn in (os.path.join(H, 'NDS_글자표_추가.tsv'),):
    if os.path.exists(fn):
        for r in csv.DictReader(open(fn, encoding='utf-8'), delimiter='\t'):
            try:
                c = int(r['부호'], 16); g = hg1.glyph(r.get('글자'))
                if g is not None: CM.extra[c] = g; CM.rev[g] = c
            except Exception: pass
dec = lambda ents: [CM.dec(e) for e in ents]
names = dec(MSG[NAMEF][1])
mv = hg2.find_table(MSG, CM, ['몸통박치기', '할퀴기'], (400, 600)) or hg2.find_table(MSG, CM, ['태클', '클로어택'], (400, 600))
ab = hg2.find_table(MSG, CM, ['맹화', '급류', '심록'], (100, 200))
it = hg2.find_table(MSG, CM, ['몬스터볼', '어둠의돌'], (400, 700)) or hg2.find_table(MSG, CM, ['디지볼', '어둠의돌'], (400, 700))
mvn, abn, itn = mv[1], ab[1], it[1]
tyn = next((dec(ent) for _, ent in MSG if len(ent) == 18 and CM.dec(ent[0]) in ('노말', '일반')), None)
if not tyn: raise SystemExit('타입 이름표를 못 찾음')
desc_f = next((dec(ent) for fi, (_, ent) in enumerate(MSG) if fi != mv[0] and len(ent) == len(mvn) and sum(1 for x in dec(ent) if '\\n' in x) > 0.8 * len(ent) and sum(len(x) for x in dec(ent)) / len(ent) > 15), None)
SP = {i for i, d in enumerate(desc_f or []) if '필살기' in d}
P, L, E, W = narc('personal'), narc('learn'), narc('evo'), NARC(rom.get('a/0/1/1')).files
slots = [(r['이름'], int(r['칸'])) for r in csv.DictReader(open(os.path.join(H, 'hg2_out', 'slots.tsv'), encoding='utf-8'), delimiter='\t')]
slot_of = dict(slots); name_of = {s: n for n, s in slots}
# 속성: 롬 표 + 원래 표기(프리·언노운)
pos, e, ov, comp = hg_attr.ov_read(rom); tab = bytes(ov[hg_attr.o(hg_attr.TABLE_ADDR):hg_attr.o(hg_attr.TABLE_ADDR) + 128])
orig_attr = {}
for fn in ('wikimon_속성.tsv', 'NDS_속성_고침.tsv'):
    for r in csv.DictReader(open(os.path.join(H, fn), encoding='utf-8'), delimiter='\t'):
        if r.get('이름') and r.get('속성', '').strip(): orig_attr[r['이름'].strip()] = r['속성'].strip()
dex = hg_attr.dex_attrs(rom, {n: s for n, s in slots}) or {}
stage = {r['이름']: r['단계'] for r in draft}; origin = {r['이름']: r['출처'] for r in draft}
# 기술
def move(m, lv):
    d = W[m]; return dict(lv=lv, id=m, name=mvn[m], type=tyn[d[4]] if d[4] < len(tyn) else '?', cat=['물리', '특수', '변화'][d[2]] if d[2] < 3 else '?', pw=d[3], acc=d[5], pp=d[6], sp=m in SP)
METH = {1: '친밀도', 2: '친밀도(낮)', 3: '친밀도(밤)', 4: '레벨', 7: '도구 사용', 18: '도구 지니고 레벨(낮)', 19: '도구 지니고 레벨(밤)', 20: '기술', 21: '파티 종'}
sp_rows = []
for n, s in sorted(slots, key=lambda x: x[1]):
    pr = hg1.personal(P[s]); b = P[s]
    att = (tab[s >> 2] >> ((s & 3) * 2)) & 3
    evs = []
    for m, prm, t in hg1.evos(E[s]):
        if m == 4: txt = 'Lv%d' % prm
        elif m in (7, 18, 19): txt = '%s%s' % (itn[prm] if prm < len(itn) else prm, ' 사용' if m == 7 else (' 지니고 낮 레벨업' if m == 18 else ' 지니고 밤 레벨업'))
        elif m == 20: txt = '「%s」 배우고 레벨업' % (mvn[prm] if prm < len(mvn) else prm)
        elif m == 21: txt = '파티에 %s' % (names[prm] if prm < len(names) else prm)
        else: txt = '%s %s' % (METH.get(m, '방법 %d' % m), prm or '')
        evs.append(dict(to=t, method=m, text=txt.strip()))
    sp_rows.append(dict(id=s, name=names[s], design=n, stage=stage.get(n, '?'), origin=origin.get(n, '?'),
        attr=['중립', '백신', '데이터', '바이러스'][att], attr_orig=orig_attr.get(n, ''), dex_attr=dex.get(s, ''),
        types=list(dict.fromkeys(tyn[t] for t in pr['type'])), stats=pr['stats'], bst=sum(pr['stats']),
        abilities=list(dict.fromkeys(abn[a] for a in (b[22], b[23]) if a < len(abn))), catch=pr['catch'], evo=evs,
        moves=[move(m, lv) for lv, m in hg1.learnset(L[s])]))
by = {r['id']: r for r in sp_rows}
for r in sp_rows:
    r['from'] = [dict(id=o['id'], text=x['text']) for o in sp_rows for x in o['evo'] if x['to'] == r['id']]
# 출현: 야생
wild = collections.defaultdict(lambda: collections.defaultdict(lambda: dict(lo=999, hi=0, how=set(), pct=0)))
cur = None; how_re = re.compile(r'^- (걷기 아침|걷기 낮|걷기 밤|파도타기|헌 낚싯대|좋은 낚싯대|대단한 낚싯대|바위깨기):\s*(.*)$')
for line in open(os.path.join(H, '야생_장소별.md'), encoding='utf-8'):
    line = line.rstrip('\n')
    if line.startswith('## '): cur = re.sub(r' — 야생 파일.*$', '', line[3:]).strip(); continue
    m = how_re.match(line)
    if not m or not cur: continue
    for part in m.group(2).split(', '):
        pm = re.match(r'(\S+) Lv(\d+)~(\d+)(?:\((\d+)%\))?', part)
        if not pm: continue
        d = wild[pm.group(1)][cur]; d['lo'] = min(d['lo'], int(pm.group(2))); d['hi'] = max(d['hi'], int(pm.group(3))); d['how'].add(m.group(1).replace('걷기 ', ''))
        d['pct'] = max(d['pct'], int(pm.group(4) or 0))
events = collections.defaultdict(list)
for r in csv.DictReader((l for l in open(os.path.join(H, 'NDS_이벤트표.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t'):
    if r['우리 종'] and r['우리 종'] in slot_of: events[r['우리 종']].append('%s · %s%s' % (r['종류'], r['장소'], (' Lv' + r['Lv']) if r.get('Lv') else ''))
trn = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(H, 'NDS_트레이너.tsv'), encoding='utf-8'), delimiter='\t'):
    for part in r['파티'].split(','):
        pm = re.match(r'\s*(\S+):(\d+)', part)
        if pm: trn[pm.group(1)].append('%s Lv%s' % (r['새 이름'] or r['하트골드 이름'], pm.group(2)))
for r in sp_rows:
    w = wild.get(r['design'], {})
    places = sorted(((k, v) for k, v in w.items()), key=lambda kv: (kv[1]['lo'], -kv[1]['pct']))
    r['wild'] = [dict(place=k, lo=v['lo'], hi=v['hi'], how='·'.join(sorted(v['how'])), pct=v['pct']) for k, v in places]
    r['events'] = events.get(r['design'], []); r['trainers'] = trn.get(r['design'], [])
json.dump(dict(rom=os.path.basename(A.rom), types=tyn, species=sp_rows), open(A.out, 'w', encoding='utf-8'), ensure_ascii=False)
print('종 %d, 진화 %d, 기술 줄 %d → %s' % (len(sp_rows), sum(len(r['evo']) for r in sp_rows), sum(len(r['moves']) for r in sp_rows), A.out))
