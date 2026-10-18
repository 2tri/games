"""주요 트레이너 파티표 → ../NDS_트레이너.tsv  (GBC parties.json 기반, 종 이름은 이번 판 이름으로)
열: 키 | 하트골드 이름 | 새 이름 | 파티(종:레벨, …) | 비고
라이벌(Rival1#n·Rival2#n)·간부(ExecutiveM#n·F#n)는 하트골드에서 같은 직업 트레이너를 번호 순서로 찾는다(이름이 변수이거나 여러 명)."""
import json, csv, os, re
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
parties = json.load(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'parties.json'), encoding='utf-8'))
draft = {r['이름'] for r in csv.DictReader(open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t')}
roster = list(csv.DictReader(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'order', 'roster.csv'), encoding='utf-8-sig')))
ROM2 = {r['롬이름'].strip(): r['종'].strip() for r in roster if r['롬이름'].strip()}
FIX = {'메탈시드몬': '메탈시드라몬', '메가시라몬': '메가시드라몬', '메탈그레몬': '메탈그레이몬', '스컬그레몬': '스컬그레이몬', '아트캅테몬': '아트라캅테리몬',
       '베놈묘티몬': '베놈묘티몬', '레이디데블': '레이디데블몬', '황금아르마': '안킬로몬', '네페르몬': '네페르티몬', '페가수스몬': '페가수몬', '아르마몬': '두리몬', '잠수몬': '서브마리몬', '수리몬': '슈림몬'}
HGSS = {'Falkner': '비상', 'Bugsy': '호일', 'Whitney': '꼭두', 'Morty': '유빈', 'Chuck': '사도', 'Jasmine': '규리', 'Pryce': '류옹', 'Clair': '이향',
        'Will': '일목', 'Koga': '독수', 'Bruno': '시바', 'Karen': '카렌', 'Champion': '목호', 'Brock': '웅', 'Misty': '이슬', 'LtSurge': '마티스',
        'Erika': '민화', 'Janine': '도희', 'Sabrina': '초련', 'Blaine': '강연', 'Blue': '그린', 'Red': '레드'}
NEW = {'Falkner': '소라', 'Bugsy': '한솔', 'Whitney': '미나', 'Morty': '나리', 'Chuck': '레오몬', 'Jasmine': '안드로몬', 'Pryce': '정석', 'Clair': '리키',
       'Will': '메탈시드라몬', 'Koga': '피노키몬', 'Bruno': '파워드라몬', 'Karen': '피에몬', 'Champion': '아포카리몬', 'Brock': '재하', 'Misty': '정석',
       'LtSurge': '한솔', 'Erika': '미나', 'Janine': '예지', 'Sabrina': '나리', 'Blaine': '산해', 'Blue': '리키', 'Red': '정우'}
def norm(n):
    n = FIX.get(n, n); n = ROM2.get(n, n)
    return n
out = [['키', '하트골드 이름', '새 이름', '파티', '비고']]; bad = []
for k, v in parties.items():
    if k.startswith('_') or not v: continue
    mons = []
    for m in v:
        sp = norm(m['sp'])
        if sp not in draft: bad.append((k, m['sp'], sp)); sp = norm(m.get('until', sp))
        mons.append('%s:%d' % (sp, m['lv']))
    base = k.split('#')[0]
    out.append([k, HGSS.get(base, '(직업으로 찾음)'), NEW.get(base, '매튜' if base.startswith('Rival1') else ('정우' if base.startswith('Rival2') else '')), ', '.join(mons),
                '라이벌: 같은 직업 n번째' if base.startswith('Rival') else ('간부: 같은 직업 n번째' if base.startswith('Executive') else '')])
open(os.path.join(P, 'NDS_트레이너.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join('\t'.join(r) for r in out) + '\n')
print(len(out) - 1, '명, 이름 못 맞춘 종:', bad)
