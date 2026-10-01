"""물건 시험 (savanna.state 다음): 가방 넘김, 검은 톱니 → 레이디데블몬, 고기 → 유대, 능력 보기 하트, 센터 정화 → 가트몬"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
W = json.load(open(os.path.join(S, 'web.json'))); SPN = list(W['species'].keys())
sys.path.insert(0, os.path.join(S, '..')); import story
IT = [i[0] for i in story.ITEMS]
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
G = SYM['_G']; m = e.pb.memory; P0 = G + 15; BAG = G + 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20
load_state(e, S + '/savanna.state'); e.tick(5)
m[P0] = SPN.index('gatomon'); m[P0 + 1] = 25; m[P0 + 3] = 45
for i, n in enumerate([3, 1, 1, 2, 1, 5, 1, 1]): m[BAG + i] = n
def p(b, n=1, after=12):
    for _ in range(n): e.press(b, 4, after)
def open_bag():
    p('start', 1, 20); e.shot('it_menu'); p('down', 2); p('a', 1, 30)
open_bag(); e.shot('it_bag0')
p('down', 6, 45); e.shot('it_bag_scroll')
p('a', 1, 30); e.shot('it_pick'); p('a', 1, 30)              # 검은 톱니 → 첫째
for i in range(60):
    if m[SYM['_cur_song']] == 6: break
    p('a', 1, 10)
e.tick(120); e.shot('it_gear_evo')
for i in range(40): p('a', 1, 10)
log('검은 톱니 →', SPN[m[P0]], '남은 톱니', m[BAG + IT.index('검은 톱니')])
# 고기
p('up', 1, 45); e.shot('it_bag_meat'); p('a', 1, 30); p('a', 1, 30); e.tick(30); e.shot('it_meat'); p('a', 3, 20)
log('고기 → 유대', m[P0 + 3], '남은 고기', m[BAG + IT.index('고기')])
p('b', 1, 30); p('b', 1, 30); settle(e)
# 능력 보기
p('start', 1, 20); p('up', 1); p('a', 1, 30); p('a', 1, 30); p('a', 1, 40); e.shot('it_status')
p('b', 1, 30); p('b', 1, 30); p('b', 1, 30); settle(e); log('field', gstate(e))
# 센터 정화
walk(e, 'down', 4); settle(e); log('out', gstate(e))
walk(e, 'down', 3); walk(e, 'left', 1); walk(e, 'down', 5); walk(e, 'left', 3); walk(e, 'up', 1); settle(e); log('center?', gstate(e))
walk(e, 'up', 5); p('a', 1, 20)
for i in range(80):
    if m[SYM['_field_idle']] and not m[SYM['_tb_shown']]: break
    p('a', 1, 14)
    if i == 25: e.shot('it_purify')
log('정화 →', SPN[m[P0]], gstate(e)); e.shot('it_after'); e.stop()
