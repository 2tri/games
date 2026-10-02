"""디지몬스터 → '내 버전' 패치 만들기
  python3 patch.py            # work/base.gbc (사용자가 준 디지몬스터 롬) → work/myver.gbc, work/myver.ips
롬·패치 결과는 저장소에 올리지 않는다. 이 파일과 우리 그림·자료만 올린다.

내 버전 v0.1 내용
 1. 진화 확장 (금 진화 엔진에 새 진화 종류 6~10 추가)
    6 유대 높음: 레벨 ≥ L 이고 친밀도(유대) ≥ 100  → 본래 진화
    7 유대 낮음: 레벨 ≥ L 이고 친밀도 < 40          → 실패 진화
    8 자기 문장: 레벨 ≥ L 이고 그 디지몬의 문장(배지)이 있음 → 문장 진화
    9 암흑 진화: 레벨 ≥ L 이고 문장은 있지만 자기 문장은 없음
   10 아무 문장: 레벨 ≥ L 이고 문장(배지)이 하나라도 있음
    (진화 장면에서 B로 멈추는 것은 금 그대로)
 2. 문장 = 배지 8개: 사랑0(비상) 지식1(호일) 순수2(꼭두) 빛3(유빈) 우정4(규리) 용기5(사도) 성실6(류옹) 희망7(이향)
 3. 포획: 성숙기 이상 디지몬은 몬스터볼로 못 잡음 (디지몬 RPG처럼 유년기·성장기만)
 4. 롬에 없던 코로몬 추가 (꼬리선 자리, 29번 도로 야생) → Lv11 아구몬, 아이콘·울음소리·도감
 5. 디지몬스터 버그: 메탈가루몬 진화 목록 끝 표시 없음 → 고침 (Lv39에 팔몬이 되던 문제)
"""
import os, re, sys, json, struct
import numpy as np
from PIL import Image
import dmrom, gblz, krtext, encounters, remap
from dmrom import addr, bankptr

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
HIGH_BOND, LOW_BOND = 100, 40
CREST_BIT = {'사랑': 0, '지식': 1, '순수': 2, '빛': 3, '우정': 4, '용기': 5, '성실': 6, '희망': 7}
NUM_SP = dmrom.NUM
MOVES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'moves.json')))      # 금판 기술 이름 → 번호
TYPES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'slots.json')))['types']
def moves_by_name(lst): return [(lv, MOVES[nm]) for lv, nm in lst]
ICON_JIGGLYPUFF = 2                      # 둥근 분홍 아이콘 (constants/icon_constants.asm)
LV, ITEM, TRADE, HAPPY, STAT, BOND_HI, BOND_LO, CREST, DARK, ANYCREST = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

# ── 빈 곳 나눠 쓰기 ──
class Space:
    def __init__(self, rom):
        self.free = {}                      # bank → [시작 주소(뱅크 안), 끝]
        for bank, start, n, fill in rom.free_runs(0x80):
            self.free[bank] = [start + 0x20, 0x8000]       # 앞쪽 0x20 은 여유로 남김
    def take(self, n, bank=None, banks=None):
        for b in ([bank] if bank is not None else banks):
            s, e = self.free.get(b, (0, 0))
            if e - s >= n:
                self.free[b][0] = s + n; return b, s
        raise MemoryError('빈 곳 없음 %d' % n)
PIC_BANKS = [0x75, 0x76, 0x77, 0x7c, 0x7d]

# ── 아주 작은 어셈블러 (필요한 명령만) ──
class Asm:
    J = {None: 0xC3, 'nz': 0xC2, 'z': 0xCA, 'nc': 0xD2, 'c': 0xDA}
    R = {None: 0x18, 'nz': 0x20, 'z': 0x28, 'nc': 0x30, 'c': 0x38}
    def __init__(self, org): self.org, self.b, self.lab, self.fix = org, bytearray(), {}, []
    def here(self): return self.org + len(self.b)
    def L(self, n): self.lab[n] = self.here()
    def db(self, *x): self.b += bytes(x)
    def w(self, v): self.b += struct.pack('<H', v)
    def ref(self, t):
        if isinstance(t, str): self.fix.append(('abs', len(self.b), t)); self.w(0)
        else: self.w(t)
    def jp(self, t, cc=None): self.db(self.J[cc]); self.ref(t)
    def call(self, t): self.db(0xCD); self.ref(t)
    def jr(self, t, cc=None): self.db(self.R[cc]); self.fix.append(('rel', len(self.b), t)); self.db(0)
    def ld_a_mem(self, a): self.db(0xFA); self.w(a)
    def cp(self, n): self.db(0xFE, n)
    def build(self):
        for kind, pos, name in self.fix:
            t = self.lab[name]
            if kind == 'abs': self.b[pos:pos + 2] = struct.pack('<H', t)
            else:
                off = t - (self.org + pos + 1)
                assert -128 <= off < 128, name; self.b[pos] = off & 255
        return bytes(self.b)

def find(d, pat, what):
    i = d.find(bytes.fromhex(pat))
    if i < 0 or d.find(bytes.fromhex(pat), i + 1) >= 0: raise SystemExit('코드 위치를 하나로 못 찾음: ' + what)
    return i

# ── 그림 넣기 ──
def png_to_idx(path, maxw, maxh):
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).astype(int)
    h, w = a.shape[:2]; idx = np.zeros((h, w), np.uint8)
    op = a[..., 3] > 128; L = a[..., :3] @ np.array([.299, .587, .114])
    cols = sorted({tuple(a[y, x, :3]) for y, x in zip(*np.nonzero(op))}, key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
    white = [c for c in cols if min(c) > 230]; black = [c for c in cols if max(c) < 60]
    mid = [c for c in cols if c not in white and c not in black]
    pal = [mid[0] if mid else (200, 200, 200), mid[-1] if len(mid) > 1 else (120, 120, 120)]
    for y in range(h):
        for x in range(w):
            if not op[y, x]: continue
            c = tuple(a[y, x, :3])
            if c in white: idx[y, x] = 0
            elif c in black: idx[y, x] = 3
            else: idx[y, x] = 1 + int(np.argmin([sum((np.array(c) - np.array(p)) ** 2) for p in pal]))
    return idx, pal

def to_gb_pic(idx, tw, th):
    """색번호 그림 → 금판 그림 바이트 (가운데 아래 맞춤, 세로 줄 먼저)"""
    H, W = th * 8, tw * 8; c = np.zeros((H, W), np.uint8); h, w = idx.shape
    if h > H or w > W: raise ValueError('그림이 큼 %s > %s' % (idx.shape, (H, W)))
    oy, ox = H - h, (W - w) // 2; c[oy:oy + h, ox:ox + w] = idx
    out = bytearray()
    for tx in range(tw):
        for ty in range(th):
            for r in range(8):
                row = c[ty * 8 + r, tx * 8:tx * 8 + 8]
                lo = sum(((v & 1) << (7 - i)) for i, v in enumerate(row)); hi = sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))
                out += bytes([lo, hi])
    return bytes(out)

def rgb555(c): return (c[0] * 31 // 255) | (c[1] * 31 // 255) << 5 | (c[2] * 31 // 255) << 10

class Patch:
    def __init__(self, base):
        self.r = dmrom.Rom(base); self.d = self.r.d; self.sp = Space(self.r); self.log = []
    def put(self, a, data): self.d[a:a + len(data)] = data
    # 이름 (5글자까지)
    def name(self, no, s):
        e = krtext.encode(s)
        if len(e) > 10: raise ValueError('이름이 김 (5글자): ' + s)
        self.put(self.r.names + 10 * (no - 1), e + b'\x50' * (10 - len(e)))
    def stats(self, no, **kw):
        a = self.r.bs + 0x20 * (no - 1); e = self.d
        keys = {'hp': 1, 'atk': 2, 'def': 3, 'spd': 4, 'sat': 5, 'sdf': 6, 'type1': 7, 'type2': 8, 'catch': 9, 'exp': 10, 'pic_size': 17, 'growth': 22}
        for k, v in kw.items(): e[a + keys[k]] = v
    def palette(self, no, c1, c2):
        a = self.r.pal + 8 * no
        self.put(a, struct.pack('<4H', rgb555(c1), rgb555(c2), rgb555(c1), rgb555(c2)))
    def pic(self, no, front_png, back_png):
        fi, pal = png_to_idx(front_png, 56, 56); bi, _ = png_to_idx(back_png, 48, 48)
        size = 7 if max(fi.shape) > 48 else 6 if max(fi.shape) > 40 else 5
        fdat = gblz.compress(to_gb_pic(fi, size, size)); bdat = gblz.compress(to_gb_pic(bi, 6, 6))
        ents = []
        for dat in (fdat, bdat):
            bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat); ents += [bank, p & 255, p >> 8]
        self.put(self.r.pics + 6 * (no - 1), bytes(ents))
        self.stats(no, pic_size=size * 0x11)
        self.palette(no, *pal)
    # 메뉴 아이콘 (ReadMonMenuIcon: cp EGG / jr z / dec a / ld hl, MonMenuIcons …)
    def icon(self, no, icon_id):
        d = bytes(self.d); m = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', d, re.S)
        self.put(addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')) + no - 1, bytes([icon_id]))
    # 울음소리 (LoadCry: ld a, BANK(PokemonCries) / rst Bankswitch / ld hl, PokemonCries / add hl,bc ×6) — 종류, 음높이, 길이
    def cry(self, no, idx, pitch, length):
        d = bytes(self.d); m = re.search(rb'\x3e(.)\xd7\x21(..)\x09\x09\x09\x09\x09\x09\x5e\x23\x56\x23\x2a', d, re.S)
        self.put(addr(m.group(1)[0], int.from_bytes(m.group(2), 'little')) + 6 * (no - 1), struct.pack('<3H', idx, pitch, length))
    def cry_of(self, no):
        d = bytes(self.d); m = re.search(rb'\x3e(.)\xd7\x21(..)\x09\x09\x09\x09\x09\x09\x5e\x23\x56\x23\x2a', d, re.S)
        a = addr(m.group(1)[0], int.from_bytes(m.group(2), 'little')) + 6 * (no - 1); return struct.unpack('<3H', d[a:a + 6])
    # 도감: 분류(형) · 키(0.1m) · 몸무게(0.1kg) · 3줄. 원래 자리 크기 안에서만 씀 (도감 글은 종 번호로 뱅크가 정해져 옮기기 어려움)
    def dex(self, no, kind, height, weight, lines):
        d = bytes(self.d)
        m = re.search(rb'\x21(..)\x78\x3d\x06\x00\x4f\x09\x09\x07\xe6\x01\xc6(.)\x47\x2a\x66\x6f\xc9', d, re.S)
        tab = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')); b0 = m.group(2)[0]
        ent = lambda sp: addr(b0 + ((sp - 1) >> 7), d[tab + 2 * (sp - 1)] | d[tab + 2 * (sp - 1) + 1] << 8)
        assert len(lines) == 3 and all(len(l) <= 16 for l in lines), '도감 글은 3줄, 줄마다 16자까지'
        e = krtext.encode(kind) + b'\x50' + bytes([height]) + struct.pack('<H', weight) + b'\x59'.join(krtext.encode(l) for l in lines) + b'\x50'
        room = min((ent(s) - ent(no) for s in range(1, NUM_SP + 1) if ent(s) > ent(no) and ent(s) // 0x4000 == ent(no) // 0x4000), default=0)
        if len(e) <= room:
            self.put(ent(no), e + bytes(room - len(e))); self.log.append('도감 %d번 %d/%d바이트' % (no, len(e), room)); return
        # 원래 자리가 모자라면 같은 뱅크의 빈 곳으로 옮기고 포인터를 바꿈 (도감 뱅크는 종 번호로 정해짐: 1~128 / 129~251)
        bank = ent(no) // 0x4000
        b, p = self.sp.take(len(e), bank=bank)
        self.put(addr(b, p), e); self.put(tab + 2 * (no - 1), struct.pack('<H', p))
        self.log.append('도감 %d번 %d바이트 → 빈 곳 %02X:%04X' % (no, len(e), b, p))
    # 글 한 덩이 바꾸기: a = 글자 시작(text 명령 0x00 다음). <DONE>/<PROMPT> 앞까지를 새 글로, 남는 자리는 빈칸(0x7f)
    def text_at(self, a, new):
        d = self.d; end = a
        while d[end] not in (0x5e, 0x5f):
            end += 2 if 1 <= d[end] <= 0x0b else 1          # 한글은 2바이트 (둘째 바이트가 0x5e 일 수 있음)
        e = krtext.encode_text(new)
        assert len(e) <= end - a, '글이 원래보다 김 (%d > %d): %s' % (len(e), end - a, new)
        self.put(a, e + b'\x7f' * (end - a - len(e)))
    # 대사 한 덩어리를 통째로 바꾸기 (texts.py 의 addr = text 명령 0x00 자리). new 는 <LINE>·<PARA>·<DONE> 등을 포함한 전체 글
    #   원래 자리에 들어가면 그대로 쓰고, 길면 빈 뱅크에 새로 쓴 뒤 원래 자리에 'text_far 새 주소 / text_end' 를 남김
    #   (금 대사가 원래 쓰는 방식이라 같은 뱅크 2바이트 주소로 가리키던 스크립트도 그대로 동작)
    def retext(self, a, new):
        d = self.d; assert d[a] == 0x00, '대사 시작이 아님 %X' % a
        end = a + 1
        while d[end] not in (0x5e, 0x5f, 0x50): end += 2 if 1 <= d[end] <= 0x0b else 1
        e = krtext.encode_text(new)
        assert e and e[-1] in (0x5e, 0x5f, 0x50), '끝 표시(<DONE>/<PROMPT>/@)로 끝나야 함'
        if len(e) <= end - a:
            self.put(a + 1, e + b'\x50' * (end - a - len(e))); return 'in'
        b, p = self.sp.take(len(e) + 1, banks=[0x7c, 0x7d, 0x77, 0x76, 0x75])
        self.put(addr(b, p), b'\x00' + e)
        self.put(a, bytes([0x16, p & 255, p >> 8, b, 0x50])); return 'far'
    # 스타팅: 공박사 연구소의 세 볼 스크립트 (pokepic X / cry X / … getmonname X / … givepoke X, 5) 종 바꾸기 → {새 종: 묻는 글 주소}
    def starters(self, mapping):
        d = bytes(self.d); texts = {}
        for old, new in mapping.items():
            a = re.search(bytes([0x56, old, 0x84, old, 0x00]), d).start(); seg = d[a:a + 80]
            for k in (1, 3, seg.index(bytes([0x40, old])) + 1, seg.index(bytes([0x2d, old, 5])) + 1):
                self.put(a + k, bytes([new]))
            k = seg.index(0x4d, 5)                                    # 첫 writetext = '…로 하겠니?' 글
            texts[new] = addr(a // 0x4000, seg[k + 1] | seg[k + 2] << 8) + 1
        return texts
    # 스타팅 고르는 물건: 공박사 연구소의 볼 3개만 '금 트로피' 필드 그림 칸(방 꾸미기에만 쓰임)으로 바꾸고 그 그림을 디지바이스로
    #   (볼 그림을 바꾸면 땅에 떨어진 아이템 볼까지 바뀌므로). png: 16×16, 투명 + 밝은·어두운 색 + 검정
    def digivice(self, png, sprite_id=0x5E, pal=5):
        d = bytes(self.d)
        m = re.search(rb'\xe5\x21(..)\x3d\x4f\x06\x00\x3e\x06\xcd..\x2a\x5f\x2a\x57', d, re.S)       # GetSprite: ld hl, OverworldSprites
        tab = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
        a = np.asarray(Image.open(png).convert('RGBA')).astype(int)
        idx = np.zeros((16, 16), int); op = a[..., 3] > 128; L = a[..., :3] @ np.array([.299, .587, .114])
        idx[op & (L >= 170)] = 1; idx[op & (L < 170) & (L >= 60)] = 2; idx[op & (L < 60)] = 3
        gfx = bytearray()
        for ty, tx in ((0, 0), (0, 1), (1, 0), (1, 1)):                    # 좌상·우상·좌하·우하
            for y in range(8):
                row = idx[ty * 8 + y, tx * 8:tx * 8 + 8]
                gfx += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(row)), sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
        b, p = self.sp.take(64, banks=[0x77, 0x7c, 0x7d, 0x76, 0x75]); self.put(addr(b, p), bytes(gfx))
        self.put(tab + 6 * (sprite_id - 1), bytes([p & 255, p >> 8, 64, b, 3, pal]))
        n = 0; i = d.find(b'\x54\x07\x0a')                                  # 볼 셋: SPRITE_POKE_BALL, y 3+4, x 6~8+4
        while i >= 0:
            if d[i + 13:i + 16] == b'\x54\x07\x0b' and d[i + 26:i + 29] == b'\x54\x07\x0c':
                for k in (0, 13, 26): self.put(i + k, bytes([sprite_id]))
                n += 1
            i = d.find(b'\x54\x07\x0a', i + 1)
        assert n == 1, '연구소 볼 셋을 못 찾음 (%d)' % n
        self.log.append('스타팅 고르는 물건 → 디지바이스 (%s)' % os.path.basename(png))
    # 트레이너가 데리고 있는 종 바꾸기 {옛 종: 새 종}
    def trainer_species(self, mapping):
        n = 0
        for t in self.r.trainers():
            for lv, sp, a in t['mons']:
                if sp in mapping: self.put(a, bytes([mapping[sp]])); n += 1
        return n
    # 새 디지몬 한 칸: 능력치는 앞뒤 단계의 평균, 나머지(속성·성장·기술머신)는 앞 단계 복사
    def new_mon(self, no, name, prev, nxt, art, kind, dex_lines, height, weight):
        a, p, q = self.r.bs + 0x20 * (no - 1), self.r.bs + 0x20 * (prev - 1), self.r.bs + 0x20 * (nxt - 1)
        self.put(a + 1, self.d[p + 1:p + 0x20])
        for k in range(1, 7): self.d[a + k] = (self.d[p + k] + self.d[q + k] + 1) // 2
        self.d[a + 10] = (self.d[p + 10] + self.d[q + 10]) // 2                # 경험치 수율
        self.name(no, name)
        f = os.path.join(WEB, 'art', art + '-f.png'); b = os.path.join(WEB, 'art', art + '-b.png')
        if not os.path.exists(f):
            f, b = os.path.join(WEB, 'art', 'placeholder-f.png'), os.path.join(WEB, 'art', 'placeholder-b.png')
            self.log.append('%s 그림 없음 → 임시 그림(물음표 알)' % name)
        self.pic(no, f, b)
        d = bytes(self.d); m = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', d, re.S)
        self.icon(no, d[addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')) + prev - 1])
        idx, pitch, length = self.cry_of(prev); self.cry(no, idx, max(0, pitch - 32), length + 32)
        self.dex(no, kind, height, weight, dex_lines)
    def evos(self, no, evos, moves=None):
        """진화·기술 목록을 새로 써서 뱅크 0x10 빈 곳에 두고 포인터를 바꿈. moves=None 이면 원래 기술 목록 유지"""
        old_ev, old_mv = self.r.evos_attacks(no)
        mv = old_mv if moves is None else moves
        blob = bytearray()
        for e in evos: blob += bytes(e)
        blob.append(0)
        for lv, m in mv: blob += bytes([lv, m])
        blob.append(0)
        bank = self.r.evos // 0x4000
        b, p = self.sp.take(len(blob), bank=bank); self.put(addr(b, p), blob)
        self.put(self.r.evos + 2 * (no - 1), struct.pack('<H', p))
    def raw_moves_after(self, no, n_evo_bytes):
        """끝 표시가 빠진 진화 목록 (디지몬스터 버그): 진화 n 바이트 뒤부터를 기술 목록으로 읽음"""
        bank = self.r.evos // 0x4000
        p = self.d[self.r.evos + 2 * (no - 1)] | self.d[self.r.evos + 2 * (no - 1) + 1] << 8
        a = addr(bank, p) + n_evo_bytes; mv = []
        while self.d[a]: mv.append((self.d[a], self.d[a + 1])); a += 2
        return mv

    # ── 진화 확장 코드 ──
    def evo_engine(self, crest_of):
        d = bytes(self.d)
        site = find(d, 'fae5d0beda2460cd8d60ca2460e511', 'EVOLVE_STAT 자리')
        bank = site // 0x4000
        # 원래 코드에서 주소 읽기
        LEVEL = d[site + 1] | d[site + 2] << 8                 # wTempMonLevel
        DONT1 = d[site + 5] | d[site + 6] << 8; DONT2 = DONT1 + 1
        EVERSTONE = d[site + 8] | d[site + 9] << 8
        hap = find(d, 'fae1d0fedcda', '친밀도 진화 자리'); HAPPY_RAM = d[hap + 1] | d[hap + 2] << 8
        prc = d.find(bytes.fromhex('fae5d0eafbd0'), site); PROCEED = 0x4000 + prc % 0x4000
        m = find(d, 'fa90d13d0600', '진화 전 종 번호'); OLDSP = d[m + 1] | d[m + 2] << 8
        bdg = find(d, 'fa30d647fa2fd64f', '배지'); BADGES = d[bdg + 5] | d[bdg + 6] << 8
        n_code = 140
        b, org = self.sp.take(n_code + 251, bank=bank)
        a = Asm(org)
        a.db(0x78); a.cp(STAT); a.jr('custom', 'nz')            # ld a,b / cp 5
        a.ld_a_mem(LEVEL); a.jp(0x4000 + (site + 3) % 0x4000)    # 원래 길로 (cp [hl] 부터)
        a.L('custom')
        a.ld_a_mem(LEVEL); a.db(0xBE); a.jp(DONT2, 'c')          # 레벨 모자람
        a.db(0x78)                                               # ld a,b (종류)
        a.cp(BOND_HI); a.jr('high', 'z'); a.cp(BOND_LO); a.jr('low', 'z')
        a.cp(CREST); a.jr('crest', 'z'); a.cp(DARK); a.jr('dark', 'z'); a.cp(ANYCREST); a.jr('any', 'z')
        a.jp(DONT2)
        a.L('high'); a.ld_a_mem(HAPPY_RAM); a.cp(HIGH_BOND); a.jp(DONT2, 'c'); a.jr('ok')
        a.L('low'); a.ld_a_mem(HAPPY_RAM); a.cp(LOW_BOND); a.jp(DONT2, 'nc'); a.jr('ok')
        a.L('any'); a.ld_a_mem(BADGES); a.db(0xA7); a.jp(DONT2, 'z'); a.jr('ok')
        a.L('crest'); a.call('own'); a.jp(DONT2, 'z'); a.jr('ok')
        a.L('dark'); a.ld_a_mem(BADGES); a.db(0xA7); a.jp(DONT2, 'z'); a.call('own'); a.jp(DONT2, 'nz')
        a.L('ok')
        a.call(EVERSTONE); a.jp(DONT2, 'z')                      # 변함없는 돌이면 안 함
        a.db(0x23); a.jp(PROCEED)                                # inc hl → 대상 종
        a.L('own')                                               # a = 배지 & 문장표[종-1] (z = 자기 문장 없음)
        a.db(0xE5); a.ld_a_mem(OLDSP); a.db(0x3D, 0x5F, 0x16, 0x00, 0x21); a.ref('table'); a.db(0x19)
        a.ld_a_mem(BADGES); a.db(0xA6, 0xE1, 0xC9)
        a.L('table')
        a.db(*[crest_of.get(no, 0) for no in range(1, 252)])
        code = a.build(); assert len(code) <= n_code + 251, len(code)
        self.put(addr(b, org), code)
        # 걸기: 원래 'ld a,[wTempMonLevel]' 3바이트 → jp 새 코드
        self.put(site, bytes([0xC3, org & 255, org >> 8]))
        self.log.append('진화 확장 코드 뱅크 %02X:%04X (%d바이트), 레벨 %04X 친밀도 %04X 배지 %04X 진화전 %04X 진행 %04X 안함 %04X' %
                        (b, org, len(code), LEVEL, HAPPY_RAM, BADGES, OLDSP, PROCEED, DONT2))

    # ── 포획: 잡기 확률이 0인 디지몬은 절대 안 잡힘 ──
    def catch_engine(self):
        d = bytes(self.d)
        site = find(d, '47ea90d1cd3b31b83e00', '포획 난수 자리')
        CATCH = d[find(d, 'fad1d147fad6d1', '포획률') + 1] | 0xd1 << 8
        bank = site // 0x4000
        RANDOM = d[site + 5] | d[site + 6] << 8
        b, org = self.sp.take(16, bank=bank)
        a = Asm(org)
        a.call(RANDOM); a.db(0xF5); a.ld_a_mem(CATCH); a.db(0xA7); a.jr('block', 'z'); a.db(0xF1, 0xC9)
        a.L('block'); a.db(0xF1, 0x3E, 0xFF, 0xC9)
        self.put(addr(b, org), a.build())
        self.put(site + 4, bytes([0xCD, org & 255, org >> 8]))
        self.log.append('포획 막기 코드 뱅크 %02X:%04X' % (b, org))

    def ips(self, path):
        base, new = self.r.base, bytes(self.d); out = bytearray(b'PATCH'); i = 0; n = len(new)
        while i < n:
            if base[i] == new[i]: i += 1; continue
            j = i
            while j < n and (base[j] != new[j] or (j + 1 < n and base[j + 1] != new[j + 1])) and j - i < 0xFFFF: j += 1
            if i == 0x454F46: i -= 1
            out += struct.pack('>I', i)[1:] + struct.pack('>H', j - i) + new[i:j]; i = j
        out += b'EOF'; open(path, 'wb').write(out); return len(out)

def build(base, out_rom, out_ips):
    P = Patch(base); r = P.r
    # 1·2 진화 확장 + 문장
    # 종 번호는 판마다 다를 수 있으므로 이름으로 찾는다 (2014판·2.0판 공통)
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    def S(nm):
        assert nm in N, '롬에 %s 없음' % nm
        return N[nm]
    # 6 어드벤처 완전체 빈칸: 그레이몬 → 메탈그레이몬 → 워그레이몬, 가루몬 → 워가루몬 → 메탈가루몬
    #   야생·트레이너·이벤트 어디에도 안 쓰이는 포켓몬 칸에 넣음. 그림이 아직 없으면 임시 그림(물음표 알)
    #   도감: 공식 도감(digimon.net) 프로필을 3줄로 줄임. 키·몸무게는 공식 값이 없어 임시
    MGR = N.get('메탈그레몬') or S('핫삼'); WGR = N.get('워가루몬') or S('링곰')
    P.new_mon(MGR, '메탈그레몬', S('그레이몬'), S('워그레이몬'), 'metalgreymon', '사이보그형', ['몸의 절반 이상을 기계화한', '디지몬. 공격력은 핵탄두', '한 발에 맞먹는다고 한다'], 42, 2800)
    P.new_mon(WGR, '워가루몬', S('가루몬'), S('메탈가루몬'), 'weregarurumon', '수인형', ['가루몬이 진화해 두 발로', '걷게 된 디지몬. 발차기와', '점프력이 강하다'], 21, 1100)
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    crest = {'그레이몬': '용기', '가루몬': '우정', '버드라몬': '사랑', '캅테리몬': '지식', '니드몬': '순수', '원뿔몬': '성실', '엔젤몬': '희망', '가트몬': '빛',
             '메탈그레몬': '용기', '워가루몬': '우정'}
    P.evo_engine({S(nm): 1 << CREST_BIT[c] for nm, c in crest.items()})
    # 8 디지몬스터 버그: 기술 목록이 (기술, 레벨) 순서로 뒤집혀 들어간 종 (워그레이몬 등) → 바로잡음
    #   금은 (레벨, 기술) 로 읽으므로 '레벨 108에 막치기' 같은 엉뚱한 값이 됨. 뒤집어 읽어 레벨이 1~100 오름차순이면 뒤집힌 것으로 봄
    fixed = {}
    # 홀리엔젤몬: 진화 목록이 두 번 들어가 둘째 목록이 기술로 읽힘 → 둘째 목록을 건너뜀
    HA = S('홀리엔젤몬'); ev, mv = r.evos_attacks(HA)
    if any(l > 100 for l, _ in mv):
        fixed[HA] = P.raw_moves_after(HA, 8); P.evos(HA, ev, fixed[HA]); P.log.append('홀리엔젤몬 진화 목록 겹침 고침')
    for no in range(1, dmrom.NUM + 1):
        ev, mv = r.evos_attacks(no)
        if no in fixed or all(1 <= l <= 100 for l, _ in mv): continue
        nev = sum(4 if e[0] == STAT else 3 for e in ev) + 1
        bank = r.evos // 0x4000; p = r.d[r.evos + 2 * (no - 1)] | r.d[r.evos + 2 * (no - 1) + 1] << 8
        a = addr(bank, p) + nev; sw = []
        while r.d[a] and r.d[a + 1]: sw.append((r.d[a + 1], r.d[a])); a += 2
        if sw and all(1 <= l <= 100 for l, _ in sw) and [l for l, _ in sw] == sorted(l for l, _ in sw):
            fixed[no] = sw; P.evos(no, ev, sw)
    P.log.append('기술 목록 뒤집힘 고침: %s' % ', '.join(r.name(n) for n in fixed if n != HA))
    # 성숙기 → 완전체: 자기 문장이면 원작 레벨보다 3~7 빠르게, 다른 문장만 있으면 원작 레벨 — 디지몬마다 진화 시점이 다르게 (원작 36·36·36·40·32·25)
    # 완전체 → 궁극체: 자기 문장 + Lv45·46 (애니에서 워프 진화는 마지막 무렵)
    def learn(no, *more):                      # 앞 단계 기술 + 다음 단계의 높은 레벨 기술, 레벨 순
        mv = list(fixed.get(no) or r.evos_attacks(no)[1])
        for m in more: mv += [x for x in (fixed.get(m) or r.evos_attacks(m)[1]) if x[0] > 30]
        return sorted(set(mv))
    P.evos(S('그레이몬'), [(CREST, 32, MGR), (ANYCREST, 36, MGR)])
    P.evos(MGR, [(CREST, 45, S('워그레이몬'))], learn(S('그레이몬'), S('워그레이몬')))
    P.evos(S('가루몬'), [(CREST, 33, WGR), (ANYCREST, 36, WGR)])
    P.evos(WGR, [(CREST, 46, S('메탈가루몬'))], learn(S('가루몬'), S('메탈가루몬')))
    P.evos(S('버드라몬'), [(CREST, 31, S('가루다몬')), (ANYCREST, 36, S('가루다몬'))])
    P.evos(S('캅테리몬'), [(CREST, 35, S('아트캅테몬')), (ANYCREST, 40, S('아트캅테몬')), (ITEM, 169, S('로제몬'))])   # 로제몬 갈래는 그대로
    P.evos(S('니드몬'), [(CREST, 29, S('릴리몬')), (ANYCREST, 32, S('릴리몬'))])
    P.evos(S('원뿔몬'), [(CREST, 34, S('쥬드몬')), (ANYCREST, 38, S('쥬드몬'))])           # 원래 통신 교환 진화라 혼자서는 못 했음
    P.evos(S('엔젤몬'), [(CREST, 25, S('홀리엔젤몬')), (ANYCREST, 30, S('홀리엔젤몬'))])
    # 성장기 → 성숙기: 유대
    P.evos(S('파피몬'), [(BOND_HI, 16, S('가루몬')), (LV, 16, S('우가몬'))])               # 유대 높음 가루몬, 아니면 우가몬
    P.evos(S('플롯트몬'), [(BOND_HI, 16, S('가트몬')), (LV, 16, S('위자몬'))])             # 유대 높음 가트몬, 아니면 위자몬
    # 5 디지몬스터 버그: 메탈가루몬 진화 목록 끝 표시 (깨져 있을 때만 — 올바른 진화 종류는 1~5)
    MG = S('메탈가루몬'); ev = r.evos_attacks(MG)[0]
    if any(not 1 <= e[0] <= 5 for e in ev):
        P.evos(MG, [ev[0]], P.raw_moves_after(MG, 3)); P.log.append('메탈가루몬 진화 목록 고침')
    # 4 코로몬: 롬에 없으면 아직 포켓몬인 꼬리선 자리(29번 도로 야생)에 넣음
    KORO = N.get('코로몬')
    if KORO is None:
        KORO = S('꼬리선')
        P.name(KORO, '코로몬')
        P.stats(KORO, hp=44, atk=40, **{'def': 35}, spd=38, sat=35, sdf=35, type1=0, type2=0, catch=255, exp=50, growth=0)
        P.pic(KORO, os.path.join(WEB, 'art', 'koromon-f.png'), os.path.join(WEB, 'art', 'koromon-b.png'))
        P.evos(KORO, [(LV, 11, S('아구몬'))], [(1, 33), (1, 45), (5, 145), (9, 44)])
        P.icon(KORO, ICON_JIGGLYPUFF)
        idx, _, _ = P.cry_of(S('아구몬')); P.cry(KORO, idx, 160, 150)          # 아구몬 울음을 높고 짧게
        # 공식 도감(digimon.net): 유년기Ⅱ, 렛서형, 필살기 거품. 키·몸무게는 공식 값이 없어 임시
        P.dex(KORO, '렛서형', 3, 30, ['솜털이 빠지고 몸이 커진', '소형 디지몬. 아직 싸울 수', '없지만 거품으로 위협한다'])
    # 7 스타팅: 불꽃 볼 → 아구몬, 물 볼 → 파피몬, 셋째 볼 → 브이몬(파워디지몬 주인공) (원래 길몬·레나몬·테리어몬)
    #   라이벌은 금처럼 내 것에 강한 쪽을 가져가므로, 트레이너 표의 세 줄을 그대로 바꿈 (3단계: 메탈그레이몬·워가루몬·황제드라몬)
    #   파닥몬은 공박사 조수가 주는 알 칸(원래 토게피)이라 알에서 나옴 — 토코몬 그림이 오면 알을 토코몬으로
    VM, XV, IM = S('브이몬'), S('엑스브이몬'), S('황제드라몬')
    TAM = {S('길몬'): S('아구몬'), S('그라우몬'): S('그레이몬'), S('듀크몬'): MGR,
           S('레나몬'): S('파피몬'), S('구미호몬'): S('가루몬'), S('샤크라몬'): WGR,
           S('테리어몬'): VM, S('가르고몬'): XV, S('래피드몬'): IM}
    T = P.starters({S('길몬'): S('아구몬'), S('레나몬'): S('파피몬'), S('테리어몬'): VM})
    P.text_at(T[S('아구몬')], '공박사『불꽃 디지몬<LINE>아구몬으로 하겠니!?')
    P.text_at(T[S('파피몬')], '공박사『물디지몬<LINE>파피몬이 마음에 드느냐!?')
    P.text_at(T[VM], '공박사『소룡디지몬<LINE>브이몬이 마음에 들었느냐!?')
    P.log.append('스타팅 → 아구몬·파피몬·브이몬, 트레이너 종 %d곳 바꿈' % P.trainer_species(TAM))
    dv = os.path.join(WEB, 'art', 'digivice.png')                     # 받은 그림 (16×16), 없으면 임시 그림
    P.digivice(dv if os.path.exists(dv) else os.path.join(WEB, 'art', 'digivice_temp.png'))
    # 10 브이몬 줄: 디지몬스터는 엑스브이몬·황제드라몬을 우파·누오 칸 능력치·기술(물대포·지진) 그대로 둠 → 스타팅답게 다시 잡음
    #   아머 진화(디지멘탈 도구)는 그대로, 애니에 안 나온 브이드라몬 갈래만 뺌. 레벨 진화는 다른 스타팅처럼 16
    P.evos(VM, [(ITEM, 23, S('번개드라몬')), (ITEM, 24, S('매그너몬')), (ITEM, 22, S('화염드라몬')), (LV, 16, XV)])
    P.stats(XV, hp=65, atk=85, **{'def': 70}, spd=80, sat=60, sdf=65, type1=TYPES['DRAGON'], type2=TYPES['FLYING'])
    P.evos(XV, [(LV, 40, IM)], moves_by_name([(1, 'TACKLE'), (1, 'LEER'), (1, 'QUICK_ATTACK'), (16, 'WING_ATTACK'), (22, 'DOUBLE_KICK'),
                                             (28, 'SLASH'), (34, 'OUTRAGE'), (40, 'HYPER_BEAM')]))
    P.stats(IM, hp=95, atk=115, **{'def': 90}, spd=90, sat=100, sdf=90, type1=TYPES['DRAGON'], type2=TYPES['FLYING'])
    P.evos(IM, [(ITEM, 8, S('황제팔라딘'))], moves_by_name([(1, 'WING_ATTACK'), (1, 'SLASH'), (1, 'OUTRAGE'), (40, 'ZAP_CANNON'),
                                                          (46, 'HYPER_BEAM'), (52, 'FLY')]))
    # 9 새 디지몬 칸 (slots.json): 그림(art/<id>-f.png·-b.png)이 있는 것만 넣음. PLACEHOLDER=1 이면 그림 없어도 물음표 알로 넣어 시험
    SL = json.load(open(os.path.join(HERE, 'slots.json')))
    egg = bytes(P.d).find(bytes([0x2e, S('파닥몬'), 5]))            # 공박사 조수의 알 (giveegg 종, 레벨)
    installed = {}
    for m in SL['mons']:
        f, b = (os.path.join(WEB, 'art', m['id'] + s_) for s_ in ('-f.png', '-b.png'))
        if not (os.path.exists(f) and os.path.exists(b)):
            if os.environ.get('PLACEHOLDER') != '1': continue
            f, b = os.path.join(WEB, 'art', 'placeholder-f.png'), os.path.join(WEB, 'art', 'placeholder-b.png')
        no = N.get(m['name']) or S(m['slot'])
        st = dict(zip(('hp', 'atk', 'def', 'spd', 'sat', 'sdf'), m['stats']))
        P.name(no, m['name'])
        P.stats(no, **st, type1=TYPES[m['type'][0]], type2=TYPES[m['type'][1]], exp=m['exp'], catch=m['catch'], growth=0)
        P.pic(no, f, b)
        P.evos(no, [(LV, lv, S(t)) for _, lv, t in m['evos']], moves_by_name(m['moves']))
        P.dex(no, *m['dex'])
        if m['grade'].startswith(('유년기', '유아기')): P.icon(no, ICON_JIGGLYPUFF)
        if m['id'] == 'tokomon' and egg > 0: P.put(egg + 1, bytes([no])); P.log.append('조수의 알 → 토코몬')
        installed[no] = m
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    P.log.append('새 디지몬 칸 %d종: %s' % (len(installed), ', '.join(m['name'] for m in installed.values()) or '없음 (그림 대기)'))
    # A단계: 야생·트레이너·이벤트가 가리키는 포켓몬·뺄 종 → 남길 디지몬 (mapping.csv). 계획종이 설치된 칸은 그대로
    P.r.d = P.d
    remap.apply(P, encounters.find_all(P.r), installed, set(json.load(open(os.path.join(HERE, 'order', 'keep.json')))))
    # 3 포획 규칙
    P.catch_engine()
    G = json.load(open(os.path.join(HERE, 'grades.json')))
    CATCHABLE = {'유년기Ⅰ', '유년기Ⅱ', '성장기'}
    # 등급 모를 때: 다른 종의 진화 대상이 아니면(=줄의 첫 단계) 잡을 수 있게.
    # 고친 뒤의 롬에서 올바른 진화 종류(1~10)만 센다 — 원본 메탈가루몬처럼 끝 표시가 깨진 목록이 엉뚱한 종을 대상으로 만들지 않게
    P.r.d = P.d
    targets = set()
    for no in range(1, dmrom.NUM + 1):
        for e in P.r.evos_attacks(no)[0]:
            if 1 <= e[0] <= 10 and 1 <= e[-1] <= dmrom.NUM: targets.add(e[-1])
    blocked = []
    for k, v in G.items():
        no = int(k); g = v['grade']
        ok = (g in CATCHABLE) if g else (no not in targets)
        if not ok:
            P.stats(no, catch=0); blocked.append(no)
    for no in (MGR, WGR):
        P.stats(no, catch=0); blocked.append(no)
    for no, m in installed.items():
        P.stats(no, catch=m['catch'])
        if m['catch'] == 0 and no not in blocked: blocked.append(no)
        if m['catch'] and no in blocked: blocked.remove(no)
    P.log.append('포획 불가 %d종 (성숙기 이상)' % len(blocked))
    P.r.d = P.d
    open(out_rom, 'wb').write(bytes(P.d))
    n = P.ips(out_ips)
    P.log.append('패치 %d바이트 → %s' % (n, out_ips))
    return P

if __name__ == '__main__':
    os.makedirs(dmrom.WORK, exist_ok=True)
    P = build(dmrom.default_rom(), os.path.join(dmrom.WORK, 'myver.gbc'), os.path.join(dmrom.WORK, 'myver.ips'))
    print('\n'.join(P.log))
