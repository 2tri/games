#!/usr/bin/env python3
"""python inject_dark.py <입력 롬> <출력 롬> — 어둠 진화 도구 손보기(2026-10-22 사용자 결정)
1) 검은 톱니 진화 3줄(그레이몬→스컬그레이몬 · 가트몬→레이디데블몬 · 워가루몬→블랙워가루몬)이 「지닌 채 밤에 레벨업」이라 조건이 어려움
   → 낮에도 되게 같은 줄을 낮(방법 18)으로 한 줄씩 더함. 진화표(a/0/3/4) 칸 = 6바이트(방법, 값, 대상), 한 종 7칸 한도.
2) 일반 상점 표(arm9) 판매 시기: 어둠의돌 단계 6(배지 8개) → 2(배지 1개부터), 검은 톱니·금속코트 6 → 5(배지 7개부터 = 태그와 같음).
   표 칸 = {도구 u16, 단계 u16}. 단계 1=배지 0 · 2=1~2 · 3=3~4 · 4=5~6 · 5=7 · 6=8+ (pret scrcmd_mart.c). 상점은 배지 수를 그때그때 읽으므로 세이브가 있어도 바로 적용됨.
3) 어둠의돌 도구 설명(msg219#108) 「지닌 채 레벨을 올리면」은 틀림 — 진화표는 「도구 사용」(방법 7)이다. 사용하는 글로 고침."""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import csv
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []

# ---- 1) 검은 톱니 낮 진화
ITEM_BLACK = 326; HELD_DAY, HELD_NIGHT = 18, 19
nar = NARC(nds.get('a/0/3/4')); files = list(nar.files); added = []
for sp, f in enumerate(files):
    d = bytearray(f); ents = [struct.unpack_from('<HHH', d, k) for k in range(0, 42, 6)]
    ents = [e for e in ents if e[0]]
    new = []
    for m, p, t in ents:
        if m == HELD_NIGHT and p == ITEM_BLACK and (HELD_DAY, ITEM_BLACK, t) not in ents:
            new.append((HELD_DAY, ITEM_BLACK, t)); added.append((sp, t))
    if not new: continue
    assert len(ents) + len(new) <= 7, '진화 칸 7개 넘음 종 %d' % sp
    for i, (m, p, t) in enumerate(ents + new): struct.pack_into('<HHH', d, 6 * i, m, p, t)
    files[sp] = bytes(d)
assert len(added) in (0, 3), '검은 톱니 줄이 3개가 아님: %s' % added
if added: nar.files = files; nds.put('a/0/3/4', nar.build())
done.append('검은 톱니 낮 진화 +%d줄 %s' % (len(added), added) if added else '검은 톱니 낮 진화 이미 있음')

# ---- 2) 상점 판매 시기
a9o, a9s = struct.unpack_from('<I', nds.d, 0x20)[0], struct.unpack_from('<I', nds.d, 0x2C)[0]
a9 = bytes(nds.d[a9o:a9o + a9s]); seq = (4, 3, 2, 17, 26, 25, 24, 23); pos = -1
for p in range(0, len(a9) - 80):
    if all(struct.unpack_from('<H', a9, p + 4 * k)[0] == v for k, v in enumerate(seq)):
        assert pos < 0, '일반 상점 표가 둘 이상'; pos = p
assert pos >= 0, '일반 상점 표를 못 찾음'
NEWTIER = {108: 2, 326: 5, 233: 5}; got = {}
for k in range(60):
    it, tr = struct.unpack_from('<HH', a9, pos + 4 * k)
    if it in (0, 0xFFFF) or tr > 8: break
    if it in NEWTIER:
        struct.pack_into('<H', nds.d, a9o + pos + 4 * k + 2, NEWTIER[it]); got[it] = (tr, NEWTIER[it])
assert set(got) == set(NEWTIER), '상점 표에 없는 도구: %s' % (set(NEWTIER) - set(got))
done.append('상점 단계(도구 %s)' % ', '.join('%d: %d→%d' % (i, a, b) for i, (a, b) in got.items()))

# ---- 3) 어둠의돌 설명
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(H, '..', 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
seed, ents = MSG[219]; ents = list(ents)
OLD = '어둠의 돌{01AE} 지닌 채\\n레벨을 올리면 어둠에 물든다{01AE}'.replace(' ', '{01DE}')
NEW = '어둠의 돌{01AE} 디지몬에게 쓰면\\n어둠 갈래로 진화한다{01AE}'.replace(' ', '{01DE}')
cur = CM.dec(ents[108])
if cur == OLD:
    enc = CM.enc(NEW); assert CM.dec(enc) == NEW, '설명 검산 실패'
    ents[108] = enc; fl = list(mn.files); fl[219] = msg_encode(seed, ents); mn.files = fl
    done.append('어둠의돌 설명(%s)' % nds.put(hg1.NARC_PATHS['msg'], mn.build()))
else: assert cur == NEW, '어둠의돌 설명이 예상과 다름: %r' % cur; done.append('어둠의돌 설명 이미 바꿈')

open(dst, 'wb').write(bytes(nds.d)); print('ok', ' / '.join(done))
