"""검수 보고서 — 고친 롬(myver.gbc)을 읽어 100줄 이내로 요약·규칙 검사 (자문자에게 그대로 붙임)
  python3 check.py                 요약 + 규칙 R1~R14
  python3 check.py --full evo      + 진화 표 전체 (칸 | 이름 | 순서 | 종류 | 조건 | 결과)
  python3 check.py --full party    + 관장·사천왕·챔피언·라이벌·레드 파티
  python3 check.py --full wild     + 야생표 지역별 종·레벨
줄 앞 표시: [X] 규칙 위반 · [OK] 통과 · [?] 확인 불가. 규칙은 계획서 v0.4 기준."""
import argparse, collections, json, os, re, struct, sys, zlib
import dmrom, krtext, encounters as E, remap, texts as T
import rules as RU

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
KR = E.KR
ORIG = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(KR, 'data/pokemon/names.asm')) if 'dname' in l]
GROUPS = re.findall(r'dw (\w+)Group', open(os.path.join(KR, 'data/trainers/party_pointers.asm')).read())
JOHTO = [('Falkner', '버드라몬'), ('Bugsy', '캅테리몬'), ('Whitney', '니드몬'), ('Morty', '가트몬'), ('Chuck', '그레이몬'),
         ('Jasmine', '가루몬|워가루몬'), ('Pryce', '쥬드몬'), ('Clair', '홀리엔젤몬')]
BOSS = ['Falkner', 'Bugsy', 'Whitney', 'Morty', 'Chuck', 'Jasmine', 'Pryce', 'Clair', 'Will', 'Koga', 'Bruno', 'Karen', 'Champion',
        'Brock', 'Misty', 'LtSurge', 'Erika', 'Janine', 'Sabrina', 'Blaine', 'Blue', 'Red', 'Rival1', 'Rival2']
EARLY = ['29번 도로', '30번 도로', '31번 도로', '32번 도로', '너도밤나무 숲', '모다피의 탑']
ORIG_MOVES = [tuple(int(x) for x in (m.group(1), m.group(2))) for m in
              re.finditer(r'^\s*move \w+,\s*\w+,\s*(\d+),\s*\w+,\s*\d+,\s*(\d+),', open(os.path.join(KR, 'data/moves/moves.asm')).read(), re.M)]
EVK = {1: '레벨', 2: '도구', 3: '통신', 4: '친밀도', 5: '능력치', 6: '유대 높음', 7: '유대 낮음', 8: '자기 문장', 9: '암흑', 10: '아무 문장'}
LEVELED = {1, 5, 6, 7, 8, 9, 10}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import icons as _ICN
G_ICONS = {v[1] for v in _ICN.CATS.values()}                  # G단계 아이콘 10종이 쓰는 금 아이콘 번호


class Ctx:
    def __init__(self, path):
        self.path = path; self.r = dmrom.Rom(path); self.d = bytes(self.r.d)
        self.base = dmrom.Rom(dmrom.default_rom())
        self.name = self.r.name
        self.pk = {n for n in range(1, 252) if self.name(n) == ORIG[n - 1]}
        G = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'grades.json'))).items()}
        SL = json.load(open(os.path.join(HERE, 'slots.json')))
        self.slots = {m['name']: m for m in SL['mons']}
        self.installed = {n for n in range(1, 252) if self.name(n) in self.slots}
        self.grade = {}
        for n in range(1, 252):
            nm = self.name(n)
            if nm in self.slots: self.grade[n] = self.slots[nm]['grade']
            elif n in G and G[n]['name'] == nm and G[n]['grade']: self.grade[n] = G[n]['grade']
        self.grade.update({161: '유년기Ⅱ', 212: '완전체', 217: '완전체'})
        self.palswap = {v[1]: nm for nm, v in RU.PALSWAP.items() if self.name(v[1]) == nm}     # F단계 색만 바꾼 종
        self.grade.update({n: RU.PALSWAP[nm][2] for n, nm in self.palswap.items()})
        self.keep = set(json.load(open(os.path.join(HERE, 'order', 'keep.json')))) | self.installed | set(self.palswap)
        if self.name(RU.UNOWN[0]) == RU.UNOWN[1]: self.keep.add(RU.UNOWN[0])      # 안농 칸 → 디지문자 (D단계)
        self.empty = {n for n in range(1, 252) if self.name(n) == RU.EMPTY_NAME}       # D-7 잠자는 칸 정리
        self.drop = {n for n in range(1, 252) if n not in self.pk and n not in self.keep and n not in self.empty}
        self.sites = E.find_all(self.base)
        for s in self.sites: s['cur'] = self.d[s['addr']]
        self.trainers = self.r.trainers(len(GROUPS))
        il = self.d.find(krtext.encode('마스터볼') + b'\x50' + krtext.encode('하이퍼볼') + b'\x50'); self.items = []
        if il >= 0:                                                   # 지금 롬의 도구 이름표 (D단계에서 바뀐 이름 반영)
            for _ in range(256):
                j = self.d.index(0x50, il); self.items.append(krtext.decode(self.d, il, j)); il = j + 1

    def evos(self, n):
        return [e for e in self.r.evos_attacks(n)[0] if 1 <= e[0] <= 10]

    def cond(self, e):
        t = e[0]
        if t in LEVELED: return 'Lv%d' % e[1] + (' (공격%s방어)' % {1: '>', 2: '<', 3: '='}.get(e[2], '?') if t == 5 else '')
        if t in (2, 3):
            if t == 3 and e[1] == 0xff: return '—'
            return '「%s」' % (self.items[e[1] - 1] if 0 < e[1] <= len(self.items) else '도구 %d' % e[1])
        if t == 4: return '220↑' + {1: '', 2: ' 낮', 3: ' 밤'}.get(e[1], '')
        return '?'


def moves_table(c):
    d = c.d; a = d.find(bytes([1, 0, 40, 0, 255, 35, 0, 2, 0, 50, 1, 255, 25, 0]))
    n0 = d.find(krtext.encode('막치기') + b'\x50' + krtext.encode('태권당수') + b'\x50')
    names = []
    if n0 >= 0:
        p = n0
        for _ in range(251):
            j = d.index(0x50, p); names.append(krtext.decode(d, p, j)); p = j + 1
    return a, names


def engine_dark(c):
    """진화 확장 코드에서 종류 9(암흑) 갈래를 찾아 친밀도(유대) 비교가 있는지"""
    d = c.d
    m = re.search(rb'\xfe\x06\x28(.)\xfe\x07\x28(.)\xfe\x08\x28(.)\xfe\x09\x28(.)', d, re.S)
    if not m: return None, '종류 6~9 분기 모양을 못 찾음'
    j = m.start() + 14; dark = j + 2 + (m.group(4)[0] - 256 if m.group(4)[0] > 127 else m.group(4)[0])
    h = re.search(rb'\xfa(..)\xfe\xdc\xda', d[:0x8000] if False else d, re.S)    # 금 친밀도 진화: ld a,[wTempMonHappiness] / cp 220 / jp c
    hap = d[h.start() + 1:h.start() + 3] if h else None
    blk = d[dark:dark + 24]
    if hap is None: return None, '친밀도 변수 주소를 못 찾음'
    return (hap in blk), '%05X' % dark


def summary(c, out):
    ips = os.path.join(os.path.dirname(c.path), 'myver.ips')
    out.append('롬: %s  CRC32 %08X  IPS 크기 %s B' % (os.path.basename(c.path), zlib.crc32(c.d), os.path.getsize(ips) if os.path.exists(ips) else '?'))
    # 잠자는 칸: 어디에도 안 나오고(야생·트레이너·이벤트·스타팅) 얻을 수 있는 종에서 진화로도 못 가는 칸
    seen = {s['cur'] for s in c.sites if s['kind'] != '트레이너'} | {sp for t in c.trainers for _, sp, _ in t['mons']}   # 트레이너는 지금 파티(옮긴 무리 포함)
    stack = list({s['cur'] for s in c.sites if s['kind'] != '트레이너'}); got = set(stack)
    while stack:
        n = stack.pop()
        for e in c.evos(n):
            if e[-1] not in got: got.add(e[-1]); stack.append(e[-1])
    sleep = [n for n in range(1, 252) if n not in seen and n not in got]
    dig = 251 - len(c.pk) - len(c.empty)
    out.append('칸: 디지몬 %d / 포켓몬 %d / 빈 칸(%s) %d / 잠자는 칸 %d (그중 포켓몬 %d)' % (dig, len(c.pk), RU.EMPTY_NAME, len(c.empty), len(sleep), sum(n in c.pk for n in sleep)))
    wk = collections.OrderedDict((k, set()) for k in ('풀숲', '물', '낚시', '박치기 나무', '대량발생 풀숲', '대량발생 물', '벌레잡기 대회'))
    for s in c.sites:
        if s['kind'] in wk and s['cur'] in c.pk: wk[s['kind']].add(s['cur'])
    allw = set().union(*wk.values())
    out.append('야생표에 남은 포켓몬 종: %d  (%s)%s' % (len(allw), ' / '.join('%s %d' % (k, len(v)) for k, v in wk.items()),
               '  — %s' % ', '.join(c.name(n) for n in sorted(allw)) if allw else ''))
    tp = [t for t in c.trainers if any(sp in c.pk for _, sp, _ in t['mons'])]
    tsp = {sp for t in tp for _, sp, _ in t['mons'] if sp in c.pk}
    boss = sorted({t['name'] for t in tp if GROUPS[t['group']] in BOSS})
    out.append('트레이너 파티에 남은 포켓몬: %d명 / %d종  (관장·사천왕·챔피언·라이벌·레드 중: %s)' % (len(tp), len(tsp), ', '.join(boss) or '없음'))
    ev = [(n, e[-1]) for n in range(1, 252) if n not in c.pk for e in c.evos(n) if e[-1] in c.pk]
    out.append('진화 결과가 포켓몬인 항목: %d%s' % (len(ev), '  — ' + ', '.join('%s→%s' % (c.name(a), c.name(b)) for a, b in ev) if ev else ''))
    idx = T.refs_index(c.d); cnt = collections.Counter()
    for (bank, ptr), rf in idx.items():
        p = dmrom.addr(bank, ptr)
        if p >= len(c.d): continue
        t = T.read_text(c.d, p)
        if t and t[1] >= 2:
            for w in ('포켓몬', '몬스터볼', '로켓단', '오박사'): cnt[w] += t[2].count(w)
    out.append('대사 속 「포켓몬」「몬스터볼」「로켓단」「오박사」 남은 수: %d / %d / %d / %d' % tuple(cnt[w] for w in ('포켓몬', '몬스터볼', '로켓단', '오박사')))
    allc = [c.d.count(krtext.encode(w)) for w in ('포켓몬', '몬스터볼', '로켓단', '오박사')]
    out.append('롬 전체(이름표·메뉴 포함) 같은 낱말 남은 수: %d / %d / %d / %d' % tuple(allc))


def rules(c, out):
    def rep(code, bad, ok_msg, fmt, note=''):
        if bad:
            out.append('[X] %s %d건%s' % (code, len(bad), note))
            cap = 10 if len(bad) <= 10 else 6
            for b in bad[:cap]: out.append('     ' + fmt(b))
            if len(bad) > cap: out.append('     … 외 %d건 (--full evo 로 전체)' % (len(bad) - cap) if code in ('R1', 'R2', 'R3') else '     … 외 %d건' % (len(bad) - cap))
        else: out.append('[OK] %s %s' % (code, ok_msg))
    dig = sorted(c.keep)                    # 남길 종 + 설치된 새 종 (뺄 종·포켓몬 칸의 진화는 게임에서 안 보이므로 빼고 봄)
    # R1 · R2
    r1, r2, r2x, unk = [], [], [], set()
    for n in dig:
        for e in c.evos(n):
            g = c.grade.get(e[-1])
            if g is None: unk.add(e[-1]); continue
            if e[0] not in LEVELED: continue
            lv = e[1]; lo, hi = RU.CHAMPION_LV
            if g == '완전체' and lv < RU.COMPLETE_LV: r1.append((n, e, '완전체인데 %d 미만' % RU.COMPLETE_LV))
            if g == '궁극체' and lv < RU.ULTIMATE_LV: r1.append((n, e, '궁극체인데 %d 미만' % RU.ULTIMATE_LV))
            if g == '성숙기' and not lo <= lv <= hi:
                (r2x if c.name(n) in RU.R2_EXCEPT else r2).append((n, e, '%d~%d 밖' % (lo, hi)))
    f = lambda b: '%s %s %s → %s (%s)' % (c.name(b[0]), EVK[b[1][0]], c.cond(b[1]), c.name(b[1][-1]), b[2])
    rep('R1', r1, '완전체 ≥%d, 궁극체 ≥%d (남길 종 %d)' % (RU.COMPLETE_LV, RU.ULTIMATE_LV, len(dig)), f)
    rep('R2', r2, '성숙기 진화 Lv%d~%d' % RU.CHAMPION_LV, f)
    for b in r2x: out.append('     (예외 인정 rules.R2_EXCEPT 초반 벌레 줄: %s)' % f(b))
    # R3 순서
    r3 = []
    for n in dig:
        ks = [e[0] for e in c.evos(n)]
        for seq, nm in (((8, 9, 10), '자기 문장 → 암흑 → 아무 문장'), ((6, 7, 1), '유대 높음 → 유대 낮음 → 레벨')):
            pos = [ks.index(k) for k in seq if k in ks]
            if pos != sorted(pos): r3.append((n, nm, ' · '.join(EVK[k] for k in ks)))
    rep('R3', r3, '진화 목록 순서 (남길 종 %d)' % len(dig), lambda b: '%s: %s 순서가 아님 (지금 %s)' % (c.name(b[0]), b[1], b[2]))
    # R4
    ok, where = engine_dark(c)
    if ok is None: out.append('[?] R4 %s' % where)
    elif ok: out.append('[OK] R4 종류 9(암흑) 갈래에 친밀도 비교 있음 (%s)' % where)
    else: out.append('[X] R4 종류 9(암흑) 갈래에 친밀도(유대 낮음) 비교가 없음 (코드 %s)' % where)
    # R5
    r5, r5q = [], []
    want = lambda n: RU.CATCH_BY_NAME.get(c.name(n), RU.CATCH_BY_GRADE.get(c.grade.get(n)))
    for n in dig:
        g = c.grade.get(n); cr = c.r.d[c.r.bs + 0x20 * (n - 1) + 9]
        if want(n) is None: r5q.append(n); continue
        if cr != want(n): r5.append((n, g, cr))
    rep('R5', r5, '포획률 %d종 전부 단계표와 일치 (남길 종 기준, 이름 지정 %d종 포함)' % (len(dig) - len(r5q), sum(c.name(n) in RU.CATCH_BY_NAME for n in dig)),
        lambda b: '%s (%s) 포획률 %d → %d 이어야' % (c.name(b[0]), b[1], b[2], want(b[0])),
        note=' (남길 종 %d 중, 단계별 기대값과 다름)' % len(dig))
    if r5q: out.append('[?] R5 단계를 몰라 판정 못 함 %d종: %s' % (len(r5q), ', '.join('%s(%s)' % (c.name(n), c.grade.get(n, '?')) for n in r5q)))
    # R6
    r6 = sorted({(s['where'], s['lv'], c.name(s['cur'])) for s in c.sites if s['kind'] in remap.WILD and any(s['where'].startswith(p) for p in EARLY)
                 and c.grade.get(s['cur']) in ('완전체', '궁극체')})
    rep('R6', r6, '초반 지역 야생에 완전체 이상 없음', lambda b: '%s Lv%d %s' % b)
    # R7
    r7 = []
    for g, want in JOHTO:
        t = next(t for t in c.trainers if GROUPS[t['group']] == g)
        last = c.name(t['mons'][-1][1])
        if last not in want.split('|'): r7.append((t['name'], last, want))
    rep('R7', r7, '성도 관장 8명 마지막 = 문장 주인 파트너', lambda b: '%s: 마지막 %s (→ %s 이어야)' % b)
    # R8
    a, mnames = moves_table(c)
    if a < 0: out.append('[?] R8 기술 표를 못 찾음')
    else:
        cur = [(c.d[a + 7 * i + 2], c.d[a + 7 * i + 5]) for i in range(len(ORIG_MOVES))]
        diff = [i for i in range(len(ORIG_MOVES)) if cur[i] != ORIG_MOVES[i]]
        r8 = [(mnames[i] if i < len(mnames) else str(i + 1),) + cur[i] + ORIG_MOVES[i] for i in diff if cur[i][0] > 120 or cur[i][1] > 40]
        rep('R8', r8, '원작 금과 위력·PP가 다른 기술 %d개 모두 위력 ≤120, PP ≤40 (원작 그대로인 기술은 안 봄)' % len(diff),
            lambda b: '%s 위력 %d PP %d (원작 %d / %d)' % b)
    # R9
    r9 = []
    for n in range(1, 252):
        s = c.name(n); e = c.d[c.r.names + 10 * (n - 1):c.r.names + 10 * n]
        if not s.strip() or '{' in s or len(s) > 5 or e[0] == 0x50: r9.append((n, s))
    rep('R9', r9, '이름 5글자 이하, 빈 이름 없음 (251칸)', lambda b: '%d번 「%s」' % b)
    # R10
    r10 = collections.Counter()
    for n in dig:
        for e in c.evos(n):
            if e[-1] in c.drop: r10[('진화', c.name(n) + '→' + c.name(e[-1]))] += 1
    for s in c.sites:
        if s['cur'] in c.empty:                                       # 빈 칸(-----)을 가리키는 야생·트레이너·이벤트
            k = '야생' if s['kind'] in remap.WILD else ('트레이너' if s['kind'] == '트레이너' else '이벤트')
            r10[(k, '빈 칸 %d번(%s)' % (s['cur'], s['where']))] += 1
        if s['cur'] in c.drop:
            k = '야생' if s['kind'] in remap.WILD else ('트레이너' if s['kind'] == '트레이너' else '이벤트')
            r10[(k, c.name(s['cur']))] += 1
    rep('R10', sorted(r10.items()), '진화 결과·야생·트레이너·이벤트가 뺄 종·빈 칸을 안 가리킴',
        lambda b: '%s: %s%s' % (b[0][0], b[0][1], '' if b[1] == 1 else ' ×%d' % b[1]))
    # R11
    pics = collections.defaultdict(list)
    for n in range(1, 252): pics[bytes(c.d[c.r.pics + 6 * (n - 1):c.r.pics + 6 * n])].append(n)
    r11 = [ns for ns in pics.values() if len(ns) > 1 and len({bytes(c.d[c.r.pal + 8 * n:c.r.pal + 8 * n + 8]) for n in ns}) < len(ns)]
    shared = sum(len(ns) > 1 for ns in pics.values())
    rep('R11', r11, '같은 그림을 쓰는 칸 묶음 %d개, 팔레트 모두 다름' % shared, lambda b: '같은 그림·같은 팔레트: ' + ', '.join(c.name(n) for n in b))
    # R12
    new = {161: 'koromon', 212: 'metalgreymon', 217: 'weregarurumon'}
    new.update({n: c.slots[c.name(n)]['id'] for n in c.installed})
    b = c.base.d; r12 = []
    for n, did in sorted(new.items()):
        lack = []
        if c.name(n) == ORIG[n - 1]: lack.append('이름')
        if bytes(c.d[c.r.bs + 0x20 * (n - 1) + 1:c.r.bs + 0x20 * (n - 1) + 11]) == bytes(b[c.r.bs + 0x20 * (n - 1) + 1:c.r.bs + 0x20 * (n - 1) + 11]): lack.append('능력치')
        if not c.r.evos_attacks(n)[1]: lack.append('기술')
        if not os.path.exists(os.path.join(WEB, 'art', did + '-f.png')): lack.append('그림(물음표 알)')
        elif bytes(c.d[c.r.pics + 6 * (n - 1):c.r.pics + 6 * n]) == bytes(b[c.r.pics + 6 * (n - 1):c.r.pics + 6 * n]): lack.append('그림')
        dexp = re.search(rb'\x21(..)\x78\x3d\x06\x00\x4f\x09\x09\x07\xe6\x01\xc6(.)\x47\x2a\x66\x6f\xc9', c.d, re.S)
        tab = dmrom.addr(dexp.start() // 0x4000, int.from_bytes(dexp.group(1), 'little'))
        ent = lambda D: dmrom.addr(dexp.group(2)[0] + ((n - 1) >> 7), D[tab + 2 * (n - 1)] | D[tab + 2 * (n - 1) + 1] << 8)
        if bytes(c.d[ent(c.d):ent(c.d) + 24]) == bytes(b[ent(b):ent(b) + 24]): lack.append('도감')
        m = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', c.d, re.S)
        ia = dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')) + n - 1
        if c.d[ia] not in G_ICONS: lack.append('아이콘')                # G단계 10종 중 하나
        m = re.search(rb'\x3e(.)\xd7\x21(..)\x09\x09\x09\x09\x09\x09\x5e\x23\x56\x23\x2a', c.d, re.S)
        ca = dmrom.addr(m.group(1)[0], int.from_bytes(m.group(2), 'little')) + 6 * (n - 1)
        if bytes(c.d[ca:ca + 6]) == bytes(b[ca:ca + 6]): lack.append('울음')
        if lack: r12.append((c.name(n), lack))
    waiting = [m['name'] for m in c.slots.values() if m['name'] not in {c.name(n) for n in c.installed}]
    rep('R12', r12, '설치된 새 종 %d개 7항목(이름·능력치·진화·그림·도감·아이콘·울음) 다 있음' % len(new), lambda b: '%s: %s 없음/원래 것' % (b[0], '·'.join(b[1])))
    out.append('     (그림 대기라 아직 안 넣은 새 종 %d: %s)' % (len(waiting), ', '.join(waiting)))
    # R13 트레이너 파티의 궁극체: 사천왕·챔피언·레드·라이벌 마지막만
    r13, gi = [], collections.Counter()
    for t in c.trainers:
        g = GROUPS[t['group']]; i = gi[g]; gi[g] += 1
        if g in RU.ULTIMATE_OK or (g == RU.RIVAL_FINAL[0] and i >= RU.RIVAL_FINAL[1]): continue
        for lv, sp, _ in t['mons']:
            if c.grade.get(sp) == '궁극체': r13.append((g, i + 1, t['name'], c.name(sp), lv))
    rep('R13', r13, '궁극체는 사천왕·챔피언·레드·라이벌 마지막(%s %d번째 이후) 파티에만' % (RU.RIVAL_FINAL[0], RU.RIVAL_FINAL[1] + 1),
        lambda b: '%s (%d) %s: %s Lv%d' % b)
    # R14 포켓몬 칸(잠자는 칸 포함)의 진화 결과가 디지몬 칸을 가리키지 않음
    r14 = [(n, e) for n in sorted(c.pk) for e in c.evos(n) if e[-1] not in c.pk]
    rep('R14', r14, '포켓몬 칸 %d개의 진화 결과가 디지몬 칸을 안 가리킴' % len(c.pk),
        lambda b: '%s %s %s → %s' % (c.name(b[0]), EVK[b[1][0]], c.cond(b[1]), c.name(b[1][-1])))
    # R15 남길 종 메뉴 아이콘이 G단계 10종 안에 있음 (포켓몬 아이콘 0)
    m = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', c.d, re.S)
    ia0 = dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
    r15 = [(c.name(n), c.d[ia0 + n - 1]) for n in dig if c.d[ia0 + n - 1] not in G_ICONS]
    rep('R15', r15, '남길 종 %d 메뉴 아이콘이 모두 10종(유년기·공룡·짐승·새·벌레·식물·바다·기계·천사·악마) 안에 있음' % len(dig),
        lambda b: '%s: 아이콘 %d' % b)
    # R16 E단계 출현 연결 (rules.PLACE_SWAP·PLACE_ADD): 넣을 종이 그 지역 야생에 있고, 없앨 종이 그 지역에 없음
    N = {c.name(n): n for n in range(1, 252)}; r16 = []
    wild = [s for s in c.sites if s['kind'] in remap.WILD]
    for frm, to, area in RU.PLACE_SWAP:
        if frm not in N: continue
        left = [s['where'] for s in wild if s['cur'] == N[frm] and (not area or s['where'].startswith(area))]
        if left: r16.append(('%s 가 %s 에 남음' % (frm, area or '야생'), len(left)))
    babies = {n for n, g in c.grade.items() if g.startswith('유년기')}
    baby_of = {e[-1]: b for b in babies for e in c.evos(b) if e[0] == 1 and e[-1] not in babies}
    for nm, kd, area, slots, (lo, hi), cond in RU.PLACE_ADD:
        if nm not in N: continue
        here = [s for s in wild if s['kind'] == kd and s['where'].startswith(area) and s['cur'] == N[nm]]
        # 초반 야생 유년기(R17)로 그 종의 유년기가 된 Lv 낮은 칸도 넣은 것으로 침
        here_b = [s for s in wild if s['kind'] == kd and s['where'].startswith(area) and s['cur'] == baby_of.get(N[nm]) and c.d[s['addr'] - 1] <= RU.BABY_WILD_LV]
        bad_lv = [s for s in here if not lo <= c.d[s['addr'] - 1] <= hi]
        if not here and not here_b: r16.append(('%s 가 %s %s 에 없음' % (nm, area, kd), 0))
        elif bad_lv: r16.append(('%s 의 %s 레벨이 %d~%d 밖' % (nm, area, lo, hi), len(bad_lv)))
    rep('R16', r16, '출현 연결표 %d줄 (없앨 종 %d, 넣을 곳 %d) 모두 맞음' % (len(RU.PLACE_SWAP) + len(RU.PLACE_ADD), len(RU.PLACE_SWAP), len(RU.PLACE_ADD)),
        lambda b: '%s (%d곳)' % b)
    # R17 초반 야생 유년기 (rules.BABY_WILD_LV, 사용자 2026-10-03): 그 레벨 이하 야생 칸에, 유년기가 롬에 있는 성장기가 없음
    r17 = collections.Counter(c.name(s['cur']) for s in wild if s['cur'] in baby_of and c.d[s['addr'] - 1] <= RU.BABY_WILD_LV)
    rep('R17', sorted(r17.items()), 'Lv%d 이하 야생에 유년기가 있는 성장기 없음 (유년기 %d종)' % (RU.BABY_WILD_LV, len(babies)), lambda b: '%s (%d곳)' % b)
    # R19 스타팅 공 3개: 스크립트의 그림·울음·이름·주는 종 네 바이트가 모두 같은 종이고, 유년기 스타팅(rules.BABY_STARTERS, 칸이 있을 때) 또는 성장기
    r19 = []; NB = {c.base.name(n): n for n in range(1, 252)}; base = bytes(c.base.d)
    for old, rk in (('길몬', '아구몬'), ('레나몬', '파피몬'), ('테리어몬', '브이몬')):
        o = NB[old]; a = re.search(bytes([0x56, o, 0x84, o, 0x00]), base).start(); seg = base[a:a + 80]
        ks = (1, 3, seg.index(bytes([0x40, o])) + 1, seg.index(bytes([0x2d, o, 5])) + 1)
        got = [c.d[a + k] for k in ks]
        bb = next((b for r_, b, _ in RU.BABY_STARTERS if r_ == rk and b in N), rk)
        if len(set(got)) != 1 or got[0] != N[bb]: r19.append((old, '%s 이어야 하는데 %s' % (bb, '·'.join(c.name(g) for g in got))))
    rep('R19', r19, '스타팅 공 3개 = %s (그림·울음·이름·주는 종 모두 같음)' % '·'.join(next((b for r_, b, _ in RU.BABY_STARTERS if r_ == rk and b in N), rk) for rk in ('아구몬', '파피몬', '브이몬')),
        lambda b: '%s 공: %s' % b)
    # R20 파워디지몬(02) 이후 디지몬 이름이 롬 이름표에 없음 (rules.LATE_SERIES·LATE_EXTRA, series.json 분류, 사용자 2026-10-05)
    SER = {v['name']: v['series'] for v in json.load(open(os.path.join(HERE, 'series.json'))).values()}
    r20 = [(n, c.name(n)) for n in range(1, 252) if SER.get(c.name(n)) in RU.LATE_SERIES or c.name(n) in RU.LATE_EXTRA]
    rep('R20', r20, '파워디지몬 이후 디지몬 이름 0 (테이머즈·그 뒤 작품·애니 미등장 %d종 분류)' % sum(1 for v in SER.values() if v in RU.LATE_SERIES),
        lambda b: '%d %s' % b)
    # R18 넣은 노래 (rules.MUSIC): 금 음악 엔진처럼 따라가서 모르는 명령·시간 0 무한 반복·음 길이 넘침(255프레임) 없고, 네 채널 한 바퀴 프레임이 같음
    r18 = []
    for nm, ids in RU.MUSIC.items():
        bad, fr, lp = music_sim(c.d, ids[0])
        if bad: r18.append((nm, bad))
        elif max(fr) - min(fr) > 2: r18.append((nm, '채널 길이 다름 %s' % fr))
        elif max(lp) - min(lp) > 2: r18.append((nm, '반복 구간 길이 다름 %s' % lp))
    rep('R18', r18, '넣은 노래 %d곡 엔진 시뮬레이션 문제 없음 (음 길이 넘침·채널 어긋남 없음)' % len(RU.MUSIC), lambda b: '%s: %s' % b)


def music_sim(d, mid):
    """금 음악 엔진(audio/engine.asm)처럼 곡 하나를 한 바퀴 따라감 → (문제 또는 None, 채널별 프레임 수, 채널별 반복 구간 프레임 수)
    음 길이 프레임 = (칸 × 템포 + 나머지) 의 위 바이트, 16비트 곱이라 템포×칸이 65535 를 넘으면 돌아감"""
    m = re.search(rb'\x21(..)\x19\x19\x19\x2a\xea', d, re.S)
    mtab = dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
    bank = d[mtab + 3 * mid]; h = dmrom.addr(bank, d[mtab + 3 * mid + 1] | d[mtab + 3 * mid + 2] << 8)
    n = (d[h] >> 6) + 1; frames = []; looped = []; tempo = 256
    for k in range(n):
        cid = d[h + 3 * k] & 7; a = d[h + 3 * k + 1] | d[h + 3 * k + 2] << 8
        speed = 1; frac = 0; total = 0; loops = {}; seen = set(); at = {}
        for _ in range(100000):
            at.setdefault(a, total)
            b = d[dmrom.addr(bank, a)]
            if b < 0xd0:
                units = ((b & 15) + 1) * speed
                if units > 255: return '칸×속도 255 넘음', [], []
                prod = tempo * units + frac
                if prod > 0xffff: return '음 길이 넘침 (템포 %d × %d칸)' % (tempo, units), [], []
                total += prod >> 8; frac = prod & 0xff; a += 1
            elif b <= 0xd7: a += 1
            elif b == 0xd8: speed = d[dmrom.addr(bank, a + 1)]; a += 2 if cid == 3 else 3
            elif b == 0xda: tempo = d[dmrom.addr(bank, a + 1)] << 8 | d[dmrom.addr(bank, a + 2)]; a += 3
            elif b in (0xdb, 0xe5, 0xe3): a += 2
            elif b == 0xe1: a += 3                                                     # vibrato
            elif b == 0xfd:
                cnt = d[dmrom.addr(bank, a + 1)]; tgt = d[dmrom.addr(bank, a + 2)] | d[dmrom.addr(bank, a + 3)] << 8
                if cnt == 0:
                    if total == 0 or total == at.get(tgt, 0): return '시간 0 무한 반복', [], []
                    if tgt not in at: return '반복 위치가 음 사이가 아님', [], []
                    looped.append(total - at[tgt]); break
                loops[a] = loops.get(a, 0) + 1
                if loops[a] < cnt: a = tgt
                else: loops[a] = 0; a += 4
            elif b == 0xff: looped.append(0); break
            else: return '모르는 명령 %02X' % b, [], []
        else: return '끝나지 않음', [], []
        frames.append(total)
    return None, frames, looped


def full_evo(c, out):
    out.append(''); out.append('## 진화 표 (칸 | 이름 | 순서 | 종류 | 조건 | 결과)')
    out.append('| 칸 | 이름 | 순서 | 종류 | 조건 | 결과 |'); out.append('|---|---|---|---|---|---|')
    for n in range(1, 252):
        ev = c.evos(n)
        tag = ' (포켓몬)' if n in c.pk else ''
        for i, e in enumerate(ev):
            g = c.grade.get(e[-1]) or ('포켓몬' if e[-1] in c.pk else '?')
            out.append('| %d | %s%s | %d | %s | %s | %s (%s) |' % (n, c.name(n), tag, i + 1, EVK[e[0]], c.cond(e), c.name(e[-1]), g))


def full_party(c, out):
    out.append(''); out.append('## 관장·사천왕·챔피언·라이벌·레드 파티')
    for g in BOSS:
        for t in c.trainers:
            if GROUPS[t['group']] == g:
                out.append('- %s %s: %s' % (g, t['name'], ', '.join('%s Lv%d' % (c.name(sp), lv) for lv, sp, _ in t['mons'])))


def full_wild(c, out):
    out.append(''); out.append('## 야생표 (지역 | 종류 | 종 Lv)')
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in c.sites:
        if s['kind'] in remap.WILD: by[(s['where'].split(' ')[0] if s['kind'] in ('풀숲', '대량발생 풀숲') else s['where'], s['kind'])][c.name(s['cur'])].append(s['lv'])
    for (w, k), sp in sorted(by.items()):
        out.append('- %s (%s): %s' % (w, k, ', '.join('%s %d~%d' % (n, min(v), max(v)) for n, v in sorted(sp.items()))))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('rom', nargs='?', default=os.path.join(dmrom.WORK, 'myver.gbc'))
    ap.add_argument('--full', nargs='*', choices=['evo', 'party', 'wild'])
    a = ap.parse_args()
    c = Ctx(a.rom); out = []
    summary(c, out); out.append(''); rules(c, out)
    for k in (a.full or []): {'evo': full_evo, 'party': full_party, 'wild': full_wild}[k](c, out)
    print('\n'.join(out))
