import sys, os, struct
A1=int(__import__('os').environ.get('A1','0x0227cce8'),16); A2=int(__import__('os').environ.get('A2','0x022bc958'),16)
sys.path.insert(0,'.'); sys.path.insert(0,'/home/user/games')
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom_path, out, tid, sp1, sp2 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); os.makedirs(out, exist_ok=True)
R = NDS(open(rom_path, 'rb').read()); personal = NARC(R.get(hg1.NARC_PATHS['personal'])).files
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0); emu.savestate.load_file(os.environ.get('STATE','ag4.dst'))
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
run(5)
if not os.environ.get('NOLEFT'): walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
for a in (A1, A2):
    print(hex(a), 'before', list(emu.memory.unsigned[a - 8:a]))
tmpl = bytes(emu.memory.unsigned[A1:A1 + 236])
m1 = pkm.make_mon(tmpl, sp1 or 252, 50, [33], personal); m2 = pkm.make_mon(tmpl, sp2 or 252, 50, [33], personal)
for a in (A1, A2) if sp1 else ():
    for i, b in enumerate(m1): emu.memory.unsigned[a + i] = b
    if sp2:
        for i, b in enumerate(m2): emu.memory.unsigned[a + 236 + i] = b
        emu.memory.unsigned[a - 4] = 2
if not os.environ.get('NOLEFT'): walk(Keys.KEY_RIGHT, 1)
walk(Keys.KEY_UP, 1); press(Keys.KEY_A)
frames=[]
for t in range(0, 2400, 20):
    run(20)
    im = emu.screenshot(); frames.append(im.crop((0,0,256,192)).resize((128,96)))
    px = im.crop((0, 192, 256, 384)).convert('RGB').getpixel((128, 70))
    if px[0] > 180 and px[1] < 90 and px[2] < 90:
        im.save(out + '/menu.png'); print('menu', t)
        for k in range(1,6): run(60); emu.screenshot().save(out+'/after%d.png'%k)
        break
    if t % 80 == 60: press(Keys.KEY_A, 4, 0)

from PIL import Image
sel=frames[::max(1,len(frames)//16)][:16]
sh=Image.new('RGB',(128*8,96*2))
for i,f in enumerate(sel): sh.paste(f,((i%8)*128,(i//8)*96))
sh.save(out+'/film.png')
