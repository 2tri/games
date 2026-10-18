#!/usr/bin/env python3
r"""기술 점검 (2026-10-16) — 롬에 「실제로 써진」 기술 배우기 표를 여러 기준으로 본다. 롬은 읽기만.
사용:   python 기술_점검.py <롬.nds> [--slots hg2_out/칸표.tsv]      (hg2 뒤 롬 아무거나 · 최종_오늘.nds 도 됨)
결과:   기술_점검.md — 기준마다 걸린 종 목록. 끝줄 「기술 점검: 걸린 곳 n」
기준 (10/16 사용자 「성장기 초반은 몸통박치기 같은 약한 것, Lv7~8 에 타입 공격」 + 설계 규칙)
  [초반]   성장기: Lv1~6 에 위력 45 이상 공격, Lv7~12 에 위력 65 이상 공격
  [타입]   성장기: 자기 타입 공격을 처음 배우는 Lv 가 5 미만(너무 이름)이거나 진화 전까지 없음
  [Lv1]    모든 종: 첫 레벨에 공격 기술이 없음(야생·트레이너가 공격을 못 함)
  [진화뒤] 성장기: 레벨 진화 Lv 이상에서 배우는 기술(B안: 진화 전까지만)
  [자속]   모든 종: 자기 타입 공격이 2개 미만
  [물특]   공격 능력이 높은데 특수 기술이 대부분(또는 반대) — 공·특공 차 15 이상, 반대쪽 기술이 2배 이상
  [겹침]   같은 기술 두 번 · [20칸] 21개 이상"""
import os, sys, csv, argparse, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import hg1, hg2
from hg1 import NDS, NARC, msg_decode
P = H if os.path.exists(os.path.join(H, 'NDS_종_초안.tsv')) else os.path.join(H, '..')
EARLY = [(6, 45), (12, 65)]
ROOKIE = ('성장기', '유년기', '유년기Ⅱ', '유년기Ⅰ')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--slots', default='hg2_out/칸표.tsv'); ap.add_argument('--out', default='기술_점검.md')
    A = ap.parse_args()
    rom = NDS(open(A.rom, 'rb').read())
    draft = {r['이름']: r for r in csv.DictReader((l for l in open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
    slot = {}
    for l in open(A.slots, encoding='utf-8').read().split('\n')[1:]:
        r = l.split('\t')
        if len(r) >= 2 and r[1].isdigit() and r[0] in draft: slot[r[0]] = int(r[1])
    N = NARC(rom.get(hg1.NARC_PATHS['msg'])); MSG = []
    for f in N.files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append((0, []))
    CM, _, _ = hg1.infer_charmap(MSG, set(draft))
    mv = hg2.find_table(MSG, CM, ['몸통박치기', '할퀴기'], (400, 600)) or hg2.find_table(MSG, CM, ['태클', '클로어택'], (400, 600))
    names = mv[1]
    wf = NARC(rom.get('a/0/1/1')).files
    pers = NARC(rom.get(hg1.NARC_PATHS['personal'])).files
    learn = NARC(rom.get(hg1.NARC_PATHS['learn'])).files
    evo = NARC(rom.get(hg1.NARC_PATHS['evo'])).files
    T = hg1.TYPES
    out = collections.defaultdict(list)
    for nm, s in sorted(slot.items(), key=lambda x: x[1]):
        g = draft[nm]['단계']; p = hg1.personal(pers[s]); ls = hg1.learnset(learn[s])
        if not ls: out['[Lv1]'].append('%s: 기술 없음' % nm); continue
        types = set(p['type']); atk, spa = p['stats'][1], p['stats'][4]
        info = lambda m: (wf[m][2], wf[m][3], wf[m][4])        # 분류, 위력, 타입
        att = [(l, m) for l, m in ls if info(m)[1] > 0]
        desc = lambda l, m: '%d:%s(%s %d)' % (l, names[m], T[info(m)[2]] if info(m)[2] < len(T) else '?', info(m)[1])
        lo = min(l for l, _ in ls)
        if not any(info(m)[1] > 0 for l, m in ls if l == lo): out['[Lv1]'].append('%s(%s): 첫 레벨 %d 에 공격 없음 — %s' % (nm, g, lo, ' '.join(desc(l, m) for l, m in ls if l == lo)))
        c = collections.Counter(m for _, m in ls)
        if any(v > 1 for v in c.values()): out['[겹침]'].append('%s: %s' % (nm, [names[m] for m, v in c.items() if v > 1]))
        if len(ls) > 20: out['[20칸]'].append('%s: %d개' % (nm, len(ls)))
        stab = [(l, m) for l, m in att if info(m)[2] in types]
        if len(set(m for _, m in stab)) < 2: out['[자속]'].append('%s(%s %s): 자기 타입 공격 %d개' % (nm, g, '/'.join(T[t] for t in sorted(types)), len(set(m for _, m in stab))))
        phys = sum(1 for _, m in att if info(m)[0] == 0); spec = sum(1 for _, m in att if info(m)[0] == 1)
        if atk - spa >= 15 and spec >= 2 * max(1, phys): out['[물특]'].append('%s: 공 %d > 특공 %d 인데 물리 %d · 특수 %d' % (nm, atk, spa, phys, spec))
        if spa - atk >= 15 and phys >= 2 * max(1, spec): out['[물특]'].append('%s: 특공 %d > 공 %d 인데 물리 %d · 특수 %d' % (nm, spa, atk, phys, spec))
        if g in ROOKIE:
            for lim_lv, lim_pw in EARLY:
                bad = [desc(l, m) for l, m in att if l <= lim_lv and info(m)[1] >= lim_pw and info(m)[1] != 1]
                if bad: out['[초반]'].append('%s: Lv%d 까지 위력 %d 이상 — %s' % (nm, lim_lv, lim_pw, ' '.join(bad)))
            first = min((l for l, m in stab if info(m)[2] != 0), default=None) if (types - {0}) else None   # 노말 타입 종의 Lv1 몸통박치기는 규칙대로라 뺌
            if not (types - {0}): stab_ok = True
            evl = [prm for m_, prm, t_ in hg1.evos(evo[s]) if m_ == 4]
            ev = min(evl) if evl else None
            if not (types - {0}): pass
            elif first is None or (ev and first >= ev): out['[타입]'].append('%s: 진화(Lv%s) 전까지 자기 타입 공격 없음' % (nm, ev))
            elif first < 5: out['[타입]'].append('%s: 자기 타입 공격을 Lv%d 에 — 너무 이름(%s)' % (nm, first, ' '.join(desc(l, m) for l, m in stab if l == first)))
            if ev:
                after = [desc(l, m) for l, m in ls if l >= ev]
                if after: out['[진화뒤]'].append('%s(진화 Lv%d): %s' % (nm, ev, ' '.join(after)))
    L = ['# 기술 점검 (롬에 실제로 써진 표, 기술_점검.py)', '']
    tot = 0
    for k in ('[초반]', '[타입]', '[Lv1]', '[진화뒤]', '[자속]', '[물특]', '[겹침]', '[20칸]'):
        v = out.get(k, []); tot += len(v)
        L += ['## %s %d곳' % (k, len(v)), ''] + ['- ' + x for x in v] + ['']
    L.insert(2, '> 걸린 곳 합계 %d. 기준은 이 파일 맨 위 설명 참고.' % tot)
    open(A.out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('기술 점검: 걸린 곳 %d (%s) → %s' % (tot, ', '.join('%s %d' % (k, len(v)) for k, v in out.items()), A.out))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
