"""python attrtest.py <롬(mkenemy 로 만든 사본)> <내 종> <레벨> — 전투 중 피해 계산 훅(0x02252A3A→3E) 앞뒤 피해를 기록: 나가는 피해 / 들어온 피해 = 속성 배율"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/home/user/games')
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom_path, sp, lv = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
R = NDS(open(rom_path, 'rb').read()); personal = NARC(R.get(hg1.NARC_PATHS['personal'])).files
W = NARC(R.get('a/0/1/1')).files; PPD = {i: W[i][6] for i in range(len(W)) if len(W[i]) > 6}
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0); emu.savestate.load_file('ag4.dst')
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
def touch(x, y): emu.input.touch_set_pos(x, y); run(8); emu.input.touch_release(); run(30)
PROBE = []; _pend = {}
def cb_in(addr, size):
    r = emu.memory.register_arm9; sp_, r5, r6, r7 = r.sp, r.r5, r.r6, r.r7
    dmg = struct.unpack('<i', bytes(emu.memory.unsigned[sp_ + 0x50:sp_ + 0x54]))[0]
    sa = struct.unpack('<H', bytes(emu.memory.unsigned[r5 + 0x2D40 + 0xC0 * r7:r5 + 0x2D42 + 0xC0 * r7]))[0]
    sd = struct.unpack('<H', bytes(emu.memory.unsigned[r5 + 0x2D40 + 0xC0 * r6:r5 + 0x2D42 + 0xC0 * r6]))[0]
    _pend['x'] = (sa, sd, dmg)
def cb_out(addr, size):
    if 'x' in _pend:
        x = _pend.pop('x'); r0 = emu.memory.register_arm9.r0
        if r0 >= 0x80000000: r0 -= 1 << 32
        PROBE.append(x + (r0,))
emu.memory.register_exec(0x02252A3A, cb_in); emu.memory.register_exec(0x02252A3E, cb_out)
run(5); walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
ADDRS = (0x0227cce8, 0x022bc958); tmpl = bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236])
new = pkm.make_mon(tmpl, sp, lv, [33], personal, 0, pp=PPD)
for a in ADDRS:
    for i, b in enumerate(new): emu.memory.unsigned[a + i] = b
walk(Keys.KEY_RIGHT, 1); walk(Keys.KEY_UP, 1); press(Keys.KEY_A)
def is_menu(img):
    px = img.crop((0, 192, 256, 384)).convert('RGB').getpixel((128, 70)); return px[0] > 180 and px[1] < 90 and px[2] < 90
for i in range(60):
    run(60)
    if is_menu(emu.screenshot()): break
    press(Keys.KEY_A, 4, 10)
for turn in range(4):
    touch(128, 70); run(20); touch(64, 55)
    for t in range(0, 1500, 30):
        run(30)
        if t > 150 and is_menu(emu.screenshot()): break
        if t % 90 == 60: press(Keys.KEY_A, 4, 0)
print(json.dumps(PROBE))
