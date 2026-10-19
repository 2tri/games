"""풀숲에서 지그재그로 걷다가 전투가 시작되면 화면을 찍고 도망치는 걸 반복한다. 롬은 복사본, 화면은 shots/enc_N.png"""
import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image, ImageChops

E = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(E, 'shots'); os.makedirs(OUT, exist_ok=True)
emu = DeSmuME(); emu.open(os.path.join(E, sys.argv[1])); emu.volume_set(0)
emu.savestate.load_file(os.path.join(E, sys.argv[2]))
WANT = int(sys.argv[3]) if len(sys.argv) > 3 else 6

def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=8):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def top():
    return emu.screenshot().crop((0, 0, 256, 192))
def in_battle():
    # 전투 화면 위쪽은 하단 이름판이 있는 어두운 파랑 바탕 — 지도 화면보다 훨씬 단색에 가깝다
    im = top().convert('RGB').resize((32, 24)); px = list(im.getdata())
    return sum(1 for r, g, b in px if b > r + 15 and b > g) > 300 or False

found = 0; steps = 0
dirs = [Keys.KEY_LEFT, Keys.KEY_RIGHT]
before = None
while found < WANT and steps < 400:
    press(dirs[steps % 2], 16, 2); steps += 1
    if steps % 4 == 0:
        run(30)
        im = emu.screenshot()
        # 전투 판정: 아래 화면이 초록(메뉴)이 아니라 베이지(전투 배경)이거나, 위 화면 아래쪽에 대사 상자
        bot = im.crop((0, 192, 256, 384)).convert('RGB').getpixel((128, 20))
        if bot[1] > 200 and bot[0] > 200:       # 전투 메뉴의 연한 바탕
            run(150); im = emu.screenshot()
            found += 1
            im.save(os.path.join(OUT, 'enc_%d.png' % found))
            # 도망
            for _ in range(3):
                run(40)
                emu.input.touch_set_pos(128, 176); run(4); emu.input.touch_release(); run(80)
            for _ in range(6): press(Keys.KEY_B, 4, 40)
            run(60)
emu.savestate.save_file(os.path.join(E, 's_enc_end.dst'))
print('만난 횟수', found, '걸음', steps)
emu.destroy()
