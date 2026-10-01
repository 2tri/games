"""마을(에렉몬에게 그물 받은 뒤) → 1번 길 풀숲 → 유년기 그물로 포획 시도"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/vil.state'); e.tick(5)
walk(e, 'down', 8); settle(e); log('route1?', gstate(e))      # 회복 센터 문 앞(7,6) → 1번 길(4,0)
walk(e, 'down', 2); walk(e, 'left', 1); log('grass', gstate(e))
G = SYM['_G']
for b in range(6):
    for i in range(80):
        walk(e, 'left' if i % 2 else 'right', 1)
        if scene(e) != 1: break
    for k in range(30): e.press('b', 3, 8)
    e.shot('n%d_menu' % b)
    for t in range(4):
        e.press('right', 3, 10); e.press('a', 3, 60)          # 가방 (그리는 데 시간 걸림)
        e.press('down', 3, 45); e.press('down', 3, 45); e.shot('n%d_bag%d' % (b, t)); e.press('a', 3, 30)   # 유년기 그물
        for k in range(14): e.press('b', 3, 10)
        if scene(e) == 1: break
    e.shot('n%d_after' % b)
    for k in range(30):
        if scene(e) == 1: break
        e.press('a', 3, 10)
    settle(e)
    g = gstate(e); log('battle', b, g)
    if g['nparty'] > 2: break
log('end', gstate(e)); e.shot('n_end'); e.stop()
