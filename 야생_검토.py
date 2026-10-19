#!/usr/bin/env python3
r"""적재적소 점검 (2026-10-16, 사용자 완성 조건 4 「각 디지몬이 맞는 곳에 나오기」) — 최종 롬의 야생 표를 장소 이름으로 펼치고 이상한 곳을 자동으로 찾는다.
사용:   python 야생_검토.py 최종_오늘.nds          (같은 폴더에 hg2_out/칸표.tsv · 야생_지명.tsv · NDS_종_초안.tsv · NDS_진화.tsv · NDS_이벤트표.tsv)
결과:   야생_장소별.md  — 장소마다 아침·낮·밤 걷기 / 파도타기 / 낚시 / 바위깨기 칸의 디지몬·레벨·확률 + 그 장소의 경고
        야생_종별.md    — 디지몬마다 처음 만나는 곳·레벨, 얻는 길(야생·이벤트·진화), 얻을 길이 없는 종(도감 완성 막힘)
경고 종류: [단계] 레벨에 비해 높은 단계(맨 끝 1% 칸의 「강한 드문 종」은 일부러라 뺌) · [낮은단계] Lv25↑ 인데 진화 전 · [1부] 성도에 「1부 안 나옴」 종 · [물] 파도타기·낚시에 물 타입이 아닌 종 · [반복] 한 표에 같은 종이 너무 많음
읽는 법: 경고는 「고칠 후보」일 뿐이다. 사용자와 같이 보고 NDS_귀한종.tsv(규칙)·NDS_대체표 등을 고친 뒤 롬을 다시 만든다."""
import os, sys, csv, struct, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import hg1
from hg1 import NDS, NARC
P = H if os.path.exists(os.path.join(H, 'NDS_종_초안.tsv')) else os.path.join(H, '..')

# 하트골드 지명 번호(맵 머리말 +0x12, pret map_sections.h) → 한국어판 지명
KR = {126: '연두마을', 127: '무궁시티', 128: '도라지시티', 129: '고동마을', 130: '진청시티', 131: '금빛시티', 132: '담청시티', 133: '인주시티', 134: '황토마을', 135: '분노의 호수',
      136: '검은먹시티', 137: '은빛산', 138: '태초마을', 139: '상록시티', 140: '회색시티', 141: '블루시티', 142: '보라타운', 143: '갈색시티', 144: '무지개시티', 145: '연분홍시티',
      146: '홍련마을', 147: '석영고원', 148: '노랑시티', 197: '디그다의 굴', 198: '달맞이산', 199: '블루시티 동굴', 200: '돌산터널', 201: '무인발전소', 202: '사파리존',
      203: '쌍둥이섬', 204: '모다피의 탑', 205: '방울탑', 206: '불탄탑', 207: '자연공원', 208: '라디오타워', 209: '알프의 유적', 210: '연결동굴', 211: '야돈의 우물', 212: '등대',
      213: '로켓단 아지트', 214: '너도밤나무 숲', 215: '금빛 지하통로', 216: '절구산', 217: '얼음샛길', 218: '소용돌이섬', 219: '은빛산 동굴', 220: '어둠의 동굴', 221: '챔피언로드',
      222: '용의 굴', 223: '동성폭포', 224: '상록숲', 226: '아쿠아호', 228: '절벽동굴', 230: '방울 소리 오솔길', 231: '신오 유적', 232: '매몰탑'}
for k in range(149, 197): KR[k] = '%d번도로' % (k - 148)
WALK_RATE = [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]
WILD_MIN = {'성숙기': 18, '아머체': 25, '완전체': 30, '궁극체': 50}
RANK = {'유년기Ⅱ': 0, '유년기': 0, '성장기': 1, '성숙기': 2, '아머체': 2, '완전체': 3, '궁극체': 4}
def rank_for(lv): return 1 if lv < 25 else 2 if lv < 38 else 3          # hg3 와 같은 기준(10/16 저녁)

def tsv(name):
    for q in (os.path.join(P, name), name):
        if os.path.exists(q): return [r for r in csv.DictReader((l for l in open(q, encoding='utf-8') if not l.startswith('#')), delimiter='\t')]
    return []

def main():
    rom = NDS(open(sys.argv[1], 'rb').read())
    terms = {r['옛']: r['새'] for r in tsv('NDS_용어표.tsv') if r.get('옛') and r.get('새')}
    def place(sec):
        nm = KR.get(sec, '지명 %s' % sec)
        return terms.get(nm, terms.get(nm.replace(' ', ''), nm)) + ('' if terms.get(nm, nm) == nm else '(원래 %s)' % nm)
    kan = {}
    for q in ('hg2_out/칸표.tsv', os.path.join(P, 'hg2_out', '칸표.tsv')):
        if os.path.exists(q):
            for l in open(q, encoding='utf-8').read().split('\n')[1:]:
                r = l.split('\t')
                if len(r) >= 2 and r[1].isdigit(): kan[int(r[1])] = r[0]
            break
    if not kan: sys.exit('실패: hg2_out/칸표.tsv 가 없음 — hg2 를 돌린 폴더에서 실행')
    draft = {r['이름']: r for r in tsv('NDS_종_초안.tsv')}
    rare = {r['이름']: r.get('규칙', '').strip() for r in tsv('NDS_귀한종.tsv')}
    region = {}; sec_of = {}
    for r in tsv('야생_지명.tsv'):
        k = (r.get('파일 번호') or '').strip()
        if k.isdigit():
            region[int(k)] = (r.get('지역') or '').strip()
            num = ''.join(ch for ch in (r.get('지명') or '') if ch.isdigit())
            if num: sec_of[int(k)] = int(num)
    enc = NARC(rom.get(hg1.NARC_PATHS['enc'])).files
    nm = lambda s: kan.get(s, '칸%d(우리 종 아님)' % s)
    grade = lambda n: draft.get(n, {}).get('단계', '')
    types = lambda n: draft.get(n, {}).get('타입', '')
    L = ['# 야생 장소별 (최종 롬에서 자동, 야생_검토.py)', '', '> 칸 = 디지몬 Lv(확률). 경고는 고칠 후보 — 사용자와 같이 본다.', '']
    first = {}; warn_n = collections.Counter(); info_n = collections.Counter()
    evo_to = collections.defaultdict(set)
    for e in tsv('NDS_진화.tsv'): evo_to[e['출발']].add(e['도착'])
    def can_grow(n_, reg):            # 야생에 내보낼 수 있는 진화형이 있나(진화형이 「안 나옴」·성도의 「1부 안 나옴」이거나, 자기가 「드문 칸」 파트너면 규칙대로라 경고 아님)
        if rare.get(n_) == '드문 칸': return False
        return any(rare.get(t) not in ('안 나옴', '드문 칸') and not (rare.get(t) == '1부 안 나옴' and reg == '성도') and grade(t) != '궁극체' for t in evo_to.get(n_, ()))   # 궁극체는 드문 칸 전용이라 보통 칸은 진화 전이 맞음
    for i, d in enumerate(enc):
        if len(d) != 0xC4 or not any(d[0:6]): continue
        sec = sec_of.get(i); reg = region.get(i, '?')
        title = '%s — 야생 파일 %d (%s)' % (place(sec) if sec else '지명 모름', i, reg)
        lv = list(d[8:20]); W = []
        rows = []
        for tname, base in (('아침', 0x14), ('낮', 0x2C), ('밤', 0x44)):
            if not d[0]: break
            cnt = collections.Counter(); lvs = collections.defaultdict(list)
            for k in range(12):
                s = struct.unpack_from('<H', d, base + 2 * k)[0]
                if s: cnt[s] += WALK_RATE[k]; lvs[s].append(lv[k])
            rows.append('- 걷기 %s: %s' % (tname, ', '.join('%s Lv%d~%d(%d%%)' % (nm(s), min(lvs[s]), max(lvs[s]), c) for s, c in cnt.most_common())))
            for s in cnt:
                n_ = nm(s); g = grade(n_); mlv = min(lvs[s])
                first.setdefault(n_, []).append((mlv, title))
                ks = [k for k in range(12) if struct.unpack_from('<H', d, base + 2 * k)[0] == s]
                if mlv < WILD_MIN.get(g, 0):
                    if all(k >= 10 for k in ks) and RANK.get(g, 9) <= rank_for(mlv) + 1: info_n['[강한 드문 1%%] %s Lv%d' % (n_, mlv)] += 1      # 사용자 10/16: 낮은 확률로 강한 종(일부러)
                    else: W.append('[단계] %s(%s) Lv%d — %s 는 Lv%d 이상' % (n_, tname, mlv, g, WILD_MIN[g]))
                if RANK.get(g, 9) < rank_for(min(lvs[s])) and can_grow(n_, reg) and min(lvs[s]) >= 25 and not all(k >= 10 for k in ks): W.append('[낮은단계] %s(%s) Lv%d — 레벨에 비해 진화 전' % (n_, tname, min(lvs[s])))
                if reg == '성도' and rare.get(n_) == '1부 안 나옴': W.append('[1부] %s — 성도에 「1부 안 나옴」 종' % n_)
                if cnt[s] >= 60: W.append('[반복] %s(%s) %d%%' % (n_, tname, cnt[s]))
        for wname, base, nslot, rate_i in (('파도타기', 0x64, 5, 1), ('바위깨기', 0x78, 2, 2), ('헌 낚싯대', 0x80, 5, 3), ('좋은 낚싯대', 0x94, 5, 4), ('대단한 낚싯대', 0xA8, 5, 5)):
            if not d[rate_i]: continue
            items = []
            for k in range(nslot):
                lo, hi, s = d[base + 4 * k], d[base + 4 * k + 1], struct.unpack_from('<H', d, base + 4 * k + 2)[0]
                if not s: continue
                n_ = nm(s); items.append('%s Lv%d~%d' % (n_, lo, hi)); first.setdefault(n_, []).append((lo, title + ' ' + wname))
                if wname != '바위깨기' and '물' not in types(n_).split('/'): W.append('[물] %s(%s) — 물 타입이 아님' % (n_, wname))
                if lo < WILD_MIN.get(grade(n_), 0):
                    if k == 4 and RANK.get(grade(n_), 9) <= rank_for(lo) + 1: info_n['[강한 드문 1%%] %s Lv%d' % (n_, lo)] += 1
                    else: W.append('[단계] %s(%s) Lv%d' % (n_, wname, lo))
            if items: rows.append('- %s: %s' % (wname, ', '.join(items)))
        L += ['## ' + title, ''] + rows
        if W:
            L += ['', '**경고 %d**: ' % len(W) + ' / '.join(sorted(set(W)))]
            for w in set(W): warn_n[w.split(']')[0] + ']'] += 1
        L.append('')
    L.insert(3, '> 경고 합계: %s' % (', '.join('%s %d' % kv for kv in warn_n.most_common()) or '없음'))
    L.insert(4, '> 일부러 넣은 「낮은 확률 강한 종」(1%% 칸): %d칸 — 경고 아님' % sum(info_n.values()))
    open('야생_장소별.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    # ---- 종별: 처음 만나는 곳 + 얻는 길
    ev_sp = {}
    for r in tsv('NDS_이벤트표.tsv'):
        o = (r.get('우리 종') or '').strip()
        if o and not o.startswith('(') and r.get('종류', '').strip() in ('스타팅', '알', '선물', '교환', '고정', '떠돌이', '추적', '심볼'):
            ev_sp.setdefault(o, []).append('%s %s Lv%s' % (r['종류'], r.get('장소', ''), r.get('Lv', '') or '?'))
    evo = tsv('NDS_진화.tsv'); nxt = collections.defaultdict(list)
    for e in evo: nxt[e['출발']].append((e['도착'], e['방법'], e['값']))
    got = set(first) | set(ev_sp); todo = list(got); how = {n_: '야생' if n_ in first else '이벤트' for n_ in got}
    while todo:
        a = todo.pop()
        for b, m, v in nxt.get(a, []):
            if b not in got: got.add(b); todo.append(b); how[b] = '진화(%s %s %s)' % (a, m, v)
    L2 = ['# 디지몬별 얻는 길 (최종 롬 야생 + 이벤트표 + 진화표)', '', '| 디지몬 | 단계 | 처음 야생 | 이벤트 | 얻는 길 |', '|---|---|---|---|---|']
    for n_ in draft:
        f = min(first.get(n_, [(999, '')]))
        L2.append('| %s | %s | %s | %s | %s |' % (n_, grade(n_), ('Lv%d %s' % f) if f[0] < 999 else '-', '; '.join(ev_sp.get(n_, [])) or '-', how.get(n_, '**얻을 길 없음**')))
    no = [n_ for n_ in draft if n_ not in got]
    L2.insert(2, '> 얻을 길 없는 종 %d: %s' % (len(no), ' '.join(no) or '없음'))
    open('야생_종별.md', 'w', encoding='utf-8').write('\n'.join(L2) + '\n')
    print('→ 야생_장소별.md (경고 %s) · 야생_종별.md (얻을 길 없는 종 %d: %s)' % (dict(warn_n), len(no), ' '.join(no[:20])))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
