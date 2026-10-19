#!/usr/bin/env python3
"""포켓몬 흔적 전수 조사 (롬은 읽기만) — 야생·트레이너 말고 다른 표에 남은 포켓몬 찾기 (2026-10-14)
사용:   python hg_trace.py "<최종 롬.nds>"     → 흔적_조사.txt
하는 일:
 - 롬의 종 이름표로 칸마다 「디지몬 / 포켓몬」을 가른다(이름이 「몬」으로 끝나거나 디지문자면 디지몬).
 - 롬 안 모든 파일(NARC 는 멤버마다)에서 2·4·6·8바이트 간격으로 「종 번호처럼 보이는 값」이 6개 넘게 이어진 곳을 찾고,
   그 안에 포켓몬 칸 번호가 섞인 곳을 점수 순으로 적는다(박치기 나무·사파리존·벌레잡기 대회·배틀 프런티어·게임 속 교환 등 후보).
 - 이미 HG3 가 바꾸는 야생(a/0/3/7)·트레이너(a/0/5/5, a/0/5/6)·글(a/0/2/7) 은 뺀다.
 - 후보마다 앞뒤 바이트와 들어 있는 종 이름을 적어 설계자가 표 모양을 알아보게 한다."""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC

SKIP = {'a/0/3/7', 'a/0/5/5', 'a/0/5/6', 'a/0/2/7', 'a/0/0/4', 'a/0/0/5', 'a/0/0/2', 'a/0/3/3', 'a/0/3/4', 'a/0/2/0', 'a/0/8/1'}

def main():
    raw = open(sys.argv[1], 'rb').read(); rom = NDS(raw)
    MSG = []
    for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
        try: MSG.append(hg1.msg_decode(f))
        except Exception: MSG.append((0, []))
    CM, NAMEF, _ = hg1.infer_charmap(MSG, set())
    names = [CM.dec(e) for e in MSG[NAMEF][1]]
    def skel(n): return ''.join(ch for ch in n if '가' <= ch <= '힣')
    nsp = min(494, len(names))
    poke = {i for i in range(1, nsp) if not (skel(names[i]).endswith('몬') or skel(names[i]) in ('디지문자', '디지타마'))}
    L = ['== 포켓몬 흔적 전수 조사 — 롬 %s' % rom.code, '종 이름표 msg %d, 칸 %d 중 포켓몬 이름인 칸 %d' % (NAMEF, nsp - 1, len(poke)),
         '포켓몬 칸 앞 40: %s' % ', '.join('%d %s' % (i, skel(names[i])) for i in sorted(poke)[:40])]
    hits = []
    for path in sorted(rom.paths):
        if path in SKIP: continue
        try: data = rom.get(path)
        except Exception: continue
        members = []
        if data[:4] == b'NARC':
            try: members = list(enumerate(NARC(data).files))
            except Exception: members = [(None, data)]
        else: members = [(None, data)]
        for mi, f in members:
            n = len(f)
            if n < 12: continue
            for stride in (2, 4, 6, 8):
                for start in range(0, min(stride, 8), 2):
                    run = []; k = start
                    def flush():
                        if len(run) >= 6:
                            vals = [v for _, v in run]
                            pk = [v for v in vals if v in poke]
                            if len(pk) >= 2 and len(set(vals)) >= 3:
                                hits.append((len(pk), len(run), path, mi, stride, run[0][0], vals))
                    while k + 2 <= n:
                        v = f[k] | (f[k + 1] << 8)
                        if 1 <= v < nsp: run.append((k, v))
                        else:
                            flush(); run = []
                        k += stride
                    flush()
    # 같은 자리 중복(간격만 다른 것) 줄이기: (경로, 멤버, 시작) 하나에 가장 점수 높은 것만
    best = {}
    for h in hits:
        key = (h[2], h[3], h[5] // 16)
        if key not in best or (h[0], h[1]) > (best[key][0], best[key][1]): best[key] = h
    hs = sorted(best.values(), key=lambda h: (-h[0], -h[1]))
    by_path = collections.Counter(h[2] for h in hs)
    L.append('\n후보 %d곳. 묶음(경로)별 후보 수 상위: %s' % (len(hs), ', '.join('%s:%d' % kv for kv in by_path.most_common(25))))
    L.append('\n-- 점수 순 상위 120 (포켓몬 칸 수 / 이어진 값 수 / 경로 / 멤버 / 간격 / 시작 오프셋 / 앞 24 값과 이름)')
    for pk, ln, path, mi, stride, off, vals in hs[:120]:
        nm = ' '.join('%d%s' % (v, ('*' + skel(names[v])) if v in poke else '') for v in vals[:24])
        L.append('%3d %3d  %s 멤버 %s 간격 %d @0x%X : %s' % (pk, ln, path, mi, stride, off, nm))
    L.append('\n(* = 포켓몬 이름 칸. 설계자: 표 모양을 보고 HG3 에 바꾸기를 더함)')
    open('흔적_조사.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:4])); print('→ 흔적_조사.txt 전문을 설계자에게')

if __name__ == '__main__':
    main()
