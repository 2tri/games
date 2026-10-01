"""처음부터 해변 쉘몬까지 자동 진행 (단계마다 화면·상태 기록)"""
import sys, os, faulthandler; faulthandler.dump_traceback_later(280, exit=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, save_state, scene, settle, tb, oam
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
e.tick(90); e.shot('00_title'); e.press('start', 4, 30)
for i in range(60):                      # 아이 고르기 화면이 뜰 때까지
    if oam(e, 0) == (56, 136): break
    e.press('a', 3, 10)
e.shot('01_kidpick'); e.press('a', 4, 30); e.shot('02_confirm'); e.press('a', 4, 30)
settle(e); log('camp', gstate(e)); e.shot('03_camp')
walk(e, 'up', 6); settle(e); log('forest', gstate(e)); e.shot('04_forest')
walk(e, 'up', 7); settle(e); log('after kuwaga', gstate(e)); e.shot('05_after_kuwaga')
walk(e, 'up', 4); settle(e); log('route1', gstate(e)); e.shot('06_route1')
save_state(e, S + '/r1.state')
# 1번 길: 길(x=5)로 위로 — 풀숲은 피함
walk(e, 'up', 1)
for i in range(18):
    walk(e, 'up', 1); settle(e)
    g = gstate(e)
    if g['map'] == 3: break
log('village', gstate(e)); e.shot('07_village')
walk(e, 'up', 7); e.press('a', 4, 20); settle(e); log('elecmon', gstate(e)); e.shot('08_after_elecmon')
save_state(e, S + '/vil.state')
walk(e, 'right', 6); settle(e); log('beach', gstate(e)); e.shot('09_beach')
walk(e, 'right', 7)
for i in range(8):                       # 쉘몬 앞(위쪽 1줄)까지
    if gstate(e)['y'] <= 1 or tb(e): break
    walk(e, 'up', 1)
log('before shell', gstate(e))
for i in range(12): e.press('a', 3, 10)
e.shot('10_shell_pic')
settle(e, 600); log('after shell', gstate(e)); e.shot('11_after_shell')
e.stop()
