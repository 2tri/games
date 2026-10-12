"""용어·지명·수호자 이름 (7판 누적, 설계자 2026-10-07): rules.TERM_RENAME / PLACE_RENAME / BADGE_RENAME / LEADER_RENAME

1. 대사 전체: 모든 글 덩어리(옮겨진 것도 따라감)에서 낱말을 바꿈 — 긴 것부터, 한 번에(한글 앞뒤가 아닌 자리만), 조사는 patch._josa 로 맞춤. 길면 빈 뱅크로(retext)
2. 지명 표(Landmarks: x, y, 이름 포인터): 새 이름을 같은 뱅크 빈 곳에 쓰고 포인터만 바꿈 (자리 없으면 그 지명은 대사만 바뀌고 지도는 옛 이름 → 로그)
3. 수호자(관장) 트레이너 이름: 트레이너 표의 이름 (길면 boss2.rebuild_group 으로 무리를 옮김)
4. 직업 이름 「관장」·배지 이름 표: 심볼이 있고 제자리에 들어갈 때만 (안 되면 로그)
patch.build 에서 story2 다음, diff7 앞에 `import places2; P.log += places2.apply(P)`"""
import os, re
import dmrom, krtext, rules
from dmrom import addr


def _keys(S):
    for at in ('by', 'syms', 'd'):
        v = getattr(S, at, None)
        if isinstance(v, dict):
            return v
    return {}


def rename_texts(P, pairs, names=()):
    """pairs = [(옛, 새)] 를 모든 대사 덩어리에 적용 → (바꾼 덩어리 수, 옮긴 수)
    낱말 앞이 한글이 아닐 때만(「완성도」의 성도 제외). names(사람 이름)는 뒤가 조사·기호·끝일 때만(「비상구」「그린 그림」 제외)"""
    import texts as TX, patch, story2
    d = bytes(P.d)
    idx = TX.refs_index(d)
    done = set()
    n_in = n_far = 0
    pairs = sorted(pairs, key=lambda q: -len(q[0]))
    M = dict(pairs)
    NM = set(names)
    JO = '[은는이가을를과의에와도만랑『<!?,.…]'     # 이름 뒤: 조사·말머리 기호·글 명령(<LINE>)·문장 부호·끝 (빈칸은 안 됨: 「그린 사람」)
    alt = '|'.join(re.escape(o) + ('(?=%s|$)' % JO if o in NM else '') for o, _ in pairs)
    rx = re.compile('(?<![가-힣])(?:%s)' % alt)
    for (bank, ptr) in sorted(idx):
        a = story2.follow(d, addr(bank, ptr))
        if a >= len(d) or a in done or d[a] != 0x00:
            continue
        t = TX.read_text(d, a)
        if not t or t[1] < 1:
            continue
        done.add(a)
        s0 = s = t[2]
        m = rx.search(s)
        while m:
            nm = M[m.group(0)]
            s = s[:m.start()] + nm + patch._josa(nm, s[m.end():])
            m = rx.search(s, m.start() + len(nm))
        if s == s0:
            continue
        s = patch._wrap(s)
        if P.retext(a, s) == 'in':
            n_in += 1
        else:
            n_far += 1
        d = bytes(P.d)
    return n_in, n_far


def landmarks(P, S, M):
    a = S.get('Landmarks')
    if a is None:
        return '지명 표: Landmarks 심볼 없음'
    d = bytes(P.d)
    bank = a // 0x4000
    done = []
    miss = []
    for i in range(120):
        e = a + 4 * i
        p = d[e + 2] | d[e + 3] << 8
        if not 0x4000 <= p < 0x8000:
            break
        na = addr(bank, p)
        j = d.find(0x50, na, na + 40)
        if j < 0:
            continue
        old = krtext.decode(d, na, j).replace('　', ' ').strip()
        new = M.get(old)
        if not new:
            continue
        nb = krtext.encode(new) + b'\x50'
        if len(nb) <= j + 1 - na:
            P.put(na, nb + b'\x50' * (j + 1 - na - len(nb)))
            done.append(old + '→' + new)
            continue
        try:
            b, q = P.sp.take(len(nb), bank=bank)
            P.put(addr(b, q), nb)
            P.put(e + 2, bytes([q & 255, q >> 8]))
            done.append(old + '→' + new)
        except MemoryError:
            miss.append(old)
    return '지명 표 %d개 바꿈%s' % (len(done), ' — 자리 없어 지도는 옛 이름: ' + ', '.join(miss) if miss else '')


def leaders(P, groups, M):
    """트레이너 표의 이름 (같은 길이면 제자리, 길면 무리 다시 씀)"""
    import boss2
    P.r.d = P.d
    done = []
    for g, new in M.items():
        ts = [t for t in P.r.trainers(len(groups)) if groups[t['group']] == g]
        if not ts:
            continue
        t = ts[0]
        ob = krtext.encode(t['name'])
        nb = krtext.encode(new)
        if len(nb) == len(ob):      # 8판: 짧아지면 끝표시가 뒤로 밀려 무리 표가 깨짐(마티스→한솔: 무리 사라짐) → 같은 길이만 제자리
            P.put(t['start'], nb + b'\x50' * (len(ob) - len(nb)))
            P.r.d = P.d
        else:
            boss2.rebuild_group(P, groups, g, {0: (new, [(lv, sp) for lv, sp, _ in t['mons']])})
            P.r.d = P.d
        done.append('%s %s→%s' % (g, t['name'], new))
    return '수호자 이름 %d명: %s' % (len(done), ', '.join(done))


def strings_in_place(P, S, key_words, M, label):
    """심볼 이름에 key_words 가 든 표(@ 로 끝나는 글 나열)를 제자리에서 바꿈 (전체 길이가 늘지 않을 때만)"""
    keys = _keys(S)
    d = bytes(P.d)
    hit = [k for k in keys if all(w in k.lower() for w in key_words)]
    if not hit:
        return '%s: 심볼 없음' % label
    a = keys[hit[0]]
    pos = a
    names = []
    for i in range(64):
        j = d.find(0x50, pos, pos + 24)
        if j < 0:
            break
        names.append(krtext.decode(d, pos, j))
        pos = j + 1
        if names[-1] == '' or i > 40:
            break
    new = [M.get(n, n).replace('포켓몬', '디지몬') for n in names]
    ob = b''.join(krtext.encode(n) + b'\x50' for n in names)
    nb = b''.join(krtext.encode(n) + b'\x50' for n in new)
    if new == names:
        return '%s(%s): 바꿀 것 없음 (%s)' % (label, hit[0], '·'.join(names))
    if len(nb) > len(ob):
        return '%s(%s): 길이 늘어 못 바꿈 (%d > %d) — 대사만 바뀜' % (label, hit[0], len(nb), len(ob))
    P.put(a, nb + b'\x50' * (len(ob) - len(nb)))
    return '%s(%s): %d개 바꿈 (%s)' % (label, hit[0], sum(1 for x, y in zip(names, new) if x != y), '·'.join(new))


def apply(P):
    import romanat, encounters
    S = romanat.Sym()
    SY = _keys(S)
    log = []
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    pairs = list(rules.TERM_RENAME.items()) + list(rules.PLACE_RENAME.items()) + list(rules.BADGE_RENAME.items()) + list(rules.LEADER_TEXT.items())
    try:
        n_in, n_far = rename_texts(P, pairs, names=rules.LEADER_TEXT.keys())
        log.append('용어·지명·이름 대사 %d덩어리 (제자리 %d, 옮김 %d)' % (n_in + n_far, n_in, n_far))
    except Exception as ex:
        log.append('대사 바꾸기 실패 %r' % (ex,))
    for fn in (lambda: landmarks(P, SY, rules.PLACE_RENAME),
               lambda: leaders(P, groups, rules.LEADER_RENAME),
               lambda: strings_in_place(P, SY, ('trainerclass', 'name'), {'관장': rules.TERM_RENAME.get('관장', '관장')}, '직업 이름'),
               lambda: strings_in_place(P, SY, ('badge', 'name'), rules.BADGE_RENAME, '배지 이름 표')):
        try:
            log.append(fn())
        except Exception as ex:
            log.append('places2 실패 %r' % (ex,))
    P.r.d = P.d
    return log
