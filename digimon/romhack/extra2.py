"""추가 묶음 (설계자 2026-10-06): 도감 순서 · 성장 곡선 · 기본 이름 · 마일도 대사

1. 새 도감 순서(NewPokedexOrder, 251바이트) = order/roster.csv 줄 순서(파트너 → 파일 섬 → …) + 나머지 디지몬 + 빈 칸
2. 성장 곡선: rules.GROWTH_PARTNER 줄(파트너 8줄)은 MEDIUM_SLOW(3), 그 밖 디지몬은 MEDIUM_FAST(0). 능력치 표 22번째 바이트
3. 기본 이름: 심볼 이름에 PlayerName/RivalName 이 든 글(「골드」「실버」 류)을 rules.DEFAULT_NAMES 로 (같은 길이 이하만)
4. 브이몬 교환 NPC (2판): 관동 교환 NPC 주는 종 → 브이몬. (마일도 대사는 story2 로 옮김)
patch.build 에서 types2 다음에 `import extra2; P.log += extra2.apply(P)`"""
import os, re, csv, struct
import dmrom, krtext, rules, encounters
from dmrom import addr


def dex_order(P, S):
    tab = S['NewPokedexOrder']
    d = bytes(P.d)
    assert sorted(d[tab:tab + 251]) == list(range(1, 252)), '새 도감 순서 표가 아님'
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    order = []
    for row in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'order', 'roster.csv'), encoding='utf-8-sig')):
        nm = row['롬이름'] or row['종']
        if nm in N and N[nm] not in order:
            order.append(N[nm])
    rest = [n for n in range(1, dmrom.NUM + 1) if n not in order and P.r.name(n) != rules.EMPTY_NAME]
    empty = [n for n in range(1, dmrom.NUM + 1) if n not in order and n not in rest]
    full = order + rest + empty
    assert sorted(full) == list(range(1, 252))
    P.put(tab, bytes(full))
    return '도감 순서: 로스터 %d + 그 밖 %d + 빈 칸 %d' % (len(order), len(rest), len(empty))


def growth(P):
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    n3 = n0 = 0
    partner = set(rules.GROWTH_PARTNER)
    for nm, no in N.items():
        if nm == rules.EMPTY_NAME:
            continue
        g = 3 if nm in partner else 0
        P.d[P.r.bs + 0x20 * (no - 1) + 22] = g
        if g:
            n3 += 1
        else:
            n0 += 1
    return '성장 곡선: 파트너 줄 %d종 MEDIUM_SLOW, 그 밖 %d종 MEDIUM_FAST' % (n3, n0)


def _keys(S):
    for at in ('syms', 'd', 'names', 'table', 'map', 'sym'):
        v = getattr(S, at, None)
        if isinstance(v, dict):
            return list(v.keys())
    try:
        return list(S.keys())
    except Exception:
        return []


def default_names(P, S):
    """2판: 심볼 대신 롬 전체에서 「골드@」「실버@」(이름표 끝표 뒤에 오는 것)를 같은 길이의 새 이름으로"""
    out = []
    d = bytes(P.d)
    for old, new in rules.DEFAULT_NAMES:
        ob, nb = krtext.encode(old) + b'P', krtext.encode(new) + b'P'
        if len(nb) != len(ob):
            out.append('%s→%s 길이 다름' % (old, new))
            continue
        n = 0
        i = d.find(ob)
        while i >= 0:
            if i == 0 or d[i - 1] in (0x50, 0x7f, 0x00):
                P.put(i, nb)
                n += 1
            i = d.find(ob, i + 1)
        out.append('%s→%s %d곳' % (old, new, n))
    return '기본 이름: ' + ', '.join(out)


def trade_vmon(P):
    """묶음 H (e): 관동 교환 NPC(원본 주는 종 프테라 142 → 레어코일 82 → 코뿌리 112 순)의 주는 종 → 브이몬, 받는 종 → 뿔몬. NPCTrades 3f:4c24, 32바이트"""
    P.r.d = P.d
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    if '브이몬' not in N:
        return '브이몬 교환: 브이몬 칸 없음'
    B_ = dmrom.Rom(dmrom.default_rom())
    nt = addr(0x3f, 0x4c24)
    where = {142: '14번 도로', 82: '발전소', 112: '회색시티'}
    for want in (142, 82, 112):
        for k in range(6):
            e = nt + 32 * k
            if B_.d[e + 2] == want:
                P.put(e + 1, bytes([N.get('뿔몬', P.d[e + 1])]))
                P.put(e + 2, bytes([N['브이몬']]))
                b_ = krtext.encode('브이몬') + b'P'
                P.put(e + 3, b_ + b'P' * (11 - len(b_)))
                return '브이몬 교환: %s NPC(%d번째) 주는 종 → 브이몬, 받는 종 → 뿔몬' % (where[want], k + 1)
    return '브이몬 교환: 관동 교환 NPC 못 찾음 (원본 주는 종 %s)' % [B_.d[nt + 32 * k + 2] for k in range(6)]


def boss_text(P, S):
    import boss2
    g, i = boss2.pick()
    KR = encounters.KR
    tc = boss2._consts(os.path.join(KR, 'constants', 'trainer_constants.asm'), 'trainerclass')
    cls = g.upper()
    nick = next((n for (c, n), k in tc.items() if c == cls and k == i + 1), None)
    assert nick, '트레이너 이름 상수'
    for mp in boss2.KANTO_MAPS:
        f = os.path.join(KR, 'maps', mp + '.asm')
        if not os.path.exists(f):
            continue
        txt = open(f, encoding='utf-8', errors='ignore').read()
        m = re.search(r'trainer\s+(?:EVENT\w+,\s*)?%s,\s*%s,\s*(?:EVENT_\w+,\s*)?(\w+),\s*(\w+)' % (cls, nick), txt)
        if not m:
            continue
        labels = m.groups()
        done = []
        for lab, new in zip(labels, rules.BOSS2_TEXT[:2]):
            try:
                P.retext(S[lab], new)
                done.append(lab)
            except Exception:
                pass
        # 이긴 뒤 대사: 그 트레이너 스크립트에서 세 번째 글 라벨 (…AfterText / …AfterBattleText)
        m2 = re.search(r'(\w+After\w*Text)', txt[m.end():m.end() + 400])
        if m2 and len(rules.BOSS2_TEXT) > 2:
            try:
                P.retext(S[m2.group(1)], rules.BOSS2_TEXT[2])
                done.append(m2.group(1))
            except Exception:
                pass
        return '보스 대사 %d개 (%s)' % (len(done), ', '.join(done) or '라벨 심볼 없음')
    return '보스 대사: 맵에서 트레이너 줄 못 찾음'


def apply(P):
    import romanat
    S = romanat.Sym()
    log = []
    for fn in (lambda: dex_order(P, S), lambda: growth(P), lambda: default_names(P, S), lambda: trade_vmon(P)):   # 보스 대사는 story2 로
        try:
            log.append(fn())
        except Exception as ex:
            log.append('extra2 실패: %r' % (ex,))
    P.r.d = P.d
    return log
