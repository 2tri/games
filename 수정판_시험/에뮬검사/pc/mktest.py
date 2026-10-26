"""python mktest.py <롬> <출력> "<명령들>" — 방(지도64, 스크립트 846)의 진입점을 시험 명령으로 덮어쓴 시험 롬.
명령: mon:종,레벨  var:번호16,값  flag:번호  heal  warp:지도,x,y,방향  raw:16진"""
import sys, struct
sys.path.insert(0, r'C:\Users\skagn\OneDrive\Desktop\claude')
import hg1
from hg1 import NDS, NARC
src, out, cmds = sys.argv[1], sys.argv[2], sys.argv[3]
code = b''
for c in cmds.split():
    k, _, a = c.partition(':'); a = a.split(',') if a else []
    if k == 'mon': code += struct.pack('<7H', 137, int(a[0]), int(a[1]), 0, 0, 0, 0x800C)
    elif k == 'var': code += struct.pack('<3H', 41, int(a[0], 16), int(a[1]))
    elif k == 'flag': code += struct.pack('<2H', 30, int(a[0], 16))
    elif k == 'item': code += struct.pack('<4H', 125, int(a[0]), int(a[1]), 0x800C)
    elif k == 'heal': code += struct.pack('<H', 282)
    elif k == 'warp': code += struct.pack('<6H', 176, int(a[0]), 0, int(a[1]), int(a[2]), int(a[3]))
    elif k == 'raw': code += bytes.fromhex(a[0])
code += struct.pack('<H', 2)
rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/1/2')); f = bytearray(nar.files[846]); p = 0; ents = []
while p + 4 <= len(f):
    v = struct.unpack_from('<I', f, p)[0]
    if (v & 0xFFFF) == 0xFD13: break
    ents.append(p + 4 + v); p += 4
body = p + 2  # 진입점 표 뒤에 새 코드를 붙이고 진입점을 모두 그쪽으로
f = f[:body] + code + f[body:]
# 앞에 끼운 만큼 기존 진입점이 밀리지만 모든 진입점을 새 코드로 돌리므로 무관
for i in range(len(ents)):
    struct.pack_into('<I', f, 4 * i, body - (4 * i + 4))
nar.files[846] = bytes(f); rom.put('a/0/1/2', nar.build()); open(out, 'wb').write(bytes(rom.d)); print('ok', len(ents), len(code))
