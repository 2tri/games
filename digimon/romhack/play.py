"""디지몬스터 롬을 PyBoy로 띄워 화면 찍기 (조사·시험용)"""
import sys, os
from pyboy import PyBoy
class Play:
    def __init__(self, rom, out):
        self.pb = PyBoy(rom, window='null', sound_emulated=False); self.out = out; os.makedirs(out, exist_ok=True); self.pb.set_emulation_speed(0)
    def tick(self, n=1):
        for _ in range(n): self.pb.tick()
    def press(self, b, hold=6, after=20):
        self.pb.button_press(b); self.tick(hold); self.pb.button_release(b); self.tick(after)
    def shot(self, name): self.pb.screen.image.save(os.path.join(self.out, name + '.png'))
    def stop(self): self.pb.stop(save=False)
if __name__ == '__main__':
    import dmrom
    p = Play(sys.argv[1] if len(sys.argv) > 1 else dmrom.default_rom(), os.path.join(dmrom.WORK, 'shots'))
    p.tick(400); p.shot('t0')
    for i in range(1, 30):
        p.press('a' if i % 3 else 'start', 6, 60); p.shot('t%d' % i)
    p.stop()
