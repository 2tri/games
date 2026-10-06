"""고친 롬(work/myver.gbc) 자동 시험 — PyBoy
  python3 romtest.py            트레이너 표 + 진화(유대·문장·암흑) + 포획률
처음 한 번은 인트로를 지나가서 work/intro.state 를 만든다 (롬이 바뀌면 지우고 다시).
램 주소는 pokegold-kr 디스어셈블리 기준 (한글판 금)."""
import os, re, sys
import dmrom, krtext, wild
from play import Play

W = dmrom.WORK
ROM = os.path.join(W, 'myver.gbc')
# ── 램 주소 ──
PARTY_COUNT, PARTY_SPECIES, PARTY_MONS, PARTY_OT, PARTY_NICK = 0xdb1f, 0xdb20, 0xdb27, 0xdc47, 0xdc89
NUM_ITEMS, NUM_BALLS = 0xd66a, 0xd6af
JOHTO_BADGES = 0xd62f
MAP_GROUP, MAP_NUM, YC, XC = 0xdafd, 0xdafe, 0xdaff, 0xdb00
NEWBARK_SCENE, HOUSE1F_SCENE = 0xd75e, 0xd760
ENEMY_SPECIES, ENEMY_CATCH = 0xd1ac, 0xd1d1
BATTLE_MODE, OTHER_CLASS, OTHER_ID, OT_COUNT, OT_SPECIES = 0xd1d3, 0xd1d5, 0xd1d8, 0xde52, 0xde53
RARE_CANDY, POKE_BALL = 0x20, 0x05
# 작업팩 S7 기술 시험용 램 (pokegold-kr 심볼)
B_MON_MOVES, B_MON_PP, B_MON_HP, P_SUB3, E_SUB3, E_STATLV = 0xcb0e, 0xcb14, 0xcb1c, 0xcb50, 0xcb55, 0xcbba
CUR_P_MOVE, CUR_E_MOVE, E_MOVES, E_PP, E_STATUS, E_HP = 0xcbc9, 0xcbca, 0xd1ae, 0xd1b4, 0xd1ba, 0xd1bc
SHOTS = os.path.join(W, 'shots')


def new(state=None):
    p = Play(ROM, SHOTS)
    if state:
        with open(os.path.join(W, state), 'rb') as f: p.pb.load_state(f)
    return p


def save(p, name):
    with open(os.path.join(W, name), 'wb') as f: p.pb.save_state(f)


def intro():
    """전원 → 이름 'ㄱㄱㄱㄱㄱ' → 2층 방. 입력 순서는 고정(에뮬레이터는 결정적)"""
    p = new()
    p.tick(300)
    for _ in range(52): p.press('a', 6, 50)
    p.press('start', 6, 40); p.press('a', 6, 60)
    for _ in range(40): p.press('a', 6, 50)
    p.press('start', 6, 30); p.press('a', 6, 60)
    for _ in range(30): p.press('a', 6, 60)
    m = p.pb.memory
    assert (m[MAP_GROUP], m[MAP_NUM]) == (24, 7), '인트로 뒤 방이 아님: %d,%d' % (m[MAP_GROUP], m[MAP_NUM])
    save(p, 'intro.state'); p.stop()


def put_party(p, mons, names, item=None):
    """mons = [(종, 레벨, 유대)]"""
    m = p.pb.memory
    m[PARTY_COUNT] = len(mons)
    for i, (sp, lv, hap) in enumerate(mons):
        m[PARTY_SPECIES + i] = sp
        b = PARTY_MONS + 48 * i
        for k in range(48): m[b + k] = 0
        m[b] = sp; m[b + 2] = 0x21; m[b + 6] = 0x12; m[b + 7] = 0x34
        exp = lv ** 3; m[b + 8] = exp >> 16; m[b + 9] = exp >> 8 & 255; m[b + 10] = exp & 255
        m[b + 21] = m[b + 22] = 0xaa; m[b + 23] = 35; m[b + 27] = hap; m[b + 31] = lv
        for o in (34, 36): m[b + o + 1] = 50
        for o in (38, 40, 42, 44, 46): m[b + o + 1] = 30
        nm = list(names[sp]) + [0x50] * 11
        ot = list(krtext.encode('시험')) + [0x50] * 11
        for k in range(11): m[PARTY_NICK + 11 * i + k] = nm[k]; m[PARTY_OT + 11 * i + k] = ot[k]
    m[PARTY_SPECIES + len(mons)] = 0xff
    m[NUM_ITEMS] = 1; m[NUM_ITEMS + 1] = item or RARE_CANDY; m[NUM_ITEMS + 2] = 10; m[NUM_ITEMS + 3] = 0xff
    m[NUM_BALLS] = 1; m[NUM_BALLS + 1] = POKE_BALL; m[NUM_BALLS + 2] = 20; m[NUM_BALLS + 3] = 0xff


def candy(slot, mons, names, badges=0, presses=16, item=None):
    """방에서 가방 → 이상한사탕(또는 item) → slot 번째에게 1번(이어서 몇 번 더) 쓰고 종 번호를 돌려줌"""
    p = new('intro.state'); m = p.pb.memory
    put_party(p, mons, names, item); m[JOHTO_BADGES] = badges; p.tick(10)
    p.press('start', 6, 80); p.press('down', 6, 30); p.press('a', 6, 90)   # 가방
    p.press('a', 6, 60); p.press('a', 6, 90)                                # 사탕 → 사용하다
    for _ in range(slot): p.press('down', 6, 20)
    p.press('a', 6, 60)
    for i in range(1, presses):
        if i in (8,): p.tick(200)        # 진화 애니메이션 (B 는 진화 취소라 누르지 않음)
        p.press('a', 6, 70)
    r = m[PARTY_SPECIES + slot], m[PARTY_MONS + 48 * slot + 31]
    p.stop(); return r


def test_evo(names):
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    PARTY = [(N['파피몬'], 15, 200), (N['파피몬'], 15, 70), (N['그레이몬'], 31, 70), (N['코로몬'], 7, 70),
             (N['메탈그레몬'], 44, 70), (N['가루몬'], 32, 70)]
    cases = [  # 이름, slot, 배지, 레벨 덮어쓰기, 기대 종
        ('파피몬 유대↑(200) → 가루몬', 0, 0, None, N['가루몬']),
        ('파피몬 유대 보통(70) → 우가몬', 1, 0, None, N['우가몬']),
        ('그레이몬 + 용기 배지 Lv32 → 메탈그레이몬', 2, 1 << 5, None, N['메탈그레몬']),
        ('그레이몬 배지 없음 Lv32 → 그대로', 2, 0, None, N['그레이몬']),
        ('그레이몬 다른 배지 Lv32 → 그대로', 2, 1, None, N['그레이몬']),
        ('그레이몬 다른 배지 + 유대 70 Lv36 → 메탈그레이몬', 2, 1, 35, N['메탈그레몬'], 30),
        ('메탈그레이몬 + 용기 Lv45 → 워그레이몬', 4, 1 << 5, None, N['워그레이몬'], 30),
        ('메탈그레이몬 다른 배지 Lv45 → 그대로', 4, 1, None, N['메탈그레몬']),
        ('가루몬 + 우정 배지 Lv33 → 워가루몬', 5, 1 << 4, None, N['워가루몬']),
        ('코로몬 Lv8 → 아구몬', 3, 0, None, N['아구몬']),
    ]
    SK = '스컬그레몬' if '스컬그레몬' in N else '그레이몬'      # 스컬그레몬 그림 전에는 암흑 갈래가 없어 그대로
    extra = [  # 따로 한 마리씩: 이름, 종, 레벨, 기대 종, 유대(친밀도)[, 배지, 누르는 수]
        ('브이몬 Lv16 → 엑스브이몬', '브이몬', 15, '엑스브이몬', 70),
        ('뿔몬 Lv8 → 파피몬 (새 칸, 그림 있을 때)', '뿔몬', 7, '파피몬', 70),
        ('토코몬 Lv8 → 파닥몬 (새 칸, 그림 있을 때)', '토코몬', 7, '파닥몬', 70),
        ('파닥몬 유대 높음(200) → 엔젤몬', '파닥몬', 15, '엔젤몬', 200),
        ('파닥몬 유대 낮음(40) → 데블몬', '파닥몬', 15, '데블몬', 40),
        ('파닥몬 유대 보통(100) → 엔젤몬', '파닥몬', 15, '엔젤몬', 100),
        ('파피몬 유대 140 (150 미만) → 우가몬', '파피몬', 15, '우가몬', 140),
        ('파피몬 유대 150 (기준값) → 가루몬', '파피몬', 15, '가루몬', 150),
        ('그레이몬 다른 배지 + 유대 40 Lv32 → %s' % SK, '그레이몬', 31, SK, 40, 1, 30 if SK != '그레이몬' else 16),
        ('그레이몬 다른 배지 + 유대 40 Lv36 → %s' % (SK if SK != '그레이몬' else '메탈그레몬 (아무 문장)'), '그레이몬', 35,
         SK if SK != '그레이몬' else '메탈그레몬', 40, 1, 30),
        ('가트몬 + 빛 배지 Lv30 → 엔젤우몬', '가트몬', 29, '엔젤우몬', 70, 1 << 3, 30),
        ('가트몬 다른 배지 Lv30 → 그대로', '가트몬', 29, '가트몬', 70, 1, 16),
        ('가트몬 다른 배지 + 유대 40 Lv30 → 레이디데블 (암흑)', '가트몬', 29, '레이디데블' if '레이디데블' in N else '가트몬', 40, 1, 30),
        ('엔젤우몬 + 빛 배지 Lv45 → 마그나드몬', '엔젤우몬', 44, '마그나드몬', 70, 1 << 3, 30),
        ('쉬라몬 Lv18 → 원뿔몬', '쉬라몬', 17, '원뿔몬', 70),
        ('텐타몬 유대 낮음(40) Lv16 → 쿠가몬', '텐타몬', 15, '쿠가몬', 40),
        ('텐타몬 유대 보통(100) Lv16 → 그대로', '텐타몬', 15, '텐타몬', 100, 0, 16),
        ('텐타몬 유대 보통(100) Lv21 → 캅테리몬', '텐타몬', 20, '캅테리몬', 100),
        ('쿠가몬 + 배지 Lv34 → 오쿠와몬 (아무 문장)', '쿠가몬', 33, '오쿠와몬', 70, 1, 30),
        ('피코데블몬 Lv20 → 데블몬', '피코데블몬', 19, '데블몬', 70),
    ]
    bad = 0
    for name, sp_name, lv, want_name, hap, *bg in extra:
        if sp_name not in N or want_name not in N: print('  %-36s → 건너뜀 (아직 롬에 없음)' % name); continue
        sp, got_lv = candy(0, [(N[sp_name], lv, hap)], names, bg[0] if bg else 0, bg[1] if len(bg) > 1 else 30)
        ok = sp == N[want_name]; bad += not ok
        print('  %-36s → %3d Lv%-3d %s' % (name, sp, got_lv, 'OK' if ok else '틀림(기대 %d)' % N[want_name]))
    for name, slot, badge, lv, want, *more in cases:
        mons = [list(x) for x in PARTY]
        if lv: mons[slot][1] = lv
        sp, got_lv = candy(slot, [tuple(x) for x in mons], names, badge, *(more or [16]))   # 새 기술 배우기 창이 뜨는 경우는 더 누름
        ok = sp == want; bad += not ok
        print('  %-36s → %3d Lv%-3d %s' % (name, sp, got_lv, 'OK' if ok else '틀림(기대 %d)' % want))
    return bad


def to_grass():
    """방 → 1층 → 연두마을 → 29번 도로 풀숲 (연구원·엄마 장면은 램으로 넘김).
    마을 사람이 돌아다녀 길을 막을 수 있으므로 좌표를 보며 목표에 닿을 때까지 걷는다"""
    p = new('intro.state'); m = p.pb.memory
    m[NEWBARK_SCENE] = 1; m[HOUSE1F_SCENE] = 1
    pos = lambda: (m[MAP_GROUP], m[MAP_NUM], m[XC], m[YC])
    def walk(d, until, limit=40):
        for _ in range(limit):
            if until(pos()): return
            p.press(d, 10, 10); p.tick(30)
        raise AssertionError('못 감: %s %s' % (d, pos()))
    walk('right', lambda q: q[2] >= 7)
    walk('up', lambda q: q[1] == 6); p.tick(60)                      # 2층 → 1층
    walk('down', lambda q: q[3] >= 2); walk('left', lambda q: q[2] <= 8)
    walk('down', lambda q: q[3] >= 7); walk('left', lambda q: q[2] <= 7)
    walk('down', lambda q: q[1] == 4); p.tick(60)                    # 연두마을
    walk('down', lambda q: q[3] >= 9)
    walk('left', lambda q: q[1] == 3); p.tick(60)                    # 29번 도로
    walk('left', lambda q: q[2] <= 44)
    walk('down', lambda q: q[3] >= 11)
    return p


def test_catch(names, trials=10):
    p = to_grass(); m = p.pb.memory
    put_party(p, [(7, 15, 70)], names)
    save(p, 'grass.state'); p.stop()
    # 첫 만남까지 걷고 전투 메뉴에서 저장
    p = new('grass.state'); m = p.pb.memory; m[ENEMY_SPECIES] = 0
    for i in range(80):
        p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
        if m[ENEMY_SPECIES]: break
    p.tick(400)
    for _ in range(3): p.press('a', 6, 60)
    p.tick(300); p.shot('battle_menu'); save(p, 'battle.state'); sp = m[ENEMY_SPECIES]; p.stop()

    def throw(rate, k):
        p = new('battle.state'); m = p.pb.memory
        m[ENEMY_CATCH] = rate; p.tick(1 + 13 * k)
        p.press('right', 6, 40); p.press('a', 6, 120); p.press('right', 6, 60)   # 가방 → 볼 주머니
        p.press('a', 6, 60); p.press('a', 6, 60)
        got = False
        for _ in range(14):
            p.press('a', 6, 70); got |= m[PARTY_COUNT] == 2     # 별명 화면에선 램 뱅크가 바뀌어 0으로 읽히므로 매번 확인
        p.stop(); return got
    c0 = sum(throw(0, k) for k in range(trials))
    c90 = sum(throw(90, k) for k in range(trials))
    c255 = sum(throw(255, k) for k in range(2 * trials))             # 체력 가득이면 한 번에 약 33% → 20번 (10번이면 모두 실패할 확률 약 2%)
    print('  상대 %d번 체력 가득, 몬스터볼 %d번씩 — 포획률 0: %d 잡힘 (0이어야 함) / 포획률 90(성숙기·아머체): %d 잡힘 (기록) / 포획률 255: %d/%d 잡힘 (0보다 커야 함)'
          % (sp, trials, c0, c90, c255, 2 * trials))
    # 실제 풀숲 만남에서 잡을 수 없는 종이 포획률 0으로 들어오는지
    seen = {}
    for t in range(12):
        p = new('grass.state'); m = p.pb.memory; p.tick(1 + 17 * t); m[ENEMY_SPECIES] = 0
        for i in range(80):
            p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
            if m[ENEMY_SPECIES]: break
        p.tick(200); seen[m[ENEMY_SPECIES]] = m[ENEMY_CATCH]; p.stop()
    r = dmrom.Rom(ROM)
    print('  29번 도로 만남:', ', '.join('%s(%d) 포획률 %d' % (r.name(s), s, c) for s, c in sorted(seen.items()) if s))
    bad = (c0 != 0) + (c255 == 0)
    bad += sum(c != r.base_stats(s)['catch'] for s, c in seen.items() if s)
    toko = [s for s in seen if s and r.name(s) == '토코몬']                  # E 연결표: 토코몬은 야생 없음 (조수의 알 전용)
    if toko: print('  틀림: 29번 도로에 토코몬이 나옴'); bad += 1
    else: print('  29번 도로 12번 만남에 토코몬 없음 (연결표: 야생 없음) OK')
    return bad


def test_trainers():
    """트레이너 표를 게임과 같은 방식으로 읽기 (ReadTrainerParty: 무리 포인터 → FF 를 세며 n-1명 건너뜀 → 이름 @ → 종류 → FF 까지)
    파서(dmrom.trainers) 결과와 495명 모두 같은지 + 옮긴 라이벌 무리 첫 대결"""
    r = dmrom.Rom(ROM); d = bytes(r.d); bank, tab = r.trainer_table(); ts = r.trainers(66)
    EXTRA = {0: 0, 1: 4, 2: 1, 3: 5}; bad = 0
    for t in ts:
        a = dmrom.addr(bank, d[tab + 2 * t['group']] | d[tab + 2 * t['group'] + 1] << 8)
        for _ in range(t['idx']): a = d.index(0xff, a) + 1
        a = d.index(0x50, a) + 1; kind = d[a]; a += 1; mons = []
        while d[a] != 0xff: mons.append((d[a], d[a + 1])); a += 2 + EXTRA[kind]
        bad += mons != [(lv, sp) for lv, sp, _ in t['mons']]
    print('  게임 방식으로 읽은 트레이너 %d명 중 파서와 다른 사람: %d' % (len(ts), bad))
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(wild.KR, 'data/trainers/party_pointers.asm')).read())
    r1 = [t for t in ts if groups[t['group']] == 'Rival1'][:3]
    show = ' / '.join(', '.join('%s Lv%d' % (r.name(sp), lv) for lv, sp, _ in t['mons']) for t in r1)
    ok = all([r.name(sp) for _, sp, _ in t['mons']][0] in ('추추몬', '데롱몬') and len(t['mons']) == 2 for t in r1)   # 데롱몬 = 추추몬 유년기 (그림 오면)
    print('  라이벌 1차 (옮긴 무리, 2마리): %s %s' % (show, 'OK' if ok else '틀림'))
    return bad + (not ok)


def test_black_gear(names):
    """D-4: 검은 톱니(태양의 돌 칸)를 그레이몬에게 쓰면 다크그레몬. 다른 종에게는 안 됨"""
    import rules
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}; it = rules.BLACK_GEAR['item']; bad = 0
    if rules.BLACK_GEAR['to'] not in N: print('  건너뜀 (다크그레몬 없음)'); return 0
    for name, sp, lv, want in (('검은 톱니 → 그레이몬 Lv20 → 다크그레몬', '그레이몬', 20, N['다크그레몬']),
                               ('검은 톱니 → 가루몬 Lv20 → 그대로', '가루몬', 20, N['가루몬'])):
        got, got_lv = candy(0, [(N[sp], lv, 70)], names, 0, 30, item=it)
        ok = got == want; bad += not ok
        print('  %-36s → %3d Lv%-3d %s' % (name, got, got_lv, 'OK' if ok else '틀림(기대 %d)' % want))
    return bad


def test_dark_real(names, N):
    """스컬그레몬이 들어온 롬: 그레이몬 자기 문장 32 메탈그레몬 → 암흑 32 스컬그레몬 → 아무 문장 36 메탈그레몬"""
    g = N['그레이몬']; bad = 0
    cases = [  # 이름, 유대, 배지, 기대 종
        ('암흑: 유대 40 + 다른 배지 Lv32 → 스컬그레몬', 40, 1, N['스컬그레몬']),
        ('암흑: 유대 64(사탕 +5 → 69) + 다른 배지 → 스컬그레몬', 64, 1, N['스컬그레몬']),   # 이상한사탕 레벨업 때 유대 +5 뒤에 진화 판정
        ('암흑: 유대 65(사탕 +5 → 70) + 다른 배지 → 그대로', 65, 1, g),
        ('암흑: 유대 40 + 배지 없음 Lv32 → 그대로', 40, 0, g),
        ('암흑: 유대 40 + 용기 배지 Lv32 → 메탈그레이몬', 40, 1 << 5, N['메탈그레몬']),
    ]
    for name, hap, badge, want in cases:
        # 진화하는 경우는 진화 직후 새 기술 배우기 창까지 넘기도록 30번, 그대로인 경우는 Lv36(아무 문장)에 닿지 않게 16번
        sp, got_lv = candy(0, [(g, 31, hap)], names, badge, 30 if want != g else 16)
        ok = sp == want; bad += not ok
        print('  %-36s → %3d Lv%-3d %s' % (name, sp, got_lv, 'OK' if ok else '틀림(기대 %d)' % want))
    return bad


def test_dark(names):
    """암흑 진화(종류 9) 코드 시험: 아직 쓰는 종이 없으므로 시험용 롬을 따로 만들어
    그레이몬 목록의 둘째(아무 문장 Lv36)를 「암흑 Lv32 → 데블몬」으로 바꿔 넣고 확인 (myver.gbc 는 그대로)"""
    global ROM
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    if '스컬그레몬' in N: return test_dark_real(names, N)
    d = bytearray(r.d); g = N['그레이몬']
    p = d[r.evos + 2 * (g - 1)] | d[r.evos + 2 * (g - 1) + 1] << 8; a = dmrom.addr(r.evos // 0x4000, p)
    assert d[a] == 8 and d[a + 3] == 10, '그레이몬 목록 모양이 예상과 다름'
    d[a + 3:a + 6] = bytes([9, 32, N['데블몬']])
    test_rom = os.path.join(W, 'dark_test.gbc'); open(test_rom, 'wb').write(bytes(d))
    cases = [  # 이름, 유대, 배지, 기대 종
        ('암흑: 유대 40 + 다른 배지 Lv32 → 데블몬', 40, 1, N['데블몬']),
        ('암흑: 유대 100 + 다른 배지 Lv32 → 그대로', 100, 1, g),
        ('암흑: 유대 40 + 배지 없음 Lv32 → 그대로', 40, 0, g),
        ('암흑: 유대 40 + 용기 배지 Lv32 → 메탈그레이몬', 40, 1 << 5, N['메탈그레몬']),
    ]
    keep, ROM = ROM, test_rom; bad = 0
    try:
        for name, hap, badge, want in cases:
            sp, got_lv = candy(0, [(g, 31, hap)], names, badge)
            ok = sp == want; bad += not ok
            print('  %-36s → %3d Lv%-3d %s' % (name, sp, got_lv, 'OK' if ok else '틀림(기대 %d)' % want))
    finally:
        ROM = keep
    return bad


def text_targets(r):
    """화면으로 볼 대사: 관장 비상 승리 대사(D-2), 유대 측정(D-3) 150~199·0~49 구간 → [(이름, text 시작 주소)]"""
    import rules
    d = bytes(r.d); out = []
    m = re.search(re.escape(bytes([0x64])) + b'(..)' + re.escape(bytes([0, 0, 0x5e, 1, 1])), d, re.S)
    out.append(('관장 비상 승리 대사', dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))))
    for k, label in ((2, '유대 측정 150~199'), (5, '유대 측정 0~49')):
        body = rules.BOND_TEXTS[k][1].split('<')[0]
        h = d.find(krtext.encode(body))
        out.append((label, h - 1 if h > 0 and d[h - 1] == 0 else None))
    # 작업팩 S5 대사 치환 3장면 (야돈 우물·모모 농장·불탄 탑): 글 조각이 든 덩어리의 시작(text 명령 0x00)
    for label, frag in (('S5 야돈 우물 (강집)', '우물에서 개굴몬에게'), ('A 방울탑 현자 (사성수·청룡몬)', '깨어나 디지털 월드를 떠돈다하오'), ('S5 모모 농장', '앓아 누워 버렸단다'), ('S5 불탄 탑 (라이벌)', '전설의 디지몬을 찾으려고')):
        h = d.find(krtext.encode(frag)); s = h
        while h > 0 and s > h - 400 and d[s] != 0x00: s -= 1
        out.append((label, s if h > 0 and d[s] == 0x00 else None))
    return out


def test_texts(names):
    """대사 화면 확인: 시험용 롬에서 주인공 방 책장 글(공용 「그림책 책장」)을 대상 대사로 점프(text_far)하게 바꾸고
    책장 앞에서 말을 걸어 쪽마다 찍음 → work/shots/txt_*.png (myver.gbc 는 그대로)"""
    global ROM
    r = dmrom.Rom(ROM); d = bytes(r.d)
    hb = krtext.encode('그림책이 모여져있군'); h = d.find(hb)
    s = h - 1
    while d[s] != 0x00: s -= 1                                   # 책장 글 시작 (text 명령)
    assert s > h - 12, '책장 글 시작을 못 찾음'
    bad = 0; keep = ROM
    try:
        for k, (label, ta) in enumerate(text_targets(r)):
            if ta is None: print('  %-24s → 못 찾음' % label); bad += 1; continue
            e = bytearray(d); bank, ptr = ta // 0x4000, ta % 0x4000 + 0x4000
            e[s:s + 5] = bytes([0x16, ptr & 255, ptr >> 8, bank, 0x50])
            ROM = os.path.join(W, 'text_test.gbc'); open(ROM, 'wb').write(bytes(e))
            p = new('intro.state'); m = p.pb.memory
            for d_, cond in (('right', lambda: m[XC] >= 5), ('up', lambda: m[YC] <= 2)):
                for _ in range(10):
                    if cond(): break
                    p.press(d_, 10, 10); p.tick(30)
            p.press('up', 6, 30)                                      # 책장(5,1) 보기
            ok = (m[XC], m[YC]) == (5, 2); at = (m[XC], m[YC])        # 책장 앞 (글이 짧으면 끝난 뒤 A 로 다시 말을 거니 여기서 봄)
            p.press('a', 6, 120); shots = 0
            for page in range(8):
                p.tick(90); p.shot('txt_%d_%d' % (k, page)); shots += 1
                p.press('a', 6, 40)
            bad += not ok
            print('  %-24s → 책장 앞 %s, 화면 %d장 (work/shots/txt_%d_*.png)' % (label, 'OK' if ok else '못 감 %d,%d' % at, shots, k))
            p.stop()
    finally:
        ROM = keep
    return bad


def test_battle_pics(names, pairs=None):
    """전투 화면 그림 확인: 시험용 롬에서 29번 도로 풀숲 종을 모두 상대 종으로, 내 파티 첫 칸을 내 종으로 → 만남 화면 찍기
    (상대 앞모습 + 내 뒷모습, 둘 다 롬 팔레트). work/shots/pic_*.png. myver.gbc 는 그대로"""
    global ROM
    import encounters
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    if pairs is None:
        pairs = [('다크그레몬', '블랙워그몬'), ('블랙워그몬', '다크그레몬'), ('모티몬', '시드몬'), ('둥실몬', '깜몬'), ('푸니몬', '야옹몬'),
                 ('가지몬', '고스몬'), ('쿠가몬', '팬텀몬'), ('스컬그레몬', '엔젤우몬'),
                 ('묘티스몬', '레이디데블'), ('피노키몬', '아포카리몬'), ('오메가몬', '디아블로몬'), ('워그레이몬', '워그레이몬'),
                 ('피에몬', '쉘몬'), ('쉘몬', '피에몬'), ('데블드라몬', '데블드라몬'), ('메탈가루몬', '메탈가루몬'),
                 ('텐타몬', '플라이몬'), ('두리몬', '울퉁몬'), ('포로몬', '꼬마몬'), ('디그몬', '메라몬'),
                 ('메탈시드몬', '파워드라몬'), ('파워드라몬', '안드로몬'),
                 ('케라몬', '우드몬'), ('쥬레이몬', '메가드라몬'), ('메가드라몬', '쥬레이몬'), ('톱니몬', '가드로몬'),     # 작업팩 S3 새 종
                 ('가드로몬', '베놈묘티몬'), ('베놈묘티몬', '톱니몬'), ('우드몬', '케라몬'),
                 ('팔몬', '데블몬'), ('데블몬', '팔몬'), ('황제팔라딘', '번개드라몬'), ('번개드라몬', '황제팔라딘'), ('엔젤몬', '엔젤몬')]   # S3 그림 교체
    skip = [p for p in pairs if p[0] not in N or p[1] not in N]          # 그림 대기로 아직 롬에 없는 종은 건너뜀
    if skip: print('  건너뜀 (롬에 아직 없음): %s' % ', '.join('%s/%s' % p for p in skip))
    pairs = [p for p in pairs if p not in skip]
    grass = [s['addr'] for s in encounters.find_all(dmrom.Rom(dmrom.default_rom())) if s['kind'] == '풀숲' and s['where'].startswith('29번 도로')]
    bad = 0; keep = ROM
    try:
        for k, (foe, mine) in enumerate(pairs):
            if foe not in N or mine not in N: print('  %s / %s → 건너뜀 (롬에 없음)' % (foe, mine)); continue
            e = bytearray(r.d)
            for a in grass: e[a] = N[foe]
            ROM = os.path.join(W, 'pic_test.gbc'); open(ROM, 'wb').write(bytes(e))
            p = new('grass.state'); m = p.pb.memory
            put_party(p, [(N[mine], 30, 70)], names); m[ENEMY_SPECIES] = 0
            for i in range(120):
                p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
                if m[ENEMY_SPECIES]: break
            p.tick(400)
            for _ in range(3): p.press('a', 6, 60)
            p.tick(300); p.shot('pic_%d' % k)
            ok = m[ENEMY_SPECIES] == N[foe]; bad += not ok
            print('  상대 %-6s / 내 %-6s → %s (work/shots/pic_%d.png)' % (foe, mine, 'OK' if ok else '만남 종 %d' % m[ENEMY_SPECIES], k))
            p.stop()
    finally:
        ROM = keep
    return bad


def test_e4(names, group='Will', cls=0x0b, tid=1):
    """사천왕 전투 시작 (작업팩 S4): 29번 도로 풀숲에서 만남 직전 상대 트레이너 칸을 사천왕으로 → 트레이너 전투로 들어가
    상대 파티가 롬 트레이너 표와 같은지. work/shots/e4_<무리>.png"""
    import encounters
    r = dmrom.Rom(ROM)
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    want = [sp for t in r.trainers(len(groups)) if groups[t['group']] == group and t['idx'] == tid - 1 for _, sp, _ in t['mons']]
    p = new('grass.state'); m = p.pb.memory
    put_party(p, [(want[0], 50, 70)], names)
    for i in range(160):
        m[OTHER_CLASS] = cls; m[OTHER_ID] = tid
        p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
        if m[BATTLE_MODE]: break
    p.tick(600)
    for _ in range(4): p.press('a', 6, 80)
    p.tick(200); p.shot('e4_' + group)
    got = [m[OT_SPECIES + k] for k in range(m[OT_COUNT])] if m[BATTLE_MODE] == 2 else []
    ok = got == want
    print('  %s 전투 모드 %d, 상대 파티 %s → %s (work/shots/e4_%s.png)' % (group, m[BATTLE_MODE], ' '.join(r.name(x) for x in got) or '-', 'OK' if ok else '기대 ' + ' '.join(r.name(x) for x in want), group))
    p.stop()
    return 0 if ok else 1


def _wait_menu(p, frames=3000):
    """전투 메뉴(싸우다·가방·디지몬·도망치다)가 화면에 뜰 때까지 (전투 그림 시험 화면 pic_0 의 메뉴 칸과 비교). 글은 B 로 넘김"""
    import numpy as np
    from PIL import Image
    ref = np.asarray(Image.open(os.path.join(SHOTS, 'pic_0.png')).convert('L'), dtype=int)[104:140, 72:160]
    for f in range(0, frames, 10):
        p.tick(10)
        cur = np.asarray(p.pb.screen.image.convert('L'), dtype=int)[104:140, 72:160]
        if np.abs(cur - ref).mean() < 4: return True
        if f % 60 == 50: p.press('b', 4, 4)
    return False


def _fight(p, m, slot=0, frames=4200, tag=None):
    """전투 메뉴에서 싸우다 → 기술 slot 고르고, 상대 체력이 줄 때까지(모으는 턴이면 다음 턴까지) 따라감.
    돌려줌: (처음 체력, 줄어든 뒤 체력, 모으는 턴 봄, 걸린 프레임). 멈추면 걸린 프레임 = None"""
    ehp = lambda: m[1, E_HP] << 8 | m[1, E_HP + 1]                       # WRAM 뱅크 1 (d000~) 에서 직접
    hp0 = ehp()
    p.press('a', 8, 90)                                                   # 싸우다
    for _ in range(slot): p.press('down', 8, 30)
    p.press('a', 8, 30)
    charged = False
    for f in range(0, frames, 10):
        p.tick(10)
        if m[P_SUB3] >> 4 & 1 and not charged:
            charged = True
            if tag:                                                         # 모으는 턴 글 화면
                for _ in range(6):
                    p.tick(20); p.shot('%s_c%d' % (tag, _))
        hp = ehp()
        if hp < hp0: return hp0, hp, charged, f
        if f % 60 == 50: p.press('b', 4, 4)                              # 글 넘기기 (메뉴에서는 아무 일 없음)
    return hp0, hp0, charged, None


def test_moves(names, foe='코로몬', foe_lv=100, my_lv=30):
    """S7 전용 필살기 31개: 시험용 롬(효과 확률 100%, 29번 도로 풀숲 = 노말 타입 코로몬 Lv100)에서 내 첫 칸 기술 1개로 한 번씩 씀.
    통과: 상대 체력이 줆(멈춤 없음) + 효과(화상·얼음·마비·독·혼란·능력↓)가 걸림 + 2턴 기술은 모으는 턴(체력 그대로·모으기 표시) 다음 턴에 맞음.
    풀죽음·추가 효과 없음(0)은 화면만. 빗나가면 누르는 때를 바꿔 4번까지 다시 (몇 번째에 맞았는지 적음). work/shots/mv_<칸>_*.png"""
    global ROM
    import encounters, rules
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    mt = r.d.find(bytes([1, 0, 40, 0, 255, 35, 0]))
    e = bytearray(r.d)
    for no, *_ in rules.SPECIALS:
        if e[mt + 7 * (no - 1) + 6]: e[mt + 7 * (no - 1) + 6] = 255
    for s_ in encounters.find_all(dmrom.Rom(dmrom.default_rom())):
        if s_['kind'] == '풀숲' and s_['where'].startswith('29번 도로'): e[s_['addr']] = N[foe]; e[s_['addr'] - 1] = foe_lv
    keep = ROM; ROM = os.path.join(W, 'move_test.gbc'); open(ROM, 'wb').write(bytes(e))
    STAT = {4: ('화상', lambda m: m[1, E_STATUS] >> 4 & 1), 5: ('얼음', lambda m: m[1, E_STATUS] >> 5 & 1), 6: ('마비', lambda m: m[1, E_STATUS] >> 6 & 1),
            2: ('독', lambda m: m[1, E_STATUS] >> 3 & 1), 76: ('혼란', lambda m: m[E_SUB3] >> 7 & 1),
            68: ('공격↓', lambda m: m[E_STATLV] < 7), 69: ('방어↓', lambda m: m[E_STATLV + 1] < 7), 70: ('스피드↓', lambda m: m[E_STATLV + 2] < 7),
            72: ('특방↓', lambda m: m[E_STATLV + 4] < 7)}
    bad = 0
    try:
        for no, sp, nm, ty, pw, acc, pp, eff, ch, anim, how in rules.SPECIALS:
            res = (0, 0, False, None, None, 0)
            for tryn in range(4):
                p = new('grass.state'); m = p.pb.memory
                put_party(p, [(N[sp], my_lv, 70)], names); m[JOHTO_BADGES] = 0xff     # 배지 8개 (안 그러면 남의 디지몬이라 말을 안 들음)
                b = PARTY_MONS
                m[b + 2], m[b + 3], m[b + 4], m[b + 5] = no, 0, 0, 0
                m[b + 23], m[b + 24], m[b + 25], m[b + 26] = pp, 0, 0, 0
                for o in (34, 36): m[b + o], m[b + o + 1] = 0x03, 0xe7                # 체력 999 (상대 차례에 안 쓰러지게)
                m[ENEMY_SPECIES] = 0
                for i in range(120):
                    p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
                    if m[ENEMY_SPECIES]: break
                if not _wait_menu(p): p.stop(); continue
                p.press('a', 8, 90); p.shot('mv_%d_0' % no); p.press('b', 8, 30)        # 기술 목록 화면 (이름 길이·타입 확인)
                if not _wait_menu(p): p.stop(); continue
                p.tick(1 + 17 * tryn)                                                   # 다시 할 때는 누르는 때를 바꿈 (같은 입력 = 같은 난수 = 같은 빗나감)
                hp0, hp1, charged, f = _fight(p, m, tag='mv_%d' % no)
                p.shot('mv_%d_1' % no)
                eff_ok = None
                if eff in STAT:
                    p.tick(120); eff_ok = bool(STAT[eff][1](m))
                res = (hp0, hp1, charged, f, eff_ok, tryn + 1)
                p.stop()
                if f is not None: break
            hp0, hp1, charged, f, eff_ok, ntry = res
            two = eff in (151, 75)
            ok = f is not None and (not two or charged) and eff_ok is not False
            bad += not ok
            print('  %3d %-8s %-6s 위력%3d → 상대 체력 %d→%d%s%s %s %s' % (
                no, nm, sp, pw, hp0, hp1, ' · 모으는 턴 확인' if two and charged else (' · 모으는 턴 못 봄' if two else ''),
                (' · %s %s' % (STAT[eff][0], '걸림' if eff_ok else '안 걸림')) if eff in STAT else '',
                'OK' if ok else ('멈춤/안 맞음' if f is None else '실패'), '' if ntry <= 1 else '(%d번째에 맞음)' % ntry))
    finally:
        ROM = keep
    return bad


def test_boss_move(names, group='Will', cls=0x0b, tid=1, special=131):
    """보스 기술: 트레이너 표에 지정됐는지 + 그 보스 전투에서 상대가 그 기술을 실제로 씀(첫 디지몬 기술을 그 기술 하나로 바꿔 강제)."""
    import encounters
    r = dmrom.Rom(ROM)
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    ts = [t for t in r.trainers(len(groups)) if groups[t['group']] == group and t['idx'] == tid - 1]
    in_table = False
    for t in ts:                                                                     # 기술 칸 있는 파티: 종(1)·레벨·기술 4
        a = r.d.index(0x50, t['start']) + 2
        for lv, sp, _ in t['mons']:
            a += 2
            if t['kind'] in (2, 3): a += 1
            if special in r.d[a:a + 4]: in_table = True
            a += 4
    p = new('grass.state'); m = p.pb.memory
    put_party(p, [(t['mons'][0][1], 60, 70)], names); m[JOHTO_BADGES] = 0xff
    for o in (34, 36): m[PARTY_MONS + o], m[PARTY_MONS + o + 1] = 0x03, 0xe7
    for i in range(160):
        m[OTHER_CLASS] = cls; m[OTHER_ID] = tid
        p.press(['left', 'right'][i % 2], 10, 10); p.tick(30)
        if m[BATTLE_MODE]: break
    _wait_menu(p)
    for k_, v_ in enumerate((special, 0, 0, 0)): m[1, E_MOVES + k_] = v_
    m[1, E_PP] = 5
    hp0 = m[B_MON_HP] << 8 | m[B_MON_HP + 1]; used = False
    for turn in range(3):                                                            # 상대는 메뉴 전에 이번 턴 기술을 골라 둠 → 다음 턴부터 그 기술
        p.press('a', 8, 90); p.press('a', 8, 30)
        for f in range(0, 2400, 10):
            p.tick(10)
            if m[CUR_E_MOVE] == special: used = True
            if used and (m[B_MON_HP] << 8 | m[B_MON_HP + 1]) < hp0: break
            if f % 60 == 50: p.press('b', 4, 4)
        if used and (m[B_MON_HP] << 8 | m[B_MON_HP + 1]) < hp0: break
        _wait_menu(p)
    p.shot('boss_%s' % group)
    hp1 = m[B_MON_HP] << 8 | m[B_MON_HP + 1]
    ok = in_table and used and hp1 < hp0
    print('  %s: 트레이너 표에 %s %s, 전투에서 상대가 씀 %s, 내 체력 %d→%d → %s (work/shots/boss_%s.png)' % (
        group, r.d[0] and special, '있음' if in_table else '없음', used, hp0, hp1, 'OK' if ok else '실패', group))
    p.stop()
    return 0 if ok else 1


def test_move_desc(names, moves=(221, 136, 245), sp='워그레이몬'):
    """기술 설명 화면 3개: 필드에서 START → 디지몬 → 첫 칸 → 「사용할 수 있는기술」, 커서를 기술마다 내려 찍음 → work/shots/desc_<n>.png
    통과: 화면 아래 설명 칸이 비어 있지 않음(글자 픽셀이 있음)"""
    import numpy as np
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    p = new('grass.state'); m = p.pb.memory
    put_party(p, [(N[sp], 50, 70)], names)
    b = PARTY_MONS
    for k in range(4): m[b + 2 + k] = moves[k] if k < len(moves) else 0; m[b + 23 + k] = 5 if k < len(moves) else 0
    p.tick(30)
    for k in ('start', 'a', 'a', 'down', 'down', 'a'): p.press(k, 8, 70)
    bad = 0
    for i, no in enumerate(moves):
        if i: p.press('down', 8, 60)
        p.tick(30); p.shot('desc_%d' % i)
        img = np.asarray(p.pb.screen.image.convert('L'), dtype=int)
        ink = int((img[112:140, 8:152] < 100).sum())                                   # 아래 설명 칸 글자 픽셀
        ok = ink > 80; bad += not ok
        print('  기술 %d 설명 화면 → %s (글자 픽셀 %d, work/shots/desc_%d.png)' % (no, 'OK' if ok else '비어 있음', ink, i))
    p.stop()
    return bad


def test_evo_scene(names, sp='아구몬', lv=15):
    """S8 진화 장면: 아구몬 Lv15 에 이상한사탕 1번 → Lv16 그레이몬 진화. 시작 글·흰 번쩍임·끝 글을 찍음 → work/shots/evo8_*.png
    통과: 진화 뒤 종이 바뀜 + 찍은 장면 중 화면이 거의 흰색인 장면(번쩍임)이 있음"""
    import numpy as np
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    p = new('intro.state'); m = p.pb.memory
    put_party(p, [(N[sp], lv, 70)], names); m[JOHTO_BADGES] = 0xff; p.tick(10)
    p.press('start', 6, 80); p.press('down', 6, 30); p.press('a', 6, 90)
    p.press('a', 6, 60); p.press('a', 6, 90); p.press('a', 6, 60)
    white = 0; k = 0; best = 0
    for f in range(1400):
        p.tick(1)
        img = np.asarray(p.pb.screen.image.convert('L'), dtype=int)
        wf = (img > 240).mean()
        if wf > 0.97: white += 1
        if f % 40 == 0 and k < 30: p.shot('evo8_%02d' % k); k += 1
        if f % 120 == 119: p.press('a', 6, 0)
    sp1 = m[PARTY_SPECIES]
    ok = sp1 == N.get('그레이몬') and white >= 1
    print('  %s Lv%d → %s, 흰 화면 %d프레임 → %s (work/shots/evo8_*.png)' % (sp, lv, r.name(sp1), white, 'OK' if ok else '실패'))
    p.stop()
    return 0 if ok else 1


def test_party_icons(names):
    """G단계: 파티 화면에 분류가 다른 디지몬 6마리를 넣고 아이콘 찍기 → work/shots/party_icons_*.png"""
    r = dmrom.Rom(ROM); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    sets = [['코로몬', '아구몬', '파피몬', '피요몬', '텐타몬', '팔몬'], ['쉬라몬', '안드로몬', '엔젤몬', '데블몬', '가트몬', '쿠가몬']]
    for k, six in enumerate(sets):
        p = new('intro.state'); m = p.pb.memory
        put_party(p, [(N[x], 20, 70) for x in six if x in N], names); p.tick(10)
        p.press('start', 6, 80); p.press('a', 6, 120); p.tick(40); p.shot('party_icons_%d' % k)
        p.tick(16); p.shot('party_icons_%d_b' % k); p.stop()
    print('  파티 화면 2장 (work/shots/party_icons_*.png)')
    return 0


if __name__ == '__main__':
    os.makedirs(SHOTS, exist_ok=True)
    if not os.path.exists(os.path.join(W, 'intro.state')) or '--intro' in sys.argv:
        print('인트로 지나가는 중…'); intro()
    r = dmrom.Rom(ROM)
    names = {n: bytes(r.d[r.names + 10 * (n - 1):r.names + 10 * n]) for n in range(1, dmrom.NUM + 1)}
    print('트레이너 표'); bad = test_trainers()
    print('진화'); bad += test_evo(names)
    print('암흑 진화'); bad += test_dark(names)
    print('검은 톱니'); bad += test_black_gear(names)
    print('대사 화면 (시험용 롬)'); bad += test_texts(names)
    print('포획'); bad += test_catch(names)
    print('전투 화면 그림 (시험용 롬)'); bad += test_battle_pics(names)
    print('파티 화면 아이콘'); bad += test_party_icons(names)
    print('사천왕 전투 시작'); bad += test_e4(names)
    print('S7 전용 필살기 31'); bad += test_moves(names)
    print('S7 보스 기술'); bad += test_boss_move(names)
    print('S7 기술 설명 화면'); bad += test_move_desc(names)
    print('S8 진화 장면'); bad += test_evo_scene(names)
    print('결과:', '모두 통과' if not bad else '%d개 실패' % bad)
    sys.exit(1 if bad else 0)
