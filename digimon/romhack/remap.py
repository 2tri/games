"""A단계: 롬이 가리키는 포켓몬·뺄 디지몬을 남길 디지몬으로 바꾸기 (patch.py 가 부름)
대응표: mapping.csv (칸 → 대체칸, 계획종). 계획종이 그림과 함께 그 칸에 설치되면 그 칸을 그대로 씀.
야생(풀숲·물·대량발생·낚시·박치기 나무·벌레잡기 대회)은 레벨로 단계를 낮춤:
  Lv20 미만 = 유년기·성장기만, Lv20 이상 = 성숙기·아머체까지. 완전체·궁극체는 야생에 안 나옴.
  스타팅(아구몬·파피몬·브이몬)과 선물 전용(플롯트몬)은 야생에 안 나오게 다른 종으로.
트레이너·이벤트는 대체칸 그대로 (상대 파티는 C단계에서 다시 짬)."""
import csv, json, os, re
import krtext
from wild import KR

HERE = os.path.dirname(os.path.abspath(__file__))
WILD = {'풀숲', '물', '대량발생 풀숲', '대량발생 물', '낚시', '박치기 나무', '벌레잡기 대회'}
LOW = {'유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '유년기', '성장기'}
MID = LOW | {'성숙기', '아머체'}
WILD_LV = 20
# 게임 코너 경품 = 야생에 안 나오는 성장기 (어드벤처·02 파트너): 금빛 파닥몬·추추몬·쉬라몬, 무지개 텐타몬·팔몬·호크몬
PRIZE = {('GoldenrodGameCorner', 63): 175, ('GoldenrodGameCorner', 23): 69, ('GoldenrodGameCorner', 27): 69, ('GoldenrodGameCorner', 147): 116,
         ('CeladonGameCornerPrizeRoom', 122): 43, ('CeladonGameCornerPrizeRoom', 133): 1, ('CeladonGameCornerPrizeRoom', 137): 21}
# 야생에 안 내보낼 종 → 대신 나올 종: 스타팅 줄, 선물 전용(플롯트몬), 경품 6종
WILD_SUB = {4: 161, 7: 74, 133: 16, 194: 17, 173: 16,
            175: 16, 69: 10, 116: 129, 43: 10, 1: 161, 21: 16}
# 한 단계 아래 (야생에서 레벨이 낮을 때). 앞 단계가 롬에 없거나 스타팅이면 비슷한 종으로
DOWN = {2: 1, 3: 2, 5: 161, 6: 212, 8: 74, 9: 217, 11: 10, 12: 11, 14: 69, 15: 14, 17: 16, 18: 17, 22: 21, 25: 172, 27: 74, 28: 27,
        35: 175, 39: 174, 40: 174, 42: 93, 44: 43, 45: 44, 52: 41, 56: 61, 57: 56, 61: 60, 62: 61, 70: 69, 93: 41, 102: 161, 105: 74,
        111: 74, 112: 111, 117: 116, 126: 161, 130: 129, 131: 186, 134: 129, 135: 60, 136: 161, 140: 60, 145: 5, 167: 10, 168: 167,
        172: 60, 174: 175, 176: 174, 186: 129, 194: 16, 195: 194, 197: 195, 212: 5, 217: 8, 230: 117}
# 새 칸 (slots.json) 이 설치됐을 때의 아래 단계
DOWN_NEW = {'쉘몬': 116, '모노크로몬': 74, '워매몬': 161, '시드라몬': 129, '켄터스몬': 60, '고스몬': 41, '쿠가몬': 10}
# 칸이 아니라 자리마다 따로 정한 것: (종류, 맵, 원래 칸) → 새 칸
SITE = {('선물', 'BillsFamilysHouse', 133): 173}                     # 빌의 이브이 → 플롯트몬 (유대 갈래 선물)
for (w, sp), t in PRIZE.items():
    for k in ('선물', '경품 확인', '경품 이름'): SITE[(k, w, sp)] = t


def load():
    M = {}
    for row in csv.DictReader(open(os.path.join(HERE, 'mapping.csv'), encoding='utf-8-sig')):
        M[int(row['칸'])] = (int(row['대체칸']), row['계획종'].strip())
    return M


def grades(r, slots):
    G = {int(k): v['grade'] for k, v in json.load(open(os.path.join(HERE, 'grades.json'))).items()}
    G.update({161: '유년기Ⅱ', 212: '완전체', 217: '완전체'})
    for no, m in slots.items(): G[no] = m['grade']
    return G


def target(sp, site, M, G, name_of, keep):
    t = SITE.get((site['kind'], site['where'], sp))
    if t is None:
        if sp in M and not (M[sp][1] and name_of(sp) == M[sp][1]): t = M[sp][0]   # 계획종이 설치된 칸은 그대로
        else: t = sp
    if site['kind'] in WILD:
        t = WILD_SUB.get(t, t)
        ok = MID if site['lv'] >= WILD_LV else LOW
        for _ in range(6):
            if G.get(t, '성숙기') in ok: break
            t = DOWN_NEW.get(name_of(t)) or DOWN.get(t, t); t = WILD_SUB.get(t, t)
    return t


def prize_menu(P, a, new_of):
    """경품 메뉴 글 3줄 ('이름   값@') 의 이름을 바꿈. new_of(원래 이름) → 새 이름. 칸 수(화면 폭)는 그대로, 바이트 합은 원래와 같게 빈칸으로 맞춤"""
    d = P.d; items = []; p = a
    for _ in range(3):
        j = d.index(0x50, p); s = krtext.decode(d, p, j)
        m = re.match(r'(\S+)(\s+)(\d+)$', s); assert m, s
        items.append([m.group(1), len(m.group(2)), m.group(3)]); p = j + 1
    budget = p - a
    width = max(len(old) + sp + len(price) for old, sp, price in items)      # 값의 오른쪽 끝 칸 (줄마다 같게)
    blen = lambda its: sum(len(krtext.encode(nm)) + sp + len(price) + 1 for nm, sp, price in its)
    while True:
        new = [[new_of(old), width - len(new_of(old)) - len(price), price] for old, sp, price in items]
        if blen(new) <= budget: break
        width -= 1; assert min(x[1] for x in new) > 1
    tail = budget - blen(new)                                           # 남는 바이트는 마지막 줄 끝 빈칸 (보이지 않음)
    out = b''.join(krtext.encode(nm) + b'\x7f' * sp + krtext.encode(price) + (b'\x7f' * tail if k == 2 else b'') + b'\x50' for k, (nm, sp, price) in enumerate(new))
    assert len(out) == budget; P.put(a, out)
    return [x[0] for x in new]


def apply(P, sites, slots, keep):
    """sites: encounters.find_all 결과 (원본 롬 주소). slots: {칸: slots.json 항목} (설치된 새 종)"""
    r = P.r; d = P.d; M = load(); G = grades(r, slots)
    name_of = r.name
    changed = 0
    for s in sites:
        sp = d[s['addr']]
        t = target(sp, s, M, G, name_of, keep)
        if t != sp: d[s['addr']] = t; changed += 1
        s['new'] = t
    # 경품 메뉴 글: 금빛시티 (캐이시·아보·미뇽 자리), 무지개시티 (마임맨·이브이·폴리곤 자리)
    base = bytes(r.base); n_menu = 0
    orig = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(KR, 'data/pokemon/names.asm')) if 'dname' in l]
    menus = []
    for first, where in (('캐이시', 'GoldenrodGameCorner'), ('마임맨', 'CeladonGameCornerPrizeRoom')):
        e = krtext.encode(first); i = base.find(e)
        while i >= 0:
            if base[i + len(e)] == 0x7f:
                new_of = lambda old, w=where: name_of(target(orig.index(old) + 1, {'kind': '경품 확인', 'where': w, 'lv': 0}, M, G, name_of, keep))
                menus.append(prize_menu(P, i, new_of))
            i = base.find(e, i + 1)
    n_menu = len(menus)
    # 빌 할아버지가 보여 달라는 종 6개: ifnotequal 종, .WrongPokemon (같은 곳으로 뛰는 6개)
    want = [108, 43, 120, 58, 37, 172]; cand = {}
    for sp in want:
        for m in re.finditer(re.escape(bytes([0x07, sp])) + b'(..)', base, re.S): cand.setdefault(m.group(1), []).append((sp, m.start() + 1))
    hit = [v for v in cand.values() if sorted(x[0] for x in v) == sorted(want)]
    assert len(hit) == 1, '빌 할아버지 확인 자리를 하나로 못 찾음'
    for sp, a in hit[0]:
        t = target(sp, {'kind': '확인', 'where': 'BillsHouse', 'lv': 0}, M, G, name_of, keep)
        d[a] = t
    P.log.append('A단계 바꾸기: %d곳 (종 자리 %d), 경품 메뉴 %s, 빌 할아버지 확인 6개' % (changed, len(sites), ' / '.join('·'.join(m) for m in menus)))
    return changed
