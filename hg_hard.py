#!/usr/bin/env python3
"""난이도 하드 롬 만들기 + 밸런스 보고 (2026-10-14, 사용자: 「난이도는 노말과 하드 정도로만」)
사용:   python hg_hard.py "<최종 노말 롬.nds>" [--out 최종_하드.nds] [--plus 3] [--boss 5]
하는 일:
 - 일반 트레이너 파티 레벨 +3, 주요 트레이너(NDS_트레이너.tsv 의 수호자·4천왕·챔피언·라이벌·간부·정우) +5 (100 넘지 않게). 야생은 그대로.
 - 레벨이 오르면 「레벨 안전장치」와 반대로 진화 후 종으로 올리지는 않음(종은 그대로, 레벨만).
 - 보고(balance_report.txt): 주요 트레이너를 설계 순서대로 「최고 레벨 노말 → 하드」로 적어 순서가 뒤집히는 곳(앞 상대가 뒤 상대보다 센 곳)을 표시.
   야생 파일마다 걷기 레벨 범위도 적어 설계자가 지역 순서와 맞춰 봄."""
import os, sys, csv, struct, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, bps_make, bps_apply, say, R
import hg3

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default='최종_하드.nds')
    ap.add_argument('--plus', type=int, default=3); ap.add_argument('--boss', type=int, default=5)
    A = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== 하드 롬 — 롬 %s (일반 +%d, 주요 +%d)' % (rom.code, A.plus, A.boss))
    trd = NARC(rom.get(hg1.NARC_PATHS['trdata'])); trp = NARC(rom.get(hg1.NARC_PATHS['trpoke']))
    MSG = []
    for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
        try: MSG.append(hg1.msg_decode(f))
        except Exception: MSG.append((0, []))
    CM, NAMEF, _ = hg1.infer_charmap(MSG, set())
    names = [CM.dec(e) for e in MSG[NAMEF][1]]
    trn = None
    for fi, (_, ent) in enumerate(MSG):
        if abs(len(ent) - len(trd.files)) <= 1:
            nm = [CM.dec(e) for e in ent]
            if sum(1 for x in nm if x and len(x) <= 6) > len(nm) * 0.5: trn = nm; break
    rows = list(csv.DictReader(open(os.path.join(here, 'NDS_트레이너.tsv'), encoding='utf-8'), delimiter='\t'))
    # 주요 트레이너 번호: 새 이름(바뀐 뒤 이름표)으로 찾음. 라이벌·간부는 직업·이름 n번째 규칙 대신 「파티 레벨이 높은 같은 이름」 전부
    boss_ids = set(); order = []
    if trn:
        for r in rows:
            nm = hg3.skel_name(r['새 이름']) if r.get('새 이름') else ''
            hn = r['하트골드 이름'].strip()
            cands = [i for i, x in enumerate(trn) if hg3.skel_name(x) in (nm, hg3.skel_name(hn.split('#')[0]))]
            if cands: boss_ids.update(cands); order.append((r['키'], nm or hn, cands))
    files = list(trp.files); n_up = n_boss = 0; levels_before = {}; levels_after = {}
    for i, d in enumerate(trd.files):
        t = hg1.trdata(d)
        if not t or i >= len(files): continue
        party, size = hg1.trpoke(files[i], t['flags'], t['n'])
        if not party: continue
        b = bytearray(files[i]); plus = A.boss if i in boss_ids else A.plus
        levels_before[i] = max(m['lv'] for m in party)
        for k, m in enumerate(party):
            o = k * size + 2
            lv = min(100, m['lv'] + plus); struct.pack_into('<H', b, o, lv)
        files[i] = bytes(b); levels_after[i] = min(100, levels_before[i] + plus)
        if i in boss_ids:                                      # 10/14: 하드는 주요 트레이너가 회복약(23) 2개를 씀
            td = bytearray(trd.files[i]); struct.pack_into('<HH', td, 4, 23, 23); trd.files[i] = bytes(td)
        if i in boss_ids: n_boss += 1
        else: n_up += 1
    trp.files = files
    out = NDS(raw); out.put(hg1.NARC_PATHS['trpoke'], trp.build()); out.put(hg1.NARC_PATHS['trdata'], trd.build()); new_raw = bytes(out.d)
    open(A.out, 'wb').write(new_raw)
    chk = NARC(NDS(new_raw).get(hg1.NARC_PATHS['trpoke'])).files
    bad = sum(1 for i in levels_after if i < len(chk) and (lambda p: (max(m['lv'] for m in p[0]) if p[0] else -1))(hg1.trpoke(chk[i], hg1.trdata(trd.files[i])['flags'], hg1.trdata(trd.files[i])['n'])) != levels_after[i])
    say('트레이너 레벨 올림: 일반 %d명, 주요 %d명, 검산 실패 %d → %s' % (n_up, n_boss, bad, A.out))
    # ---- 밸런스 보고
    B = ['== 밸런스 보고 (노말 → 하드)', '-- 주요 트레이너 설계 순서(NDS_트레이너.tsv)대로 최고 레벨. ↓ = 앞 상대보다 낮음(뒤집힘, 확인)']
    prev = None
    for key, nm, ids in order:
        best = max(ids, key=lambda i: levels_before.get(i, 0)); lb, la = levels_before.get(best, 0), levels_after.get(best, 0)
        flag = ' ↓' if prev is not None and lb < prev - 2 and not key.startswith(('Rival', 'Executive')) else ''
        B.append('%-16s %-10s 번호 %3d  Lv %3d → %3d%s' % (key, nm, best, lb, la, flag))
        if not key.startswith(('Rival', 'Executive')): prev = lb
    enc = NARC(rom.get(hg1.NARC_PATHS['enc'])).files
    B.append('\n-- 야생 파일별 걷기 레벨(최소~최대, 0 = 없음). HG1 encounters.tsv 로 장소를 붙여 지역 순서와 비교')
    for i, d in enumerate(enc):
        if len(d) != hg3.ENC_SIZE: continue
        lv = [x for x in d[8:20] if x]
        if lv: B.append('파일 %3d: Lv %2d~%2d' % (i, min(lv), max(lv)))
    open('balance_report.txt', 'w', encoding='utf-8').write('\n'.join(B) + '\n')
    say('밸런스 보고 → balance_report.txt (주요 트레이너 %d줄)' % len(order))

if __name__ == '__main__':
    main()
