#!/usr/bin/env python3
"""화면에서 잘리는 7글자 종 이름을 6글자로 줄인다 (2026-10-20, 사용자 선택).
사용:   python inject_names.py <입력 롬> <출력 롬>
왜:     배틀 이름판·요약 화면의 이름 칸이 6글자까지라(원본 종 이름 최대 6) 7글자 이름은 마지막 글자가 잘렸음
        (블랙워그레이몬 → 「블랙워그레이」, 벨리얼묘티스몬 → 「벨리얼묘티스」) — 에뮬 전투·요약 화면에서 확인.
무엇을: 모든 글 묶음에서 아래 이름을 찾아 바꿈(종 이름표·대사·도감 등). 이름이 안 든 글 항목은 손대지 않음.
        내부 표(NDS_종_초안.tsv·그림출처 등)는 옛 이름 그대로 — 그림·칸 연결이 이름으로 되어 있어서, 화면 글자만 마지막 단계에서 바꾼다."""
import sys, os, csv
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, P)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
RENAME = {'블랙워그레이몬': '블랙워그레몬', '벨리얼묘티스몬': '벨리얼묘티몬'}
src, dst = sys.argv[1], sys.argv[2]
raw = open(src, 'rb').read(); rom = NDS(raw); nar = NARC(rom.get(hg1.NARC_PATHS['msg']))
draft = {r['이름'] for r in csv.DictReader(open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t')}
MSG = []
for f in nar.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
# 글 안의 띄어쓰기는 {01DE} 로 풀려 나오므로 이름 자체(붙어 있는 글자)만 바꿈
n_total = 0; n_files = 0; files = list(nar.files)
for fi, (seed, ents) in enumerate(MSG):
    changed = False; new_ents = list(ents)
    for ei, cs in enumerate(ents):
        try: t = CM.dec(cs)
        except Exception: continue
        if not any(k in t for k in RENAME): continue
        t2 = t
        for a, b in RENAME.items(): t2 = t2.replace(a, b)
        enc = CM.enc(t2)
        assert CM.dec(enc) == t2, '글 다시 쓰기 검산 실패 msg%d#%d' % (fi, ei)
        new_ents[ei] = enc; changed = True; n_total += 1
    if changed: files[fi] = msg_encode(seed, new_ents); n_files += 1
nar.files = files; how = rom.put(hg1.NARC_PATHS['msg'], nar.build()); open(dst, 'wb').write(bytes(rom.d))
print('이름 바꿈: 글 항목 %d개 (글 묶음 %d개) %s (%s)' % (n_total, n_files, RENAME, how))
