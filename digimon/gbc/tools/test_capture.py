"""1번 길 풀숲에서 야생 디지몬을 만나 가방의 디지바이스로 포획 시도 (3번)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, tb, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
load_state(e, S + '/r1.state'); e.tick(5)
log = lambda *a: print(*a, flush=True)
walk(e, 'up', 3); walk(e, 'left', 2); log('in grass', gstate(e))
for i in range(80):                         # 풀숲 왔다 갔다 → 전투
    walk(e, 'left' if i % 2 else 'right', 1)
    if scene(e) != 1: break
log('battle?', scene(e), gstate(e))
for k in range(30): e.press('b', 3, 8)
e.shot('c1_menu')
for t in range(3):
    e.press('right', 3, 6); e.press('a', 3, 20); e.shot('c2_bag%d' % t)
    e.press('a', 3, 20)
    for k in range(12): e.press('b', 3, 10)
    e.shot('c3_after%d' % t)
    g = gstate(e); log('try', t, g)
    if scene(e) == 1 or g['nparty'] > 1: break
for k in range(20): e.press('b', 3, 10)
settle(e); log('end', gstate(e), 'bits', e.mem(SYM['_G'] + 0) if False else '')
e.shot('c4_end'); e.stop()
