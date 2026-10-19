import sys; sys.argv=['x','../../_emu_rom.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/y26','26']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 76); run(60)
press(Keys.KEY_A, 4, 50); press(Keys.KEY_A, 4, 20); shot('a')
run(40); shot('b'); run(80); shot('c'); run(200); shot('d')
