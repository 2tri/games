#!/usr/bin/env python3
"""python inject_evo_fix.py <입력 롬> <출력 롬> — 진화 레벨 손보기(2026-10-20 사용자 결정): 토코몬 → 파닥몬 Lv20 → Lv10
이유: 알이 토코몬 Lv1 로 나오면 성장기 파닥몬까지 Lv20 이 너무 멀고, 파닥몬이 Lv20 에 되자마자 다음 레벨에 엔젤몬(Lv20)이 되어 성장기 구간이 사라짐 → 토코몬 Lv10, 파닥몬 → 엔젤몬 Lv20(아구몬·케라몬 Lv18 과 맞춤) 그대로.
진화표(a/0/3/4) 칸 = 6바이트(방법, 값, 대상): 방법 4 = 레벨."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
FIX = [(275, 277, 20, 10)]       # (출발 칸 토코몬, 도착 칸 파닥몬, 옛 레벨, 새 레벨)
src, dst = sys.argv[1], sys.argv[2]
rom = NDS(open(src, 'rb').read()); nar = NARC(rom.get('a/0/3/4')); files = list(nar.files)
for sp, tg, old, new in FIX:
    d = bytearray(files[sp]); done = False
    for k in range(0, len(d) - 5, 6):
        m, prm, t = struct.unpack_from('<HHH', d, k)
        if m == 4 and t == tg:
            assert prm in (old, new), '진화표 값이 다름 %d' % prm
            struct.pack_into('<H', d, k + 2, new); done = True
    assert done, '진화 줄을 못 찾음 %d→%d' % (sp, tg)
    files[sp] = bytes(d)
nar.files = files; rom.put('a/0/3/4', nar.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok 토코몬→파닥몬 Lv10')
