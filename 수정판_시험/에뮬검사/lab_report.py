import json, glob, os, csv, collections
from PIL import Image, ImageDraw
D = json.load(open('/home/user/games/포켓몬/디지몬_표_자료.json'))
names = {r['id']: r['name'] for r in D['species']}
mvn = {}
for r in D['species']:
    for m in r['moves']: mvn[m['id']] = (m['name'], m['type'], m['sp'])
rows = []; missing = []
tasks = [l.split('\t') for l in open('lab_tasks.tsv', encoding='utf-8').read().split('\n') if l]
for s, g, m in tasks:
    p = 'lab_out/%s_%s/log.json' % (s, g)
    if not os.path.exists(p): missing.append((s, g)); continue
    for k, mid, n, act in json.load(open(p)):
        rows.append((int(s), int(g), k, mid, n, act))
print('완료 전투', len(tasks) - len(missing), '/', len(tasks), '기술 사용', len(rows))
# 이상 후보: 메뉴 복귀 못함(프레임 150 = 1500프레임 한도), 활동량 아주 낮음
cap = [r for r in rows if r[4] >= 148]
low = sorted([r for r in rows if r[4] < 148], key=lambda r: r[5])[:40]
print('1500프레임 안에 메뉴로 못 돌아온 기술', len(cap))
for r in cap[:60]: print('  ', names[r[0]], mvn.get(r[3]), r[4], r[5])
print('활동량 낮은 기술 하위')
for r in low[:25]: print('  ', names[r[0]], mvn.get(r[3]), '프레임', r[4], '활동', r[5])
json.dump(rows, open('lab_rows.json', 'w'))
