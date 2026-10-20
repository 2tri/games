#!/usr/bin/env python3
"""디지몬골드 종 도감표 HTML 만들기 — 포켓몬/디지몬_표_자료.json(make_digimon_table.py) + 표/table_template.html → 포켓몬/디지몬_표.html"""
import json, re, os, sys
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H)
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(R, '포켓몬', '디지몬_표_자료.json')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(R, '포켓몬', '디지몬_표.html')
d = json.load(open(src, encoding='utf-8'))
DARK_ITEMS = ('어둠의돌', '검은 톱니')
def merge_conds(texts):
    items = {}; others = []
    for t in texts:
        m = re.match(r'(.+) 지니고 (낮|밤) 레벨업$', t)
        if m: items.setdefault(m.group(1), []).append(m.group(2))
        elif t not in others: others.append(t)
    parts = list(others)
    for it, times in items.items():
        ts = sorted(set(times))
        parts.append('%s 지니고 레벨업' % it if len(ts) == 2 else '%s 지니고 %s에 레벨업' % (it, ts[0]))
    return ' / '.join(parts)
sp = []
for r in d['species']:
    ev = {}
    for e in r['evo']: ev.setdefault(e['to'], []).append(e['text'])
    e2 = [dict(t=t, c=merge_conds(tx), k=int(any(x in c for x in DARK_ITEMS for c in tx))) for t, tx in ev.items()]
    sp.append(dict(i=r['id'], n=r['name'], d=r['design'], s=r['stage'], o=r['origin'], a=r['attr'], ao=r['attr_orig'], t=r['types'], h=r['stats'], b=r['bst'],
        ab=r['abilities'], cr=r['catch'], e=e2,
        m=[[m['lv'], m['name'], m['type'], m['cat'], m['pw'], m['acc'], m['pp'], int(m['sp'])] for m in r['moves']],
        w=[[x['place'], x['lo'], x['hi'], x['how'], x['pct']] for x in r['wild']], ev=r['events'], tr=r['trainers']))
data = json.dumps(dict(rom='디지몬골드 최신(이지+노래) v1.1 · 2026-10-19', types=d['types'], species=sp), ensure_ascii=False, separators=(',', ':'))
tpl = open(os.path.join(H, 'table_template.html'), encoding='utf-8').read()
memo = open(os.path.join(H, 'memo.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(tpl.replace('__DATA__', data).replace('__MEMO__', json.dumps(memo, ensure_ascii=False)))
print('저장', out, len(data) // 1024, 'KB 자료')
