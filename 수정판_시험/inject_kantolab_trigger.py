#!/usr/bin/env python3
"""python inject_kantolab_trigger.py <입력 롬> <출력 롬> — 2부 시작 관동 연구소(맵 505, 스크립트 740, 이벤트 457): 입장하자마자 장면 006(스타팅 3개 고르기)이 문에서 시작되게 함.
이유(2026-10-20 에뮬 확인): 지금까지는 4131 을 1 로 올리는 코드가 오박사 말걸기 스크립트(번호 1) 안에만 있어서, 들어가도 아무 일 없다가 오박사에게 말을 건 뒤(그 자리 앞)에서야 장면 006 이 시작됨
  → 장면의 「위로 8칸」 걷기가 어긋나 플레이어가 맵 밖(y=-1)으로 나감. 원래(4131==1 로 들어올 때)는 문 쪽에서 시작해 (8,4) 에 멈춤.
고침 2: 스타팅 지급 명령 중 레벨 5 로 남은 것을 45 로(설계표 「관동 스타팅 Lv45」).
고침: 스크립트 740 끝에 새 토막(번호 12: SetVar 4131,1 / ClearFlag 766·767·768 / End) 추가 + 이벤트 457 에 칸 이벤트(문에서 한 칸 들어선 (8,12), 4131==0 일 때 → 번호 12).
  토막이 끝나면 엔진이 장면(레벨 스크립트: 4131==1 → 스크립트 7)을 바로 확인해 문 쪽에서 시작. 칸 이벤트 = 16바이트(스크립트, x, y, 폭, 높이, 높이값, 값, 변수 — 다른 이벤트 파일 실제 값으로 확인)."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
src, dst = sys.argv[1], sys.argv[2]
rom = NDS(open(src, 'rb').read())
sc = NARC(rom.get('a/0/1/2')); f = sc.files[740]
ents = []; p = 0
while p + 4 <= len(f):
    v = struct.unpack_from('<I', f, p)[0]
    if (v & 0xFFFF) == 0xFD13: break
    ents.append(p + 4 + v); p += 4
assert len(ents) == 11 and f[p:p + 2] == b'\x13\xfd', '스크립트 740 모양이 다름'
new = struct.pack('<HHH', 0x29, 0x4131, 1) + b''.join(struct.pack('<HH', 0x1f, fl) for fl in (0x2fe, 0x2ff, 0x300)) + struct.pack('<H', 2)
code0 = p + 2                     # 원래 명령 시작(표 끝 표식 바로 뒤)
body = f[code0:]
ents2 = [e + 4 for e in ents] + [len(f) + 4]          # 표 한 칸(4바이트) 늘어나므로 전부 +4, 새 토막은 맨 끝
out = b''.join(struct.pack('<I', e - (4 * i + 4)) for i, e in enumerate(ents2)) + f[p:code0] + body + new
out = bytearray(out); fixed = []
for k in range(len(out) - 8):                          # 스타팅 종 지급(GiveMon, 명령 137): 종 변수 8004, 레벨 5 → 45. hg_event 가 첫 번째만 고쳐서 나머지는 레벨 5 로 주고 있었음
    if out[k:k + 4] == b'\x89\x00\x04\x80' and struct.unpack_from('<H', out, k + 4)[0] == 5:
        struct.pack_into('<H', out, k + 4, 45); fixed.append(k)
print('GiveMon 레벨 5→45:', fixed)
sc.files[740] = bytes(out)
rom.put('a/0/1/2', sc.build())
ev = NARC(rom.get(hg1.NARC_PATHS['zone_event'])); g = ev.files[457]
o = 0; nb = struct.unpack_from('<I', g, o)[0]; o += 4 + 20 * nb
no = struct.unpack_from('<I', g, o)[0]; o += 4 + 32 * no
nw = struct.unpack_from('<I', g, o)[0]; o += 4 + 12 * nw
assert struct.unpack_from('<I', g, o)[0] == 0 and len(g) == o + 4, '칸 이벤트가 이미 있거나 파일 끝이 다름'
ev.files[457] = g[:o] + struct.pack('<I', 1) + struct.pack('<8H', 12, 8, 12, 1, 1, 0, 0, 0x4131)
rom.put(hg1.NARC_PATHS['zone_event'], ev.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok 관동 연구소 입장 장면 시작 고침')
