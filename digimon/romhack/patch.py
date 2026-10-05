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
import os, re, sys, json, struct, collections
import numpy as np
from PIL import Image
import dmrom, gblz, krtext, encounters, remap
from dmrom import addr, bankptr

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
from rules import HIGH_BOND, LOW_BOND
import rules
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
def png_to_idx(path, maxw, maxh, pal=None):
    """pal 을 주면 그 두 색에 맞춰 칸을 나눔 (뒷모습은 앞모습 팔레트로 — 롬은 앞·뒤가 팔레트 하나)"""
    im = Image.open(path).convert('RGBA'); a = np.asarray(im).astype(int)
    h, w = a.shape[:2]; idx = np.zeros((h, w), np.uint8)
    op = a[..., 3] > 128; L = a[..., :3] @ np.array([.299, .587, .114])
    cols = sorted({tuple(a[y, x, :3]) for y, x in zip(*np.nonzero(op))}, key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
    white = [c for c in cols if min(c) > 230]; black = [c for c in cols if max(c) < 60]
    mid = [c for c in cols if c not in white and c not in black]
    pal = pal or [mid[0] if mid else (200, 200, 200), mid[-1] if len(mid) > 1 else (120, 120, 120)]
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
        fi, pal = png_to_idx(front_png, 56, 56); bi, _ = png_to_idx(back_png, 48, 48, pal)
        size = 7 if max(fi.shape) > 48 else 6 if max(fi.shape) > 40 else 5
        fdat = gblz.compress(to_gb_pic(fi, size, size)); bdat = gblz.compress(to_gb_pic(bi, 6, 6))
        ents = []
        for dat in (fdat, bdat):
            bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat); ents += [bank, p & 255, p >> 8]
        self.put(self.r.pics + 6 * (no - 1), bytes(ents))
        self.stats(no, pic_size=size * 0x11)
        self.palette(no, *pal)
    def flip_back(self, no):
        """롬의 지금 뒷모습(48×48)을 좌우로 뒤집어 다시 넣음 — 1.4 그림처럼 우리 그림 파일이 없는 종용 (사용자 2026-10-05 「에렉몬 뒤 바라보는 방향」)"""
        self.r.d = self.d
        idx = np.fliplr(self.r.pic(no, back=True)).copy()
        dat = gblz.compress(to_gb_pic(idx, 6, 6))
        bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat)
        self.put(self.r.pics + 6 * (no - 1) + 3, bytes([bank, p & 255, p >> 8]))
    def back_only(self, no, back_png):
        """앞은 그대로(1.4 그림) 두고 뒷모습만 우리 그림으로. 색은 롬의 지금 팔레트 두 색에 가까운 쪽으로 나눔 (팔레트는 안 바꿈)"""
        self.r.d = self.d
        bi, _ = png_to_idx(back_png, 48, 48, self.r.palette(no))
        dat = gblz.compress(to_gb_pic(bi, 6, 6))
        bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat)
        self.put(self.r.pics + 6 * (no - 1) + 3, bytes([bank, p & 255, p >> 8]))
    def enlarge14(self, no, back):
        """롬의 지금 그림(1.4 그림)을 칸을 꽉 채우게 키워 다시 넣음 (그림 세션 tools/enlarge14.py, 사용자 메모 「확대」 2026-10-05).
        롬에서 꺼낸 그림이라 파일로 남기지 않고 빌드 안에서만 씀. 색 4개 그대로(색번호 그대로 키움)"""
        sys.path.insert(0, os.path.join(WEB, 'tools')); import enlarge14 as EN
        self.r.d = self.d
        t = self.r.pic(no, back=back).astype(int)
        r_ = EN.enlarge(t, 48 if back else 56); idx = np.where(r_ < 0, 0, r_).astype(np.uint8)
        if back: dat = gblz.compress(to_gb_pic(idx, 6, 6)); off = 3
        else:
            size = 7 if max(idx.shape) > 48 else 6 if max(idx.shape) > 40 else 5
            dat = gblz.compress(to_gb_pic(idx, size, size)); off = 0; self.stats(no, pic_size=size * 0x11)
        bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat)
        self.put(self.r.pics + 6 * (no - 1) + off, bytes([bank, p & 255, p >> 8]))
        return idx.shape
    # 트레이너 그림 (GetTrainerPic: ld hl, TrainerPicPointers / ld a,[wTrainerClass] / dec a / ld bc,3 …, 팔레트는 TrainerPalettes 직업×4바이트, 0 = 주인공)
    def trainer_pic(self, cls, png):
        d = bytes(self.d)
        m = re.search(rb'\x21(..)\xfa..\x3d\x01\x03\x00\xcd..\x3e(.)\xcd', d, re.S)
        tab = addr(m.group(2)[0], int.from_bytes(m.group(1), 'little'))
        idx, pal = png_to_idx(png, 56, 56)
        dat = gblz.compress(to_gb_pic(idx, 7, 7))
        bank, p = self.sp.take(len(dat), banks=PIC_BANKS); self.put(addr(bank, p), dat)     # 13·14·1F 뱅크는 FixPicBank 가 바꿔 읽어서 피함
        self.put(tab + 3 * (cls - 1), bytes([bank, p & 255, p >> 8]))
        m = re.search(rb'\x6f\x26\x00\x29\x29\x01(..)\x09\xc9', d, re.S)
        pt = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
        self.put(pt + 4 * cls, struct.pack('<2H', rgb555(pal[0]), rgb555(pal[1])))
        return pal
    # 주인공 그림 (사용자 2026-10-04 「주인공은 태일」): front = 인트로(트레이너 직업 CAL 그림, 56×56), card = 트레이너 카드(40×56, 압축 없음, 가로 순서),
    #   back = 전투 시작 뒷모습 ChrisBackpic(48×48, 압축, GetTrainerBackpic·명예의 전당이 같은 주소·뱅크를 읽음). 팔레트 = 표 0번(주인공)·CAL
    def player_pics(self, front=None, card=None, back=None):
        d = bytes(self.d); done = []; pal = None
        m = re.search(rb'\x6f\x26\x00\x29\x29\x01(..)\x09\xc9', d, re.S)
        pt = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
        if front:
            pal = self.trainer_pic(0x0c, front); done.append('인트로 앞모습')
        if card:
            idx, cp = png_to_idx(card, 40, 56, pal) if pal else png_to_idx(card, 40, 56)
            cv = np.zeros((56, 40), int); h, w = idx.shape; cv[56 - h:, (40 - w) // 2:(40 - w) // 2 + w] = idx
            gfx = bytearray()
            for ty in range(7):
                for tx in range(5):
                    for y in range(8):
                        row = cv[ty * 8 + y, tx * 8:tx * 8 + 8]
                        gfx += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(row)), sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
            KR_CARD = 0x25507                                                  # 1.4 롬에서 금 chris_card.2bpp 와 바이트가 같은 곳 (확인함)
            assert d[KR_CARD:KR_CARD + 4] == bytes(self.r.d[KR_CARD:KR_CARD + 4]); self.put(KR_CARD, bytes(gfx)); done.append('트레이너 카드')
        if back:
            m = re.search(rb'\x21(..)\xfa..\xfe.\x20\x03\x21(..)\x11\x10\x93\x06(.)\x0e\x31', d, re.S)
            old = int.from_bytes(m.group(1), 'little'); bank = m.group(3)[0]
            idx, bp = png_to_idx(back, 48, 48, pal) if pal else png_to_idx(back, 48, 48)
            dat = gblz.compress(to_gb_pic(idx, 6, 6))
            try: b_, p_ = self.sp.take(len(dat), banks=[bank])
            except MemoryError:
                _, end = gblz.decompress(d, addr(bank, old)); assert len(dat) <= end - addr(bank, old), '뒷모습이 원래 자리보다 큼'; p_ = old
            self.put(addr(bank, p_), dat); n = 0
            for i in [x.start() for x in re.finditer(re.escape(b'\x21' + old.to_bytes(2, 'little')), d)]:
                if bytes([0x06, bank]) in d[i + 3:i + 16] or i == m.start(): self.put(i + 1, p_.to_bytes(2, 'little')); n += 1
            assert n >= 1; pal = pal or bp; done.append('전투 뒷모습(%d곳)' % n)
        if pal: self.put(pt, struct.pack('<2H', rgb555(pal[0]), rgb555(pal[1])))     # 표 0번 = 주인공(PlayerPalette)
        return done
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
    def _dex_tab(self):
        d = bytes(self.d)
        m = re.search(rb'\x21(..)\x78\x3d\x06\x00\x4f\x09\x09\x07\xe6\x01\xc6(.)\x47\x2a\x66\x6f\xc9', d, re.S)
        tab = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')); b0 = m.group(2)[0]
        return d, tab, (lambda sp: addr(b0 + ((sp - 1) >> 7), d[tab + 2 * (sp - 1)] | d[tab + 2 * (sp - 1) + 1] << 8))
    def dex(self, no, kind, height, weight, lines):
        assert len(lines) == 3 and all(len(l) <= 16 for l in lines), '도감 글은 3줄, 줄마다 16자까지'
        e = krtext.encode(kind) + b'\x50' + bytes([height]) + struct.pack('<H', weight) + b'\x59'.join(krtext.encode(l) for l in lines) + b'\x50'
        self.dex_bytes(no, e)
    def dex_entry(self, no):
        """도감 한 항목 그대로 (분류 @ 키 몸무게 글 @)"""
        d, tab, ent = self._dex_tab(); a = ent(no); i = a
        for part in (0, 1):
            while d[i] != 0x50: i += 2 if 1 <= d[i] <= 0x0b else 1
            i += 1
            if part == 0: i += 3
        return d[a:i]
    def dex_bytes(self, no, e):
        d, tab, ent = self._dex_tab()
        room = min((ent(s) - ent(no) for s in range(1, NUM_SP + 1) if ent(s) > ent(no) and ent(s) // 0x4000 == ent(no) // 0x4000), default=0)
        if len(e) <= room:
            self.put(ent(no), e + bytes(room - len(e))); self.log.append('도감 %d번 %d/%d바이트' % (no, len(e), room)); return
        # 원래 자리가 모자라면 같은 뱅크의 빈 곳으로 옮기고 포인터를 바꿈 (도감 뱅크는 종 번호로 정해짐: 1~128 / 129~251)
        bank = ent(no) // 0x4000
        for k, (fb, fs, fe) in enumerate(getattr(self, 'dexfree', [])):     # 빈 칸 도감 자리 (dex_pool)
            if fb == bank and fe - fs >= len(e):
                self.dexfree[k] = (fb, fs + len(e), fe); b, p = fb, 0x4000 + fs % 0x4000; break
        else:
            b, p = self.sp.take(len(e), bank=bank)
        self.put(addr(b, p), e); self.put(tab + 2 * (no - 1), struct.pack('<H', p))
        self.log.append('도감 %d번 %d바이트 → 빈 곳 %02X:%04X' % (no, len(e), b, p))
    def dex_pool(self, empty_nos):
        """빈 칸(-----) 도감 글은 게임에서 안 보임 → 5바이트(분류@ 키·몸무게 0 글@)로 줄이고 남는 자리를 dex_bytes 가 옮길 곳으로 씀"""
        d, tab, ent = self._dex_tab(); self.dexfree = []
        for no in empty_nos:
            a = ent(no)
            room = min((ent(s) - a for s in range(1, NUM_SP + 1) if ent(s) > a and ent(s) // 0x4000 == a // 0x4000), default=0)
            if room < 5: continue
            self.put(a, bytes([0x50, 0, 0, 0, 0x50]))
            if room > 5: self.dexfree.append((a // 0x4000, a + 5, a + room))
        return sum(fe - fs for _, fs, fe in self.dexfree)
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
        d = bytes(self.d); texts = {}; self.starter_at = getattr(self, 'starter_at', {})
        for old, new in mapping.items():
            a = re.search(bytes([0x56, old, 0x84, old, 0x00]), d).start(); seg = d[a:a + 80]
            for k in (1, 3, seg.index(bytes([0x40, old])) + 1, seg.index(bytes([0x2d, old, 5])) + 1):
                self.put(a + k, bytes([new]))
            k = seg.index(0x4d, 5)                                    # 첫 writetext = '…로 하겠니?' 글
            texts[new] = addr(a // 0x4000, seg[k + 1] | seg[k + 2] << 8) + 1
            self.starter_at[new] = (a, texts[new])
        return texts
    # 이미 바꾼 스타팅을 한 번 더 바꾸기 (starters 가 기억한 스크립트 자리를 그대로 씀) → {새 종: 묻는 글 주소}
    def restarter(self, mapping):
        texts = {}
        for old, new in mapping.items():
            a, t = self.starter_at.pop(old); seg = bytes(self.d[a:a + 80])
            for k in (1, 3, seg.index(bytes([0x40, old])) + 1, seg.index(bytes([0x2d, old, 5])) + 1):
                assert self.d[a + k] == old; self.put(a + k, bytes([new]))
            self.starter_at[new] = (a, t); texts[new] = t
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
    # 사람 필드 그림 (걷기 6장: 16×96 = 앞·뒤·옆 서기, 앞·뒤·옆 걷기, 금 순서) — 투명 = 색 0, 옅은 회색 1, 짙은 회색 2, 검정 3
    def walker(self, png, sprite_id, pal):
        d = bytes(self.d)
        m = re.search(rb'\xe5\x21(..)\x3d\x4f\x06\x00\x3e\x06\xcd..\x2a\x5f\x2a\x57', d, re.S)       # GetSprite: ld hl, OverworldSprites
        tab = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
        a = np.asarray(Image.open(png).convert('RGBA')).astype(int)
        assert a.shape[:2] == (96, 16), a.shape
        idx = np.zeros((96, 16), int); op = a[..., 3] > 128; L = a[..., :3] @ np.array([.299, .587, .114])
        idx[op & (L >= 128)] = 1; idx[op & (L < 128) & (L >= 40)] = 2; idx[op & (L < 40)] = 3
        gfx = bytearray()
        for f in range(6):
            for ty, tx in ((0, 0), (0, 1), (1, 0), (1, 1)):                # 좌상·우상·좌하·우하
                for y in range(8):
                    row = idx[f * 16 + ty * 8 + y, tx * 8:tx * 8 + 8]
                    gfx += bytes([sum(((v & 1) << (7 - i)) for i, v in enumerate(row)), sum((((v >> 1) & 1) << (7 - i)) for i, v in enumerate(row))])
        # 표의 크기 칸 = 12칸(192바이트): 걷기 그림은 그 두 배를 이어서 읽음 (서기 3장 → VRAM 0, 걷기 3장 → VRAM 1)
        e = tab + 6 * (sprite_id - 1); assert d[e + 2] == len(gfx) // 2 and d[e + 4] == 1, d[e:e + 6].hex()
        # 원래 자리에 덮어씀 (크기가 같음): 이름 정하기·인트로처럼 표를 안 거치고 주인공 그림 주소(30:4000)를 바로 읽는 곳도 바뀌게
        self.put(addr(d[e + 3], d[e] | d[e + 1] << 8), bytes(gfx))
        self.put(e + 5, bytes([pal]))
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
    # 상대 파티: 무리(트레이너 그룹) 하나를 통째로 다시 씀. 이름·종류(기술/도구 유무)는 그대로, 마릿수는 바뀌어도 됨
    #   기술이 있는 트레이너는 그 레벨까지 배운 마지막 4개, 도구가 있는 트레이너는 같은 자리 도구(새 자리는 없음)
    def team_bytes(self, t, mons):
        d = self.d; j = d.index(0x50, t['start']); out = bytearray(d[t['start']:j + 2])
        for i, (lv, sp) in enumerate(mons):
            out += bytes([lv, sp])
            if t['kind'] in (2, 3): out.append(d[t['mons'][i][2] + 1] if i < len(t['mons']) else 0)
            if t['kind'] in (1, 3):
                ms = []
                for l, mv in self.r.evos_attacks(sp)[1]:
                    if l <= lv and mv not in ms:
                        ms.append(mv)
                        if len(ms) > 4: ms.pop(0)
                out += bytes(ms + [0] * (4 - len(ms)))
        return bytes(out + b'\xff')
    def group(self, gname, groups, new):
        """new = {무리 안 순서(0부터): [(레벨, 종 번호)]}. 원래 자리에 들어가면 그 자리(남는 곳은 FF), 넘치면 같은 뱅크 빈 곳으로 옮김"""
        ts = [t for t in self.r.trainers(len(groups)) if groups[t['group']] == gname]
        blob = b''.join(self.team_bytes(t, new[t['idx']]) if t['idx'] in new else bytes(self.d[t['start']:t['end']]) for t in ts)
        s, e = ts[0]['start'], ts[-1]['end']
        if len(blob) <= e - s: self.put(s, blob + b'\xff' * (e - s - len(blob))); return
        bank, tab = self.r.trainer_table()
        b, p = self.sp.take(len(blob), bank=bank); self.put(addr(b, p), blob)
        self.put(tab + 2 * groups.index(gname), struct.pack('<H', p))
        self.log.append('트레이너 무리 %s %d → %d바이트, 뱅크 %02X:%04X 로 옮김' % (gname, e - s, len(blob), b, p))
    # D단계 같은 길이 치환. 대사: 새 말 + 그 줄 나머지 + 빈칸(줄어든 바이트만큼, 줄 끝이라 안 보임) → 길이가 같아 포인터를 안 건드림
    #   도구 이름표(item_list = 시작, 끝): 이름을 세어 읽는 목록이라 뒤 이름을 당기고 목록 끝에 '@'
    def words(self, pairs, item_list):
        CTRL = (0x50, 0x59, 0x5a, 0x5c, 0x5d, 0x5e, 0x5f)
        out = []
        for old, new in pairs:
            ob, nb = krtext.encode(old), krtext.encode(new); gap = len(ob) - len(nb); assert gap >= 0, (old, new)
            n = 0; i = bytes(self.d).find(ob)
            while i >= 0:
                if gap and item_list[0] <= i < item_list[1]:
                    e = item_list[1]; self.put(i, nb + bytes(self.d[i + len(ob):e]) + b'\x50' * gap)
                elif gap:
                    j = i + len(ob)
                    while self.d[j] not in CTRL: j += 2 if 1 <= self.d[j] <= 0x0b else 1
                    self.put(i, nb + bytes(self.d[i + len(ob):j]) + krtext.encode(' ') * gap)
                else: self.put(i, nb)
                n += 1; i = bytes(self.d).find(ob, i + len(nb))
            out.append('%s→%s %d곳' % (old, new, n))
        self.log.append('D단계 낱말 바꾸기: ' + ', '.join(out))
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
        p0 = self.d[self.r.evos + 2 * (no - 1)] | self.d[self.r.evos + 2 * (no - 1) + 1] << 8
        a0 = addr(bank, p0); n0 = sum(4 if e[0] == STAT else 3 for e in old_ev) + 1 + 2 * len(old_mv) + 1
        if len(blob) <= n0 and 0x4000 <= p0 < 0x8000:                   # 원래 자리에 들어가면 그 자리에 (뱅크 빈 곳 아낌)
            self.put(a0, blob); return
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
        b, org = self.evo_space if getattr(self, 'evo_space', None) else self.sp.take(n_code + 251, bank=bank)
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
        a.L('dark'); a.ld_a_mem(HAPPY_RAM); a.cp(LOW_BOND); a.jp(DONT2, 'nc')          # 유대 낮음일 때만
        a.ld_a_mem(BADGES); a.db(0xA7); a.jp(DONT2, 'z'); a.call('own'); a.jp(DONT2, 'nz')   # 문장(배지)은 있지만 자기 문장이 아님
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
    P.evo_space = P.sp.take(140 + 251, bank=r.evos // 0x4000)          # 진화 확장 코드 자리 (코드는 B단계 진화 표 뒤에 씀)
    MGR = N.get('메탈그레몬') or S('핫삼'); WGR = N.get('워가루몬') or S('링곰')
    P.new_mon(MGR, '메탈그레몬', S('그레이몬'), S('워그레이몬'), 'metalgreymon', '사이보그형', ['몸의 절반 이상을 기계화한', '디지몬. 공격력은 핵탄두', '한 발에 맞먹는다고 한다'], 42, 2800)
    P.new_mon(WGR, '워가루몬', S('가루몬'), S('메탈가루몬'), 'weregarurumon', '수인형', ['가루몬이 진화해 두 발로', '걷게 된 디지몬. 발차기와', '점프력이 강하다'], 21, 1100)
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
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
    P.evos(S('캅테리몬'), [(CREST, 35, S('아트캅테몬')), (ANYCREST, 40, S('아트캅테몬'))])   # 로제몬(태양의 돌) 갈래는 뺌 (B단계)
    P.evos(S('니드몬'), [(CREST, 30, S('릴리몬')), (ANYCREST, 32, S('릴리몬'))])
    P.evos(S('원뿔몬'), [(CREST, 34, S('쥬드몬')), (ANYCREST, 38, S('쥬드몬'))])           # 원래 통신 교환 진화라 혼자서는 못 했음
    P.evos(S('엔젤몬'), [(CREST, 30, S('홀리엔젤몬')), (ANYCREST, 34, S('홀리엔젤몬'))])   # 완전체 30 이상 (B단계)
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
    P.text_at(T[S('아구몬')], '겐나이『불꽃 디지몬<LINE>아구몬으로 하겠니!?')
    P.text_at(T[S('파피몬')], '겐나이『물디지몬<LINE>파피몬이 마음에 드느냐!?')
    P.text_at(T[VM], '겐나이『소룡디지몬<LINE>브이몬이 마음에 들었느냐!?')
    P.log.append('스타팅 → 아구몬·파피몬·브이몬, 트레이너 종 %d곳 바꿈' % P.trainer_species(TAM))
    dv = os.path.join(WEB, 'art', 'digivice.png')                     # 받은 그림 (16×16), 없으면 임시 그림
    P.digivice(dv if os.path.exists(dv) else os.path.join(WEB, 'art', 'digivice_temp.png'))
    gw = os.path.join(WEB, 'art', 'gennai_ow.png')                    # 연구소 박사 필드 그림 → 겐나이 (src/people/gennai_ai.png 보고 16×16 로 찍음)
    if os.path.exists(gw):                                            # SPRITE_ELM = 0x10 (연구소 화면 OAM으로 확인), SPRITE_OAK = 0x05 (오박사 연구소·이상한 할아버지 집·목호 방), PAL_OW_BLUE
        for sid in (0x10, 0x05): P.walker(gw, sid, 1)
        P.log.append('박사 필드 그림(공박사·오박사) → 겐나이 (파란 팔레트)')
    tw = os.path.join(WEB, 'art', 'taichi_ow.png')                    # 주인공 필드 그림 → 태일 (src/people/taichi_ai.png 보고 16×16 로 찍음, 사용자 2026-10-04)
    if os.path.exists(tw):                                            # SPRITE_CHRIS 0x01 걷기, 0x02 자전거(자전거 그림 없이 같은 그림), PAL_OW_BLUE
        for sid in (0x01, 0x02): P.walker(tw, sid, 1)
        P.log.append('주인공 필드 그림 → 태일 (걷기·자전거, 파란 팔레트)')
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
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}               # 코로몬·메탈그레몬처럼 앞에서 만든 칸도 찾게
    for m in SL['mons']:
        f, b = (os.path.join(WEB, 'art', m['id'] + s_) for s_ in ('-f.png', '-b.png'))
        if not (os.path.exists(f) and os.path.exists(b)):
            if os.environ.get('PLACEHOLDER') != '1': continue
            f, b = os.path.join(WEB, 'art', 'placeholder-f.png'), os.path.join(WEB, 'art', 'placeholder-b.png')
        no = N.get(m['name']) or (m['slot'] if isinstance(m['slot'], int) else S(m['slot']))      # 빈 칸(-----)은 번호로
        st = dict(zip(('hp', 'atk', 'def', 'spd', 'sat', 'sdf'), m['stats']))
        P.name(no, m['name']); N[m['name']] = no                        # 새 칸끼리 진화(푸니몬 → 뿔몬)도 찾게
        P.stats(no, **st, type1=TYPES[m['type'][0]], type2=TYPES[m['type'][1]], exp=m['exp'], catch=m['catch'], growth=0)
        P.pic(no, f, b)
        P.evos(no, [(LV, lv, S(t)) for _, lv, t in m['evos']], moves_by_name(m['moves']))
        P.dex(no, *m['dex'])
        lk = S(m['like']); idx, pitch, length = P.cry_of(lk)
        baby = m['grade'].startswith(('유년기', '유아기'))
        P.cry(no, idx, (pitch + (0x30 if baby else -0x20)) & 0xffff, (length - 0x10 if baby else length + 0x20) & 0xffff)
        d_ = bytes(P.d); mi = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', d_, re.S)
        P.icon(no, ICON_JIGGLYPUFF if baby else d_[addr(mi.start() // 0x4000, int.from_bytes(mi.group(1), 'little')) + lk - 1])
        if m['id'] == 'tokomon' and egg > 0: P.put(egg + 1, bytes([no])); P.log.append('조수의 알 → 토코몬')
        installed[no] = m
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    P.log.append('새 디지몬 칸 %d종: %s' % (len(installed), ', '.join(m['name'] for m in installed.values()) or '없음 (그림 대기)'))
    # 스타팅 → 유년기 (사용자 2026-10-03 「스타팅도 성장기 말고 유년기」). 유년기 칸이 아직 없으면(그림 대기) 성장기 그대로
    bs = {N[rk]: (N[bb], txt) for rk, bb, txt in rules.BABY_STARTERS if bb in N}
    for k_, t_ in P.restarter({rk: v[0] for rk, v in bs.items()}).items():
        P.text_at(t_, next(v[1] for v in bs.values() if v[0] == k_))
    P.log.append('스타팅 유년기: %s' % ', '.join('%s → %s' % (rk, bb) for rk, bb, _ in rules.BABY_STARTERS if bb in N))
    # B단계 진화 표 (2026-10-02 자문 판정). 갈래체·중간체 그림이 들어오면(그 이름이 롬에 있으면) 그 칸으로
    has = lambda nm: nm in N
    def T(*ev): return [(k, lv, S(nm)) for k, lv, nm in ev]
    EV = {
        '쿠네몬': T((LV, 14, '플라이몬')),
        '플라이몬': T((ANYCREST, 34, '오쿠와몬')),                       # 쿠네몬 줄은 파트너가 아니라 자기 문장 없음
        '스나이몬': T((ANYCREST, 34, '아라크네몬')),
        '호크몬': T((LV, 18, '아쿠이라몬')) if has('아쿠이라몬') else T((ANYCREST, 35, '실피드몬')),
        '가트몬': (T((CREST, 30, '엔젤우몬')) if has('엔젤우몬') else []) + (T((DARK, 30, '레이디데블')) if has('레이디데블') else []),     # 달맞이 돌 → 오파니몬 삭제. 자기 문장 → 암흑 순서
        '홀리엔젤몬': T((CREST, 45, '세라피몬')),
        '피코데블몬': T((LV, 20, '데블몬')),                            # 정사 진화. 피에몬은 사천왕 전용
        '피에몬': [], '위자몬': [], '스팅몬': [], '데블몬': [], '디지타마몬': [], '안드로몬': [], '콩알몬': [],
        '에테몬': T((LV, 45, '메탈에테몬')),
        '레오몬': T((LV, 50, '샤벨레오몬')),                            # 통신 → 개굴몬 삭제
        '울퉁몬': T((LV, 25, '모노크로몬')) if has('모노크로몬') else [],
        '쉬라몬': T((LV, 18, '원뿔몬')),
        '베타몬': T((LV, 16, '시드라몬')) if has('시드라몬') else T((LV, 30, '메가시라몬')),
        '인펠몬': T((LV, 45, '디아블로몬')),
        '엑스브이몬': T((LV, 45, '황제드라몬')),
        '파닥몬': T((BOND_HI, 16, '엔젤몬'), (BOND_LO, 16, '데블몬'), (LV, 16, '엔젤몬')),
        '그레이몬': T((CREST, 32, '메탈그레몬')) + (T((DARK, 32, '스컬그레몬')) if has('스컬그레몬') else []) + T((ANYCREST, 36, '메탈그레몬')),
    }
    if has('아쿠이라몬'): EV['아쿠이라몬'] = T((ANYCREST, 35, '실피드몬'))
    if has('엔젤우몬'): EV['엔젤우몬'] = T((CREST, 45, '마그나드몬'))
    if has('쿠가몬'):                                                # 주말 작업팩 E 연결표: 텐타몬 유대 낮음 Lv16, 쿠가몬 Lv34 아무 문장 → 오쿠와몬
        EV['텐타몬'] = T((BOND_LO, 16, '쿠가몬'), (LV, 21, '캅테리몬'))
        EV['쿠가몬'] = T((ANYCREST, 34, '오쿠와몬'))
    for nm, ev in EV.items(): P.evos(S(nm), ev)
    # 잠자는 포켓몬 칸의 진화가 디지몬 칸을 가리키면 지움 (스라크 → 메탈그레몬 칸, 깜지곰 → 워가루몬 칸 같은 것, R14)
    orig = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(encounters.KR, 'data/pokemon/names.asm')) if 'dname' in l]
    pk = {n for n in range(1, dmrom.NUM + 1) if r.name(n) == orig[n - 1]}
    cut = []
    for n in sorted(pk):
        ev = r.evos_attacks(n)[0]
        keep_ev = [e for e in ev if e[-1] in pk]
        if len(keep_ev) != len(ev): P.evos(n, keep_ev); cut.append(r.name(n))
    P.log.append('B단계 진화 표 %d종, 포켓몬 칸 진화 정리: %s' % (len(EV), ', '.join(cut) or '없음'))
    # 1·2 진화 확장 코드 + 문장표 (문장 = 배지): 조건부 종까지 정해진 뒤에
    crest = {'그레이몬': '용기', '가루몬': '우정', '버드라몬': '사랑', '캅테리몬': '지식', '니드몬': '순수', '원뿔몬': '성실', '엔젤몬': '희망', '가트몬': '빛',
             '메탈그레몬': '용기', '워가루몬': '우정', '홀리엔젤몬': '희망', '엔젤우몬': '빛'}
    P.evo_engine({N[nm]: 1 << CREST_BIT[c] for nm, c in crest.items() if nm in N})
    # A단계: 야생·트레이너·이벤트가 가리키는 포켓몬·뺄 종 → 남길 디지몬 (mapping.csv). 계획종이 설치된 칸은 그대로
    P.r.d = P.d
    sites0 = encounters.find_all(P.r)                                  # 원래 롬 자리 (치환 뒤에는 표를 원래 종으로 못 찾으므로 한 번만)
    remap.apply(P, sites0, installed, set(json.load(open(os.path.join(HERE, 'order', 'keep.json')))))
    # E단계 출현 연결 (rules.PLACE_SWAP·PLACE_ADD)
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}; groups_ = collections.OrderedDict(); nsw = nadd = 0
    for s in sites0:
        if s['kind'] in remap.WILD: groups_.setdefault((s['kind'], s['where']), []).append(s)
    for frm, to, area in rules.PLACE_SWAP:
        for (kd, wh), ss in groups_.items():
            if area and not wh.startswith(area): continue
            for s in ss:
                if P.d[s['addr']] == N[frm]: P.d[s['addr']] = N[to]; nsw += 1
    for nm, kd, area, slots, (lo, hi), cond in rules.PLACE_ADD:
        per = 7 if kd == '풀숲' else 3
        for (k_, wh), ss in groups_.items():
            if k_ != kd or not wh.startswith(area): continue
            for i, s in enumerate(ss):
                lv = P.d[s['addr'] - 1]
                if cond and not cond[0] <= lv <= cond[1]: continue
                if i % per in slots: P.d[s['addr']] = N[nm]; nadd += 1
                if P.d[s['addr']] == N[nm]: P.d[s['addr'] - 1] = min(max(lv, lo), hi)    # 그 지역에 원래 있던 같은 종도 레벨 맞춤
    P.log.append('E단계 출현 연결: 바꿈 %d자리, 넣음 %d자리' % (nsw, nadd))
    # 유년기 → 성장기 진화 레벨 (rules.BABY_EVO_LV): 그보다 늦게 진화하는 레벨 진화를 그 레벨로
    P.r.d = P.d
    babies = {N[m['name']] for m in SL['mons'] if m['grade'].startswith('유년기') and m['name'] in N} | {N['코로몬']}
    nlv = []
    for b_ in sorted(babies):
        ev_ = [tuple(e_) for e_ in P.r.evos_attacks(b_)[0]]
        new_ = [(LV, rules.BABY_EVO_LV, e_[-1]) if e_[0] == LV and e_[1] > rules.BABY_EVO_LV and e_[-1] not in babies else e_ for e_ in ev_]
        if new_ != ev_: P.evos(b_, new_); nlv.append('%s %d' % (r.name(b_), ev_[0][1]))
    P.log.append('유년기 → 성장기 Lv%d: %s (원래 레벨)' % (rules.BABY_EVO_LV, ', '.join(nlv)))
    # 초반 야생 유년기 (rules.BABY_WILD_LV): 그 레벨 이하 야생 칸의 성장기 → 레벨로 그 성장기가 되는 유년기 (롬에 있을 때만)
    P.r.d = P.d
    baby_of = {}
    for b_ in babies:
        for e_ in P.r.evos_attacks(b_)[0]:
            if e_[0] == LV and e_[-1] not in babies: baby_of.setdefault(e_[-1], b_)
    nb_ = collections.Counter()
    for (kd, wh), ss in groups_.items():
        for s in ss:
            sp_ = P.d[s['addr']]
            if sp_ in baby_of and P.d[s['addr'] - 1] <= rules.BABY_WILD_LV:
                P.d[s['addr']] = baby_of[sp_]; nb_['%s→%s' % (r.name(sp_), r.name(baby_of[sp_]))] += 1
    P.log.append('초반 야생 유년기 (Lv%d 이하): %s' % (rules.BABY_WILD_LV, ', '.join('%s %d자리' % kv for kv in nb_.items()) or '없음'))
    # F단계 색만 바꾼 종 (rules.PALSWAP): 원본의 기본 정보·그림·기술·울음·아이콘·도감을 그대로 가리키고, 팔레트와 공격 +10·방어 −10 만 다르게
    P.r.d = P.d; N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    dm = re.search(rb'\xfe\xfd\x28.\x3d\x21(..)\x5f\x16\x00\x19\x7e\xc9', bytes(P.d), re.S)
    icons = addr(dm.start() // 0x4000, int.from_bytes(dm.group(1), 'little'))
    for nm, (src, slot, grade, c1, c2) in rules.PALSWAP.items():
        s_ = N[src]; a_, b_ = r.bs + 0x20 * (slot - 1), r.bs + 0x20 * (s_ - 1)
        P.put(a_ + 1, bytes(P.d[b_ + 1:b_ + 0x20]))                          # 첫 바이트(종 번호)만 빼고 복사
        P.stats(slot, atk=min(255, P.d[b_ + 2] + 10), **{'def': max(1, P.d[b_ + 3] - 10)})
        P.name(slot, nm)
        P.put(r.pics + 6 * (slot - 1), bytes(P.d[r.pics + 6 * (s_ - 1):r.pics + 6 * s_]))
        P.palette(slot, c1, c2)
        P.evos(slot, [], P.r.evos_attacks(s_)[1])
        P.cry(slot, *P.cry_of(s_)); P.put(icons + slot - 1, bytes([P.d[icons + s_ - 1]]))
        P.dex_bytes(slot, P.dex_entry(s_))                                   # 원본 글 그대로 (3줄이라 한 줄 더할 자리 없음)
    P.log.append('F단계 색만 바꾼 종: ' + ', '.join('%s(%d, %s 그림)' % (nm, v[1], v[0]) for nm, v in rules.PALSWAP.items()))
    # D-4 검은 톱니 (rules.BLACK_GEAR)
    BG = rules.BLACK_GEAR; it = BG['item']; dd = bytes(P.d); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    ob, nb = krtext.encode(BG['old']), krtext.encode(BG['name'])
    assert len(ob) == len(nb) and dd.count(ob) == 1, '도구 이름'
    P.put(dd.find(ob), nb)
    s4 = dd.find(krtext.encode('디지몬을 잡기 위한 도구') + b'\x59')                 # 수퍼볼(4번) 설명 → 설명 포인터 표
    bk = s4 // 0x4000; pb = struct.pack('<H', 0x4000 + s4 % 0x4000); dtab = dd.find(pb, bk * 0x4000, (bk + 1) * 0x4000) - 6
    da = addr(bk, struct.unpack('<H', dd[dtab + 2 * (it - 1):dtab + 2 * it])[0]); de = dd.index(0x50, da)
    j = da
    while dd[j] != 0x50: j += 2 if 1 <= dd[j] <= 0x0b else 1
    ne = krtext.encode(BG['desc']) + b'\x50'; assert len(ne) <= j + 1 - da, '설명이 김'
    P.put(da, ne + b'\x50' * (j + 1 - da - len(ne)))
    at = next(a_ for a_ in range(len(dd) - 40) if dd[a_ + 7:a_ + 9] == b'\xb0\x04' and dd[a_ + 21:a_ + 23] == b'\x58\x02' and dd[a_ + 28:a_ + 30] == b'\xc8\x00')
    P.put(at + 7 * (it - 1), b'\x00\x00')                                         # 값 0 (상점 판매 없음)
    gr = N[BG['from']]
    P.evos(gr, [(ITEM, it, N[BG['to']])] + [tuple(e) for e in P.r.evos_attacks(gr)[0] if 1 <= e[0] <= 10])
    assert dd.count(BG['ball']) == 1, '아지트 아이템볼'
    P.d[dd.find(BG['ball']) + 4] = it
    vg = [k for k in range(len(dd) - 3) if dd[k:k + 3] == bytes([0x9e, it, 1])]
    assert len(vg) == 2, '대회 상품 스크립트 %d곳' % len(vg)
    for k in vg:
        P.d[k + 1] = BG['prize']
        if dd[k - 7:k - 5] == bytes([0x41, it]): P.d[k - 6] = BG['prize']           # getitemname (결과 발표 글)
    P.log.append('D-4 검은 톱니: %s 칸 이름·설명·값 0, %s 도구 진화 → %s, 아지트 B1F 아이템볼, 대회 1등 상품 → 이상한사탕' % (BG['old'], BG['from'], BG['to']))
    # 종 번호 → 단계 (grades.json + 새로 넣은 칸). C단계 파티와 포획률이 같이 씀
    G = json.load(open(os.path.join(HERE, 'grades.json')))
    grade = {int(k): v['grade'] for k, v in G.items() if v['grade'] and v['name'] == r.name(int(k))}
    grade.update({KORO: '유년기Ⅱ', MGR: '완전체', WGR: '완전체'})
    for no, m in installed.items(): grade[no] = m['grade']
    for nm, v in rules.PALSWAP.items(): grade[v[1]] = v[2]
    # C단계 상대 파티 — A단계 바꾸기 뒤에
    #   1) parties.json: 「무리」 = 그 무리 첫 사람, 「무리#n」 = n번째 사람. 종(sp)이 아직 롬에 없으면(그림·색 바꾸기 전) until 종
    #   2) 암흑단 조직원(rules.GRUNT_GROUPS): parties.json 에 없는 사람은 레벨대별 종으로 (레벨은 그대로)
    #   3) 그 밖의 트레이너 파티에 궁극체가 있으면 한 단계 아래로 (rules.R13_DOWN). 사천왕·챔피언·레드·라이벌 마지막은 빼고
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}
    plan = {}; waiting = set()
    for key, mons in json.load(open(os.path.join(HERE, 'parties.json'))).items():
        if key.startswith('_'): continue
        g, _, k = key.partition('#'); new = []
        for m in mons:
            if m['sp'] not in N: waiting.add('%s→%s' % (m['sp'], m['until']))
            new.append((m['lv'], N[m['sp']] if m['sp'] in N else N[m['until']]))
        plan.setdefault(g, {})[int(k) - 1 if k else 0] = new
    TS = P.r.trainers(len(groups)); ngrunt = nr13 = 0
    for t in TS:
        g = groups[t['group']]
        if g not in rules.GRUNT_GROUPS or t['idx'] in plan.get(g, {}): continue
        last = len(t['mons']) - 1; new = []
        for i, (lv, _, _) in enumerate(t['mons']):
            pool = rules.GRUNT_LOW if lv < rules.GRUNT_LV else rules.GRUNT_HIGH
            new.append((lv, N[pool[1] if i == last else pool[i % 2]]))
        plan.setdefault(g, {})[t['idx']] = new; ngrunt += 1
    for t in TS:
        g = groups[t['group']]
        if g in rules.ULTIMATE_OK or (g == rules.RIVAL_FINAL[0] and t['idx'] >= rules.RIVAL_FINAL[1]) or t['idx'] in plan.get(g, {}): continue
        if not any(grade.get(sp) == '궁극체' for _, sp, _ in t['mons']): continue
        plan.setdefault(g, {})[t['idx']] = [(lv, N[rules.R13_DOWN[r.name(sp)]] if grade.get(sp) == '궁극체' else sp) for lv, sp, _ in t['mons']]
        nr13 += 1
    for g, new in plan.items(): P.group(g, groups, new)
    P.r.d = P.d
    P.log.append('C단계 파티: 지정 %d명, 암흑단 조직원 %d명, 궁극체 낮춤 %d명. 임시 종: %s' % (
        sum(len(v) for v in plan.values()) - ngrunt - nr13, ngrunt, nr13, ', '.join(sorted(waiting)) or '없음'))
    # 3 포획 규칙
    P.catch_engine()
    # 단계별 포획률 (rules.py). 이름 지정(떠돌이 셋 30, 보스·암흑체 0)이 먼저. 단계를 모르는 칸(포켓몬·뺄 종)은 그대로
    zero = []
    for no, g in sorted(grade.items()):
        rate = rules.CATCH_BY_NAME.get(r.name(no), rules.CATCH_BY_GRADE.get(g))
        if rate is None: continue
        P.stats(no, catch=rate)
        if rate == 0: zero.append(r.name(no))
    P.log.append('포획률: 단계표 %d종, 못 잡는 종 %d (%s)' % (len(grade), len(zero), ', '.join(zero)))
    # 기술: 1.4 가 원작에서 바꾼 것만 고침 (rules.MOVE_FIX)
    mt = bytes(P.d).find(bytes([1, 0, 40, 0, 255, 35, 0, 2, 0, 50, 1, 255, 25, 0]))
    assert mt > 0, '기술 표를 못 찾음'
    for no, (pw, pp) in rules.MOVE_FIX.items():
        if pw is not None: P.d[mt + 7 * (no - 1) + 2] = pw
        if pp is not None: P.d[mt + 7 * (no - 1) + 5] = pp
    P.log.append('기술 고침 %d개' % len(rules.MOVE_FIX))
    # D단계 1차: 겐나이·암흑단·디지볼 (rules.WORDS), 안농 → 디지문자 (이름·도감만). A단계 바꾸기 뒤라 안농 칸 자리는 그대로
    il = bytes(P.d).find(krtext.encode('마스터볼') + b'\x50' + krtext.encode('하이퍼볼') + b'\x50')
    assert il > 0, '도구 이름표를 못 찾음'
    ie = il
    for _ in range(256): ie = P.d.index(0x50, ie) + 1                 # 도구 이름 256개 (pokegold-kr data/items/names.asm)
    P.words(rules.WORDS, (il, ie))
    # D-2 관장 승리 대사 + 문장 두 줄 (원래 자리에 안 들어가면 retext 가 빈 뱅크로 옮기고 text_far 로 연결)
    import texts as TX
    for cls, (l1, l2) in rules.GYM_LINES.items():
        mt_ = re.search(re.escape(bytes([0x64])) + b'(..)' + re.escape(bytes([0, 0, 0x5e, cls, 1])), bytes(P.d), re.S)
        ta = addr(mt_.start() // 0x4000, int.from_bytes(mt_.group(1), 'little'))
        end_, _, s_ = TX.read_text(bytes(P.d), ta)
        assert s_.endswith('<DONE>'), s_
        P.retext(ta, s_[:-len('<DONE>')] + '<PARA>%s<LINE>%s<DONE>' % (l1, l2))
    # D-3 유대 측정 대사 6구간
    for head, new in rules.BOND_TEXTS:
        hb = krtext.encode(head); h = bytes(P.d).find(hb)
        assert h > 0 and P.d[h - 1] == 0x00 and bytes(P.d).find(hb, h + 1) < 0, head
        P.retext(h - 1, new)
    P.log.append('D-2 관장 승리 대사 %d명, D-3 유대 측정 %d구간' % (len(rules.GYM_LINES), len(rules.BOND_TEXTS)))
    un, unm = rules.UNOWN
    P.name(un, unm)
    P.dex(un, '문자형', 5, 50, ['디지털 월드의 문자가', '형체를 얻은 것. 유적', '벽에 새겨진 글자 모양'])   # 주말 작업팩 D-6 (길이에 맞춰 줄임)
    # D-7 잠자는 포켓몬 칸 → 「-----」, 포획률 0 (check.py 의 잠자는 칸과 같은 판정)
    P.r.d = P.d
    ORIG = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(encounters.KR, 'data/pokemon/names.asm')) if 'dname' in l]
    # 자리는 원래 롬에서 찾고(표를 원래 종 배열로 찾으므로) 지금 종을 읽음. 트레이너는 지금 파티(옮긴 무리 포함)
    wild_ev = {P.d[s['addr']] for s in encounters.find_all(dmrom.Rom(base)) if s['kind'] != '트레이너'}
    seen = wild_ev | {sp for t in P.r.trainers(len(groups)) for _, sp, _ in t['mons']}
    stack = list(wild_ev); got = set(stack)
    while stack:
        n_ = stack.pop()
        for e in P.r.evos_attacks(n_)[0]:
            if 1 <= e[0] <= 10 and e[-1] not in got: got.add(e[-1]); stack.append(e[-1])
    empty = [n_ for n_ in range(1, dmrom.NUM + 1) if n_ not in seen and n_ not in got and r.name(n_) == ORIG[n_ - 1]]
    for n_ in empty: P.name(n_, rules.EMPTY_NAME); P.stats(n_, catch=0)
    P.log.append('D-7 잠자는 포켓몬 칸 %d개 → 「%s」·포획률 0' % (len(empty), rules.EMPTY_NAME))
    # 파워디지몬(02) 이후 디지몬 (rules.LATE_SERIES·LATE_EXTRA): 게임에서 닿지 않는 1.4 칸 → 「-----」·포획률 0. 그림·도감 글은 롬에 남지만 볼 길이 없음.
    #   이름이 1.4 이름 그대로인 칸만 (새로 넣은 종·색 바꾼 종은 series.json 에 이름이 없어 해당 안 됨)
    SER = {v['name']: v['series'] for v in json.load(open(os.path.join(HERE, 'series.json'))).values()}
    late = [n_ for n_ in range(1, dmrom.NUM + 1) if n_ not in seen and n_ not in got and r.name(n_) != ORIG[n_ - 1]
            and (SER.get(r.name(n_)) in rules.LATE_SERIES or r.name(n_) in rules.LATE_EXTRA)]
    late_names = [r.name(n_) for n_ in late]
    for n_ in late: P.name(n_, rules.EMPTY_NAME); P.stats(n_, catch=0)
    P.log.append('파워디지몬 이후 디지몬 %d칸 → 「%s」: %s' % (len(late), rules.EMPTY_NAME, ', '.join(late_names)))
    # 1.4 그림 다시 그리기 (rules.REDRAW): 우리 그림이 앞·뒤 다 있는 종. 팔레트도 그림 색으로
    N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}; nrd = []
    for nm, art in rules.REDRAW.items():
        f, b = (os.path.join(WEB, 'art', art + s_) for s_ in ('-f.png', '-b.png'))
        if nm in N and os.path.exists(f) and os.path.exists(b): P.pic(N[nm], f, b); nrd.append(nm)
    P.log.append('1.4 그림 다시 그리기 %d종: %s' % (len(nrd), ', '.join(nrd)))
    for nm, art in rules.BACK_ONLY.items():                                  # 앞은 1.4 그대로, 뒤만 우리 그림 (그림 세션이 뒤만 새로 그린 종)
        bp = os.path.join(WEB, 'art', art + '-b.png')
        if nm in N and nm not in nrd and os.path.exists(bp) and not os.path.exists(os.path.join(WEB, 'art', art + '-f.png')):
            P.back_only(N[nm], bp); P.log.append('  %s 뒷모습만 새 그림 (앞은 1.4)' % nm)
    for nm in rules.FLIP_BACK:                                               # 1.4 뒷모습 좌우 뒤집기 (우리 그림이 있는 종은 그림 파일에서 뒤집음)
        if nm in N and nm not in nrd: P.flip_back(N[nm]); P.log.append('  %s 뒷모습 좌우 뒤집음 (1.4 그림)' % nm)
    big = []
    for back, names in ((False, rules.ENLARGE14_FRONT), (True, rules.ENLARGE14_BACK)):   # 1.4 그림 확대 (우리 그림으로 바뀐 종은 건너뜀)
        for nm in names:
            if nm in N and nm not in nrd: h_, w_ = P.enlarge14(N[nm], back); big.append('%s %s %d×%d' % (nm, '뒤' if back else '앞', w_, h_))
    P.log.append('1.4 그림 확대 %d장: %s' % (len(big), ', '.join(big)))
    for nm, (src, slot, *_) in rules.PALSWAP.items():                      # 색만 바꾼 종은 원본의 새 그림을 따라감 (팔레트는 자기 것)
        if src in nrd:
            P.put(r.pics + 6 * (slot - 1), bytes(P.d[r.pics + 6 * (N[src] - 1):r.pics + 6 * N[src]]))
            P.stats(slot, pic_size=P.d[r.bs + 0x20 * (N[src] - 1) + 17]); P.log.append('  %s 그림 → %s 새 그림' % (nm, src))
    # 노래 (rules.MUSIC): gbc/music 곡을 금 음악 엔진 형식으로 (music.py) 빈 뱅크에 넣고 음악 포인터 표(Music, 3바이트 dba)를 바꿈
    import music
    m = re.search(rb'\x21(..)\x19\x19\x19\x2a\xea', bytes(P.d), re.S)
    mtab = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
    ff = float(os.environ.get('MUSIC_FF', rules.MUSIC_FF))              # 델타 빨리감기 배수로 들을 때 원래 곡이 되게 (rules.MUSIC_FF, 사용자 2026-10-04·05)
    for nm, ids in rules.MUSIC.items():
        js = music.load(nm); loop = True if nm == 'evolve' else None
        slow = 1 if nm == 'heal' else None                              # 디지몬센터 회복은 정해진 프레임만 기다림 → 템포는 그대로, 음만 낮춤
        st = music.STYLES.get(rules.MUSIC_STYLE.get(nm))                  # 잔잔한 배경음 등 곡 느낌 (rules.MUSIC_STYLE)
        size = len(music.song_bytes(js, 0x4000, loop, ff, slow, st, rules.MUSIC_FF_PITCH))
        b, p = P.sp.take(size, banks=[0x13, 0x11, 0x0b]); P.put(addr(b, p), music.song_bytes(js, p, loop, ff, slow, st, rules.MUSIC_FF_PITCH))
        for i in ids: P.put(mtab + 3 * i, bytes([b]) + struct.pack('<H', p))
    P.log.append('노래 %d곡 → 금 음악 %d번호 (표 %06X)%s' % (len(rules.MUSIC), sum(len(v) for v in rules.MUSIC.values()), mtab,
                                                       ' — 빨리감기 %g배용 (템포 ×%g%s)' % (ff, ff, ', 음 낮춤' if rules.MUSIC_FF_PITCH else '') if ff != 1 else ''))
    # 인트로 박사 그림 → 겐나이 (사용자: 「이름만 겐나이로 나와서 아쉽다」, 그림 세션 art/gennai_portrait.png). 직업 POKEMON_PROF = 10
    gp = os.path.join(WEB, 'art', 'gennai_portrait.png')
    if os.path.exists(gp): P.log.append('인트로 박사 그림 → 겐나이 (색 %s)' % (P.trainer_pic(10, gp),))
    # 주인공 그림 → 태일 (주문서: art/taichi_front.png 56×56 · taichi_back.png 48×48, 카드는 taichi_card.png 또는 폭 40 이하인 앞모습)
    tf, tc, tb = (os.path.join(WEB, 'art', 'taichi_%s.png' % s) for s in ('front', 'card', 'back'))
    tf = tf if os.path.exists(tf) else None; tb = tb if os.path.exists(tb) else None
    tc = tc if os.path.exists(tc) else (tf if tf and Image.open(tf).width <= 40 else None)
    if tf or tb: P.log.append('주인공 그림 → 태일: ' + ', '.join(P.player_pics(tf, tc, tb)))
    # 제목 화면: 한글 로고(art/title/logo.png, title_logo.py) + 칠색조 자리에 디지몬 (title.py)
    import title
    mon = os.path.join(WEB, 'art', rules.TITLE_MON[0] + ('.png' if '/' in rules.TITLE_MON[0] else '-f.png'))
    npc, nbg = title.apply(P, rules.TITLE_LOGO and os.path.join(WEB, 'art', 'title', rules.TITLE_LOGO), mon, rules.TITLE_MON[1], digital=rules.TITLE_BG == 'digital')
    P.log.append('제목 화면: 로고 %s, 칠색조 → %s (스프라이트 %d조각), 배경 %s (새 타일 %d)' % (rules.TITLE_LOGO or '1.4 그대로', rules.TITLE_MON[0], npc, rules.TITLE_BG, nbg))
    # 도감 새 글 (dex_texts.json, 사용자 지시 2026-10-02): 금 원문 그대로였던 남길 종 58종. 키·몸무게는 지금 롬 값 그대로
    DX = json.load(open(os.path.join(HERE, 'dex_texts.json'))); N = {r.name(n): n for n in range(1, dmrom.NUM + 1)}; ndx = 0
    nfree = P.dex_pool([n for n in range(1, dmrom.NUM + 1) if r.name(n) == rules.EMPTY_NAME])
    for nm, v in DX.items():
        if nm.startswith('_') or nm not in N: continue
        e = P.dex_entry(N[nm]); i = 0
        while e[i] != 0x50: i += 2 if 1 <= e[i] <= 0x0b else 1          # 분류 끝 '@'
        P.dex(N[nm], v[0], e[i + 1], e[i + 2] | e[i + 3] << 8, v[1:]); ndx += 1
    P.log.append('도감 새 글 %d종 (dex_texts.json), 빈 칸 도감 자리 %d바이트를 옮길 곳으로' % (ndx, nfree))
    # G단계 메뉴 아이콘 10종: art/icons/<분류>.png(tools/icons.py)를 금 아이콘 10칸에 같은 크기(128바이트)로 덮어쓰고, 디지몬 칸마다 배정 (icons.json)
    sys.path.insert(0, os.path.join(WEB, 'tools')); import icons as ICN
    gm = re.search(rb'\x11(..)\x19\x2a\x5f\x56\xe1\x01\x08(.)', bytes(P.d), re.S)
    itab = addr(gm.start() // 0x4000, int.from_bytes(gm.group(1), 'little')); ib = gm.group(2)[0]
    for cat, (_, iid) in ICN.CATS.items():
        g = np.asarray(Image.open(os.path.join(WEB, 'art', 'icons', cat + '.png')).convert('L')).astype(int)
        v = np.select([g > 212, g > 127, g > 42], [0, 1, 2], 3); gfx = bytearray()
        for ty in range(4):
            for tx in range(2):
                for y in range(8):
                    row = v[ty * 8 + y, tx * 8:tx * 8 + 8]
                    gfx += bytes([sum((int(c) & 1) << (7 - i) for i, c in enumerate(row)), sum(((int(c) >> 1) & 1) << (7 - i) for i, c in enumerate(row))])
        P.put(addr(ib, P.d[itab + 2 * iid] | P.d[itab + 2 * iid + 1] << 8), bytes(gfx))
    IC = json.load(open(os.path.join(HERE, 'icons.json'))); cat_of = {n_: k for k, v in IC.items() if not k.startswith('_') for n_ in v}
    TYPE_CAT = {20: '공룡', 26: '공룡', 0: '짐승', 2: '새', 7: '벌레', 22: '식물', 21: '바다', 9: '기계', 24: '천사', 8: '악마', 27: '악마', 25: '짐승'}
    nic, by_type = 0, []
    for n_ in range(1, dmrom.NUM + 1):
        nm = r.name(n_)
        if nm == rules.EMPTY_NAME: continue
        cat = cat_of.get(nm)
        if cat is None: cat = TYPE_CAT.get(P.d[r.bs + 0x20 * (n_ - 1) + 7], '짐승'); by_type.append('%s(%s)' % (nm, cat))
        P.icon(n_, ICN.CATS[cat][1]); nic += 1
    P.log.append('G단계 메뉴 아이콘 10종: %d칸 배정%s' % (nic, ', 타입으로 정한 칸 ' + ', '.join(by_type) if by_type else ''))
    P.r.d = P.d
    open(out_rom, 'wb').write(bytes(P.d))
    n = P.ips(out_ips)
    P.log.append('패치 %d바이트 → %s' % (n, out_ips))
    return P

if __name__ == '__main__':
    os.makedirs(dmrom.WORK, exist_ok=True)
    P = build(dmrom.default_rom(), os.path.join(dmrom.WORK, 'myver.gbc'), os.path.join(dmrom.WORK, 'myver.ips'))
    print('\n'.join(P.log))
