import sys
sys.argv=['x','../../_emu_test.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/ft3','126']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 76); run(60)
for _ in range(7): press(Keys.KEY_B, 4, 45)
run(90)
def seq(label, key, pre):
    mm = keymask(pre); emu.input.keypad_add_key(mm); run(20); emu.input.keypad_rm_key(mm); run(60)
    m = keymask(key); emu.input.keypad_add_key(m)
    for f in range(36):
        run(1)
        if f in (10, 24, 35): emu.screenshot().crop((60, 40, 200, 130)).save('%s_%s_w%d.png' % (tag, label, f))
    emu.input.keypad_rm_key(m); run(6); emu.screenshot().crop((60, 40, 200, 130)).save('%s_%s_s0.png' % (tag, label))
    run(40); emu.screenshot().crop((60, 40, 200, 130)).save('%s_%s_s1.png' % (tag, label))
seq('U', Keys.KEY_UP, Keys.KEY_LEFT)
seq('D', Keys.KEY_DOWN, Keys.KEY_RIGHT)
seq('L', Keys.KEY_LEFT, Keys.KEY_UP)
seq('R', Keys.KEY_RIGHT, Keys.KEY_DOWN)
