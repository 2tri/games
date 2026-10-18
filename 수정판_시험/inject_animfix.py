#!/usr/bin/env python3
"""앞모습 움직임 자료(a/1/8/0, 종마다 89바이트 × 494) 중 노란 실루엣 깜빡임을 일으키는 칸을 얌전한 칸의 움직임으로 바꾼다. (Claude 작성, 2026-10-16)
사용:   python inject_animfix.py <입력 롬> <출력 롬> [--slots 26,266,294] [--like 1] [--table hg2_out/칸표.tsv]
왜:     pret src/pokemon.c NARC_ReadPokepicAnimScript: 멤버 0 = 종 번호 × 89바이트 기록(앞 44바이트 = 앞모습: 머리 4바이트[움직임 종류 …] + 움직임 10토막×4바이트, 뒤 44바이트 = 뒷모습, 마지막 1바이트).
        칸 26(원래 Raichu)·266(Silcoon)·294(Loudred)는 앞모습 머리의 둘째 바이트가 0x13(19) → 요약 화면에 들어갈 때 노란 실루엣 효과가 1~2초 나옴(10/16 에뮬레이터 확인).
        우리 188칸 중 이 값이 0x13 인 칸은 이 셋뿐(다른 칸은 0~23 중 0x13 아님).
방법:   그 칸의 앞모습 44바이트만 --like 칸의 앞모습 44바이트로 덮음(뒷모습·끝 바이트는 그대로). 크기·개수 안 바뀜."""
import sys, os, argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
from hg1 import NDS, NARC
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--slots', default='26,266,294'); ap.add_argument('--like', type=int, default=1)
A = ap.parse_args()
raw = open(A.rom, 'rb').read(); rom = NDS(raw); nar = NARC(rom.get('a/1/8/0')); f = list(nar.files); R = 89
assert len(f[0]) == R * 494, '기록 크기가 89 × 494 가 아님'
m = bytearray(f[0]); like = bytes(m[A.like * R:A.like * R + 44]); done = []
for s in [int(x) for x in A.slots.split(',')]:
    if m[s * R + 1] != 0x13: print('칸 %d: 머리 둘째 바이트 0x%02X — 0x13 이 아니라 건드리지 않음' % (s, m[s * R + 1])); continue
    m[s * R:s * R + 44] = like; done.append(s)
f[0] = bytes(m); nar.files = f; rom.put('a/1/8/0', nar.build())
open(A.out, 'wb').write(bytes(rom.d)); print('저장: %s (앞모습 움직임 바꾼 칸 %s ← 칸 %d)' % (A.out, done, A.like))
