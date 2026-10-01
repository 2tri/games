"""PyBoy로 롬 실행 확인: 버튼 누르기·화면 찍기 (델타 없이 검증)"""
import sys, os
from pyboy import PyBoy

class Emu:
    def __init__(self, rom, out, sav=None):
        self.out = out; os.makedirs(out, exist_ok=True)
        kw = {}
        self.pb = PyBoy(rom, window='null', cgb=True, sound_emulated=False, **kw)
        self.pb.set_emulation_speed(0)
        self.n = 0
    def tick(self, n=1):
        for _ in range(n): self.pb.tick(1, True)
    def press(self, b, hold=6, after=10):
        self.pb.button_press(b); self.tick(hold); self.pb.button_release(b); self.tick(after)
    def shot(self, name):
        self.pb.screen.image.convert('RGB').resize((480, 432), 0).save(os.path.join(self.out, name + '.png'))
    def mash(self, n, b='a', gap=12):
        for _ in range(n): self.press(b, 4, gap)
    def mem(self, addr): return self.pb.memory[addr]
    def stop(self): self.pb.stop(save=False)

import re as _re
def _syms():
    d = {}
    try:
        for m in _re.finditer(r'DEF (_\w+) 0x([0-9A-Fa-f]+)', open(os.path.join(os.path.dirname(__file__), '..', 'digimon.noi')).read()):
            d[m.group(1)] = int(m.group(2), 16) & 0xFFFF
    except Exception as ex: print('noi', ex)
    return d
SYM = _syms()
G_ADDR = SYM.get('_G', 0xC0D0)
def scene(e): return e.pb.memory[SYM['_scene']]
def gstate(e):
    m = e.pb.memory
    return {'kid': m[G_ADDR + 4], 'map': m[G_ADDR + 5], 'x': m[G_ADDR + 6], 'y': m[G_ADDR + 7], 'dir': m[G_ADDR + 8], 'nparty': m[G_ADDR + 13]}
def walk(e, d, steps):
    """한 칸씩 정확히: 화면이 움직이기 시작하면(걸음 시작) 바로 손을 떼고, 도착할 때까지 기다림"""
    m = e.pb.memory
    for _ in range(steps):
        g0 = gstate(e); sc0 = (m[0xFF42], m[0xFF43]); e.pb.button_press(d); started = False
        for i in range(40):
            e.tick(1)
            if (m[0xFF42], m[0xFF43]) != sc0 or (gstate(e)['x'], gstate(e)['y'], gstate(e)['map']) != (g0['x'], g0['y'], g0['map']):
                started = True; break
        e.pb.button_release(d)
        if started:
            for i in range(40):
                g = gstate(e)
                if (g['x'], g['y'], g['map']) != (g0['x'], g0['y'], g0['map']): break
                e.tick(1)
        e.tick(3)
def save_state(e, path):
    with open(path, 'wb') as f: e.pb.save_state(f)
def load_state(e, path):
    with open(path, 'rb') as f: e.pb.load_state(f)

def tb(e): return e.pb.memory[SYM['_tb_shown']]
def pick_slot(e):
    """첫째 디지몬의 기술 중 PP 남은 필살기(기술 번호 6 이상) → 없으면 PP 남은 아무 기술"""
    m = e.pb.memory; P = SYM['_G'] + 15
    ok = [i for i in range(4) if m[P + 10 + i] != 0xFF and m[P + 14 + i]]
    sig = [i for i in ok if m[P + 10 + i] >= 6]
    return (sig or ok or [0])[-1] if sig else (ok or [0])[0]
def settle(e, maxn=400, fight_move=None):
    """글상자·장면이 끝나 필드에서 자유롭게 움직일 수 있을 때까지 A. fight_move='sig' 이면 기술 고를 때 필살기"""
    idle = 0
    for i in range(maxn):
        if e.pb.memory[SYM['_field_idle']] and not tb(e):
            idle += 1
            if idle > 4: return True
            e.tick(1); continue
        idle = 0
        if fight_move == 'sig' and e.pb.memory[SYM['_win_top']] == 8:      # 기술 창: 다 그려진 뒤 천천히
            e.tick(25)
            for k in range(pick_slot(e)): e.press('down', 3, 15)
            e.press('a', 3, 20)
            for w in range(120):
                if e.pb.memory[SYM['_win_top']] != 8: break
                e.tick(1)
            continue
        e.press('a', 3, 8)
    return False
def oam(e, i): return e.pb.memory[0xFE00 + i * 4], e.pb.memory[0xFE00 + i * 4 + 1]
