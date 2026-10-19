import sys; sys.argv=['x','../../_emu_test.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/ft','126']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 76); run(60)
for _ in range(7): press(Keys.KEY_B, 4, 45)
run(90)
import itertools
for nmk, k in (('D', Keys.KEY_DOWN), ('U', Keys.KEY_UP), ('L', Keys.KEY_LEFT), ('R', Keys.KEY_RIGHT)):
    m = keymask(k); emu.input.keypad_add_key(m)
    for f in range(40):
        run(1)
        if f in (12, 20, 28, 36): shot('%s%d' % (nmk, f))
    emu.input.keypad_rm_key(m); run(30)
