#!/usr/bin/env python3
"""장면 대사 실마리 고치기 도우미 — 롬은 읽기만 (2026-10-13)
사용:   python hg_clues.py "<디지골드 롬.nds>"   → 실마리_후보.txt
하는 일: NDS_장면대사.tsv 의 줄마다 실마리로 원문을 찾아 보고,
 - 정확히 1개면 OK
 - 0개면: 실마리 낱말 하나하나로 찾아 가장 많이 맞는 원문 후보 3개(앞 60글자)를 적는다
 - 여럿이면: 맞는 원문들을 번호와 함께 앞 50글자씩 적는다(설계자가 실마리를 더 좁힘)
설계자는 이 파일을 보고 NDS_대사.md 의 실마리를 고친다."""
import os, sys, re, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, msg_decode

def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--find', default='', help='쉼표로 나눈 낱말 — 든 글 전문을 실마리_찾기.txt 로')
    A = ap.parse_args()
    H = os.path.dirname(os.path.abspath(__file__))
    rom = NDS(open(A.rom, 'rb').read())
    MSG = []
    for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append((0, []))
    draft = list(csv.DictReader(open(os.path.join(H, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t'))
    CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
    hg1.detect_space(MSG, CM)
    xp = os.path.join(H, 'NDS_글자표_추가.tsv')
    if os.path.exists(xp):
        for r in csv.DictReader(open(xp, encoding='utf-8'), delimiter='\t'):
            try:
                g = hg1.glyph(r.get('글자'))
                if g is None: continue
                CM.extra[int(r['부호'], 16)] = g; CM.rev[g] = int(r['부호'], 16)
            except Exception: pass
    def flat(x): return re.sub(r'\{[0-9A-F]{4}\}|\\[nrf]|\s', '', x)
    dec = [[CM.dec(e) for e in ent] for _, ent in MSG]
    fl = [[flat(x) for x in ent] for ent in dec]
    scenes = list(csv.DictReader(open(os.path.join(H, 'NDS_장면대사.tsv'), encoding='utf-8'), delimiter='\t'))
    def full(fi, j, n=320):
        t = re.sub(r'\{(?!FFFE)[0-9A-F]{4}\}', ' ', dec[fi][j]).replace('{FFFE}', '[이름]')
        return t[:n].replace('\\n', ' ').replace('\\f', ' / ').replace('\\r', ' // ')
    L = ['== 실마리 후보 (롬 %s)' % rom.code]; ok = 0
    G = ['== 「@글」로 고른 원문 확인(설계자가 고른 자리 — 장면과 맞는지 보기)']
    for row in scenes:
        clue = row['실마리'].strip()
        if clue.startswith('@글꼴'):          # 10/14 「@글꼴 ……|…… #0 ~126」: 모양 맞는 파일 후보를 번호 가까운 순으로(레드 자리 확인용)
            mm = re.match(r'@글꼴\s+(.+?)\s+#(\d+)\s+~(\d+)', clue)
            if mm:
                shape = [flat(x) for x in mm.group(1).split('|')]
                cands = [fi for fi, ent in enumerate(fl) if fi != NAMEF and len(shape) <= len(ent) <= len(shape) + 2 and [flat(x) for x in ent[:len(shape)]] == shape]
                cands.sort(key=lambda fi: abs(fi - int(mm.group(3))))
                G.append('%s %s → 「@글꼴」 후보 %d개(가까운 순): %s' % (row['번호'], row['장면'].split(' / ')[-1][:16], len(cands), ', '.join('msg%d(%d줄)' % (fi, len(fl[fi])) for fi in cands[:8])))
            continue
        if clue.startswith('@글'):
            for a, b in re.findall(r'msg(\d+)#(\d+)', clue):
                a, b = int(a), int(b)
                txt = full(a, b) if a < len(dec) and b < len(dec[a]) else '(롬에 없는 자리!)'
                G.append('%s %s → msg%d#%d: %s' % (row['번호'], row['장면'].split(' / ')[-1][:16], a, b, txt))
            continue
        if not clue or clue.startswith('@') or clue.startswith('('): continue
        clues = [flat(c) for c in clue.split('·') if c.strip()]
        hits = [(fi, j) for fi, ent in enumerate(fl) if fi != NAMEF for j, x in enumerate(ent) if clues and all(c in x for c in clues)]
        if len(hits) == 1: ok += 1; continue
        L.append('\n## %s %s | 실마리: %s | 맞는 글 %d개' % (row['번호'], row['장면'][:30], clue, len(hits)))
        if hits:
            for fi, j in hits[:6]: L.append('   msg%d#%d: %s' % (fi, j, re.sub(r'\{[0-9A-F]{4}\}', ' ', dec[fi][j])[:50].replace('\\n', ' ')))
        else:
            score = collections.Counter()
            for c in clues:
                for fi, ent in enumerate(fl):
                    if fi == NAMEF: continue
                    for j, x in enumerate(ent):
                        if c in x: score[(fi, j)] += 1
            for (fi, j), n in score.most_common(3):
                L.append('   후보(%d/%d 낱말) msg%d#%d: %s' % (n, len(clues), fi, j, re.sub(r'\{[0-9A-F]{4}\}', ' ', dec[fi][j])[:60].replace('\\n', ' ')))
            if not score: L.append('   (실마리 낱말이 롬 글 어디에도 없음 — 다른 말로 쓰여 있음)')
    L.insert(1, '정확히 1개 맞는 줄 %d, 고칠 줄 %d' % (ok, sum(1 for l in L if l.startswith('\n## '))))
    open('실마리_후보.txt', 'w', encoding='utf-8').write('\n'.join(L + [''] + G) + '\n')
    if A.find:
        F = ['== 낱말로 찾은 글 전문 (%s)' % A.find]
        for w in [x.strip() for x in A.find.split(',') if x.strip()]:
            fw = flat(w); hits = [(fi, j) for fi, ent in enumerate(fl) if fi != NAMEF for j, x in enumerate(ent) if fw in x]
            F.append('\n## %s — %d개%s' % (w, len(hits), ' (앞 25개)' if len(hits) > 25 else ''))
            for fi, j in hits[:25]: F.append('   msg%d#%d: %s' % (fi, j, full(fi, j)))
        open('실마리_찾기.txt', 'w', encoding='utf-8').write('\n'.join(F) + '\n'); print('→ 실마리_찾기.txt')
    print(L[1]); print('→ 실마리_후보.txt 전문을 설계자에게')

if __name__ == '__main__':
    main()
