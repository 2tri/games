"""진화 갈래 시험 (savanna.state 다음): 유대에 따라 본래·다른·실패 성숙기, B로 멈춤, 억지 암흑 진화, 검은 톱니, 센터 정화"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, save_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
W = json.load(open(os.path.join(S, 'web.json'))); SPN = list(W['species'].keys())
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
G = SYM['_G']; m = e.pb.memory; P0 = G + 15
GRASS = S + '/grass.state'
load_state(e, S + '/savanna.state'); e.tick(5)
walk(e, 'down', 4); settle(e); walk(e, 'down', 3); walk(e, 'right', 8); settle(e)
walk(e, 'right', 1); settle(e); walk(e, 'right', 5); walk(e, 'down', 1); log('grass', gstate(e))
save_state(e, GRASS)

def setup(sp, lv, bond, crests=None):
    load_state(e, GRASS); e.tick(2)
    m[P0] = SPN.index(sp); m[P0 + 1] = lv; m[P0 + 3] = bond; m[P0 + 4] = 0xF4; m[P0 + 5] = 1
    x = (lv + 1) ** 3 - 1; m[P0 + 6] = x & 255; m[P0 + 7] = (x >> 8) & 255; m[P0 + 8] = (x >> 16) & 255; m[P0 + 9] = 0
    for i in range(4): m[P0 + 14 + i] = 30
    if crests is not None: m[G + 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 16 + 32] = crests

def fight(cancel=False, shot=None):
    for i in range(80):
        walk(e, 'down' if i % 2 else 'up', 1)
        if scene(e) != 1: break
    foe = SPN[m[SYM['_foe']]]
    e.tick(30); m[SYM['_foe'] + 4] = 1; m[SYM['_foe'] + 5] = 0          # 시험: 한 방에 끝나게
    for k in range(400):
        if scene(e) == 1 and m[SYM['_field_idle']]: break
        if m[SYM['_cur_song']] == 6:            # 진화 곡
            if shot: e.tick(60); e.shot(shot); shot = None
            if cancel: e.press('b', 3, 10); continue
        e.press('a', 3, 10)
    settle(e)
    return foe

def case(name, sp, lv, bond, want, crests=None, cancel=False):
    setup(sp, lv, bond, crests)
    foe = fight(cancel, 'br_' + name)
    got = SPN[m[P0]]
    log('%-8s %s Lv%d 유대%3d → %-14s (기대 %s) %s  [상대 %s, 유대 %d]' % (name, sp, lv, bond, got, want, 'OK' if got == want else 'FAIL', foe, m[P0 + 3]))

case('main', 'agumon', 13, 80, 'greymon')
case('alt', 'agumon', 13, 40, 'tyranomon')
case('fail', 'agumon', 13, 5, 'numemon')
case('cancel', 'agumon', 13, 80, 'agumon', cancel=True)
case('gabu', 'gabumon', 13, 30, 'ogremon')
case('force', 'greymon', 29, 5, 'skullgreymon', crests=0b10)
case('crest', 'garurumon', 29, 5, 'weregarurumon', crests=0b10)
case('alt30', 'tyranomon', 29, 50, 'mamemon', crests=0b10)
case('nocrest', 'tyranomon', 29, 50, 'tyranomon', crests=0)
e.stop()
