#!/usr/bin/env python3
"""「다른 포켓몬」 그림 묶음(a/1/1/4, otherpoke)에 있는 종 칸의 전투 그림을 새 그림으로 맞춘다. (Claude 작성, 2026-10-16)
사용:   python inject_otherpoke.py <입력 롬.nds> <출력 롬.nds> [--species 172] [--table hg2_out/칸표.tsv] [--base <원본 이지 롬.nds>]
왜:     게임 코드(GetMonSpriteCharAndPlttNarcIdsEx, pret/pokeheartgold src/pokemon.c)가 아래 칸(Pichu 172, Unown 201, Castform 351, Deoxys 386,
        Burmy 412, Wormadam 413, Cherrim 421, Shellos 422, Gastrodon 423, Rotom 479, Giratina 487, Shaymin 492, Arceus 493, 알)은
        종이 무엇이든 모양 그림을 a/0/0/4(포켓몬 그림)가 아니라 a/1/1/4(otherpoke)에서 읽는다. hg4 는 a/0/0/4 만 바꾸므로 이 칸에 새 종을 넣으면
        요약·전투 화면에 원래 포켓몬(예: 번개콩알몬 칸 172 → Pichu)이 나온다 (10/16 에뮬레이터 확인: 칸 172 의 a/0/0/4 6개를 다른 종으로 바꿔도 Pichu 가 그대로).
        따라다니는 그림도 비슷하다: 한 종에 필드 그림 파일이 둘 이상(암컷·폼)이면 게임은 성별·폼으로 고르는데 hg4_follow 는 한 파일에만 넣었다
        (칸 25 콩알몬: 파일 322 만 → 암컷은 323 의 Pikachu 암컷 그림, 칸 172: 472 만 → 보통 형태 471 은 Pichu 그대로) → 같은 종의 나머지 파일에 복사.
방법:   칸 172(Pichu) = otherpoke 멤버 154(뒷모습)·155(앞모습)·156·157(뾰족귀 형태 뒷·앞)와 팔레트 252(보통)·253(이로치)·254·255(뾰족귀).
        a/0/0/4 의 같은 칸 멤버(1 = 남 뒷모습, 3 = 남 앞모습, 4 = 보통 팔레트, 5 = 이로치 팔레트)를 그대로 복사. 크기가 다르면 멈춤.
        다른 칸(201·351 …)이 칸표에 새 종으로 있으면 경고만 하고 건드리지 않는다(형태 번호 계산이 달라서 아직 필요 없음)."""
import sys, os, csv, argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
from hg1 import NDS, NARC

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--species', default='172'); ap.add_argument('--table', default='hg2_out/칸표.tsv'); ap.add_argument('--base', default=None, help='원본(이지) 롬 — 따라다니는 그림이 바뀐 파일을 알아내는 데 씀')
A = ap.parse_args()
SP = [int(x) for x in A.species.split(',') if x]
OTHER_SLOTS = {172: 'Pichu', 201: 'Unown', 351: 'Castform', 386: 'Deoxys', 412: 'Burmy', 413: 'Wormadam', 421: 'Cherrim', 422: 'Shellos',
               423: 'Gastrodon', 479: 'Rotom', 487: 'Giratina', 492: 'Shaymin', 493: 'Arceus'}
# 칸 → (뒷모습 멤버들, 앞모습 멤버들, 보통 팔레트 멤버들, 이로치 팔레트 멤버들)  — 형태 0·1(뾰족귀)
PICHU = {172: ([154, 156], [155, 157], [252, 254], [253, 255])}

raw = open(A.rom, 'rb').read()
nd = NDS(raw)
try:
    rows = list(csv.reader(open(A.table, encoding='utf-8'), delimiter='\t'))[1:]
    ours = {int(r[1]): r[0] for r in rows if r[1].isdigit()}
    for s, nm in OTHER_SLOTS.items():
        if s in ours and s not in PICHU: print('경고: 칸 %d(%s 자리)에 새 종 「%s」 — otherpoke 형태 계산을 아직 안 넣음(이 칸은 원래 그림이 나옴)' % (s, nm, ours[s]))
except FileNotFoundError:
    print('칸표 없음 — 경고 검사 건너뜀')

poke = NARC(nd.get('a/0/0/4')).files
oth = NARC(nd.get('a/1/1/4')); of = list(oth.files)
n = 0
for s in SP:
    if s not in PICHU: print('칸 %d 는 아직 지원 안 함' % s); continue
    back, front, pal, shiny = PICHU[s]
    for dst_list, src in ((back, s * 6 + 1), (front, s * 6 + 3), (pal, s * 6 + 4), (shiny, s * 6 + 5)):
        for d in dst_list:
            if len(of[d]) != len(poke[src]): sys.exit('크기 다름: otherpoke %d(%d) ← 포켓몬그림 %d(%d)' % (d, len(of[d]), src, len(poke[src])))
            of[d] = bytes(poke[src]); n += 1
oth.files = of
out = NDS(raw); out.put('a/1/1/4', oth.build())
# 따라다니는 그림: 한 종에 필드 그림 파일이 둘 이상(암컷·폼)인 칸 — hg4_follow 는 색 맞추기로 찾은 한 파일에만 넣었다.
# 게임은 종 번호 → 파일 표(sModelIndexLUT, arm9)로 성별·폼에 따라 파일을 고른다 → 같은 종의 나머지 파일에도 복사.
# 표 위치: 값 u16[494], 종 171·172·173 = (173,174,176) 서명(한국판 롬 arm9 0xFF73C), 파일 = 297 + 값, 다음 종 값과의 차이만큼 파일이 있음.
import struct, hg4_follow as HF
a9o = struct.unpack_from('<I', raw, 0x20)[0]
fol = NARC(out.get('a/0/8/1')); ff = list(fol.files)
base_ff = NARC(NDS(open(A.base, 'rb').read()).get('a/0/8/1')).files if A.base else None
sig = struct.pack('<3H', 173, 174, 176)
a9 = raw[a9o:a9o + struct.unpack_from('<I', raw, 0x2C)[0]]
pos = a9.find(sig)
if base_ff is None: print('--base 없음 — 따라다니는 그림 정리 건너뜀')
elif pos < 0 or a9.find(sig, pos + 2) >= 0 or pos < 171 * 2: print('경고: 필드 그림 번호 표 서명을 arm9 에서 못 찾음/둘 이상 — 따라다니는 그림 정리 건너뜀')
else:
    t0 = pos - 171 * 2; vals = [struct.unpack_from('<H', a9, t0 + 2 * k)[0] for k in range(494)]
    fixed = []
    for sl in sorted(ours):
        if sl >= 493: continue
        files = list(range(297 + vals[sl], 297 + vals[sl + 1]))
        if len(files) < 2: continue
        chg = [f for f in files if f < len(ff) and ff[f] != base_ff[f]]
        if len(chg) != 1: print('칸 %d(%s) 파일 %s: 바뀐 것 %d개 — 건너뜀' % (sl, ours[sl], files, len(chg))); continue
        src_f = chg[0]
        for dst_f in files:
            if dst_f == src_f: continue
            if len(ff[src_f]) != len(ff[dst_f]) or not (HF.is_follow(HF.btx_layout(ff[src_f])) and HF.is_follow(HF.btx_layout(ff[dst_f]))):
                print('경고: 칸 %d 파일 %d → %d 크기·형식이 달라 건너뜀' % (sl, src_f, dst_f)); continue
            ff[dst_f] = bytes(ff[src_f]); fixed.append('칸 %d %s: 파일 %d → %d' % (sl, ours[sl], src_f, dst_f))
    print('따라다니는 그림 정리: %d곳 %s' % (len(fixed), '; '.join(fixed)))
fol.files = ff
out2 = NDS(bytes(out.d)); out2.put('a/0/8/1', fol.build()); out = out2
open(A.out, 'wb').write(bytes(out.d))
print('저장: %s  otherpoke 멤버 %d개 바꿈 (칸 %s)' % (A.out, n, SP))
