"""해변(쉘몬을 이긴 것으로 깃발) → 2번 길 (덤비는 디지몬·떨어진 물건·턱) → 기어 사바나 → 우정의 신전 레오몬"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
ID = json.load(open(os.path.join(S, 'ids.json'))); FL = ID['flags']; MP = ID['maps']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/beach.state'); e.tick(5)
G = SYM['_G']; m = e.pb.memory
FLAGS_OFF = 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 8          # game_t 안 flags 위치
def setflag(n): i = FL[n]; m[G + FLAGS_OFF + (i >> 3)] |= 1 << (i & 7)
def crests(): return m[G + FLAGS_OFF + 32]
setflag('shellmon')
m[G + 16] = 30; m[G + 19] = 150; m[G + 20] = 0          # 시험용: 파트너 Lv30, 체력 150
walk(e, 'right', 8); walk(e, 'up', 6); log('beach top', gstate(e))      # 쉘몬 그림은 지도에 다시 들어올 때 사라지므로 옆 칸(8)으로
walk(e, 'up', 1); settle(e); log('route2', gstate(e), MP['route2'])
walk(e, 'up', 1); walk(e, 'left', 1)
for i in range(13):
    walk(e, 'up', 1); settle(e, 900)
log('after challenger', gstate(e)); e.shot('r2_mid')
walk(e, 'up', 1); walk(e, 'left', 3)
for i in range(4):
    walk(e, 'up', 1); settle(e, 1500)      # (4,3)에서 라이벌전
log('top', gstate(e), 'rival', bool(e.pb.memory[G + FLAGS_OFF + (FL['rival1'] >> 3)] & (1 << (FL['rival1'] & 7))))
walk(e, 'up', 1); settle(e); log('savanna', gstate(e), MP['savanna']); e.shot('r2_savanna')
for i in range(10):
    walk(e, 'up', 1); settle(e)
    if gstate(e)['map'] == MP['temple1']: break
log('temple', gstate(e)); e.shot('r2_temple')
walk(e, 'up', 5); e.shot('r2_leo'); print('oam', [ (e.mem(0xFE00+i*4), e.mem(0xFE00+i*4+1), e.mem(0xFE00+i*4+2), e.mem(0xFE00+i*4+3)) for i in range(4, 8)])
walk(e, 'up', 1); e.press('a', 4, 30); settle(e, 1500); log('after leomon', gstate(e), 'crests', bin(crests()))
e.shot('r2_after')
from emu import save_state; save_state(e, S + '/savanna.state'); e.stop()
