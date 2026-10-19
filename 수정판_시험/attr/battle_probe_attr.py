"""python3 btest.py <rom> <P38.dst> <seed> [turns] [shotprefix] — 야생 전투 열고 매 턴 1번 기술, HP 변화 기록"""
import sys, os, struct, random
os.environ.setdefault('SDL_VIDEODRIVER','dummy'); os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, st, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]); turns = int(sys.argv[4]) if len(sys.argv) > 4 else 2
shot = sys.argv[5] if len(sys.argv) > 5 else None
random.seed(seed)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(st)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=20):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def rd(a, n): return bytes(emu.memory.unsigned[a:a + n])
PROBE = []
_pend = {}
def _rd32(a): return struct.unpack('<I', bytes(emu.memory.unsigned[a:a + 4]))[0]
def cb_in(addr, size):
    R = emu.memory.register_arm9
    sp, r5, r6, r7 = R.sp, R.r5, R.r6, R.r7
    dmg = struct.unpack('<i', bytes(emu.memory.unsigned[sp + 0x50:sp + 0x54]))[0]
    sa = struct.unpack('<H', bytes(emu.memory.unsigned[r5 + 0x2D40 + 0xC0 * r7:r5 + 0x2D42 + 0xC0 * r7]))[0]
    sd = struct.unpack('<H', bytes(emu.memory.unsigned[r5 + 0x2D40 + 0xC0 * r6:r5 + 0x2D42 + 0xC0 * r6]))[0]
    bs = _rd32(r5 + 0x213C); flag = _rd32(_rd32(sp + 0x54))
    _pend['x'] = (r7, r6, sa, sd, dmg, bs, flag)
def cb_out(addr, size):
    if 'x' in _pend:
        x = _pend.pop('x'); r0 = emu.memory.register_arm9.r0
        if r0 >= 0x80000000: r0 -= 1 << 32
        PROBE.append(x + (r0,)); print('PROBE 공격 %d(종 %d) → 방어 %d(종 %d) 피해 들어옴 %d 나감 %d (battleStatus %X, moveStatus %X)' % (x[0], x[2], x[1], x[3], x[4], r0, x[5], x[6]), flush=True)
emu.memory.register_exec(0x02252A3A, cb_in)
emu.memory.register_exec(0x02252A3E, cb_out)
OV12_HEAD = bytes.fromhex('78b589b00c1c061ccef5d4ff2168051c0f2900d911e1491879 44c988'.replace(' ', ''))
def inbattle(): return rd(0x022382C0, len(OV12_HEAD)) == OV12_HEAD
KEYS = [Keys.KEY_UP, Keys.KEY_DOWN, Keys.KEY_LEFT, Keys.KEY_RIGHT]
d = random.choice(KEYS)
for i in range(3000):
    if i % 5 == 0: d = random.choice(KEYS)
    m = keymask(d); emu.input.keypad_add_key(m); run(16); emu.input.keypad_rm_key(m); run(2)
    if inbattle(): break
    if i % 4 == 3: press(Keys.KEY_A, 4, 10)   # 트레이너 말 넘기기
    if inbattle(): break
else: print('no battle'); os._exit(1)
run(600)
hook = rd(0x02252A3A, 4).hex(); tab = rd(0x0226D680, 4).hex(); par = rd(0x0226D700, 8).hex()
ram = rd(0x02200000, 0x200000)
mons = None
for i in range(0, len(ram) - 0x200, 4):
    if struct.unpack_from('<H', ram, i)[0] == 277:
        sp2 = struct.unpack_from('<H', ram, i + 0xC0)[0]; hp = struct.unpack_from('<i', ram, i + 0x4C)[0]
        ok = 1 <= sp2 <= 493
        for k in (0, 1):
            b = ram[i + 0xC0 * k:i + 0xC0 * (k + 1)]
            hp_, mhp = struct.unpack_from('<iI', b, 0x4C)
            ok &= b[0x24] <= 17 and b[0x25] <= 17 and 1 <= b[0x34] <= 100 and 0 < hp_ <= mhp < 1000
        if ok: mons = 0x02200000 + i; break
if mons is None: print('battleMons 못 찾음'); os._exit(1)
def mon(k):
    b = rd(mons + 0xC0 * k, 0xC0)
    return dict(sp=struct.unpack_from('<H', b, 0)[0], lv=b[0x34], hp=struct.unpack_from('<i', b, 0x4C)[0], mv=struct.unpack_from('<H', b, 0xC)[0], t=(b[0x24], b[0x25]))
a, e = mon(0), mon(1)
print('ov12 훅자리 %s 표 %s 배율 %s | 우리 %s | 적 %s' % (hook, tab, par, a, e), flush=True)
for t in range(turns):
    h0, h1 = mon(0)['hp'], mon(1)['hp']
    press(Keys.KEY_A, 4, 60)      # 싸우다
    press(Keys.KEY_A, 4, 60)      # 1번 기술
    for _ in range(40):
        run(60)
        if mon(1)['hp'] <= 0 or mon(0)['hp'] <= 0: break
        pass
    # 다음 명령 고르기 화면이 될 때까지
    run(300)
    n0, n1 = mon(0)['hp'], mon(1)['hp']
    print('턴 %d: 적 HP %d→%d (피해 %d), 우리 HP %d→%d (피해 %d)' % (t + 1, h1, n1, h1 - n1, h0, n0, h0 - n0), flush=True)
    if shot: emu.screenshot().save('%s_t%d.png' % (shot, t + 1))
    if n1 <= 0 or n0 <= 0: break
os._exit(0)
