"""처음부터 해변 쉘몬까지 자동 진행 (단계마다 화면·상태 기록)"""
import sys, os, faulthandler; faulthandler.dump_traceback_later(280, exit=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, save_state, scene, settle, tb, oam, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
e.tick(90); e.shot('00_title'); e.press('start', 4, 30)
import re as _re
T_CUR_T = int(_re.search(r'#define T_CUR_T (\d+)', open(os.path.join(S, 'gen', 'gen.h')).read()).group(1))
for i in range(60):                      # 아이 고르기 화면이 뜰 때까지 (이름 줄 (0,9) 의 커서)
    if e.pb.memory[0x9800 + 9 * 32] == T_CUR_T and scene(e) == 2: break
    e.press('a', 3, 10)
e.tick(30)
for k in range(4):                       # 4명 초상 차례로
    e.shot('01_kidpick%d' % k); e.press('right', 4, 40)
e.shot('01_kidpick'); e.press('a', 4, 30); e.shot('02_confirm'); e.press('a', 4, 30)
settle(e); log('house2f', gstate(e)); e.shot('03_room')
walk(e, 'down', 3); walk(e, 'right', 4); settle(e); log('house1f', gstate(e)); e.shot('04_1f')
walk(e, 'down', 5); walk(e, 'left', 4); walk(e, 'up', 1); e.press('a', 4, 20); e.shot('05_note'); settle(e)
walk(e, 'down', 1); settle(e); log('town', gstate(e)); e.shot('06_town')
walk(e, 'right', 4); walk(e, 'up', 7); e.shot('07_bus'); settle(e); log('camp', gstate(e)); e.shot('08_camp')
save_state(e, S + '/camp.state')
walk(e, 'up', 5); walk(e, 'right', 6); e.shot('09_camp_mid'); walk(e, 'up', 4); settle(e); log('forest', gstate(e)); e.shot('10_forest')
walk(e, 'up', 7); settle(e); log('after kuwaga', gstate(e)); e.shot('11_after_kuwaga')
walk(e, 'up', 4); settle(e); log('route1', gstate(e)); e.shot('12_route1')
save_state(e, S + '/r1.state')
# 1번 길: 길(x=5)로 위로 — 풀숲은 피함
walk(e, 'up', 1)
for i in range(18):
    walk(e, 'up', 1); settle(e)
    g = gstate(e)
    if g['map'] == 6: break
log('village', gstate(e)); e.shot('13_village')
walk(e, 'up', 5); walk(e, 'left', 1); walk(e, 'up', 2); settle(e); log('center', gstate(e)); e.shot('14_center')
walk(e, 'up', 5); e.press('a', 4, 20); settle(e); log('elecmon', gstate(e)); e.shot('14_after_elecmon')
walk(e, 'down', 6); settle(e); log('out', gstate(e))
save_state(e, S + '/vil.state')
walk(e, 'right', 9); settle(e); log('beach', gstate(e)); e.shot('15_beach')
save_state(e, S + '/beach.state')
walk(e, 'right', 7)
for i in range(8):                       # 쉘몬 앞(위쪽 1줄)까지
    if gstate(e)['y'] <= 1 or tb(e): break
    walk(e, 'up', 1)
log('before shell', gstate(e))
G_ = SYM['_G']; e.pb.memory[G_ + 16] = 12; e.pb.memory[G_ + 19] = 40; e.pb.memory[G_ + 20] = 0   # 시험용: 해변에서 Lv12까지 올린 것으로 (회복 아이템 없이)
for i in range(4): e.press('a', 3, 10)
e.shot('16_shell_pic')
settle(e, 1500, 'sig'); log('after shell', gstate(e), 'crests', bin(e.pb.memory[G_ + 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 16 + 32])); e.shot('17_after_shell')
e.stop()
