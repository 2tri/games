"""작업팩 S7 — 기술 (A·S6 판정 2026-10-06, rules.MOVE_RENAME · SPECIALS · TYPE_FIX · TRAINER_MOVE_SWAP · BOSS_GROUPS)

patch.build 끝 무렵에 apply(P, groups) 로 부름. 하는 것:
  7-0 일반 기술 30개 이름 (기술 이름표를 통째로 다시 써서 NamesPointers 기술 칸을 옮김)
  7-1 전용 필살기 31칸: 기술 표 7바이트·이름·설명
      + 엔진이 기술 「번호」로 따로 처리하는 곳 정리 (그 칸의 옛 기술 성질이 새 필살기에 붙지 않게)
        급소 잘 나오는 목록(152·177) · 늘 나중에 움직이는 기술(233) · 얼음 녹이는 기술(221) · 스케치 PP(166)
        필드 기술 메뉴(알낳기 135·우유 마시기 208) · 「~를 사용했다」 문법 표 · AI 목록
      + 2턴 기술의 모으는 턴: 글(목록에 없는 연출이면 「땅으로 숨었다」가 나옴)과 연출(공격 연출이 한 번 더 나옴)
  7-2 종 타입 · 7-3 트레이너 1명 전용 기술 7개 바꿈 · 7-4 배우는 레벨 · 보스·라이벌 파티 기술 지정
기술 번호 = 금 한글판(pokegold-kr) 번호, 롬 주소는 원본 금 심볼(romanat.Sym)로 찾고 바이트를 확인한 뒤 고침."""
import re, struct
import dmrom, krtext, rules
from dmrom import addr

STRUGGLE, KARATE_CHOP, FLAME_WHEEL = 0xa5, 0x02, 0xac
FLY, DIG, RAZOR_WIND, SOLARBEAM, SKULL_BASH, SKY_ATTACK = 0x13, 0x5b, 0x0d, 0x4c, 0x82, 0x8f


def pct(p):                       # 금 percent 매크로 (p * 255 / 100, 버림)
    return p * 255 // 100


def _expect(P, a, want, what):
    got = bytes(P.d[a:a + len(want)])
    assert got == want, '%s: %X 바이트가 다름 %s ≠ %s' % (what, a, got.hex(' '), want.hex(' '))


def _list_fix(P, a, ids, term=0xff, sets=False):
    """번호 목록(term 으로 끝남)에서 ids 를 같은 목록(세트)의 다른 번호로 바꿈 → 그 번호는 목록에서 빠진 것과 같고 목록 길이는 그대로.
    sets=True 면 0 으로 나뉜 세트(문법 표)마다 따로"""
    n = 0; i = a; cur = []
    while P.d[i] != term:
        if sets and P.d[i] == 0: cur = []; i += 1; continue
        cur.append(i); i += 1
        if sets and P.d[i] in (0, term) or not sets and P.d[i] == term:
            keep = [j for j in cur if P.d[j] not in ids]
            for j in cur:
                if P.d[j] in ids:
                    assert keep, '목록 %X 가 전부 필살기 칸' % a
                    P.d[j] = P.d[keep[0]]; n += 1
            cur = []
    return n


def apply(P, groups):
    import romanat
    S = romanat.Sym(); d = P.d; log = []
    SP = rules.SPECIALS; ids = {row[0] for row in SP}
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    # ── 7-0 + 7-1 이름: 기술 이름표 251개를 다시 씀 ──
    m = re.search(rb'\x6c(..)\x6c(..)\x00\x00\x00\x6c(..)', bytes(d), re.S)       # NamesPointers: 디지몬·기술·없음·도구
    assert m and m.start() == S['NamesPointers'], 'NamesPointers'
    mp = m.start() + 3; a = addr(d[mp], d[mp + 1] | d[mp + 2] << 8); names = []
    for _ in range(251): j = d.index(0x50, a); names.append(bytes(d[a:j])); a = j + 1
    old_names = [krtext.decode(x + b'\x50') for x in names]
    for no, nm in rules.MOVE_RENAME.items(): names[no - 1] = krtext.encode(nm)
    for row in SP: names[row[0] - 1] = krtext.encode(row[2])
    dec = [krtext.decode(x + b'\x50') for x in names]
    dup = {x for x in dec if dec.count(x) > 1 and x.strip()}
    assert not dup, '기술 이름 겹침: %s' % dup
    assert max(len(x) for x in names) <= 16, '기술 이름 16바이트(한글 8자) 넘음'
    for row in SP: assert len(row[2]) <= 7, '전투 기술 목록은 7칸: %s' % row[2]
    blob = b''.join(x + b'\x50' for x in names)
    b, p = P.sp.take(len(blob), banks=[0x6c, 0x6d, 0x72, 0x74])
    P.put(addr(b, p), blob); P.put(mp, bytes([b, p & 255, p >> 8]))
    log.append('7-0 기술 이름 %d개 + 필살기 %d개 → 이름표 %02X:%04X' % (len(rules.MOVE_RENAME), len(SP), b, p))
    # ── 7-1 기술 표 (Moves: 연출·효과·위력·타입·명중·PP·확률) ──
    mt = S['Moves']
    _expect(P, mt, bytes([1, 0, 40, 0, 255, 35, 0]), '기술 표 막치기')
    for no, sp, nm, ty, pw, acc, pp, eff, ch, anim, _ in SP:
        P.put(mt + 7 * (no - 1), bytes([anim, eff, pw, rules.T_[ty], pct(acc), pp, pct(ch)]))
    # 설명 (MoveDescriptions: 같은 뱅크 2바이트 포인터) — 「○○몬의 필살기」 / 효과 한 줄
    dt = S['MoveDescriptions']; db = dt // 0x4000
    for no, sp, nm, ty, pw, acc, pp, eff, ch, anim, _ in SP:
        l1, l2 = rules.SPECIAL_DESC.get(no, ('%s의 필살기' % sp, rules.SPECIAL_EFFECT_LINE[eff]))
        assert len(l1) <= 18 and len(l2) <= 18, (l1, l2)
        s = krtext.encode_text('%s<NEXT>%s' % (l1, l2)) + b'\x50'
        b2, p2 = P.sp.take(len(s), bank=db); P.put(addr(b2, p2), s)
        P.put(dt + 2 * (no - 1), struct.pack('<H', p2))
    log.append('7-1 필살기 %d칸 기술 표·설명 (설명 뱅크 %02X)' % (len(SP), db))
    # ── 엔진: 기술 번호로 따로 처리하는 곳 ──
    n_eng = []
    c = S['CriticalHitMoves']; _expect(P, c, bytes([0x02, 0x0d, 0x4b, 0x98, 0xa3, 0xb1, 0xee, 0xff]), '급소 목록')
    n_eng.append('급소 목록 %d' % _list_fix(P, c, ids))                                  # 찝게햄머 152 · 에어로블레스트 177 칸
    g = S['GetMovePriority']; _expect(P, g, bytes([0x47, 0xfe, 0xe9, 0x3e, 0x00, 0xc8]), '우선도')
    P.d[g + 2] = 0xff; n_eng.append('늘 나중 233')                                      # 받아 던지기 칸: 「cp VITAL_THROW」 → 없는 번호
    thaw = [x.start() for x in re.finditer(rb'\xfe\xac\x28.\xfe\xdd', bytes(d[0x0d * 0x4000:0x0e * 0x4000]), re.S)]
    assert len(thaw) == 2, '얼음 녹이는 기술 확인 %d곳' % len(thaw)
    for x in thaw: P.d[0x0d * 0x4000 + x + 5] = FLAME_WHEEL                              # 「cp SACRED_FIRE」 → 화염 자동차 한 번 더
    n_eng.append('얼음 녹임 221 (2곳)')
    sk = 0
    for pat, rng in ((rb'\x7e\xfe\xa6\x06\x01\x28', (0x0f, 0x10)), (rb'\xfe\xa6\x3e\x01\x28', (0x0d, 0x0e)), (rb'\x7e\xfe\xa6\x28', (0x03, 0x04))):
        hit = list(re.finditer(pat, bytes(d[rng[0] * 0x4000:rng[1] * 0x4000])))
        assert len(hit) == 1, '스케치 확인 %s %d곳' % (pat, len(hit))
        P.d[rng[0] * 0x4000 + hit[0].start() + hit[0].group(0).index(0xa6)] = 0xff; sk += 1   # PP 되돌리기·변신 PP·포인트업 금지
    n_eng.append('스케치 166 (%d곳)' % sk)
    mm = S['MonMenuOptions']; nm_ = 0
    for k in range(20):
        e = mm + 3 * k
        if P.d[e] == 0xff: break
        if P.d[e] == 0 and P.d[e + 2] in ids: P.d[e + 2] = STRUGGLE; nm_ += 1               # 필드 기술 메뉴(알낳기·우유 마시기) → 발버둥(배울 수 없는 기술)
    assert nm_ == 2, '필드 기술 메뉴 %d' % nm_
    n_eng.append('필드 기술 135·208')
    n_eng.append('문법 표 %d' % _list_fix(P, S['MoveGrammar'], ids, term=0xff, sets=True))
    for lab in ('EncoreMoves', 'RainDanceMoves', 'SunnyDayMoves', 'UsefulMoves', 'StallMoves', 'ResidualMoves'):
        n_eng.append('%s %d' % (lab, _list_fix(P, S[lab], ids)))
    # 2턴 기술 모으는 턴 글: 연출 번호가 목록(회오리·솔라빔·로켓박치기·불새·공중날기·구멍파기)에 없으면 마지막 「구멍을 파서 숨었다」가 나옴
    #   → 목록 순서를 바꿔 「없으면 세찬 빛」으로 하고, 그 글(불새 연출 143 은 이제 아무 기술도 안 씀)을 「힘을 모으고 있다!」로
    ut = S['BattleCommand_Charge.UsedText'] + 10
    old = bytes([0xfe, 0x0d, 0x21, 0x14, 0x6d, 0x28, 0x21, 0xfe, 0x4c, 0x21, 0x19, 0x6d, 0x28, 0x1a, 0xfe, 0x82, 0x21, 0x1e, 0x6d, 0x28, 0x13,
                 0xfe, 0x8f, 0x21, 0x23, 0x6d, 0x28, 0x0c, 0xfe, 0x13, 0x21, 0x28, 0x6d, 0x28, 0x05, 0xfe, 0x5b, 0x21, 0x2d, 0x6d, 0xc9])
    _expect(P, ut, old, '모으는 턴 글')
    new = bytearray()
    for k, (anim, lo) in enumerate(((RAZOR_WIND, 0x14), (SOLARBEAM, 0x19), (SKULL_BASH, 0x1e), (FLY, 0x28), (DIG, 0x2d))):
        new += bytes([0xfe, anim, 0x21, lo, 0x6d, 0x28, 7 * (4 - k) + 3])               # jr z → ret
    new += bytes([0x21, 0x23, 0x6d, 0xc9])                                                 # 그 밖(불새 포함) = 세찬 빛 → 「힘을 모으고 있다!」
    new += bytes(len(old) - len(new))
    P.put(ut, bytes(new))
    gt = S['_BattleGlowingText']; ob, nb = krtext.encode('세찬 빛이 감싼다!'), krtext.encode('힘을 모으고 있다!')
    assert len(ob) == len(nb) and bytes(d).find(ob, gt, gt + 40) > 0, '세찬 빛 글'
    P.put(bytes(d).find(ob, gt, gt + 40), nb)
    # 모으는 턴 연출: 금은 그 기술 연출을 「모으기」 표시로 틀어서, 모으기가 없는 연출(파괴광선 등)은 공격 연출이 한 번 더 나옴
    #   → 원래 2턴 기술 연출이 아니면 솔라빔의 모으기 연출을 틂 (뱅크 0D 끝 빈 곳에 작은 함수)
    ch = S['BattleCommand_Charge']; lma0 = S['LoadMoveAnim']; lma, la = lma0 % 0x4000 + 0x4000, S['LoadAnim'] % 0x4000 + 0x4000   # 같은 뱅크(0D) 안 주소
    calls = [x.start() for x in re.finditer(re.escape(b'\xcd' + struct.pack('<H', lma)), bytes(d[ch:ch + 0x90]))]
    assert len(calls) == 1, '모으는 턴 연출 호출 %d' % len(calls)
    _expect(P, lma0, bytes([0xaf, 0xea, 0x0d, 0xd0, 0xea, 0x06, 0xd0, 0x3e, 0x0c, 0xcd, 0xd0, 0x3b]), 'LoadMoveAnim')
    fa = addr(0x0d, 0x7f96)
    assert all(P.d[fa + k] in (0x00, 0xff) for k in range(64)), '뱅크 0D 끝 빈 곳'
    gbv = S['GetBattleVar']; code = bytearray([0x3e, 0x0c, 0xcd, gbv & 255, gbv >> 8])  # a = 이 기술 연출 번호
    nat = (FLY, DIG, RAZOR_WIND, SOLARBEAM, SKULL_BASH, SKY_ATTACK)
    body_after = 1 + 3 + 3 + 2 + 3                                                       # xor·두 번 저장·ld a·jp LoadAnim
    for k, x in enumerate(nat):
        code += bytes([0xfe, x, 0x28, 4 * (len(nat) - 1 - k) + body_after])            # 원래 2턴 연출 → .orig
    code += bytes([0xaf, 0xea, 0x0d, 0xd0, 0xea, 0x06, 0xd0, 0x3e, SOLARBEAM, 0xc3, la & 255, la >> 8])
    code += bytes([0xc3, lma & 255, lma >> 8])                                           # .orig: jp LoadMoveAnim
    P.put(fa, bytes(code)); P.put(ch + calls[0] + 1, struct.pack('<H', 0x7f96))
    n_eng.append('모으는 턴 글·연출 (뱅크 0D:7F96 %d바이트)' % len(code))
    # 연출 번호를 기술 번호처럼 쓰는 곳 (원작은 연출 = 기술 번호) → 빌려 쓴 연출이면 엉뚱한 기술로 처리됨
    #   ① 기술 쓴 글: 「마지막에 쓴 기술」(따라하기·사슬묶기·앵콜·카운터 등이 봄)과 문법을 연출 번호로 → 실제 기술 번호(BATTLE_VARS_MOVE)
    #   ② 상대 AI 가 기억하는 내 기술(UpdateUsedMoves) ③ 전투 기술 정보 칸 타입 → wCurPlayerMove ④ 2턴 기술 모으는 턴의 마지막 기술
    BV_ANIM, BV_MOVE, CUR_P = 0x0c, 0x10, 0xcbc9
    um = S['UsedMoveText']
    seg = bytes(d[um:um + 0x40])
    k1 = seg.find(bytes([0xfa, 0xef, 0xca, 0xcd])); assert k1 > 0, 'UsedMoveText 내 기술 기억'
    P.put(um + k1, bytes([0xfa, CUR_P & 255, CUR_P >> 8]))
    k2 = seg.find(bytes([0x3e, BV_ANIM, 0xcd, gbv & 255, gbv >> 8, 0xea])); assert k2 > k1, 'UsedMoveText 마지막 기술'
    P.d[um + k2 + 1] = BV_MOVE
    core = bytes(d[0x0f * 0x4000:0x10 * 0x4000])
    hit = [x.start() for x in re.finditer(re.escape(bytes([0xfa, 0xef, 0xca, 0x47, 0x21])), core)]
    assert len(hit) == 1, '기술 정보 칸 타입 %d' % len(hit)
    P.put(0x0f * 0x4000 + hit[0], bytes([0xfa, CUR_P & 255, CUR_P >> 8]))
    seg = bytes(d[ch:ch + 0x90])
    k3 = seg.find(bytes([0x3e, BV_ANIM, 0xcd, gbv & 255, gbv >> 8, 0x47, 0xfe, FLY])); assert k3 > 0, '모으는 턴 마지막 기술'
    P.d[ch + k3 + 1] = BV_MOVE
    n_eng.append('연출 번호→기술 번호 4곳 (마지막 기술·문법, AI 기억, 정보 칸 타입, 모으는 턴)')
    log.append('엔진: ' + ', '.join(n_eng))
    # ── 7-2 종 타입 ──
    for nm, (t1, t2) in rules.TYPE_FIX.items():
        P.stats(N[nm], type1=rules.T_[t1], type2=rules.T_[t2])
    log.append('7-2 타입 %d종' % len(rules.TYPE_FIX))
    # ── 7-4 배우는 레벨 (레벨업 표) ──
    learn = []
    for no, sp, nm, *_r, how in SP:
        if not isinstance(how, tuple): continue
        t = N[sp]; pre = [(e, k) for k in range(1, dmrom.NUM + 1) for e in P.r.evos_attacks(k)[0] if e[-1] == t]
        own = [e[1] for e, k in pre if e[0] == 8]                                          # 자기 문장(종류 8) 레벨
        lv = (min(own) if own else min(e[1] for e, k in pre)) + how[1]
        ev, mv = P.r.evos_attacks(t)
        mv = sorted([x for x in mv if x[1] != no] + [(lv, no)], key=lambda x: x[0])
        P.evos(t, ev, mv); P.r.d = P.d
        learn.append('%s %s Lv%d' % (sp, nm, lv))
    log.append('7-4 배우는 레벨: ' + ', '.join(learn))
    P.s7_learn = learn
    # ── 7-3 트레이너 기술 바꿈 + 보스·라이벌 기술 지정 ──
    boss = {N[sp]: no for no, sp, nm, *_r, how in SP if how == 'boss'}
    rival = {N[sp]: no for no, sp, nm, *_r, how in SP if how == 'rival'}
    powr = lambda mv: P.d[mt + 7 * (mv - 1) + 2] if mv else -1
    swapped = 0; given = []
    for gname in sorted({groups[t['group']] for t in P.r.trainers(len(groups))}):
        ts = [t for t in P.r.trainers(len(groups)) if groups[t['group']] == gname]
        out = bytearray(); changed = False
        for t in ts:
            j = d.index(0x50, t['start']); kind = t['kind']
            want = {}                                                                       # 이 사람 파티 순서 → 넣을 필살기
            for i, (lv, sp, _) in enumerate(t['mons']):
                if sp in boss and gname in rules.BOSS_GROUPS[P.r.name(sp)]: want[i] = boss[sp]
                if sp in rival and gname in rules.RIVAL_GROUPS and lv >= 16: want[i] = rival[sp]
            nk = kind | 1 if want else kind                                                 # 기술 칸이 없는 형식(0·2)이면 기술 칸 있는 형식(1·3)으로
            out += bytes(d[t['start']:j + 1]) + bytes([nk])
            a = j + 2
            for i, (lv, sp, _) in enumerate(t['mons']):
                out += bytes(d[a:a + 2]); a += 2
                if kind in (2, 3): out.append(d[a]); a += 1
                elif nk in (2, 3): out.append(0)
                if kind in (1, 3): ms = list(d[a:a + 4]); a += 4
                elif nk in (1, 3):                                                          # 금이 기술 칸 없는 파티에 주는 것과 같게: 그 레벨까지 배운 마지막 4개
                    ms = []
                    for l, mv in P.r.evos_attacks(sp)[1]:
                        if l <= lv and mv not in ms:
                            ms.append(mv)
                            if len(ms) > 4: ms.pop(0)
                    ms += [0] * (4 - len(ms))
                else: continue
                for k in range(4):
                    if ms[k] in rules.TRAINER_MOVE_SWAP: ms[k] = rules.TRAINER_MOVE_SWAP[ms[k]]; swapped += 1; changed = True
                if i in want and want[i] not in ms:
                    k = ms.index(0) if 0 in ms else min(range(4), key=lambda q: powr(ms[q]))  # 빈 칸, 없으면 위력이 가장 낮은 기술 자리
                    given.append('%s#%d %s: %s → %s' % (gname, t['idx'] + 1, P.r.name(sp), old_names[ms[k] - 1] if ms[k] else '빈 칸', dec[want[i] - 1]))
                    ms[k] = want[i]; changed = True
                out += bytes(ms)
            assert d[a] == 0xff; out.append(0xff)
            changed |= nk != kind
        if not changed: continue
        s, e = ts[0]['start'], ts[-1]['end']
        bank, tab = P.r.trainer_table(); fr = P.sp.free.get(bank, [0, 0])
        if len(out) <= e - s: P.put(s, bytes(out) + b'\xff' * (e - s - len(out)))
        elif e % 0x4000 + 0x4000 == fr[0] and len(out) <= e - s + fr[1] - fr[0]:      # 바로 뒤가 뱅크 끝 빈 곳이면 그 자리에서 늘림
            P.put(s, bytes(out)); fr[0] = s % 0x4000 + 0x4000 + len(out)
            log.append('트레이너 무리 %s 제자리에서 %d → %d바이트 (뒤 빈 곳)' % (gname, e - s, len(out)))
        else:
            b3, p3 = P.sp.take(len(out), bank=bank); P.put(addr(b3, p3), bytes(out))
            P.put(tab + 2 * groups.index(gname), struct.pack('<H', p3))
            P.sp.give(bank, s % 0x4000 + 0x4000, e % 0x4000 + 0x4000)
            log.append('트레이너 무리 %s → %02X:%04X 로 옮김 (%d바이트)' % (gname, b3, p3, len(out)))
        P.r.d = P.d
    log.append('7-3 트레이너 기술 바꿈 %d곳, 필살기 지정 %d명' % (swapped, len(given)))
    P.s7_given = given
    return log
