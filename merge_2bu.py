#!/usr/bin/env python3
"""2부 대사 합치기 (2026-10-14) — 집 Claude 가 쓴 2부 대사 표(2부대사_결과.md)를 NDS_장면대사.tsv 에 넣는다.
사용:   python merge_2bu.py 2부대사_결과.md        → NDS_장면대사.tsv 고침 + 2부대사_검사.txt
규칙 검사: 열 5개, 번호 숫자, 한 줄(\\n·\\f 사이) 20자 이하(이름 변수 {주인공}·{라이벌}은 5자로 셈), 쓸 수 없는 낱말(포켓몬·몬스터볼·체육관·관장·배지·트레이너).
 - 지금 표에 있는 번호: 「새 대사」만 바꿈(실마리는 그대로).
 - 「(삭제)」: 그 줄을 빈 대사로 두지 않고 원래 대사를 그대로 둠(롬 글을 지우면 안 되므로) → 검사 파일에 적음.
 - 230 이상 새 장면: 실마리가 없으면 넣지 않고 검사 파일에 모아 둠(설계자가 원문 자리를 찾아 넣음)."""
import os, sys, re, csv, io

BAD = ('포켓몬', '몬스터볼', '체육관', '관장', '배지', '트레이너')

def width(line):
    return len(re.sub(r'\{(주인공|라이벌)\}', '#####', line))

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '2부대사_결과.md'
    H = os.path.dirname(os.path.abspath(__file__)); tp = os.path.join(H, 'NDS_장면대사.tsv')
    rows = list(csv.DictReader(open(tp, encoding='utf-8'), delimiter='\t')); by = {r['번호']: r for r in rows}
    got = []
    for l in open(src, encoding='utf-8').read().split('\n'):
        l = l.strip()
        if not l.startswith('|') or l.startswith('|---') or l.startswith('| #') or l.startswith('| 번호'): continue
        c = [x.strip() for x in l.strip('|').split('|')]
        if len(c) < 5 or not c[0].isdigit(): continue
        got.append((c[0], c[1], c[2], c[3], '|'.join(c[4:]).strip()))
    L = ['== 2부 대사 합치기 — 받은 줄 %d' % len(got)]; changed = 0; kept = []; newrows = []; warn = []
    for num, scene, who, clue, text in got:
        t = text.replace('\\\\n', '\\n').replace('\\\\f', '\\f')
        for line in re.split(r'\\[nf]', t):
            if width(line) > 20: warn.append('%s: 한 줄 %d자 「%s」' % (num, width(line), line))
        for w in BAD:
            if w in t: warn.append('%s: 쓰면 안 되는 낱말 「%s」' % (num, w))
        if t in ('(삭제)', '삭제', ''):
            kept.append(num); continue
        if num in by:
            by[num]['새 대사'] = t; changed += 1
        else:
            newrows.append((num, scene, who, clue, t))
    out = io.StringIO(); wr = csv.DictWriter(out, fieldnames=list(rows[0].keys()), delimiter='\t', lineterminator='\n'); wr.writeheader()
    for r in rows: wr.writerow(r)
    open(tp, 'w', encoding='utf-8', newline='\n').write(out.getvalue())
    L.append('바꾼 줄 %d, (삭제)라서 원래 대사 둔 줄 %d: %s' % (changed, len(kept), ' '.join(kept)))
    L.append('새 장면(원문 자리 없음 — 설계자가 넣음) %d줄:' % len(newrows)); L += ['  ' + ' | '.join(x) for x in newrows]
    L.append('경고 %d건:' % len(warn)); L += ['  ' + w for w in warn]
    open('2부대사_검사.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:3])); print('→ 2부대사_검사.txt')

if __name__ == '__main__':
    main()
