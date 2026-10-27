#!/usr/bin/env python3
"""python inject_kaiser.py <입력 롬> <출력 롬> — 2부 「디지몬 카이저 정우」 전투 넣기 (2026-10-27, 사용자 결정 「카이저 넣고 v1 완성」)
설계(2부_초안.md 장면 55 · NDS_트레이너.tsv Mildo 줄 · 2부대사_결과.md 198/199)는 정해져 있었으나 hg3 가 「직업최고:엘리트트레이너」
자리를 못 찾아(report_hg3: 주요 트레이너를 못 찾음: Mildo) 롬에 정우 전투가 없었다.
 ① 트레이너 340(개발용 빈 칸 「철수」, 쓰는 곳·대사 없음) → 이름 「정우」, 직업 53(쓰는 트레이너 0명) → 직업 이름 「디지몬 카이저」 + 그림 ken_tr_ai.png
    파티: 메탈티라몬 64 · 메가시드라몬 64 · 다크퍼펫몬 65 · 기가드라몬 66 · 키메라몬 68 (기술 = 그 레벨까지 배우는 마지막 4개), 도구 회복약 4개(마일도와 같음)
 ② 트레이너 대사표(a/0/5/7 + a/1/3/1 + 글 722)에 정우 3줄: 만남(198) · 졌을 때 · 이긴 뒤 말 걸기(199 = 아군이 됨, 마일도·황제드라몬)
    표를 원래 크기보다 늘리면 넘친 칸을 게임이 못 찾아 대사 없이 전투만 됨(에뮬 확인) → 안 쓰이는 트레이너 540 의 3줄 칸을 돌려씀
 ③ 28번도로(지도32, 카이저 요새 가는 길) 입구 바로 서쪽 (885,265)에 아래를 보는 시야 5 트레이너로 세움(트레이너 사람 스크립트 번호 = 2999 + 트레이너 번호) — 관문에서 들어와 서쪽으로 가면 반드시 마주침
여러 번 돌려도 같은 결과."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT); sys.path.insert(0, H)
import hg1, hg4, hg4_trainer, trainer_cell
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []
TID, CLS, MAP, POS, SPRITE = 340, 53, 32, (885, 265), 324
NAME, CLSNAME = '정우', '디지몬 카이저'
PARTY = [('메탈티라몬', 64), ('메가시드라몬', 64), ('다크퍼펫몬', 65), ('기가드라몬', 66), ('키메라몬', 68)]
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
# 대화창은 두 줄: \n = 첫 줄→둘째 줄, \f = 둘째 줄에서 한 줄 올려 이어 쓰기, \r = 새 쪽 (원작 트레이너 대사와 같은 방식)
# 둘째 줄에서 \n 을 쓰면 셋째 줄로 넘쳐 그 뒤 글이 안 나오고 대화가 끝남(에뮬 확인)
TEXT = {
    0: '정우{01C4} 디지몬 카이저다{01AB}\\n탑을 무너뜨린 게 너희였나\\r어둠의 힘을\\n똑똑히 보여 주지{01AB}\\r',
    1: '{01AE}{01AE}{01AE}{01AE}{01AE}{01AE}이럴 수가\\n내가 지다니{01AE}{01AE}{01AE}\\n',
    2: '정우{01C4} {01AE}{01AE}{01AE}{01AE}{01AE}{01AE}내가\\n뭘 한 거지\\r스팅몬{01AE}{01AE}{01AE}{01AE}{01AE}{01AE} 미안해\\n마일도가 심은 어둠의 씨앗 때문이야\\r파일드라몬과 스팅몬은\\n황제드라몬이 될 수 있어\\r카이저 요새에서\\n마일도가 기다려\\n',
}

# ---------- 글 ----------
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
mfiles = list(mn.files); mdirty = False
def dec(b, i): return CM.dec(MSG[b][1][i])
def put(b, i, text):
    global mdirty
    seed, ents = MSG[b]; ents = list(ents); enc = CM.enc(text); assert CM.dec(enc) == text, '글 %d:%d 검산 실패' % (b, i)
    if i == len(ents): ents.append(enc)
    elif CM.dec(ents[i]) == text: return False
    else: ents[i] = enc
    MSG[b] = (seed, ents); mfiles[b] = msg_encode(seed, ents); mdirty = True; return True
SPECIES = MSG[233][1]; SPN = [CM.dec(e) for e in SPECIES]
NAMEB, CLASSB, TEXTB = 723, 724, 722
assert len(MSG[NAMEB][1]) == 738 and dec(CLASSB, 24).startswith('엘리트'), '트레이너 이름·직업 글 자리가 예상과 다름'
if put(NAMEB, TID, T(NAME)): done.append('트레이너 %d 이름 → %s' % (TID, NAME))
if put(CLASSB, CLS, T(CLSNAME)): done.append('직업 %d 이름 → %s' % (CLS, CLSNAME))

# ---------- 트레이너 자료·파티 ----------
td = NARC(nds.get(hg1.NARC_PATHS['trdata'])); tp = NARC(nds.get(hg1.NARC_PATHS['trpoke'])); TD = list(td.files); TP = list(tp.files)
used_by = [i for i, f in enumerate(TD) if len(f) > 1 and f[1] == CLS and i != TID]
assert not used_by, '직업 %d 를 쓰는 트레이너가 있음: %s' % (CLS, used_by)
learn = NARC(nds.get(hg1.NARC_PATHS['learn'])).files
def moves_at(sp, lv):
    got = []
    for l, m in hg1.learnset(learn[sp]):
        if l <= lv and m not in got: got.append(m)
    got = got[-4:]
    return got + [0] * (4 - len(got))
items = TD[260][4:12]                                   # 마일도와 같은 회복약 4개
new_td = bytes([3, CLS, 0, len(PARTY)]) + items + struct.pack('<I', 7) + bytes(4)
body = b''
for nm, lv in PARTY:
    sp = SPN.index(nm); mv = moves_at(sp, lv)
    body += struct.pack('<BBHHH4HH', 100, 0, lv, sp, 0, *mv, 0)
if TD[TID] != new_td or TP[TID] != body:
    TD[TID] = new_td; TP[TID] = body; td.files = TD; tp.files = TP
    nds.put(hg1.NARC_PATHS['trdata'], td.build()); nds.put(hg1.NARC_PATHS['trpoke'], tp.build())
    done.append('트레이너 %d 파티: %s' % (TID, ', '.join('%s %d' % p for p in PARTY)))

# ---------- 트레이너 대사표 ----------
tbn = NARC(nds.get('a/0/5/7')); ofn = NARC(nds.get('a/1/3/1'))
tb = bytearray(tbn.files[0]); of = bytearray(ofn.files[0])
E = [struct.unpack_from('<HH', tb, i) for i in range(0, len(tb), 4)]
assert len(E) == len(MSG[TEXTB][1]) or any(t == TID for t, _ in E), '대사표와 글 수가 다름'
have = {ty: i for i, (t, ty) in enumerate(E) if t == TID}
if not have:
    # 표를 원래 크기(1717칸)보다 늘리면 넘친 칸을 게임이 못 찾음(에뮬 확인: 정우·333번 모두 끝 칸에선 대사 없이 바로 전투)
    # → 쓰이지 않는 트레이너 540(애호가클럽 수비: 필드 배치·TrainerBattle 참조 없음)의 3줄 칸을 정우 몫으로 돌려씀
    DONOR = 540
    o = struct.unpack_from('<H', of, 2 * DONOR)[0] // 4
    assert [E[o + k] for k in range(3)] == [(DONOR, 0), (DONOR, 1), (DONOR, 2)], '트레이너 %d 대사 칸이 예상과 다름' % DONOR
    for k in range(3): struct.pack_into('<HH', tb, 4 * (o + k), TID, k); E[o + k] = (TID, k)
    struct.pack_into('<H', of, 2 * TID, 4 * o)
    have = {ty: o + ty for ty in (0, 1, 2)}
    tbn.files = [bytes(tb)]; ofn.files = [bytes(of)]
    nds.put('a/0/5/7', tbn.build()); nds.put('a/1/3/1', ofn.build()); done.append('트레이너 %d 의 대사 칸 %d~%d 를 정우 몫으로' % (DONOR, o, o + 2))
for ty, txt in TEXT.items():
    if put(TEXTB, have[ty], T(txt)): done.append('정우 대사 %d' % ty)
assert len(MSG[TEXTB][1]) == len(E), '대사표 줄 수와 글 수가 다름'
if mdirty: mn.files = mfiles; nds.put(hg1.NARC_PATHS['msg'], mn.build())

# ---------- 직업 그림 ----------
art = NARC(nds.get('a/0/5/8')); files = list(art.files); per = 5; base_i = CLS * per
rows80, pal = hg4_trainer.load_png(os.path.join(ROOT, 'games', 'digimon', 'art', 'src', 'people', 'ken_tr_ai.png'))
f0 = files[base_i]; c0 = f0.find(b'RAHC'); info = trainer_cell.parse_ncer(files[base_i + 2]); nb = f0[c0 + 0x20:]
for ci in range(len(info['cells'])): nb = trainer_cell.disassemble(nb, info, ci, rows80)
new0 = f0[:c0 + 0x20] + nb
old4, mode, w = hg4_trainer.decode_any(files[base_i + 4])
new4 = hg4_trainer.encode_any(files[base_i + 4], [r + r for r in rows80] if w == 160 else rows80, mode)
new1 = hg4.nclr_with_colors(files[base_i + 1], pal)
if (files[base_i], files[base_i + 1], files[base_i + 4]) != (new0, new1, new4):
    files[base_i], files[base_i + 1], files[base_i + 4] = new0, new1, new4
    art.files = files; nds.put('a/0/5/8', art.build()); done.append('직업 %d 그림 → ken_tr_ai.png' % CLS)

# ---------- 28번도로에 세우기 ----------
hdr_ev = None
ev = NARC(nds.get(hg1.NARC_PATHS['zone_event'])); EV = list(ev.files)
# 지도 32 의 이벤트 파일 번호: 머리말 표(arm9 RAM 이 아니라 롬의 arm9)에서 찾기 어려워 — 이벤트 안 워프(887,266→299)로 확인
cand = [i for i, g in enumerate(EV) if len(g) > 8 and struct.pack('<6H', 887, 266, 299, 3, 0, 0)[:8] in g]
assert len(cand) == 1, '28번도로 이벤트 파일을 하나로 못 찾음: %s' % cand
ei = cand[0]; g = bytearray(EV[ei])
o = 0; nb_ = struct.unpack_from('<I', g, o)[0]; o += 4 + 20 * nb_; no_at = o; no = struct.unpack_from('<I', g, o)[0]; o += 4
objs = [list(struct.unpack_from('<16H', g, o + 32 * i)) for i in range(no)]
if any(ob[5] == 2999 + TID for ob in objs): done.append('이미 있음: 28번도로 정우')
else:
    z = objs[0][14:16] if objs else [0, 0]
    ob = [no, SPRITE, 0, 1, 0, 2999 + TID, 1, 5, 0, 0, 0, 0, POS[0], POS[1]] + list(z)   # 아래를 보고, 시야 5
    g = g[:o + 32 * no] + struct.pack('<16H', *ob) + g[o + 32 * no:]
    struct.pack_into('<I', g, no_at, no + 1)
    EV[ei] = bytes(g); ev.files = EV; nds.put(hg1.NARC_PATHS['zone_event'], ev.build())
    done.append('28번도로(이벤트 파일 %d) (%d,%d)에 정우 세움' % (ei, POS[0], POS[1]))

open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('정우 넣기 %d건' % len(done))
