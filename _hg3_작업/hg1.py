#!/usr/bin/env python3
"""HG1 — 하트골드 디지몬 개조판: 분석 + 롬 쓰기 시험 + 내 설계(GBC) 대조. 표준 라이브러리만 쓴다(설치할 것 없음).

[집 PC 에서 할 일]
1. 이 글 전체를 복사해 메모장에 붙이고, 「다른 이름으로 저장」 → 파일 형식 「모든 파일」, 이름 hg1.py, 인코딩 UTF-8.
   롬과 같은 폴더에 두면 편하다.
2. 그 폴더에서 Claude Code 에게:  「python hg1.py "<롬 파일 이름>.nds" 실행해 줘. 파이썬이 없으면 설치부터 도와줘.
   코드는 고치지 말고, 오류가 나면 오류 원문만 보여 줘.」
   (Claude 없이 직접: 명령 프롬프트에서  python hg1.py "롬.nds")
3. 끝나면 hg1_out.zip 이 생긴다 → 회사로 보낸다(Teams 등 들어오는 쪽). 롬 파일은 보내지 않는다.
4. (선택) hg1_out/test_name.nds 를 폰 델타로 열면 아구몬 이름이 「시험몬」으로 보이는지 확인 → 롬 쓰기가 되는지 시험.

원본 롬은 읽기만 한다. 쓰기 시험은 hg1_out/test_*.nds 복사본에만 한다.
맨 아래 긴 글자 덩어리는 내 설계 자료(압축)다. 한 글자라도 깨지면 「설계 자료가 깨짐」이 나온다 → 다시 복사."""
import os, sys, struct, zlib, json, base64, hashlib, collections, argparse, zipfile, time, traceback
try: sys.stdout.reconfigure(errors='replace'); sys.stderr.reconfigure(errors='replace')   # 한국어 콘솔(cp949)에서 「—」 같은 글자로 멈추지 않게
except Exception: pass

VERSION = 'HG1 2026-10-08'
R = []                       # report.txt 줄
def say(*a):
    s = ' '.join(str(x) for x in a)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii', 'replace').decode())
    R.append(s)

# ======================================================================= NDS 롬
def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc

class NDS:
    """파일 이름표(FNT)·위치표(FAT)를 직접 읽고 쓴다. 파일을 바꿀 때 다른 파일 위치는 건드리지 않는다
       (자리에 맞으면 제자리, 아니면 롬 끝 빈 곳에) → 패치가 작다."""
    def __init__(self, data):
        self.d = bytearray(data)
        self.title = bytes(self.d[0:12]).rstrip(b'\0').decode('latin1')
        self.code = bytes(self.d[12:16]).decode('latin1')
        self.fnt_off, self.fnt_size, self.fat_off, self.fat_size = struct.unpack_from('<IIII', self.d, 0x40)
        self.nfiles = self.fat_size // 8
        self.paths = {}
        self._walk(0xF000, '', 0)

    def fat(self, i):
        return struct.unpack_from('<II', self.d, self.fat_off + i * 8)

    def _walk(self, dir_id, prefix, depth):
        if depth > 32: raise ValueError('FNT 깊이 이상')
        sub, first, _ = struct.unpack_from('<IHH', self.d, self.fnt_off + (dir_id & 0xFFF) * 8)
        p = self.fnt_off + sub; fid = first
        while True:
            l = self.d[p]; p += 1
            if l == 0: break
            name = bytes(self.d[p:p + (l & 0x7F)]).decode('latin1'); p += l & 0x7F
            if l & 0x80:
                sid = struct.unpack_from('<H', self.d, p)[0]; p += 2
                self._walk(sid, prefix + name + '/', depth + 1)
            else:
                self.paths[prefix + name] = fid; fid += 1

    def get(self, path):
        s, e = self.fat(self.paths[path]); return bytes(self.d[s:e])

    def _region_starts(self):
        st = [struct.unpack_from('<I', self.d, o)[0] for o in (0x20, 0x30, 0x40, 0x48, 0x50, 0x58, 0x68)]
        return st + [self.fat(i)[0] for i in range(self.nfiles)]

    def used_end(self):
        return max([struct.unpack_from('<I', self.d, 0x80)[0]] + [self.fat(i)[1] for i in range(self.nfiles)])

    def put(self, path, data):
        """→ '제자리' 또는 '끝에'"""
        fid = self.paths[path]; s, e = self.fat(fid)
        later = [x for x in self._region_starts() if x > s]
        limit = min(later) if later else len(self.d)
        if len(data) <= limit - s:
            self.d[s:s + len(data)] = data
            if s + len(data) < e: self.d[s + len(data):e] = b'\xff' * (e - s - len(data))
            struct.pack_into('<II', self.d, self.fat_off + fid * 8, s, s + len(data)); how = '제자리'
            if s + len(data) > struct.unpack_from('<I', self.d, 0x80)[0]: struct.pack_into('<I', self.d, 0x80, s + len(data))
        else:
            ns = (self.used_end() + 0x1FF) & ~0x1FF
            ne = ns + len(data)
            if len(self.d) < ne: self.d += b'\xff' * (ne - len(self.d))
            self.d[ns:ne] = data
            struct.pack_into('<II', self.d, self.fat_off + fid * 8, ns, ne)
            if ne > struct.unpack_from('<I', self.d, 0x80)[0]: struct.pack_into('<I', self.d, 0x80, ne)
            while (0x20000 << self.d[0x14]) < len(self.d): self.d[0x14] += 1
            how = '끝에'
        struct.pack_into('<H', self.d, 0x15E, crc16(bytes(self.d[0:0x15E])))
        return how

# ======================================================================= NARC
class NARC:
    def __init__(self, data):
        if data[:4] != b'NARC': raise ValueError('NARC 아님')
        self.head4 = data[4:8]
        p = struct.unpack_from('<H', data, 0xC)[0]
        if data[p:p + 4] != b'BTAF': raise ValueError('BTAF 없음')
        sz, n = struct.unpack_from('<IH', data, p + 4)
        fat = [struct.unpack_from('<II', data, p + 12 + i * 8) for i in range(n)]
        q = p + sz
        if data[q:q + 4] != b'BTNF': raise ValueError('BTNF 없음')
        fsz = struct.unpack_from('<I', data, q + 4)[0]
        self.fnt = data[q + 8:q + fsz]
        r = q + fsz
        if data[r:r + 4] != b'GMIF': raise ValueError('GMIF 없음')
        base = r + 8
        self.files = [bytes(data[base + s:base + e]) for s, e in fat]
        gaps = [data[base + fat[i][1]:base + fat[i + 1][0]] for i in range(n - 1) if fat[i + 1][0] > fat[i][1]]
        self.pad = gaps[0][:1] if gaps else b'\xff'
        self.pad_last = (struct.unpack_from('<I', data, r + 4)[0] - 8) > (fat[-1][1] if fat else 0)

    def build(self):
        body = bytearray(); fat = bytearray()
        for i, f in enumerate(self.files):
            s = len(body); body += f; fat += struct.pack('<II', s, s + len(f))
            if i < len(self.files) - 1 or self.pad_last: body += self.pad * ((-len(body)) % 4)
        btaf = b'BTAF' + struct.pack('<IHH', 12 + len(fat), len(self.files), 0) + fat
        btnf = b'BTNF' + struct.pack('<I', 8 + len(self.fnt)) + self.fnt
        gmif = b'GMIF' + struct.pack('<I', 8 + len(body)) + body
        total = 16 + len(btaf) + len(btnf) + len(gmif)
        return b'NARC' + self.head4 + struct.pack('<IHH', total, 16, 3) + btaf + btnf + gmif

# ======================================================================= 글(msg)
def msg_decode(data):
    """→ (seed, [부호 목록(끝 0xFFFF 포함)])"""
    count, seed = struct.unpack_from('<HH', data, 0)
    out = []
    for i in range(count):
        key = (seed * 0x2FD * (i + 1)) & 0xFFFF; k32 = key | (key << 16)
        off, ln = struct.unpack_from('<II', data, 4 + i * 8)
        off ^= k32; ln ^= k32
        if off + ln * 2 > len(data) or ln > 0x4000: raise ValueError('글 항목 %d 범위 밖' % i)
        ck = (0x91BD3 * (i + 1)) & 0xFFFF; cs = []
        for j in range(ln):
            cs.append(struct.unpack_from('<H', data, off + j * 2)[0] ^ ck); ck = (ck + 0x493D) & 0xFFFF
        out.append(cs)
    return seed, out

def msg_encode(seed, entries):
    n = len(entries); tab = bytearray(); body = bytearray(); off = 4 + 8 * n
    for i, cs in enumerate(entries):
        key = (seed * 0x2FD * (i + 1)) & 0xFFFF; k32 = key | (key << 16)
        tab += struct.pack('<II', off ^ k32, len(cs) ^ k32)
        ck = (0x91BD3 * (i + 1)) & 0xFFFF
        for c in cs:
            body += struct.pack('<H', c ^ ck); ck = (ck + 0x493D) & 0xFFFF
        off += 2 * len(cs)
    return struct.pack('<HH', n, seed) + bytes(tab) + bytes(body)

KS = []
for _b1 in range(0xB0, 0xC9):
    for _b2 in range(0xA1, 0xFF):
        try: KS.append(bytes([_b1, _b2]).decode('cp949'))
        except Exception: KS.append('\0')
KS_INDEX = {c: i for i, c in enumerate(KS) if c != '\0'}
SPECIAL = {0xE000: '\\n', 0x25BC: '\\r', 0x25BD: '\\f'}

class Charmap:
    """한글 부호표. mode='ks'(완성형 2,350자 순서) 또는 'uni'(현대 한글 11,172자 순서), base=「가」의 부호"""
    def __init__(self, mode, base, extra=None):
        self.mode, self.base = mode, base
        self.extra = dict(extra or {})              # 부호 → 글자 (숫자·문장부호, 나중에 채움)
        self.rev = {v: k for k, v in self.extra.items()}
    def ch(self, c):
        if c in SPECIAL: return SPECIAL[c]
        if c in self.extra: return self.extra[c]
        k = c - self.base
        if self.mode == 'ks' and 0 <= k < len(KS) and KS[k] != '\0': return KS[k]
        if self.mode == 'uni' and 0 <= k < 11172: return chr(0xAC00 + k)
        return None
    def dec(self, cs):
        s = []
        for c in cs:
            if c == 0xFFFF: break
            t = self.ch(c)
            s.append(t if t is not None and t not in '{}\\' else '{%04X}' % c)
        return ''.join(s)
    def enc(self, s):
        s = s.replace('…', '...')               # 이 롬 글에는 「…」 글자가 없고 점 세 개로 쓴다(집 보고 10/12)
        out = []; i = 0
        while i < len(s):
            if s[i] == '{':
                j = s.index('}', i); out.append(int(s[i + 1:j], 16)); i = j + 1; continue
            if s[i] == '\\' and i + 1 < len(s) and s[i + 1] in 'nrf':
                out.append({'n': 0xE000, 'r': 0x25BC, 'f': 0x25BD}[s[i + 1]]); i += 2; continue
            c = s[i]
            if c in self.rev: out.append(self.rev[c])
            elif self.mode == 'ks' and c in KS_INDEX: out.append(self.base + KS_INDEX[c])
            elif self.mode == 'uni' and 0xAC00 <= ord(c) <= 0xD7A3: out.append(self.base + ord(c) - 0xAC00)
            else: raise ValueError('부호표에 없는 글자: %r' % c)
            i += 1
        return out + [0xFFFF]
    def is_hangul(self, c):
        k = c - self.base
        return 0 <= k < (len(KS) if self.mode == 'ks' else 11172)

# ======================================================================= PNG·그림
def png(path, w, h, rows, pal):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    p = bytes(c for col in pal for c in col)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0))
                           + ch(b'PLTE', p) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))

DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001',
       '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111']

class Sheet:
    def __init__(self, cols, rows, cw=80, chh=88):
        self.cw, self.ch, self.cols = cw, chh, cols
        self.w, self.h = cols * cw, max(1, rows) * chh
        self.px = [[0] * self.w for _ in range(self.h)]
        self.pal = {(255, 255, 255): 0, (0, 0, 0): 1}
    def idx(self, col):
        if col not in self.pal:
            if len(self.pal) >= 256:
                return min(self.pal.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[0], col)))[1]
            self.pal[col] = len(self.pal)
        return self.pal[col]
    def put(self, cell, rows, pal):
        gx, gy = (cell % self.cols) * self.cw, (cell // self.cols) * self.ch
        for y in range(min(80, len(rows))):
            for x in range(min(80, len(rows[y]))):
                v = rows[y][x]
                if v: self.px[gy + y][gx + x] = self.idx(pal[v] if pal else (v * 16, v * 16, v * 16))
    def label(self, cell, n):
        gx, gy = (cell % self.cols) * self.cw + 2, (cell // self.cols) * self.ch + 81
        for k, d in enumerate(str(n)):
            for i, b in enumerate(DIG[int(d)]):
                if b == '1': self.px[gy + i // 3][gx + k * 4 + i % 3] = 1
    def save(self, path):
        pal = sorted(self.pal, key=self.pal.get)
        png(path, self.w, self.h, self.px, pal + [(0, 0, 0)] * (256 - len(pal)))

def sect(data, magic):
    i = data.find(magic); return i if i >= 0 else None

def lcg_dec(words, rev):
    v = list(words); n = len(v)
    s = v[-1] if rev else v[0]
    for i in (range(n - 1, -1, -1) if rev else range(n)):
        v[i] ^= s & 0xFFFF; s = (s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
    return v

def glyph(v):
    """NDS_글자표_추가.tsv 의 글자 칸 → 실제 글자. 「(공백)」 = 띄어쓰기. 빈칸·None 은 None(그 줄 무시)
    (10/14: 탭 뒤 공백 한 칸이 붙여넣기·편집기에서 사라져 01DE 가 「글자 없음」으로 덮였음)"""
    if v is None: return None
    if v.strip() in ('(공백)', '(띄어쓰기)', 'SPACE'): return ' '
    return v if v != '' else None

def ncgr_rows(data):
    """포켓몬 전투 그림(160x80, 4bpp) → (행 목록, 복호 방식)"""
    c = sect(data, b'RAHC')
    if c is None: return None, None
    size = struct.unpack_from('<I', data, c + 4)[0]
    px = data[c + 0x20:c + 0x20 + 6400]          # 디지골드 롬은 RAHC 크기 칸이 0(원본은 6432) → 크기 칸을 믿지 않고 160x80 4bpp = 6400바이트(집 보고 10/12)
    if len(px) != 6400: return None, 'size%d' % len(px)
    w = list(struct.unpack('<3200H', px))
    best = None
    for name, v in (('pt', lcg_dec(w, True)), ('dp', lcg_dec(w, False)), ('none', w)):
        b = struct.pack('<3200H', *v); p = []
        for byte in b: p += [byte & 15, byte >> 4]
        rows = [p[y * 160:(y + 1) * 160] for y in range(80)]
        score = sum(1 for x in range(160) if rows[0][x] == 0) + sum(1 for x in range(160) if rows[79][x] == 0)
        if best is None or score > best[0]: best = (score, rows, name)
    return best[1], best[2]

def nclr(data):
    c = sect(data, b'TTLP')
    if c is None: return None
    off = c + 0x18; cols = []
    for i in range(16):
        v = struct.unpack_from('<H', data, off + i * 2)[0]
        cols.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return cols

# ======================================================================= BPS 패치
def _vlq(n):
    out = bytearray()
    while True:
        x = n & 0x7F; n >>= 7
        if n == 0: out.append(0x80 | x); break
        out.append(x); n -= 1
    return bytes(out)

def bps_make(src, dst):
    out = bytearray(b'BPS1') + _vlq(len(src)) + _vlq(len(dst)) + _vlq(0)
    i = 0; n = len(dst); ns = len(src)
    while i < n:
        j = i
        while j < n and j < ns and src[j] == dst[j]: j += 1
        if j > i:
            out += _vlq(((j - i - 1) << 2) | 0); i = j; continue
        j = i
        while j < n and not (j + 16 <= min(n, ns) and src[j:j + 16] == dst[j:j + 16]): j += 1
        out += _vlq(((j - i - 1) << 2) | 1) + dst[i:j]; i = j
    out += struct.pack('<I', zlib.crc32(src) & 0xFFFFFFFF) + struct.pack('<I', zlib.crc32(dst) & 0xFFFFFFFF)
    out += struct.pack('<I', zlib.crc32(bytes(out)) & 0xFFFFFFFF)
    return bytes(out)

def bps_apply(src, patch):
    p = 4
    def rd():
        nonlocal p
        data = 0; shift = 1
        while True:
            x = patch[p]; p += 1
            data += (x & 0x7F) * shift
            if x & 0x80: return data
            shift <<= 7; data += shift
    ss, ts, ms = rd(), rd(), rd(); p += ms
    out = bytearray(); end = len(patch) - 12
    while p < end:
        d = rd(); cmd, ln = d & 3, (d >> 2) + 1
        if cmd == 0: out += src[len(out):len(out) + ln]
        elif cmd == 1: out += patch[p:p + ln]; p += ln
        else: raise ValueError('이 검사기는 0·1 명령만')
    return bytes(out)

# ======================================================================= 4세대 자료 읽기
TYPES = ['노말', '격투', '비행', '독', '땅', '바위', '벌레', '고스트', '강철', '페어리(???)', '불꽃', '물', '풀', '전기', '에스퍼', '얼음', '드래곤', '악']
EVO_METHOD = {0: '-', 1: '친밀도', 2: '친밀도(낮)', 3: '친밀도(밤)', 4: '레벨', 5: '통신', 6: '통신+도구', 7: '도구 사용', 8: '레벨(공>방)',
              9: '레벨(공=방)', 10: '레벨(공<방)', 11: '레벨(성격값1)', 12: '레벨(성격값2)', 13: '레벨(빈칸)', 14: '레벨(껍질)', 15: '아름다움',
              16: '도구(수컷)', 17: '도구(암컷)', 18: '도구 지닌 채 레벨(낮)', 19: '도구 지닌 채 레벨(밤)', 20: '기술 알고 레벨',
              21: '파티에 종', 22: '레벨(수컷)', 23: '레벨(암컷)', 24: '장소(자기장)', 25: '장소(이끼)', 26: '장소(얼음)'}
KNOWN_POKEMON = ('이상해씨 이상해풀 이상해꽃 파이리 리자드 리자몽 꼬부기 어니부기 거북왕 캐터피 단데기 버터플 뿔충이 딱충이 독침붕 구구 피죤 피죤투 '
    '꼬렛 레트라 깨비참 깨비드릴조 아보 아보크 피카츄 라이츄 모래두지 고지 식스테일 나인테일 푸린 푸크린 주뱃 골뱃 뚜벅쵸 냄새꼬 라플레시아 '
    '디그다 닥트리오 나옹 페르시온 고라파덕 골덕 망키 성원숭 가디 윈디 발챙이 슈륙챙이 강챙이 캐이시 윤겔라 후딘 알통몬 근육몬 괴력몬 '
    '모다피 우츠동 우츠보트 왕눈해 독파리 꼬마돌 데구리 딱구리 포니타 날쌩마 야돈 야도란 코일 레어코일 파오리 두두 두트리오 쥬쥬 쥬레곤 '
    '질퍽이 질뻐기 셀러 파르셀 고오스 고우스트 팬텀 롱스톤 슬리프 슬리퍼 크랩 킹크랩 찌리리공 붐볼 아라리 나시 탕구리 텅구리 시라소몬 홍수몬 '
    '내루미 또가스 또도가스 뿔카노 코뿌리 럭키 덩쿠리 캥카 쏘드라 시드라 콘치 왕콘치 별가사리 아쿠스타 마임맨 스라크 루주라 에레브 마그마 '
    '쁘사이저 켄타로스 잉어킹 갸라도스 라프라스 메타몽 이브이 샤미드 쥬피썬더 부스터 폴리곤 암나이트 암스타 투구 투구푸스 프테라 잠만보 '
    '프리져 썬더 파이어 미뇽 신뇽 망나뇽 뮤츠 치코리타 베이리프 메가니움 브케인 마그케인 블레이범 리아코 엘리게이 장크로다일 꼬리선 다꼬리 '
    '부우부 야부엉 레디바 레디안 페이검 아리아도스 크로뱃 초라기 랜턴 피츄 삐 토게피 토게틱 네이티 네이티오 메리프 보송송 전룡 아르코 마릴 '
    '마릴리 꼬지모 왕구리 통통코 두코 솜솜코 에이팜 해너츠 해루미 왕자리 우파 누오 에브이 블래키 니로우 야도킹 무우마 안농 마자용 키링키 '
    '피콘 쏘콘 노고치 글라이거 강철톤 블루 그랑블루 침바루 핫삼 단단지 헤라크로스 포푸니 깜지곰 링곰 마그마그 마그카르고 꾸꾸리 메꾸리 '
    '코산호 총어 대포무노 딜리버드 만타인 무장조 델빌 헬가 킹드라 코코리 코리갑 폴리곤2 노라키 루브도 배루키 카포에라 뽀뽀라 에레키드 마그비 '
    '밀탱크 해피너스 라이코 앤테이 스이쿤 애버라스 데기라스 마기라스 루기아 칠색조 세레비').split()

NARC_PATHS = {'personal': 'a/0/0/2', 'pokegra': 'a/0/0/4', 'msg': 'a/0/2/7', 'learn': 'a/0/3/3', 'evo': 'a/0/3/4', 'enc': 'a/0/3/7',
              'trdata': 'a/0/5/5', 'trpoke': 'a/0/5/6', 'mmodel': 'a/0/8/1', 'icon': 'a/0/2/0', 'script': 'a/0/1/2', 'zone_event': 'a/0/3/2'}

def personal(d):
    if len(d) < 28: return None
    return {'stats': list(d[0:6]), 'type': [d[6], d[7]], 'catch': d[8], 'exp': d[9], 'items': list(struct.unpack_from('<HH', d, 12)),
            'gender': d[16], 'growth': d[19], 'egg': [d[20], d[21]], 'ability': [d[22], d[23]], 'color': d[25]}

def learnset(d):
    out = []
    for i in range(0, len(d) - 1, 2):
        v = struct.unpack_from('<H', d, i)[0]
        if v == 0xFFFF: break
        out.append((v >> 9, v & 0x1FF))
    return out

def evos(d):
    out = []
    for i in range(0, min(len(d), 42) - 5, 6):
        m, prm, t = struct.unpack_from('<HHH', d, i)
        if m: out.append((m, prm, t))
    return out

def trdata(d):
    if len(d) < 20: return None
    items = list(struct.unpack_from('<4H', d, 4)); ai = struct.unpack_from('<I', d, 12)[0]
    return {'flags': d[0], 'class': d[1], 'n': d[3], 'items': items, 'ai': ai, 'double': d[16]}

def trpoke(d, flags, n):
    base = 6 + (2 if flags & 2 else 0) + (8 if flags & 1 else 0)
    for extra in (2, 0):                       # 하트골드는 볼 캡슐 2바이트가 붙는다
        size = base + extra
        if n and len(d) >= size * n and len(d) - size * n < size:
            out = []
            for k in range(n):
                o = k * size
                lv, sp = struct.unpack_from('<HH', d, o + 2)
                p = o + 6; item = None; moves = None
                if flags & 2: item = struct.unpack_from('<H', d, p)[0]; p += 2
                if flags & 1: moves = list(struct.unpack_from('<4H', d, p)); p += 8
                out.append({'lv': lv, 'sp': sp & 0x3FF, 'form': sp >> 10, 'iv': d[o], 'item': item, 'moves': moves})
            return out, size
    return None, None

def detect_space(MSG, CM, share=0.2):
    """한글 아닌 글자 중 가장 흔한 것을 띄어쓰기로 보고 글자표에 넣음 → (부호, 비율) 또는 None"""
    freq = collections.Counter(); between = collections.Counter()
    for _, ent in MSG:
        for e in ent:
            for j, c in enumerate(e):
                if c == 0xFFFF or CM.is_hangul(c) or c in SPECIAL or c >= 0xF000: continue
                freq[c] += 1
                if 0 < j < len(e) - 1 and CM.is_hangul(e[j - 1]) and CM.is_hangul(e[j + 1]): between[c] += 1
    total = sum(freq.values()) or 1
    if not freq: return None
    sp, n = freq.most_common(1)[0]
    # 띄어쓰기라면 한글과 한글 사이에 자주 나와야 한다(변수 명령·문장부호와 구별)
    if n / total <= share or between[sp] < 0.25 * n: return None     # 디지골드는 0.29 (집 보고 10/12)
    CM.extra[sp] = ' '; CM.rev[' '] = sp
    return sp, n / total

def infer_charmap(MSG, dnames=()):
    """알려진 이름(포켓몬 1·2세대 + 설계 디지몬)과 글자 간격이 맞는 자리를 투표 → (Charmap, 종 이름 파일 번호, 투표) 또는 None"""
    known = [k for k in set(KNOWN_POKEMON) | dnames if len(k) >= 2]
    votes = collections.Counter(); where = collections.Counter()
    for fi, (_, ent) in enumerate(MSG):
        if not (300 <= len(ent) <= 1600): continue
        lens = collections.defaultdict(list)
        for e in ent:
            body = e[:-1] if e and e[-1] == 0xFFFF else e
            if 2 <= len(body) <= 8: lens[len(body)].append(body)
        for k in known:
            for mode in ('ks', 'uni'):
                try: ids = [KS_INDEX[c] for c in k] if mode == 'ks' else [ord(c) - 0xAC00 for c in k]
                except KeyError: continue
                for body in lens.get(len(k), []):
                    base = body[0] - ids[0]
                    if all(body[j] - ids[j] == base for j in range(1, len(k))):
                        votes[(mode, base)] += 1; where[(mode, base, fi)] += 1
    if not votes: return None
    (mode, base), nv = votes.most_common(1)[0]
    NAMEF = max((n, fi) for (m2, b2, fi), n in where.items() if (m2, b2) == (mode, base))[1]
    return Charmap(mode, base), NAMEF, votes

# ======================================================================= 본체
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('--out', default='hg1_out'); ap.add_argument('--quick', action='store_true')
    A = ap.parse_args()
    os.makedirs(os.path.join(A.out, 'texts'), exist_ok=True)
    t0 = time.time()
    raw = open(A.rom, 'rb').read()
    rom = NDS(raw)
    say('==', VERSION)
    say('롬: 제목 %s 코드 %s (IPKK=하트골드 한국, IPGK=소울실버 한국) 크기 %.1fMB 사용 끝 0x%X 파일 %d' %
        (rom.title, rom.code, len(raw) / 1048576, rom.used_end(), rom.nfiles))
    say('롬 sha1:', hashlib.sha1(raw).hexdigest())
    N = {}
    say('\n== NARC')
    for k, p in NARC_PATHS.items():
        try:
            N[k] = NARC(rom.get(p)); say('%-10s %s 파일 %d' % (k, p, len(N[k].files)))
        except Exception as e:
            say('%-10s %s 실패: %s' % (k, p, e))
    if 'msg' not in N or 'personal' not in N:
        say('실패: 글 또는 능력치 NARC 를 못 읽음 — 경로가 다른 개조판일 수 있음. 롬 안 a/ 목록:')
        say(sorted(x for x in rom.paths if x.startswith('a/'))[:80]); return finish(A, t0)

    # ---------------- 글 풀기
    MSG = []; bad = 0
    for f in N['msg'].files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append((0, [])); bad += 1
    say('글 파일 %d (풀기 실패 %d)' % (len(MSG), bad))

    # ---------------- 한글 부호표 추정: 알려진 이름(포켓몬 1·2세대 + 내 설계 디지몬)과 글자 간격이 맞는 자리를 투표로 찾음
    design = load_design()
    dnames = {s['ko'] for s in design['species']} if design else set()
    res = infer_charmap(MSG, dnames)
    if res is None:
        say('실패: 알려진 이름을 하나도 못 찾음 — 글자표가 완성형·현대 한글 순서가 아님. charstats 를 보고 다시 잡아야 함')
        return finish(A, t0)
    CM, NAMEF, votes = res; mode, base = CM.mode, CM.base; nv = votes.most_common(1)[0][1]
    NAMES = [CM.dec(e) for e in MSG[NAMEF][1]]
    say('\n== 글자표: %s 순서, 「가」=0x%04X (알려진 이름 %d개 일치, 2등 후보 %s)' % ('완성형 2350자' if mode == 'ks' else '현대 한글 11172자',
        base, nv, votes.most_common(2)[1:] or '없음'))
    hit = sum(1 for x in NAMES if x in dnames); clean = sum(1 for x in NAMES if x and '{' not in x)
    say('종 이름 파일 msg %d: 항목 %d, 깨끗한 이름 %d, 내 설계 디지몬 이름과 같은 것 %d' % (NAMEF, len(NAMES), clean, hit))
    if CM.mode == 'ks':
        hi = sum(1 for _, ent in MSG for e in ent for c in e if CM.base + len(KS) <= c < CM.base + 11172)
        say('완성형 범위 바로 뒤 부호 쓰임: %d (많으면 확장 글자표를 쓰는 개조판)' % hi)

    freq = collections.Counter(); ctx = {}
    for fi, (_, ent) in enumerate(MSG):
        for e in ent:
            for j, c in enumerate(e):
                if c != 0xFFFF and not CM.is_hangul(c) and c not in SPECIAL:
                    freq[c] += 1
                    if c not in ctx: ctx[c] = (fi, CM.dec(e[max(0, j - 6):j + 7]))
    with open(os.path.join(A.out, 'charstats.txt'), 'w', encoding='utf-8') as f:
        for c, n in freq.most_common(400): f.write('%04X\t%d\tmsg%d\t%s\n' % (c, n, ctx[c][0], ctx[c][1]))
    say('한글 아닌 부호 종류 %d (charstats.txt). 흔한 12개: %s' % (len(freq), ' '.join('%04X:%d' % x for x in freq.most_common(12))))

    # ---------------- 표 찾기·글 덤프
    def find_file(count_ok):
        c = []
        for fi, (_, ent) in enumerate(MSG):
            if ent and count_ok(len(ent)):
                ds = [CM.dec(e) for e in ent]
                hang = sum(1 for x in ds if x and '{' not in x[:2]) / len(ds)
                avg = sum(len(x) for x in ds) / len(ds)
                c.append((hang > 0.5, -avg, fi))
        c.sort(reverse=True)
        return c[0][2] if c else None
    nper = len(N['personal'].files)
    MOVEF = find_file(lambda n: 467 <= n <= 470)
    ITEMF = find_file(lambda n: 530 <= n <= 545)
    TRNF = find_file(lambda n: 'trdata' in N and abs(n - len(N['trdata'].files)) <= 1)
    CLSF = None                                       # 직업 이름표: 특성 표(124개)와 개수가 비슷해서 낱말로 고름(10/13 집 보고: 직업 칸에 「마중물」 등 특성이 찍혔음)
    CLS_WORDS = ('관장', '챔피언', '사천왕', '간부', '반바지', '아가씨', '기모노', '로켓', '엘리트', '트레이너')
    best = None
    for fi, (_, ent) in enumerate(MSG):
        if not ent or not (100 <= len(ent) <= 140): continue
        ds = [CM.dec(e) for e in ent]
        if any(x in ('맹화', '급류', '심록') for x in ds): continue
        sc = sum(1 for x in ds for w in CLS_WORDS if w in x)
        if sc and (best is None or sc > best[0]): best = (sc, fi)
    CLSF = best[1] if best else find_file(lambda n: 120 <= n <= 135)
    PLACEF = find_file(lambda n: 270 <= n <= 290)
    say('\n== 표 위치(추정): 종 이름 msg %s, 기술 %s, 도구 %s, 트레이너 이름 %s, 직업 %s, 지명 %s' % (NAMEF, MOVEF, ITEMF, TRNF, CLSF, PLACEF))
    def names_of(fi): return [CM.dec(e) for e in MSG[fi][1]] if fi is not None else []
    MOVES, ITEMS, TRN, CLS, PLACES = names_of(MOVEF), names_of(ITEMF), names_of(TRNF), names_of(CLSF), names_of(PLACEF)
    def nm(lst, i): return lst[i] if lst and 0 <= i < len(lst) else '#%d' % i
    say('기술 1~12:', ' / '.join(MOVES[1:13]))
    say('직업 앞 20:', ' / '.join(CLS[:20]))
    open(os.path.join(A.out, 'classes.tsv'), 'w', encoding='utf-8').write('번호\t직업\n' + ''.join('%d\t%s\n' % (i, c) for i, c in enumerate(CLS)))   # 10/14: 트레이너 그림 짝 맞추기용
    say('지명 앞 20:', ' / '.join(PLACES[:20]))
    for k in ('몸통박치기', '울음소리', '포켓몬', '디지몬', '체육관', '관장', '배지', '로켓단', '오박사', '공박사'):
        say('「%s」 나오는 글 수: %d' % (k, sum(1 for _, ent in MSG for e in ent if k in CM.dec(e))))
    if not A.quick:
        for fi, (seed, ent) in enumerate(MSG):
            with open(os.path.join(A.out, 'texts', 'msg_%04d.txt' % fi), 'w', encoding='utf-8') as f:
                for j, e in enumerate(ent): f.write('%d\t%s\n' % (j, CM.dec(e)))
        say('글 전체 → texts/ (%d 파일)' % len(MSG))

    # ---------------- 종 표
    say('\n== 종')
    P = [personal(f) for f in N['personal'].files]
    L = [learnset(f) for f in N['learn'].files] if 'learn' in N else []
    E = [evos(f) for f in N['evo'].files] if 'evo' in N else []
    with open(os.path.join(A.out, 'species.tsv'), 'w', encoding='utf-8') as f:
        f.write('번호\t이름\t타입\tHP 공 방 스 특공 특방\t포획\t경험\t성장\t특성\t진화\t기술\n')
        for i, p in enumerate(P):
            if not p: continue
            ev = ' ; '.join('%s(%d)→%s' % (EVO_METHOD.get(m, str(m)), prm, nm(NAMES, t)) for m, prm, t in (E[i] if i < len(E) else []))
            lr = ' '.join('%d:%s' % (lv, nm(MOVES, mv)) for lv, mv in (L[i] if i < len(L) else []))
            f.write('%d\t%s\t%s\t%s\t%d\t%d\t%d\t%s\t%s\t%s\n' % (i, nm(NAMES, i), '/'.join(TYPES[t] if t < len(TYPES) else str(t) for t in p['type']),
                    ' '.join(map(str, p['stats'])), p['catch'], p['exp'], p['growth'], p['ability'], ev, lr))
    mon = [i for i, x in enumerate(NAMES) if x.endswith('몬')]
    say('능력치 %d, 이름 %d, 「몬」 끝 이름 %d (첫 번호 %s, 마지막 %s)' % (nper, len(NAMES), len(mon), mon[:1], mon[-1:]))
    say('이름 1~40:', ' / '.join('%d:%s' % (i, NAMES[i]) for i in range(1, min(41, len(NAMES)))))

    # ---------------- 트레이너
    if 'trdata' in N and 'trpoke' in N:
        say('\n== 트레이너')
        sizes = collections.Counter(); tops = []
        with open(os.path.join(A.out, 'trainers.tsv'), 'w', encoding='utf-8') as f:
            f.write('번호\t직업\t이름\t도구\tAI\t더블\t파티\n')
            for i, d in enumerate(N['trdata'].files):
                t = trdata(d)
                if not t: continue
                party, size = trpoke(N['trpoke'].files[i], t['flags'], t['n']) if i < len(N['trpoke'].files) else (None, None)
                sizes[size] += 1
                ps = ' , '.join('Lv%d %s%s%s' % (m['lv'], nm(NAMES, m['sp']), '@' + nm(ITEMS, m['item']) if m['item'] else '',
                                ' [' + '/'.join(nm(MOVES, x) for x in m['moves'] if x) + ']' if m['moves'] else '') for m in (party or [])) or '(못 읽음)'
                f.write('%d\t%s\t%s\t%s\t%x\t%d\t%s\n' % (i, nm(CLS, t['class']), nm(TRN, i), ','.join(nm(ITEMS, x) for x in t['items'] if x), t['ai'], t['double'], ps))
                if party: tops.append((max(m['lv'] for m in party), i, t['class']))
        say('트레이너 %d, 파티 항목 크기 분포 %s' % (len(N['trdata'].files), dict(sizes)))
        say('레벨 높은 10:', ', '.join('%d(%s %s Lv%d)' % (i, nm(CLS, c), nm(TRN, i), lv) for lv, i, c in sorted(tops, reverse=True)[:10]))

    # ---------------- 야생(배치 추정: 걷기 낮 12칸)
    if 'enc' in N:
        ok = 0
        with open(os.path.join(A.out, 'encounters.tsv'), 'w', encoding='utf-8') as f:
            f.write('번호\t걷기 비율\t레벨 12\t낮 12칸(추정 배치)\n')
            for i, d in enumerate(N['enc'].files):
                if len(d) < 0x5C: continue
                day = struct.unpack_from('<12H', d, 0x2C)
                if all(x < nper for x in day): ok += 1
                f.write('%d\t%d\t%s\t%s\n' % (i, d[0], list(d[8:20]), ' / '.join(nm(NAMES, x) for x in day)))
        say('\n== 야생 파일 %d, 낮 칸이 모두 종 범위 안인 파일 %d (배치 추정이 맞으면 거의 전부)' % (len(N['enc'].files), ok))

    # ---------------- 필드 그림(따라다니기)
    if 'mmodel' in N:
        sz = collections.Counter(len(f) for f in N['mmodel'].files)
        say('\n== 필드 그림 a/0/8/1: 파일 %d, 크기 상위 %s, 머리글 %s' % (len(N['mmodel'].files), sz.most_common(5),
            collections.Counter(bytes(f[:4]) for f in N['mmodel'].files).most_common(4)))

    # ---------------- 전투 그림
    if 'pokegra' in N and not A.quick:
        g = N['pokegra'].files; nsp = len(g) // 6
        sh = Sheet(20, (nsp + 19) // 20); modes = collections.Counter(); empty = 0
        for i in range(nsp):
            fs = g[i * 6:(i + 1) * 6]
            pal = next((nclr(f) for f in fs if f[:4] == b'RLCN'), None)
            rows = None
            for k in (3, 2, 1, 0):
                if k < len(fs) and fs[k][:4] == b'RGCN':
                    rows, md = ncgr_rows(fs[k]); modes[md] += 1
                    if rows: break
            if rows: sh.put(i, [r[:80] for r in rows], pal)
            else: empty += 1
            sh.label(i, i)
        sh.save(os.path.join(A.out, 'front_sheet.png'))
        say('\n== 전투 그림 %d종 → front_sheet.png (칸 아래 숫자 = 종 번호, 그림 없음 %d, 복호 방식 %s)' % (nsp, empty, dict(modes)))
        # 뒷모습도 한 장으로(10/12: 디지골드 뒷모습의 출처를 알아보려고 — DS 디지몬 스토리에는 뒷모습이 없음)
        shb = Sheet(20, (nsp + 19) // 20); emptyb = 0
        for i in range(nsp):
            fs = g[i * 6:(i + 1) * 6]
            pal = next((nclr(f) for f in fs if f[:4] == b'RLCN'), None); rows = None
            for k in (1, 0):
                if k < len(fs) and fs[k][:4] == b'RGCN':
                    rows, _ = ncgr_rows(fs[k])
                    if rows: break
            if rows: shb.put(i, [r[:80] for r in rows], pal)
            else: emptyb += 1
            shb.label(i, i)
        shb.save(os.path.join(A.out, 'back_sheet.png'))
        say('== 뒷모습 %d종 → back_sheet.png (그림 없음 %d)' % (nsp, emptyb))

    say('\n== 쓰기 시험')
    selftest(A, rom, raw, N, MSG, CM, NAMEF, NAMES)

    if design:
        say('\n== 내 설계(GBC 205종)와 대조')
        idx = collections.defaultdict(list)
        for i, x in enumerate(NAMES): idx[x.replace(' ', '')].append(i)
        found, miss = [], []
        with open(os.path.join(A.out, 'match.tsv'), 'w', encoding='utf-8') as f:
            f.write('설계 이름\t단계\t쓰임\t개조판 번호\n')
            for s in design['species']:
                hitn = idx.get(s['ko'].replace(' ', ''), []) or idx.get(s['rom'].replace(' ', ''), [])
                f.write('%s\t%s\t%s\t%s\n' % (s['ko'], s['grade'], s['use'], ','.join(map(str, hitn)) or '없음'))
                (found if hitn else miss).append(s['ko'])
        say('개조판에 이름이 있는 종 %d / 없는 종 %d' % (len(found), len(miss)))
        say('없는 종:', ' '.join(miss))
        dset = {s['ko'] for s in design['species']} | {s['rom'] for s in design['species']}
        only = ['%d:%s' % (i, x) for i, x in enumerate(NAMES) if x.endswith('몬') and x not in dset and x not in KNOWN_POKEMON]
        say('개조판에만 있는 「몬」 이름(이름 표기가 달라 못 맞춘 것 포함):', ' '.join(only))
    finish(A, t0)

def selftest(A, rom, raw, N, MSG, CM, NAMEF, NAMES):
    def ok(name, cond, extra=''):
        say('%s %s %s' % ('OK' if cond else '실패:', name, extra))
    for k, n in N.items():
        b = n.build(); same = b == rom.get(NARC_PATHS[k])
        ok('NARC %s 다시 만들기' % k, NARC(b).files == n.files, '(바이트까지 같음)' if same else '(내용 같음, 바이트 다름)')
    diff = sum(1 for fi, f in enumerate(N['msg'].files) if MSG[fi][1] and msg_encode(*MSG[fi]) != f)
    ok('글 암호화 왕복', diff == 0, '(다른 파일 %d)' % diff)
    bad = 0; first = None
    for fi, (_, ent) in enumerate(MSG):
        for e in ent:
            body = e[:-1] if e and e[-1] == 0xFFFF else e
            if 0xFFFF in body: continue
            try:
                if CM.enc(CM.dec(e))[:-1] != body: bad += 1; first = first or (fi, CM.dec(e)[:30])
            except Exception as ex:
                bad += 1; first = first or (fi, str(ex))
    ok('부호표 왕복', bad == 0, '(어긋난 항목 %d, 첫 예 %s)' % (bad, first))
    r2 = NDS(raw); r2.put('a/0/2/7', N['msg'].build())
    ok('롬에 같은 글 NARC 다시 쓰기', bytes(r2.d[:0x15E]) + bytes(r2.d[0x160:]) == raw[:0x15E] + raw[0x160:], '(머리말 검사값 말고는 롬이 그대로면 OK)')
    tgt = next((i for i, x in enumerate(NAMES) if x == '아구몬'), None)
    if tgt is None: tgt = next((i for i, x in enumerate(NAMES) if x.endswith('몬')), None)
    if tgt is None: return
    seed, ent = MSG[NAMEF]; ent = [list(e) for e in ent]
    ent[tgt] = CM.enc('시험몬')
    nn = NARC(N['msg'].build()); nn.files = list(nn.files); nn.files[NAMEF] = msg_encode(seed, ent)
    r3 = NDS(raw); how = r3.put('a/0/2/7', nn.build())
    _, ent4 = msg_decode(NARC(NDS(bytes(r3.d)).get('a/0/2/7')).files[NAMEF])
    ok('종 이름 바꾸기(%d번 %s → 시험몬, %s)' % (tgt, NAMES[tgt], how), CM.dec(ent4[tgt]) == '시험몬')
    open(os.path.join(A.out, 'test_name.nds'), 'wb').write(bytes(r3.d))
    patch = bps_make(raw, bytes(r3.d))
    open(os.path.join(A.out, 'test_name.bps'), 'wb').write(patch)
    ok('BPS 패치 만들기·적용 확인', bps_apply(raw, patch) == bytes(r3.d), '(패치 %d바이트)' % len(patch))

def load_design():
    if '@@' in DESIGN_B64:      # 묶음판: 같은 폴더의 design.json
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design.json')
        try: return json.load(open(p, encoding='utf-8'))
        except Exception as e: say('설계 자료(design.json) 읽기 실패:', e); return None
    try:
        b = base64.b64decode(''.join(DESIGN_B64.split()))
        if hashlib.sha1(b).hexdigest() != DESIGN_SHA1:
            say('실패: 설계 자료가 복사 중에 깨짐(sha1 다름) — 붙여넣기를 다시 해 주세요'); return None
        return json.loads(zlib.decompress(b).decode('utf-8'))
    except Exception as e:
        say('설계 자료 읽기 실패:', e); return None

def finish(A, t0=None):
    if t0: say('\n걸린 시간 %.0f초' % (time.time() - t0))
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')
    zp = os.path.abspath(A.out).rstrip('/\\') + '.zip'
    base = os.path.dirname(os.path.abspath(A.out))
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, fs in os.walk(A.out):
            for fn in fs:
                if fn.endswith('.nds'): continue
                full = os.path.join(root, fn); z.write(full, os.path.relpath(os.path.abspath(full), base))
    print('\n끝 — %s 를 설계자에게 보내 주세요. (시험 롬 test_name.nds 는 폰 확인용, 보내지 않음)' % zp)

DESIGN_SHA1 = '@@SHA1@@'
DESIGN_B64 = """
@@B64@@
"""

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        print('실패: 위 오류 전체를 그대로 보고')
        sys.exit(1)
