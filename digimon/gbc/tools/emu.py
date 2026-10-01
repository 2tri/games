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
    """한 칸씩 정확히: 자리가 바뀌는 순간 손을 뗌"""
    for _ in range(steps):
        g0 = gstate(e); e.pb.button_press(d)
        for i in range(40):
            e.tick(1)
            g = gstate(e)
            if (g['x'], g['y'], g['map']) != (g0['x'], g0['y'], g0['map']): break
        e.pb.button_release(d); e.tick(3)
def save_state(e, path):
    with open(path, 'wb') as f: e.pb.save_state(f)
def load_state(e, path):
    with open(path, 'rb') as f: e.pb.load_state(f)

def tb(e): return e.pb.memory[SYM['_tb_shown']]
def settle(e, maxn=400, fight_move=0):
    """글상자·장면이 끝나 필드에서 자유롭게 움직일 수 있을 때까지 A (싸움이면 fight_move 기술)"""
    idle = 0
    for i in range(maxn):
        if e.pb.memory[SYM['_field_idle']] and not tb(e):
            idle += 1
            if idle > 4: return True
            e.tick(1); continue
        idle = 0
        e.press('a', 3, 8)
    return False
def oam(e, i): return e.pb.memory[0xFE00 + i * 4], e.pb.memory[0xFE00 + i * 4 + 1]
