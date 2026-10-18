"""NDS 종 자료 초안 (2026-10-08). 입력: design.json(GBC 설계), dg_excel/*.tsv(디지골드 제작자 엑셀), repo/romhack/order/roster.csv(GBC 칸 번호)
출력: ../NDS_종_초안.tsv (종마다 한 줄) + ../NDS_종_초안_요약.md
원칙
- 칸 번호 = GBC 때 그 디지몬을 넣은 골드 도감 번호(1~251). 하트골드도 같은 번호를 쓰므로 야생·이벤트 자리가 GBC판과 같아진다.
- 디지골드에 있는 종(66): 디지골드의 타입·특성·능력치·기술·진화를 그대로 쓰고(이미 하트골드에 맞춰 다듬어진 값), 그림·걷기 그림도 디지골드 것.
- 새 종: 타입은 GBC 설계, 능력치는 GBC 설계 비율을 디지골드 단계별 평균 합계에 맞춰 늘림, 특성은 타입 기본값, 기술은 같은 단계·같은 타입 디지골드 디지몬의 기술표를 본보기로(누구를 본떴는지 적음).
- 진화: 디지골드 방식(레벨 / 돌 사용 / 기술 배우고 레벨업 / 지닌 채 레벨업 / 둘이 함께 있을 때 레벨업)으로 옮긴다. GBC 의 유대 낮음·검은 톱니 갈래 = 「어둠의돌 사용」(디지골드와 같음), 문장 조건은 레벨만 남김.
- 유아기는 뺀다(사용자 10/8). 유년기도 뺀다(사용자 10/12, 토코몬만 남김 — 알 선물)."""
import json, csv, os, re, collections
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
d = json.load(open(os.path.join(H, 'design.json'), encoding='utf-8')); S = {s['ko']: s for s in d['species']}
src = open(os.path.join(H, 'make_digigold_lists.py'), encoding='utf-8').read()
EXCEL = eval(src.split("EXCEL = ", 1)[1].split("\nassert", 1)[0])
DG = {m: g for g, m in EXCEL}; DG['블랙워그레이몬'] = '워그레이몬(검정)'
DGN_TO_MY = {g: m for g, m in EXCEL}
TYPES = ['노말', '격투', '비행', '독', '땅', '바위', '벌레', '고스트', '강철', '페어리', '불꽃', '물', '풀', '전기', '에스퍼', '얼음', '드래곤', '악']
GRADE_FIX = {'돌핀몬': '완전체', '맘몬': '완전체', '번개콩알몬': '완전체', '베타몬': '성장기', '에이프몬': '성숙기', '오쿠와몬': '완전체', '콩알몬': '완전체', '쿠네몬': '성장기'}
TARGET = {'유년기Ⅰ': 330, '유년기Ⅱ': 330, '유년기': 330, '성장기': 405, '성숙기': 485, '아머체': 520, '완전체': 555, '궁극체': 630}
ABIL = {'불꽃': '맹화,불꽃몸', '물': '급류,수의베일', '풀': '심록,엽록소', '전기': '정전기,피뢰침', '얼음': '아이스바디,눈숨기', '격투': '근성,의욕',
        '독': '독가시,악취', '땅': '모래숨기,옹골참', '비행': '날카로운눈,근성', '에스퍼': '싱크로,정신력', '벌레': '벌레의알림,복안', '바위': '옹골참,돌머리',
        '고스트': '부유,불면', '드래곤': '위협,정신력', '악': '위협,프레셔', '강철': '클리어바디,옹골참', '노말': '의욕,근성', '페어리': '헤롱헤롱바디,하늘의은총'}
STONE = {'ITEM_BLACK_GEAR': '어둠의돌 사용', 'ITEM_THUNDER_STONE': '천둥의돌 사용', 'ITEM_WATER_STONE': '물의돌 사용', 'ITEM_FIRE_STONE': '불꽃의돌 사용',
         'ITEM_MOON_STONE': '달의돌 사용', 'ITEM_KINGS_ROCK': '왕의징표석 지닌 채 레벨업', 'ITEM_METAL_COAT': '금속코트 지닌 채 레벨업', 'ITEM_UP_GRADE': '업그레이드 지닌 채 레벨업'}
roster = {r['종'].strip(): r for r in csv.DictReader(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'order', 'roster.csv'), encoding='utf-8-sig'))}
DROP = {s['ko'] for s in d['species'] if s['grade'] == '유아기Ⅰ' or (s['grade'].startswith('유년기') and s['ko'] != '토코몬')}   # 10/12: 성장기부터 시작, 유년기는 토코몬(알 선물)만

def tsv(name):
    return [l.rstrip('\n').split('\t') for l in open(os.path.join(H, 'dg_excel', name + '.tsv'), encoding='utf-8')]
MAIN = {r[2]: r for r in tsv('메인') if len(r) > 14 and r[2]}
MOVE_FIX = {'Iron Tail': '아이언테일'}
LEARN = {r[0]: [(r[i], MOVE_FIX.get(r[i + 1], r[i + 1]).replace(' ', '')) for i in range(1, len(r) - 1, 2) if r[i + 1] not in ('', '-')] for r in tsv('자력기 학습목록')[1:] if r and r[0]}

def grade(ko): return GRADE_FIX.get(ko) or S[ko]['grade'] or '성숙기'
# 디지골드 엑셀 「진화조건」 = 이 종이 무엇에서 어떻게 진화해 오나 → 나가는 진화표로 뒤집음
DG_OUT = collections.defaultdict(list)
for g, r in MAIN.items():
    if ' / ' in r[14]:
        frm, cond = r[14].split(' / ', 1)
        srcs = [x.strip().lstrip('.') for x in frm.split(',')]
        for x in srcs:
            DG_OUT[x].append((g, '%s%s' % (cond.strip(), '' if len(srcs) == 1 else ', ' + '+'.join(srcs) + ' 함께')))
# 기술 본보기: 같은 첫 타입 + 합계가 가장 가까운 종(디지골드 디지몬 우선, 없으면 포켓몬)
POOL = [(g, r[3], r[4], int(r[13])) for g, r in MAIN.items() if g in LEARN and r[13].isdigit()]
DGN = set(DG.values())
def pick_donor(t1, t2, tgt):
    c = [x for x in POOL if x[1] == t1] or [x for x in POOL if t1 in (x[1], x[2])] or POOL
    return min(c, key=lambda x: (abs(x[3] - tgt) + (0 if x[0] in DGN else 25) - (15 if t2 in (x[1], x[2]) else 0)))[0]
# 디지골드 디지몬의 (단계, 첫 타입) → 기술표 본보기
donors = collections.defaultdict(list)
for m, g in DG.items():
    if g in MAIN and g in LEARN: donors[(grade(m), MAIN[g][3])].append(g)
by_grade = collections.defaultdict(list)
for (gr, t), v in donors.items(): by_grade[gr] += v

# 설계 자료(design.json)에 빠진 진화 보충: GBC rules.PALSWAP_EVOS(10/7 추가 진화 55개) — 문장 조건은 레벨만 남김
import sys as _sys
_sys.path.insert(0, os.path.join(P, '..', 'GBC', 'repo', 'romhack'))
import rules as _rules
SHORT = {'스컬그레몬': '스컬그레이몬', '블랙워그몬': '블랙워그레이몬', '아트캅테몬': '아트라캅테리몬', '레이디데블': '레이디데블몬', '메가시라몬': '메가시드라몬',
         '메탈시드몬': '메탈시드라몬', '메탈그레몬': '메탈그레이몬'}
EVO_ADD = collections.defaultdict(list)
for src_, lst in _rules.PALSWAP_EVOS.items():
    for kind, lv, tgt in lst:
        EVO_ADD[SHORT.get(src_, src_)].append('%s(Lv %d)' % (SHORT.get(tgt, tgt), lv))
# GBC 마지막 주에 slots.json 으로만 들어간 10종(로스터 밖): 호우오몬·헤라캅테몬·바이킹몬 등
SLOTS = json.load(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'slots.json'), encoding='utf-8'))
EXTRA_NAMES = ['호우오몬', '헤라캅테몬', '바이킹몬', '하이안드몬', '메탈티라몬', '그란쿠와몬', '리리스몬', '발키리몬', '데비타마몬']   # 데드메라몬은 데스메라몬과 같은 디지몬(결정7) → 219 줄 하나로
EXTRAS = {m['name']: m for m in SLOTS['mons'] if m['name'] in EXTRA_NAMES}
TYPE_EN = {'NORMAL': '노말', 'FIGHTING': '격투', 'FLYING': '비행', 'POISON': '독', 'GROUND': '땅', 'ROCK': '바위', 'BUG': '벌레', 'GHOST': '고스트', 'STEEL': '강철',
           'FIRE': '불꽃', 'WATER': '물', 'GRASS': '풀', 'ELECTRIC': '전기', 'PSYCHIC': '에스퍼', 'ICE': '얼음', 'DRAGON': '드래곤', 'DARK': '악'}

def evo_text(ko):
    out = []
    for e in (S[ko]['evos'] if ko in S else []):
        to = e['to']
        if to in DROP: continue
        conds = [c[0] for c in e['cond']]
        if e['kind'] == 'ITEM': t = STONE.get(e['val'], e['val'] + ' 사용')
        elif 'IF_MAX_FRIENDSHIP' in conds or (to in S and '유대 낮음' in S[to]['use'] and ko in S[to]['use']): t = '어둠의돌 사용'
        else: t = 'Lv %d' % e['val'] if e['val'] else '친밀도'
        s = '%s(%s)' % (to, t)
        if s not in out and not any(o.startswith(to + '(') for o in out): out.append(s)
    for x in EVO_ADD.get(ko, []):
        if not any(o.split('(')[0] == x.split('(')[0] for o in out): out.append(x)
    return ' ; '.join(out)

rows = []; stat_new = collections.Counter()
for s in d['species']:
    ko = s['ko']
    if ko in DROP or ko == '디지문자': continue
    gr = grade(ko); slot = roster.get(ko, {}).get('칸', '')
    if ko in DG:
        g = DG[ko]; r = MAIN.get(g if g in MAIN else '워그레이몬')
        types = '/'.join(x for x in (r[3], r[4]) if x); ab = ','.join(x for x in (r[5], r[6]) if x)
        st = ' '.join(r[7:13]); tot = r[13]; ev = ' ; '.join('%s[%s]' % (DGN_TO_MY.get(n, n), c) for n, c in DG_OUT.get(g, [])) or '-'
        learn = ' '.join('%s:%s' % x for x in LEARN.get(g if g in LEARN else '워그레이몬', []))
        dg_targets = {DGN_TO_MY.get(n, n) for n, c in DG_OUT.get(g, [])}
        extra = [x for x in evo_text(ko).split(' ; ') if x and x.split('(')[0] not in dg_targets]
        note = '디지골드 「%s」 그대로' % g + (' / 설계에만 있는 진화: ' + ' ; '.join(extra) if extra else '') + (' / 디지골드 칸: ' + r[16] if len(r) > 16 and r[16] else '')
        rows.append([slot, ko, gr, '디지골드', types, ab, st, tot, '디지골드: %s' % ev, learn, note])
    else:
        t1, t2 = TYPES[s['type'][0]], TYPES[s['type'][1]]
        types = t1 if t1 == t2 else t1 + '/' + t2
        base = s['stats']; tgt = TARGET.get(gr, 485); k = tgt / max(1, sum(base))
        st = [max(20, min(200, round(x * k))) for x in base]
        donor = pick_donor(t1, t2, tgt)
        learn = ' '.join('%s:%s' % x for x in LEARN[donor])
        rows.append([slot, ko, gr, '새로', types, ABIL.get(t1, '의욕,근성'), ' '.join(map(str, st)), str(sum(st)), evo_text(ko), learn, '기술은 「%s」 본뜸(타입 맞춰 손볼 것)' % donor])
        stat_new[gr] += 1
for ko, m in EXTRAS.items():
    gr = m['grade']; t1, t2 = TYPE_EN[m['type'][0]], TYPE_EN[m['type'][1]]
    types = t1 if t1 == t2 else t1 + '/' + t2
    tgt = TARGET.get(gr, 555); k = tgt / max(1, sum(m['stats']))
    st = [max(20, min(200, round(x * k))) for x in m['stats']]
    donor = pick_donor(t1, t2, tgt)
    learn = ' '.join('%s:%s' % x for x in LEARN[donor])
    rows.append([str(m['slot']), ko, gr, '새로', types, ABIL.get(t1, '의욕,근성'), ' '.join(map(str, st)), str(sum(st)), evo_text(ko), learn,
                 '기술은 「%s」 본뜸(타입 맞춰 손볼 것) / GBC 10/7 추가 종(slots.json, 로스터 밖)' % donor])
# ---- 칸 배정: 새 종 = GBC 칸(골드 도감 번호), 디지골드 종 = 디지골드가 넣은 칸(포켓몬 이름, 번호는 HG1 로 확인), 칸 없는 2부 종 = 빈 칸
SPECIAL = {25, 132, 133, 150, 151, 152, 155, 158, 172, 175, 201, 235, 243, 244, 245, 249, 250, 251, 130, 131, 143, 185}
used = {int(r[0]) for r in rows if r[3] == '새로' and r[0].isdigit() and r[1] not in EXTRAS}
extra_slot = {}
for r in rows:
    if r[1] in EXTRAS:
        n = int(r[0])
        if n in used or n in SPECIAL: r[0] = ''          # 이미 쓰이는 번호면 빈 칸 받음
        else: extra_slot[r[1]] = n; used.add(n)
dg_gbc = {int(r[0]) for r in rows if r[3] == '디지골드' and r[0].isdigit()}
free = [n for n in range(1, 252) if n not in used and n not in dg_gbc and n not in SPECIAL]
k = 0
for r in rows:
    if r[3] == '디지골드' and r[1] == '블랙워그레이몬':
        r.insert(1, r[0] if r[0].isdigit() else str(free.pop())); r[11] += ' / 별도 칸: 자료·그림은 디지골드 워그레이몬을 복사해 검은 색으로(디지골드에선 같은 칸의 색 다른 모습)'
    elif r[3] == '디지골드':
        m = re.search(r'디지골드 칸: (\S+)', r[10])
        r.insert(1, '디지골드 「%s」 칸' % (m.group(1) if m else '?'))
    elif r[0].isdigit():
        r.insert(1, str(int(r[0])))
    else:
        r.insert(1, str(free[k])); r[11] = r[11] + ' / 칸 새로 배정(GBC 칸 없음)'; k += 1
for r in rows:                      # 결정7: 이름은 「데드메라몬」, 진화 글 안의 이름도
    if r[2] == '데스메라몬': r[2] = '데드메라몬'
    r[9] = r[9].replace('데스메라몬', '데드메라몬')
rows.sort(key=lambda r: int(r[0]) if r[0].isdigit() else 999)
head = ['칸(골드 도감 번호)', 'NDS 칸', '이름', '단계', '출처', '타입', '특성', 'HP 공 방 특공 특방 스피드', '합', '진화', '레벨 기술', '메모']
open(os.path.join(P, 'NDS_종_초안.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join('\t'.join(r) for r in [head] + rows) + '\n')
nds = collections.Counter(r[1] for r in rows)
print('종 %d (디지골드 %d, 새로 %d) NDS 칸 겹침 %s' % (len(rows), sum(1 for r in rows if r[4] == '디지골드'), sum(1 for r in rows if r[4] == '새로'), [k for k, v in nds.items() if v > 1]))
