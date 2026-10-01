"""디지몬스터(한글판 포켓몬 금 개조) 롬 읽기·쓰기 도구
표 위치는 코드 모양(서명)으로 찾는다 → 2014판·2.0판 어느 쪽이든 같은 방법으로.
롬 파일·뽑아낸 그림은 저장소에 올리지 않는다 (work/ 는 .gitignore)."""
import os, re, struct
import numpy as np
import krtext, gblz

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
NUM = 251

def addr(bank, ptr): return bank * 0x4000 + (ptr - 0x4000 if bank else ptr)
def bankptr(a): return a // 0x4000, (a % 0x4000) + (0x4000 if a >= 0x4000 else 0)

class Rom:
    def __init__(self, path):
        self.path = path
        self.d = bytearray(open(path, 'rb').read())
        self.base = bytes(self.d)
        self.find()

    # ── 표 찾기 ──
    def find(self):
        d = bytes(self.d)
        # 능력치: 0x20 바이트마다 종 번호 1..251
        self.bs = next(x for x in range(len(d) - 0x20 * NUM) if d[x] == 1 and all(d[x + 0x20 * k] == k + 1 for k in range(NUM)))
        # 그림 포인터: GetFrontpic 의 ld hl, PokemonPicPointers / ld d, BANK / cp UNOWN
        m = re.search(rb'\x21(..)\xfa..\x16(.)\xfe\xc9', d, re.S)
        self.pics = addr(m.group(2)[0], int.from_bytes(m.group(1), 'little'))
        # FixPicBank 표 (13 xx 14 xx 1f xx ff)
        m = re.search(rb'\x13(.)\x14(.)\x1f(.)\xff', d, re.S)
        self.fix = {0x13: m.group(1)[0], 0x14: m.group(2)[0], 0x1f: m.group(3)[0]}
        # 팔레트: _GetMonPalettePointer (ld l,a / ld h,0 / add hl,hl ×3 / ld bc,X / add hl,bc / ret) 중 0번 항목이 회색 계열인 것
        self.pal = None
        for m in re.finditer(rb'\x6f\x26\x00\x29\x29\x29\x01(..)\x09\xc9', d, re.S):
            a = addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little'))
            if d[a:a + 8] != d[a + 8:a + 16] or True:
                c = struct.unpack('<4H', d[a:a + 8])
                if c[0] == c[2]: self.pal = a        # 000 항목은 일반·색다른 색이 같음
        # 이름: 10바이트 칸 251개, 각 칸이 한글 글자 + 0x50 채움
        a1 = krtext.encode(self.name_guess())
        self.names = None
        i = d.find(a1)
        while i >= 0:
            if self._names_ok(i - 10 * (self.guess_no - 1)): self.names = i - 10 * (self.guess_no - 1); break
            i = d.find(a1, i + 1)
        # 진화·기술 포인터 표: EvosAttacksPointers (2바이트 × 251), 같은 뱅크 안을 가리킴
        self.evos = self._find_evos()

    def name_guess(self):
        self.guess_no = 4; return '아구몬'
    def _names_ok(self, a):
        d = self.d
        if a < 0: return False
        for k in range(NUM):
            e = d[a + 10 * k:a + 10 * k + 10]
            if e[0] == 0x50: return False
            s = krtext.decode(e, 0, 10)
            if '{' in s: return False
        return True
    def _find_evos(self):
        d = bytes(self.d)
        # GetPokemonEvosAttacks 류: ld hl, EvosAttacksPointers / ld a, BANK(..) 를 직접 찾기 어렵다 → 모양으로:
        # 같은 뱅크 포인터 251개, 오름차순, 각 대상이 '진화 목록(0으로 끝) + 기술 목록(0으로 끝)' 형식
        for bank in range(0x0c, 0x80):
            base = bank * 0x4000
            for off in range(0, 0x4000 - 2 * NUM, 1):
                a = base + off
                p0 = d[a] | d[a + 1] << 8
                if not (0x4000 <= p0 < 0x8000): continue
                ps = struct.unpack('<%dH' % NUM, d[a:a + 2 * NUM])
                if any(not (0x4000 <= p < 0x8000) for p in ps): continue
                # 원본은 오름차순·첫 칸이 표 바로 뒤. 고친 롬은 일부가 빈 곳으로 옮겨가므로 '대부분 오름차순 + 최솟값이 표 바로 뒤'로 본다
                if min(ps) != 0x4000 + off + 2 * NUM: continue
                if sum(ps[i + 1] > ps[i] for i in range(NUM - 1)) < NUM * 3 // 4: continue
                return a
        return None

    # ── 읽기 ──
    def name(self, sp): return krtext.decode(self.d, self.names + 10 * (sp - 1), self.names + 10 * sp)
    def base_stats(self, sp):
        e = self.d[self.bs + 0x20 * (sp - 1):self.bs + 0x20 * sp]
        return {'hp': e[1], 'atk': e[2], 'def': e[3], 'spd': e[4], 'sat': e[5], 'sdf': e[6], 'type': (e[7], e[8]),
                'catch': e[9], 'exp': e[10], 'items': (e[11], e[12]), 'gender': e[13], 'egg_steps': e[15],
                'pic_size': e[17], 'growth': e[22], 'egg_groups': e[23], 'raw': bytes(e)}
    def palette(self, sp, shiny=False):
        a = self.pal + 8 * sp + (4 if shiny else 0)
        c = struct.unpack('<2H', self.d[a:a + 4])
        return [((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31) for v in c]
    def pic_ptr(self, sp, back=False):
        e = self.d[self.pics + 6 * (sp - 1) + (3 if back else 0):][:3]
        b = self.fix.get(e[0], e[0]); return addr(b, e[1] | e[2] << 8)
    def pic(self, sp, back=False):
        """→ (h,w) 색번호 0~3 배열"""
        if sp == 201: return None
        data, _ = gblz.decompress(self.d, self.pic_ptr(sp, back))
        if back: tw = th = 6
        else:
            s = self.d[self.bs + 0x20 * (sp - 1) + 17]; tw, th = s & 15, s >> 4
        n = tw * th; a = np.zeros((th * 8, tw * 8), np.uint8)
        for t in range(n):
            tx, ty = t // th, t % th           # 금판 그림은 세로 줄 먼저
            blk = data[t * 16:t * 16 + 16]
            if len(blk) < 16: break
            for r in range(8):
                lo, hi = blk[2 * r], blk[2 * r + 1]
                for c in range(8):
                    a[ty * 8 + r, tx * 8 + c] = ((lo >> (7 - c)) & 1) | (((hi >> (7 - c)) & 1) << 1)
        return a
    def evos_attacks(self, sp):
        """→ ([진화...], [(레벨, 기술)...]). 진화 = (종류, 값..., 대상)"""
        bank = self.evos // 0x4000
        p = self.d[self.evos + 2 * (sp - 1)] | self.d[self.evos + 2 * (sp - 1) + 1] << 8
        a = addr(bank, p); d = self.d; ev = []
        while d[a]:
            t = d[a]
            if t == 5: ev.append((t, d[a + 1], d[a + 2], d[a + 3])); a += 4     # EVOLVE_STAT: 레벨, 비교, 대상
            else: ev.append((t, d[a + 1], d[a + 2])); a += 3
        a += 1; mv = []
        while d[a]: mv.append((d[a], d[a + 1])); a += 2
        return ev, mv

    def free_runs(self, minlen=0x200):
        """뱅크 끝의 빈 곳 (FF 또는 00 연속) 목록"""
        out = []
        for bank in range(1, len(self.d) // 0x4000):
            b = bytes(self.d[bank * 0x4000:(bank + 1) * 0x4000])
            for fill in (0xff, 0x00):
                n = len(b) - len(b.rstrip(bytes([fill])))
                if n >= minlen: out.append((bank, 0x4000 + 0x4000 - n, n, fill)); break
        return out

    def save(self, path): open(path, 'wb').write(bytes(self.d))

def default_rom():
    for p in [os.environ.get('DMROM', ''), os.path.join(WORK, 'base.gbc'),
              '/tmp/claude-0/-home-user-games/6383e336-0dcf-5b3b-862b-dcfdcb19a4bd/scratchpad/rom/dm.gbc']:
        if p and os.path.exists(p): return p
    raise SystemExit('디지몬스터 롬이 없음: romhack/work/base.gbc 에 두거나 DMROM=경로')
