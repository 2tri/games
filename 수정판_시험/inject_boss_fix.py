#!/usr/bin/env python3
"""python inject_boss_fix.py <입력 롬> <출력 롬> — 설계표(NDS_이벤트표.tsv)와 다르던 심볼 보스 2곳을 표대로(2026-10-20 사용자 결정 「설계표로」)
  1) 어둠의 동굴 보스(맵 123, 스크립트 108): 워그레이몬(슬롯 257) Lv55 → 블랙워그레몬(슬롯 109) Lv50 — 울음·그림 명령(0x4C)의 종도 같이 바꿈
  2) 동성폭포 디아블로몬(맵 298, 스크립트 114): Lv60 → Lv50"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
src, dst = sys.argv[1], sys.argv[2]
rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/1/2'))
f = bytearray(nar.files[108])
a = bytes([0x4C, 0x00, 0x01, 0x01, 0x00, 0x00]); b = bytes([0x4D, 0x02, 0x01, 0x01, 0x37, 0x00])
ia, ib = bytes(f).find(a), bytes(f).find(b); assert ia >= 0 and ib >= 0 and bytes(f).count(a) == 1 and bytes(f).count(b) == 1, '스크립트 108 모양이 다름'
f[ia + 2:ia + 4] = struct.pack('<H', 109); f[ib + 2:ib + 6] = struct.pack('<HH', 109, 50)
nar.files[108] = bytes(f)
g = bytearray(nar.files[114]); c = bytes([0x4D, 0x02, 0xE8, 0x01, 0x3C, 0x00]); ic = bytes(g).find(c)
assert ic >= 0 and bytes(g).count(c) == 1, '스크립트 114 모양이 다름'
g[ic + 4:ic + 6] = struct.pack('<H', 50); nar.files[114] = bytes(g)
rom.put('a/0/1/2', nar.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok 심볼 보스 2곳(어둠의 동굴 블랙워그레몬 Lv50, 동성폭포 디아블로몬 Lv50)')
