"""7판 누적 (설계자 2026-10-07, 검토 반영): 상성표·트레이너 단계·신대륙 야생
(1) 상성표: 빛(에스퍼 24)→암흑(악 27) 「무효(0)」 → 「2배(20)」. 어둠의 약점 = 빛 (엔젤몬 필살기가 묘티스몬·4천왕에 통하게)
(2) 일반 트레이너 파티: 단계에 비해 레벨이 낮은 디지몬(성숙기<10, 완전체<26, 궁극체<45)은 앞 단계로 (보스·라이벌·간부는 손대지 않음)
(3) 신대륙(관동) 야생 풀숲·물 레벨 ×1.3, 최소 25 (2부 경험치 가뭄)
(4) 검은 톱니로 어둠 갈래 진화 (유대 NPC 없이도), 곤충 마을 상점 2500
patch.build 에서 places2 다음, diff7 앞에 `import sane7; P.log += sane7.apply(P)`"""
import os, re, json
import dmrom, encounters, rules, remap

HERE = os.path.dirname(os.path.abspath(__file__))
PSYCHIC, DARK = 24, 27
BOSS_GROUPS = {'Falkner', 'Bugsy', 'Whitney', 'Morty', 'Chuck', 'Jasmine', 'Pryce', 'Clair', 'Will', 'Koga', 'Bruno', 'Karen', 'Champion',
               'Brock', 'Misty', 'LtSurge', 'Erika', 'Janine', 'Sabrina', 'Blaine', 'Blue', 'Red', 'Rival1', 'Rival2', 'ExecutiveM', 'ExecutiveF'}
STAGE_MIN = {'성숙기': 10, '완전체': 26, '궁극체': 45}
KANTO = ('태초마을', '상록시티', '회색시티', '블루시티', '갈색시티', '보라타운', '노랑시티', '무지개시티', '연분홍시티', '홍련마을', '은빛', '달맞이', '디그다', '돌산', '연결동굴')


def type_chart(P):
    d = bytes(P.d)
    hits = []
    for m in re.finditer(re.escape(bytes([PSYCHIC, DARK, 0])), d):
        i = m.start()
        if i < 3:
            continue
        before_ok = d[i - 3] < 28 and d[i - 2] < 28 and d[i - 1] in (0, 5, 10, 20)
        after_ok = d[i + 3] < 28 or d[i + 3] in (0xfe, 0xff)
        if before_ok and after_ok:
            hits.append(i)
    if len(hits) != 1:
        return '상성표: 빛→암흑 항목 후보 %d개 %s — 안 바꿈' % (len(hits), ['%X' % h for h in hits])
    P.put(hits[0] + 2, bytes([20]))
    return '상성표: 빛(에스퍼)→암흑(악) 무효 → 2배 (%X)' % hits[0]


def grades(P):
    r = P.r
    G = {}
    for k, v in json.load(open(os.path.join(HERE, 'grades.json'), encoding='utf-8')).items():
        if v.get('grade') and r.name(int(k)) == v['name']:
            G[int(k)] = v['grade']
    SL = {m['name']: m['grade'] for m in json.load(open(os.path.join(HERE, 'slots.json'), encoding='utf-8'))['mons']}
    for n in range(1, dmrom.NUM + 1):
        nm = r.name(n)
        if nm in SL:
            G[n] = SL[nm]
    for nm, v in rules.PALSWAP.items():
        if r.name(v[1]) == nm:
            G[v[1]] = v[2]
    return G


def trainer_stages(P):
    P.r.d = P.d
    r = P.r
    G = grades(P)
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    prevo = {}
    for n in range(1, dmrom.NUM + 1):
        for e in r.evos_attacks(n)[0]:
            if 1 <= e[0] <= 10:
                prevo.setdefault(e[-1], n)
    changed = []
    stuck = []
    # 10판(R33): 앞 단계가 없는 종은 게임에 이미 나오는(야생·트레이너) 같은 타입·맞는 단계 종 중 종족값 합이 가장 가까운 것으로
    used = {sp for t in r.trainers(len(groups)) for _, sp, _ in t['mons']}
    for s in encounters.find_all(dmrom.Rom(dmrom.default_rom())):
        if s['kind'] in ('풀숲', '물', '낚시') and 1 <= P.d[s['addr']] <= dmrom.NUM: used.add(P.d[s['addr']])
    stage_for = lambda lv: max([g_ for g_, m_ in STAGE_MIN.items() if lv >= m_], key=lambda g_: STAGE_MIN[g_], default='성장기')
    def substitute(sp, lv):
        want = stage_for(lv)
        bs = r.base_stats(sp)
        tot = lambda n: sum(r.base_stats(n)[k] for k in ('hp', 'atk', 'def', 'spd', 'sat', 'sdf'))
        cands = [n for n in used if G.get(n) == want and r.name(n) != rules.EMPTY_NAME and not r.name(n).startswith('-')]
        same = [n for n in cands if bs['type'][0] in r.base_stats(n)['type']]
        pool = same or cands
        return min(pool, key=lambda n: abs(tot(n) - tot(sp))) if pool else None
    for t in r.trainers(len(groups)):
        g = groups[t['group']]
        if g in BOSS_GROUPS or g in rules.GRUNT_GROUPS:
            continue
        for lv, sp, a in t['mons']:
            sp0 = sp
            n_ = 0
            while G.get(sp) in STAGE_MIN and lv < STAGE_MIN[G[sp]] and sp in prevo and n_ < 3:
                sp = prevo[sp]
                n_ += 1
            if G.get(sp) in STAGE_MIN and lv < STAGE_MIN[G[sp]]:
                alt = substitute(sp, lv)
                if alt: sp = alt
            if sp != sp0:
                P.d[a] = sp
                changed.append('%s %s %s Lv%d→%s' % (g, t['name'], r.name(sp0), lv, r.name(sp)))
            elif G.get(sp) in STAGE_MIN and lv < STAGE_MIN[G[sp]]:
                stuck.append('%s Lv%d' % (r.name(sp), lv))
    P.r.d = P.d
    return '트레이너 단계 맞춤 %d칸%s%s' % (len(changed),
                                       (': ' + ', '.join(changed[:10]) + (' …' if len(changed) > 10 else '')) if changed else '',
                                       (' / 앞 단계 없어 그대로: ' + ', '.join(sorted(set(stuck))[:10])) if stuck else '')


def kanto_wild(P):
    n = 0
    for s in encounters.find_all(dmrom.Rom(dmrom.default_rom())):
        if s['kind'] not in ('풀숲', '물'):
            continue
        w = s['where']
        m = re.match(r'(\d+)번 도로', w)
        if not ((m and int(m.group(1)) <= 28) or w.startswith(KANTO)):
            continue
        lv = P.d[s['addr'] - 1]
        if 1 <= lv <= 100:
            P.d[s['addr'] - 1] = max(25, min(100, int(round(lv * 1.3))))
            n += 1
    return '신대륙 야생 레벨 ×1.3 (최소 25): %d칸' % n


def black_gear(P):
    """검은 톱니 = 어둠 진화 도구 (사용자 10/7 「유대 NPC 말고 다른 방법」): 유대 낮음(7)·암흑(9) 갈래가 있는 종마다 그 갈래를 도구 진화(2)로도 열어 둠.
    유대와 상관없이, 대상 단계의 최소 레벨(정상보다 3 낮은 성숙기 13·완전체 27·궁극체 42)이 되면 (진화 코드의 표). 곤충 마을 상점에서도 팜"""
    import digi2
    P.r.d = P.d
    r = P.r
    item = rules.BLACK_GEAR['item']
    added = []
    nofit = []
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    for light, (dark, lv) in getattr(rules, 'DARK_PAIRS', {}).items():       # 빛 종마다 어둠 갈래(종류 9: 유대 70 미만 + 문장 3) 보장
        if light not in N or dark not in N:
            continue
        ev, mv = r.evos_attacks(N[light])
        ev = [tuple(e) for e in ev if 1 <= e[0] <= 10 and e[0] != 5]
        if any(e[-1] == N[dark] and e[0] in (7, 9) for e in ev):
            continue
        try:
            P.evos(N[light], [(9, lv, N[dark])] + ev, mv)
        except MemoryError:
            nofit.append('%s→%s' % (light, dark))
        P.r.d = P.d
    for n in range(1, dmrom.NUM + 1):
        ev, mv = r.evos_attacks(n)
        ev = [tuple(e) for e in ev if 1 <= e[0] <= 10 and e[0] != 5]
        bad = [e[-1] for e in ev if e[0] in (7, 9)]
        if not bad or any(e[0] == 2 and e[1] == item for e in ev):
            continue
        try:
            P.evos(n, [(2, item, bad[0])] + ev, mv)
            added.append('%s→%s' % (r.name(n), r.name(bad[0])))
        except MemoryError:      # 진화 뱅크 0x10 이 꽉 차면 그 종만 건너뜀
            nofit.append('%s→%s' % (r.name(n), r.name(bad[0])))
    P.r.d = P.d
    MIN = {'성숙기': 13, '아머체': 16, '완전체': rules.COMPLETE_LV - 3, '궁극체': rules.ULTIMATE_LV - 3}   # 암흑 진화는 정상보다 3 낮게 (사용자 10/7 「부정하게 올라간 느낌」)
    tab = getattr(P, 'gear_table', None)
    nfill = 0
    if tab:
        G = grades(P)
        for n in range(1, dmrom.NUM + 1):
            lv = MIN.get(G.get(n), 0)
            P.d[tab + n - 1] = lv
            nfill += lv > 0
    try:
        mart = digi2.add_to_mart(P, 'Azalea', [item])
    except Exception as ex:
        mart = '상점 실패 %r' % (ex,)
    try:
        P.put(digi2.item_tables(P)[0] + 7 * (item - 1), (2500).to_bytes(2, 'little'))      # 값
    except Exception:
        pass
    return '검은 톱니 어둠 진화 %d종 (%s)%s / 최소 레벨 표 %d종(성숙기 13·완전체 %d·궁극체 %d) / %s' % (
        len(added), ', '.join(added), (' — 진화 뱅크 자리 없어 못 넣음 %d: %s' % (len(nofit), ', '.join(nofit))) if nofit else '', nfill, rules.COMPLETE_LV - 3, rules.ULTIMATE_LV - 3, mart)


def evo_kinds(P):
    """9판: 완전체로 가는 레벨 진화(1)는 자기 문장(8)으로, 궁극체로 가는 것은 아무 문장(10)으로 — 설계 J「진화 = 문장 개수」(R27).
    롬 원본에 남은 야돈→야도란 Lv37(개굴몬→왕개굴몬)·황제드라몬→황제파이터 Lv55 같은 줄"""
    P.r.d = P.d
    r = P.r
    G = grades(P)
    fixed = []
    for n in range(1, dmrom.NUM + 1):
        ev, mv = r.evos_attacks(n)
        ev = [tuple(e) for e in ev if 1 <= e[0] <= 10 and e[0] != 5]
        new = []
        chg = False
        for e in ev:
            g = G.get(e[-1])
            if e[0] == 1 and g == '완전체':
                new.append((8, e[1], e[2])); chg = True
            elif e[0] == 1 and g == '궁극체':
                new.append((10, e[1], e[2])); chg = True
            else:
                new.append(e)
        if chg:
            P.evos(n, new, mv)
            P.r.d = P.d
            fixed.append('%s→%s' % (r.name(n), '·'.join(r.name(e[-1]) for e in new if e not in ev)))
    return '완전체·궁극체 레벨 진화 → 문장 종류 %d줄%s' % (len(fixed), ': ' + ', '.join(fixed) if fixed else '')


BASIC_ATTACK = {0x00: 33, 0x01: 2, 0x02: 16, 0x03: 40, 0x04: 189, 0x05: 88, 0x07: 210, 0x08: 122, 0x09: 232,      # 타입 → 기본 공격기 (몸통박치기·가라테촙·바람·독침·진흙·돌·연속베기·핥기·메탈클로)
                0x14: 52, 0x15: 55, 0x16: 22, 0x17: 84, 0x18: 93, 0x19: 181, 0x1a: 44, 0x1b: 44}      # 불꽃세례·물대포·덩굴채찍·전기쇼크·염동력·눈보라·물기


def learnsets_attack(P):
    """11판(R29): 종마다 레벨 1~100 의 「마지막 4기술」(FillMoves: 같은 기술 건너뜀, 5개째면 앞을 밂)에 위력 있는 기술이 하나는 있게.
    없으면 그 레벨에 배우는 보조기를 타입 기본 공격기(없으면 몸통박치기)로 바꿈 — 목록 길이가 같아 진화 뱅크·트레이너 뱅크를 안 씀 (트레이너 뱅크 0x0e 가 꽉 차 R29_FILL 은 못 켬)"""
    P.r.d = P.d
    r = P.r
    mt = bytes(P.d).find(bytes([1, 0, 40, 0, 255, 35, 0]))
    if mt < 0: return 'R29 학습표: 기술 표 못 찾음'
    powr = lambda mv: P.d[mt + 7 * (mv - 1) + 2] if 1 <= mv <= 251 else 0

    def window(mv_list, lv):
        ms = []
        for l, m in mv_list:
            if l <= lv and m not in ms:
                ms.append(m)
                if len(ms) > 4: ms.pop(0)
        return ms
    fixed = []
    for n in range(1, dmrom.NUM + 1):
        nm = r.name(n)
        if nm == rules.EMPTY_NAME or nm.startswith('-'): continue
        ev, mv = r.evos_attacks(n)
        mv = [list(x) for x in mv]
        if not mv: continue
        t1 = r.base_stats(n)['type'][0]
        chg = []
        for _ in range(8):
            bad = next((lv for lv in sorted({1} | {l for l, _ in mv}) if not any(powr(m) > 0 for m in window(mv, lv))), None)
            if bad is None: break
            k = max((i for i, (l, m) in enumerate(mv) if l <= bad and powr(m) == 0), default=None)      # 그 레벨까지 배운 마지막 보조기
            if k is None: break
            known = {m for _, m in mv}
            cand = [BASIC_ATTACK.get(t1, 33), 33, 10, 64, 29]      # 타입 기본기 → 몸통박치기 → 할퀴기 → 쪼기 → 박치기
            new = next((c for c in cand if c not in known and powr(c) > 0), None)
            if new is None: break
            chg.append('Lv%d %d→%d' % (mv[k][0], mv[k][1], new))
            mv[k][1] = new
        if chg:
            P.evos(n, [tuple(e) for e in ev], [tuple(x) for x in mv])
            P.r.d = P.d
            fixed.append('%s(%s)' % (nm, ', '.join(chg)))
    return 'R29 학습표 공격기 보장 %d종%s' % (len(fixed), ': ' + ', '.join(fixed) if fixed else '')


def no_babies_wild(P):
    """19판: 야생 칸의 유년기(BABY_KEEP 빼고)를 그 종의 레벨 진화 대상(성장기)으로. 레벨은 그대로 (Lv2~5 아구몬처럼)"""
    if not getattr(rules, 'NO_BABIES', False): return '유년기 그대로 (NO_BABIES 꺼짐)'
    P.r.d = P.d
    r = P.r
    G = grades(P)
    try:      # 19판 보강: grades.json 에 없는 1.4 기본 유년기(코로몬 161)는 order/allmons.json 의 단계를 씀 (없으면 코로몬 야생이 그대로 남음)
        for m_ in json.load(open(os.path.join(HERE, 'order', 'allmons.json'), encoding='utf-8')):
            if m_.get('grade') and 1 <= m_['no'] <= dmrom.NUM and r.name(m_['no']) == m_['ko']: G.setdefault(m_['no'], m_['grade'])
    except Exception: pass
    nxt = {}
    for n in range(1, dmrom.NUM + 1):
        for e in r.evos_attacks(n)[0]:
            if e[0] == 1 and 1 <= e[-1] <= dmrom.NUM: nxt.setdefault(n, e[-1])
    cnt = {}
    stuck = set()
    for s in encounters.find_all(dmrom.Rom(dmrom.default_rom())):
        if s['kind'] not in remap.WILD: continue      # 야생 칸만 (선물·알·고정 만남은 안 건드림)
        sp = P.d[s['addr']]
        if not (1 <= sp <= dmrom.NUM) or not (G.get(sp) or '').startswith('유') or r.name(sp) in rules.BABY_KEEP: continue
        t = sp
        for _ in range(3):
            if not (G.get(t) or '').startswith('유'): break
            if t not in nxt: break
            t = nxt[t]
        if (G.get(t) or '').startswith('유'):
            stuck.add(r.name(sp)); continue
        P.d[s['addr']] = t
        k_ = '%s→%s' % (r.name(sp), r.name(t)); cnt[k_] = cnt.get(k_, 0) + 1
    P.r.d = P.d
    return '야생 유년기 → 성장기 %d칸: %s%s' % (sum(cnt.values()), ', '.join('%s %d' % kv for kv in cnt.items()) or '없음', (' / 진화 대상 없어 그대로: ' + ', '.join(sorted(stuck))) if stuck else '')


def apply(P):
    log = []
    for fn in (lambda: type_chart(P), lambda: no_babies_wild(P), lambda: trainer_stages(P), lambda: kanto_wild(P), lambda: black_gear(P), lambda: evo_kinds(P), lambda: learnsets_attack(P)):
        try:
            log.append(fn())
        except Exception as ex:
            log.append('sane7 실패 %r' % (ex,))
    return log
