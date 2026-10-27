#!/usr/bin/env python3
"""python inject_sanhae_ship.py <입력 롬> <출력 롬> — 2부 시작 「배 안에서 산해가 먼저 말을 건다」 (설계 2부_초안 #40 · 2부대사_결과 230) 연결 (2026-10-27)
문제(에뮬 확인): 산해 대사가 글 254:9 에 들어 있었는데, 원작에서 이 글은 「두 번째 항해부터」 선원이 하는 말(스크립트 156 진입 1, VAR_SCENE_SS_AQUA>=7)이라
첫 항해 장면에는 안 나옴. 첫 항해에 나오는 장면(스크립트 156 진입 4 = 복도에서 노신사가 달려와 「손녀를 찾고 있단다」, 글 254:7)은 원작 그대로였음.
고침:
 · 글 254:7 (노신사 장면 대사) → 산해 대사 (장면 연출·움직임은 그대로: 달려와서 말을 걸고 떠남 = 「먼저 말을 건다」)
 · 글 254:9 (둘째 항해부터 선원 말) → 평범한 선원 인사로
 · 지도307 복도 인물(오브젝트 3, 노신사 그림 341) 그림 → 343(주황 머리 소년, 산해 인상)
줄바꿈 규칙은 fix_linebreaks.py 와 같음. 여러 번 돌려도 같은 결과."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []
BANK, MAP_EVENT, OBJ, OLD_SPR, NEW_SPR = 254, 278, 3, 341, 343
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
SANHAE = '너{01AD} 신대륙은 처음이지{01AC}\\n지금 카이저 때문에\\f난리라고{01AB}\\f나는 산해{01AB}\\f우리 같이 싸우자{01AB}\\r'
SAILOR = '이번 항해도 잘 부탁하네{01AB}\\n피곤하면 방에서 쉬게나\\r'
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
seed, ents = MSG[BANK]; ents = list(ents); dirty = False
assert len(ents) == 11, '글 254 가 예상과 다름'
for i, txt, name in ((7, SANHAE, '배 안 산해 대사(노신사 장면 자리)'), (9, SAILOR, '둘째 항해 선원 인사')):
    enc = CM.enc(T(txt)); assert CM.dec(enc) == T(txt), '글 %d:%d 검산 실패' % (BANK, i)
    if ents[i] != enc: ents[i] = enc; dirty = True; done.append(name)
if dirty:
    files = list(mn.files); files[BANK] = msg_encode(seed, ents); mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())

ev = NARC(nds.get(hg1.NARC_PATHS['zone_event'])); EV = list(ev.files); g = bytearray(EV[MAP_EVENT])
o = 4 + 20 * struct.unpack_from('<I', g, 0)[0]; no = struct.unpack_from('<I', g, o)[0]; o += 4
ob = list(struct.unpack_from('<16H', g, o + 32 * OBJ)); assert ob[0] == OBJ and ob[1] in (OLD_SPR, NEW_SPR), '지도307 오브젝트 3 이 예상과 다름: %s' % ob
if ob[1] != NEW_SPR:
    ob[1] = NEW_SPR; struct.pack_into('<16H', g, o + 32 * OBJ, *ob); EV[MAP_EVENT] = bytes(g); ev.files = EV
    nds.put(hg1.NARC_PATHS['zone_event'], ev.build()); done.append('복도 인물 그림 341 → 343')
open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('배 안 산해 %d건' % len(done))
