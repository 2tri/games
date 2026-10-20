"""python lab2.py <롬> <폴더> <종> <레벨> <기술,..> [item] — 지정 종·기술로 소라전에 들어가 기술을 하나씩 쓰며(싸운다 → 기술 터치) 프레임 시트를 만든다"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '/home/user/games')
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageChops
rom_path, out, sp, lv, mv = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), [int(x) for x in sys.argv[5].split(',')]
item = int(sys.argv[6]) if len(sys.argv) > 6 else 0
os.makedirs(out, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
personal = NARC(NDS(open(rom_path, 'rb').read()).get(hg1.NARC_PATHS['personal'])).files
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0); emu.savestate.load_file(os.path.join(HERE, 'ag4.dst'))
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
def touch(x, y): emu.input.touch_set_pos(x, y); run(8); emu.input.touch_release(); run(30)
run(5); walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
ADDRS = (0x0227cce8, 0x022bc958)
tmpl = bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236]); W = NARC(NDS(open(rom_path, 'rb').read()).get('a/0/1/1')).files; PPD = {i: W[i][6] for i in range(len(W)) if len(W[i]) > 6}
new = pkm.make_mon(tmpl, sp, lv, mv, personal, item, pp=PPD)
for a in ADDRS:
    for i, b in enumerate(new): emu.memory.unsigned[a + i] = b
walk(Keys.KEY_RIGHT, 1); walk(Keys.KEY_UP, 1); press(Keys.KEY_A)
# 첫 「무엇을 할까?」까지 A
ref = None
def bottom(): return emu.screenshot().crop((0, 192, 256, 384)).convert('RGB')
def is_menu(img):   # 「싸운다」 빨간 큰 버튼이 있는가
    px = img.getpixel((128, 70)); return px[0] > 180 and px[1] < 90 and px[2] < 90
for i in range(60):
    run(60)
    if is_menu(bottom()): break
    press(Keys.KEY_A, 4, 10)
else:
    print('메뉴 못 찾음'); emu.screenshot().save(out + '/fail.png'); sys.exit(1)
frames = []; log = []
MOVE_XY = [(64, 55), (192, 55), (64, 120), (192, 120)]
for k in range(len(mv)):
    touch(128, 70); run(20)
    if k == 0: emu.screenshot().save(out + '/menu.png')
    touch(*MOVE_XY[k]); n0 = len(frames)
    for t in range(0, 1500, 10):
        run(10); im = emu.screenshot(); frames.append(im.copy())
        if t % 60 == 50 and not os.environ.get('NOPRESS'): press(Keys.KEY_A, 4, 0)
        if t > 150 and is_menu(im.crop((0, 192, 256, 384)).convert('RGB')): break
    seg = frames[n0:]; act = 0.0
    import numpy as np
    arr = [np.asarray(f.crop((0, 0, 256, 140)).convert('L'), dtype=np.int16) for f in seg]
    for a, b in zip(arr, arr[1:]): act += float(np.abs(a - b).mean())
    log.append((k, mv[k], len(seg), round(act, 1)))
json.dump(log, open(out + '/log.json', 'w'))
# 시트: 기술마다 위 화면만 8열
tw, th = 128, 96
idx = 0
for k, m, n, act in log:
    ch = frames[idx:idx + n]; idx += n
    cols = 8; rows = (len(ch) + cols - 1) // cols
    sh = Image.new('RGB', (cols * tw, max(1, rows) * th))
    for i, im in enumerate(ch): sh.paste(im.crop((0, 0, 256, 192)).resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    sh.save('%s/move%d_%d.png' % (out, k, m))
emu.screenshot().save(out + '/end.png'); print('끝', log)
