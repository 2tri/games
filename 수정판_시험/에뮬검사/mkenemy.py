# python mkenemy.py <롬> <출력> <종 번호> <레벨> <기술번호> — 소라(트레이너 20) 파티 전부를 그 종·레벨·기술 하나로 + 연구소 진입점 → 강제 전투
import sys, struct
sys.path.insert(0, '/home/user/games')
import hg1
from hg1 import NDS, NARC
src, out, sp, lv, mv = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
tid = 20
rom = NDS(open(src, 'rb').read())
trd = NARC(rom.get(hg1.NARC_PATHS['trdata'])).files; tp = NARC(rom.get(hg1.NARC_PATHS['trpoke']))
t = hg1.trdata(trd[tid]); pk, size = hg1.trpoke(tp.files[tid], t['flags'], t['n']); assert t['flags'] & 1
b = bytearray(tp.files[tid])
ONE = len(sys.argv) > 6 and sys.argv[6] == 'one'
if ONE:
    td = bytearray(trd[tid]); td[3] = 1; trd[tid] = bytes(td)
    nt = NARC(rom.get(hg1.NARC_PATHS['trdata'])); nt.files = trd; rom.put(hg1.NARC_PATHS['trdata'], nt.build())
    b = bytearray(bytes(b[:size]))
for k in range(1 if ONE else t['n']):
    o = k * size; struct.pack_into('<HH', b, o + 2, lv, sp)
    p = o + 6 + (2 if t['flags'] & 2 else 0); struct.pack_into('<4H', b, p, mv, 0, 0, 0)
tp.files[tid] = bytes(b); rom.put(hg1.NARC_PATHS['trpoke'], tp.build())
nar = NARC(rom.get('a/0/1/2')); f = bytearray(nar.files[843]); code = struct.pack('<HHHBBH', 213, tid, 0, 0, 0, 2); p = 0
while p + 4 <= len(f):
    v = struct.unpack_from('<I', f, p)[0]
    if (v & 0xFFFF) == 0xFD13: break
    tg = p + 4 + v
    if 0 < tg < len(f) - len(code): f[tg:tg + len(code)] = code
    p += 4
nar.files[843] = bytes(f); rom.put('a/0/1/2', nar.build()); open(out, 'wb').write(bytes(rom.d)); print('ok', sp, lv, mv)
