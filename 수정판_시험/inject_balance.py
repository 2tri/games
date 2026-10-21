#!/usr/bin/env python3
"""python inject_balance.py <입력 롬> <출력 롬> — 초반 트레이너 레벨 손보기(노말 기준, 2026-10-20 마지막 밸런스)
근거(롬에서 읽은 값): 수호자를 낮춘 뒤(초반 벽: 성숙기 −2 등) 체육관 졸개는 원래 레벨 그대로라 졸개가 수호자보다 높거나 같았음.
  1부 수호자 에이스 7·14·21·25·42 에 대해 졸개 최고 Lv 11·16·22·25·42, 그리고 연결동굴 뒤 33번도로 외길 트레이너가 Lv21(한솔 에이스 14 · 미나 21 과 같음).
고침: 졸개 최고 레벨 = 수호자 에이스 −2(소라 체육관은 −1), 파티 안 비율 유지. 33번도로 용민 Lv21 → 15.
표 = {트레이너 번호: [새 레벨…]}(트레이너 데이터 번호 = 파일 번호, trpoke 레벨은 마리당 2바이트 +2)"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
PLAN = {50: [6, 5], 29: [6, 5],                 # 소라(Lv7) 체육관 졸개 소룡·날개 (11·9 →)
        68: [12, 12], 67: [8, 9, 12], 69: [12],   # 한솔(Lv14) 체육관 졸개 기지·정남·희주 (16 →)
        22: [19], 5: [16, 16, 19], 70: [19, 19],  # 미나(Lv21) 체육관 졸개 미카·진주·채린 (21~22 →)
        493: [23],                              # 가트몬(Lv25) 체육관 졸개 매순 (25 →)
        119: [40],                              # 리키(Lv42) 체육관 졸개 지예 (42 →)
        61: [15, 11, 9]}                        # 33번도로 용민 (21·15·12 →)
src, dst = sys.argv[1], sys.argv[2]
rom = NDS(open(src, 'rb').read()); td = NARC(rom.get('a/0/5/5')); tp = NARC(rom.get('a/0/5/6')); files = list(tp.files)
for t, lvs in PLAN.items():
    d = hg1.trdata(td.files[t]); assert d and d['n'] == len(lvs), '트레이너 %d 마릿수가 다름' % t
    pk, size = hg1.trpoke(files[t], d['flags'], d['n']); assert pk
    b = bytearray(files[t])
    for k, lv in enumerate(lvs):
        assert pk[k]['lv'] >= lv, '트레이너 %d 레벨이 이미 더 낮음' % t
        struct.pack_into('<H', b, k * size + 2, lv)
    files[t] = bytes(b)
tp.files = files; rom.put('a/0/5/6', tp.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok 트레이너 %d명 레벨 손봄' % len(PLAN))
