#!/usr/bin/env python3
"""python inject_rival.py <입력 롬> <출력 롬> — 2부 매튜 6·7차 새 대사 + 리키 첫 대사 고침 (2026-10-28, 사용자 위임 「어울리는 걸로」)
설계표(2부대사_결과.md 191~193·200~202·195)는 있었으나 롬에는 원작 라이벌 대사가 그대로였다.
 · 6차 = 트레이너 285~287(워가루몬 Lv50 에이스) : 만남 = 글 48:0 · 졌을 때(종류 1) = 192 · 이겼을 때(종류 20) = 193
 · 7차 = 트레이너 489~491(메탈가루몬 Lv59) : 만남 = 글 517:3 · 졌을 때 = 201 · 이겼을 때 = 202 · 이긴 뒤 필드(517:4) = 다음 싸움 안내
 · 리키 449:0 「리키야 많이 컸지?」(리키가 자기 이름을 부르는 꼴) → 「리키: 오랜만이야! 많이 컸구나?」
줄바꿈 규칙은 fix_linebreaks.py 와 같음(\\n 한 번 뒤는 \\f, 새 쪽 \\r). 여러 번 돌려도 같은 결과."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []
BS = chr(92); N, F, R = BS + 'n', BS + 'f', BS + 'r'
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
RIVAL = '{FFFE}{0103}{0002}{0001}{0000}{01C4} '       # 「매튜: 」 (글 48 의 원래 이름표 변수)
PLAYER_VAR = '{FFFE}{0103}{0002}{0000}{0000}{01C4} '   # 글 517 의 원래 이름표 변수
D3 = '{01AE}' * 3

TEXT = {
    (48, 0): RIVAL + '검은 톱니는 버렸어{01AB}' + N + '워가루몬이 돌아왔지{01AB}' + F + '이번엔 진짜' + F + '내 힘이야{01AB}' + R,
    (517, 3): PLAYER_VAR + '마지막 승부다{01AB}' + N + '메탈가루몬' + '{01AD} 간다{01AB}' + F + '우정의 힘을' + F + '봐라{01AB}' + R,
    (517, 4): '다음은 어둠의' + N + '{0125}천왕이 기다린다' + R + '싸우기 전에' + N + '디지몬을 회복하는 것도' + F + '잊지 마' + R,
    (449, 0): '리키{01C4} 오랜만이야{01AB}' + N + '많이 컸구나{01AC}' + F + '페가수스몬과 함께' + F + '희망을 걸게{01AB}',
}
TRAINER = {   # (트레이너 번호들, 대사 종류) → 글
    ((285, 286, 287), 1): '좋아{01AD} 오늘은 네가' + N + '한 수 위야' + F + '톱니 없이도' + F + '나는 더 강해진다' + N,
    ((285, 286, 287), 20): '오늘은 내가' + N + '한 수 위군' + N,
    ((489, 490, 491), 1): D3 + '졌다{01AB}' + N + '하지만 우리 둘이면' + F + '어떤 어둠도' + F + '이길 수 있어' + N,
    ((489, 490, 491), 20): '아직이야{01AB}' + N + '다시 와' + N,
}

draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
files = list(mn.files); mdirty = False
def put(b, i, text, name):
    global mdirty
    seed, ents = MSG[b]; ents = list(ents); enc = CM.enc(T(text)); assert CM.dec(enc) == T(text), '글 %d:%d 검산 실패' % (b, i)
    if ents[i] == enc: return
    ents[i] = enc; MSG[b] = (seed, ents); files[b] = msg_encode(seed, ents); mdirty = True; done.append(name)

for (b, i), txt in TEXT.items(): put(b, i, txt, '글 %d:%d' % (b, i))
tb = NARC(nds.get('a/0/5/7')).files[0]; of = NARC(nds.get('a/1/3/1')).files[0]
E = [struct.unpack_from('<HH', tb, k) for k in range(0, len(tb), 4)]
for (tids, ty), txt in TRAINER.items():
    for tid in tids:
        o = struct.unpack_from('<H', of, 2 * tid)[0] // 4; at = {}
        while o < len(E) and E[o][0] == tid: at[E[o][1]] = o; o += 1
        assert ty in at, '트레이너 %d 에 대사 종류 %d 가 없음' % (tid, ty)
        put(722, at[ty], txt, '트레이너 %d 종류 %d' % (tid, ty))
if mdirty: mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('매튜·리키 대사 %d건' % len(done))
