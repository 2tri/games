import sys, struct
from desmume.emulator import DeSmuME
import pk4
rom, st = sys.argv[1:3]
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(st)
for _ in range(10): emu.cycle(False)
ram = bytes(emu.memory.unsigned[0x02000000:0x02400000])
pat = struct.pack('<II', 6, 1)
o = 0; found = []
while True:
    o = ram.find(pat, o)
    if o < 0: break
    raw = ram[o + 8:o + 8 + 236]
    d = pk4.decode(raw)
    body = b''.join(d['blocks'][c] for c in d['order'])
    chk = sum(struct.unpack('<64H', body)) & 0xFFFF
    ok = chk == struct.unpack_from('<H', raw, 6)[0]
    sp = struct.unpack_from('<H', d['blocks']['A'], 0)[0]
    if ok and 0 < sp < 600: found.append((0x02000000 + o, sp, d['party'][4]))
    o += 4
print('파티 후보', [(hex(a), s, 'Lv%d' % l) for a, s, l in found])
