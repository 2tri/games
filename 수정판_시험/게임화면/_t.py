import sys; sys.argv=['x','../../_emu_rom.nds','../../게임화면_오늘/d1015b/out4.dst','../../게임화면_오늘/d1015b/pt2','252,253,257,261,262,264']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 76); run(60); shot('p0')
press(Keys.KEY_A, 4, 50); shot('p1')
press(Keys.KEY_A, 4, 70); shot('p2')
press(Keys.KEY_A, 4, 70); shot('p3')
