"""작업팩 2부 H-5 — 2부 보스·오메가블레이드 입수 (설계자 2026-10-06). 새 맵 스크립트 없이 기존 데이터만 바꿈.
(1) 보스 트레이너: 관동 도로(Route1~25)의 쿨트레이너♂(없으면 ♀) 중 레벨 합이 가장 높은 사람 → 이름 「오이카와」, 파티 rules.BOSS2
    궁극체 예외(R13): pick() 이 돌려주는 (무리, 순서) 를 patch·check 가 같이 씀 (ultimate_ok_trainers)
(2) 오메가블레이드: rules.OMEGA_BALL 의 맵 아이템볼(순서) 을 오메가블레이드로 (디아블로몬의 역습 이벤트는 백로그 → 그 전까지 은빛산 보물)
pokegold-kr: constants/trainer_constants.asm(직업·이름 순서), constants/item_constants.asm, data/trainers/parties.asm, maps/*.asm
patch.build 에서 digi2 다음에 `import boss2; P.log += boss2.apply(P, groups)`"""
import os, re, struct
import dmrom, krtext, rules, encounters
from dmrom import addr

KANTO_MAPS = ['Route%d' % n for n in range(1, 26)]


def _consts(path, head):
    """asm 의 const 목록 → {이름: 번호}. head('trainerclass')가 있으면 {(직업, 이름): 직업 안 순서(1부터)}"""
    out = {}
    n = 0
    cls = None
    for line in open(path, encoding='utf-8', errors='ignore'):
        t = line.split(';')[0].strip()
        m = re.match(r'const_def(?:\s+(\$?[0-9a-fA-F]+))?$', t)
        if m:
            n = int(m.group(1).replace('$', '0x'), 0) if m.group(1) else 0
            continue
        if head:
            m = re.match(head + r'\s+(\w+)', t)
            if m:
                cls = m.group(1)
                n = 1
                continue
        m = re.match(r'const\s+(\w+)', t)
        if m:
            out[(cls, m.group(1)) if head else m.group(1)] = n
            n += 1
        elif re.match(r'const_skip', t):
            n += 1
    return out


def item_ids():
    return _consts(os.path.join(encounters.KR, 'constants', 'item_constants.asm'), None)


def pick():
    """관동 도로의 쿨트레이너♂(없으면 ♀) 중 레벨 합이 가장 높은 사람 → (무리 이름, 무리 안 순서 0부터)"""
    KR = encounters.KR
    tc = _consts(os.path.join(KR, 'constants', 'trainer_constants.asm'), 'trainerclass')
    src = open(os.path.join(KR, 'data', 'trainers', 'parties.asm'), encoding='utf-8', errors='ignore').read()
    pat = re.compile(r'^(\w+)Group:\n(.*?)(?=^\w+Group:|\Z)', re.M | re.S)
    blocks = {b.group(1).upper(): (b.group(1), b.group(2)) for b in pat.finditer(src)}
    rec_pat = re.compile(r'db\s+"')
    lv_pat = re.compile(r'db\s+(\d+),\s[A-Z_0-9]+')
    for cls in ('COOLTRAINERM', 'COOLTRAINERF'):
        if cls not in blocks:
            continue
        gname, body = blocks[cls]
        cuts = [m.start() for m in rec_pat.finditer(body)]
        recs = [body[a:b] for a, b in zip(cuts, cuts[1:] + [len(body)])]
        best = None
        for mp in KANTO_MAPS:
            f = os.path.join(KR, 'maps', mp + '.asm')
            if not os.path.exists(f):
                continue
            txt = open(f, encoding='utf-8', errors='ignore').read()
            for m in re.finditer(r'trainer\s+(?:EVENT\w+,\s*)?%s,\s*(\w+)' % cls, txt):      # generic_trainer CLASS, NICK / trainer EVENT, CLASS, NICK
                idx = tc.get((cls, m.group(1)))
                if not idx or idx > len(recs):
                    continue
                lvsum = sum(int(x) for x in lv_pat.findall(recs[idx - 1]))
                if best is None or lvsum > best[0]:
                    best = (lvsum, idx, mp)
        if best:
            return gname, best[1] - 1
    raise AssertionError('관동 쿨트레이너를 못 찾음')


def ultimate_ok_trainers():
    try:
        g, i = pick()
        return {(g, i)}
    except Exception:
        return set()


def rebuild_group(P, groups, gname, over):
    """무리 하나를 다시 씀. over = {순서: (새 이름, [(레벨, 종 번호)])}. 종류(기술·도구 칸)는 그대로, 기술은 그 레벨까지 배운 마지막 4개"""
    d = P.d
    ts = [t for t in P.r.trainers(len(groups)) if groups[t['group']] == gname]
    out = bytearray()
    for t in ts:
        if t['idx'] not in over:
            out += bytes(d[t['start']:t['end']])
            continue
        name, mons = over[t['idx']]
        kind = t['kind']
        out += krtext.encode(name) + b'\x50' + bytes([kind])
        for lv, sp in mons:
            out += bytes([lv, sp])
            if kind in (2, 3):
                out.append(0)
            if kind in (1, 3):
                ms = []
                for l, mv in P.r.evos_attacks(sp)[1]:
                    if l <= lv and mv not in ms:
                        ms.append(mv)
                        if len(ms) > 4:
                            ms.pop(0)
                out += bytes(ms + [0] * (4 - len(ms)))
        out.append(0xff)
    s, e = ts[0]['start'], ts[-1]['end']
    bank, tab = P.r.trainer_table()
    if len(out) <= e - s:
        P.put(s, bytes(out) + b'\xff' * (e - s - len(out)))
        where = '제자리'
    else:
        b, p = P.sp.take(len(out), bank=bank)
        P.put(addr(b, p), bytes(out))
        P.put(tab + 2 * groups.index(gname), struct.pack('<H', p))
        P.sp.give(bank, s % 0x4000 + 0x4000, e % 0x4000 + 0x4000)
        where = '%02X:%04X' % (b, p)
    P.r.d = P.d
    return where


def item_ball(P, map_label, order, new_item):
    """maps/<맵>.asm 의 itemball 줄(순서 order, 0부터)을 새 도구로. 그 맵 아이템볼 (도구, 개수) 바이트 열을 롬에서 하나로 찾아 바꿈"""
    KR = encounters.KR
    ids = item_ids()
    f = os.path.join(KR, 'maps', map_label + '.asm')
    assert os.path.exists(f), '맵 파일 없음 ' + map_label
    balls = re.findall(r'itemball\s+(\w+)(?:,\s*(\d+))?', open(f, encoding='utf-8', errors='ignore').read())
    assert len(balls) > order, '%s 아이템볼 %d개' % (map_label, len(balls))
    seq = bytes(sum(([ids[c], int(q or 1)] for c, q in balls), []))
    dd = bytes(P.d)
    i = dd.find(seq)
    assert i >= 0 and dd.find(seq, i + 1) < 0, '%s 아이템볼 바이트 열을 하나로 못 찾음' % map_label
    P.d[i + 2 * order] = new_item
    return '%s 아이템볼 %d번(%s) → 도구 %d' % (map_label, order + 1, balls[order][0], new_item)


def apply(P, groups):
    log = []
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    try:
        g, i = pick()
    except Exception as ex:
        return ['H-5 보스 트레이너 못 정함: %r (maps/Route*.asm 의 쿨트레이너 줄 형식을 코멘트로)' % (ex,)]
    name, mons = rules.BOSS2
    party = [(lv, N[sp] if sp in N else N[until]) for lv, sp, until in mons]
    where = rebuild_group(P, groups, g, {i: (name, party)})
    log.append('H-5 보스 트레이너: %s %d번째 → %s (%s), %s' % (
        g, i + 1, name, '·'.join(sp if sp in N else '%s(임시 %s)' % (sp, until) for _, sp, until in mons), where))
    try:
        log.append(' ' + item_ball(P, rules.OMEGA_BALL[0], rules.OMEGA_BALL[1], rules.OMEGA_BLADE['item']))
    except Exception as ex:
        log.append(' 오메가블레이드 아이템볼 실패: %r' % (ex,))
    return log
