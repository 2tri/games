"""작업팩 S10 — 필드 그림 (설계자 2026-10-06 작성)
10-1 트레이너 전투 시작 효과: 금의 포켓볼 2타일(16×8, 아래는 엔진이 뒤집어 그림) → 디지바이스 + 색
10-2 땅 위 아이템볼(SPRITE_POKE_BALL, 16×16 1장) → 디지알
10-3 파도타기(SPRITE_SURF) → 고래몬 등 위
10-4·10-5 포켓몬 모양 필드 그림 → 디지몬 (rules.FIELD_SPRITES: 스프라이트 상수 이름 → (그림 이름, 팔레트))
그림은 이 파일 안의 글자 격자: . 투명  o 밝은색  x 어두운색  # 검정  e 눈(앞모습 검정, 뒷모습 몸색)
스프라이트 번호는 pokegold-kr constants/sprite_constants.asm 에서 읽음.
표 항목(6바이트: 주소·크기·뱅크·종류·팔레트)의 크기·종류는 그대로 두고 그림만 바꿈.
patch.build 에서 evo8 다음에 `import field10; P.log += field10.apply(P)`"""
import os, re, struct
import rules
from dmrom import addr

# ── 그림 ──
EGG = [  # 디지알 16×16 (아이템볼)
    '................',
    '.....######.....',
    '....#oooooo#....',
    '...#oooooooo#...',
    '..#oooxooooxo#..',
    '..#ooxoxooxox#..',
    '.#oooooooooooo#.',
    '.#oxxxxxxxxxxo#.',
    '.#xoxoxoxoxoxx#.',
    '.#oxxxxxxxxxxo#.',
    '.#oooooooooooo#.',
    '..#oooooooooo#..',
    '..#oooooooooo#..',
    '...#oooooooo#...',
    '....########....',
    '................']
BALL_TOP = [  # 전투 시작 효과 16×8 (위 절반, 아래는 엔진이 뒤집음) → 디지바이스
    '.....######.....',
    '...##oooooo##...',
    '..#oooooooooo#..',
    '.#ooo######ooo#.',
    '.#oo#xxxxxx#oo#.',
    '#ooo#xxxxxx#ooo#',
    '#oo##xxxxxx##oo#',
    '#oo#xxxxxxxx#oo#']

# 서는 그림 3장: 앞(아래 보기)·뒤·옆(왼쪽 보기). 뒤는 앞에서 e → x 로 (눈 지움) 자동
SPRITES = {
    'whamon': {  # 고래몬 + 올라탄 사람 (파도타기)
        'down': [
            '......####......',
            '.....#oooo#.....',
            '.....#e##e#.....',
            '......#oo#......',
            '...#########....',
            '..#xxxxxxxxx#...',
            '.#xxxxxxxxxxx#..',
            '.#xx#xxxxx#xx#..',
            '.#xxxxxxxxxxx#..',
            '.#xooooooooox#..',
            '..#ooooooooo#...',
            '...#ooooooo#....',
            '....#######.....',
            '.....#x#x#......',
            '......###.......',
            '................'],
        'up': [
            '......####......',
            '.....#oooo#.....',
            '.....#oooo#.....',
            '......#oo#......',
            '...#########....',
            '..#xxxxxxxxx#...',
            '.#xxxxxxxxxxx#..',
            '.#xxxxxxxxxxx#..',
            '.#xxxxxxxxxxx#..',
            '.#xxxxxxxxxxx#..',
            '..#xxxxxxxxx#...',
            '...#xxxxxxx#....',
            '....#######.....',
            '...#xx#.#xx#....',
            '..#xxx#.#xxx#...',
            '...###...###....'],
        'left': [
            '.......####.....',
            '......#oooo#....',
            '......#e#oo#....',
            '.......#oo#.....',
            '....########....',
            '..##xxxxxxxx##..',
            '.#xxxxxxxxxxxx#.',
            '#x#xxxxxxxxxxx#.',
            '#xxxxxxxxxxxxx#.',
            '#ooooooooxxxxx##',
            '.#oooooooxxxxxx#',
            '..######xxxxx#x#',
            '........#xxx#.##',
            '.........#x#....',
            '..........#.....',
            '................']},
    'gekomon': {  # 개굴몬 (개구리, 머리 위 나팔)
        'down': [
            '.......##.......',
            '......#xx#......',
            '.....#xxxx#.....',
            '....#xeooex#....',
            '....#xxxxxx#....',
            '...#xxxxxxxx#...',
            '..#xoooooooox#..',
            '..#xoooooooox#..',
            '..#xoooooooox#..',
            '...#xoooooox#...',
            '..#xxoooooxxx#..',
            '.#xx#xxxxxx#xx#.',
            '.#x#.######.#x#.',
            '..#..........#..',
            '................',
            '................'],
        'left': [
            '......##........',
            '.....#xx#.......',
            '....#xxxx#......',
            '...#xexxxx#.....',
            '...#xxxxxxx#....',
            '..#xxxxxxxxx#...',
            '.#oooxxxxxxxx#..',
            '.#ooooxxxxxxx#..',
            '.#ooooxxxxxxx#..',
            '..#oooxxxxxx#...',
            '.#xxxxxxxxxxx#..',
            '#xx#xxxxxxx#xx#.',
            '#x#.#######.#x#.',
            '.#...........#..',
            '................',
            '................']},
    'elecmon': {  # 에렉몬 (붉은 토끼형, 꼬리 부채)
        'down': [
            '..#......#..##..',
            '.#x#....#x#x#x#.',
            '.#xx#..#xx#xoxo#',
            '..#xx##xx#xoxox#',
            '...#xxxxx##xoxo#',
            '..#xxeooex#xxx#.',
            '..#xxxxxxx##x#..',
            '..#xoooooox#....',
            '.#xxoooooooxx#..',
            '.#xoooooooooox#.',
            '.#x#oooooooo#x#.',
            '..#.#oooooo#.#..',
            '....#xx##xx#....',
            '....#x#..#x#....',
            '.....#....#.....',
            '................'],
        'left': [
            '....#......#....',
            '...#x#....#x#.#.',
            '...#xx#..#xx##x#',
            '....#xx##xx#oxo#',
            '.....#xxxxxxxox#',
            '....#xexxxxxxoo#',
            '....#xxxxxxxxx#.',
            '...#xxooooxxx#..',
            '..#xxoooooooxx#.',
            '..#xoooooooooox#',
            '..#x#ooooooo#xx#',
            '...#.#ooooo#.#..',
            '.....#xx#xx#....',
            '.....#x#.#x#....',
            '......#...#.....',
            '................']},
    'kuwagamon': {  # 쿠가몬 (붉은 딱정벌레, 큰 집게)
        'down': [
            '#...........#...',
            '#x#.......#x#...',
            '.#x#.....#x#....',
            '..#x#...#x#.....',
            '...#xxxxx#......',
            '..#xxeoxex#.....',
            '..#xxxxxxx#.....',
            '.#xxx###xxx#....',
            '#xx#xxxxx#xx#...',
            '#x#xxxxxxx#x#...',
            '#x#xxxxxxx#x#...',
            '.#.#xxxxx#.#....',
            '....#xxx#.......',
            '...#x#x#x#......',
            '...#..#..#......',
            '................'],
        'left': [
            '#...............',
            '#x#.............',
            '.#x#..######....',
            '..#x##xxxxxx#...',
            '...#xexxxxxxx#..',
            '...#xxxxxxxxxx#.',
            '..#xxxxxxxxxxx#.',
            '.#x#xxxxxxxxxx#.',
            '#x#.#xxxxxxxxx#.',
            '.#..#xxxxxxxx#..',
            '.....#xxxxxx#...',
            '....#x#x#x#x#...',
            '....#.#...#.#...',
            '................',
            '................',
            '................']},
    'gatomon': {  # 가트몬 (흰 고양이, 큰 귀, 장갑)
        'down': [
            '.#..........#...',
            '#o#........#o#..',
            '#oo#......#oo#..',
            '#ooo#....#ooo#..',
            '.#ooo####ooo#...',
            '..#oooooooo#....',
            '..#oeooooeo#....',
            '..#oooo#ooo#....',
            '...#oooooo#.....',
            '..#xx#oo#xx#..#.',
            '.#xxx#oo#xxx#.#x',
            '.#xx#oooo#xx#.#x',
            '..#.#oooo#.#.#x#',
            '....#o##o#..#x#.',
            '....#o#.#o###...',
            '.....#...#......'],
        'left': [
            '....#.......#...',
            '...#o#.....#o#..',
            '...#oo#...#oo#..',
            '...#ooo###ooo#..',
            '....#oooooooo#..',
            '...#oooooooooo#.',
            '...#oeoooooooo#.',
            '...#oo#ooooooo#.',
            '....#oooooooo#..',
            '..#xx#oooooo#.#.',
            '.#xxx#oooooo#x#.',
            '.#xx#oooooo#xx#.',
            '..#.#oooooo#x#..',
            '....#oo##oo###..',
            '....#o#..#o#....',
            '.....#....#.....']},
    'monochromon': {  # 모노크로몬 (회색 갑옷 짐승, 뿔 하나)
        'down': [
            '.......#........',
            '......#x#.......',
            '....###x###.....',
            '...#xxxxxxx#....',
            '..#xxxxxxxxx#...',
            '..#xeoxxxoex#...',
            '..#xxxxxxxxx#...',
            '.#xxoooooooxx#..',
            '#xxxoooooooxxx#.',
            '#xxxoooooooxxx#.',
            '#xxxoooooooxxx#.',
            '.#xxoooooooxx#..',
            '.#x#xxxxxxx#x#..',
            '.#x#.#x#x#.#x#..',
            '.##..##.##..##..',
            '................'],
        'left': [
            '....#...........',
            '...#x#..........',
            '..##x###........',
            '.#xxxxxx####....',
            '#xxxxxxxxxxx#...',
            '#xexxxxxxxxxx#..',
            '#xxxxxxxxxxxxx#.',
            '.#xoooooooooox#.',
            '.#xoooooooooox#.',
            '.#xoooooooooox#.',
            '.#xoooooooooox#.',
            '..#xxxxxxxxxxx#.',
            '..#x#xx##xx#x#..',
            '..#x#.#..#.#x#..',
            '..##..#..#..##..',
            '................']},
}
PAL_OW = {'RED': 0, 'BLUE': 1, 'GREEN': 2, 'BROWN': 3, 'PINK': 4, 'SILVER': 5, 'TREE': 6, 'ROCK': 7}


def _grid(rows, up=False):
    """글자 격자 → 색번호 2차원 (뒷모습이면 e → x)"""
    out = []
    for r in rows:
        assert len(r) == 16, '격자 폭 %d: %s' % (len(r), r)
        out.append([{'.': 0, 'o': 1, 'x': 2, '#': 3, 'e': (2 if up else 3)}[c] for c in r])
    return out


def _tiles(grid, h=16):
    """16×h 색번호 → 금 OAM 순서(좌상·우상·좌하·우하, 16×16 마다) 2bpp"""
    gfx = bytearray()
    for fy in range(0, h, 16):
        for ty, tx in ((0, 0), (0, 1), (1, 0), (1, 1)):
            for y in range(8):
                row = grid[fy + ty * 8 + y][tx * 8:tx * 8 + 8]
                gfx += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(row)),
                              sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
    return bytes(gfx)


def frames(name):
    """앞·뒤·옆 3장 (뒤가 없으면 앞에서 눈을 지움)"""
    s = SPRITES[name]
    down = _grid(s['down'])
    up = _grid(s['up']) if 'up' in s else _grid(s['down'], up=True)
    left = _grid(s['left'])
    return down, up, left


def _shift(grid, dy=1):
    """걷기 장면용: 1픽셀 아래로 (위 줄은 투명)"""
    return [[0] * 16] * dy + grid[:-dy]


def sprite_ids():
    """pokegold-kr constants/sprite_constants.asm → {이름: 번호}"""
    import encounters
    p = os.path.join(encounters.KR, 'constants', 'sprite_constants.asm')
    ids = {}
    n = 0
    for line in open(p, encoding='utf-8', errors='ignore'):
        t = line.split(';')[0].strip()
        m = re.match(r'const_def(?:\s+(\$?[0-9a-fA-F]+))?$', t)
        if m:
            n = int(m.group(1).replace('$', '0x'), 0) if m.group(1) else 0
            continue
        m = re.match(r'const\s+(SPRITE_\w+)', t)
        if m:
            ids[m.group(1)] = n
            n += 1
            continue
        m = re.match(r'const_skip(?:\s+(\d+))?', t)
        if m:
            n += int(m.group(1) or 1)
    return ids


def _ow_table(P):
    m = re.search(rb'\xe5\x21(..)\x3d\x4f\x06\x00\x3e\x06\xcd..\x2a\x5f\x2a\x57', bytes(P.d), re.S)   # GetSprite: ld hl, OverworldSprites (patch.digivice 와 같음)
    assert m, 'OverworldSprites'
    return addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))


def put_sprite(P, tab, sid, name, pal):
    """표 항목 sid 의 그림을 바꿈. 크기(바이트)·종류는 표 값 그대로: 64 = 1장, 192 = 3장(서기), 종류 1(걷기)이면 3장 더(1픽셀 흔들림)
    2판: 64 이면 앞모습 1장만, 그 밖 크기는 표 6바이트를 로그에 남기고 건너뜀"""
    e = tab + 6 * (sid - 1)
    size, kind = P.d[e + 2], P.d[e + 4]
    raw = bytes(P.d[e:e + 6]).hex()
    if name == 'egg':
        assert size == 64, '아이템볼 크기 %d 표 %s' % (size, raw)
        gfx = _tiles(_grid(EGG))
    else:
        d_, u_, l_ = frames(name)
        if size == 64:
            gfx = _tiles(d_)
        elif size == 192:
            gfx = b''.join(_tiles(g) for g in (d_, u_, l_))
            if kind == 1:
                gfx += b''.join(_tiles(_shift(g)) for g in (d_, u_, l_))
        else:
            raise ValueError('%s 크기 %d 종류 %d 표 %s (64·192 가 아님)' % (name, size, kind, raw))
    b, p = P.sp.take(len(gfx), banks=[0x77, 0x7c, 0x7d, 0x76, 0x75] + [0x2c, 0x2d, 0x3f, 0x6a, 0x72, 0x74])
    P.put(addr(b, p), gfx)
    P.put(e, bytes([p & 255, p >> 8, size, b, kind, pal if pal is not None else P.d[e + 5]]))
    return '%02X:%04X %d바이트 %s' % (b, p, len(gfx), {1: '걷기', 2: '서기', 3: '한 장'}.get(kind, kind))


def _sym_keys(S):
    for at in ('by', 'syms', 'd', 'names', 'table', 'map', 'sym'):
        v = getattr(S, at, None)
        if isinstance(v, dict):
            return list(v.keys())
    try:
        return list(S.keys())
    except Exception:
        return []


def rgb555(c): return (c[0] * 31 // 255) | (c[1] * 31 // 255) << 5 | (c[2] * 31 // 255) << 10


def battle_ball(P):
    """10-1 전투 시작 효과 포켓볼 2타일(32바이트) → 디지바이스. 색은 이름에 Pokeball·Pal 이 든 심볼(있으면)을 흰·밝은 회색·어두운 회색·검정으로"""
    import romanat
    S = romanat.Sym()
    log = []
    keys = _sym_keys(S)
    cand = [k for k in keys if 'ball' in k.lower() and any(w in k.lower() for w in ('tiles', 'gfx', 'graphics', '2bpp'))]
    name = 'TrainerBattlePokeballTiles' if 'TrainerBattlePokeballTiles' in keys else next(
        (k for k in cand if 'trainer' in k.lower() or 'battle' in k.lower()), None)
    if not name:
        return ['10-1 전투 시작 효과: 심볼 못 찾음 (2판 후보: %s)' % (', '.join(cand[:15]) or '없음')]
    a = S[name]
    grid = _grid(BALL_TOP)
    gfx = bytearray()
    for tx in (0, 1):
        for y in range(8):
            row = grid[y][tx * 8:tx * 8 + 8]
            gfx += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(row)),
                          sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
    P.put(a, bytes(gfx))
    log.append('10-1 전투 시작 효과 → 디지바이스 (%X, 32바이트)' % a)
    pal = struct.pack('<4H', rgb555((255, 255, 255)), rgb555((200, 200, 208)), rgb555((96, 96, 112)), rgb555((16, 16, 24)))
    hit = [k for k in _sym_keys(S) if 'okeball' in k.lower() and 'pal' in k.lower()]
    for k in hit:
        try:
            P.put(S[k], pal)
            log.append(' 색 %s → 회색조' % k)
        except Exception as ex:
            log.append(' 색 %s 못 바꿈: %s' % (k, ex))
    if not hit:
        log.append(' 색 심볼 못 찾음 (이름에 Pokeball·Pal) — 색은 그대로. 심볼 이름을 코멘트로')
    return log


def apply(P):
    log = []
    try:
        log += battle_ball(P)
    except Exception as ex:
        log.append('10-1 전투 시작 효과 실패: %r' % (ex,))
    ids = sprite_ids()
    tab = _ow_table(P)
    off = 0x54 - ids.get('SPRITE_POKE_BALL', 0x54)               # patch.digivice 가 쓰는 0x54 와 맞춤 (asm 의 const_def 기준이 달라도)
    if off:
        ids = {k: v + off for k, v in ids.items()}
        log.append(' 스프라이트 번호 보정 %+d' % off)
    done = []
    miss = []
    ALT = {'SPRITE_MILTANK': ('SPRITE_COW', 'SPRITE_MOOMOO', 'SPRITE_MONSTER', 'SPRITE_TAUROS')}   # 2판: 이름이 다를 때 후보
    for const, (name, pal) in rules.FIELD_SPRITES.items():
        const = const if const in ids else next((c for c in ALT.get(const, ()) if c in ids), const)
        if const not in ids:
            miss.append(const)
            continue
        try:
            done.append('%s→%s %s' % (const[7:], name, put_sprite(P, tab, ids[const], name, PAL_OW.get(pal))))
        except Exception as ex:
            miss.append('%s(%s)' % (const, ex))
    log.append('10-2~5 필드 그림 %d: %s' % (len(done), ', '.join(done)))
    if miss:
        log.append(' 못 바꿈 (상수 없음·크기 다름): %s' % ', '.join(miss))
    log.append(' 스프라이트 상수 전체 %d개: %s' % (len(ids), ' '.join('%s=%d' % (k[7:], v) for k, v in sorted(ids.items(), key=lambda kv: kv[1]))))
    log.append(' sprite_constants 에 있는 포켓몬 이름 스프라이트: %s' % ', '.join(sorted(k[7:] for k in ids if any(
        w in k for w in ('LAPRAS', 'SNORLAX', 'GYARADOS', 'HO_OH', 'LUGIA', 'PIKACHU', 'JYNX', 'MOLTRES', 'DRAGON', 'EEVEE', 'TOGE', 'UNOWN',
                         'SUICUNE', 'ENTEI', 'RAIKOU', 'ONIX', 'MARILL', 'BIG')))))
    return log
