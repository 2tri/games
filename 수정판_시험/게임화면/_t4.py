import sys; sys.argv=['x','../../_emu_rom2.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/bag','252']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 113); run(100); shot('b0')
touch(60, 30); run(60); shot('b1')
press(Keys.KEY_R, 4, 40); run(40); shot('b2')
press(Keys.KEY_R, 4, 40); run(40); shot('b3')
