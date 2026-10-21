#!/usr/bin/env python3
"""python inject_evo_moves.py <입력 롬> <출력 롬> — 「기술을 알면 레벨업 진화」 4줄에 필요한 기술을 배우는 길 만들기 (2026-10-21)
왜:   진화표(a/0/3/4) 방법 20 = 그 기술을 아는 채로 레벨업. 니드몬→릴리몬(파동탄) · 버드라몬→가루다몬 · 가트몬→엔젤우몬 · 원뿔몬→쥬드몬 이 필요한 기술이
      배우기 표(a/0/3/3)에 없어서(10/16 「겹친 기술」 정리 때 빠진 것으로 보임) 진화가 불가능했음 — 공략서 작성 중 롬에서 발견.
무엇을: 진화표에서 방법 20 인 줄을 전부 찾아 그 기술을 아래 레벨에 배우기 표에 더함(이미 있으면 그대로). 같은 레벨에 다른 기술이 있으면 가장 가까운 빈 레벨로.
레벨:  설계표(NDS_진화.tsv) 값 — 니드몬 35 · 버드라몬 36 · 가트몬 40 · 원뿔몬 35 (이미 차 있으면 빈 레벨 중 가까운 쪽)"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1
from hg1 import NDS, NARC
WANT = {'니드몬': 35, '버드라몬': 36, '가트몬': 40, '원뿔몬': 35}
src, dst = sys.argv[1], sys.argv[2]
slot = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hg2_out', '칸표.tsv'), encoding='utf-8').read().split('\n')[1:]:
    r = l.split('\t')
    if len(r) >= 2 and r[1].isdigit(): slot[r[0]] = int(r[1])
rom = NDS(open(src, 'rb').read()); ev = NARC(rom.get('a/0/3/4')).files; ln = NARC(rom.get('a/0/3/3')); lf = list(ln.files)
n = 0; out = []
for name, want in WANT.items():
    s = slot[name]
    mv = [p for m, p, t in hg1.evos(ev[s]) if m == 20]
    assert mv, '%s 에 방법 20 진화가 없음' % name
    ls = hg1.learnset(lf[s])
    for p in mv:
        if any(m == p for _, m in ls): out.append('%s 이미 배움' % name); continue
        used = {l for l, _ in ls}; lv = want
        for d in range(0, 20):
            for c in (want - d, want + d):
                if c not in used and 2 <= c <= 100: lv = c; break
            else: continue
            break
        assert lv not in used
        ls = sorted(ls + [(lv, p)], key=lambda x: x[0])
        raw = lf[s]; k = 0
        while struct.unpack_from('<H', raw, k)[0] != 0xFFFF: k += 2
        lf[s] = b''.join(struct.pack('<H', (l << 9) | m) for l, m in ls) + raw[k:]      # 끝 표시(FFFF)와 그 뒤 덧붙임은 원래대로
        n += 1; out.append('%s Lv%d 기술 %d 추가' % (name, lv, p))
ln.files = lf; rom.put('a/0/3/3', ln.build()); open(dst, 'wb').write(bytes(rom.d)); print('ok', '; '.join(out))
