"""고친 롬(work/myver.gbc) 자동 시험 — PyBoy
  python3 romtest.py            진화 7가지 + 포획 막기
처음 한 번은 인트로를 지나가서 work/intro.state 를 만든다 (롬이 바뀌면 지우고 다시).
램 주소는 pokegold-kr 디스어셈블리 기준 (한글판 금)."""
import os, sys
import dmrom, krtext
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


def put_party(p, mons, names):
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
    m[NUM_ITEMS] = 1; m[NUM_ITEMS + 1] = RARE_CANDY; m[NUM_ITEMS + 2] = 10; m[NUM_ITEMS + 3] = 0xff
    m[NUM_BALLS] = 1; m[NUM_BALLS + 1] = POKE_BALL; m[NUM_BALLS + 2] = 20; m[NUM_BALLS + 3] = 0xff


def candy(slot, mons, names, badges=0, presses=16):
    """방에서 가방 → 이상한사탕 → slot 번째에게 1번(이어서 몇 번 더) 먹이고 종 번호를 돌려줌"""
    p = new('intro.state'); m = p.pb.memory
    put_party(p, mons, names); m[JOHTO_BADGES] = badges; p.tick(10)
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
    PARTY = [(N['파피몬'], 15, 120), (N['파피몬'], 15, 70), (N['그레이몬'], 29, 70), (N['코로몬'], 10, 70),
             (N['메탈그레몬'], 44, 70), (N['가루몬'], 29, 70)]
    cases = [  # 이름, slot, 배지, 레벨 덮어쓰기, 기대 종
        ('파피몬 유대↑ → 가루몬', 0, 0, None, N['가루몬']),
        ('파피몬 유대↓ → 우가몬', 1, 0, None, N['우가몬']),
        ('그레이몬 + 용기 배지 Lv30 → 메탈그레이몬', 2, 1 << 5, None, N['메탈그레몬']),
        ('그레이몬 배지 없음 Lv30 → 그대로', 2, 0, None, N['그레이몬']),
        ('그레이몬 다른 배지 Lv30 → 그대로', 2, 1, None, N['그레이몬']),
        ('그레이몬 다른 배지 Lv36 → 메탈그레이몬', 2, 1, 35, N['메탈그레몬'], 30),
        ('메탈그레이몬 + 용기 Lv45 → 워그레이몬', 4, 1 << 5, None, N['워그레이몬'], 30),
        ('메탈그레이몬 다른 배지 Lv45 → 그대로', 4, 1, None, N['메탈그레몬']),
        ('가루몬 + 우정 배지 Lv30 → 워가루몬', 5, 1 << 4, None, N['워가루몬']),
        ('코로몬 Lv11 → 아구몬', 3, 0, None, N['아구몬']),
    ]
    bad = 0
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
    c255 = sum(throw(255, k) for k in range(trials))
    print('  상대 %d번, 포획률 0: %d/%d 잡힘 (0이어야 함) / 포획률 255: %d/%d 잡힘 (0보다 커야 함)' % (sp, c0, trials, c255, trials))
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
    return bad


if __name__ == '__main__':
    os.makedirs(SHOTS, exist_ok=True)
    if not os.path.exists(os.path.join(W, 'intro.state')) or '--intro' in sys.argv:
        print('인트로 지나가는 중…'); intro()
    r = dmrom.Rom(ROM)
    names = {n: bytes(r.d[r.names + 10 * (n - 1):r.names + 10 * n]) for n in range(1, dmrom.NUM + 1)}
    print('진화'); bad = test_evo(names)
    print('포획'); bad += test_catch(names)
    print('결과:', '모두 통과' if not bad else '%d개 실패' % bad)
    sys.exit(1 if bad else 0)
