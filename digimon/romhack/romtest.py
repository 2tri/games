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
RARE_CANDY, POKE_BALL = 0x20, 0x05
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
    PARTY = [(N['파피몬'], 15, 200), (N['파피몬'], 15, 70), (N['그레이몬'], 31, 70), (N['코로몬'], 10, 70),
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
        ('코로몬 Lv11 → 아구몬', 3, 0, None, N['아구몬']),
    ]
    SK = '스컬그레몬' if '스컬그레몬' in N else '그레이몬'      # 스컬그레몬 그림 전에는 암흑 갈래가 없어 그대로
    extra = [  # 따로 한 마리씩: 이름, 종, 레벨, 기대 종, 유대(친밀도)[, 배지, 누르는 수]
        ('브이몬 Lv16 → 엑스브이몬', '브이몬', 15, '엑스브이몬', 70),
        ('뿔몬 Lv11 → 파피몬 (새 칸, 그림 있을 때)', '뿔몬', 10, '파피몬', 70),
        ('토코몬 Lv10 → 파닥몬 (새 칸, 그림 있을 때)', '토코몬', 9, '파닥몬', 70),
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
    ok = all([r.name(sp) for _, sp, _ in t['mons']][0] == '추추몬' and len(t['mons']) == 2 for t in r1)
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
            p.press('a', 6, 120); shots = 0
            for page in range(8):
                p.tick(90); p.shot('txt_%d_%d' % (k, page)); shots += 1
                p.press('a', 6, 40)
            ok = (m[XC], m[YC]) == (5, 2); bad += not ok
            print('  %-24s → 책장 앞 %s, 화면 %d장 (work/shots/txt_%d_*.png)' % (label, 'OK' if ok else '못 감 %d,%d' % (m[XC], m[YC]), shots, k))
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
                 ('묘티스몬', '레이디데블'), ('피노키몬', '아포카리몬'), ('오메가몬', '디아블로몬')]
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
    print('결과:', '모두 통과' if not bad else '%d개 실패' % bad)
    sys.exit(1 if bad else 0)
