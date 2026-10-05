"""디지몬 기술 참고표: 공식 도감(digimon.net 한국어) 필살기 → 성격 분류 → 비슷한 금 기술(연출·효과 빌려 쓰기 후보)"""
import json, re, sys
sys.path.insert(0, '/home/user/games/digimon/romhack')
S = '/tmp/claude-0/-home-user-games/6383e336-0dcf-5b3b-862b-dcfdcb19a4bd/scratchpad/skills/'
K = '/home/user/narishma-gb/pokegold-kr/'
D = json.load(open(S + 'dn_moves.json'))
rom = open('/home/user/games/digimon/romhack/work/myver.gbc', 'rb').read()
names = [re.search(r'li "(.*)"', l).group(1) for l in open(K + 'data/moves/names.asm') if 'li "' in l]
eff = [re.match(r'\s*const (\w+)', l).group(1) for l in open(K + 'constants/move_effect_constants.asm') if re.match(r'\s*const \w+', l)]
T0 = 0x4172e                                                   # 기술 표 (롬에서 찾음: 막치기 01 00 28 00 FF 23 00)
moves = []
for i in range(251):
    b = rom[T0 + 7 * i: T0 + 7 * i + 7]
    moves.append(dict(no=i + 1, name=names[i], anim=b[0], eff=eff[b[1]] if b[1] < len(eff) else b[1], power=b[2], type=b[3], acc=round(b[4] * 100 / 255), pp=b[5], chance=round(b[6] * 100 / 255)))
TYPE = {0: '노말', 1: '격투', 2: '비행', 3: '독', 4: '땅', 5: '바위', 7: '벌레', 8: '고스트', 9: '강철', 20: '불꽃', 21: '물', 22: '풀', 23: '전기', 24: '에스퍼', 25: '얼음', 26: '드래곤', 27: '악'}
CAT = [  # (성격, 금 타입, 낱말)
    ('어둠', 27, '어둠 암흑 데스 다크 나이트메어 저주 지옥 데빌 마왕 공포 그림자 이블 블랙 헬 악마 사신'),
    ('빛·성스러움', 24, '빛 성스러 홀리 천사 헤븐 세븐 신성 정화 희망 축복 무지개'),
    ('불꽃', 20, '불꽃 불길 불덩이 불을 화염 플레임 파이어 버닝 용암 작열 태양 폭염 업화'),
    ('얼음', 25, '얼음 냉기 블리자드 프리즈 콜드 아이스 빙결 눈보라 코키토스 얼어'),
    ('전기', 23, '전기 번개 벼락 뇌운 썬더 전격 스파크 일렉트 라이트닝 방전 전류 쇼커'),
    ('물', 21, '거품 버블 워터 해일 파도 어뢰 바다 하이드로 물고기 피쉬 수압 액체 물줄기 물을 물대포'),
    ('풀', 22, '꽃 덩굴 씨앗 잎 아이비 플라워 나무 식물 포자 가시 바늘 니들 선인장'),
    ('벌레', 7, '독침 스파이크 곤충 벌레 송곳'),
    ('독', 3, '독 포이즌 산성 점액 똥 응가'),
    ('땅', 4, '땅 드릴 대지 모래 크랙 지진 흙 가이아'),
    ('바람·비행', 2, '바람 회오리 날개 윙 토네이도 깃털 하늘 돌풍 사이클론 트위스터 비행'),
    ('바위·강철', 9, '바위 강철 메탈 금속 철 해머 망치'),
    ('광선·포격', 0, '레이저 빔 미사일 캐논 블래스터 버스터 포격 탄 미사일 포 광선 에너지'),
    ('격투', 1, '펀치 킥 주먹 발차기 할퀴 클로 손톱 발톱 칼 검 소드 참격 크러셔 권 베어 베는 단칼'),
    ('정신', 24, '최면 환상 텔레파시 마술 매직 마법 환영'),
]
EFFX = [('마비', 'EFFECT_PARALYZE_HIT', '마비 저림 전기 감전'), ('잠', 'EFFECT_SLEEP', '최면 잠 재우'), ('독', 'EFFECT_POISON_HIT', '독 포이즌'),
        ('얼음', 'EFFECT_FREEZE_HIT', '얼려 얼음 동결'), ('화상', 'EFFECT_BURN_HIT', '불태 화상 작열'), ('흡수', 'EFFECT_LEECH_HIT', '피를 빼 흡수 빨아'),
        ('연속', 'EFFECT_MULTI_HIT', '연속 난사 일제히 연타 여러 발'), ('혼란', 'EFFECT_CONFUSE_HIT', '혼란 환상 현혹'), ('풀죽음', 'EFFECT_FLINCH_HIT', '위협 겁')]
TIER = {'유아기': (10, 30), '유년기': (15, 35), '성장기': (35, 60), '아머체': (60, 90), '성숙기': (60, 90), '완전체': (80, 110), '궁극체': (100, 150)}
def clause(v, m):
    p = v['profile']; i = p.find('『' + m + '』')
    if i < 0: return ''
    s = p[:i]
    a = max(s.rfind('』'), s.rfind('필살기'))
    s = s[a + 1:] if a >= 0 else s[-70:]
    s = re.sub(r'^(살기는|살기인|살기|기는|는|은|과|와|,|\s)+', '', s)
    return s.strip(' 은는,')
def classify(m, cl):
    txt = m + ' ' + cl
    for nm, ty, kw in CAT:
        if any(k in txt for k in kw.split()): return nm, ty
    return '물리', 0
def effect(m, cl):
    txt = m + ' ' + cl
    for nm, e, kw in EFFX:
        if any(k in txt for k in kw.split()): return nm, e
    return '', ''
def pick(ty, tier, e):
    lo, hi = tier; mid = (lo + hi) / 2
    HM = {15, 19, 57, 70, 148, 250, 127, 165}                      # 비전머신(풀베기·공중날기·파도타기·괴력·플래시·바다 회오리·폭포오르기)·발버둥은 빼고
    cand = [x for x in moves if x['type'] == ty and x['power'] > 1 and x['no'] not in HM and not (ty == 0 and ('펀치' in x['name'] or '킥' in x['name']))]
    if not cand: cand = [x for x in moves if x['type'] == 0 and x['power'] > 1]
    def score(x):
        s = abs(x['power'] - mid) + (0 if lo <= x['power'] <= hi else 40)
        if e and x['eff'] == e: s -= 25
        return s
    return sorted(cand, key=score)[:2]
rows = []
for k, v in D.items():
    g = v.get('grade') or ''
    tier = next((TIER[t] for t in TIER if g.startswith(t)), (35, 60))
    for m in v['moves']:
        cl = clause(v, m); cat, ty = classify(m, cl); en, e = effect(m, cl)
        c = pick(ty, tier, e)
        rows.append(dict(no=v['no'], ko=k, grade=g, attr=v.get('attr', ''), move=m, desc=cl, cat=cat, gtype=TYPE.get(ty, ty), effect=en,
                         sugg=[dict(name=x['name'], type=TYPE.get(x['type'], x['type']), power=x['power'], eff=x['eff'], pp=x['pp']) for x in c]))
json.dump(dict(rows=rows, moves=moves), open(S + 'skill_ref.json', 'w'), ensure_ascii=False, indent=0)
print(len(rows), '기술')
for r in rows[:6] + rows[40:52]:
    print('%s %s | %s | %s %s | 설명: %s → %s' % (r['ko'], r['grade'], r['move'], r['cat'], r['effect'], r['desc'][-40:], ', '.join('%s(%s %d)' % (s['name'], s['type'], s['power']) for s in r['sugg'])))
