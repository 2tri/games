#!/usr/bin/env python3
"""HG2 시험용 가짜 디지골드 롬 만들기 (진짜 롬이 없는 회사 PC 에서 스크립트를 시험하려고).
   python test_fake_rom.py <출력.nds> [--draft ../NDS_종_초안.tsv]
- 종 이름표 500칸: 1~251 은 포켓몬 이름(알려진 이름 + 채움), 디지골드 65종은 252번부터, 초안의 「본뜬 종」 이름도 400번대에 넣음
- 기술·특성·도구 이름표: 초안에 나오는 이름 + 채움
- 능력치·기술·진화 표 500칸"""
import os, sys, re, csv, struct, argparse, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1

def filler(prefix, n, avoid):
    syl = [chr(0xAC00 + i * 28) for i in range(0, 399, 7)]   # 받침 없는 글자 몇 개
    out = []
    for a, b, c in itertools.product(syl, syl, syl):
        nm = prefix + a + b + c
        if nm not in avoid: out.append(nm)
        if len(out) >= n: break
    return out

def narc(files, pad_last=True):
    n = hg1.NARC.__new__(hg1.NARC); n.head4 = b'\xfe\xff\x00\x01'; n.fnt = struct.pack('<IHH', 4, 0, 1)
    n.files = files; n.pad = b'\xff'; n.pad_last = pad_last
    return n.build()

def blz_compress(R):
    """시험용 뒤에서부터 LZ 압축(hg_scan.blz_decompress 짝)"""
    rev = R[::-1]; stream = bytearray(); i = 0; n = len(rev)
    while i < n:
        fp = len(stream); stream.append(0); flags = 0
        for b in range(8):
            if i >= n: break
            best = (0, 0)
            for disp in range(3, min(4098, i) + 1):
                l = 0
                while l < 18 and i + l < n and rev[i + l] == rev[i + l - disp]: l += 1
                if l > best[0]: best = (l, disp)
            if best[0] >= 3:
                l, disp = best; v = ((l - 3) << 12) | (disp - 3)
                stream += bytes([v >> 8, v & 0xFF]); flags |= 0x80 >> b; i += l
            else:
                stream.append(rev[i]); i += 1
        stream[fp] = flags
    clen = len(stream) + 8
    return bytes(stream[::-1]) + struct.pack('<II', clen | (8 << 24), len(R) - clen)

def build_rom(FILES, arm9=b''):
    tree = {}
    for p in FILES:
        parts = p.split('/'); t = tree
        for q in parts[:-1]: t = t.setdefault(q, {})
        t[parts[-1]] = None
    dirs = []
    def walk(t, parent):
        dirs.append([t, parent])
        me = len(dirs) - 1
        for k, v in sorted(t.items()):
            if isinstance(v, dict): walk(v, me)
    walk(tree, 0)
    idx = {id(d[0]): i for i, d in enumerate(dirs)}
    order = []
    def collect(t, prefix):
        first = len(order)
        for k, v in sorted(t.items()):
            if v is None: order.append(prefix + k)
        dirs[idx[id(t)]].append(first)
        for k, v in sorted(t.items()):
            if isinstance(v, dict): collect(v, prefix + k + '/')
    collect(tree, '')
    subs = []
    for t, parent, first in dirs:
        b = b''
        for k, v in sorted(t.items()):
            if v is None: b += bytes([len(k)]) + k.encode()
        for k, v in sorted(t.items()):
            if isinstance(v, dict): b += bytes([0x80 | len(k)]) + k.encode() + struct.pack('<H', 0xF000 + idx[id(v)])
        subs.append(b + b'\0')
    main = b''; body = b''; off = 8 * len(dirs)
    for i, (t, parent, first) in enumerate(dirs):
        main += struct.pack('<IHH', off + len(body), first, len(dirs) if i == 0 else 0xF000 + parent); body += subs[i]
    fnt = main + body
    FNT_OFF = 0x4000; FAT_OFF = FNT_OFF + ((len(fnt) + 0x1FF) & ~0x1FF)
    pos = FAT_OFF + ((len(order) * 8 + 0x1FF) & ~0x1FF)
    data = bytearray(pos); fat = b''
    for p in order:
        f = FILES[p]; fat += struct.pack('<II', len(data), len(data) + len(f)); data += f; data += b'\xff' * ((-len(data)) % 0x200)
    data[FNT_OFF:FNT_OFF + len(fnt)] = fnt; data[FAT_OFF:FAT_OFF + len(fat)] = fat
    if arm9:
        a9o = len(data); data += arm9; data += b'\xff' * ((-len(data)) % 0x200)
        struct.pack_into('<III', data, 0x28, 0x02000000, len(arm9), 0); struct.pack_into('<I', data, 0x20, a9o)
    data[0:12] = b'POKEMON HG\0\0'; data[12:16] = b'IPKK'
    struct.pack_into('<IIII', data, 0x40, FNT_OFF, len(fnt), FAT_OFF, len(fat))
    struct.pack_into('<I', data, 0x80, len(data)); data[0x14] = 0
    while (0x20000 << data[0x14]) < len(data): data[0x14] += 1
    struct.pack_into('<H', data, 0x15E, hg1.crc16(bytes(data[0:0x15E])))
    return bytes(data) + b'\xff' * 0x20000


def fake_btx(size=32, seed=0):
    """데리고 다니는 그림 흉내(BTX0: 텍스처 tsure_poke.1~8 4bpp size×size, 팔레트 2벌) — hg4_follow.btx_layout 이 읽는 꼴(10/16)"""
    n = 8; tex_bytes = size * size // 2
    # TEX0 머리(0x3C) 뒤에: 텍스처 사전 · 팔레트 사전 · 텍스처 자료 · 팔레트 자료
    def dict3d(entries, names, esz):
        cnt = len(entries)
        hdr = bytes([0, cnt]) + struct.pack('<H', 0) + bytes(12)          # 크기 등은 도구가 안 봄
        tree = bytes(4 * cnt)
        ent = struct.pack('<HH', esz, 4 + esz * cnt) + b''.join(entries)
        return hdr + tree[:4 * cnt - 4] + ent if False else hdr + tree + b''.join(entries) + b''.join(nm.encode('latin1').ljust(16, bytes(1)) for nm in names)
    texd = 0x3C
    tex_ents = [struct.pack('<II', ((k * tex_bytes) >> 3) | (2 if size == 32 else 3) << 20 | (2 if size == 32 else 3) << 23 | 3 << 26, 0) for k in range(n)]
    tdict = dict3d(tex_ents, ['tsure_poke.%d' % (k + 1) for k in range(n)], 8)
    pal_ents = [struct.pack('<HH', (k * 32) >> 3, 0) for k in range(2)]
    pdict = dict3d(pal_ents, ['tsure_poke_pl', 'tsure_poke_pl_r'], 4)
    tdict_off = texd; pdict_off = tdict_off + len(tdict); tdata_off = pdict_off + len(pdict); pdata_off = tdata_off + n * tex_bytes
    tex0 = bytearray(b'TEX0' + bytes(0x3C - 4))
    struct.pack_into('<H', tex0, 0x0E, tdict_off); struct.pack_into('<I', tex0, 0x14, tdata_off)
    struct.pack_into('<I', tex0, 0x34, pdict_off); struct.pack_into('<I', tex0, 0x38, pdata_off)
    body = bytes(tex0) + tdict + pdict + bytes([(seed + k) & 255 for k in range(n * tex_bytes)]) + bytes([(seed * 7 + k) & 255 for k in range(64)])
    return b'BTX0' + struct.pack('<HHIHHI', 0xFEFF, 1, 0x14 + len(body), 0x10, 1, 0x14) + body

def fake_follow():
    """a/0/8/1 흉내: 0~296 사람 모형(가짜), 297~ 데리고 다니는 그림. 칸 3·25 는 암컷 파일이 따로(값 +1), 249·250 은 큰 모형(64)"""
    vals = [0] * 494; v = 0
    for sp in range(1, 494):
        vals[sp] = v; v += 2 if sp in (3, 25, 172) else 1
    files = [b'XXXX' + bytes(12)] * 297
    big = {vals[249], vals[250]}
    for k in range(v + 1): files.append(fake_btx(64 if k in big else 32, k))
    return files, struct.pack('<494H', *vals)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--black', action='store_true', help='450칸에 두 번째 「워그레이몬」(검은 것이 따로 있는 경우 시험)'); ap.add_argument('--draft', default=next((q for q in (os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'NDS_종_초안.tsv')) if os.path.exists(q)), 'NDS_종_초안.tsv'))   # 10/16: 집(같은 폴더)·회사(한 칸 위) 둘 다
    A = ap.parse_args()
    rows = list(csv.DictReader(open(A.draft, encoding='utf-8'), delimiter='\t'))
    CM = hg1.Charmap('ks', 0x0400)
    names = [''] * 500
    for i, k in enumerate(hg1.KNOWN_POKEMON[:250]): names[i + 1] = k
    dg = []
    for r in rows:
        m = re.search(r'디지골드 「(.+?)」 그대로', r['메모'])
        if m and m.group(1) not in dg: dg.append(m.group(1))
    import hg2
    for r in rows:   # 디지골드 종은 덮은 포켓몬 번호 자리에(진짜 디지골드와 같게)
        m = re.search(r'디지골드 「(.+?)」 그대로', r['메모']); mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
        if m and mm and mm.group(1) in hg2.REPLACED_DEX: names[hg2.REPLACED_DEX[mm.group(1)]] = m.group(1).replace('워그레이몬(검정)', '워그레이몬')
    donors = sorted({m.group(1) for r in rows for m in [re.search(r'「(.+?)」 본뜸', r['메모'])] if m} - set(names))
    for i, g in enumerate(donors): names[400 + i] = g
    fill = iter(filler('', 500, set(names)))
    names = [n if n else next(fill) for n in names]; names[0] = '가가가'
    if A.black: names[450] = '워그레이몬'
    moves = sorted({tok.partition(':')[2] for r in rows for tok in r['레벨 기술'].split()} | {'몸통박치기', '할퀴기'})
    moves = ['가나다'] + moves; moves += filler('기', 468 - len(moves), set(moves))
    abil = sorted({a for r in rows for a in r['특성'].split(',') if a} | {'맹화', '급류', '심록'})
    abil = ['가나'] + abil; abil += filler('특', 124 - len(abil), set(abil))
    items = ['가나', '몬스터볼', '어둠의돌', '불꽃의돌', '천둥의돌', '물의돌', '달의돌', '빛의돌', '각성의돌', '태양의돌', '리프의돌', '금속코트', '왕의징표석', '업그레이드', '예리한손톱', '동글동글돌', '마음의물방울', '이상한사탕']
    items += filler('도', 540 - len(items), set(items))
    def ok(s):
        # 글자표에 없는 글자(괄호·숫자·영어)는 진짜 롬처럼 아무 번호로 — 풀면 {XXXX} 로 나온다
        out = []
        for ch in s:
            try: out += CM.enc(ch)[:-1]
            except ValueError: out.append(0x0120 + (ord(ch) % 64))
        return out + [0xFFFF]
    msgs = [hg1.msg_encode(0x1111, [ok('안녕')]), hg1.msg_encode(0x2222, [ok(n) for n in names]), hg1.msg_encode(0x3333, [ok(n) for n in moves]),
            hg1.msg_encode(0x4444, [ok(n) for n in abil]), hg1.msg_encode(0x5555, [ok(n) for n in items])]
    pers = [bytes([40, 40, 40, 40, 40, 40, 0, 0, 45, 64]) + bytes(2) + struct.pack('<HH', 5, 0) + bytes([127, 20, 70, 0, 1, 1, 65, 66]) + bytes(20) for _ in range(500)]
    learn = [struct.pack('<HH', (1 << 9) | 1, 0xFFFF) for _ in range(500)]
    evo = [bytes(44) for _ in range(500)]
    # 디지골드 종의 원래 진화도 넣어 둔다(HG2 가 옛 진화를 빼고 더하는 걸 시험하려고)
    slot_of = {}
    for r in rows:
        m = re.search(r'디지골드 「(.+?)」 그대로', r['메모']); mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
        if m and mm and mm.group(1) in hg2.REPLACED_DEX: slot_of[r['이름']] = hg2.REPLACED_DEX[mm.group(1)]
    for r in rows:
        if r['이름'] not in slot_of or not r['진화'].startswith('디지골드:'): continue
        ev = []
        for part in r['진화'][len('디지골드:'):].split(';'):
            mm = re.match(r'\s*(\S+)\[(.+)\]', part)
            if not mm or mm.group(1) not in slot_of: continue
            cond = mm.group(2); lm = re.match(r'Lv (\d+)', cond)
            if lm: ev.append((4, int(lm.group(1)), slot_of[mm.group(1)]))
            elif '사용' in cond: ev.append((7, items.index(cond.split(' ')[0]) if cond.split(' ')[0] in items else 2, slot_of[mm.group(1)]))
            else: ev.append((20, 1, slot_of[mm.group(1)]))
        evo[slot_of[r['이름']]] = b''.join(struct.pack('<HHH', *e) for e in ev[:7]) + bytes(6 * (7 - len(ev[:7]))) + b'\x00\x00'
    # HG3 시험용: 대사·타입 이름표·야생 표·트레이너
    talk = ['비상은 비행 디지몬의 관장이야', '포켓몬센터에서 쉬어 가렴', '로켓단이 성도 지방을 노린다!', '완성도가 높은 비상구', '웅이 기다린다',
            '체육관 관장을 이기면 배지를 준다', '레드를 만났다', '꼭두각시 인형', '나는 오박사다! 포켓몬스터의 세계에 온 것을 환영한다', '이슬이 맺혔다', '관장 이슬은 물 타입을 쓴다', '이걸 사도 괜찮아', '트레이너가 그린 그림', '트레이너는 아침 이슬을 본다', '골드 스프레이를 쓴 트레이너', '관장이랑 싸웠다', '관장이지만 약하다']
    types = ['노말', '격투', '비행', '독', '땅', '바위', '벌레', '고스트', '강철', '페어리', '불꽃', '물', '풀', '전기', '에스퍼', '얼음', '드래곤', '악']
    msgs += [hg1.msg_encode(0x6666, [ok(x) for x in talk]), hg1.msg_encode(0x7777, [ok(x) for x in types])]
    msgs += [hg1.msg_encode(0x5555, [ok('……'), ok('……')])]          # 레드 글 흉내(@글꼴 시험)
    tnames = ['비상', '유빈', '웅', '시바'] + ['실버'] * 21 + ['무희가', '무희나', '무희다', '무희라', '무희마'] + ['엘가', '엘나', '엘다', '엘라']   # 30~33 엘리트트레이너(정우 자리 고르기 시험), 0~3 관장 등, 4~24 라이벌(7번 × 스타팅 3), 25~29 기모노 소녀
    classes = ['가나'] + filler('직', 119, set()); classes[5] = '라이벌'; classes[9] = '엘리트트레이너♂'
    msgs += [hg1.msg_encode(0x8888, [ok(x) for x in tnames]), hg1.msg_encode(0x9999, [ok(x) for x in classes])]
    # 트레이너 글 표(trtbl 흉내): (트레이너 번호, 글 종류) 쌍 + 같은 개수의 글 파일. 라이벌(4·5)만 종류 25(짐) 글이 있음
    tpairs = [(t, ty) for t in range(len(tnames)) for ty in list(range(22)) + ([25] if 4 <= t < 25 else [])]
    msgs += [hg1.msg_encode(0x7777, [ok('트레이너글') for k in range(len(tpairs))])]
    trtbl = b''.join(struct.pack('<HH', t, ty) for t, ty in tpairs)
    NL = chr(92) + 'n'
    cats = [('파충류형 디지몬' if 252 <= i < 330 else '씨앗포켓몬') for i in range(500)]
    descs = ['가나다라마바사아자' + NL + '차카타파하가나다라' + NL + '마바사아자차카타' for i in range(500)]
    msgs += [hg1.msg_encode(0xAAAA, [ok(x) for x in cats]), hg1.msg_encode(0xBBBB, [CM.enc(x) for x in descs])]
    import random; random.seed(3)
    enc = []
    for k in range(10):
        b = bytearray(0xC4); b[0] = 30
        for off in [0x14 + 2 * j for j in range(36)]: struct.pack_into('<H', b, off, random.choice([16, 19, 21, 161, 13, 252, 175, 386, 400] + ([450] if A.black else [])))
        enc.append(bytes(b))
    trd = []; trp = []
    RIV_LV = [5, 16, 22, 30, 40, 45, 55]                              # 라이벌 차수별 최고 레벨(3명씩 같음)
    for k in range(25):
        flags = k % 2; n = 2
        trd.append(bytes([flags, 5 if k >= 4 else 3, 0, n]) + bytes(16)); top = RIV_LV[[0, 2, 1, 3, 4, 6, 5][(k - 4) // 3]] if k >= 4 else 11   # 번호 순서 ≠ 전투 순서(정렬 시험)
        e = b''
        for j in range(n):
            e += struct.pack('<BBHH', 0, 0, top - 1 + j, random.choice([16, 152, 4, 252, 300]))
            if flags & 1: e += struct.pack('<4H', 1, 2, 0, 0)
            e += b'\x00\x00'
        trp.append(e)
    for k, sp in enumerate([134, 135, 136, 196, 197]):          # 기모노 소녀 5명(직업 7, 이브이 진화형 1마리 Lv17)
        trd.append(bytes([0, 7, 0, 1]) + bytes(16)); trp.append(struct.pack('<BBHH', 0, 0, 17, sp) + bytes(2))
    for lv, dbl in ((30, 0), (52, 0), (45, 0), (60, 1)):          # 엘리트트레이너 4명: 혼자 싸우는 셋 중 Lv52(번호 31)가 뽑혀야 함, Lv60 은 더블이라 제외
        trd.append(bytes([0, 9, 0, 1]) + bytes(12) + bytes([dbl]) + bytes(3)); trp.append(struct.pack('<BBHH', 0, 0, lv, 16) + bytes(2))
    ncgr_t = b'RGCN' + bytes(12) + b'RAHC' + struct.pack('<I', 0x20 + 6400) + bytes(0x18) + bytes(6400)
    nclr_t = b'RLCN' + bytes(12) + b'TTLP' + bytes(0x14) + bytes(32)
    gra = []
    def nclr(v): return b'RLCN' + bytes(12) + b'TTLP' + bytes(0x14) + struct.pack('<HH', 0, v) + bytes(28)   # 칸마다 다른 색(복사 시험용)
    for i in range(500): gra += [b'', ncgr_t, b'', ncgr_t, nclr(i), nclr(10000 + i)]
    scr = [bytes(40) + struct.pack('<HHH', 0x0089, 152, 5) + bytes(10) + struct.pack('<HHH', 0x00F5, 249, 40), struct.pack('<HHH', 0x0089, 155, 5)]
    scr.append(struct.pack('<HHH', 41, 0x8004, 350) + struct.pack('<HHH', 41, 0x8005, 1) + struct.pack('<HHHH', 127, 0x8004, 0x8005, 0x800C) + struct.pack('<HH', 20, 2033) + bytes(8))   # 관장 기술머신(TM23) 선물 흉내
    scr = [struct.pack('<I', 2) + struct.pack('<H', 0xFD13) + x for x in scr]      # 진짜처럼 머리 표(상대 위치 1개) + 끝 표시 FD13(10/15 롬 검사기 시험)
    icon_pal = b'RLCN' + bytes(12) + b'TTLP' + struct.pack('<IIIII', 0x18 + 96, 3, 0, 96, 0x10) + bytes(96)
    icon_g = b'RGCN' + bytes(12) + b'RAHC' + struct.pack('<IHHIIII', 0x20 + 1024, 8, 4, 3, 0x10, 0, 1024) + bytes(4) + bytes(1024)
    icons = [icon_pal] + [b'RCER' + bytes(28), b'RNAN' + bytes(28)] * 3 + [icon_g] * 500
    random.seed(9)
    pal_tab = bytes(random.choice([0, 1, 1, 2]) for _ in range(507))
    code = bytes(random.choice(range(6, 256)) for _ in range(64))
    a9 = bytearray(code * 8 + bytes(0x200)); a9[0x100:0x124] = struct.pack('<7I', 0, 0, 0, 0, 0, 0, 0) + bytes([0x21, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21])
    mart = b''.join(struct.pack('<HH', it, t) for it, t in ((4, 1), (3, 3), (2, 4), (17, 1), (26, 2), (25, 4), (24, 5), (23, 6), (28, 3), (18, 1), (22, 1), (21, 2), (19, 2), (20, 2), (27, 4), (78, 2), (79, 2), (76, 3), (77, 4)))   # 일반 상점 표(pret scrcmd_mart.c _020FBF22 차례, 10/16)
    starters = struct.pack('<3I', 261, 252, 287) + code + struct.pack('<3I', 261, 252, 287)   # 스타팅 표: 4바이트 int 3칸 × 2곳(필드·고르기 화면), 디지골드 값(10/16)
    follow_files, follow_lut = fake_follow()
    body = bytes(a9[0x200:]) + code * 4 + pal_tab + mart + code * 2 + starters + code * 4 + follow_lut + code * 2   # 10/16 필드 그림 번호 표(sModelIndexLUT 흉내)
    comp = blz_compress(body); arm9 = bytearray(a9[:0x200]) + comp
    struct.pack_into('<I', arm9, 0x100 + 0x14, 0x02000000 + len(arm9))      # 압축 끝 주소
    FILES = {'a/1/3/1': narc([trtbl]), 'a/0/1/2': narc(scr), 'a/0/2/0': narc(icons), 'a/0/0/4': narc(gra), 'a/0/0/2': narc(pers), 'a/0/2/7': narc(msgs, pad_last=False), 'a/0/3/3': narc(learn), 'a/0/3/4': narc(evo),
             'a/0/3/7': narc(enc), 'a/0/5/5': narc(trd), 'a/0/5/6': narc(trp),
             'a/0/1/1': narc([bytes([0, 0, 1, 40, 0, 100, 20, 0]) + bytes(28) for _ in range(468)]),
             'a/0/1/0': narc([bytes([k & 255, k >> 8]) * 8 for k in range(500)]),
             'a/0/8/1': narc(follow_files),   # 데리고 다니는 그림(10/16)   # 기술 연출(기술 번호 순, 10/16 필살기 연출 시험)
             # 10/15 야생 표 밖: 박치기(파일 3: 나무 1묶음), 사파리(1 구역), 교환(2건)
             'a/2/5/2': narc([struct.pack('<HH', 1, 0) + b''.join(struct.pack('<HBB', sp, 5, 10) for sp in (16, 21, 43, 69, 0, 0)) * 3 + struct.pack('<hh', 3, 4) + struct.pack('<hh', -1, -1) * 5] + [struct.pack('<HH', 0, 0)] * 2),
             'a/2/3/0': narc([bytes([10, 3, 2, 2, 2, 0, 0, 0]) + b''.join(struct.pack('<HH', 19 + (k % 5), 15) for k in range(30)) + struct.pack('<HH', 143, 20) * 30 + bytes(40)
                              + b''.join(struct.pack('<HH', 129, 10) for _ in range(30)) + struct.pack('<HH', 54, 20) * 9 + bytes(12)
                              + (b''.join(struct.pack('<HH', 129, 10) for _ in range(30)) + struct.pack('<HH', 118, 20) * 6 + bytes(8)) * 3]),
             'a/1/1/2': narc([struct.pack('<i', 95) + bytes(0x48) + struct.pack('<ii', 69, 0), struct.pack('<i', 66) + bytes(0x48) + struct.pack('<ii', 96, 0)]),
             'data/mushi/mushi_encount.bin': b''.join(struct.pack('<HBBBBH', sp, 7, 12, 100 - 10 * k, 20, 0) for k, sp in enumerate((10, 11, 13, 14, 46, 48, 123, 127, 10, 11))) * 4}   # 기술 자료(36바이트, 필살기 시험용 10/14)
    open(A.out, 'wb').write(build_rom(FILES, bytes(arm9)))
    print('가짜 롬 %s: 종 500, 디지골드 이름 %d, 본뜬 종 %d, 기술 %d, 특성 %d, 도구 %d' % (A.out, len(dg), len(donors), len(moves), len(abil), len(items)))

if __name__ == '__main__':
    main()
