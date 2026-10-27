#!/usr/bin/env python3
"""python inject_mildo.py <입력 롬> <출력 롬> — 2부 마일도 최종전 대사 넣기 (2026-10-27)
설계표(2부대사_결과.md 206~208)는 있었으나 롬에는 원작 레드의 「……」 점 줄만 남아 있었다.
 · 전투 전  = 글 묶음 125(은빛산 꼭대기, 지도465 스크립트 107)의 0번   ← 206
 · 졌을 때  = 트레이너 260 대사 종류 1(마일도가 지면 전투 화면에 나옴)   ← 207
 · 이겼을 때 = 트레이너 260 대사 종류 20(플레이어가 지면)               ← 208
 · 글 125 의 1번(이긴 뒤 필드 대사) = 「정우에게 전해 다오 미안했다고」(설계표에 없던 끝맺음)
줄바꿈 규칙은 fix_linebreaks.py 와 같음(쪽마다 첫 줄 \\n 둘째 줄, 새 쪽 \\r). 여러 번 돌려도 같은 결과."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT); sys.path.insert(0, H)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []
TID, FIELD_BANK = 260, 125
D = '{01AE}' * 6                      # 「……」
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
BATTLE_BEFORE = '마일도{01C4} ' + D + '왔군\\r나는 마일도\\n어둠의 씨앗을 심은 자\\r씨앗이여' + '{01AD}' + ' 깨어나라\\n벨리얼묘티몬{01AB}\\r'
LOSE_LINE = '어둠이' + D + '\\n걷히다니\\r유대의 힘' + D + '\\n그것이 답이었나\\n'
WIN_LINE = '어둠은\\n끝나지 않는다{01AB}\\n'
AFTER_FIELD = '마일도{01C4} ' + D + '정우에게 전해 다오\\n미안했다고\\r'    # 전투 중 207 과 겹치지 않게 정우와 이어지는 끝맺음(에뮬: 207 을 되풀이하면 어색)

draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
mfiles = list(mn.files); mdirty = False
def put(b, i, text):
    global mdirty
    seed, ents = MSG[b]; ents = list(ents); enc = CM.enc(T(text)); assert CM.dec(enc) == T(text), '글 %d:%d 검산 실패' % (b, i)
    if CM.dec(ents[i]) == T(text): return False
    ents[i] = enc; MSG[b] = (seed, ents); mfiles[b] = msg_encode(seed, ents); mdirty = True; return True

tb = NARC(nds.get('a/0/5/7')).files[0]; of = NARC(nds.get('a/1/3/1')).files[0]
E = [struct.unpack_from('<HH', tb, i) for i in range(0, len(tb), 4)]
o = struct.unpack_from('<H', of, 2 * TID)[0] // 4
at = {}
while o < len(E) and E[o][0] == TID: at[E[o][1]] = o; o += 1
assert 1 in at and 20 in at, '마일도 대사 칸(1·20)을 못 찾음: %s' % at
assert len(MSG[FIELD_BANK][1]) == 2, '글 125 가 예상과 다름'
for (b, i), txt, name in (((FIELD_BANK, 0), BATTLE_BEFORE, '마일도 전투 전'), ((722, at[1]), LOSE_LINE, '마일도 졌을 때'),
                          ((722, at[20]), WIN_LINE, '마일도 이겼을 때'), ((FIELD_BANK, 1), AFTER_FIELD, '마일도 이긴 뒤')):
    if put(b, i, txt): done.append(name)
if mdirty: mn.files = mfiles; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('마일도 대사 %d건' % len(done))
