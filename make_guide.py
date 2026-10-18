#!/usr/bin/env python3
"""공략 초안 만들기 (2026-10-15) — 설계 표(tsv)에서 「블로그 공략」 꼴의 문서를 자동으로 → C:/개인/NDS/공략_초안.md
표가 바뀌면 다시 돌리면 된다. 장소 차례는 NDS_스토리.md 2절의 장소 칸만 쓴다(설명 글은 옛것이라 안 씀)."""
import os, re, csv, collections
H = os.path.dirname(os.path.abspath(__file__)); P = H if os.path.exists(os.path.join(H, 'NDS_종_초안.tsv')) else os.path.join(H, '..')   # 10/16: 집은 같은 폴더
def tsv(name):
    p = os.path.join(P, name)
    return [r for r in csv.DictReader((l for l in open(p, encoding='utf-8') if not l.startswith('#')), delimiter='\t')] if os.path.exists(p) else []

draft = tsv('NDS_종_초안.tsv'); grade = {r['이름']: r['단계'] for r in draft}; typ = {r['이름']: r['타입'] for r in draft}
tr = {r['키']: r for r in tsv('NDS_트레이너.tsv')}
ev = tsv('NDS_이벤트표.tsv'); gifts = tsv('NDS_선물도구.tsv'); evo = tsv('NDS_진화.tsv'); rare = tsv('NDS_귀한종.tsv')
gift_by = {r['키']: r for r in gifts}

ORDER1 = [('Falkner', '1', '전망산 수련장'), ('Bugsy', '2', '곤충 마을 수련장'), ('Whitney', '3', '장난감 마을 수련장'), ('Morty', '4', '유령 마을 수련장'),
          ('Chuck', '5', '바위산 마을 수련장'), ('Jasmine', '6', '톱니공장 수련장'), ('Pryce', '7', '얼음나라 수련장'), ('Clair', '8', '용의 골짜기 수련장')]
E4 = [('Will', '어둠의 4천왕 1'), ('Koga', '어둠의 4천왕 2'), ('Bruno', '어둠의 4천왕 3'), ('Karen', '어둠의 4천왕 4'), ('Champion', '챔피언')]
ORDER2 = [('LtSurge', '1', '항구 마을'), ('Sabrina', '2', '빛의 언덕'), ('Misty', '3', '왕개굴몬 성'), ('Erika', '4', '초등학교 마을'),
          ('Janine', '5', '사파리 마을'), ('Blaine', '6', '화산 섬'), ('Brock', '7', '미궁 마을'), ('Blue', '8', '디지타마몬 마을')]
FINAL = [('Mildo', '신대륙 도로 — 디지몬 카이저(정우)'), ('Red', '카이저 요새 꼭대기 — 마일도 최종')]

def party(key):
    r = tr.get(key)
    if not r: return '(표에 없음)'
    out = []
    for tok in r['파티'].split(','):
        nm, _, lv = tok.strip().rpartition(':'); out.append('%s Lv%s(%s)' % (nm, lv, grade.get(nm, '?')[:3]))
    return ' · '.join(out)

def reward(key):
    g = gift_by.get(key)
    return g['새 도구'] if g else '(기술머신 그대로)'

L = ['# 디지몬 2부(NDS) 공략 초안 — 표에서 자동 생성 (%s)' % __import__('datetime').date.today(), '',
     '> 설계 표(NDS_트레이너·이벤트표·선물도구·진화·귀한종)에서 만든 초안. 실제 플레이로 확인한 것은 아님. 표가 바뀌면 make_guide.py 를 다시 돌린다.', '']
L += ['## 1. 시작', '- 스타팅: 아구몬(불꽃·백신) / 파닥몬(노말·비행·데이터) / 케라몬(고스트·악·언노운). 속성은 도감 표기일 뿐, 전투 상성은 타입으로.',
      '- 연구소 조수가 알(플롯트몬)을 준다. 매튜(라이벌)는 파피몬.', '']
L += ['## 2. 1부 수호자 8곳 (성도)', '', '| 순서 | 장소 | 수호자 | 파티 | 이기면 받는 것 |', '|---|---|---|---|---|']
for key, n, place in ORDER1:
    r = tr.get(key, {}); L.append('| %s | %s | %s | %s | 문장(배지) + %s |' % (n, place, r.get('새 이름', '?'), party(key), reward(key)))
L += ['', '## 3. 나선산 — 어둠의 4천왕과 챔피언', '', '| | 상대 | 파티 |', '|---|---|---|']
for key, nm in E4: L.append('| %s | %s | %s |' % (nm, tr.get(key, {}).get('새 이름', '?'), party(key)))
L += ['', '## 4. 2부 신대륙 수호자 8곳 (관동)', '', '| 순서 | 장소 | 수호자 | 파티 | 이기면 받는 것 |', '|---|---|---|---|---|']
for key, n, place in ORDER2:
    r = tr.get(key, {}); L.append('| %s | %s | %s | %s | 증표 + %s |' % (n, place, r.get('새 이름', '?'), party(key), reward(key)))
L += ['', '## 5. 마지막 싸움', '', '| 어디 | 상대 | 파티 |', '|---|---|---|']
for key, where in FINAL: L.append('| %s | %s | %s |' % (where, tr.get(key, {}).get('새 이름', '?'), party(key)))
L += ['', '## 6. 디지몬을 얻는 곳 (선물·교환·고정·떠돌이·심볼)', '', '| 종류 | 장소 | 디지몬 | Lv | 메모 |', '|---|---|---|---|---|']
for r in ev:
    if r['종류'] in ('스타팅', '알', '선물', '교환', '고정', '떠돌이', '추적', '심볼') and r['우리 종'].strip() and not r['우리 종'].startswith('('):
        L.append('| %s | %s | %s | %s | %s |' % (r['종류'], r['장소'], r['우리 종'], r['Lv'] or '-', (r['하트골드 원래'] or '')[:20]))
L += ['', '## 7. 디지멘탈·태그를 받는 곳', '', '| 어디 | 받는 것 | 쓰임 |', '|---|---|---|']
for r in ev:
    if r['종류'] == '도구': L.append('| %s (%s) | %s | %s |' % (r['하트골드 원래'], r['장소'], r['우리 종'], (r['근거'] or '').split('·')[-1].strip()[:40]))
L += ['', '## 8. 진화 조건', '']
by = collections.defaultdict(list)
for r in evo: by[r['방법']].append(r)
NAME = {'레벨': '레벨이 오르면', '도구사용': '디지멘탈·돌을 쓰면(아머 진화)', '도구지니고낮': '지닌 채 낮에 레벨이 오르면(태그·궁극의 문장)', '도구지니고밤': '지닌 채 밤에 레벨이 오르면', '기술': '기술을 배우면', '파티종': '파티에 짝이 있으면(조그레스)', '친밀도': '친밀도'}
for m in ('레벨', '도구사용', '도구지니고낮', '도구지니고밤', '파티종', '기술', '친밀도'):
    rows = by.get(m)
    if not rows: continue
    L.append('### %s' % NAME.get(m, m)); L.append('')
    L += ['- %s → %s (%s)' % (r['출발'], r['도착'], r['값']) for r in rows]; L.append('')
L += ['## 9. 야생에 안 나오는 디지몬(규칙)', '']
for r in rare:
    if r['규칙'] in ('안 나옴', '1부 안 나옴', '드문 칸'): L.append('- %s: %s — %s' % (r['이름'], r['규칙'], r['이유']))
open(os.path.join(P, '공략_초안.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('→ 공략_초안.md (%d줄)' % len(L))
