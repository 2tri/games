"""python 글_화면검사_촬영.py <롬> <ag4.dst> <폴더> — 연구소 위쪽 NPC 에게 말을 걸어 대화 쪽마다 상자 영역을 찍음(30쪽)"""
import sys
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
emu = DeSmuME(); emu.open(sys.argv[1]); emu.volume_set(0); emu.savestate.load_file(sys.argv[2]); d = sys.argv[3]
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
run(5); press(Keys.KEY_UP, 3, 20); press(Keys.KEY_A, 4, 60)
for i in range(30):
    run(90); emu.screenshot().convert('RGB').crop((0, 140, 256, 192)).save('%s/p%02d.png' % (d, i)); press(Keys.KEY_A, 3, 10)
