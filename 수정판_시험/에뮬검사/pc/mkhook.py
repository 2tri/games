"""python mkhook.py <롬> <출력> <파일> <진입점번호(1부터)> "<명령들>" — 그 진입점을 파일 끝에 붙인 시험 명령으로 돌림(mktest 와 같은 명령)."""
import sys, struct
sys.path.insert(0, r'C:\Users\skagn\OneDrive\Desktop\claude')
from hg1 import NDS, NARC
src, out, fi, en, cmds = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
code = b''
for c in cmds.split():
    k, _, a = c.partition(':'); a = a.split(',') if a else []
    if k == 'mon': code += struct.pack('<7H', 137, int(a[0]), int(a[1]), 0, 0, 0, 0x800C)
    elif k == 'item': code += struct.pack('<4H', 125, int(a[0]), int(a[1]), 0x800C)
    elif k == 'var': code += struct.pack('<3H', 41, int(a[0], 16), int(a[1]))
    elif k == 'flag': code += struct.pack('<2H', 30, int(a[0], 16))
    elif k == 'heal': code += struct.pack('<H', 282)
    elif k == 'warp': code += struct.pack('<6H', 176, int(a[0]), 0, int(a[1]), int(a[2]), int(a[3]))
    elif k == 'raw': code += bytes.fromhex(a[0])
code += struct.pack('<H', 2)
rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/1/2')); f = bytearray(nar.files[fi])
while len(f) % 4: f += b'\0'
at = len(f); f += code
struct.pack_into('<I', f, 4 * (en - 1), at - (4 * (en - 1) + 4))
nar.files[fi] = bytes(f); rom.put('a/0/1/2', nar.build()); open(out, 'wb').write(bytes(rom.d)); print('ok', fi, en, hex(at))
