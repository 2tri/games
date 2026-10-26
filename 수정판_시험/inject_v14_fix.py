#!/usr/bin/env python3
"""python inject_v14_fix.py <입력 롬> <출력 롬> — 1부 남은 항목 PC 시험(2026-10-26)에서 찾은 것 고침
 ① 「붉은 메가시드라몬」(분노의 호수, 색다른 개체 Lv30)이 전투에서 초록으로 보임: 색다른 팔레트가 일반 색의 RGB 채널만 돌린 것
    → 일반 팔레트의 밝기·채도는 그대로 두고 색조만 붉은 계열(빨강~주홍)로 바꾼 팔레트를 색다른 팔레트(a/0/0/4 의 130×6+5)에 넣음.
 ② 챔피언 방(지도305, 글 522:9·10) 전투 뒤 이름표가 「레오몬:」 — 이 방의 챔피언은 아포카리몬(용어표 「챔피언 목호 → 챔피언 아포카리몬」)
    → 「아포카리몬:」. (다른 장면의 「레오몬:」은 용어표 「목호 → 레오몬」대로라 그대로 둠)
 ③ 대사에 원작 포켓몬 이름이 남은 82줄(편지 「주뱃만큼은」, 울음소리, 교환 대사 5곳이 실제 교환 종과 다름, 삐쭉귀 피츄, 안농노트, 야돈우물 등) → 디지몬 이름(v14_names.py).
여러 번 돌려도 같은 결과."""
import sys, os, struct, csv, colorsys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []

# ========= ① 붉은 메가시드라몬 색다른 팔레트 =========
SP_MEGASEADRAMON = 130
pg = NARC(nds.get(hg1.NARC_PATHS['pokegra'])); pfiles = list(pg.files)
def pal_off(f): return f.find(b'TTLP') + 0x18
def red_pal(normal):
    o = pal_off(normal); out = []
    for j in range(16):
        v = struct.unpack_from('<H', normal, o + 2 * j)[0]
        r, g, b = (v & 31) / 31, ((v >> 5) & 31) / 31, ((v >> 10) & 31) / 31
        h, s, val = colorsys.rgb_to_hsv(r, g, b)
        if j == 0 or s < 0.15:                      # 투명색·회색·흰색·검정은 그대로
            out.append(v); continue
        h2 = (0.97 + h * 0.08) % 1.0               # 원래 색조 차이를 조금 남긴 빨강~주홍(약 349°~18°)
        r2, g2, b2 = colorsys.hsv_to_rgb(h2, max(s, 0.55), val)
        out.append(round(r2 * 31) | round(g2 * 31) << 5 | round(b2 * 31) << 10)
    return out
ni, si = SP_MEGASEADRAMON * 6 + 4, SP_MEGASEADRAMON * 6 + 5
new = red_pal(pfiles[ni]); sh = bytearray(pfiles[si]); o = pal_off(sh)
cur = [struct.unpack_from('<H', sh, o + 2 * j)[0] for j in range(16)]
if cur == new: done.append('이미 고침: 메가시드라몬 색다른 팔레트 붉게')
else:
    for j, v in enumerate(new): struct.pack_into('<H', sh, o + 2 * j, v)
    pfiles[si] = bytes(sh); pg.files = pfiles; nds.put(hg1.NARC_PATHS['pokegra'], pg.build())
    done.append('메가시드라몬 색다른 팔레트 → 붉은 계열 (a/0/0/4 #%d)' % si)

# ========= ② 챔피언 방 이름표 =========
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(H, '..', 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
mfiles = list(mn.files); mdirty = False
OLD, NEW = '레오몬{01C4}', '아포카리몬{01C4}'
seed, ents = MSG[522]; ents = list(ents)
for idx in (9, 10):
    s = CM.dec(ents[idx])
    if s.startswith(NEW): done.append('이미 고침: 글 522:%d 이름표' % idx); continue
    assert s.startswith(OLD) and '소란해졌구나' in s, '글 522:%d 가 예상과 다름: %r' % (idx, s[:40])
    s2 = NEW + s[len(OLD):]; enc = CM.enc(s2); assert CM.dec(enc) == s2, '글 522:%d 검산 실패' % idx
    ents[idx] = enc; mdirty = True; done.append('챔피언 방 이름표 레오몬 → 아포카리몬 (글 522:%d)' % idx)
if mdirty: mfiles[522] = msg_encode(seed, ents); MSG[522] = (seed, ents)

# ========= ③ 원작 포켓몬 이름이 남은 대사 (울음소리·교환·사파리·삐쭉귀 등, v14_names.py) =========
# 교환 대사는 실제 교환 자료(a/1/1/2, 설계표 「교환 자료는 손대지 않음」)의 주는·받는 종으로, 나머지는 NDS_포켓몬대체표.tsv 대로. 조사(은/는 등)도 받침에 맞춤.
import v14_names
SP_ = '{01DE}'
nfix = 0
for bank, idx in sorted(set(v14_names.plan()) | set(v14_names.CRY)):
    seed, ents = MSG[bank]; ents = list(ents)
    cur = CM.dec(ents[idx]).replace(SP_, ' ')
    new = v14_names.fix(bank, idx, cur)
    if new == cur: continue                      # 이미 고침
    new = new.replace(' ', SP_); enc = CM.enc(new); assert CM.dec(enc) == new, '글 %d:%d 검산 실패' % (bank, idx)
    ents[idx] = enc; MSG[bank] = (seed, ents); mfiles[bank] = msg_encode(seed, ents); mdirty = True; nfix += 1
done.append('원작 포켓몬 이름 → 디지몬 이름 %d줄' % nfix if nfix else '이미 고침: 원작 포켓몬 이름')
if mdirty:
    mn.files = mfiles; nds.put(hg1.NARC_PATHS['msg'], mn.build())

open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('v1.4 수정 %d건' % len(done))
