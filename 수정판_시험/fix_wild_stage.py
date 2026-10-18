#!/usr/bin/env python3
"""야생(걷기) 표에 「단계 ↔ 레벨」 규칙을 적용한 시험 롬을 만든다. 롬 파일은 읽기만 하고 새 파일로 저장한다. (Claude 작성, 2026-10-13)
사용:   python fix_wild_stage.py <입력 롬.nds> <출력 롬.nds> [--min 성숙기=15 완전체=30 궁극체=50] [--report 보고.txt]
규칙:   칸의 디지몬 단계가 그 칸 레벨의 기준보다 높으면
        1) 그 디지몬으로 진화해 오는 하위 단계(롬의 진화표 a/0/3/4 거꾸로)로 바꾼다 — 그것도 어긋나면 한 단계 더 내려간다
        2) 진화 앞단계가 없으면 같은 주 타입의 성장기 중 초반 풀숲에 이미 나오는 종으로 바꾼다
기준 레벨(제안): 성숙기 15↑ · 완전체 30↑ · 궁극체 50↑   (사용자 방침: 초반은 유년기·성장기, 뒤로 갈수록 성숙기)"""
import sys, os, csv, struct, argparse, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
import hg1
from hg1 import NDS, NARC

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--report', default=None)
ap.add_argument('--min', nargs='*', default=['성숙기=15', '완전체=30', '궁극체=50'])
ap.add_argument('--skip', nargs='*', default=['궁극체'], help='손대지 않을 단계(전설급 — 사신수 등)')
A = ap.parse_args()
MIN = {k: int(v) for k, v in (x.split('=') for x in A.min)}
RANK = {'유년기Ⅰ': 0, '유년기Ⅱ': 1, '아머체': 2, '성장기': 2, '성숙기': 3, '완전체': 4, '궁극체': 5}
def too_high(st, lv): return st in MIN and st not in A.skip and lv < MIN[st]

draft = list(csv.DictReader(open(os.path.join(PROJ, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t'))
stage = {r['이름']: r['단계'] for r in draft}
ptype = {r['이름']: (r['타입'].split('/')[0] if r.get('타입') else '') for r in draft}

rom = NDS(open(A.rom, 'rb').read())
MSG = []
for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
    try: MSG.append(hg1.msg_decode(f))
    except Exception: MSG.append((0, []))
CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
names = [CM.dec(e) for e in MSG[NAMEF][1]]
idx = {}
for i, n in enumerate(names): idx.setdefault(n, i)

# 진화표(롬): 칸마다 7 x (방법 u16, 값 u16, 대상 u16) + 2바이트
evo = NARC(rom.get(hg1.NARC_PATHS['evo'])).files
pre = collections.defaultdict(list)
for s, f in enumerate(evo):
    if len(f) < 42: continue
    for k in range(7):
        m, p, t = struct.unpack_from('<HHH', f, k * 6)
        if m and 0 < t < len(names) and t != s: pre[t].append(s)

nar = NARC(rom.get('a/0/3/7')); files = list(nar.files)
def st_of(s): return stage.get(names[s]) if s < len(names) else None

# 초반(최대 레벨 ≤ 12) 풀숲에 이미 나오는 성장기 — 대체 후보 풀
early = collections.Counter()
for z, f in enumerate(files):
    if len(f) < 92 or f[0] == 0: continue
    if max(f[8:20]) > 12: continue
    for off in (20, 44, 68):
        for s in struct.unpack_from('<12H', f, off):
            if st_of(s) == '성장기': early[s] += 1

def lower(s, lv, seen=()):
    """s 보다 낮은 단계 대체 종(기준 만족) 또는 None"""
    for p in pre.get(s, []):
        if p in seen: continue
        st = st_of(p)
        if st is None: continue
        if not too_high(st, lv) and RANK.get(st, 9) < RANK.get(st_of(s), 9): return p
        q = lower(p, lv, seen + (s,))
        if q is not None: return q
    return None

def fallback(s, lv, used):
    ty = ptype.get(names[s], '')
    ok = [c for c, _ in early.most_common() if not too_high(st_of(c), lv)]
    for pool in ([c for c in ok if ptype.get(names[c], '') == ty and c not in used], [c for c in ok if c not in used],
                 [c for c in ok if ptype.get(names[c], '') == ty], ok):
        if pool: return pool[0]
    return None

report = ['구역\t칸\t때\t레벨\t바꾸기 전\t(단계)\t바꾼 뒤\t(단계)\t방법']
changed = 0; keep = 0; by_how = collections.Counter()
for z, f in enumerate(files):
    if len(f) < 92 or f[0] == 0: continue
    lv = list(f[8:20]); b = bytearray(f); touched = False
    used = set()                                   # 이 구역 표에 이미 있는 종(다양하게 고르려고)
    for off in (20, 44, 68): used |= set(struct.unpack_from('<12H', f, off))
    for t, off in (('아침', 20), ('낮', 44), ('밤', 68)):
        sp = list(struct.unpack_from('<12H', b, off))
        for i, s in enumerate(sp):
            st = st_of(s)
            if not too_high(st, lv[i]): continue
            n = lower(s, lv[i]); how = '진화 앞단계'
            if n is None: n = fallback(s, lv[i], used); how = '같은 타입 성장기'
            if n is None or n == s: keep += 1; continue
            sp[i] = n; used.add(n); changed += 1; touched = True; by_how[how] += 1
            report.append('%d\t%d\t%s\tLv%d\t%s\t%s\t%s\t%s\t%s' % (z, i, t, lv[i], names[s], st, names[n], st_of(n), how))
        struct.pack_into('<12H', b, off, *sp)
    if touched: files[z] = bytes(b)

nar.files = files
how = rom.put('a/0/3/7', nar.build())
open(A.out, 'wb').write(bytes(rom.d))
head = '바꾼 칸 %d (%s), 못 바꾼 칸 %d, 기준 %s → %s (쓰기: %s)' % (changed, dict(by_how), keep, MIN, A.out, how)
print(head)
if A.report:
    open(A.report, 'w', encoding='utf-8').write(head + '\n' + '\n'.join(report) + '\n')
    print('목록 →', A.report)
