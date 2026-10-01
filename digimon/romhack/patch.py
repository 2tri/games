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
 4. 롬에 없던 코로몬 추가 (꼬리선 자리, 1번 길 부근 야생) → Lv11 아구몬
 5. 디지몬스터 버그: 메탈가루몬 진화 목록 끝 표시 없음 → 고침 (Lv39에 팔몬이 되던 문제)
"""
import os, sys, json, struct
import numpy as np
from PIL import Image
import dmrom, gblz, krtext
from dmrom import addr, bankptr

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
HIGH_BOND, LOW_BOND = 100, 40
CREST_BIT = {'사랑': 0, '지식': 1, '순수': 2, '빛': 3, '우정': 4, '용기': 5, '성실': 6, '희망': 7}
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
    crest = {'그레이몬': '용기', '가루몬': '우정', '버드라몬': '사랑', '캅테리몬': '지식', '니드몬': '순수', '원뿔몬': '성실', '엔젤몬': '희망', '가트몬': '빛'}
    P.evo_engine({S(nm): 1 << CREST_BIT[c] for nm, c in crest.items()})
    # 성숙기 → 완전체: 자기 문장이면 Lv30 (희망은 원래대로 25), 아니면 문장 하나 이상 + 원래 레벨
    P.evos(S('그레이몬'), [(CREST, 30, S('워그레이몬')), (ANYCREST, 36, S('워그레이몬'))])      # 메탈그레이몬 그림 오면 그쪽으로
    P.evos(S('가루몬'), [(CREST, 30, S('메탈가루몬')), (ANYCREST, 36, S('메탈가루몬'))])
    P.evos(S('버드라몬'), [(CREST, 30, S('가루다몬')), (ANYCREST, 36, S('가루다몬'))])
    P.evos(S('캅테리몬'), [(CREST, 30, S('아트캅테몬')), (ANYCREST, 40, S('아트캅테몬')), (ITEM, 169, S('로제몬'))])   # 로제몬 갈래는 그대로
    P.evos(S('니드몬'), [(CREST, 30, S('릴리몬')), (ANYCREST, 32, S('릴리몬'))])
    P.evos(S('원뿔몬'), [(CREST, 30, S('쥬드몬')), (ANYCREST, 36, S('쥬드몬'))])           # 원래 통신 교환 진화라 혼자서는 못 했음
    P.evos(S('엔젤몬'), [(CREST, 25, S('홀리엔젤몬')), (ANYCREST, 32, S('홀리엔젤몬'))])
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
