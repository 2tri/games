import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 's_boot.dst'))
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
run(60); n = 0; touched = False; named = False; girl = False
while n < 700:
    n += 1
    if not touched and cyan_btn():
        run(40); touch(130, 151); run(80); touched = True
        emu.screenshot().save(os.path.join(out, 'after_touch.png')); continue
    q = emu.screenshot().convert('RGB').getpixel((4, 198))
    if touched and not named and q[1] > 170 and q[2] < 110 and q[0] > 120:
        press(Keys.KEY_START, 4, 60); press(Keys.KEY_A, 4, 60); named = True; continue
    if touched and not girl:
        im2 = emu.screenshot().convert('RGB')
        hit = any((lambda p: p[0] < 90 and p[1] > 150 and p[2] > 150)(im2.getpixel((x, y))) for x in range(150, 230, 6) for y in range(236, 262, 4))
        if hit:
            run(30); emu.screenshot().save(os.path.join(out, 'gender_boy_card.png'))
            touch(188, 138); run(120); emu.screenshot().save(os.path.join(out, 'gender_girl_q.png')); girl = True; continue
    press(Keys.KEY_A, 4, 40)
    if n % 6 == 0: emu.screenshot().save(os.path.join(out, 'f%03d.png' % n))
    if touched and n % 40 == 0: emu.savestate.save_file(os.path.join(out, 'prog.dst'))
emu.savestate.save_file(os.path.join(out, 'full_end.dst'))
print('끝', n, touched, named)
