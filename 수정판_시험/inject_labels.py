#!/usr/bin/env python3
"""python inject_labels.py <입력 롬> <출력 롬> — 2부 인물 대사에 말하는 사람 이름표 붙이기 (2026-10-28, 사용자 지적: 걷는 그림이 일반 인물이라 누가 누군지 모름)
2부대사_결과.md 표의 화자와 롬 글을 대조해(labscan 방식) 이름표(「이름{01C4} 」)가 빠진 필드 대사에 붙인다.
첫 줄(이름표 포함)이 19자를 넘으면 붙이지 않고 알린다. 이미 이름표가 있으면 그대로. 여러 번 돌려도 같은 결과."""
import sys, os, re, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read())
BS = chr(92)
TARGETS = [(480, [0, 1], '산해'), (526, [0, 1], '엔젤우몬'), (464, [8, 9], '예지'), (487, [0, 1], '릴리몬'), (509, [0, 1], '재하'),
           (407, [34], '스팅몬'), (52, [0, 1], '스팅몬'), (457, [0, 2], '쥬드몬'), (449, [1], '리키'), (446, [6, 7], '겐나이'),
           (515, [0], '정우'), (538, [18], '겐나이'), (340, [4], '예지'), (358, [0], '예지'), (531, [0], '나리')]
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append(None)
CM = hg1.infer_charmap([m if m else (0, []) for m in MSG], draft)[0]
files = list(mn.files); done = []; skipped = []

def first_line_len(t):
    s = re.split('[' + BS + BS + '][nfr]', t, 1)[0]
    s = re.sub(r'\{FFFE\}\{[0-9A-F]{4}\}\{[0-9A-F]{4}\}\{[0-9A-F]{4}\}\{[0-9A-F]{4}\}', 'XXX', s)   # 변수 칸은 3글자 몫
    s = re.sub(r'\{[0-9A-F]{4}\}', 'X', s)
    return len(s.replace('{01DE}', ' '))

for b, idxs, name in TARGETS:
    seed, ents = MSG[b]; ents = list(ents); dirty = False
    for i in idxs:
        t = CM.dec(ents[i]); plain = t.replace('{01DE}', '')
        k = plain.find('{01C4}')
        if 0 < k <= 7 and BS not in plain[:k]: continue                      # 이미 이름표 있음
        new = name + '{01C4}{01DE}' + t
        if first_line_len(new) > 19: skipped.append('%d:%d %s' % (b, i, name)); continue
        enc = CM.enc(new); assert CM.dec(enc) == new, '%d:%d 검산 실패' % (b, i)
        ents[i] = enc; dirty = True; done.append('%d:%d %s' % (b, i, name))
    if dirty: MSG[b] = (seed, ents); files[b] = msg_encode(seed, ents)
if done: mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
for s in skipped: print(' ! 첫 줄이 길어 못 붙임:', s)
print('이름표 %d줄 붙임, %d줄 건너뜀' % (len(done), len(skipped)))
