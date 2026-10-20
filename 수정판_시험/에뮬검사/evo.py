"""python evo.py <롬> <폴더> <출발 종> <방법> <값> <도착 종> — 레벨 직전까지 올린 출발 종으로 소라전에서 이겨 진화하는지(진화 뒤 파티 종 번호) 확인"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/home/user/games')
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom_path, out, src, meth, val, tgt = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
os.makedirs(out, exist_ok=True); HERE = os.path.dirname(os.path.abspath(__file__))
R = NDS(open(rom_path, 'rb').read()); personal = NARC(R.get(hg1.NARC_PATHS['personal'])).files
W = NARC(R.get('a/0/1/1')).files; PPD = {i: W[i][6] for i in range(len(W)) if len(W[i]) > 6}
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0); emu.savestate.load_file(os.path.join(HERE, 'ag4.dst'))
HOUR = os.environ.get('HOUR')
RTC = (0x021d1a58 + 16, 0x021d1a74 + 16)
def run(n):
    for _ in range(n):
        if HOUR:
            for a in RTC: emu.memory.unsigned[a] = int(HOUR)
        emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
def touch(x, y): emu.input.touch_set_pos(x, y); run(8); emu.input.touch_release(); run(30)
growth = personal[src][19]
L = int(os.environ.get('LV', val if meth == 4 else 30))
item = int(os.environ.get('HOLD', val if meth in (18, 19) else 0))
moves = [33] + ([val] if meth == 20 else [])
tmpl = None
run(5); walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
ADDRS = (0x0227cce8, 0x022bc958)
tmpl = bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236])
new = pkm.make_mon(tmpl, src, L - 1, moves, personal, item, exp=pkm.exp_for(growth, L) - 1, pp=PPD)
if meth == 1:      # 친밀도 진화: 친밀도 칸(블록 A 0x14) 255
    pk = pkm.decode(new); A = bytearray(pk['blocks']['A']); A[0x14 - 0x08 + 0] = 255; pk['blocks']['A'] = bytes(A); new = pkm.encode(pk)
for a in ADDRS:
    for i, b in enumerate(new): emu.memory.unsigned[a + i] = b
walk(Keys.KEY_RIGHT, 1); walk(Keys.KEY_UP, 1); press(Keys.KEY_A)
def is_menu(img):
    px = img.getpixel((128, 70)); return px[0] > 180 and px[1] < 90 and px[2] < 90
shots = 0
for t in range(0, 9000, 30):
    run(30)
    im = emu.screenshot()
    if is_menu(im.crop((0, 192, 256, 384)).convert('RGB')):
        touch(128, 70); run(20); touch(64, 55)
    elif t % 60 == 0: press(Keys.KEY_A, 4, 0)
    dense = os.environ.get('EVO_DENSE')
    if (t % 90 == 0 and shots < 60 and t >= 600 if dense else t % 600 == 0 and shots < 14): im.save('%s/f%02d.png' % (out, shots)); shots += 1
    cur = pkm.species(pkm.decode(bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236])))
    if cur != src and t > 300: break
run(60)
cur = pkm.species(pkm.decode(bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236])))
lvl = pkm.level(pkm.decode(bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236])))
emu.screenshot().save(out + '/end.png')
res = dict(src=src, meth=meth, val=val, tgt=tgt, got=cur, lv=lvl, ok=(cur == tgt), frames=t)
json.dump(res, open(out + '/res.json', 'w')); print(json.dumps(res))
