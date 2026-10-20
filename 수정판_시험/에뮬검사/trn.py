"""python trn.py <롬> <폴더> <트레이너 번호> — 연구소에서 내 첫 마리를 아구몬 Lv100(파괴광선)으로 바꾸고 그 트레이너와 전투: 도입 화면·첫 마리·한 대 친 뒤를 저장"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/home/user/games')
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image
rom_path, out, tid = sys.argv[1], sys.argv[2], int(sys.argv[3]); os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
R = NDS(open(rom_path, 'rb').read()); personal = NARC(R.get(hg1.NARC_PATHS['personal'])).files
W = NARC(R.get('a/0/1/1')).files; PPD = {i: W[i][6] for i in range(len(W)) if len(W[i]) > 6}
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0); emu.savestate.load_file(os.path.join(HERE, 'ag4.dst'))
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
def touch(x, y): emu.input.touch_set_pos(x, y); run(8); emu.input.touch_release(); run(30)
def is_menu(img):
    px = img.crop((0, 192, 256, 384)).convert('RGB').getpixel((128, 70)); return px[0] > 180 and px[1] < 90 and px[2] < 90
run(5); walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
ADDRS = (0x0227cce8, 0x022bc958)
tmpl = bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236]); new = pkm.make_mon(tmpl, 252, 100, [63], personal, 0, pp=PPD)
for a in ADDRS:
    for i, b in enumerate(new): emu.memory.unsigned[a + i] = b
walk(Keys.KEY_RIGHT, 1); walk(Keys.KEY_UP, 1); press(Keys.KEY_A)
frames = []; menu_seen = False; res = dict(tid=tid, menu=False)
for t in range(0, 3600, 20):
    run(20); im = emu.screenshot(); frames.append(im.copy())
    if t % 80 == 60 and not is_menu(im): press(Keys.KEY_A, 4, 0)
    if is_menu(im): menu_seen = True; res['menu'] = True; res['t_menu'] = t; im.save(out + '/menu.png'); break
# 도입 필름: 앞쪽 프레임 여러 장
sel = [frames[min(len(frames) - 1, i)] for i in (8, 20, 35)] + [frames[-1]] if menu_seen else frames[::max(1, len(frames) // 4)][:4]
row = Image.new('RGB', (128 * len(sel), 96))
for i, f in enumerate(sel): row.paste(f.crop((0, 0, 256, 192)).resize((128, 96)), (i * 128, 0))
row.save(out + '/intro.png')
if menu_seen:
    touch(128, 70); run(20); touch(64, 55)
    for t in range(0, 900, 20):
        run(20)
        if t % 80 == 60: press(Keys.KEY_A, 4, 0)
    emu.screenshot().save(out + '/after.png')
    res['after_menu'] = is_menu(emu.screenshot())
json.dump(res, open(out + '/res.json', 'w')); print(json.dumps(res))
