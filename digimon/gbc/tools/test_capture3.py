"""유년기가 나올 때까지 싸움 → 유년기면 그물, 아니면 도망. 포획 성공 길을 확인"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
W = json.load(open(os.path.join(S, 'web.json'))); SPN = list(W['species'].keys())
noi = open(os.path.join(S, '..', 'digimon.noi')).read(); FOE = int(re.search(r'DEF _foe 0x([0-9A-Fa-f]+)', noi).group(1), 16)
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
load_state(e, S + '/vil.state'); e.tick(5)
walk(e, 'right', 1); walk(e, 'down', 7); settle(e)
walk(e, 'down', 2); walk(e, 'left', 1)
for b in range(25):
    for i in range(80):
        walk(e, 'left' if i % 2 else 'right', 1)
        if scene(e) != 1: break
    for k in range(30): e.press('b', 3, 8)
    sp = SPN[e.mem(FOE)]; tier = W['species'][sp]['tier']; log('battle', b, sp, tier)
    if tier in ('baby', 'baby2'):
        for t in range(5):
            e.press('right', 3, 10); e.press('a', 3, 60); e.press('down', 3, 45); e.press('down', 3, 45)
            e.shot('ok_bag%d' % t); e.press('a', 3, 30)
            for k in range(6): e.press('b', 3, 10)
            e.shot('ok_msg%d' % t)
            for k in range(10): e.press('b', 3, 10)
            if scene(e) == 1: break
        settle(e); log('after net', gstate(e)); e.shot('ok_end'); break
    else:
        for t in range(6):
            e.press('down', 3, 10); e.press('right', 3, 10); e.press('a', 3, 20)
            for k in range(10): e.press('b', 3, 10)
            if scene(e) == 1: break
        settle(e)
log('end', gstate(e)); e.stop()
