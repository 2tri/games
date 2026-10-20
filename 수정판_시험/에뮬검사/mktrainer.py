# python mktrainer.py <롬> <출력> <트레이너 번호> — 연구소 진입점을 「그 트레이너와 전투」로 바꾼 시험용 롬 사본
import sys, struct
sys.path.insert(0, '/home/user/games')
import hg1
from hg1 import NDS, NARC
src, out, tid = sys.argv[1], sys.argv[2], int(sys.argv[3])
rom = NDS(open(src, 'rb').read())
nar = NARC(rom.get('a/0/1/2')); f = bytearray(nar.files[843]); code = struct.pack('<HHHBBH', 213, tid, 0, 0, 0, 2); p = 0
while p + 4 <= len(f):
    v = struct.unpack_from('<I', f, p)[0]
    if (v & 0xFFFF) == 0xFD13: break
    tg = p + 4 + v
    if 0 < tg < len(f) - len(code): f[tg:tg + len(code)] = code
    p += 4
nar.files[843] = bytes(f); rom.put('a/0/1/2', nar.build()); open(out, 'wb').write(bytes(rom.d))
