#!/usr/bin/env python3
"""야생 표에서 NDS_귀한종.tsv 규칙을 어긴 칸을 고친 롬을 만든다. 롬은 읽기만 하고 새 파일로 저장. (Claude 작성, 2026-10-14)
사용:   python fix_wild_rare.py <입력 롬.nds> <출력 롬.nds> [--report 보고.txt]
왜:     hg3.wild_pick() 은 유년기 종이 「안 나옴」 일 때 바꿀 후보가 비어 원래 종을 그대로 돌려준다(토코몬 48칸이 야생에 남음).
        설계자가 hg3 를 고치기 전까지의 임시 처방 — 같은 표(구역)에 이미 나오는 종 중 규칙에 맞는 것으로 바꾼다.
규칙:   「안 나옴」 종 → 어디서도 안 나옴 / 「드문 칸」 종 → 풀숲 9~12번·파도타기 4·5번·바위깨기 2번·낚싯대 4·5번 칸에만
        단계 최소 레벨: 성숙기 18 · 아머체 25 · 완전체 30 · 궁극체 50(드문 칸만)   (hg3 와 같음)
고르기: 같은 표에 나오는 종 중 규칙에 맞는 것 — 같은 주 타입 먼저, 단계는 원래 종보다 높지 않게, 많이 나오는 종 먼저."""
import sys, os, csv, struct, argparse, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--report', default=None)
A = ap.parse_args()
ENC_SPECIES = ([0x14 + 2 * k for k in range(12)] + [0x2C + 2 * k for k in range(12)] + [0x44 + 2 * k for k in range(12)] +
               [0x5C, 0x5E, 0x60, 0x62] + [0x64 + 4 * k + 2 for k in range(5)] + [0x78 + 4 * k + 2 for k in range(2)] +
               [0x80 + 4 * k + 2 for k in range(5)] + [0x94 + 4 * k + 2 for k in range(5)] + [0xA8 + 4 * k + 2 for k in range(5)] +
               [0xBC + 2 * k for k in range(4)])
WILD_MIN = {'성숙기': 18, '아머체': 25, '완전체': 30, '궁극체': 50}
RANK = {'유년기Ⅱ': 0, '유년기': 0, '성장기': 1, '성숙기': 2, '아머체': 2, '완전체': 3, '궁극체': 4}
def is_rare_slot(off):
    if off < 0x5C: return ((off - 0x14) // 2) % 12 >= 8
    if 0x64 <= off < 0x78: return (off - 0x66) // 4 >= 3
    if 0x78 <= off < 0x80: return (off - 0x7A) // 4 >= 1
    if 0x80 <= off < 0xBC: return ((off - 0x82) // 4) % 5 >= 3
    return False

draft = list(csv.DictReader(open(os.path.join(PROJ, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t'))
grade = {r['이름']: r['단계'] for r in draft}
ptype = {r['이름']: (r['타입'].split('/')[0] if r.get('타입') else '') for r in draft}
rare = [l.rstrip('\n').split('\t') for l in open(os.path.join(PROJ, 'NDS_귀한종.tsv'), encoding='utf-8') if not l.startswith('#')][1:]
NEVER = {r[0] for r in rare if len(r) > 1 and r[1].strip() == '안 나옴'}
RARE_ONLY = {r[0] for r in rare if len(r) > 1 and r[1].strip() == '드문 칸'}

# 그림이 있는 종만 후보로(새 그림이 없는 칸은 원래 포켓몬 그림이 남아 있음 — 가지몬=강철톤 등)
import re
HAS_ART = {r['이름'] for r in draft if r['출처'] == '디지골드'}
_na = os.path.join(PROJ, 'nds_art')
if os.path.isdir(_na):
    for dn in os.listdir(_na):
        m = re.match(r'\d+_(.+)$', dn)
        if m and os.path.exists(os.path.join(_na, dn, 'front.png')): HAS_ART.add(m.group(1))
rom = NDS(open(A.rom, 'rb').read())
MSG = []
for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
    try: MSG.append(hg1.msg_decode(f))
    except Exception: MSG.append((0, []))
CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
names = [CM.dec(e) for e in MSG[NAMEF][1]]
nar = NARC(rom.get('a/0/3/7')); files = list(nar.files)

def allowed(n, lv, rare_slot):
    if n in NEVER: return False
    g = grade.get(n, '')
    if lv < WILD_MIN.get(g, 0): return False
    if (n in RARE_ONLY or g == '궁극체') and not rare_slot: return False
    return True

log = []; changed = 0; unfixed = []
for z, d in enumerate(files):
    if len(d) < 0xC4 or d[0] == 0: continue
    b = bytearray(d); walk = list(b[8:20]) or [5]
    here = collections.Counter()
    for off in ENC_SPECIES:
        s = struct.unpack_from('<H', b, off)[0]
        if 0 < s < len(names): here[names[s]] += 1
    for off in ENC_SPECIES:
        s = struct.unpack_from('<H', b, off)[0]
        if not (0 < s < len(names)): continue
        n = names[s]
        if n not in NEVER and n not in RARE_ONLY: continue
        if off < 0x5C: lv = walk[((off - 0x14) // 2) % 12]
        elif off < 0x64 or off >= 0xBC: lv = min(walk)
        else: lv = b[off - 1]
        rs = is_rare_slot(off)
        if allowed(n, lv, rs): continue
        og = RANK.get(grade.get(n, ''), 1)
        cand = [c for c in here if c != n and c in HAS_ART and allowed(c, lv, rs) and c in grade and RANK.get(grade[c], 9) <= max(og, 1)]
        if not cand:
            cand = [c for c in here if c != n and c in HAS_ART and allowed(c, lv, rs) and c in grade]
        if not cand: unfixed.append((z, off, n, lv)); continue
        cand.sort(key=lambda c: (ptype.get(c, '') != ptype.get(n, ''), -here[c], c))
        new = cand[0]; idx = names.index(new)
        struct.pack_into('<H', b, off, idx); changed += 1
        log.append('%d\t0x%02X\tLv%d\t%s\t%s' % (z, off, lv, n, new))
    files[z] = bytes(b)
nar.files = files
print('바꾼 칸 %d, 못 바꾼 칸 %d, 쓰기: %s' % (changed, len(unfixed), rom.put('a/0/3/7', nar.build())))
open(A.out, 'wb').write(bytes(rom.d))
if A.report:
    open(A.report, 'w', encoding='utf-8').write('바꾼 칸 %d, 못 바꾼 칸 %d\n구역\t자리\t레벨\t바꾸기 전\t바꾼 뒤\n' % (changed, len(unfixed)) + '\n'.join(log) + '\n' +
                                               ('\n못 바꾼 칸: %s\n' % unfixed if unfixed else ''))
    print('목록 →', A.report)
