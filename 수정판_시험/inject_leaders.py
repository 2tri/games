#!/usr/bin/env python3
"""python inject_leaders.py <입력 롬> <출력 롬> — 2부 수호자 이름 통일 (2026-10-28)
2부 수호자 자리는 원작 관장(마티스·초련·이슬·민화·도희·강연·웅·그린)인데, 디지바이스 등록·전화·체육관 졸개 대사에 원작 이름이 그대로 남아 있었다
(예: 예지를 등록하면 「이슬을 등록했다!」). 트레이너 이름(글 723)과 같은 이름 산해·엔젤우몬·예지·릴리몬·재하·스팅몬·쥬드몬·리키로 바꾼다.
줄 번호를 정해 놓고 바꾸므로 「이슬」이 들어간 다른 낱말(아이슬란드·이슬만)은 건드리지 않는다. 여러 번 돌려도 같은 결과."""
import sys, os, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
# 앞에 있는 것이 먼저 적용된다(긴 것 먼저)
PAIRS = [('마티스 소령님', '산해님'), ('마티스체육관', '디지몬체육관'), ('마티스님', '산해님'), ('마티스', '산해'),
         ('민화 언니는', '릴리몬님은'), ('민화언니는', '릴리몬님은'), ('민화 언니를', '릴리몬님을'), ('민화 언니', '릴리몬님'), ('민화님', '릴리몬님'), ('민화입니다만', '릴리몬입니다만'), ('민화를', '릴리몬을'), ('민화', '릴리몬'),
         ('도희 언니란다', '재하 형이란다'), ('도희님', '재하님'), ('도희와도', '재하와도'), ('도희를', '재하를'), ('도희야', '재하야'), ('도희', '재하'),
         ('이슬이 없어서', '예지가 없어서'), ('이슬이가', '예지가'), ('이슬이를', '예지를'), ('이슬이야', '예지야'), ('이슬님은', '예지님은'), ('이슬을', '예지를'), ('이슬', '예지'),
         ('초련님에게', '엔젤우몬님에게'), ('초련님은', '엔젤우몬님은'), ('초련을', '엔젤우몬을'), ('초련인데', '엔젤우몬인데'), ('초련', '엔젤우몬'),
         ('강연이 있는', '스팅몬이 있는'), ('강연을', '스팅몬을'), ('강연이다', '스팅몬이다'), ('강연', '스팅몬'),
         ('웅이님은', '쥬드몬님은'), ('웅이를', '쥬드몬을'), ('웅인데', '쥬드몬인데'),
         ('그린의 집', '리키의 집'), ('그린을', '리키를'), ('그린이야', '리키야'),
         ('그녀는', '그 아이는'), ('레드와 싸워서', '마일도와 싸워서'), ('태초마을', '겐나이 마을')]
WHOLE = {(652, 0): ('웅', '쥬드몬'), (642, 0): ('그린', '리키')}     # 줄 전체가 이름 하나인 곳
LINES = [(336, 1), (647, 0), (647, 10), (722, 336), (722, 337), (722, 338), (722, 339), (722, 341), (722, 344), (478, 3),
         (486, 18), (486, 20), (488, 1), (722, 345), (722, 347), (722, 349), (722, 353), (722, 355), (641, 0), (641, 10),
         (356, 8), (509, 9), (509, 10), (509, 13), (509, 14), (509, 16), (510, 2), (640, 0), (640, 10), (643, 14),
         (358, 2), (464, 14), (645, 0), (645, 10), (678, 9), (722, 323), (722, 332),
         (251, 5), (650, 0), (650, 10), (678, 10), (722, 371),
         (514, 11), (52, 24), (646, 0), (646, 10),
         (46, 2), (652, 10), (722, 317),
         (441, 5), (444, 9), (642, 10), (514, 5), (480, 1)]
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
files = list(mn.files); dirty_banks = set()
OLDNAMES = ('마티스', '민화', '도희', '이슬', '초련', '강연', '웅이', '그린', '레드와', '태초마을', '그녀는')
for b, i in LINES + list(WHOLE):
    seed, ents = MSG[b]; ents = list(ents); t = CM.dec(ents[i]); new = t
    if (b, i) in WHOLE:
        o, n = WHOLE[(b, i)]
        if new.replace(SP, '') == o: new = n
    else:
        for o, n in PAIRS: new = new.replace(T(o), T(n))
    if new == t: continue
    chk = new.replace(SP, '')
    if (b, i) not in WHOLE: assert not any(x in chk for x in OLDNAMES), '%d:%d 옛 이름이 남음: %s' % (b, i, chk[:40])
    enc = CM.enc(new); assert CM.dec(enc) == new, '%d:%d 검산 실패' % (b, i)
    ents[i] = enc; MSG[b] = (seed, ents); files[b] = msg_encode(seed, ents); dirty_banks.add(b); done.append('%d:%d' % (b, i))
if done: mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
print('수호자 이름 통일 %d줄' % len(done))
for d in done: print(' -', d)
