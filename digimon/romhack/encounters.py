"""롬에서 디지몬 종을 가리키는 곳을 모두 찾기 (A단계: 포켓몬·뺄 종 바꾸기용)
  python3 encounters.py [롬]   → 종류별 개수와 아직 포켓몬·뺄 종을 가리키는 곳 요약
찾는 곳 (표 위치는 데이터·코드 모양으로 찾고, 개수를 pokegold-kr 디스어셈블리와 맞춰 봄):
  풀숲·물(성도·관동·대량발생) / 낚시(무리·시간대) / 박치기 나무 / 벌레잡기 대회 / 트레이너
  이벤트: 선물(givepoke) · 알(giveegg) · 고정 만남(loadwildmon) · 경품(setval·getmonname) · NPC 교환 · 단단지 선물 · 떠돌이 셋
돌려주는 것: [{kind, where, addr(종 바이트 파일 주소), sp, lv}]. 주소는 원본·고친 롬이 같다(스크립트·표를 옮기지 않으므로)."""
import os, re, sys, collections
import dmrom, krtext, wild as W

KR = W.KR
GIVEPOKE, GIVEEGG, SETVAL, SPECIAL, GETMONNAME, LOADWILDMON, STARTBATTLE = 0x2d, 0x2e, 0x15, 0x0f, 0x40, 0x5d, 0x5f


def _grass_water(d, names):
    sp_ok = lambda s: 1 <= s <= 251
    def grass_ok(e):
        return (e[0], e[1]) in names and all(1 <= e[5 + 2 * k] <= 100 and sp_ok(e[6 + 2 * k]) for k in range(21)) and all(e[2 + t] <= 100 for t in range(3))
    def water_ok(e):
        return (e[0], e[1]) in names and e[2] <= 100 and all(1 <= e[3 + 2 * k] <= 100 and sp_ok(e[4 + 2 * k]) for k in range(3))
    out = []
    tabs = [('grass', a, k, False) for a, k in W.find_tables(d, 47, grass_ok)] + [('water', a, k, False) for a, k in W.find_tables(d, 9, water_ok, 4)]
    key = {v[0]: g for g, v in names.items()}
    # 대량발생 표: 풀숲은 35번 도로부터 4개, 물은 탁마산 바깥 1개 (swarm_grass.asm · swarm_water.asm)
    for kind, rec, ok, first, n in (('grass', 47, grass_ok, 'Route35', 4), ('water', 9, water_ok, 'MountMortar1FOutside', 1)):
        g = key[first]; found = []
        i = d.find(bytes(g))
        while i >= 0:
            if all(ok(d[i + rec * j:i + rec * (j + 1)]) for j in range(n)) and d[i + rec * n] == 0xff and not any(t[1] <= i < t[1] + (47 if t[0] == 'grass' else 9) * t[2] for t in tabs): found.append(i)
            i = d.find(bytes(g), i + 1)
        assert len(found) == 1, ('대량발생 표', kind, [hex(x) for x in found])
        tabs.append((kind, found[0], n, True))
    for kind, a, k, swarm in tabs:
        rec = 47 if kind == 'grass' else 9
        for i in range(k):
            e = a + rec * i; place = names[(d[e], d[e + 1])][1]
            tag = ('대량발생 ' if swarm else '') + ('풀숲' if kind == 'grass' else '물')
            if kind == 'grass':
                for t, tn in enumerate(('아침', '낮', '밤')):
                    for s in range(7): out.append(dict(kind=tag, where='%s %s' % (place, tn), addr=e + 6 + 14 * t + 2 * s, sp=d[e + 6 + 14 * t + 2 * s], lv=d[e + 5 + 14 * t + 2 * s]))
            else:
                for s in range(3): out.append(dict(kind=tag, where=place, addr=e + 4 + 2 * s, sp=d[e + 4 + 2 * s], lv=d[e + 3 + 2 * s]))
    return out


def _fish(d):
    out = []
    shore = d.find(bytes([0xb3, 129, 10, 0xd9, 129, 10, 0xff, 98, 10]))            # .Shore_Old (잉어킹·크랩 칸)
    assert shore > 0, '낚시 표를 못 찾음'
    bank = shore // 0x4000; p = 0x4000 + shore % 0x4000
    tab = d.find(bytes([0x80, p & 255, p >> 8]), bank * 0x4000, (bank + 1) * 0x4000)  # FishGroups 첫 항목
    assert tab > 0
    lists = set()
    for g in range(13):
        e = tab + 7 * g
        for r in range(3): lists.add(dmrom.addr(bank, d[e + 1 + 2 * r] | d[e + 2 + 2 * r] << 8))
    for a in sorted(lists):
        while True:
            ch, sp, lv = d[a:a + 3]
            if sp: out.append(dict(kind='낚시', where='낚시표 %X' % a, addr=a + 1, sp=sp, lv=lv))
            a += 3
            if ch == 0xff: break
    t = d.find(bytes([222, 20, 120, 20, 222, 40, 120, 40]))                          # TimeFishGroups (코산호·별가사리 칸)
    assert t > 0, '시간대 낚시 표를 못 찾음'
    for i in range(22):
        for h, tn in ((0, '낮'), (2, '밤')):
            out.append(dict(kind='낚시', where='시간대 낚시 %d %s' % (i, tn), addr=t + 4 * i + h, sp=d[t + 4 * i + h], lv=d[t + 4 * i + h + 1]))
    return out


def _trees_contest(d):
    out = []
    a = d.find(bytes([50, 48, 15, 30, 48, 15, 10, 63, 15, 5, 63, 15, 5, 49, 15, 0xff]))   # TreeMonSet_City
    assert a > 0, '박치기 나무 표를 못 찾음'
    names = ['도시 보통', '도시 드묾', '숲 보통', '숲 드묾', '협곡 보통', '협곡 드묾', '바위']           # 금판: 은판 숲 표는 없음
    for n in names:
        while d[a] != 0xff:
            out.append(dict(kind='박치기 나무', where=n, addr=a + 1, sp=d[a + 1], lv=d[a + 2])); a += 3
        a += 1
    c = d.find(bytes([20, 10, 7, 18, 20, 13, 7, 18]))                                   # ContestMons
    assert c > 0, '벌레잡기 대회 표를 못 찾음'
    while True:
        out.append(dict(kind='벌레잡기 대회', where='자연 공원', addr=c + 1, sp=d[c + 1], lv=d[c + 2]))
        if d[c] == 0xff: break
        c += 4
    return out


def _events(d):
    """디스어셈블리 스크립트에서 종이 들어간 명령을 읽어, 같은 바이트 모양을 롬에서 찾음 (개수 맞춰 봄)"""
    C = {}
    for l in open(os.path.join(KR, 'constants/pokemon_constants.asm')):
        m = re.match(r'\s*const (\w+)', l)
        if m: C[m.group(1)] = len(C) + 1
    out = []; want = collections.Counter()
    for p in sorted(os.listdir(os.path.join(KR, 'maps'))):
        if not p.endswith('.asm'): continue
        for l in open(os.path.join(KR, 'maps', p)):
            m = re.match(r'\s*(givepoke|giveegg|loadwildmon)\s+(\w+),\s*(\w+)', l)
            if m and m.group(2) in C:
                lv = int(m.group(3)) if m.group(3).isdigit() else 5
                want[(m.group(1), C[m.group(2)], lv, p[:-4])] += 1
    op = {'givepoke': GIVEPOKE, 'giveegg': GIVEEGG, 'loadwildmon': LOADWILDMON}
    seen = set()
    for (cmd, sp, lv, mp), n in sorted(want.items()):
        pat = bytes([op[cmd], sp, lv]); hits = []
        i = d.find(pat)
        while i >= 0:
            hits.append(i)
            i = d.find(pat, i + 1)
        hits = [h for h in hits if h not in seen]
        if len(hits) != n: print('  ! %s %d Lv%d (%s): %d곳 찾음 / 디스어셈블리 %d곳' % (cmd, sp, lv, mp, len(hits), n))
        for h in hits[:n]:
            seen.add(h)
            kind = {'givepoke': '선물', 'giveegg': '알', 'loadwildmon': '고정 만남'}[cmd]
            out.append(dict(kind=kind, where=mp, addr=h + 1, sp=sp, lv=lv))
            # 경품: setval X / special … / givepoke X  그리고 그 앞의 getmonname X
            if cmd == 'givepoke' and d[h - 5] == SETVAL and d[h - 4] == sp and d[h - 3] == SPECIAL:
                out.append(dict(kind='경품 확인', where=mp, addr=h - 4, sp=sp, lv=lv))
                g = d.rfind(bytes([GETMONNAME, sp]), h - 48, h)
                if g > 0: out.append(dict(kind='경품 이름', where=mp, addr=g + 1, sp=sp, lv=lv))
    # NPC 교환 6개 (요청 종, 주는 종) — 첫 항목: 슬리프 ↔ 알통몬, 별명 「근육」
    t = d.find(bytes([96, 66]) + krtext.encode('근육')) - 1
    assert t > 0, 'NPC 교환 표를 못 찾음'
    for i in range(6):
        e = t + 32 * i
        out.append(dict(kind='교환(받는 종)', where='NPC 교환 %d' % (i + 1), addr=e + 1, sp=d[e + 1], lv=0))
        out.append(dict(kind='교환(주는 종)', where='NPC 교환 %d' % (i + 1), addr=e + 2, sp=d[e + 2], lv=0))
    # 단단지 선물 (진청시티): ld a, SHUCKLE / ld [..], a / ld a, 15 … cp SHUCKLE / jr nz
    s = re.search(rb'\x3e\xd5\xea..\x3e\x0f', d, re.S)
    assert s, '단단지 선물 코드를 못 찾음'
    out.append(dict(kind='선물', where='진청시티 단단지', addr=s.start() + 1, sp=213, lv=15))
    c = d.find(b'\xfe\xd5\x20', s.start(), s.start() + 0x200)
    if c > 0: out.append(dict(kind='선물 돌려받기', where='진청시티 단단지', addr=c + 1, sp=213, lv=15))
    # 떠돌이 셋: ld a, RAIKOU / ld [..], a / ld a, ENTEI / … / ld a, SUICUNE
    r = re.search(rb'\x3e\xf3\xea..\x3e\xf4\xea..\x3e\xf5\xea', d, re.S)
    assert r, '떠돌이 초기화 코드를 못 찾음'
    for k, sp in enumerate((243, 244, 245)):
        out.append(dict(kind='떠돌이', where='떠돌이 %d' % (k + 1), addr=r.start() + 1 + 5 * k, sp=sp, lv=40))
    return out


def find_all(r):
    d = bytes(r.base); names = W.map_names()
    out = _grass_water(d, names) + _fish(d) + _trees_contest(d) + _events(d)
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(KR, 'data/trainers/party_pointers.asm')).read())
    for t in r.trainers(len(groups)):
        for lv, sp, a in t['mons']:
            out.append(dict(kind='트레이너', where='%s %s' % (groups[t['group']], t['name']), addr=a, sp=sp, lv=lv))
    return out


if __name__ == '__main__':
    r = dmrom.Rom(sys.argv[1] if len(sys.argv) > 1 else dmrom.default_rom())
    S = find_all(r)
    print('찾은 곳 %d' % len(S))
    for k, n in collections.Counter(s['kind'] for s in S).most_common(): print('  %-10s %d' % (k, n))
