import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(30)
def cyan_btn():
    im = emu.screenshot().convert('RGB')
    for y in range(335, 355, 3):
        for x in range(60, 200, 8):
            r, g, b = im.getpixel((x, y))
            if r < 90 and g > 150 and b > 150: return True
    return False
run(300); n = 0; touched = False; named = False
while n < int(sys.argv[3]):
    n += 1
    if not touched and cyan_btn():
        run(40); touch(130, 151); run(80); touched = True
        emu.screenshot().save(os.path.join(out, 'after_touch.png')); continue
    q = emu.screenshot().convert('RGB').getpixel((4, 198))
    if touched and not named and q[1] > 170 and q[2] < 110 and q[0] > 120:
        press(Keys.KEY_START, 4, 60); press(Keys.KEY_A, 4, 60); named = True; continue
    press(Keys.KEY_A, 4, 40)
    if n % 20 == 0: emu.screenshot().save(os.path.join(out, 'f%03d.png' % n))
emu.savestate.save_file(os.path.join(out, 'end.dst'))
print('끝', n, touched, named, flush=True)
