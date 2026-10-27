#!/usr/bin/env python3
"""python inject_gennai.py <입력 롬> <출력 롬> — 박사 이름 통일 (2026-10-27, 사용자 위임 「맞는 흐름으로」)
용어표(NDS_용어표.tsv 111·112줄)는 공박사·오박사 모두 「겐나이」인데 롬에는 「공박사」 49줄·「오박사」 73줄이 남아 있었고
화자 이름표만 「겐나이:」라 한 줄 안에서 이름이 부딪혔다(예: 「겐나이: … 내가 디지몬 연구가인 오박사다」).
롬 안에 「겐나이는 여럿이란다」(글 372:11)가 이미 있어 모든 박사 = 겐나이 로 통일. 세 이름 모두 받침 없는 세 글자라 조사·줄 길이 그대로.
여러 번 돌려도 같은 결과."""
import sys, os, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read())
OLD, NEW = ('오박사', '공박사'), '겐나이'
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append(None)
CM = hg1.infer_charmap([m if m else (0, []) for m in MSG], draft)[0]
files = list(mn.files); n = 0; banks = 0
for b, m in enumerate(MSG):
    if not m: continue
    seed, ents = m; ents = list(ents); dirty = False
    for i, e in enumerate(ents):
        try: t = CM.dec(e)
        except Exception: continue
        if not any(o in t for o in OLD): continue
        new = t
        for o in OLD: new = new.replace(o, NEW)
        enc = CM.enc(new); assert CM.dec(enc) == new, '%d:%d 검산 실패' % (b, i)
        ents[i] = enc; dirty = True; n += 1
    if dirty: files[b] = msg_encode(seed, ents); MSG[b] = (seed, ents); banks += 1
# 통일하면 어색해지는 줄 손보기: 겐나이가 다른 겐나이(시작의 마을)를 말하는 줄에 「시작의 마을」을 붙이고, 둘이던 이름은 하나로.
# 줄바꿈 규칙(쪽마다 \n 한 번 뒤는 \f, 새 쪽 \r)·한 줄 19자 이내 유지. (글 번호, 옛 조각, 새 조각) — 띄어쓰기는 아래서 {01DE} 로 바꿈
BS = chr(92); N, F, R = BS + 'n', BS + 'f', BS + 'r'
FIX = [
    (372, 0, '앞서 겐나이님에게' + N + '메일을', '앞서 시작의 마을 겐나이님에게' + N + '메일을'),
    (372, 1, '앞서 겐나이님에게' + N + '메일을', '앞서 시작의 마을 겐나이님에게' + N + '메일을'),
    (372, 2, '겐나이님이' + N + '조사해', '시작의 마을 겐나이님이' + N + '조사해'),
    (372, 3, '겐나이가 보낸', '시작의 마을 겐나이가 보낸'),
    (372, 3, F + '겐나이에게 갖다 주렴', F + '시작의 마을 겐나이에게 갖다 주렴'),
    (372, 4, '넌 다시 겐나이님이' + N + '있는 곳으로 돌아갈 거지', '넌 다시 시작의 마을' + N + '겐나이님이 있는 곳으로' + F + '돌아갈 거지'),
    (372, 5, F + '겐나이님에게 전해 주어라', F + '시작의 마을 겐나이님에게' + F + '전해 주어라'),
    (372, 8, '찾아왔더니 마침 겐나이로부터' + F + '심부름꾼이', '찾아왔더니 마침' + F + '시작의 마을 겐나이로부터' + F + '심부름꾼이'),
    (372, 9, '찾아왔더니 마침 겐나이로부터' + F + '심부름꾼이', '찾아왔더니 마침' + F + '시작의 마을 겐나이로부터' + F + '심부름꾼이'),
    (372, 10, '너도 겐나이의 연구를' + F + '도와주고', '너도 시작의 마을 겐나이의' + F + '연구를 도와주고'),
    (653, 14, '겐나이님이나 겐나이님은', '겐나이님은'),
]
SP = '{01DE}'
for b, i, old, new in FIX:
    seed, ents = MSG[b]; ents = list(ents); t = CM.dec(ents[i])
    old, new = old.replace(' ', SP), new.replace(' ', SP)
    if new in t and new not in old: continue          # 이미 고침 (새 조각이 옛 조각을 품고 있어도 되풀이해 붙이지 않음)
    if old not in t:
        assert new in t, '%d:%d 고칠 조각을 못 찾음: %s' % (b, i, old)
        continue
    t2 = t.replace(old, new); enc = CM.enc(t2); assert CM.dec(enc) == t2, '%d:%d 검산 실패' % (b, i)
    ents[i] = enc; MSG[b] = (seed, ents); files[b] = msg_encode(seed, ents); n += 1
if n: mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
print('박사 이름 통일: %d줄 (%d묶음)' % (n, banks))
