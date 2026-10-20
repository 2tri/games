#!/usr/bin/env python3
"""python inject_gatomon_wild.py <입력 롬> <출력 롬> — 가트몬(성숙기)을 2부 시작 쪽 야생(관동 1·2·3번도로, 야생 파일 111·112·113)에 10% 칸(칸 번호 3, 아침·낮·밤 모두)으로 넣음.
이유(2026-10-20 사용자 결정): 플롯트몬 줄은 만화에서도 후반에 나오니 후반 야생에 나오게 해서 키울 수 있게. 성장기 야생은 Lv24 상한(진화 전 성숙기 정리 규칙)이라 성숙기인 가트몬으로. 칸 3 은 세 표 모두에서 다른 칸과 같은 종(퍼펫몬·아트라캅테몬)이 겹치는 자리라 사라지는 종 없음. 야생_검토.py 의 「[낮은단계] 레벨에 비해 진화 전」 경고 9건은 사용자가 정한 예외(후반에 가트몬을 직접 키우게)."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
GATOMON = 285
src, dst = sys.argv[1], sys.argv[2]
rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/3/7')); files = list(nar.files)
for z in (111, 112, 113):
    b = bytearray(files[z])
    for off in (0x14, 0x2C, 0x44):
        old = struct.unpack_from('<H', b, off + 6)[0]
        struct.pack_into('<H', b, off + 6, GATOMON)
        dup = [struct.unpack_from('<H', b, off + 2 * k)[0] for k in range(12)].count(old)
        assert dup >= 1 and old != GATOMON, (z, off, old, dup)
    b[8 + 3] = 45                                      # 칸 3 레벨 → 45(2부 시작 파티 Lv45 에 맞춤)
    files[z] = bytes(b)
nar.files = files; rom.put('a/0/3/7', nar.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok 가트몬 야생 3곳')
