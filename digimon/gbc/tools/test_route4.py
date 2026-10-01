"""순수의 신전 → 장난감 마을 동쪽 → 4번 길 → 무한산 동굴(미로·사다리) → 꼭대기 → 데블몬의 성"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
ID = json.load(open(os.path.join(S, 'ids.json'))); MP = ID['maps']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/toytown.state'); e.tick(5)
G = SYM['_G']; m = e.pb.memory; FLAGS_OFF = 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 16
m[G + 16] = 40; m[G + 19] = 0xF4; m[G + 20] = 1                      # 시험용 Lv40 HP500
for i in range(4): m[G + 29 + i] = 30                                  # PP 채움
def go(d, n, big=900):
    for i in range(n): walk(e, d, 1); settle(e, big, 'sig')
go('down', 7); go('down', 3); go('right', 9); log('route4?', gstate(e), MP['route4'])
go('right', 10); go('up', 5); go('left', 1); log('cave?', gstate(e), MP['cave1']); e.shot('r4_cave')
go('up', 1); go('up', 4); go('right', 4); go('up', 7); go('left', 2); go('down', 4); go('left', 8); go('up', 4)
log('summit?', gstate(e), MP['summit']); e.shot('r4_summit')
go('up', 9); log('castle?', gstate(e), MP['temple3'])
for i in range(4): m[G + 29 + i] = 30                                  # 성 앞에서 PP 다시 채움
go('up', 6); e.press('a', 4, 30); settle(e, 8000, 'sig')
log('after devimon', gstate(e), 'crests', bin(m[G + FLAGS_OFF + 32])); e.shot('r4_after'); e.stop()
