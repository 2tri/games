#!/usr/bin/env python3
"""이벤트 종 번호·그림 형식 찾기 (롬은 읽기만 한다) → hg_scan_out.txt 를 설계자에게
사용:   python hg_scan.py "<디지골드 롬.nds>"
1) 스크립트(a/0/1/2)에서 고정 전투·선물·알·교환에 쓰이는 포켓몬 번호가 나오는 자리와 앞뒤 바이트 → HG3 이벤트 바꾸기용
2) HG4 2단계(아이콘·따라다니기 그림·트레이너 그림)에 필요한 형식 조사:
   - 아이콘 NARC(a/0/2/0): 파일 종류·크기, 첫 아이콘 번호, 그림 머리말
   - 아이콘 팔레트 표: arm9·오버레이(압축이면 풀어서)에서 0~5 값이 길게 이어진 곳
   - 필드 그림(a/0/8/1, BTX0): 텍스처 수·크기·형식별 묶음과 번호 범위
   - 트레이너 그림(a/0/5/8 등): 파일 수·종류
한 칸이 실패해도 나머지는 계속한다."""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1

EVENT = {143: '잠만보(길막)', 185: '꼬지모(길막)', 130: '갸라도스(분노의 호수)', 131: '라프라스(연결동굴)', 133: '이브이(선물)', 175: '토게피(알)',
         152: '치코리타(스타팅)', 155: '브케인(스타팅)', 158: '리아코(스타팅)', 243: '라이코', 244: '앤테이', 245: '스이쿤', 249: '루기아', 250: '칠색조',
         251: '세레비', 213: '단단지(선물)', 236: '배루키(선물)', 21: '깨비참(우편 교환)', 100: '찌리리공(아지트)', 101: '붐볼(아지트)', 74: '꼬마돌',
         95: '롱스톤', 147: '미뇽(선물)', 172: '피츄(삐죽귀)', 129: '잉어킹', 144: '프리져', 145: '썬더', 146: '파이어', 150: '뮤츠', 382: '가이오가',
         383: '그란돈', 384: '레쿠쟈', 483: '디아루가', 484: '펄기아', 487: '기라티나', 488: '크레세리아', 489: '피오네', 491: '다크라이', 492: '쉐이미', 386: '테오키스'}

NITRO = bytes([0x21, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21])   # arm9 모듈 정보 표시

def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def u32(d, o): return struct.unpack_from('<I', d, o)[0]

def lz_decompress(data):
    """LZ10/LZ11(앞에서부터) 풀기"""
    t = data[0]; n = data[1] | (data[2] << 8) | (data[3] << 16); i = 4; out = bytearray()
    while len(out) < n and i < len(data):
        flags = data[i]; i += 1
        for b in range(8):
            if len(out) >= n or i >= len(data): break
            if flags & (0x80 >> b):
                if t == 0x10:
                    v = (data[i] << 8) | data[i + 1]; i += 2; ln = (v >> 12) + 3; disp = (v & 0xFFF) + 1
                else:
                    a_ = data[i]; k = a_ >> 4
                    if k > 1: ln = k + 1; v = ((a_ & 15) << 8) | data[i + 1]; i += 2
                    elif k == 0: ln = (((a_ & 15) << 4) | (data[i + 1] >> 4)) + 0x11; v = ((data[i + 1] & 15) << 8) | data[i + 2]; i += 3
                    else: ln = (((a_ & 15) << 12) | (data[i + 1] << 4) | (data[i + 2] >> 4)) + 0x111; v = ((data[i + 2] & 15) << 8) | data[i + 3]; i += 4
                    disp = (v & 0xFFF) + 1
                for _ in range(ln): out.append(out[-disp])
            else: out.append(data[i]); i += 1
    return bytes(out)

def blz_decompress(data):
    """뒤에서부터 푸는 LZ(arm9·오버레이 압축). 압축이 아니면 None"""
    if len(data) < 8: return None
    a, extra = struct.unpack_from('<II', data, len(data) - 8)
    clen, hlen = a & 0xFFFFFF, a >> 24
    if extra == 0 or hlen < 8 or hlen > 0x0B or clen > len(data) or clen < hlen: return None
    keep = bytes(data[:len(data) - clen])
    comp = bytes(data[len(data) - clen:len(data) - hlen])[::-1]
    outlen = clen + extra; out = bytearray(); i = 0
    while len(out) < outlen and i < len(comp):
        flags = comp[i]; i += 1
        for b in range(8):
            if len(out) >= outlen or i >= len(comp): break
            if flags & (0x80 >> b):
                if i + 1 >= len(comp): return None
                v = (comp[i] << 8) | comp[i + 1]; i += 2
                n, disp = (v >> 12) + 3, (v & 0xFFF) + 3
                if disp > len(out): return None
                for _ in range(n): out.append(out[-disp])
            else:
                out.append(comp[i]); i += 1
    if len(out) < outlen: return None
    return keep + bytes(out[:outlen][::-1])

def binaries(rom):
    """[(이름, 풀린 바이트)] — arm9 와 오버레이 전부"""
    d = rom.d; out = []
    a9o, a9ram, a9size = u32(d, 0x20), u32(d, 0x28), u32(d, 0x2C)
    a9 = bytes(d[a9o:a9o + a9size]); note = '압축 아님'
    p = a9.find(NITRO)
    if p >= 0x1C:
        cend = u32(a9, p - 8)
        if cend:
            k = cend - a9ram
            dec = blz_decompress(a9[:k]) if 0 < k <= len(a9) else None
            if dec: a9 = dec + a9[k:]; note = '압축 풀음'
            else: note = '압축 표시 있음, 풀기 실패'
    out.append(('arm9(%s)' % note, a9))
    y9o, y9s = u32(d, 0x50), u32(d, 0x54)
    for k in range(y9s // 32):
        e = struct.unpack_from('<8I', d, y9o + 32 * k)
        ovid, fid, flag = e[0], e[6], e[7]
        try:
            s, t = rom.fat(fid); b = bytes(d[s:t])
        except Exception: continue
        if flag & 0x01000000:
            dec = blz_decompress(b)
            out.append(('overlay%d(%s)' % (ovid, '압축 풀음' if dec else '압축 풀기 실패'), dec or b))
        else: out.append(('overlay%d' % ovid, b))
    return out

def runs_small(b, maxv=5, minlen=400):
    """값이 0~maxv 인 바이트가 minlen 이상 이어진 곳(거의 0 만 있는 곳은 뺌)"""
    res = []; i = 0; n = len(b)
    while i < n:
        if b[i] <= maxv:
            j = i
            while j < n and b[j] <= maxv: j += 1
            if j - i >= minlen:
                seg = b[i:j]
                if sum(1 for x in seg if x) >= 0.2 * len(seg): res.append((i, j - i, seg))
            i = j
        else: i += 1
    return res

def rahc_info(f):
    c = f.find(b'RAHC')
    if c < 0: return None
    ty, tx, bpp, mapping, tiled, size = struct.unpack_from('<HHIIII', f, c + 8)
    return '높이 %d타일 너비 %d타일 bpp값 %d 매핑 0x%X 배치 %d(0=타일,1=줄) 크기 %d' % (ty, tx, bpp, mapping, tiled, size)

def btx_sig(d):
    """BTX0 → (텍스처 [(이름, 너비, 높이, 형식)], 팔레트 이름들)"""
    if d[:4] != b'BTX0': return None
    t = u32(d, 0x10)
    if d[t:t + 4] != b'TEX0': return None
    def dict_entries(off, esz):
        cnt = d[off + 1]; base = off + 16 + 4 * cnt
        ents = [d[base + esz * k: base + esz * (k + 1)] for k in range(cnt)]
        nb = base + esz * cnt
        names = [bytes(d[nb + 16 * k: nb + 16 * (k + 1)]).rstrip(bytes(1)).decode('latin1') for k in range(cnt)]
        return ents, names
    ti = t + u16(d, t + 0x0E); pi = t + u32(d, t + 0x34)
    ents, names = dict_entries(ti, 8)
    tex = []
    for e, nm in zip(ents, names):
        p = u32(e, 0); tex.append((nm, 8 << ((p >> 20) & 7), 8 << ((p >> 23) & 7), (p >> 26) & 7))
    _, pnames = dict_entries(pi, 4)
    return tex, pnames

def ranges(idx):
    rng = []; s = p = idx[0]
    for x in idx[1:] + [None]:
        if x is not None and x == p + 1: p = x; continue
        rng.append('%d-%d' % (s, p) if s != p else str(s))
        if x is not None: s = p = x
    return rng

def main():
    raw = open(sys.argv[1], 'rb').read(); rom = hg1.NDS(raw)
    out = ['== 이벤트 종 번호·그림 형식 찾기 — %s' % rom.code]
    def section(title, fn):
        out.append(''); out.append('== ' + title)
        try: fn()
        except Exception as e: out.append('실패: %r' % (e,))

    def scripts():
        scr = hg1.NARC(rom.get('a/0/1/2'))
        out.append('스크립트 파일 %d개' % len(scr.files))
        by_cmd = collections.Counter(); hits = []
        for fi, d in enumerate(scr.files):
            for off in range(2, len(d) - 1, 1):
                v = u16(d, off)
                if v in EVENT:
                    by_cmd[u16(d, off - 2)] += 1
                    hits.append((fi, off, v, d[max(0, off - 8):off].hex(' '), d[off + 2:off + 10].hex(' '), u16(d, off - 2)))
        top = [c for c, _ in by_cmd.most_common(15)]
        out.append('후보 %d곳(작은 번호는 잡음이 많음). 바로 앞 2바이트(명령 번호 후보) 많은 순: %s' % (len(hits), ' '.join('%04X:%d' % x for x in by_cmd.most_common(15))))
        out.append('종마다: 앞 2바이트가 위 상위 명령인 곳을 먼저, 최대 8곳')
        per = collections.defaultdict(list)
        for h in hits: per[h[2]].append(h)
        for v in sorted(per, key=lambda v: len(per[v])):
            hs = sorted(per[v], key=lambda h: (top.index(h[5]) if h[5] in top else 99, h[0], h[1]))
            out.append('-- %3d %s : %d곳' % (v, EVENT[v], len(per[v])))
            for fi, off, v_, b, a, _c in hs[:8]:
                out.append('   파일 %4d @%05X  앞[%s]  뒤[%s]' % (fi, off, b, a))

    def icons():
        ic = hg1.NARC(rom.get('a/0/2/0')).files
        kinds = collections.Counter(bytes(f[:4]) for f in ic)
        out.append('아이콘 NARC 파일 %d개, 종류 %s' % (len(ic), dict(kinds)))
        for i in range(min(10, len(ic))): out.append('  파일 %d: %s %d바이트' % (i, bytes(ic[i][:4]), len(ic[i])))
        first = next((i for i, f in enumerate(ic) if f[:4] == b'RGCN'), None)
        out.append('첫 RGCN(아이콘 그림) 번호 %s, RGCN 개수 %d, 크기 %s' % (first, kinds.get(b'RGCN', 0),
                   collections.Counter(len(f) for f in ic if f[:4] == b'RGCN').most_common(3)))
        if first is not None: out.append('아이콘 그림 머리말: %s' % rahc_info(ic[first]))
        pal = next((f for f in ic if f[:4] == b'RLCN'), None)
        if pal:
            c = pal.find(b'TTLP'); n = u32(pal, c + 0x10) // 2
            out.append('아이콘 팔레트 색 %d개(= 16색 %d벌)' % (n, n // 16))
        try:
            g = hg1.NARC(rom.get('a/0/0/4')).files
            out.append('비교 — 전투 그림 머리말: %s' % rahc_info(g[6 + 3]))
        except Exception: pass

    def palette_table():
        nic = None
        try: nic = sum(1 for f in hg1.NARC(rom.get('a/0/2/0')).files if f[:4] == b'RGCN')
        except Exception: pass
        cands = []
        for name, b in binaries(rom):
            out.append('  %s %d바이트' % (name, len(b)))
            for off, ln, seg in runs_small(b): cands.append((abs(ln - nic) if nic else 0, name, off, ln, seg))
        cands.sort(key=lambda x: (x[0], -x[3]))
        out.append('아이콘 그림 %s개. 0~5 값이 400개 넘게 이어진 곳 %d군데(아이콘 수와 가까운 순):' % (nic, len(cands)))
        for _, name, off, ln, seg in cands[:8]:
            out.append('  %s @0x%X 길이 %d 값 분포 %s' % (name, off, ln, dict(collections.Counter(seg))))
            out.append('    처음 60: ' + ' '.join(str(x) for x in seg[:60]))

    def dex_order():
        # 성도 도감 표: u16 전국 번호 256개가 성도 순서로(치코리타 152, 베이리프 153, 메가니움 154, 브케인 155 …). 10/14 도감 순서 바꾸기용
        pat = struct.pack('<9H', 152, 153, 154, 155, 156, 157, 158, 159, 160)
        found = 0
        for name, b in binaries(rom):
            i = b.find(pat)
            while i >= 0:
                vals = [u16(b, i + 2 * k) for k in range(256)]
                out.append('  %s @0x%X: 처음 24 = %s … 0 아닌 값 %d개' % (name, i, vals[:24], sum(1 for v in vals if v)))
                found += 1; i = b.find(pat, i + 2)
        if not found: out.append('  못 찾음(디지골드가 순서를 바꿨을 수 있음 — 152 153 154 로 시작하는 u16 표가 없음)')

    def overworld():
        mm = hg1.NARC(rom.get('a/0/8/1')).files
        out.append('필드 그림 파일 %d개, 종류 %s' % (len(mm), dict(collections.Counter(bytes(f[:4]) for f in mm).most_common(4))))
        groups = collections.OrderedDict(); bad = 0
        for i, f in enumerate(mm):
            try: sig = btx_sig(f)
            except Exception: sig = None
            if not sig: bad += 1; continue
            tex, pn = sig
            key = (len(tex), tuple(sorted({(w, h, fm) for _, w, h, fm in tex})), len(pn))
            groups.setdefault(key, []).append(i)
        out.append('BTX0 로 못 읽은 파일 %d개' % bad)
        out.append('묶음(텍스처 수, {(너비,높이,형식)}, 팔레트 수) → 파일 수, 번호 범위 앞부분')
        for key, idx in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:25]:
            out.append('  %s → %d개: %s' % (key, len(idx), ', '.join(ranges(idx)[:12])))
        for i in (0, len(mm) // 2, len(mm) - 1):
            try:
                tex, pn = btx_sig(mm[i]); out.append('  예 파일 %d: 텍스처 %s / 팔레트 %s' % (i, tex[:4], pn[:4]))
            except Exception: pass

    def trainer_pics():
        for path in ('a/0/5/8', 'a/0/5/9'):
            try:
                t = hg1.NARC(rom.get(path)).files
                out.append('%s: 파일 %d개, 종류 %s, 크기 %s' % (path, len(t), dict(collections.Counter(bytes(f[:4]) for f in t).most_common(4)),
                           collections.Counter(len(f) for f in t).most_common(3)))
                g = next((f for f in t if f[:4] == b'RGCN'), None)
                if g: out.append('  그림 머리말: %s' % rahc_info(g))
                if path == 'a/0/5/8': trainer_sheet(t)
            except Exception as e: out.append('%s: 못 읽음 %r' % (path, e))

    def trainer_sheet(t):
        # 10/14: 트레이너 그림 전부를 한 장에(칸 아래 숫자 = 그림 번호 = 직업 번호로 추정). hg1_out/classes.tsv 와 맞춰 보기
        try:
            import hg4_follow
            per = 5 if len(t) % 5 == 0 else None
            if not per: out.append('  트레이너 그림 모음: 파일 수가 5의 배수가 아니라 건너뜀'); return
            blocks = []; row = []
            DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001',
                   '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111']
            for k in range(len(t) // per):
                grp = t[k * per:(k + 1) * per]
                g = next((f for f in grp if f[:4] == b'RGCN' and len(f) > 4000), None) or next((f for f in grp if f[:4] == b'RGCN'), None)
                pf = next((f for f in grp if f[:4] == b'RLCN'), None)
                img = None
                if g and pf:
                    rows, mode = hg1.ncgr_rows(g)
                    pal = hg1.nclr(pf)
                    if rows and pal:
                        img = [list(r[:80]) + [0] * 0 for r in rows[:80]] + [[0] * 80 for _ in range(10)]
                        for d_i, dch in enumerate(str(k)):
                            for i, bit in enumerate(DIG[int(dch)]):
                                if bit == '1': img[82 + i // 3][2 + d_i * 4 + i % 3] = 1
                        pal = list(pal); pal[1] = (0, 0, 0) if pal[1] == pal[0] else pal[1]
                        row.append((img, pal))
                if img is None: row.append(None)
                if len(row) == 12: blocks.append(row); row = []
            if row: blocks.append(row)
            hg4_follow.rgba_sheet('트레이너_그림.png', blocks, 80, 90, 12)
            out.append('  트레이너 그림 모음 → 트레이너_그림.png (%d칸, 칸 아래 숫자 = 그림 번호)' % (len(t) // per))
        except Exception as e:
            out.append('  트레이너 그림 모음 못 만듦: %r' % e)

    def known_narcs():
        # 10/14 웹 조사(하트골드 파일표): 바꿀 그림·표가 든 묶음들. 멤버 수·크기·머리말만 적어 두면 내일 넣는 도구를 바로 만듦
        KN = [('a/0/4/6', '타이틀 화면 그림'), ('a/0/4/9', '트레이너 카드(배지)'), ('a/1/4/3', '포켓기어 겉모습'), ('a/1/4/4', '포켓기어 지도'), ('a/1/4/6', '포켓기어 전화'), ('a/1/4/7', '포켓기어 라디오'),
              ('a/0/6/8', '도감 그림'), ('a/0/7/4', '도감 자료(키·무게·순서)'), ('a/1/1/5', '알 부화 그림'), ('a/0/1/8', '도구 아이콘'), ('a/0/0/6', '트레이너 뒷모습'),
              ('a/2/5/3', 'HG 박치기 나무 야생'), ('a/2/3/0', '사파리존 야생'), ('a/1/3/3', '도감 서식지'), ('a/0/1/3', '스크립트 글'), ('a/0/0/7', '전투 배경'), ('a/0/0/8', '전투 화면 그림')]
        for path, what in KN:
            if path not in rom.paths: out.append('  %s %s: 없음' % (path, what)); continue
            try:
                d = rom.get(path)
                if d[:4] != b'NARC': out.append('  %s %s: NARC 아님(%d바이트, 머리 %s)' % (path, what, len(d), d[:4])); continue
                fs = hg1.NARC(d).files
                kinds = collections.Counter((bytes(f[:4]) if f[:4].isalpha() or f[:4] in (b'RGCN', b'RLCN', b'BTX0', b'RECN', b'RNAN') else ('LZ%02X' % f[0] if f[:1] in (b'\x10', b'\x11') else '?')) for f in fs)
                out.append('  %s %s: 멤버 %d, 종류 %s, 크기 %s' % (path, what, len(fs), dict(kinds.most_common(5)), collections.Counter(len(f) for f in fs).most_common(4)))
                if path in ('a/2/5/3', 'a/2/3/0', 'a/0/7/4', 'a/1/3/3'):
                    for mi, f in enumerate(fs[:3]): out.append('     멤버 %d 앞 48바이트: %s' % (mi, f[:48].hex(' ')))
            except Exception as e: out.append('  %s %s: 못 읽음 %r' % (path, what, e))
        # 도감 순서 표(152 153 154 …)가 a/0/7/4 안에 있는지
        pat = struct.pack('<9H', 152, 153, 154, 155, 156, 157, 158, 159, 160)
        for path in ('a/0/7/4', 'a/1/3/8', 'a/0/6/8'):
            if path not in rom.paths: continue
            try:
                for mi, f in enumerate(hg1.NARC(rom.get(path)).files):
                    g = f
                    if f[:1] in (b'\x10', b'\x11'):
                        try: g = lz_decompress(f)
                        except Exception: g = f
                    i = g.find(pat)
                    if i >= 0: out.append('  성도 도감 순서 표 후보: %s 멤버 %d @0x%X (압축 %s)' % (path, mi, i, '풀음' if g is not f else '아님'))
            except Exception: pass

    section('0) 바꿀 자리 묶음들(10/14 웹 조사)', known_narcs)
    section('1) 이벤트 종 번호(스크립트 a/0/1/2)', scripts)
    section('2) 아이콘(a/0/2/0)', icons)
    section('3) 아이콘 팔레트 표 후보(arm9·오버레이)', palette_table)
    section('3b) 성도 도감 순서 표(arm9·오버레이)', dex_order)
    section('4) 필드 그림(a/0/8/1)', overworld)
    section('5) 트레이너 그림', trainer_pics)
    open('hg_scan_out.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(l for l in out if l.startswith('==') or l.startswith('실패')))
    print('… 전체는 hg_scan_out.txt — 설계자에게 보내 주세요')

if __name__ == '__main__':
    main()
