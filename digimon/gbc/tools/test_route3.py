"""우정의 신전(레오몬 뒤) → 사바나 동쪽 → 3번 길 (덤비는 성숙기 2) → 장난감 마을 → 순수의 신전 퍼펫몬"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
ID = json.load(open(os.path.join(S, 'ids.json'))); MP = ID['maps']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/savanna.state'); e.tick(5)
G = SYM['_G']; FLAGS_OFF = 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 16
e.pb.memory[G + 16] = 40; e.pb.memory[G + 19] = 200; e.pb.memory[G + 20] = 0      # 시험용 Lv40·체력 가득
walk(e, 'down', 4); settle(e); log('savanna', gstate(e))
walk(e, 'down', 3); walk(e, 'right', 8); settle(e); log('route3', gstate(e), MP['route3'])
for i in range(26):
    walk(e, 'right', 1); settle(e, 1500)
    if gstate(e)['map'] == MP['toytown']: break
log('toytown', gstate(e)); e.shot('r3_toy')
walk(e, 'right', 7)
for i in range(6):
    walk(e, 'up', 1); settle(e)
    if gstate(e)['map'] == MP['temple2']: break
log('temple2', gstate(e))
walk(e, 'up', 3); e.press('a', 4, 30); settle(e, 1500)
log('after monzaemon', gstate(e), 'crests', bin(e.pb.memory[G + FLAGS_OFF + 32])); e.shot('r3_after')
from emu import save_state; save_state(e, S + '/toytown.state'); e.stop()
