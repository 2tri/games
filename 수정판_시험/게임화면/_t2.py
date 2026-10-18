import sys; sys.argv=['x','../../_emu_rom.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/tc','252']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(125, 30); run(120); shot('card0')
press(Keys.KEY_A, 4, 60); run(60); shot('card1')
press(Keys.KEY_A, 4, 60); run(60); shot('card2')
for _ in range(4): press(Keys.KEY_B, 4, 50)
run(60)
touch(50, 100); run(100); shot('bag0')      # 가방
touch(100, 60); run(60); shot('bag1')
