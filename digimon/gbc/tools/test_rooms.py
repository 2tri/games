"""회복 센터·상점 안 (A7·A8) · 주인공 정보 초상 (test_play 다음, vil.state)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
ID = json.load(open(os.path.join(S, 'ids.json'))); MP = ID['maps']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
m = e.pb.memory; G = SYM['_G']
load_state(e, S + '/vil.state'); e.tick(5)
def p(b, n=1, after=40):
    for _ in range(n): e.press(b, 4, after)
log('start', gstate(e))
# 주인공 정보
p('start', 1, 30); p('down', 3); p('a', 1, 60); e.shot('room_card'); p('b', 1, 30); p('b', 1, 30); settle(e)
# 회복 센터: 문(7,5) 아래(7,6)에서 위로
walk(e, 'up', 1); settle(e); log('center?', gstate(e), MP['center']); e.tick(20); e.shot('room_center')
walk(e, 'up', 5); p('a', 1, 20)
for i in range(40):
    if m[SYM['_field_idle']] and not m[SYM['_tb_shown']]: break
    p('a', 1, 20)
log('healed', gstate(e))
walk(e, 'left', 4); walk(e, 'up', 2); p('a', 1, 40); e.shot('room_pc'); p('b', 3, 30); settle(e)
walk(e, 'down', 2); walk(e, 'right', 4); walk(e, 'down', 6); settle(e); log('out', gstate(e))
# 상점: 문(12,4)
walk(e, 'right', 5); walk(e, 'up', 2); settle(e); log('shop?', gstate(e), MP['dshop']); e.tick(20); e.shot('room_shop')
walk(e, 'right', 4); e.press('up', 3, 20); p('a', 1, 30)
for i in range(6): p('a', 1, 30)
e.shot('room_shop_menu'); log('shop end', gstate(e)); e.stop()
