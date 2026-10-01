"""기술 잊기 시험 (test_route2 다음): 그레이몬 Lv29 + 용기의 문장 → 메탈그레이몬, 새 필살기 3개
첫째: 잊고 익힘(1번 칸) · 둘째: 잊고 익힘(2번 칸) · 셋째: 안 익힘"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import Emu, gstate, walk, load_state, scene, settle, SYM
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build')
W = json.load(open(os.path.join(S, 'web.json'))); SPN = list(W['species'].keys())
ID = json.load(open(os.path.join(S, 'ids.json'))); MV = ID['moves']
e = Emu(os.path.join(S, '..', 'digimon.gbc'), os.path.join(S, 'shots'))
log = lambda *a: print(*a, flush=True)
G = SYM['_G']; m = e.pb.memory; P0 = G + 15
load_state(e, S + '/grass.state'); e.tick(2)
m[P0] = SPN.index('greymon'); m[P0 + 1] = 29; m[P0 + 3] = 80; m[P0 + 4] = 0xF4; m[P0 + 5] = 1
x = 30 ** 3 - 1; m[P0 + 6] = x & 255; m[P0 + 7] = (x >> 8) & 255; m[P0 + 8] = (x >> 16) & 255; m[P0 + 9] = 0
for i, n in enumerate(['할퀴기', '노려보기', '메가파이어', '물기']): m[P0 + 10 + i] = MV.index(n); m[P0 + 14 + i] = 20
m[G + 4 + 5 + 4 + 2 + 20 * 6 + 20 * 20 + 16 + 32] = 0b11          # 용기·우정
log('before', [MV[m[P0 + 10 + i]] for i in range(4)])
for i in range(80):
    walk(e, 'down' if i % 2 else 'up', 1)
    if scene(e) != 1: break
e.tick(30); m[SYM['_foe'] + 4] = 1; m[SYM['_foe'] + 5] = 0
asks = 0; picks = 0
def wait_change(v):
    for w in range(200):
        if m[SYM['_win_top']] != v: return
        e.tick(1)
for k in range(1500):
    if scene(e) == 1 and m[SYM['_field_idle']] and not m[SYM['_tb_shown']]: break
    wt = m[SYM['_win_top']]
    if wt == 1:                              # 잊을 기술 고르기 창
        e.tick(40); picks += 1; e.shot('learn_pick%d' % picks)
        if picks == 2: e.press('down', 3, 20)
        log('  고르기', picks, '→', picks - 1 if picks <= 2 else 0)
        e.press('a', 3, 20); wait_change(1); continue
    if wt == 6:                              # 예/아니오: 1·2번째 예, 3번째 아니오, 4번째(그만둘까?) 예
        e.tick(30); asks += 1; e.shot('learn_ask%d' % asks)
        no = asks == 3
        log('  질문', asks, '아니오' if no else '예')
        if no: e.press('down', 3, 20)
        e.press('a', 3, 20); wait_change(6); continue
    e.press('a', 3, 10)
settle(e)
log('after', SPN[m[P0]], [MV[m[P0 + 10 + i]] for i in range(4)], 'asks', asks, 'picks', picks); e.shot('learn_end'); e.stop()
