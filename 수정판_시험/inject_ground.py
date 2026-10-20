#!/usr/bin/env python3
"""전투 그림 높이(a/0/0/5, 종마다 1바이트 4개: 뒷모습 남·여, 앞모습 남·여 — 그림을 아래로 내리는 값, 단위 = 1픽셀)를 우리 그림에 맞게 다시 계산한다.
사용:   python inject_ground.py <입력 롬> <출력 롬> [--table hg2_out/칸표.tsv] [--base 수정판_시험/ground_base.json]
왜:     이 표는 원래 그 칸에 있던 포켓몬 그림에 맞춘 값이라, 디지몬 그림이 들어오면 바닥에서 떠 있거나 내려간 종이 많았다
        (10/19 사용자: 피노키몬이 공중에 떠 있음 — 188종 중 발 위치가 판 위로 25~55픽셀 뜬 종이 약 50종).
        게다가 그림 상자의 기준 위치(base)가 종마다 달라서(−19~31) 값만 보고는 못 맞춘다 → 에뮬레이터로 188종을 하나씩 전투 화면에 내놓고
        상자 위치를 재서(값 20 으로 고정, 그림의 맨 윗줄이 화면 어디에 찍히는지) ground_base.json 에 저장해 둠(칸 번호 → base).
        그림의 맨 아랫줄이 화면의 y = base + (그림 맨 아랫줄) + 값 에 찍힘. 상대 쪽 판의 그림자 중심 y ≈ 86, 내 쪽 이름판 윗선 y ≈ 93.
방법:   값 = 목표 y − base − 맨 아랫줄 (0 아래로는 못 내림). 목표 = 땅에 서는 종 89(그림자 바로 아래) · 나는 종 80(9픽셀 띄움).
        뒷모습(첫 두 값)은 이미 맨 아랫줄 + 값 = 79 인 종이 176/188 이라 건드리지 않음."""
import sys, os, csv, json, argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
import hg1, hg4
from hg1 import NDS, NARC
HOVER = {'플라이몬', '쿠가몬', '캅테리몬', '아트라캅테몬', '스팅몬', '파닥몬', '엔젤몬', '홀리엔젤몬', '엔젤우몬', '레이디데블몬', '데블몬', '피코데블몬', '팬텀몬', '고스몬',
         '페가수몬', '호우오몬', '세라피몬', '마그나드몬', '베이더몬', '스타몬', '버드라몬', '가루다몬', '호크몬', '호루스몬', '실피드몬', '피콜로몬', '데이터몬', '슈퍼스타몬', '묘티스몬'}
T_GROUND, T_HOVER = 89, 80
here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--table', default='hg2_out/칸표.tsv'); ap.add_argument('--base', default=os.path.join(here, 'ground_base.json')); A = ap.parse_args()
BASE = {int(k): v for k, v in json.load(open(A.base, encoding='utf-8')).items()}
rom = NDS(open(A.rom, 'rb').read()); F = NARC(rom.get(hg1.NARC_PATHS['pokegra'])).files; nar = NARC(rom.get('a/0/0/5')); O = list(nar.files)
assert len(O) >= 494 * 4 and all(len(x) == 1 for x in O[:494 * 4]), '높이 표 모양이 다름'
rows = [r for r in csv.reader(open(A.table, encoding='utf-8'), delimiter='\t') if len(r) >= 2 and r[1].isdigit()]
n = 0; log = []; lo = hi = 0
for name, s in ((r[0], int(r[1])) for r in rows):
    if s not in BASE: log.append('base 없음(재지 않음): %s 칸 %d' % (name, s)); continue
    fr, _ = hg1.ncgr_rows(F[s * 6 + 3]); fb = hg4.opaque_box(fr) if fr else None
    if fb is None: log.append('그림 없음: %s 칸 %d' % (name, s)); continue
    t = T_HOVER if name in HOVER else T_GROUND
    want = t - BASE[s] - fb[1]; v = max(0, min(255, want))
    if want < 0: hi += 1
    O[s * 4 + 2] = O[s * 4 + 3] = bytes([v]); n += 1
nar.files = O; rom.put('a/0/0/5', nar.build()); open(A.out, 'wb').write(bytes(rom.d))
print('저장: %s (앞모습 높이 다시 계산한 칸 %d, 0 으로도 목표보다 낮은 칸 %d)' % (A.out, n, hi)); [print(' ', x) for x in log]
