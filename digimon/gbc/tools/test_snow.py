"""얼음 설원 (test_route3 다음): 장난감 마을 → 3번 길 북쪽 → 설원 → 프리지몬 도전자 → 얼음 속 검은 톱니"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
ID = json.load(open(os.path.join(S, 'ids.json'))); MP = ID['maps']
sys.path.insert(0, os.path.join(S, '..')); import story
IT = [i[0] for i in story.ITEMS]
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
G = SYM['_G']; m = e.pb.memory; BAG = G + 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20
load_state(e, S + '/toytown.state'); e.tick(5)
m[G + 16] = 25; m[G + 19] = 0xF4; m[G + 20] = 1
for i in range(4): m[G + 29 + i] = 30
def go(d, n):
    for i in range(n): walk(e, d, 1); settle(e, 900, 'sig')
go('down', 7); go('down', 3); go('left', 8); log('route3?', gstate(e), MP['route3'])
go('left', 9); go('up', 6); go('up', 1); log('snow?', gstate(e), MP['snow']); e.shot('snow_in')
gear0 = m[BAG + IT.index('검은 톱니')]
go('up', 7); log('after frigimon?', gstate(e))
go('right', 3); go('up', 1); e.press('a', 4, 20); settle(e)
log('gear', gear0, '→', m[BAG + IT.index('검은 톱니')], gstate(e)); e.shot('snow_end'); e.stop()
