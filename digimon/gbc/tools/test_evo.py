"""암흑 진화 시험: 그레이몬 Lv29 (용기 문장 없음, 우정만 있음) → 야생 전투 승리 → Lv30 → '그래도 진화시킬까?' 예 → 스컬그레이몬"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
W = json.load(open(os.path.join(S, 'web.json'))); SPN = list(W['species'].keys())
ID = json.load(open(os.path.join(S, 'ids.json'))); MP = ID['maps']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/savanna.state'); e.tick(5)
G = SYM['_G']; m = e.pb.memory
P0 = G + 15
m[P0] = SPN.index('greymon'); m[P0 + 1] = 29; m[P0 + 4] = 120; m[P0 + 5] = 0
x = 26999; m[P0 + 6] = x & 255; m[P0 + 7] = (x >> 8) & 255; m[P0 + 8] = (x >> 16) & 255; m[P0 + 9] = 0
walk(e, 'down', 4); settle(e); walk(e, 'down', 3); walk(e, 'right', 8); settle(e)
walk(e, 'right', 1); settle(e); walk(e, 'right', 5); walk(e, 'down', 1); log('grass', gstate(e))
for i in range(80):
    walk(e, 'down' if i % 2 else 'up', 1)
    if scene(e) != 1: break
log('battle', SPN[m[SYM['_foe']]])
for k in range(200):
    if scene(e) == 1 and m[SYM['_field_idle']]: break
    e.press('a', 3, 10)
    if k == 60: e.shot('evo_mid')
settle(e)
log('after', gstate(e), 'party0', SPN[m[P0]], 'lv', m[P0 + 1]); e.shot('evo_end'); e.stop()
