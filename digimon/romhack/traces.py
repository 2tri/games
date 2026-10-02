"""포켓몬 흔적·지명 조사 (롬을 읽기만 함)
  python3 traces.py [롬, 기본 work/myver.gbc]
    → work/traces.txt  : 걸린 곳마다 앞뒤 글 (롬 대사라서 저장소에 안 올림)
    → work/traces.json : 수만 (지명 표·종 이름·낱말별 개수)
찾는 것
  1. 지명 표 (GetLandmarkName 이 읽는 Landmarks, 항목 = x·y·이름 주소) — 지금 롬의 이름, 바이트 수, 같은 뱅크 빈 곳
  2. 포켓몬 종 이름 (금 한글판 251종) — 대사 덩어리(texts.py)와 이름표(도구·기술·트레이너 직업·종)
     지금 디지몬 이름 안에 들어 있는 경우(팬텀몬 안의 「팬텀」 등)는 뺌. 1글자 이름(뮤·삐)은 너무 흔해 안 셈
  3. 포켓몬 세계 낱말 (포켓·공박사·체육관 등) 과 지명이 대사에 나오는 수"""
import collections, json, os, re, struct, sys
import dmrom, krtext, texts, wild

LM_ASM = os.path.join(wild.KR, 'data/maps/landmarks.asm')
NOT_POKE = ['투구벌레', '시드라몬', '블루배지', '블루는 바닷빛', '블루카드', '팬텀배지', '럭키채널', '럭키- 채널', '럭키 채널', '파이어볼']   # 색·영어 낱말·배지 이름 (포켓몬 아님)
WORLD = ['포켓', '공박사', '오박사', '실프', '체육관', '관장', '배지', '사천왕', '챔피언', '포켓몬리그', '리그',
         '트레이너', '몬스터', '볼', '도감', '기술머신', '비전머신', '사파리', '라디오', '알프']


def kr_names(path, macro):
    return re.findall(r'^\s*%s\s+"([^"]*)"' % macro, open(path, encoding='utf-8').read(), re.M)


def landmark_rows():
    s = open(LM_ASM, encoding='utf-8').read()
    rows = [(int(x) + 8, int(y) + 16, lab) for x, y, lab in re.findall(r'^\s*landmark\s+(-?\d+),\s*(-?\d+),\s*(\w+)', s, re.M)]
    labels = dict(re.findall(r'^(\w+):\s*db\s+"([^"]*)@"', s, re.M))
    return rows, labels


def find_landmarks(d, rows):
    pat = b''.join(re.escape(bytes([x & 0xff, y & 0xff])) + b'..' for x, y, _ in rows[1:6])
    m = re.search(pat, d, re.S)
    t = m.start() - 4; bank = t // 0x4000
    out = []
    for k, (x, y, lab) in enumerate(rows):
        e = t + 4 * k
        assert d[e] == x & 0xff and d[e + 1] == y & 0xff, '지명 표 %d번 좌표 다름' % k
        a = dmrom.addr(bank, d[e + 2] | d[e + 3] << 8)
        end = d.index(0x50, a)
        out.append(dict(no=k, label=lab, addr=a, bytes=end - a + 1, name=krtext.decode(d, a)))
    return t, bank, out


def name_list(d, first_two, n):
    """'@'로 끝나는 이름이 n개 이어진 표 → (시작, 끝, 이름들)"""
    a = d.find(krtext.encode(first_two[0]) + b'\x50' + krtext.encode(first_two[1]) + b'\x50')
    if a < 0: return None
    i, out = a, []
    for _ in range(n):
        j = d.index(0x50, i); out.append(krtext.decode(d, i, j + 1)); i = j + 1
    return a, i, out


def ctx(s, i, n, w=14):
    return (s[max(0, i - w):i] + '[' + s[i:i + n] + ']' + s[i + n:i + n + w]).replace('<LINE>', '/').replace('<PARA>', '//').replace('<CONT>', '/')


def main(path):
    r = dmrom.Rom(path); d = bytes(r.d)
    texts.main(path)
    blocks = json.load(open(os.path.join(dmrom.WORK, 'texts.json')))
    log = []; res = {}

    # ── 1. 지명 표 ──
    rows, labels = landmark_rows()
    t, bank, lms = find_landmarks(d, rows)
    free = [f for f in r.free_runs(1) if f[0] == bank]
    res['지명표'] = dict(addr='%06X' % t, bank=bank, count=len(lms), bank_free=free[0][2] if free else 0,
                      names=[dict(no=l['no'], label=l['label'], name=l['name'], bytes=l['bytes'],
                                  same_as_gold=(l['name'] == labels.get(l['label']))) for l in lms])
    log.append('# 1. 지명 표 %06X (뱅크 %02X), %d항목, 뱅크 끝 빈 곳 %d바이트' % (t, bank, len(lms), res['지명표']['bank_free']))
    for l in lms:
        g = labels.get(l['label'])
        log.append('  %3d %-22s %-14s %2d바이트%s' % (l['no'], l['label'], l['name'], l['bytes'], '' if l['name'] == g else '  (금: %s)' % g))

    # ── 2. 포켓몬 종 이름 ──
    poke = kr_names(os.path.join(wild.KR, 'data/pokemon/names.asm'), 'dname')[:251]
    digi = sorted({r.name(n) for n in range(1, 252)} - {'-----'}, key=len, reverse=True)
    cands = sorted([p for p in poke if len(p) >= 2], key=len, reverse=True)

    def covered_by_digi(s, i, p):
        for dn in digi:
            k = dn.find(p)
            while k >= 0:
                if s[i - k:i - k + len(dn)] == dn: return dn
                k = dn.find(p, k + 1)
        return None

    lm_names = sorted({l['name'] for l in lms}, key=len, reverse=True)

    def covered(s, i, p, words, tag):
        for w in words:
            k = w.find(p)
            while k >= 0:
                if s[i - k:i - k + len(w)] == w: return tag + w
                k = w.find(p, k + 1)
        return None

    hits = collections.defaultdict(list); skipped = collections.Counter()

    def scan(s, kind, where):
        """문자열 s 에서 포켓몬 이름 찾기 (긴 이름 먼저, 디지몬 이름·지명·포켓몬 아닌 낱말·낱말 속은 뺌)"""
        used = [False] * len(s)
        for p in cands:
            i = s.find(p)
            while i >= 0:
                if not any(used[i:i + len(p)]):
                    dn = covered_by_digi(s, i, p) or covered(s, i, p, lm_names, '지명 ') or covered(s, i, p, NOT_POKE, '낱말 ')
                    if dn: skipped[(p, dn)] += 1
                    elif i > 0 and '가' <= s[i - 1] <= '힣':
                        skipped[(p, '낱말 속 ' + s[i - 1] + p)] += 1          # 찾아보·최고지·브이브이 같은 낱말 속
                    else:
                        hits[p].append((kind, where, ctx(s, i, len(p))))
                    for k in range(i, i + len(p)): used[k] = True
                i = s.find(p, i + 1)

    for b in blocks: scan(b['text'], '대사', '%06X' % b['addr'])
    spans = [(b['addr'], b['end'] + 1) for b in blocks] + [(r.names, r.names + 2510)]
    # 이름표
    tables = {}
    it = name_list(d, ['마스터볼', '하이퍼볼'], 256)
    if it: tables['도구 이름'] = it
    mv = name_list(d, ['막치기', '태권당수'], 251)
    if mv: tables['기술 이름'] = mv
    tc = name_list(d, ['체육관 관장', '체육관 관장'], 67)
    if tc: tables['트레이너 직업'] = tc
    for tname, (a, e, names) in tables.items():
        for nm in names: scan(nm, tname, nm)
        spans.append((a, e))
    # 지명 표 이름 자리
    spans += [(l['addr'], l['addr'] + l['bytes']) for l in lms]
    # 도감 글 (종마다, 지금 칸 이름과 같이)
    m = re.search(rb'\x21(..)\x78\x3d\x06\x00\x4f\x09\x09\x07\xe6\x01\xc6(.)\x47\x2a\x66\x6f\xc9', d, re.S)
    tab = dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')); b0 = m.group(2)[0]
    for sp in range(1, 252):
        ea = dmrom.addr(b0 + ((sp - 1) >> 7), d[tab + 2 * (sp - 1)] | d[tab + 2 * (sp - 1) + 1] << 8)
        i = d.index(0x50, ea) + 4; e = i                                  # 분류@ 키 몸무게(3) 뒤가 글
        while d[e] != 0x50: e += 2 if 1 <= d[e] <= 0x0b else 1
        nm = r.name(sp)
        scan(krtext.decode(d, i, e + 1).replace('<NEXT>', '/'), '도감 (빈 칸)' if nm == '-----' else '도감', '%d %s' % (sp, nm))
        spans.append((ea, e + 1))
    # 도감 글이 금 원문 그대로인 칸 (디스어셈블리 금판 도감과 비교)
    ptrs = re.findall(r'^\s*dw\s+(\w+)PokedexEntry', open(os.path.join(wild.KR, 'data/pokemon/dex_entry_pointers.asm'), encoding='utf-8').read(), re.M)
    files = dict(re.findall(r'^(\w+)PokedexEntry::\s*INCLUDE\s+"([^"]+)"', open(os.path.join(wild.KR, 'data/pokemon/dex_entries_gold.asm'), encoding='utf-8').read(), re.M))
    same_txt, same_kind = [], []
    for sp in range(1, 252):
        src = open(os.path.join(wild.KR, files[ptrs[sp - 1]]), encoding='utf-8').read()
        gkind = re.search(r'db\s+"([^"]*)@"', src).group(1)
        glines = [x.strip() for x in re.findall(r'^\s*(?:db|next|page)\s+"([^"]*)"', src, re.M)[1:]]
        glines = [x.rstrip('@').strip() for x in glines]
        ea = dmrom.addr(b0 + ((sp - 1) >> 7), d[tab + 2 * (sp - 1)] | d[tab + 2 * (sp - 1) + 1] << 8)
        i = d.index(0x50, ea) + 4; e = i
        while d[e] != 0x50: e += 2 if 1 <= d[e] <= 0x0b else 1
        cur = [x.strip() for x in re.split(r'<NEXT>|<PAGE>|\{4e\}', krtext.decode(d, i, e + 1))]
        nm = r.name(sp)
        if nm == '-----': continue
        if cur == glines: same_txt.append('%d %s' % (sp, nm))
        if krtext.decode(d, ea) == gkind: same_kind.append('%d %s(%s)' % (sp, nm, gkind))
    res['도감_금원문그대로'] = dict(글=same_txt, 분류=same_kind)
    # 도구 설명 (수퍼볼 설명으로 포인터 표 찾기, patch.py D-4 와 같은 방법)
    s4 = d.find(krtext.encode('디지몬을 잡기 위한 도구') + b'\x59')
    bk = s4 // 0x4000; dtab = d.find(struct.pack('<H', 0x4000 + s4 % 0x4000), bk * 0x4000, (bk + 1) * 0x4000) - 6
    for k in range(len(tables['도구 이름'][2]) if '도구 이름' in tables else 0):
        pa = d[dtab + 2 * k] | d[dtab + 2 * k + 1] << 8
        if not 0x4000 <= pa < 0x8000: continue
        da = dmrom.addr(bk, pa); e = da
        while e < len(d) and d[e] != 0x50: e += 2 if 1 <= d[e] <= 0x0b else 1
        if e - da > 80: continue
        scan(krtext.decode(d, da, e + 1).replace('<NEXT>', '/'), '도구 설명', tables['도구 이름'][2][k])
        spans.append((da, e + 1))
    spans.sort()
    outside = collections.defaultdict(list)
    import bisect
    starts = [a for a, _ in spans]
    for p in cands:
        enc = krtext.encode(p); i = d.find(enc)
        while i >= 0:
            k = bisect.bisect_right(starts, i) - 1
            if not (k >= 0 and spans[k][0] <= i < spans[k][1]):
                c = krtext.decode(d, max(0, i - 8), i + len(enc) + 8)
                prev = krtext.DEC2.get(bytes(d[i - 2:i]), '') if i >= 2 and 1 <= d[i - 2] <= 0x0b else ''
                if c.count('{') <= 2 and not ('가' <= prev <= '힣'):
                    outside[p].append('%06X 뱅크%02X %s' % (i, i // 0x4000, c))
            i = d.find(enc, i + 1)
    res['밖에서_걸린_바이트'] = {p: len(v) for p, v in outside.items()}
    res['이름표_범위'] = {k: ['%06X' % v[0], '%06X' % v[1]] for k, v in tables.items()}
    res['포켓몬이름'] = {p: dict(collections.Counter(h[0] for h in hits[p])) for p in sorted(hits, key=lambda p: -len(hits[p]))}
    res['분류별'] = dict(collections.Counter(h[0] for v in hits.values() for h in v))
    res['뺀것'] = {'%s(%s)' % k: v for k, v in skipped.items()}
    log.append('\n# 2. 포켓몬 종 이름 (대사 %d덩어리 + 이름표 %s + 도감 글 + 도구 설명) — %d종 걸림, 분류별 %s' % (len(blocks), ', '.join(tables), len(hits), res['분류별']))
    for p in sorted(hits, key=lambda p: -len(hits[p])):
        log.append('## %s  (%d)' % (p, len(hits[p])))
        for kind, a, c in hits[p]: log.append('  %s | %s | %s' % (kind, a, c))
    log.append('\n  디지몬 칸인데 도감 글이 금 원문 그대로: %d칸 — %s' % (len(same_txt), ', '.join(same_txt)))
    log.append('  디지몬 칸인데 도감 분류가 금 그대로: %d칸 — %s' % (len(same_kind), ', '.join(same_kind)))
    log.append('\n  뺀 것 (디지몬 이름·지명·낱말 속): %s' % dict(res['뺀것']))
    log.append('\n  대사·이름표 밖에서 같은 바이트가 나온 곳 (그림·자료일 수 있음, 눈으로 확인):')
    for p, v in outside.items():
        for x in v: log.append('    %s  %s' % (p, x))

    # ── 3. 낱말·지명이 대사에 나오는 수 ──
    def count(word):
        n = nb = 0
        for b in blocks:
            c = b['text'].count(word)
            if c: n += c; nb += 1
        return n, nb
    res['낱말'] = {w: dict(zip(('번', '덩어리'), count(w))) for w in WORLD}
    log.append('\n# 3. 포켓몬 세계 낱말 (대사 속 번 / 덩어리)')
    for w, v in res['낱말'].items(): log.append('  %-8s %4d / %4d' % (w, v['번'], v['덩어리']))
    res['지명_대사'] = {}
    log.append('\n# 4. 지명이 대사에 나오는 수 (번 / 덩어리). 「시티·마을·타운」 뺀 줄기만 나온 수는 따로')
    seen = set()
    for l in lms:
        nm = l['name']
        if nm in seen or nm in ('???',) or re.match(r'\d+번 도로', nm): continue
        seen.add(nm)
        n, nb = count(nm)
        stem = re.sub(r'(시티|마을|타운)$', '', nm); sn = 0
        if stem != nm:
            for b in blocks:
                s = b['text']; i = s.find(stem)
                while i >= 0:
                    if not s.startswith(nm, i): sn += 1
                    i = s.find(stem, i + 1)
        res['지명_대사'][nm] = dict(번=n, 덩어리=nb, 줄기만=sn)
        log.append('  %-14s %4d / %4d%s' % (nm, n, nb, ('   줄기 「%s」만 %d' % (stem, sn)) if stem != nm else ''))
    rn = sum(len(re.findall(r'\d+번 ?도로', b['text'])) for b in blocks)
    res['N번도로_대사'] = rn
    log.append('  N번 도로 (모두) %d' % rn)

    open(os.path.join(dmrom.WORK, 'traces.txt'), 'w', encoding='utf-8').write('\n'.join(log) + '\n')
    json.dump(res, open(os.path.join(dmrom.WORK, 'traces.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('지명 표 %06X %d항목, 포켓몬 이름 %d종 %d곳 → work/traces.txt' % (t, len(lms), len(hits), sum(len(v) for v in hits.values())))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(dmrom.WORK, 'myver.gbc'))
