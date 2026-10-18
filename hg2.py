#!/usr/bin/env python3
"""HG2 — 새 디지몬 127종의 자료(이름·타입·능력치·특성·포획률·기술·진화)를 디지골드 롬에 쓴다. (2026-10-08 작성, 가짜 롬으로만 시험함)
사용:   python hg2.py "<디지골드 롬.nds>"            (hg1.py 와 같은 폴더에 둔다)
결과:   hg2_out/hg2_test.nds (폰 시험용), hg2_out/hg2.bps (원본 디지골드 롬에 적용하는 패치), hg2_out/report.txt
원칙
- 원본 롬은 읽기만 한다.
- 기술·특성·도구·종 번호는 롬 안의 이름표에서 「이름」으로 찾는다(번호를 미리 알 필요 없음). 못 찾은 이름은 report.txt 에 적고 건너뛴다.
- 디지골드 65종은 건드리지 않는다. 설계에만 있는 「어둠의돌·돌 사용」 갈래만 빈 진화 칸에 더한다.
- 새 종의 나머지 값(성별 없음·알 그룹·학습 머신 등)은 「본뜬 종」(초안 메모의 기술 본보기)의 값을 복사한 뒤 덮어쓴다.
- 쓰고 나서 롬을 다시 읽어 종마다 이름·타입·능력치·기술 수·진화 대상을 대조한다(자체 검산)."""
import os, sys, re, csv, io, zlib, base64, struct, argparse, collections, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode, bps_make, bps_apply, say, R

TYPES = ['노말', '격투', '비행', '독', '땅', '바위', '벌레', '고스트', '강철', '페어리', '불꽃', '물', '풀', '전기', '에스퍼', '얼음', '드래곤', '악']
CATCH = {'유년기Ⅰ': 255, '유년기Ⅱ': 255, '유년기': 255, '성장기': 190, '성숙기': 90, '아머체': 90, '완전체': 30, '궁극체': 0}
CATCH_NAME = {'청룡몬': 5, '퍼펫몬': 30, '백호몬': 0, '주작몬': 0, '현무몬': 0, '키메라몬': 0, '아포카리몬': 0}
BASE_EXP = {'유년기Ⅰ': 50, '유년기Ⅱ': 50, '유년기': 50, '성장기': 70, '성숙기': 150, '아머체': 170, '완전체': 200, '궁극체': 250}   # 1바이트(255 까지)
EGG_AMORPHOUS, EGG_NONE = 11, 15
PARTNER = {'코로몬', '아구몬', '그레이몬', '메탈그레이몬', '워그레이몬', '뿔몬', '파피몬', '가루몬', '워가루몬', '메탈가루몬', '어니몬', '피요몬', '버드라몬', '가루다몬',
           '모티몬', '텐타몬', '캅테리몬', '아트라캅테리몬', '시드몬', '팔몬', '니드몬', '릴리몬', '로제몬', '둥실몬', '쉬라몬', '원뿔몬', '쥬드몬', '토코몬', '파닥몬',
           '엔젤몬', '홀리엔젤몬', '세라피몬', '야옹몬', '플롯트몬', '가트몬', '엔젤우몬', '마그나드몬'}
EVO_LEVEL, EVO_ITEM, EVO_FRIEND = 4, 7, 1
HELD_CLEAR = {'피코데블몬', '가트몬', '파닥몬', '토코몬'}   # 진화표 결정3(어둠의돌)·결정5(빛의돌·각성의돌 등) — 지닌 물건 없앰
DONOR_FIX = {'메가강철톤': '강철톤', '메가핫삼': '핫삼', '메가입치트': '입치트', '메가메타그로스': '메타그로스', '아트라캅테리몬': '아트라캅테몬'}   # 집 보고 10/12: 롬에 없는 이름
MOVE_ALT = {'에어커터': '에어컷터', '머드샷': '진흙뿌리기', '록블라스트': '암석봉인', '매지컬리프': '메지컬리프', '날개치기': '더블윙'}   # 롬에 없는 기술 이름 → 비슷한 기술
RENAME = {'아라크네몬': '아르케니몬', '데스메라몬': '데드메라몬', '벨리얼묘티': '벨리얼묘티스몬'}   # 02 더빙명·결정7·GBC 글자 수 제한으로 줄였던 이름
NL_TOKEN = chr(92) + 'n'          # 글 안의 줄바꿈(Charmap 이 0xE000 을 이렇게 풂)
# 디지골드가 디지몬을 넣은 자리(엑셀 「수정 전 포켓몬」) → 전국도감 번호. 이 번호로 칸을 찾고, 이름은 검산에만 쓴다.
REPLACED_DEX = {'토게피': 175, '나무지기': 252, '나무돌이': 253, '나무킹': 254, '아차모': 255, '영치코': 256, '번치코': 257, '물짱이': 258, '늪짱이': 259,
    '대짱이': 260, '포챠나': 261, '그라에나': 262, '지그제구리': 263, '직구리': 264, '개무소': 265, '실쿤': 266, '뷰티플라이': 267, '카스쿤': 268, '독케일': 269,
    '연꽃몬': 270, '로토스': 271, '로파파': 272, '도토링': 273, '잎새코': 274, '다탱구': 275, '테일로': 276, '스왈로': 277, '갈모매': 278, '패리퍼': 279,
    '비구술': 283, '비나방': 284, '버섯꼬': 285, '버섯모': 286, '게을로': 287, '발바로': 288, '게을킹': 289, '토중몬': 290, '아이스크': 291, '소곤룡': 293,
    '노공룡': 294, '폭음룡': 295, '마크탕': 296, '하리뭉': 297, '코코파스': 299, '에나비': 300, '델케티': 301, '깜까미': 302, '가보리': 304, '갱도라': 305,
    '보스로라': 306, '요가랑': 307, '요가램': 308, '썬더라이': 309, '썬더볼트': 310, '플러시': 311, '마이농': 312, '볼비트': 313, '네오비트': 314,
    '로젤리아': 315, '고래왕': 321, '가이오가': 382, '그란돈': 383, '레쿠쟈': 384, '레지기가스': 486, '크레세리아': 488}

ITEM_ID = {'심해의이빨': 226, '심해의비늘': 227, '행복의알': 231, '마음의물방울': 135, '동글동글돌': 110, '불꽃의돌': 82, '천둥의돌': 83, '태양의돌': 80, '리프의돌': 85, '각성의돌': 109, '달의돌': 81, '물의돌': 84, '빛의돌': 107, '어둠의돌': 108, '예리한손톱': 326}   # 4세대 도구 번호(pret items.h, 10/15)

def skel(n):
    """이름에서 한글만 남김(괄호·숫자·영어처럼 아직 글자표에 없는 부분은 {XXXX} 로 풀리므로)"""
    return ''.join(ch for ch in re.sub(r'\{[0-9A-F]{4}\}', '', n or '') if '가' <= ch <= '힣')

def load_draft(path):
    if path: text = open(path, encoding='utf-8').read()
    else:
        if '@@' in DRAFT_B64:   # 묶음판: 같은 폴더의 NDS_종_초안.tsv
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv')
            if not os.path.exists(p): raise SystemExit('실패: NDS_종_초안.tsv 가 같은 폴더에 없음')
            text = open(p, encoding='utf-8').read()
        else: text = zlib.decompress(base64.b64decode(''.join(DRAFT_B64.split()))).decode('utf-8')
    rows = list(csv.reader(io.StringIO(text), delimiter='\t'))
    head, rows = rows[0], rows[1:]
    return [dict(zip(head, r)) for r in rows]

def find_table(MSG, CM, must, size=None):
    """must 의 낱말이 다 들어 있는 글 파일 → (번호, 이름 목록)"""
    best = None
    for fi, (_, ent) in enumerate(MSG):
        if not ent or (size and not (size[0] <= len(ent) <= size[1])): continue
        names = [CM.dec(e) for e in ent]
        sset = set(names); hit = sum(1 for m in must if m in sset)
        if hit == len(must) and (best is None or len(names) < len(best[1])): best = (fi, names)
    return best

def stats_hgss(st):
    """초안 「HP 공 방 특공 특방 스피드」 → 하트골드 순서 HP 공 방 스피드 특공 특방"""
    hp, at, df, sa, sd, sp = [int(x) for x in st.split()]
    return [hp, at, df, sp, sa, sd]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('--out', default='hg2_out'); ap.add_argument('--draft', default=None)
    ap.add_argument('--unfreeze', action='store_true', help='칸 고정 표와 달라도 진행(세이브 깨짐)'); ap.add_argument('--no-specials', action='store_true')
    ap.add_argument('--specials-mode', choices=('reuse', 'free'), default='free', help='필살기 칸: free = 아무도 안 쓰는 칸만(10/16 저녁부터 기본 — 드물게 쓰던 기술은 종 초안 표에서 이미 정리해 기술표와 롬이 같음), reuse = 남은 1~2종 기술도 롬에서 바꿔 칸을 더 비움(칸이 모자랄 때만)')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== HG2 — 롬', rom.code, '크기 %.1fMB' % (len(raw) / 1048576))
    draft = load_draft(A.draft)
    fz = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_칸_고정.tsv')   # 10/14 세이브 유지: 이름→칸 고정 표
    if os.path.exists(fz) and '--unfreeze' not in sys.argv:
        fixed = {r['이름']: r['칸'] for r in csv.DictReader((l for l in open(fz, encoding='utf-8') if not l.startswith('#')), delimiter=chr(9))}
        now = {r['이름']: r['NDS 칸'] for r in draft if r['NDS 칸'].isdigit()}
        moved = [(k, fixed[k], now[k]) for k in fixed if k in now and now[k] != fixed[k]]
        taken = [(k, now[k]) for k in now if k not in fixed and now[k] in set(fixed.values())]
        if moved or taken: raise SystemExit('실패: 칸 고정 표(NDS_칸_고정.tsv)와 다름 — 세이브가 깨진다. 옮긴 종 %s, 남의 고정 칸을 쓴 종 %s (정말 바꾸려면 --unfreeze)' % (moved[:10], taken[:10]))
    N = {k: NARC(rom.get(hg1.NARC_PATHS[k])) for k in ('personal', 'learn', 'evo', 'msg')}
    MSG = []
    for f in N['msg'].files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append((0, []))        # 못 푸는 글 파일은 건드리지 않음
    res = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
    if not res: raise SystemExit('실패: 글자표를 못 찾음')
    CM, NAMEF, _ = res
    sp_ = hg1.detect_space(MSG, CM)
    xp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_글자표_추가.tsv')   # 월요일 HG1 결과로 채울 문장부호 표
    if os.path.exists(xp):
        for r in csv.DictReader(open(xp, encoding='utf-8'), delimiter=chr(9)):
            try:
                c = int(r['부호'], 16); g = hg1.glyph(r.get('글자'))
                if g is None: continue
                CM.extra[c] = g; CM.rev[g] = c
            except Exception: pass
    NAMES = [CM.dec(e) for e in MSG[NAMEF][1]]
    say('글자표', CM.mode, '0x%04X' % CM.base, '종 이름 파일 msg', NAMEF, '항목', len(NAMES))
    mv = find_table(MSG, CM, ['몸통박치기', '할퀴기'], (400, 600)) or find_table(MSG, CM, ['태클', '클로어택'], (400, 600))   # 10/16: 이미 한 번 고친 롬(기술 이름 바뀜)에도
    ab = find_table(MSG, CM, ['맹화', '급류', '심록'], (100, 200))
    it = find_table(MSG, CM, ['몬스터볼', '어둠의돌'], (400, 700)) or find_table(MSG, CM, ['디지볼', '어둠의돌'], (400, 700))
    for nm, t in (('기술', mv), ('특성', ab), ('도구', it)):
        if not t: raise SystemExit('실패: %s 이름표를 못 찾음' % nm)
        say('%s 이름표 msg %d (%d개)' % (nm, t[0], len(t[1])))
    def lookup(names):
        d = {}; sk = collections.defaultdict(list)
        for i, n in enumerate(names):
            if n and n not in d: d[n] = i
            if skel(n): sk[skel(n)].append(i)
        for k, v in sk.items():
            if len(v) == 1 and k not in d: d[k] = v[0]
        return d
    MOVE, ABIL, ITEM = lookup(mv[1]), lookup(ab[1]), lookup(it[1])
    def mid(nm):
        r = MOVE.get(nm, MOVE.get(skel(nm)))
        if r is None and nm in MOVE_ALT: r = MOVE.get(MOVE_ALT[nm], MOVE.get(skel(MOVE_ALT[nm])))
        return r
    first_idx = {}
    for i, n in enumerate(NAMES):
        for k in (n, skel(n)):
            if k and k not in first_idx: first_idx[k] = i
    problems = []
    def P(*a): problems.append(' '.join(str(x) for x in a))

    # ---- 우리 이름 → 칸
    slot = {}
    for r in draft:
        nds = r['NDS 칸']
        if nds.isdigit(): slot[r['이름']] = int(nds)
        else:
            m = re.search(r'디지골드 「(.+?)」 그대로', r['메모']); g = m.group(1) if m else r['이름']
            mm = re.search(r'디지골드 칸: (\S+)', r['메모']); rep = mm.group(1) if mm else None
            if rep in REPLACED_DEX:
                n = REPLACED_DEX[rep]; slot[r['이름']] = n
                if n < len(NAMES) and skel(NAMES[n]) != skel(g): P('이름 대조 다름(칸 %d): 롬 「%s」 / 엑셀 「%s」' % (n, NAMES[n], g))
            elif skel(g) in first_idx: slot[r['이름']] = first_idx[skel(g)]; P('덮은 포켓몬 번호를 몰라 이름으로 찾음:', r['이름'], first_idx[skel(g)])
            else: P('디지골드 종을 롬에서 못 찾음:', r['이름'], '(디지골드 이름 %s)' % g)
    say('칸이 정해진 종 %d / %d' % (len(slot), len(draft)))
    clash = [k for k, v in collections.Counter(slot.values()).items() if v > 1]
    if clash: P('칸 겹침:', clash)

    NEW = {r['이름'] for r in draft if r['출처'] == '새로'} | {'블랙워그레이몬'}
    NEXT = collections.defaultdict(set)    # 새 종 → 그 종이 진화하는 칸들
    for r in draft:
        if r['이름'] in NEW:
            for part in r['진화'].split(';'):
                mm = re.match(r'\s*(\S+)\(', part)
                if mm and mm.group(1) in slot: NEXT[r['이름']].add(slot[mm.group(1)])
    pers = list(N['personal'].files); learn = list(N['learn'].files); evo = list(N['evo'].files)
    seed, names_ent = MSG[NAMEF]; names_ent = [list(e) for e in names_ent]
    expect = {}; held_cleared = set(); dg_learn_n = [0]
    SPECIAL_DI = set()                     # 필살기로 쓴 기술 칸 (같은 레벨 정리에서 제자리 우선)
    for r in draft:
        ko = r['이름']
        if ko not in slot: continue
        s = slot[ko]
        new = r['출처'] == '새로' or ko == '블랙워그레이몬'
        if not new:
            if '스타팅 균형: 타입' in r['메모'] and s < len(pers):      # 10/19: 디지골드 종도 표의 타입으로 (스타팅 균형 고침만)
                pb = bytearray(pers[s]); ts_ = r['타입'].split('/'); pb[6], pb[7] = TYPES.index(ts_[0]), TYPES.index(ts_[-1]); pers[s] = bytes(pb)
                say('타입 고침(스타팅 균형): %s → %s' % (ko, r['타입']))
            if ko in HELD_CLEAR and s < len(pers) and len(pers[s]) >= 16:      # 진화표 결정3·5: 야생이 지닌 진화 돌을 뺌(암흑·아머 갈래가 너무 일찍 열림)
                pb = bytearray(pers[s]); held = struct.unpack_from('<HH', pb, 12)
                if any(held): pb[12:16] = bytes(4); pers[s] = bytes(pb); held_cleared.add(s); say('야생이 지닌 물건 뺌: %s %s' % (ko, held))
            # 디지골드 종: 설계에만 있는 돌 갈래만 더함
            m = re.search(r'설계에만 있는 진화: ([^/]+)', r['메모'])
            if m:
                ev = evos(evo[s]) if s < len(evo) else []
                for part in m.group(1).split(';'):
                    lm = re.match(r'\s*(\S+)\(Lv (\d+)\)', part)
                    if lm and lm.group(1) in slot and (lm.group(1) in NEW or not ev):   # 새 종으로 가거나, 디지골드에서 진화가 없던 종이면 더함
                        tgt = lm.group(1); ev = [e for e in ev if e[2] not in NEXT.get(tgt, set())]   # 새 종이 중간 단계면 건너뛰던 옛 진화 제거
                        if len(ev) < 7 and all(e[2] != slot[tgt] for e in ev):
                            ev.append((EVO_LEVEL, int(lm.group(2)), slot[tgt])); evo[s] = enc_evos(ev)
                            expect.setdefault(s, {})['evo_add'] = slot[tgt]
                        continue
                    mm = re.match(r'\s*(\S+)\((.+?) 사용\)', part)
                    if not mm: P('그대로 둔 설계 진화(디지골드 종끼리라 디지골드 진화 유지):', ko, part.strip()); continue
                    tgt, itm = mm.group(1), mm.group(2)
                    if tgt not in slot or itm not in ITEM: P('설계 진화 건너뜀(대상·도구 없음):', ko, part.strip()); continue
                    if any(t == slot[tgt] for _, _, t in ev): continue
                    if len(ev) >= 7: P('진화 칸이 꽉 참:', ko); continue
                    ev.append((EVO_ITEM, ITEM[itm], slot[tgt])); evo[s] = enc_evos(ev)
                    expect.setdefault(s, {})['evo_add'] = slot[tgt]
            # 10/16 사용자: 디지골드 종이라도 성장기 기술을 진화 전까지만으로 다시 짠 종은 기술표를 표대로 씀(메모 「진화 Lv… 전까지만 기술」)
            if ('전까지만 기술' in r['메모'] or '기술 레벨 정리' in r['메모']) and s < len(learn):
                mvs = []
                for tok in r['레벨 기술'].split():
                    lv, _, nm = tok.partition(':')
                    if mid(nm) is not None and lv.isdigit(): mvs.append((max(1, min(100, int(lv))), mid(nm)))
                    elif nm: P('기술 이름 없음:', ko, nm)
                mvs.sort(); learn[s] = enc_learn(mvs[:20]); dg_learn_n[0] += 1
            continue
        if s >= len(pers): P('칸 번호가 능력치 표 밖:', ko, s); continue
        # 본뜰 종
        m = re.search(r'「(.+?)」 본뜸', r['메모']); donor = m.group(1) if m else None
        if ko == '블랙워그레이몬': donor = '워그레이몬'
        donor = DONOR_FIX.get(donor, donor)
        d = first_idx.get(donor, first_idx.get(skel(donor))) if donor else None
        orig_p = N['personal'].files                       # 본뜰 값은 원본에서(이미 덮어쓴 칸을 본뜨지 않게)
        base = bytearray(orig_p[d] if d is not None and d < len(orig_p) else orig_p[s])
        if d is None: P('본뜰 종 못 찾음(원래 칸 값 사용):', ko, donor)
        if len(base) < 44: base += bytes(44 - len(base))
        st = stats_hgss(r['HP 공 방 특공 특방 스피드'])
        base[0:6] = bytes(min(255, x) for x in st)
        ts = r['타입'].split('/'); t1 = TYPES.index(ts[0]); t2 = TYPES.index(ts[-1])
        base[6], base[7] = t1, t2
        base[8] = max(3, CATCH_NAME.get(ko, CATCH.get(r['단계'], 90)))   # 0 은 4세대 포획 계산에서 0 나누기 위험 → 최소 3
        base[9] = BASE_EXP.get(r['단계'], 150)
        a1, a2 = (r['특성'].split(',') + [''])[:2]
        base[22] = ABIL.get(a1, base[22]); base[23] = ABIL.get(a2, ABIL.get(a1, base[23]))
        if a1 not in ABIL: P('특성 이름 없음:', ko, a1)
        base[16] = 255                                   # 성별 없음
        base[19] = 3 if ko in PARTNER else 0             # 성장 곡선: GBC 와 같게 파트너 줄은 「중간느림」(낮은 레벨에선 오히려 빠름 — 결정 필요)
        base[20] = base[21] = EGG_NONE                   # 새 종은 알을 못 낳게(알에서 Lv1 완전체가 나오는 문제 — 진화표 담당 결정 10)
        pers[s] = bytes(base)
        # 기술
        mvs = []
        for tok in r['레벨 기술'].split():
            lv, _, nm = tok.partition(':')
            if mid(nm) is not None and lv.isdigit(): mvs.append((max(1, min(100, int(lv))), mid(nm)))
            elif nm: P('기술 이름 없음:', ko, nm)
        mvs.sort()
        if len(mvs) > 20: P('기술이 20개를 넘어 앞 20개만:', ko, len(mvs)); mvs = mvs[:20]   # 하트골드는 20개까지
        learn[s] = enc_learn(mvs)
        # 진화
        ev = []
        for part in r['진화'].split(';'):
            part = part.strip()
            mm = re.match(r'(\S+)\((.+)\)$', part)
            if not mm: continue
            tgt, cond = mm.group(1), mm.group(2)
            if tgt not in slot: P('진화 대상 칸 없음:', ko, '→', tgt); continue
            lm = re.match(r'Lv (\d+)', cond)
            if lm: ev.append((EVO_LEVEL, int(lm.group(1)), slot[tgt])); continue
            im = re.match(r'(.+?) 사용', cond)
            if im and im.group(1) in ITEM: ev.append((EVO_ITEM, ITEM[im.group(1)], slot[tgt])); continue
            if cond == '친밀도': ev.append((EVO_FRIEND, 0, slot[tgt])); continue
            P('진화 조건을 못 옮김:', ko, part)
        evo[s] = enc_evos(ev[:7])
        # 이름
        try:
            names_ent[s] = CM.enc(RENAME.get(ko, ko))
        except ValueError as e:
            P('이름을 못 씀:', ko, e)
        expect[s] = dict(name=RENAME.get(ko, ko), stats=st, types=(t1, t2), nmoves=len(mvs), evo=[t for _, _, t in ev[:7]])

    # ---- 도감 분류·설명(같은 폴더의 design.json 이 있을 때, 파일을 확실히 찾았을 때만)
    dexf = {}
    dpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design.json')
    if os.path.exists(dpath):
        import json as _json
        DEX = {x['ko']: x['dex'] for x in _json.load(open(dpath, encoding='utf-8'))['species']}
        bp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_도감_보충.tsv')   # 비어 있던 도감 글(10/8 작성)이 있으면 먼저 씀
        if os.path.exists(bp):
            for r in csv.DictReader(open(bp, encoding='utf-8'), delimiter=chr(9)):
                DEX[r['이름']] = {'cat': r['분류'], 'text': [r[k] for k in ('설명1', '설명2', '설명3') if r.get(k)]}
        n_sp = len(NAMES); cat_f = desc_f = None
        dg_slots_ = [v for k, v in slot.items() if v not in expect or 'name' not in expect[v]]
        for fi, (_, ent) in enumerate(MSG):
            if fi == NAMEF or abs(len(ent) - n_sp) > 15: continue
            ds = [CM.dec(e) for e in ent]
            if not ds: continue
            avg = sum(len(x) for x in ds) / len(ds)
            if avg <= 9 and sum(1 for x in ds if x.endswith(('포켓몬', '디지몬', '형'))) > 0.6 * len(ds): cat_f = cat_f or (fi, ds)
            nl = sum(1 for x in ds if NL_TOKEN in x)
            if avg > 20 and nl > 0.5 * len(ds) and (desc_f is None or nl > desc_f[2]): desc_f = (fi, ds, nl)
        if cat_f and desc_f:
            say('도감 분류 msg %d, 설명 msg %d' % (cat_f[0], desc_f[0]))
            dg_cats = [cat_f[1][v] for v in dg_slots_ if v < len(cat_f[1])]
            suffix = ' 디지몬' if sum(1 for x in dg_cats if x.endswith('디지몬')) > len(dg_cats) / 2 else ''
            for fi_ in (cat_f[0], desc_f[0]): dexf[fi_] = [list(e) for e in MSG[fi_][1]]
            nd = 0
            for s_, e in expect.items():
                if 'name' not in e or e['name'] not in DEX: continue
                dx = DEX[e['name']]
                cat = dx['cat'] + ('' if dx['cat'].endswith('몬') else suffix)
                txt = NL_TOKEN.join(dx['text'])
                for fi_, val in ((cat_f[0], cat), (desc_f[0], txt)):
                    if s_ >= len(dexf[fi_]): continue
                    try: dexf[fi_][s_] = CM.enc(val)
                    except ValueError:
                        val2 = ''.join(ch for ch in val if '가' <= ch <= '힣' or ch == ' ' or NL_TOKEN.startswith(ch) or ch in 'nrf')
                        try: dexf[fi_][s_] = CM.enc(val2)
                        except ValueError as ex:
                            if not any(x.startswith('도감 글을 못 씀: ' + e['name']) for x in problems): P('도감 글을 못 씀:', e['name'], ex)
                nd += 1
            say('도감 분류·설명 씀: %d종 (분류 꼬리 「%s」)' % (nd, suffix.strip() or '없음'))
            # 10/14 사용자: 도감 분류에 속성(백신·데이터·바이러스 …)을 「백신 공룡형」처럼 붙임. 속성은 wikimon_속성.tsv(위키몬) + NDS_속성_고침.tsv(설계)
            ATTR = {}
            here_ = os.path.dirname(os.path.abspath(__file__))
            for fn_ in ('wikimon_속성.tsv', 'NDS_속성_고침.tsv'):
                ap_ = os.path.join(here_, fn_)
                if os.path.exists(ap_):
                    for r in csv.DictReader(open(ap_, encoding='utf-8'), delimiter=chr(9)):
                        if r.get('이름') and r.get('속성', '').strip(): ATTR[r['이름'].strip()] = r['속성'].strip()
            na = 0; nlong = []
            for name_, s_ in slot.items():
                a_ = ATTR.get(name_)
                if not a_ or s_ >= len(dexf[cat_f[0]]): continue
                cur = CM.dec(dexf[cat_f[0]][s_])
                base_ = re.sub(r'\s*(디지몬|포켓몬)$', '', re.sub(r'\{[0-9A-F]{4}\}', ' ', cur)).strip()
                val = (a_ + ' ' + base_) if base_ else (a_ + ' 디지몬')
                if len(val) > 10: nlong.append(val); val = (a_ + ' ' + base_)[:10].rstrip()   # 10글자까지(넘치면 에뮬레이터로 확인해 줄임)
                try: dexf[cat_f[0]][s_] = CM.enc(val); na += 1
                except ValueError: pass
            say('도감 분류에 속성 붙임: %d종 (속성 자료 %d종%s)' % (na, len(ATTR), (', 10글자 넘어 자름 %d: %s' % (len(nlong), nlong[:5])) if nlong else ''))
        else: P('도감 분류·설명 글을 확실히 못 찾아 건너뜀(분류 %s, 설명 %s)' % (bool(cat_f), bool(desc_f)))

    # ---- 기술 이름 바꾸기(NDS_기술이름.tsv: 포켓몬 티 나는 공용 기술 → 디지몬식 이름, 효과는 그대로. 10/14 사용자)
    here_ = os.path.dirname(os.path.abspath(__file__))
    rn_path = os.path.join(here_, 'NDS_기술이름.tsv'); mvf = None
    if mv and os.path.exists(rn_path):
        mvnames = list(mv[1]); mvf = [list(e) for e in MSG[mv[0]][1]]; nr = 0; miss_r = []
        for r in csv.DictReader((l for l in open(rn_path, encoding='utf-8') if not l.startswith('#')), delimiter=chr(9)):
            if r['옛'] in mvnames:
                k = mvnames.index(r['옛'])
                try: mvf[k] = CM.enc(r['새']); mvnames[k] = r['새']; nr += 1
                except ValueError as ex: P('기술 이름 못 바꿈 %s→%s: %s' % (r['옛'], r['새'], ex))
            else: miss_r.append(r['옛'])
        say('기술 이름 디지몬식으로 바꿈: %d개 (롬에 없는 옛 이름 %d: %s)' % (nr, len(miss_r), ' '.join(miss_r[:12])))
        dexf[mv[0]] = mvf
    # ---- 필살기(10/14 사용자): design.json specials(31) + NDS_필살기.tsv(종별 더빙 이름) → 안 쓰는 기술 칸을 빌려 이름·자료를 덮어 씀, 주인 learnset 에 더함
    #      빌리는 칸: 252~467 중 기술머신·비전머신 기술이 아니고, 우리 종 learnset 과 롬 트레이너 파티에 안 나오는 것(355~467 먼저)
    #      기술 자료 a/0/1/1: [효과 u16][분류 u8][위력 u8][타입 u8][명중 u8][PP u8][부가 확률 u8] … 효과 0, 부가 확률 0
    TMHM = {264, 337, 352, 347, 46, 92, 258, 339, 331, 237, 241, 269, 58, 59, 63, 113, 182, 240, 202, 219, 218, 76, 231, 85, 87, 89, 216, 91, 94, 247, 280, 104, 115, 351, 53, 188, 201, 126, 317, 332, 259, 263, 290, 156, 213, 168, 211, 285, 289, 315, 355, 411, 412, 206, 362, 374, 451, 203, 406, 409, 261, 318, 373, 153, 421, 371, 278, 416, 397, 148, 444, 419, 86, 360, 14, 446, 244, 445, 399, 157, 404, 214, 363, 398, 138, 447, 207, 365, 369, 164, 430, 433, 15, 19, 57, 70, 250, 249, 127, 431}
    sp_log = []; waza_new = None; anim_new = [None]
    if not A.no_specials and mv:
        try:
            specials = _json.load(open(dpath, encoding='utf-8'))['specials'] if os.path.exists(dpath) else []
            waza = NARC(rom.get('a/0/1/1')); wf = list(waza.files); wsizes = {len(f) for f in wf}
            if len(wf) < 468 or len(wsizes) != 1: raise ValueError('기술 자료 NARC 모양이 다름(파일 %d개, 크기 %s)' % (len(wf), sorted(wsizes)))
            if mvf is None: mvnames = list(mv[1]); mvf = [list(e) for e in MSG[mv[0]][1]]
            STAGE_LV = {'유년기Ⅱ': 10, '유년기': 8, '성장기': 12, '성숙기': 22, '아머체': 24, '완전체': 34, '궁극체': 46}   # 10/16: 유년기Ⅱ(토코몬)가 없어 Lv20(=진화 Lv)에 배우던 것 고침
            STAGE_PW = {'성장기': (50, 100, 15), '성숙기': (70, 100, 10), '아머체': (75, 100, 10), '완전체': (90, 95, 5), '궁극체': (110, 90, 5), '유년기Ⅱ': (30, 100, 20)}
            SPECIAL_TYPES = {10, 11, 12, 13, 14, 15, 16, 17}
            # 10/16 타입별 본보기 기술(4세대 번호, 한 마리 대상 공격): 노말 몸통박치기33 · 격투 깨트리다280 · 비행 날개치기17 · 독 독찌르기398 · 땅 뼈다귀치기125 · 바위 돌떨구기88
            #   벌레 시저크로스404 · 고스트 섀도클로421 · 강철 아이언헤드442 · 불꽃 화염방사53 · 물 하이드로펌프56 · 풀 에너지볼412 · 전기 10만볼트85 · 에스퍼 사이코키네시스94 · 얼음 냉동빔58 · 드래곤 용의파동406 · 악 악의파동399
            TEMPLATE = {0: 33, 1: 280, 2: 17, 3: 398, 4: 125, 5: 88, 6: 404, 7: 421, 8: 442, 9: 33, 10: 53, 11: 56, 12: 412, 13: 85, 14: 94, 15: 58, 16: 406, 17: 399}
            anim_files = None; anim_n = [0]
            try:
                an_ = NARC(rom.get('a/0/1/0'))
                if len(an_.files) >= 468: anim_files = list(an_.files)
                else: P('기술 연출 묶음(a/0/1/0) 멤버 %d개 — 기술 번호 순이 아닌 듯해 연출은 안 바꿈' % len(an_.files))
            except Exception as ex_: P('기술 연출 묶음(a/0/1/0) 못 읽음: %s' % ex_)
            grade_of_ = {r['이름']: r['단계'] for r in draft}
            want = []                                              # (주인, 이름, 타입, 위력, 명중, PP, 차례)
            have_owner = set(); seconds = []
            for sp_ in specials:
                want.append((sp_['owner'], sp_['name'], int(sp_['type']), int(sp_['power']), int(sp_['acc']), int(sp_['pp']), 1)); have_owner.add(sp_['owner'])
            fp_ = os.path.join(here_, 'NDS_필살기.tsv')
            fp_rows = list(csv.DictReader((l for l in open(fp_, encoding='utf-8') if not l.startswith('#')), delimiter=chr(9))) if os.path.exists(fp_) else []
            if fp_rows:
                for r in fp_rows:
                    o_ = r['이름'].strip(); nm_ = r['기술'].strip()
                    if not o_ or not nm_ or o_ not in slot: continue
                    order_ = int(r['차례']) if r.get('차례', '').strip().isdigit() else 1
                    src_ = (r.get('출처') or '').strip()
                    if any((rr.get('출처') or '').strip() == '더빙' for rr in fp_rows if rr['이름'].strip() == o_):   # 10/16 사용자: 더빙(만화) 이름이 있으면 그게 첫 필살기
                        order_ = 1 if src_ == '더빙' else 2
                    if o_ in have_owner and order_ == 1: order_ = 2            # 설계 31개가 1번인 종은 도감 1번을 2번으로
                    if order_ == 2 and grade_of_.get(o_, '') in ('성장기', '유년기Ⅱ', '유년기', '유년기Ⅰ'): continue   # 10/16: 성장기는 진화 전 기술만 — 2번 필살기는 진화 뒤(Lv20)라 안 넣음
                    if any(w[0] == o_ and w[6] == order_ for w in want + seconds): continue
                    s_ = slot[o_]; p0 = pers[s_] if s_ < len(pers) else None
                    t_ = int(r['타입']) if r.get('타입', '').strip().isdigit() else (hg1.personal(p0)['type'][0] if p0 else 0)
                    pw_, ac_, pp_ = STAGE_PW.get(grade_of_.get(o_, ''), (70, 100, 10))
                    if r.get('위력', '').strip().isdigit(): pw_ = int(r['위력'])
                    (want if order_ == 1 else seconds).append((o_, nm_, t_, pw_, ac_, pp_, order_)); have_owner.add(o_)
            want = want + seconds                                  # 첫 필살기를 모든 종에 먼저, 둘째는 칸이 남을 때
            used_ids = set()
            for s_ in slot.values():
                if s_ < len(learn): used_ids.update(m_ for _, m_ in hg1.learnset(learn[s_]))
            # 10/15: 롬 원래 트레이너 파티의 기술은 빼지 않음 — hg3 가 트레이너 파티를 전부 우리 종·learnset 기술로 다시 쓰므로 원래 기술 칸은 비게 됨(35개 → 수백 개)
            KEEP_MOVES = {'불꽃세례', '우드해머', '앵콜', '일렉트릭네트', '트릭', '집단구타'}   # make_learnsets.KEEP — 그 디지몬다운 기술은 reuse 에서도 안 바꿈
            RESERVED = {0, 165, 144, 118, 119}                  # 발버둥·변신·메트로놈·자연의힘 같이 엔진이 따로 쓰는 기술은 안 빌림
            freed = []
            if A.specials_mode == 'reuse':
                # 10/16 사용자: 빈 칸만 찾지 말고 기존 칸을 정리 — 우리 종 1~2종만 배우는 공격 기술 → 같은 타입·분류, 위력 ±20 안의 「3종 이상이 배우는」 기술로 바꿈 → 그 칸이 빔
                cnt_ = collections.Counter()
                for s_ in set(slot.values()):
                    if s_ < len(learn): cnt_.update(set(m_ for _, m_ in hg1.learnset(learn[s_])))
                def info_(m_): f_ = wf[m_]; return f_[2], f_[3], f_[4]          # 분류, 위력, 타입
                common_ = [m_ for m_, c_ in cnt_.items() if c_ >= 3 and 0 < m_ < len(wf) and info_(m_)[1] > 0]
                swap_ = {}
                for m_, c_ in cnt_.items():
                    if not (1 <= c_ <= 2) or m_ in TMHM or m_ in RESERVED or not (0 < m_ < len(wf)) or mvnames[m_] in KEEP_MOVES: continue
                    cat_, pw_m, ty_ = info_(m_)
                    if pw_m == 0: continue                                   # 변화 기술은 대신할 게 마땅치 않아 그대로
                    cand_ = [x_ for x_ in common_ if info_(x_)[0] == cat_ and info_(x_)[2] == ty_ and abs(info_(x_)[1] - pw_m) <= 20]
                    if cand_: swap_[m_] = min(cand_, key=lambda x_: (abs(info_(x_)[1] - pw_m), -cnt_[x_]))
                for s_ in set(slot.values()):
                    if s_ >= len(learn): continue
                    ls_ = hg1.learnset(learn[s_]); new_ = []
                    for l_, m_ in ls_:
                        m2_ = swap_.get(m_, m_)
                        if any(m2_ == x_ for _, x_ in new_): continue          # 이미 배우는 기술이면 겹치지 않게 뺌
                        new_.append((l_, m2_))
                    if new_ != ls_:
                        learn[s_] = enc_learn(new_)
                        if s_ in expect and 'nmoves' in expect[s_]: expect[s_]['nmoves'] = len(new_)
                freed = sorted(swap_)
                used_ids = set()
                for s_ in slot.values():
                    if s_ < len(learn): used_ids.update(m_ for _, m_ in hg1.learnset(learn[s_]))
                say('필살기 칸 정리(reuse): 1~2종만 배우던 공격 기술 %d개를 비슷한 흔한 기술로 바꿔 칸을 비움. 예: %s' % (len(freed), ', '.join('%s→%s' % (mvnames[a_], mvnames[b_]) for a_, b_ in list(swap_.items())[:8])))
            donors = [i_ for i_ in list(range(355, min(468, len(mvnames)))) + list(range(252, 355)) + list(range(1, 252)) if i_ not in TMHM and i_ not in RESERVED and i_ not in used_ids and mvnames[i_] and not mvnames[i_].startswith('{')]
            say('필살기 후보 %d개, 빌릴 수 있는 기술 칸 %d개' % (len(want), len(donors)))
            if len(donors) < len(want): P('빌릴 기술 칸이 모자라 뒤쪽 %d개 필살기는 못 넣음(설계 31개와 표 앞쪽 우선)' % (len(want) - len(donors)))
            for (owner, name_, t_, pw_, ac_, pp_, order_), di in zip(want, donors):
                os_ = slot.get(owner)
                if os_ is None or os_ >= len(learn): sp_log.append('필살기 주인 칸 없음: %s %s' % (owner, name_)); continue
                try: enc_ = CM.enc(name_[:8])
                except ValueError as ex: sp_log.append('필살기 이름 못 씀 %s: %s' % (name_, ex)); continue
                tpl = TEMPLATE.get(t_, 33)
                d_ = bytearray(wf[tpl])                             # 본보기 기술 자료를 통째로 가져와(대상·우선도·깃발·콘테스트) 필요한 칸만 덮음
                struct.pack_into('<H', d_, 0, 0); d_[2] = 1 if t_ in SPECIAL_TYPES else 0      # 효과 0 = 그냥 데미지 / 분류 0 물리 · 1 특수
                d_[3] = min(255, pw_); d_[4] = t_; d_[5] = min(100, ac_); d_[6] = min(40, pp_); d_[7] = 0
                wf[di] = bytes(d_); mvf[di] = enc_
                SPECIAL_DI.add(di)
                if anim_files is not None and max(di, tpl) < len(anim_files): anim_files[di] = anim_files[tpl]; anim_n[0] += 1
                lv = STAGE_LV.get(grade_of_.get(owner, ''), 20) + (8 if order_ == 2 else 0)
                ls = hg1.learnset(learn[os_]); ls = [(l_, m_) for l_, m_ in ls if m_ != di] + [(lv, di)]
                ls.sort(key=lambda x: x[0]); ls = ls[:20]
                learn[os_] = enc_learn(ls)
                if os_ in expect and 'nmoves' in expect[os_]: expect[os_]['nmoves'] = len(ls)
                sp_log.append('%s → %s (칸 %d 「%s」 대신, Lv%d)' % (owner, name_, di, mvnames[di], lv)); mvnames[di] = name_
            waza.files = wf; waza_new = waza.build(); dexf[mv[0]] = mvf
            if anim_files is not None and anim_n[0]:
                an_.files = anim_files; anim_new[0] = an_.build(); say('필살기 연출: %d개를 같은 타입 본보기 기술 연출로 바꿈(a/0/1/0)' % anim_n[0])
            say('필살기 %d개를 기술 칸에 넣음. 예: %s' % (sum(1 for x in sp_log if '→' in x), '; '.join(x for x in sp_log if '→' in x)[:300]))
            for x in sp_log:
                if '못' in x or '없음' in x: P(x)
        except Exception as ex:
            P('필살기 넣기 건너뜀: %s' % ex)
    # ---- 진화 표(NDS_진화.tsv, 진화표 담당이 확정)가 있으면: 표에 나온 출발 종의 진화를 표대로 통째로 다시 씀(디지골드 종 포함)
    ep = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_진화.tsv')
    if os.path.exists(ep):
        METHOD = {'레벨': 4, '도구사용': 7, '도구지니고낮': 18, '도구지니고밤': 19, '기술': 20, '파티종': 21, '친밀도': 1}
        table = collections.defaultdict(list)
        for r in csv.DictReader(open(ep, encoding='utf-8'), delimiter=chr(9)):
            table[r['출발'].strip()].append(r)
        nwrite = 0
        for src_, lst in table.items():
            if src_ not in slot: P('진화 표: 출발 종 칸 없음', src_); continue
            ev = []
            for r in lst:
                m = METHOD.get(r['방법'].strip()); tgt = r['도착'].strip(); val = (r.get('값') or '').strip()
                if m is None or tgt not in slot: P('진화 표: 못 옮김', src_, '→', tgt, r['방법'], val); continue
                if m == 4: prm = int(val) if val.isdigit() else 0
                elif m in (7, 18, 19): prm = ITEM.get(val, ITEM.get(skel(val), ITEM_ID.get(val)))      # 10/15: 롬 이름이 달라도 번호로(심해의이빨 226 등)
                elif m == 20: prm = mid(val)
                elif m == 21: prm = slot.get(val)
                else: prm = 0
                if prm is None: P('진화 표: 값을 롬에서 못 찾음', src_, '→', tgt, r['방법'], val); continue
                ev.append((m, prm, slot[tgt]))
            if len(ev) > 7: P('진화 표: 7줄 넘음(앞 7줄만)', src_); ev = ev[:7]
            evo[slot[src_]] = enc_evos(ev); nwrite += 1
            if slot[src_] in expect and 'name' in expect[slot[src_]]: expect[slot[src_]]['evo'] = [t for _, _, t in ev]
            elif slot[src_] in expect: expect[slot[src_]].pop('evo_add', None)
        say('진화 표 적용: 출발 종 %d (표 우선, 초안 진화는 덮음)' % nwrite)

    # ---- 같은 레벨에 기술 2개 막기 (10/19 사용자: 「Lv12 에 두 개를 동시에 배움 — 그런 일 없어야. 무조건 옆 레벨로 옮기지 말고 판단해서
    #      살릴 건 적당한 빈 자리로, 필요 없으면 날려라. 배우는 때가 너무 붙어도 안 됨」)
    #      판단 규칙 (Lv1 시작 기술은 그대로):
    #       1) 같은 레벨에 둘이면 남길 쪽 = 필살기 > 그 디지몬다운 기술(KEEP) > 위력 높은 공격 > 보조
    #       2) 밀린 기술이 공격 기술이고, 남는 쪽과 타입이 같고 위력이 같거나 약하면 → 날림 (필살기·더 센 기술이 대신함)
    #       3) 이미 같은 타입·같은 분류에서 더 센 기술을 그보다 앞 레벨에 배우면 → 날림 (늦게 배워도 쓸 일 없음)
    #       4) 그 밖(다른 타입 공격·보조 기술)은 살림: 그 종 기술표에서 앞뒤 기술과 3레벨 이상 떨어진 가장 넓은 빈 구간의 가운데로.
    #          약한 공격 기술이 6레벨 넘게 뒤로 밀려야만 자리가 나면 → 날림 (늦게 배우는 약한 기술은 쓸모없음)
    KEEP_THEME = {'불꽃세례', '우드해머', '앵콜', '일렉트릭네트', '트릭', '집단구타'}
    def mvinfo(m):
        try:
            d = wf[m]; return d[2], d[3], d[4]          # 분류(0 물리·1 특수·2 보조), 위력, 타입
        except Exception: return 2, 0, -1
    def mname(m):
        try: return mvnames[m] if isinstance(mvnames[m], str) else CM.dec(mvnames[m])
        except Exception: return '#%d' % m
    def rank(m):
        c, pw, _ = mvinfo(m)
        return (m in SPECIAL_DI, mname(m) in KEEP_THEME, c != 2, pw)
    lv_log = []; n_drop = n_move = n_sp = 0
    for s_ in range(len(learn)):
        ls_ = hg1.learnset(learn[s_])
        if not ls_: continue
        lv1 = [x for x in ls_ if x[0] <= 1]; rest = sorted([x for x in ls_ if x[0] > 1])
        by = collections.defaultdict(list)
        for l, m in rest: by[l].append(m)
        if all(len(v) == 1 for v in by.values()): continue
        n_sp += 1
        keep = {}; loser = []
        for l, ms in by.items():
            ms = sorted(ms, key=rank, reverse=True); keep[l] = ms[0]; loser += [(l, m, ms[0]) for m in ms[1:]]
        for l, m, win in sorted(loser):
            c, pw, t = mvinfo(m); wc, wpw, wt = mvinfo(win); nm = mname(m)
            why = None
            if nm not in KEEP_THEME and c != 2:
                if wc != 2 and wt == t and pw > 1 and wpw >= pw: why = '같은 레벨의 %s(같은 타입·위력 %d≥%d)이 대신함' % (mname(win), wpw, pw)
                elif any(L < l and mvinfo(M)[2] == t and mvinfo(M)[0] == c and mvinfo(M)[1] > pw for L, M in keep.items()):
                    why = '앞 레벨에 같은 타입 더 센 기술이 있음'
            if why is None:
                # 자리 찾기: l 다음부터 8레벨 안에서, 앞뒤 기술과 3레벨 이상 → 없으면 2레벨 이상 떨어진 가장 이른 레벨.
                #           그 디지몬다운 기술(KEEP)은 그래도 없으면 1레벨 간격까지 허용. 그래도 없으면 날림
                def gap_ok(p_, need):
                    return 2 <= p_ <= 100 and all(abs(p_ - L) >= need for L in keep)
                nl = None
                for need in ((3, 2, 1) if nm in KEEP_THEME else (3, 2)):
                    nl = next((p_ for p_ in range(l + 1, l + 9) if gap_ok(p_, need)), None)
                    if nl: break
                if nl is None: why = '%s — 가까운(8레벨 안) 자리에 넣으면 다른 기술과 너무 붙음' % ('보조 기술' if c == 2 else '공격 기술')
                else:
                    keep[nl] = m; n_move += 1; lv_log.append('칸 %d: %s Lv%d → Lv%d (살림: %s)' % (s_, nm, l, nl, '보조 기술' if c == 2 else ('그 디지몬다운 기술' if nm in KEEP_THEME else '다른 타입 공격'))); continue
            n_drop += 1; lv_log.append('칸 %d: %s Lv%d 날림 (%s)' % (s_, nm, l, why))
        learn[s_] = enc_learn(lv1 + sorted(keep.items()))
    say('같은 레벨 기술 정리: %d종 — 옮김 %d · 날림 %d (자세히는 아래)' % (n_sp, n_move, n_drop))
    for x in lv_log: say('  ' + x)

    # 종 칸·실제 타입·능력치 목록 (밸런스 검토용)
    with open(os.path.join(OUT_DIR if 'OUT_DIR' in globals() else 'hg2_out', 'slots.tsv'), 'w', encoding='utf-8') as f_:
        f_.write('이름\t칸\t타입\t능력치\n')
        for ko_, s_ in sorted(slot.items(), key=lambda x: x[1]):
            if s_ < len(pers) and len(pers[s_]) >= 8:
                b_ = pers[s_]; f_.write('%s\t%d\t%s\t%s\n' % (ko_, s_, '/'.join(dict.fromkeys(TYPES[t] for t in b_[6:8])), ' '.join(str(x) for x in b_[0:6])))
    # ---- 쓰기
    def rebuild(key, files):
        n = NARC(rom.get(hg1.NARC_PATHS[key])); n.files = files; return n.build()
    msgfiles = list(N['msg'].files); msgfiles[NAMEF] = msg_encode(seed, names_ent)
    for fi_, ent_ in dexf.items(): msgfiles[fi_] = msg_encode(MSG[fi_][0], ent_)
    out = NDS(raw)
    for key, files in (('personal', pers), ('learn', learn), ('evo', evo), ('msg', msgfiles)):
        how = out.put(hg1.NARC_PATHS[key], rebuild(key, files)); say('씀 %s (%s)' % (hg1.NARC_PATHS[key], how))
    if waza_new: how = out.put('a/0/1/1', waza_new); say('씀 a/0/1/1 기술 자료(필살기) (%s)' % how)
    if anim_new[0]: how = out.put('a/0/1/0', anim_new[0]); say('씀 a/0/1/0 기술 연출(필살기) (%s)' % how)
    new_raw = bytes(out.d)

    # ---- 자체 검산: 다시 읽어 대조
    chk = NDS(new_raw)
    P2 = NARC(chk.get(hg1.NARC_PATHS['personal'])).files; L2 = NARC(chk.get(hg1.NARC_PATHS['learn'])).files
    E2 = NARC(chk.get(hg1.NARC_PATHS['evo'])).files; M2 = [msg_decode(f) for f in NARC(chk.get(hg1.NARC_PATHS['msg'])).files]
    N2 = [CM.dec(e) for e in M2[NAMEF][1]]
    bad = 0
    for s, e in expect.items():
        if 'name' not in e:
            if 'evo_add' in e and e['evo_add'] not in [t for _, _, t in evos(E2[s])]: bad += 1; P('검산 실패(디지골드 갈래 추가):', s)
            continue
        p = hg1.personal(P2[s])
        ok = (N2[s] == e['name'] and p['stats'] == [min(255, x) for x in e['stats']] and tuple(p['type']) == e['types']
              and len(hg1.learnset(L2[s])) == e['nmoves'] and [t for _, _, t in evos(E2[s])] == e['evo'])
        if not ok: bad += 1; P('검산 실패:', s, e['name'])
    say('디지골드 종 기술을 표대로 다시 씀(성장기 진화 전까지 · 단계 시작 Lv 정리): %d종' % dg_learn_n[0])
    say('자체 검산: %d종 중 실패 %d' % (len(expect), bad))
    # 다른 종은 그대로인지
    O = N['personal'].files
    for i in held_cleared:                                # 지닌 물건만 비고 나머지는 그대로인지
        if not (P2[i][:12] == O[i][:12] and P2[i][16:] == O[i][16:] and P2[i][12:16] == bytes(4)): P('지닌 물건 비우기 검산 실패:', i)
    others = [i for i in range(len(pers)) if i not in expect and i not in held_cleared and i < len(P2) and P2[i] != O[i]]
    say('바꾸지 않은 칸 중 능력치가 달라진 칸: %d (0이어야 함)' % len(others))
    if others: P('엉뚱한 칸이 바뀜:', others[:20])
    # 10/15: 이름 → 칸 표(rom_check 의 「포켓몬 흔적」 검사가 씀). 새그림 = 이 칸의 전투 그림이 새로 들어가야 하는지(디지골드 자기 칸 디지몬은 원래 그림)
    with open(os.path.join(A.out, '칸표.tsv'), 'w', encoding='utf-8') as fo:
        fo.write('이름\t칸\t출처\t새그림\n')
        for r in draft:
            if r['이름'] in slot:
                keep = r['출처'] == '디지골드' and not r['NDS 칸'].isdigit()
                fo.write('%s\t%d\t%s\t%s\n' % (r['이름'], slot[r['이름']], r['출처'], '아니오' if keep else '예'))
    open(os.path.join(A.out, 'hg2_test.nds'), 'wb').write(new_raw)
    patch = bps_make(raw, new_raw); open(os.path.join(A.out, 'hg2.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(raw, patch) == new_raw else '실패'))
    say('\n== 문제·확인할 것 %d건' % len(problems)); [say('-', x) for x in problems[:300]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')
    print('\n끝 — %s/report.txt 를 설계자에게 보내 주세요(롬·패치는 보내지 않음).' % A.out)

def evos(d):
    return hg1.evos(d) if d else []

def enc_evos(ev):
    b = b''.join(struct.pack('<HHH', m, p, t) for m, p, t in ev[:7])
    return b + bytes(6 * (7 - len(ev[:7]))) + b'\x00\x00'

def enc_learn(mvs):
    b = b''.join(struct.pack('<H', (lv << 9) | (m & 0x1FF)) for lv, m in mvs) + b'\xff\xff'
    return b + b'\x00' * ((-len(b)) % 4)

DRAFT_B64 = '@@'

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
