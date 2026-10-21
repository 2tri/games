#!/usr/bin/env python3
"""python inject_egg_species.py <입력 롬> <출력 롬> [종 번호=275] — 조수에게 받는 알(원래 토게피, 슬롯 175 = 포요몬)이 토코몬(슬롯 275)으로 부화하게 함.
이유(2026-10-20): 설계는 「포요몬(유아기)을 게임에서 뺌, 알은 토코몬」(hg3.py dropped_dg {175:'토코몬'}). 그런데 알 종은 스크립트가 아니라 오버레이 1 의 「토게피 알 주기」 코드(0x02202ACC~)에 박혀 있어
      (0x02202B0E `movs r1,#0xAF`) 종 바꾸기 표가 못 건드려 포요몬이 나왔음(에뮬 확인).
어려움: 토코몬 슬롯 275 는 255 를 넘어 `movs r1,#imm8` 한 줄로 못 넣고, 오버레이에 안전한 빈 자리가 없음.
방법:  종 = 3 + 255 + (SP-258) — r1 은 바로 앞에서 3 이라 `adds r1,#0xFF; adds r1,#SP-258` 두 줄이면 됨(SP 는 258~513). 한 줄이 모자라서 아래처럼 한 칸 밀음:
        0x02202B0E~0x02202B97 구간을 2바이트 뒤로 밀고(안의 BL 은 목적지 그대로 다시 계산), 맨 끝의 `adds r2,r0,#0; lsls r2,r2,#0x18`(바이트 자르기) 두 줄을 `lsls r2,r0,#0x18` 한 줄로 줄여 자리 확보.
        오버레이 1 은 압축 풀어 넣으면 필드가 검게 멈춰서(에뮬 확인) 고친 뒤 다시 압축해 넣음(blz_compress.py, 풀어서 같은지 검산)."""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import hg1, hg_attr, hg_scan
from blz_compress import blz_compress
from hg1 import NDS
OVR = 0x021E6300; hg_attr.OV_ID = 1; hg_attr.OV_RAM = OVR
src, dst = sys.argv[1], sys.argv[2]; SP = int(sys.argv[3]) if len(sys.argv) > 3 else 275
assert 258 <= SP <= 513
nds = NDS(open(src, 'rb').read())
pos, e, ov, comp = hg_attr.ov_read(nds)
assert e[1] == OVR and len(ov) == 0x24260, '오버레이 1 모양이 다름 %X %X' % (e[1], len(ov))
A, B, C = 0x02202B0E, 0x02202B14, 0x02202B94      # 구간 시작 · 옛 BL(CreateMon) 시작 · `adds r2,r0,#0` 자리
o = lambda a: a - OVR
old = bytes(ov[o(A):o(C) + 4])
if old[:4] != bytes([0xAF, 0x21, 0x01, 0x22]) or old[-4:] != bytes([0x02, 0x1C, 0x12, 0x06]):
    print('이미 바꿨거나 모양이 다름:', old[:4].hex(), old[-4:].hex()); sys.exit(0)
new = bytearray()
new += struct.pack('<HHHH', 0x31FF, 0x3100 | (SP - 258), 0x2201, 0x1C23)        # adds r1,#0xff; adds r1,#SP-258; movs r2,#1; adds r3,r4,#0
src_a = B
while src_a < C:                                                                   # 옛 B..C 를 2바이트 뒤로(BL 은 목적지 유지)
    h1 = struct.unpack_from('<H', ov, o(src_a))[0]
    if (h1 & 0xF800) == 0xF000:
        tgt = hg_attr.bl_target(src_a, bytes(ov[o(src_a):o(src_a) + 4])); assert tgt
        new += hg_attr.thumb_bl(A + len(new), tgt); src_a += 4
    else:
        new += bytes(ov[o(src_a):o(src_a) + 2]); src_a += 2
new += struct.pack('<H', 0x0602)                                                   # lsls r2,r0,#0x18
assert len(new) == len(old), (len(new), len(old))
ov[o(A):o(A) + len(new)] = new
comp_bytes = blz_compress(bytes(ov)); assert hg_scan.blz_decompress(comp_bytes) == bytes(ov), '다시 압축 검산 실패'
how = hg_attr.put_fid(nds, e[6], comp_bytes); e[7] = 0x01000000 | len(comp_bytes); struct.pack_into('<8I', nds.d, pos, *e)
open(dst, 'wb').write(bytes(nds.d)); print('ok 알 종 %d, 오버레이 1 다시 압축 %d바이트(원래 %d) %s' % (SP, len(comp_bytes), (lambda a, b: b - a)(*nds.fat(e[6])) if False else len(comp_bytes), how))
