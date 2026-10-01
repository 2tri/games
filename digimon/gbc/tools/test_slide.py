"""전투 시작 연출 확인 (grass.state 다음): 상대가 왼쪽에서 미끄러져 들어오는 장면을 6프레임마다 찍음"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, walk, load_state, scene, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
m = e.pb.memory
load_state(e, S + '/grass.state'); e.tick(2)
started = False
for i in range(120):                     # 걸음마다 한 프레임씩 보며 전투가 시작되는 순간을 잡음
    d = 'down' if i % 2 else 'up'
    e.pb.button_press(d)
    for f in range(24):
        e.tick(1)
        if scene(e) != 1: started = True; break
    e.pb.button_release(d)
    if started: break
    e.tick(6)
    if scene(e) != 1: break
xs = []
for k in range(14):
    e.tick(6); e.shot('slide%02d' % k); xs.append(m[0xFF43])
print('SCX', xs); e.stop()
