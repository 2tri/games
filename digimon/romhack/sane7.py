"""7판 누적 (설계자 2026-10-07, 검토 반영): 상성표·트레이너 단계·신대륙 야생
(1) 상성표: 빛(에스퍼 24)→암흑(악 27) 「무효(0)」 → 「2배(20)」. 어둠의 약점 = 빛 (엔젤몬 필살기가 묘티스몬·4천왕에 통하게)
(2) 일반 트레이너 파티: 단계에 비해 레벨이 낮은 디지몬(성숙기<10, 완전체<26, 궁극체<45)은 앞 단계로 (보스·라이벌·간부는 손대지 않음)
(3) 신대륙(관동) 야생 풀숲·물 레벨 ×1.3, 최소 25 (2부 경험치 가뭄)
(4) 검은 톱니로 어둠 갈래 진화 (유대 NPC 없이도), 곤충 마을 상점 2500
patch.build 에서 places2 다음, diff7 앞에 `import sane7; P.log += sane7.apply(P)`"""
import os, re, json
import dmrom, encounters, rules

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


def apply(P):
    log = []
    for fn in (lambda: type_chart(P), lambda: trainer_stages(P), lambda: kanto_wild(P), lambda: black_gear(P)):
        try:
            log.append(fn())
        except Exception as ex:
            log.append('sane7 실패 %r' % (ex,))
    return log
