import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../수정판_시험/게임화면')
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image
import pk4
rom, st, out = sys.argv[1], sys.argv[2], sys.argv[3]
tests = [tuple(int(x) for x in t.split(',')) for t in sys.argv[4:]]  # species,pidadd
emu = DeSmuME(); emu.open(rom); emu.volume_set(0)
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=30):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y):
    emu.input.touch_set_pos(x, y); run(6); emu.input.touch_release(); run(40)
emu.savestate.load_file(st); run(10)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000]); pat = struct.pack('<II', 6, 1); o = ram.find(pat)
while o >= 0:
    d = pk4.decode(ram[o + 8:o + 244]); body = b''.join(d['blocks'][c] for c in d['order'])
    if sum(struct.unpack('<64H', body)) & 0xFFFF == struct.unpack_from('<H', ram, o + 14)[0]: break
    o = ram.find(pat, o + 4)
base = 0x02000000 + o; first = ram[o + 8:o + 244]
ims = []
for sp, padd in tests:
    emu.savestate.load_file(st); run(10)
    d = pk4.decode(pk4.with_species(first, sp)); d['pid'] = (d['pid'] + padd) & 0xFFFFFFFF
    bb = bytearray(d['blocks']['B']); print('B[0x18]', hex(bb[0x18]), 'form', bb[0x18] >> 3, 'padd', padd)
    if padd >= 1000:
        d['pid'] = (d['pid'] - padd) & 0xFFFFFFFF; bb[0x18] = (bb[0x18] & 0x07) | ((padd - 1000) << 3); d['blocks']['B'] = bytes(bb)
    raw = pk4.encode(d)
    for j, b in enumerate(raw): emu.memory.unsigned[base + 8 + j] = b
    run(5); touch(50, 76); run(60)
    press(Keys.KEY_A, 4, 50); press(Keys.KEY_A, 4, 90); run(30)
    for w in (0, 30, 60, 120, 240, 480):
        run(w if w==0 else w - prev) if False else None
    t=0
    for w in (0, 120):
        run(w - t); t = w
        ims.append(emu.screenshot().copy().crop((165, 40, 255, 140)))
W = Image.new('RGB', (90 * len(ims), 100))
for i, im in enumerate(ims): W.paste(im, (i * 90, 0))
W.save(out); print('저장', out, tests)
