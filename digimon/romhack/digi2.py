"""작업팩 2부 H-1 — 디지멘탈 8 (설계자 2026-10-06)
돌 5개(불꽃·천둥·물·잎사귀·달맞이)는 이름만 「○○디지멘탈」로, 새 칸 4개(사랑·순수·희망·빛)는 오메가블레이드처럼 만든다
(속성 = 달맞이 돌, 효과 = 진화의 돌, 설명 하나를 넷이 같이 가리킴, 이름표 한 번에 다시 씀). 새 칸 4개는 상록시티 상점에 판매.
아머 진화: rules.DIGIMENTAL 의 (앞 종 → 뒤 종) 중 둘 다 롬에 있는 것만 ITEM 진화로 넣음. 두리몬의 Lv22 디그몬 줄은 지식디지멘탈로 바꿈.
patch.build 에서 field10 다음에 `import digi2; P.log += digi2.apply(P)`"""
import os, re, struct
import dmrom, krtext, rules, encounters
from dmrom import addr

ITEM, LV = 2, 1


def unused_items():
    """pokegold-kr constants/item_constants.asm 에서 안 쓰는 도구 번호 (이름 ITEM_xx · TERU_SAMA) 오름차순"""
    p = os.path.join(encounters.KR, 'constants', 'item_constants.asm')
    out = []
    n = 0
    for line in open(p, encoding='utf-8', errors='ignore'):
        t = line.split(';')[0].strip()
        m = re.match(r'const_def(?:\s+(\$?[0-9a-fA-F]+))?$', t)
        if m:
            n = int(m.group(1).replace('$', '0x'), 0) if m.group(1) else 0
            continue
        m = re.match(r'const\s+(\w+)', t)
        if m:
            if re.match(r'ITEM_[0-9A-Fa-f]{2}$|TERU_SAMA', m.group(1)) and n < 0xb0:
                out.append(n)
            n += 1
        elif re.match(r'const_skip', t):
            n += 1
    return out


def item_tables(P):
    """(속성표 주소, 설명 포인터 표 주소, 설명 뱅크) — patch.build 의 검은 톱니·오메가블레이드와 같은 방법"""
    dd = bytes(P.d)
    s4 = dd.find(krtext.encode('디지몬을 잡기 위한 도구') + b'\x59')
    assert s4 > 0, '수퍼볼 설명'
    bk = s4 // 0x4000
    pb = struct.pack('<H', 0x4000 + s4 % 0x4000)
    dtab = dd.find(pb, bk * 0x4000, (bk + 1) * 0x4000) - 6
    at = next(a_ for a_ in range(len(dd) - 40) if dd[a_ + 7:a_ + 9] == b'\xb0\x04' and dd[a_ + 21:a_ + 23] == b'\x58\x02' and dd[a_ + 28:a_ + 30] == b'\xc8\x00')
    return at, dtab, bk


def desc_free_runs(P, dtab, bk):
    """설명 뱅크에서 어느 도구도 가리키지 않는 빈 구간 [(시작, 끝)] (오메가블레이드가 같은 글을 합쳐 비운 자리 포함)"""
    dd = bytes(P.d)
    spans = []
    for k in range(249):
        a = addr(bk, dd[dtab + 2 * k] | dd[dtab + 2 * k + 1] << 8)
        if not bk * 0x4000 <= a < (bk + 1) * 0x4000:
            continue
        j = a
        while dd[j] != 0x50:
            j += 2 if 1 <= dd[j] <= 0x0b else 1               # 한글은 2바이트 (둘째 바이트가 0x50 일 수 있음)
        spans.append((a, j + 1))
    spans.sort()
    runs = []
    cur = spans[0][0]
    lo, hi = min(s for s, _ in spans), max(e for _, e in spans)
    end = lo
    for s, e in spans:
        if s > end:
            runs.append((end, s))
        end = max(end, e)
    return sorted(runs, key=lambda r: r[0] - r[1])             # 큰 것부터


def rename_many(P, names):
    """도구 이름 여러 개를 한 번에 (patch.item_rename 과 같은 방법, 표를 한 번만 옮김)"""
    d = bytes(P.d)
    npos = re.search(rb'\x6c(..)\x6c(..)\x00\x00\x00\x6c(..)', d, re.S)
    assert npos, 'NamesPointers'
    ip = npos.start() + 10
    old = d[ip] | d[ip + 1] << 8
    bank = d[ip - 1]
    a = addr(bank, old)
    lst = []
    for _ in range(256):
        j = d.index(0x50, a)
        lst.append(d[a:j])
        a = j + 1
    for no, nm in names.items():
        lst[no - 1] = krtext.encode(nm)
    blob = b''.join(x + b'\x50' for x in lst)
    b, p = P.sp.take(len(blob), bank=bank)
    P.put(addr(b, p), blob)
    P.put(ip, struct.pack('<H', p))
    n = 0
    try:
        import romanat
        il = romanat.Sym()['InitList']
        for m in re.finditer(re.escape(b'\x11' + struct.pack('<H', old)), d[il:il + 0x80]):
            P.put(il + m.start() + 1, struct.pack('<H', p))
            n += 1
    except (FileNotFoundError, KeyError):
        pass
    return n


def add_to_mart(P, mart_label, items):
    """상점 목록(db 개수 / 도구… / -1)에 도구를 덧붙임: 같은 뱅크 빈 곳에 새로 쓰고 Marts 표의 포인터를 바꿈"""
    import romanat
    S = romanat.Sym()
    a = None
    for k in (mart_label, 'Mart' + mart_label, 'Mart' + mart_label + 'City', mart_label + 'Mart'):
        try:
            a = S[k]
            break
        except KeyError:
            pass
    if a is None:
        return '상점 심볼 없음 (%s)' % mart_label
    bank = a // 0x4000
    n = P.d[a]
    lst = list(P.d[a + 1:a + 1 + n])
    assert P.d[a + 1 + n] == 0xff, '상점 목록 끝'
    lst += [x for x in items if x not in lst]
    new = bytes([len(lst)] + lst + [0xff])
    b, p = P.sp.take(len(new), bank=bank)
    P.put(addr(b, p), new)
    mt = S['Marts']
    old = struct.pack('<H', 0x4000 + a % 0x4000)
    hit = 0
    for k in range(64):
        if bytes(P.d[mt + 2 * k:mt + 2 * k + 2]) == old:
            P.put(mt + 2 * k, struct.pack('<H', p))
            hit += 1
    return '%s 상점 %d → %d개 (%02X:%04X, 표 %d곳)' % (mart_label, n, len(lst), b, p, hit)


def apply(P):
    log = []
    N = {P.r.name(n): n for n in range(1, dmrom.NUM + 1)}
    DM = rules.DIGIMENTAL
    free = [x for x in unused_items() if x != rules.OMEGA_BLADE['item']]
    need = [k for k, v in DM.items() if v[0] is None]
    assert len(free) >= len(need), '안 쓰는 도구 칸 부족 %d < %d' % (len(free), len(need))
    ids = {k: (v[0] if v[0] is not None else free[need.index(k)]) for k, v in DM.items()}
    at, dtab, bk = item_tables(P)
    dd = bytes(P.d)
    # 새 칸 4개: 속성 = 달맞이 돌(8), 값, 설명(하나를 같이), 효과 = 진화의 돌
    desc = b'\x59'.join(krtext.encode(l) for l in rules.DIGIMENTAL_DESC) + b'\x50'
    runs = desc_free_runs(P, dtab, bk)
    run = next((r for r in runs if r[1] - r[0] >= len(desc)), None)
    if run:
        P.put(run[0], desc)
        dp = struct.pack('<H', 0x4000 + run[0] % 0x4000)
    else:
        dp = bytes(dd[dtab + 2 * (rules.OMEGA_BLADE['item'] - 1):dtab + 2 * rules.OMEGA_BLADE['item']])
        log.append(' 설명 뱅크 빈 곳 없음 → 오메가블레이드 설명을 같이 씀')
    try:
        import romanat
        ie_ = romanat.Sym()['ItemEffects']
    except (FileNotFoundError, KeyError):
        ie_ = None
    for k in need:
        it = ids[k]
        P.put(at + 7 * (it - 1), bytes(dd[at + 7 * 7:at + 7 * 8]))                          # 달맞이 돌 속성
        P.put(at + 7 * (it - 1), struct.pack('<H', rules.DIGIMENTAL_MART[1]))               # 값
        P.put(dtab + 2 * (it - 1), dp)
        if ie_:
            P.put(ie_ + 2 * (it - 1), bytes(P.d[ie_ + 2 * 7:ie_ + 2 * 8]))                   # 달맞이 돌 = EvoStoneEffect
    nil = rename_many(P, {ids[k]: v[1] for k, v in DM.items()})
    log.append('H-1 디지멘탈 이름 %d개(이름표 옮김, InitList %d), 새 칸 %s%s' % (
        len(DM), nil, ', '.join('%s=%d' % (k, ids[k]) for k in need), '' if ie_ else ' (효과 못 바꿈: 심볼 없음)'))
    try:
        log.append(' ' + add_to_mart(P, rules.DIGIMENTAL_MART[0], [ids[k] for k in need]))
    except Exception as ex:
        log.append(' 상점 추가 실패: %r' % (ex,))
    # 아머 진화
    done = []
    P.r.d = P.d
    by_from = {}
    for k, (it, nm, pairs) in DM.items():
        for frm, to in pairs:
            by_from.setdefault(frm, []).append((ids[k], to))
    for frm, lst in by_from.items():
        if frm not in N:
            continue
        ev = [tuple(e) for e in P.r.evos_attacks(N[frm])[0]]
        targets = {N[to] for _, to in lst if to in N}
        ev = [e for e in ev if not (e[0] == ITEM and e[-1] in targets) and not (frm == '아르마몬' and e[0] == LV and N.get('디그몬') == e[-1])]
        add = [(ITEM, it, N[to]) for it, to in lst if to in N]
        P.evos(N[frm], add + ev)
        P.r.d = P.d
        done.append('%s → %s' % (frm, '·'.join(to for _, to in lst if to in N)))
    log.append(' 아머 진화: ' + ', '.join(done))
    return log
