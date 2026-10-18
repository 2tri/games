#!/usr/bin/env python3
"""HG3 — 글(용어·지명·인물 이름) 바꾸기 + 야생·일반 트레이너의 포켓몬을 디지몬으로 바꾸기 + 포켓몬 흔적 검사. (2026-10-08 작성, 가짜 롬으로만 시험)
사용:   python hg3.py "<HG2 를 거친 롬.nds>" [--base "<원본 디지골드 롬.nds>"] [--vanilla "<원본 하트골드 롬.nds>"]
        --base 를 주면 패치(hg3.bps)를 원본 디지골드 롬 기준으로 만든다(폰에서 한 번에 적용).
        --vanilla 를 주면 야생·일반 트레이너 표를 원본 하트골드에서 가져와 바꾼다(GBC 판과 같은 배치). 없으면 디지골드 표를 바꾼다.
결과:   hg3_out/hg3_test.nds, hg3_out/hg3.bps, hg3_out/report.txt
같은 폴더에 hg1.py, hg2.py(또는 넘길것_HG2.py 를 hg2.py 로), 그리고 표 3개가 들어 있어야 한다(아래 TABLES 가 비어 있을 때):
NDS_종_초안.tsv, NDS_대체표.tsv, NDS_용어표.tsv"""
import os, sys, re, csv, io, zlib, base64, struct, argparse, collections, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode, bps_make, bps_apply, say, R
import hg2

TABLES_B64 = '@@'

def load_tables(here):
    KEYS = ('NDS_종_초안.tsv', 'NDS_대체표.tsv', 'NDS_용어표.tsv', 'NDS_트레이너.tsv', 'NDS_장면대사.tsv', 'NDS_글자표_추가.tsv')
    if '@@' not in TABLES_B64:
        t = eval(zlib.decompress(base64.b64decode(''.join(TABLES_B64.split()))).decode('utf-8'))
    else:
        t = {k: open(os.path.join(here, k), encoding='utf-8').read() for k in KEYS if os.path.exists(os.path.join(here, k))}
    def rd(k): return list(csv.DictReader(io.StringIO(t[k]), delimiter='\t')) if k in t else []
    return rd(KEYS[0]), rd(KEYS[1]), rd(KEYS[2]), rd(KEYS[3]), rd(KEYS[4]), rd(KEYS[5])

# ------------------------------------------------------------- 한국어 조사
def hangul(ch): return '가' <= ch <= '힣'
def batchim(ch): return (ord(ch) - 0xAC00) % 28 if hangul(ch) else 0
JOSA = [('이라는', '라는'), ('이라면', '라면'), ('이라니', '라니'), ('이라고', '라고'), ('이에요', '예요'), ('이지만', '지만'), ('이랑', '랑'), ('이나', '나'), ('이며', '며'), ('이지', '지'), ('이야', '야'), ('이다', '다'), ('이었', '였'), ('으로', '로'), ('은', '는'), ('을', '를'), ('과', '와'), ('이', '가'), ('아', '야')]
def fix_josa(new_word, rest):
    """새 낱말 뒤의 조사를 받침에 맞게. rest = 낱말 뒤 글"""
    b = batchim(new_word[-1])
    for with_b, no_b in JOSA:
        for cand in (with_b, no_b):
            if rest.startswith(cand):
                after = rest[len(cand):len(cand) + 1]
                if cand in ('이', '가', '아', '야') and after and hangul(after): return rest   # 「이다」「가지」「아직」 같은 건 건드리지 않음
                if with_b == '으로': want = '로' if (b == 0 or b == 8) else '으로'
                else: want = with_b if b else no_b
                return want + rest[len(cand):]
    return rest
JOSA_START = ('은', '는', '이', '가', '을', '를', '과', '와', '의', '에', '도', '만', '로', '으로', '랑', '이랑', '라고', '이라고', '아', '야', '님', '씨', '이다', '다',
              '들', '라는', '이라는', '라면', '이라면', '라니', '이라니', '나', '이나', '처럼', '보다', '한테', '에게', '부터', '까지')   # 10/16: 「피카츄들과·파오리들·세레비라는·갸라도스라면·텅구리나」가 안 바뀌던 것

CONTEXT = ('관장', '체육관', '수련장', '수호자', '사천왕', '4천왕', '챔피언', '배지', '문장')
CONTEXT_OF = {'성도': ('지방', '성도의', '성도에', '성도를', '성도 '), '실버': (),
              '목호': CONTEXT + ('호수', '전파', '아지트', '로켓', '분노의')}   # 낱말별 문맥(없으면 CONTEXT)
# 같은 사람이 장면에 따라 다른 디지몬(스토리 D3: 목호 = 호수·아지트에선 레오몬, 챔피언은 아포카리몬)
ALT_BY_CONTEXT = {'목호': (('챔피언', '사천왕', '4천왕', '전당'), '아포카리몬', ('호수', '전파', '아지트', '로켓', '분노의'))}   # (이 낱말이 있고, 이 낱말은 없을 때)
SKIPPED = []    # 문맥이 없어 안 바꾼 곳(사람이 훑어볼 것)
NAMEFILE_NEW = {'목호': '아포카리몬'}     # 트레이너 이름표의 목호는 챔피언 한 명뿐
# 잡담 속 포켓몬 이름을 대체표로 바꿀 때 뺄 낱말(일반 낱말과 같거나 너무 짧음)
POKE_DENY = {'럭키', '마그마', '부스터', '투구', '랜턴', '블루', '코일', '두두', '나시', '크랩', '셀러', '삐', '뮤'}
CHANGES = []    # 이름·문맥 바꾸기 기록(앞뒤 글과 함께 report 에)

def apply_terms(s, terms, counter, names_file=False):
    """앞에서부터 한 번 훑으며 바꿈(바꾼 글 안을 다시 바꾸지 않게)"""
    res = []; i = 0; n = len(s)
    while i < n:
        hit = None
        for old, new, scope in terms:       # 긴 낱말부터 정렬돼 있음
            if s.startswith(old, i):
                prev = s[i - 1] if i > 0 else ''
                nxt = s[i + len(old):]
                if prev and hangul(prev) and not old.startswith('포켓'): continue      # 10/16: 「벌레포켓몬·새포켓몬·에스퍼포켓몬」처럼 붙여 쓴 말도 바꿈(진짜 롬 글 436곳 남아 있었음)
                if scope in ('이름', '문맥', '포켓몬') and nxt and hangul(nxt[0]) and not any(nxt.startswith(x) for x in JOSA_START): continue
                if scope == '트레이너이름' and not names_file: continue
                if names_file and old in NAMEFILE_NEW: hit = (old, NAMEFILE_NEW[old]); break
                alt = ALT_BY_CONTEXT.get(old)
                if alt and not names_file and any(w in s for w in alt[0]) and not any(w in s for w in alt[2]): hit = (old, alt[1]); break
                if scope == '문맥' and not names_file and not nxt.startswith('『') and not any(w in s for w in CONTEXT_OF.get(old, CONTEXT)):
                    if len(SKIPPED) < 100: SKIPPED.append('%s : …%s[%s]%s…' % (old, s[max(0, i - 10):i], old, nxt[:10]))
                    continue
                hit = (old, new); break
        if not hit:
            res.append(s[i]); i += 1; continue
        old, new = hit; counter[old] += 1
        if len(CHANGES) < 400 and any(t[0] == old and t[2] in ('이름', '문맥') for t in terms):
            CHANGES.append('%s→%s : …%s[%s]%s…' % (old, new, s[max(0, i - 10):i], old, s[i + len(old):i + len(old) + 10]))
        res.append(new); i += len(old)
        if batchim(old[-1]) != batchim(new[-1]):
            fixed = fix_josa(new, s[i:])
            s = s[:i] + fixed; n = len(s)
    return ''.join(res)

KIMONO = {134: ('가트몬', '엔젤우몬'), 135: ('엔젤몬', '홀리엔젤몬'), 136: ('위자몬', '팬텀몬'), 196: ('고스몬', '레이디데블몬'), 197: ('데블몬', '데블드라몬')}

def find_kimono(trd_files, trp_files, cls_names=None):
    """빛의 무녀(기모노 소녀): 이브이 진화형 1마리만 가진 트레이너가 가장 많은 직업 → (직업, [(번호, 원래 종, 레벨)])"""
    by_cls = collections.defaultdict(list)
    for i, d in enumerate(trd_files):
        t0 = hg1.trdata(d)
        if not t0 or t0['n'] != 1 or i >= len(trp_files): continue
        pt, _ = hg1.trpoke(trp_files[i], t0['flags'], t0['n'])
        if pt and pt[0]['sp'] in KIMONO: by_cls[t0['class']].append((i, pt[0]['sp'], pt[0]['lv']))
    kcls, kim = max(by_cls.items(), key=lambda kv: len(kv[1])) if by_cls else (None, [])
    if len(kim) >= 4: return kcls, kim
    # 디지골드는 이브이 진화형을 바꿔 놓았을 수 있음 → 직업 이름(기모노·무희)으로 찾고, 번호 순으로 원래 다섯 진화형 자리를 줌(10/14)
    if cls_names:
        kc = [c for c, nm in enumerate(cls_names) if nm and ('기모노' in nm or '무희' in nm or '무용' in nm)]      # 10/15 집 보고: 한글판 직업 「전통무용수」
        cand = []
        for i, d in enumerate(trd_files):
            t0 = hg1.trdata(d)
            if not t0 or t0['class'] not in kc or i >= len(trp_files): continue
            pt, _ = hg1.trpoke(trp_files[i], t0['flags'], t0['n'])
            if pt: cand.append((i, max(m['lv'] for m in pt)))
        if len(cand) >= 4:
            order = list(KIMONO)
            out = []
            for grp in ([c for c in cand if c[1] < 30], [c for c in cand if c[1] >= 30]):
                for k, (i, lv) in enumerate(sorted(grp)): out.append((i, order[k % len(order)], lv))
            return (kc[0] if kc else None), out
    return None, []

def pick_by_class(word, trd_files, trp_files, cls_names):
    """직업 이름에 word 가 든, 혼자 싸우는 트레이너를 원래 파티 최고 레벨 높은 순으로 → [(번호, 레벨)] (10/14 「직업최고:」 자리)"""
    out = []
    for i, d in enumerate(trd_files):
        t = hg1.trdata(d)
        if not t or not cls_names or t['class'] >= len(cls_names) or word not in cls_names[t['class']] or t['double']: continue
        p_, _ = hg1.trpoke(trp_files[i], t['flags'], t['n']) if i < len(trp_files) else (None, None)
        out.append((i, max((m['lv'] for m in p_), default=0) if p_ else 0))
    return sorted(out, key=lambda x: (-x[1], x[0]))

def rival_groups(trd_files, trp_files, clsf):
    """라이벌 직업 트레이너를 원래 파티 최고 레벨 순으로 3명씩(스타팅별) 묶음 → (묶음 목록(이상하면 None), 문제 글)"""
    ids = [i for i, d in enumerate(trd_files) if hg1.trdata(d) and clsf and hg1.trdata(d)['class'] < len(clsf[1]) and '라이벌' in clsf[1][hg1.trdata(d)['class']]]
    def maxlv(i):
        t = hg1.trdata(trd_files[i])
        p_, _ = hg1.trpoke(trp_files[i], t['flags'], t['n']) if i < len(trp_files) else (None, None)
        return max((m['lv'] for m in p_), default=0) if p_ else 0
    lv = {i: maxlv(i) for i in ids}
    ids.sort(key=lambda i: (lv[i], i))
    notes = []
    if len(ids) != 21: notes.append('라이벌 직업 트레이너가 %d명(21명 = 7번 × 스타팅 3 이어야 함): %s' % (len(ids), [(i, lv[i]) for i in ids]))
    groups = []
    for k in range(0, len(ids), 3):
        g = ids[k:k + 3]
        if len(g) == 3 and len({lv[i] for i in g}) == 1: groups.append(g)
        else: groups.append(None); notes.append('라이벌 %d차 묶음 %s 의 레벨이 서로 다름 %s — 이 차수는 건너뜀' % (k // 3 + 1, g, [lv[i] for i in g]))
    return groups, notes

def find_trtext(rom, MSG, ntr):
    """트레이너 글 표(trtbl): 한 파일에 (트레이너 번호 u16, 글 종류 u16) 쌍이 트레이너 번호 오름차순으로 줄지어 있고, 쌍 수 = 글 묶음(msg)의 글 수.
    (10/15 pret 분석 자료: trtbl.narc 멤버 0 = 4바이트 항목 {트레이너, 종류}, 글은 그 항목 차례 그대로 msg 한 묶음(미국판 728 = 한글판 722))
    → ((글 파일 번호, [(번호, 종류)], 경로) 또는 None, 사유)"""
    banks = [(fi, len(ent)) for fi, (_, ent) in enumerate(MSG) if 600 <= len(ent) <= 4000]
    sizes = {n for _, n in banks}
    hits = []; near = []
    for path in sorted(rom.paths):
        if not path.startswith('a/'): continue
        try: nar = NARC(rom.get(path))
        except Exception: continue
        for mi, f in enumerate(nar.files):
            if len(f) < 2400 or len(f) % 4: continue
            n = len(f) // 4
            if not any(abs(n - sz) <= 2 for sz in sizes): continue
            pairs = [struct.unpack_from('<HH', f, 4 * k) for k in range(n)]
            good = sum(1 for t, ty in pairs if t < ntr + 8 and ty < 64)
            asc = sum(1 for a_, b_ in zip(pairs, pairs[1:]) if b_[0] >= a_[0])
            if good < n * 0.98 or asc < (n - 1) * 0.97: continue
            tys = collections.defaultdict(set)
            for t, ty in pairs: tys[t].add(ty)
            near.append('%s 파일%d(%d쌍, 트레이너 %d)' % (path, mi, n, len(tys)))
            if len(tys) < max(10, ntr // 4): continue
            for fi, sz in banks:
                if abs(sz - n) <= 2: hits.append((fi, pairs[:sz], path))
    if len(hits) == 1: return hits[0], ''
    if len(hits) > 1:
        exact = [h for h in hits if len(MSG[h[0]][1]) == len(h[1])]
        if len(exact) == 1: return exact[0], ''
        return None, '후보가 %d개라 고르지 않음: %s' % (len(hits), [(h[2], h[0], len(h[1])) for h in hits][:8])
    return None, '조건에 맞는 표 없음(비슷한 파일: %s)' % (', '.join(near[:6]) or '없음')

def _find_trtext_old(rom, MSG, ntr):
    cands = []; near = []
    for path in rom.paths:
        if not path.startswith('a/'): continue
        try: nar = NARC(rom.get(path))
        except Exception: continue
        for mi, f in enumerate(nar.files[:64]):
            if len(f) < 4 * 200: continue
            for skip in (0, 4):
                body = f[skip:]; body = body[:len(body) - len(body) % 4]
                pairs = [struct.unpack_from('<HH', body, 4 * k) for k in range(len(body) // 4)]
                good = [pr for pr in pairs if pr[0] < ntr + 8 and pr[1] < 40]
                if len(good) < len(pairs) * 0.98: continue
                while pairs and not (pairs[-1][0] < ntr + 8 and pairs[-1][1] < 40): pairs.pop()     # 끝 잡동사니
                if sum(1 for a, b in zip(pairs, pairs[1:]) if b[0] < a[0]) > len(pairs) // 50: continue
                tys = collections.defaultdict(set)
                for t, ty in pairs: tys[t].add(ty)
                if len(tys) < min(50, max(5, ntr // 2)): continue
                near.append('%s 파일%d(머리 %d바이트, %d쌍, 트레이너 %d, 종류 %s)' % (path, mi, skip, len(pairs), len(tys), sorted(set(ty for _, ty in pairs))[:12]))
                if sum(1 for t in tys if 1 in tys[t]) < len(tys) // 3: continue
                for fi, (_, ent) in enumerate(MSG):
                    if abs(len(ent) - len(pairs)) <= 2: cands.append((fi, pairs[:len(ent)], path))
                break
    if len(cands) > 1:
        exact = [c for c in cands if len(MSG[c[0]][1]) == len(c[1])]
        if len(exact) == 1: return exact[0], ''
        return None, '후보가 %d개라 고르지 않음: %s' % (len(cands), [(c[2], c[0], len(c[1])) for c in cands][:8])
    return (cands[0], '') if cands else (None, '조건에 맞는 표 없음. 비슷한 파일: %s' % (near[:8] or '없음'))

def skel_name(n):
    return ''.join(ch for ch in re.sub(r'\{[0-9A-F]{4}\}', '', n or '') if '가' <= ch <= '힣')

# ------------------------------------------------------------- 하트골드 야생 표(196바이트)의 종 자리
ENC_SPECIES = ([0x14 + 2 * k for k in range(12)] + [0x2C + 2 * k for k in range(12)] + [0x44 + 2 * k for k in range(12)] +
               [0x5C, 0x5E, 0x60, 0x62] + [0x64 + 4 * k + 2 for k in range(5)] + [0x78 + 4 * k + 2 for k in range(2)] +
               [0x80 + 4 * k + 2 for k in range(5)] + [0x94 + 4 * k + 2 for k in range(5)] + [0xA8 + 4 * k + 2 for k in range(5)] +
               [0xBC + 2 * k for k in range(4)])
ENC_SIZE = 0xC4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('--base'); ap.add_argument('--vanilla'); ap.add_argument('--out', default='hg3_out')
    ap.add_argument('--force', action='store_true', help='이미 HG3 를 거친 롬이어도 실행(권하지 않음)'); ap.add_argument('--lose-type', type=int, help='「짐」 트레이너 글 종류 번호를 직접 정함')
    ap.add_argument('--no-text', action='store_true'); ap.add_argument('--no-wild', action='store_true'); ap.add_argument('--no-boss', action='store_true')
    ap.add_argument('--no-grow', action='store_true', help='(사용자 선택) 레벨 높은 곳 진화형으로 바꾸기 끔'); ap.add_argument('--no-variety', action='store_true', help='(사용자 선택) 한 종 쏠림 섞기 끔')
    ap.add_argument('--strong-plus', type=int, default=5, help='(사용자 선택) 맨 끝 1%% 칸 강한 종의 레벨 더하기. 0 = 강한 종 끔')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    draft, dexmap, termrows, trainers, scenes, extra_chars = load_tables(here)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== HG3 — 롬', rom.code)
    N = {k: NARC(rom.get(hg1.NARC_PATHS[k])) for k in ('personal', 'msg', 'enc', 'trdata', 'trpoke', 'learn', 'evo')}
    MSG = []
    for f in N['msg'].files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append((0, []))        # 못 푸는 글 파일은 건드리지 않음
    CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
    sp_ = hg1.detect_space(MSG, CM)
    if sp_: say('띄어쓰기 글자 0x%04X (한글 아닌 글자의 %.0f%%)' % (sp_[0], 100 * sp_[1]))
    for r in extra_chars:                      # NDS_글자표_추가.tsv: 부호(16진수) | 글자
        try:
            c = int(r['부호'], 16); g = hg1.glyph(r.get('글자'))
            if g is None: continue
            CM.extra[c] = g; CM.rev[g] = c
        except Exception: pass
    NAMES = [CM.dec(e) for e in MSG[NAMEF][1]]
    if not A.force and any(skel_name(CM.dec(e)) == '매튜' for fi, (_, ent) in enumerate(MSG) if fi != NAMEF for e in ent):
        raise SystemExit('실패: 이 롬에 이미 「매튜」가 있음 — HG3 를 이미 거친 롬 같다. 같은 롬을 두 번 넣으면 우리 종이 또 바뀐다.\n'
                         '      HG2 결과(hg2_out/hg2_test.nds)를 넣어 다시 돌리세요.')
    problems = []
    def P(*a): problems.append(' '.join(str(x) for x in a))

    # ---- 우리 이름 → 칸 (HG2 와 같은 규칙)
    slot = {}
    for r in draft:
        if r['NDS 칸'].isdigit(): slot[r['이름']] = int(r['NDS 칸'])
        else:
            mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
            if mm and mm.group(1) in hg2.REPLACED_DEX: slot[r['이름']] = hg2.REPLACED_DEX[mm.group(1)]
    ours = set(slot.values())
    # 화면에 나오는 이름(스토리 D15: 디지골드 표기로 통일) — 대사·용어표가 설계 이름(할세몬 등)으로 써 있어도 롬 이름(호루스몬 등)으로 바꿔 씀
    DISPLAY = dict(hg2.RENAME)
    for r in draft:
        mm = re.search(r'디지골드 「(.+?)」 그대로', r['메모'])
        if mm and r['출처'] == '디지골드' and not r['NDS 칸'].isdigit() and mm.group(1) != r['이름'] and '(' not in mm.group(1):
            DISPLAY[r['이름']] = mm.group(1)
    DKEYS = sorted(DISPLAY, key=len, reverse=True)
    def disp(t):
        t = t.replace('『', '「').replace('』', '」')      # 10/15: 글자표에 없는 겹낫표
        out = []; i = 0
        while i < len(t):
            for k in DKEYS:
                if t.startswith(k, i) and not t.startswith(DISPLAY[k], i):    # 이미 화면 이름이면 그대로(벨리얼묘티스몬 → …스몬스몬 방지)
                    v = DISPLAY[k]; out.append(v); i += len(k)
                    if batchim(k[-1]) != batchim(v[-1]): t = t[:i] + fix_josa(v, t[i:])
                    break
            else:
                out.append(t[i]); i += 1
        return ''.join(out)
    say('화면 이름으로 바꿔 쓰는 설계 이름 %d: %s' % (len(DISPLAY), ', '.join('%s→%s' % kv for kv in sorted(DISPLAY.items()))))
    dg_slots = {slot[r['이름']] for r in draft if r['출처'] == '디지골드' and r['이름'] in slot and not r['NDS 칸'].isdigit()}
    # 디지골드의 검은 워그레이몬이 따로 있는 칸(이름이 「워그레이몬」인 두 번째 칸)이면 → 블랙워그레이몬
    black_src = {i for i, n in enumerate(NAMES) if hg2.skel(n) == hg2.skel('워그레이몬') and i not in ours} if '블랙워그레이몬' in slot else set()
    pers = [hg1.personal(f) for f in N['personal'].files]
    def bst(n): return sum(pers[n]['stats']) if n < len(pers) and pers[n] else 0
    eligible = [s for s in ours if s < len(pers) and pers[s] and pers[s]['catch'] > 0]
    def nearest(x):
        p = pers[x] if x < len(pers) and pers[x] else None
        t = p['type'][0] if p else None; b = bst(x)
        cand = [s for s in eligible if pers[s]['type'][0] == t] or eligible
        return min(cand, key=lambda s: (abs(bst(s) - b), s))
    DEX = {int(r['번호']): r['우리 종'] for r in dexmap}
    # ---- 레벨 안전장치: 진화 단계가 레벨에 비해 높으면 진화 전 종으로 내림(롬에 써진 진화표 기준)
    STAGE_MIN = {'성장기': 8, '성숙기': 16, '아머체': 20, '완전체': 30, '궁극체': 45}
    grade_of = {slot[r['이름']]: r['단계'] for r in draft if r['이름'] in slot}
    prevo, minlvl = {}, {}
    for src_i, f in enumerate(N['evo'].files):
        if src_i not in ours: continue                 # 10/13: 우리 종이 아닌 칸(포켓몬)의 진화는 안 봄 — 이브이→샤미드 자리 같은 데서 포켓몬으로 내려가던 문제
        for m, prm, t in hg1.evos(f):
            if t in prevo or t not in ours: continue
            prevo[t] = src_i
            minlvl[t] = prm if m == 4 and prm else STAGE_MIN.get(grade_of.get(t, ''), 0)
    devolve_log = collections.Counter()
    def devolve(y, lv):
        seen = 0
        while y in prevo and lv < minlvl.get(y, 0) and seen < 6:
            devolve_log[(y, prevo[y])] += 1; y = prevo[y]; seen += 1
        return y
    dropped_dg = {175: '토코몬'}            # 디지골드 포요몬 자리(유아기 뺌) → 토코몬
    remap_log = collections.Counter()
    def remap(x):
        if x == 0: return 0
        if x in dropped_dg: y = slot[dropped_dg[x]]; remap_log[(x, '유아기 뺌')] += 1; return y
        if x in black_src: remap_log[(x, '검은 워그레이몬→블랙워그레이몬')] += 1; return slot['블랙워그레이몬']
        if x in dg_slots: return x                 # 디지골드 디지몬(252번 이후 등) 그대로
        if 1 <= x <= 251:                         # 251 이하는 언제나 포켓몬 번호로 본다(우리 새 종 칸과 번호가 같아도)
            name = DEX.get(x)
            if name in slot: remap_log[(x, name)] += 1; return slot[name]
            if name == '디지문자':                     # 10/16: 안농(디지문자) 칸은 그림·칸이 없어 포켓몬이 남음 → 유적에 어울리는 고스몬으로
                if '고스몬' in slot: remap_log[(x, '디지문자→고스몬')] += 1; return slot['고스몬']
                return x
            y = nearest(x); remap_log[(x, '막음→비슷한 종')] += 1; return y
        y = nearest(x); remap_log[(x, '3·4세대→비슷한 종')] += 1; return y

    # ---- 1) 글
    msgfiles = list(N['msg'].files)
    if not A.no_text:
        terms_all = []
        for r in termrows:
            if r['범위'] not in ('전체', '이름', '문맥', '트레이너이름', '포켓몬'): continue
            try: CM.enc(disp(r['새']))
            except ValueError: P('용어 「%s → %s」: 새 낱말에 글자표에 없는 글자가 있어 이번엔 뺌(문장부호·숫자 표를 채우면 들어감)' % (r['옛'], r['새'])); continue
            terms_all.append((r['옛'], disp(r['새']), r['범위']))
        have = {t[0] for t in terms_all} | {r['옛'] for r in termrows}
        poke_n = 0
        for r in dexmap:
            old, new = r['포켓몬'], r['우리 종']
            if new in slot and old not in have and old not in POKE_DENY and len(old) >= 3 and old != new:     # 2글자(「고지」 등)는 표에 적은 것만
                try: CM.enc(disp(new))
                except ValueError: continue
                terms_all.append((old, disp(new), '포켓몬')); poke_n += 1
        say('잡담 속 포켓몬 이름(대체표, 이름 범위) %d개 더함' % poke_n)
        terms_all.sort(key=lambda x: -len(x[0]))
        type_terms = {r['옛']: r['새'] for r in termrows if r['범위'] == '타입표'}
        typef = hg2.find_table(MSG, CM, ['노말', '불꽃', '물'], (17, 20))
        cnt = collections.Counter(); changed_files = 0; long_lines = []
        # (가) 장면 대사: 실마리 낱말이 모두 든 글 한 덩어리를 통째로 바꿈(띄어쓰기·줄바꿈 무시)
        def flat(x): return re.sub(r'\\[nrf]|\s', '', x)
        decoded = [[CM.dec(e) for e in ent] for _, ent in MSG]
        flat_all = [[flat(x) for x in ent] for ent in decoded]
        scene_new = {}; sc_ok = sc_skip = 0; not_found = []
        # 트레이너 글(이김·짐) 줄: 트레이너 글 표로 찾음
        # 10/14 고침: 「@글…」(원문 위치 직접)은 장면 대사 쪽에서 처리 — 전에는 트레이너 글 쪽으로 빠져 81줄이 「트레이너를 못 찾음」으로 버려졌음
        tr_rows = [r for r in scenes if r['실마리'].startswith('@') and not r['실마리'].startswith('@글')]
        scenes = [r for r in scenes if not r['실마리'].startswith('@') or r['실마리'].startswith('@글')]
        if tr_rows:
            trt, why_t = find_trtext(rom, MSG, len(N['trdata'].files))
            if not trt: P('트레이너 글 표를 못 찾아 전투 글 %d줄 건너뜀(%s — HG1 결과로 위치 확인 뒤)' % (len(tr_rows), why_t))
            else:
                tfi, tpairs, tpath = trt
                say('트레이너 글 표 %s — 글 msg %d (%d줄)' % (tpath, tfi, len(tpairs)))
                KNOWN0 = {r['하트골드 이름'] for r in trainers if r.get('하트골드 이름') and not r['하트골드 이름'].startswith('(')}
                tn_fi = next((fi for fi, (_, ent) in enumerate(MSG) if abs(len(ent) - len(N['trdata'].files)) <= 1
                              and len(KNOWN0 & {skel_name(CM.dec(e)) for e in ent}) >= min(3, len(KNOWN0))), None)
                TN0 = [skel_name(CM.dec(e)) for e in MSG[tn_fi][1]] if tn_fi is not None else []
                clsf0 = hg2.find_table(MSG, CM, ['라이벌'], (100, 140))
                rgroups, rnotes = rival_groups(N['trdata'].files, N['trpoke'].files, clsf0)
                riv = [i for g in rgroups if g for i in g]
                _, kim0 = find_kimono(N['trdata'].files, N['trpoke'].files, clsf0[1] if clsf0 else None)
                types_of = collections.defaultdict(set)
                for t, ty in tpairs: types_of[t].add(ty)
                # 「짐」(주인공이 졌을 때) 글 종류: 라이벌 모두에게 있고 전체 트레이너 중 드문 종류
                common = set.intersection(*[types_of[i] for i in riv]) - {0, 1, 2} if riv else set()
                rare = sorted(common, key=lambda ty: sum(1 for t in types_of if ty in types_of[t]))
                TY_LOSE = rare[0] if rare and sum(1 for t in types_of if rare[0] in types_of[t]) <= max(25, len(types_of) // 20) else None
                if A.lose_type is not None: TY_LOSE = A.lose_type
                say('「짐」 글 종류: %s%s (라이벌 %d명 공통 종류 %s)' % (TY_LOSE, ' (직접 정함)' if A.lose_type is not None else ' (추정 — 아래 원문으로 확인, 틀리면 --lose-type 번호)', len(riv), sorted(common)))
                if riv:
                    for ty in sorted(common)[:8]:
                        k0 = next((k for k, pr in enumerate(tpairs) if pr == (riv[0], ty)), None)
                        if k0 is not None: say('   종류 %d 원문(라이벌 첫 번째): %s' % (ty, CM.dec(MSG[tfi][1][k0])[:60]))
                key_name = {r['키'].split('#')[0]: r['하트골드 이름'] for r in trainers}
                key_name.update({r['키']: r['하트골드 이름'] for r in trainers})        # 「ExecutiveM#3」처럼 차수까지 쓴 실마리
                tr_ok = tr_skip = 0
                for row in tr_rows:
                    parts = row['실마리'].split()
                    kind, who, wl = parts[0], ' '.join(parts[1:-1]), parts[-1]
                    if kind == '@라이벌':
                        n = int(who); ids = (rgroups[n - 1] or []) if n <= len(rgroups) else []
                    elif kind == '@무녀':
                        ids = [i for i, sp0, lv in kim0 if lv >= 30] if who == '방울탑' else [i for i, sp0, lv in kim0 if lv < 30 and KIMONO[sp0][0] == who]
                    else:
                        nm = key_name.get(who, '') if kind == '@트레이너' else who
                        nth = 1
                        if (nm or '').startswith('직업최고:'):
                            _cl = hg2.find_table(MSG, CM, ['라이벌'], (100, 140))
                            _pk = pick_by_class(nm.split(':', 1)[1], N['trdata'].files, N['trpoke'].files, _cl[1] if _cl else None)
                            ids = [_pk[0][0]] if _pk else []
                        else:
                            if re.match(r'^[^#]+#\d+$', nm or ''): nm, _, nth = nm.rpartition('#'); nth = int(nth)
                            ids = [i for i, x in enumerate(TN0) if nm and x == nm][nth - 1:nth]
                    ty = {'이김': 1, '전': 0}.get(wl, TY_LOSE)
                    if not ids or ty is None:
                        P('전투 글 %s(%s): %s' % (row['번호'], row['실마리'], '트레이너를 못 찾음' if not ids else '「짐」 글 종류를 몰라 건너뜀')); tr_skip += 1; continue
                    hit = 0; why = '그 트레이너에게 이 종류 글이 없음(종류 %s)' % ty
                    for tid in ids:
                        for k, pr in enumerate(tpairs):
                            if pr != (tid, ty): continue
                            ent_k = MSG[tfi][1][k]
                            if ent_k and ent_k[0] == 0xF100: why = '압축 글이라 못 바꿈'; continue
                            if (tfi, k) in scene_new: why = '다른 줄이 이미 바꾼 글(겹침)'; continue
                            orig = CM.dec(ent_k); new_txt = disp(row['새 대사'])
                            vars_ = re.findall(r'\{FFFE\}(?:\{[0-9A-F]{4}\}){2,3}', orig)
                            ph = re.findall(r'\{(주인공|라이벌)\}', new_txt)
                            for v in vars_[:len(ph)]: new_txt = re.sub(r'\{(주인공|라이벌)\}', lambda m, v=v: v, new_txt, count=1)
                            new_txt = new_txt.replace('{주인공}', '너').replace('{라이벌}', '매튜')
                            try: CM.enc(new_txt)
                            except ValueError as ex: why = '글자표에 없는 글자(%s) — 문장부호 표 채운 뒤' % ex; continue
                            scene_new[(tfi, k)] = new_txt; hit += 1
                    if hit and hit < len(ids): P('전투 글 %s(%s): %d명 중 %d명만 바뀜 — 나머지: %s' % (row['번호'], row['실마리'], len(ids), hit, why))
                    if hit: tr_ok += 1
                    else: P('전투 글 %s(%s): %s' % (row['번호'], row['실마리'], why)); tr_skip += 1
                say('전투 글(트레이너 글 표): 바꿈 %d, 건너뜀 %d' % (tr_ok, tr_skip))
        pending = [r['번호'] for r in scenes if r['실마리'].strip().startswith('(') or not r['실마리'].strip()]
        if pending: P('장면 대사 실마리 아직 없음(HG1 결과로 하트골드 트레이너·원문을 짝지은 뒤) %d줄: %s' % (len(pending), ' '.join(pending)))
        scenes = [r for r in scenes if r['번호'] not in pending]
        LABEL = re.compile(r'^((?:\{[0-9A-F]{4}\})*)([가-힣]{1,6})((?:\{(?!FFFE)[0-9A-F]{4}\}| ){2,8})(?=\S)')
        def keep_label(orig, new_txt, speaker):
            """원문 맨 앞의 말하는 사람 이름표(「공박사  …」)를 살림. 화자 칸이 「새(옛)」이고 옛 = 이름표면 새 이름으로"""
            m = LABEL.match(orig)
            if not m or new_txt.startswith(m.group(2)): return new_txt
            if re.match(r'^\{FFFE\}', orig): return new_txt
            lab = m.group(2); mm = re.match(r'^\s*([^()]+?)\s*\(([^()]+)\)', speaker or '')
            if mm and mm.group(2).strip().split()[0] == lab: lab = mm.group(1).strip().split()[0]
            elif mm is None and speaker and speaker.strip() and speaker.strip() != lab and not speaker.strip().startswith('('): lab = speaker.strip().split()[0]
            return m.group(1) + disp(lab) + m.group(3) + new_txt
        for row in scenes:
            clue = row['실마리'].strip()
            if clue.startswith('@글꼴'):
                # 「@글꼴 ……|…… #0 ~126」 = 앞 글들이 정확히 이 모양인 글 파일(글 수 ≤ 모양 수 + 2) 중 번호가 ~ 값에 가장 가까운 것의 #n 번째
                #   (10/14 레드: 분석 자료 msg 126 = 「……」「……」. 한글판은 파일 번호가 몇 칸 밀려서 모양으로 찾음)
                mm = re.match(r'@글꼴\s+(.+?)\s+#(\d+)\s+~(\d+)', clue)
                shape = [flat(x) for x in mm.group(1).split('|')] if mm else []
                cands = [fi for fi, ent in enumerate(flat_all) if fi != NAMEF and shape and len(shape) <= len(ent) <= len(shape) + 2 and [flat(x) for x in ent[:len(shape)]] == shape]
                if not cands: P('장면 대사 %s: 「@글꼴」 모양 맞는 글 파일 없음 (%s)' % (row['번호'], clue)); sc_skip += 1; continue
                near = min(cands, key=lambda fi: abs(fi - int(mm.group(3))))
                P('장면 대사 %s: 「@글꼴」 후보 파일 %s → msg%d#%s 고름' % (row['번호'], cands[:8], near, mm.group(2)))
                hits = [(near, int(mm.group(2)))]
            elif clue.startswith('@글'):
                # 「@글 msg540#0+msg540#1」 = 원문 위치를 직접 적음(10/14: 실마리 후보에서 고름). 여럿이면 모두 바꿈(남녀 주인공판 등)
                hits = [(int(a), int(b)) for a, b in re.findall(r'msg(\d+)#(\d+)', clue)]
                bad = [h for h in hits if not (h[0] < len(MSG) and h[1] < len(MSG[h[0]][1]))]
                if not hits or bad: P('장면 대사 %s: 「@글」 위치가 롬에 없음 %s' % (row['번호'], bad or clue)); sc_skip += 1; continue
            else:
                clues = [flat(c) for c in clue.split('·') if c.strip()]
                hits = [(fi, j) for fi, ent in enumerate(flat_all) if fi != NAMEF for j, x in enumerate(ent) if clues and all(c in x for c in clues)]
                if not hits: not_found.append(row['번호']); sc_skip += 1; continue
                if len(hits) != 1:
                    P('장면 대사 %s(%s): 실마리 맞는 글 %d개 — 여럿이라 건너뜀' % (row['번호'], row['장면'], len(hits))); sc_skip += 1; continue
            done_here = 0
            for fi, j in hits:
                orig = decoded[fi][j]; new_txt = disp(row['새 대사'])
                if (fi, j) in scene_new: P('장면 대사 %s: 다른 줄이 이미 바꾼 글(겹침) msg%d#%d — 건너뜀' % (row['번호'], fi, j)); continue
                if MSG[fi][1][j] and MSG[fi][1][j][0] == 0xF100: P('장면 대사 %s: 압축 글이라 못 바꿈' % row['번호']); continue
                vars_ = re.findall(r'\{FFFE\}(?:\{[0-9A-F]{4}\}){2,3}', orig)
                ph = re.findall(r'\{(주인공|라이벌)\}', new_txt)
                if ph or vars_:
                    # 10/15 완화: 원문 변수가 남으면 그냥 버리고, 새 대사 변수가 더 많으면 「너」「매튜」로
                    for v in vars_[:len(ph)]: new_txt = re.sub(r'\{(주인공|라이벌)\}', lambda m, v=v: v, new_txt, count=1)
                    new_txt = new_txt.replace('{주인공}', '너').replace('{라이벌}', '매튜')
                new_txt = keep_label(orig, new_txt, row.get('화자', ''))
                try: CM.enc(new_txt)
                except ValueError as ex: P('장면 대사 %s: 글자표에 없는 글자라 건너뜀(%s)' % (row['번호'], ex)); continue
                scene_new[(fi, j)] = new_txt; done_here += 1
            if done_here: sc_ok += 1
            else: sc_skip += 1
        say('장면 대사: 바꿈 %d, 건너뜀 %d (사유는 맨 아래)' % (sc_ok, sc_skip))
        if not_found: P('장면 대사 실마리 맞는 글 0개(원문 낱말이 다름 — HG1 texts 에서 원문을 찾아 실마리를 고칠 것) %d줄: %s' % (len(not_found), ' '.join(not_found)))
        # ---- 도구 설명(NDS_도구설명.tsv, 10/14): 이름이 바뀐 도구의 가방 설명 글. 도구 이름표와 개수가 같은(±1) 긴 글 파일 = 설명표
        dp_ = os.path.join(here, 'NDS_도구설명.tsv')
        if os.path.exists(dp_):
            it_ = hg2.find_table(MSG, CM, ['몬스터볼', '어둠의돌'], (400, 700)) or hg2.find_table(MSG, CM, ['디지볼', '어둠의돌'], (400, 700))
            descf = None
            if it_:
                for fi, (_, ent) in enumerate(MSG):
                    if fi == it_[0] or abs(len(ent) - len(it_[1])) > 1: continue
                    ds_ = [CM.dec(e) for e in ent]
                    if sum(len(x) for x in ds_) / max(1, len(ds_)) > 15: descf = fi; break
            if not it_ or descf is None: P('도구 설명표를 못 찾아 도구 설명은 건너뜀(도구 이름표 %s)' % (it_[0] if it_ else None))
            else:
                nd_ = 0; miss_ = []
                for r in csv.DictReader((l for l in open(dp_, encoding='utf-8') if not l.startswith('#')), delimiter='	'):
                    old_ = r['도구(옛 이름)'].strip(); txt_ = r['새 설명'].strip()
                    if old_ in it_[1]: k_ = it_[1].index(old_)
                    elif old_ in hg2.ITEM_ID: k_ = hg2.ITEM_ID[old_]              # 10/15: 롬 이름이 달라도 번호로
                    else: miss_.append(old_); continue
                    if k_ < len(MSG[descf][1]) and (descf, k_) not in scene_new: scene_new[(descf, k_)] = txt_; nd_ += 1
                say('도구 설명 바꿈 %d (설명표 msg %d), 이름표에 없는 도구 %d: %s' % (nd_, descf, len(miss_), ' '.join(miss_[:10])))
            # 10/15: 도구 이름도 번호로 바꿈(디지골드가 심해의이빨·비늘 이름을 바꿔 둬서 용어표의 「전체」 바꾸기가 못 잡음). 완전체 도구 = 태그, 궁극체 도구 = 궁극의 문장
            if it_:
                for id_, new_ in ((226, '태그'), (227, '궁극의 문장'), (231, '행복의알')):
                    if id_ < len(it_[1]) and it_[1][id_] != new_ and (it_[0], id_) not in scene_new:
                        scene_new[(it_[0], id_)] = new_; say('도구 이름 번호 %d 「%s」 → 「%s」' % (id_, it_[1][id_], new_))
        KNOWN_TR = {r['하트골드 이름'] for r in trainers if r.get('하트골드 이름') and not r['하트골드 이름'].startswith('(')}
        trn_guess = next((fi for fi, (_, ent) in enumerate(MSG) if abs(len(ent) - len(N['trdata'].files)) <= 1
                          and len(KNOWN_TR & {skel_name(CM.dec(e)) for e in ent}) >= min(3, len(KNOWN_TR))), None)
        say('트레이너 이름표 msg %s' % trn_guess)
        for fi, (seed, ent) in enumerate(MSG):
            if fi == NAMEF: continue                   # 종 이름표는 HG2 가 씀
            new_ent = []; ch = False
            for e in ent:
                if e and e[0] == 0xF100: new_ent.append(e); continue     # 압축 글은 건드리지 않음
                s = CM.dec(e)
                j = len(new_ent)
                if (fi, j) in scene_new: s2 = scene_new[(fi, j)]
                elif typef and fi == typef[0] and s in type_terms: s2 = type_terms[s]; cnt[s] += 1
                else: s2 = apply_terms(s, terms_all, cnt, names_file=(fi == trn_guess))
                if s2 != s:
                    try: e2 = CM.enc(s2); ch = True
                    except ValueError as ex: P('글을 다시 못 씀(그대로 둠):', fi, ex); e2 = e
                    for line in re.split(r'\\[nrf]', s2):
                        if len(re.sub(r'\{[0-9A-F]{4}\}', '', line)) > 20: long_lines.append((fi, line[:40]))
                    new_ent.append(e2)
                else: new_ent.append(e)
            if ch: msgfiles[fi] = msg_encode(seed, new_ent); changed_files += 1
        say('글: 바뀐 파일 %d, 바꾼 횟수 %d' % (changed_files, sum(cnt.values())))
        say('많이 바뀐 낱말:', ', '.join('%s %d' % x for x in cnt.most_common(25)))
        unused = [o for o, _, sc in terms_all if cnt[o] == 0 and sc != '포켓몬']
        say('한 번도 안 나온 낱말 %d개(원래 이름이 다를 수 있음 — 확인):' % len(unused), ', '.join(unused[:60]))
        say('20글자 넘는 줄 %d개(글 상자 넘침 확인):' % len(long_lines)); [say('  msg%d %s' % x) for x in long_lines[:30]]
        say('사람 이름·문맥 바꾸기 %d곳(사람이 훑어볼 것):' % len(CHANGES)); [say('  ' + x) for x in CHANGES[:150]]
        say('문맥이 없어 안 바꾼 곳 %d곳(목호·사도 등 — 바꿔야 하면 장면 대사로):' % len(SKIPPED)); [say('  ' + x) for x in SKIPPED[:60]]
        if trn_guess is not None:
            tn_ = [skel_name(CM.dec(e)) for e in MSG[trn_guess][1]]
            for nm_ in NAMEFILE_NEW:
                ids_ = [i for i, x in enumerate(tn_) if x == nm_]
                if len(ids_) > 1: P('트레이너 이름표에 「%s」가 %d명(번호 %s) — 모두 %s 로 바뀜, 챔피언 말고 다른 사람이면 확인' % (nm_, len(ids_), ids_, NAMEFILE_NEW[nm_]))
        if typef: say('타입 이름표 msg %d' % typef[0])
        else: P('타입 이름표를 못 찾음')

    # ---- 2) 야생·트레이너
    enc_files = list(N['enc'].files); trp = list(N['trpoke'].files)
    src_enc, src_trd, src_trp = N['enc'].files, N['trdata'].files, N['trpoke'].files
    if A.vanilla:
        v = NDS(open(A.vanilla, 'rb').read())
        src_enc = NARC(v.get(hg1.NARC_PATHS['enc'])).files; src_trd = NARC(v.get(hg1.NARC_PATHS['trdata'])).files; src_trp = NARC(v.get(hg1.NARC_PATHS['trpoke'])).files
        diff = [(k, len(a), len(b)) for k, a, b in (('야생', src_enc, N['enc'].files), ('트레이너', src_trd, N['trdata'].files), ('트레이너 파티', src_trp, N['trpoke'].files)) if len(a) != len(b)]
        if diff: raise SystemExit('실패: 원본 하트골드와 디지골드의 표 파일 수가 다름 %s — 디지골드가 표를 늘렸으므로 --vanilla 없이 돌리세요' % diff)
        cls_diff = [i for i in range(len(src_trd)) if hg1.trdata(src_trd[i]) and hg1.trdata(N['trdata'].files[i]) and hg1.trdata(src_trd[i])['class'] != hg1.trdata(N['trdata'].files[i])['class']]
        if cls_diff: P('원본과 디지골드의 트레이너 직업이 다른 번호 %d개(짝이 어긋났을 수 있음): %s' % (len(cls_diff), cls_diff[:40]))
        trp = list(src_trp); enc_files = list(src_enc)        # 짝이 맞게 원본 하트골드 것으로 시작
        say('야생·트레이너 표: 원본 하트골드에서 가져옴')
    if not A.no_wild:
        # ---- 야생 규칙(10/14 사용자와 정함)
        #  NDS_귀한종.tsv: 「안 나옴」(알에서 나오는 종·전설·심볼·악당·가트몬) / 「드문 칸」(스타팅·선물 = 4%·1% 칸에만)
        #  단계: 성숙기 Lv15↑, 아머체 Lv25↑, 완전체 Lv30↑, 궁극체 = Lv50↑ 이면서 드문 칸에만
        #  바꿀 종: 진화 전 종(규칙에 맞으면) → 같은 타입·맞는 단계 중 능력치 합이 가까운 종(같은 표에 이미 나온 종은 피함)
        rare_path = os.path.join(here, 'NDS_귀한종.tsv')
        rare_rows = [r for r in csv.DictReader((l for l in open(rare_path, encoding='utf-8') if not l.startswith('#')), delimiter='\t')] if os.path.exists(rare_path) else []
        if not rare_rows: P('NDS_귀한종.tsv 가 없어 귀한 종 규칙을 건너뜀')
        NEVER = {slot[r['이름']] for r in rare_rows if r['이름'] in slot and r.get('규칙', '').strip() == '안 나옴'}
        NEVER_J = {slot[r['이름']] for r in rare_rows if r['이름'] in slot and r.get('규칙', '').strip() == '1부 안 나옴'}    # 10/15: 성도(1부)에서만 금지, 관동(2부) 야생은 허용
        REGION = {}; SEC = {}
        for rp_ in (os.path.join(here, '야생_지명.tsv'), '야생_지명.tsv'):
            if os.path.exists(rp_):
                for r_ in csv.DictReader((l for l in open(rp_, encoding='utf-8') if not l.startswith('#')), delimiter='	'):
                    k_ = (r_.get('파일 번호') or r_.get('번호') or '').strip(); v_ = (r_.get('지역') or '').strip()
                    if k_.isdigit():
                        REGION[int(k_)] = v_
                        n_ = ''.join(ch for ch in (r_.get('지명') or '') if ch.isdigit())
                        if n_: SEC[int(k_)] = int(n_)
                break
        if NEVER_J and not REGION: P('「1부 안 나옴」 종이 있는데 야생_지명.tsv 가 없어 관동 구분을 못 함 → 전부 안 나옴으로 처리(집 [11e] 표가 오면 관동에서는 나옴)')
        cur_region = ['']
        RARE_ONLY = {slot[r['이름']] for r in rare_rows if r['이름'] in slot and r.get('규칙', '').strip() == '드문 칸'}
        INSTEAD = {slot[r['이름']]: slot[r['대신'].strip()] for r in rare_rows if r['이름'] in slot and (r.get('대신') or '').strip() in slot}   # 10/15 「대신」 칸: 그 종으로 바로 바꿈(추추몬 → 피코데블몬)
        rare_slots = NEVER | RARE_ONLY | NEVER_J   # 아래 「얻을 길 없는 종 넣기」에서 이 종들은 넣지 않음
        for r in rare_rows:
            if r['이름'] not in slot: P('귀한 종 표의 이름이 초안에 없음:', r['이름'])
        WILD_MIN = {'성숙기': 18, '아머체': 25, '완전체': 30, '궁극체': 50}      # 10/14 성숙기 18(파트너 첫 진화 뒤)
        RANK = {'유년기Ⅱ': 0, '유년기': 0, '성장기': 1, '성숙기': 2, '아머체': 2, '완전체': 3, '궁극체': 4}
        def is_rare_slot(off):
            if off < 0x5C: return ((off - 0x14) // 2) % 12 >= 8               # 풀숲 12칸 중 9~12번(4%·4%·1%·1%)
            if 0x64 <= off < 0x78: return (off - 0x66) // 4 >= 3              # 파도타기 5칸 중 4·5번
            if 0x78 <= off < 0x80: return (off - 0x7A) // 4 >= 1              # 바위깨기 2칸 중 2번
            if 0x80 <= off < 0xBC: return ((off - 0x82) // 4) % 5 >= 3        # 낚싯대 3종 각 5칸 중 4·5번
            return False                                                       # 라디오·대량 발생 칸
        # 10/16 진짜 롬(어젯밤 결과) 점검: 낚시·파도타기 148칸에 물 아닌 종(디지골드가 발챙이 칸에 에렉몬을 넣어 원래 발챙이 자리마다 에렉몬 71칸 등)
        #   → 물가 칸(파도타기·낚시)은 물 타입만. 단계 검사는 그 칸의 「최저」 레벨로(전에는 최고 레벨이라 Lv10~20 칸에 성숙기가 통과)
        WATER_T = {11}                                   # 물만(얼음을 넣었더니 파피몬·워가루몬 같은 늑대가 낚시로 나옴)
        def is_water_slot(off): return 0x64 <= off < 0x78 or 0x80 <= off < 0xBC
        def is_water(s_): return bool(s_ < len(pers) and pers[s_] and set(pers[s_]['type']) & WATER_T)
        def allowed(s_, lv, rare_slot, water=False):
            if s_ in NEVER: return False
            if water and not is_water(s_): return False
            if s_ in NEVER_J and cur_region[0] != '관동': return False
            g = grade_of.get(s_, '')
            if lv < WILD_MIN.get(g, 0): return False
            if (s_ in RARE_ONLY or g == '궁극체') and not rare_slot: return False
            return True
        commons = [c for c in eligible if c not in NEVER and c not in NEVER_J and c not in RARE_ONLY and grade_of.get(c, '') in RANK and grade_of.get(c, '') != '궁극체' and not grade_of.get(c, '').startswith('유년기')]
        wild_log = collections.Counter()
        def wild_pick(y, lv, rare_slot, here_sp, memo, water=False):
            mk = (y, lv, rare_slot, water)
            if mk in memo: return memo[mk]
            if allowed(y, lv, rare_slot, water): memo[mk] = y; return y
            if y in INSTEAD and allowed(INSTEAD[y], lv, rare_slot, water):
                wild_log[('대신 종', '표')] += 1; memo[mk] = INSTEAD[y]; return INSTEAD[y]
            g = grade_of.get(y, '')
            why = ('안 나옴' if y in NEVER else '물가에 물 아닌 종' if (water and not is_water(y)) else '드문 칸 전용' if y in RARE_ONLY else '궁극체(Lv50 드문 칸)' if g == '궁극체' else '레벨에 비해 높은 단계')
            z, seen = y, 0
            while z in prevo and seen < 6:
                z = prevo[z]; seen += 1
                if allowed(z, lv, rare_slot, water):
                    wild_log[(why, '진화 전')] += 1; memo[mk] = z; return z
            t0 = pers[y]['type'][0] if y < len(pers) and pers[y] else None
            ok = [c for c in commons if lv >= WILD_MIN.get(grade_of.get(c, ''), 0) and (not water or is_water(c))]
            if not ok and water: ok = [c for c in commons if lv >= WILD_MIN.get(grade_of.get(c, ''), 0)]
            if not ok: memo[mk] = y; return y
            top = max(RANK[grade_of.get(c, '')] for c in ok)
            lv_rank = 3 if lv >= 35 else 2 if lv >= 22 else 1          # 10/16: 바꿔 넣을 때는 레벨에 맞는 단계(대단한 낚싯대 Lv40 에 성장기가 나오던 것)
            want = min(max(RANK.get(g, 1), lv_rank), top)
            def key(c):
                return (RANK[grade_of.get(c, '')] != want, pers[c]['type'][0] != t0, c in here_sp, abs(bst(c) - bst(y)), c)
            cand = [c for c in ok if RANK[grade_of.get(c, '')] <= want]
            if not cand: cand = [c for c in ok if RANK[grade_of.get(c, '')] <= 1] or ok     # 10/15: 유년기 「안 나옴」(토코몬)이 그대로 남던 버그 — 성장기 후보로
            z = min(cand, key=key); wild_log[(why, '같은 타입 비슷한 종')] += 1; memo[mk] = z; return z
        bad_size = 0
        for i, d in enumerate(src_enc):
            if len(d) != ENC_SIZE: bad_size += 1; continue
            cur_region[0] = REGION.get(i, '')
            b = bytearray(d)
            walk_lv = list(b[8:20]) or [5]
            here_sp = set(); memo = {}; slots_lv = []
            for off in ENC_SPECIES:
                x = struct.unpack_from('<H', b, off)[0]
                if off < 0x5C: lv = walk_lv[((off - 0x14) // 2) % 12]
                elif off < 0x64 or off >= 0xBC: lv = min(walk_lv)
                else: lv = b[off - 2]                          # 파도타기·바위깨기·낚시: 그 칸의 최저 레벨(10/16 — 최고 레벨이면 Lv10~20 칸에 성숙기가 통과)
                y = remap(x)
                y = devolve(y, lv) if y else y
                slots_lv.append((off, y, lv))
                if y: here_sp.add(y)
            for off, y, lv in slots_lv:
                if y:
                    z = wild_pick(y, lv, is_rare_slot(off), here_sp, memo, is_water_slot(off))
                    if z != y: here_sp.add(z)
                    y = z
                struct.pack_into('<H', b, off, y)
            enc_files[i] = bytes(b)
        say('야생 파일 %d (크기가 달라 건너뛴 파일 %d)' % (len(src_enc), bad_size))
        say('야생 규칙으로 바꾼 칸 %d: %s' % (sum(wild_log.values()), ', '.join('%s→%s %d' % (a, b_, n) for (a, b_), n in wild_log.most_common())))
        # ---- 10/16 저녁 사용자: 「한 곳에 한 종만 나오는 곳은 더 섞고, 낮은 확률로 강한 애들도」 + 적재적소(관동 Lv50 풀숲에 성장기가 나오던 것)
        #  A) 레벨에 비해 낮은 단계 → 진화형(Lv25↑ 성숙기, Lv38↑ 완전체 — 갈래가 여럿이면 칸마다 돌아가며)
        #  B) 걷기 시간대마다 한 종이 50% 넘으면 그 종은 40% 까지만, 나머지 칸은 그 장소 타입에 맞고 다른 곳에 덜 나오는 종 3~4종
        #  C) 맨 끝 1% 칸(걷기 12번·파도타기 5번·대단한 낚싯대 5번) = 그 표 주인공 종의 진화형, 레벨 +5(그 칸에만 있던 종·「드문 칸」 종은 안 건드림)
        WALK_RATE = [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1]
        evo_up = collections.defaultdict(list)
        for src_i, f in enumerate(N['evo'].files):
            if src_i not in ours: continue
            for m, prm, t in hg1.evos(f):
                if t in ours and t not in evo_up[src_i]: evo_up[src_i].append(t)
        def rank_for(lv): return 1 if lv < 25 else 2 if lv < 38 else 3
        # 장소 분위기(지명 번호 pret map_sections → 타입 번호 hg1.TYPES): 섞을 종을 고를 때 먼저 봄. 없는 곳은 그 표에 이미 있는 종들의 타입
        T_ = {n: i for i, n in enumerate(hg1.TYPES)}
        def tt(*ns): return {T_[n] for n in ns if n in T_}
        PLACE_THEME = {204: tt('고스트', '악', '독'), 205: tt('불꽃', '고스트', '에스퍼'), 206: tt('불꽃', '고스트'), 207: tt('벌레', '풀'), 214: tt('벌레', '풀'), 224: tt('벌레', '풀'),
                       209: tt('에스퍼', '바위', '고스트'), 211: tt('물', '에스퍼'), 212: tt('전기', '강철'), 201: tt('전기', '강철'), 213: tt('독', '악'),
                       218: tt('물', '비행'), 222: tt('드래곤', '물'), 217: tt('얼음', '바위'), 202: tt('풀', '벌레', '노말')}
        for sec_ in (197, 198, 199, 200, 210, 215, 216, 219, 220, 221, 228): PLACE_THEME[sec_] = tt('바위', '땅', '악')
        tables_with = collections.Counter()
        for d in enc_files:
            if len(d) == ENC_SIZE:
                for y_ in {struct.unpack_from('<H', d, off)[0] for off in ENC_SPECIES}: tables_with[y_] += 1
        def grow(y, lv, rare_slot, water, k):
            seen = 0
            while RANK.get(grade_of.get(y, ''), 9) < rank_for(lv) and evo_up.get(y) and seen < 4:
                opts = [z for z in evo_up[y] if allowed(z, lv, rare_slot, water)]
                if not opts: break
                y = opts[k % len(opts)]; seen += 1
            return y
        use_cnt = collections.Counter()
        for d in enc_files:
            if len(d) == ENC_SIZE:
                for off in ENC_SPECIES: use_cnt[struct.unpack_from('<H', d, off)[0]] += 1
        var_log = collections.Counter()
        first_seen = {}                                                # 종마다 가장 낮은 레벨 자리(아래 세 단계 뒤 사라진 종을 되살릴 곳)
        for i, d in enumerate(enc_files):
            if len(d) != ENC_SIZE: continue
            for off in ENC_SPECIES:
                if 0x5C <= off < 0x64 or off >= 0xBC: continue
                y_ = struct.unpack_from('<H', d, off)[0]
                lv_ = d[8 + ((off - 0x14) // 2) % 12] if off < 0x5C else d[off - 2]
                if y_ and (y_ not in first_seen or lv_ < first_seen[y_][2]): first_seen[y_] = (i, off, lv_)
        for i, d in enumerate(enc_files):
            if len(d) != ENC_SIZE: continue
            cur_region[0] = REGION.get(i, '')
            b = bytearray(d); lv12 = list(b[8:20])
            only_here = {y_ for y_ in (struct.unpack_from('<H', b, o)[0] for o in ENC_SPECIES) if tables_with[y_] <= 1}
            def lv_of(o): return lv12[((o - 0x14) // 2) % 12] if o < 0x5C else b[o - 2]
            for off in sorted(ENC_SPECIES, key=lv_of):                 # A (레벨 낮은 칸부터)
                if 0x5C <= off < 0x64 or off >= 0xBC: continue        # 라디오·대량 발생 칸은 그대로
                y = struct.unpack_from('<H', b, off)[0]
                if not y or y not in ours or y in RARE_ONLY: continue
                if y in only_here: only_here.discard(y); continue      # 그 표에만 있는 종: 가장 낮은 레벨 칸 하나는 그대로
                lv = lv12[((off - 0x14) // 2) % 12] if off < 0x5C else b[off - 2]
                z = y if A.no_grow else grow(y, lv, is_rare_slot(off), is_water_slot(off), off // 2)
                if z != y: struct.pack_into('<H', b, off, z); var_log['낮은 단계 → 진화형'] += 1; use_cnt[z] += 1
            if b[0] and not A.no_variety:                              # B
                for base_off in (0x14, 0x2C, 0x44):
                    sp = [struct.unpack_from('<H', b, base_off + 2 * k)[0] for k in range(12)]
                    share = collections.Counter()
                    for k, s_ in enumerate(sp): share[s_] += WALK_RATE[k]
                    dom, pct = share.most_common(1)[0]
                    if pct <= 50 or dom not in ours: continue
                    others = [s_ for s_ in share if s_ != dom and s_ in ours]
                    themes = PLACE_THEME.get(SEC.get(i)) or {t for s_ in (others or [dom]) for t in (pers[s_]['type'] if s_ < len(pers) and pers[s_] else [])}
                    kept = 0; todo_k = []
                    for k in range(12):
                        if sp[k] != dom: continue
                        if kept + WALK_RATE[k] <= 40: kept += WALK_RATE[k]; continue
                        todo_k.append(k)
                    pairs = [todo_k[j:j + 2] for j in range(0, len(todo_k), 2)]
                    have = set(sp); picks = []
                    for pr in pairs:
                        lvp = min(lv12[k] for k in pr); rare_p = all(is_rare_slot(base_off + 2 * k) for k in pr)
                        if len(picks) >= 4: c = picks[pairs.index(pr) % 4]
                        else:
                            want = rank_for(lvp)
                            cands = [c for c in commons if c not in have and allowed(c, lvp, rare_p) and allowed(c, max(lv12[k] for k in pr), rare_p)
                                     and (T_.get('물') in themes or set(pers[c]['type']) != {T_.get('물')})]      # 물만 타입은 물 분위기 장소가 아니면 풀숲에 안 섞음
                            if not cands: continue
                            c = min(cands, key=lambda c: (RANK.get(grade_of.get(c, ''), 9) != want, not (set(pers[c]['type']) & themes), use_cnt[c], abs(bst(c) - bst(dom)), c))
                            picks.append(c); have.add(c)
                        for k in pr: struct.pack_into('<H', b, base_off + 2 * k, c); use_cnt[c] += 1; var_log['한 종 쏠림 → 섞음'] += 1
            def strong_at(off, lv_new, water):                         # C
                y = struct.unpack_from('<H', b, off)[0]
                if y in RARE_ONLY or y in NEVER or use_cnt[y] <= 3: return False
                tbl = [struct.unpack_from('<H', b, o)[0] for o in ENC_SPECIES if (0x14 <= o < 0x5C) == (0x14 <= off < 0x5C) and (water == is_water_slot(o))]
                top_r = max((RANK.get(grade_of.get(x_, ''), 0) for x_ in tbl if x_ and x_ != y), default=0)     # 그 장소에서 가장 높은 단계보다 한 단계 위여야 「강한」 종
                for host, _n in collections.Counter(tbl).most_common():
                    for z in evo_up.get(host, []):
                        gz = grade_of.get(z, '')
                        if z in NEVER or (z in NEVER_J and cur_region[0] != '관동') or z in RARE_ONLY: continue
                        if water and not is_water(z): continue
                        if gz == '궁극체' and lv_new < 45: continue
                        if RANK.get(gz, 9) > rank_for(lv_new) + 1 or RANK.get(gz, 0) <= top_r: continue
                        struct.pack_into('<H', b, off, z); use_cnt[z] += 1; var_log['맨 끝 1% 칸 = 강한 진화형'] += 1; return True
                return False
            if b[0] and A.strong_plus > 0:
                for ks in (11, 10):
                    olds = [struct.unpack_from('<H', b, bo + 2 * ks)[0] for bo in (0x14, 0x2C, 0x44)]
                    if any(y_ in RARE_ONLY or y_ in NEVER or use_cnt[y_] <= 3 for y_ in olds): continue
                    nl = min(100, lv12[ks] + A.strong_plus); snap = bytes(b)
                    if all(strong_at(bo + 2 * ks, nl, False) for bo in (0x14, 0x2C, 0x44)): b[8 + ks] = nl; break
                    b[:] = snap
            for flag_i, lo_o in ((1, 0x64 + 16), (5, 0xA8 + 16)):        # 파도타기 5번 · 대단한 낚싯대 5번
                if A.strong_plus > 0 and b[flag_i] and strong_at(lo_o + 2, min(100, b[lo_o] + A.strong_plus), True):
                    b[lo_o], b[lo_o + 1] = min(100, b[lo_o] + A.strong_plus), min(100, max(b[lo_o], b[lo_o + 1]) + A.strong_plus)
            enc_files[i] = bytes(b)
        now_sp = set()
        for d in enc_files:
            if len(d) == ENC_SIZE: now_sp |= {struct.unpack_from('<H', d, off)[0] for off in ENC_SPECIES if not (0x5C <= off < 0x64 or off >= 0xBC)}   # 대량 발생·라디오 칸만 남은 종은 없는 것으로
        for y_, (i_, off_, lv_) in first_seen.items():
            if y_ not in now_sp:                                       # 진화형으로만 바뀌어 얻을 길이 사라진 종(추추몬·프리지몬 등) → 가장 낮은 레벨 자리에 되살림
                bb = bytearray(enc_files[i_]); struct.pack_into('<H', bb, off_, y_); enc_files[i_] = bytes(bb); var_log['마지막 자리라 되살림'] += 1; now_sp.add(y_)
        say('야생 다양성·적재적소(10/16 저녁): %s' % (', '.join('%s %d' % kv for kv in var_log.most_common()) or '바꿀 것 없음'))
        # ---- 얻을 길 없는 종 → 걷기 칸 6·7번(5%+5%, 아침·낮·밤 모두)에 넣음(교차 검증 10/8: 골레몬·스타몬 등 10종)
        def present_species():
            got = set()
            for d in enc_files:
                if len(d) == ENC_SIZE:
                    for off in ENC_SPECIES: got.add(struct.unpack_from('<H', d, off)[0])
            return got
        evo_next = collections.defaultdict(set)
        for src_i, f in enumerate(N['evo'].files):
            for m, prm, t in hg1.evos(f): evo_next[src_i].add(t)
        ev_path = os.path.join(here, 'NDS_이벤트표.tsv')
        ev_rows = list(csv.DictReader(open(ev_path, encoding='utf-8'), delimiter='\t')) if os.path.exists(ev_path) else []
        if not ev_rows: P('NDS_이벤트표.tsv 가 없어 「얻을 길 없는 종 야생에 넣기」를 건너뜀(이벤트로 줄 종까지 야생에 들어가지 않게)')
        EVENT_SP = {slot[r['우리 종']] for r in ev_rows if r['우리 종'] in slot and r['종류'] in ('스타팅', '알', '선물', '교환', '고정', '떠돌이', '추적', '심볼')}    # 이벤트 작업(#17)에서 줄 종(맵그림·막음·도구는 뺌)
        def reachable():
            r = present_species() | EVENT_SP
            todo = list(r)
            while todo:
                x = todo.pop()
                for t in evo_next.get(x, ()):
                    if t not in r: r.add(t); todo.append(t)
            return r
        ORDER = {'유년기': 0, '성장기': 1, '성숙기': 2, '아머체': 3, '완전체': 4, '궁극체': 5}
        def catch(n): return pers[n]['catch'] if n < len(pers) and pers[n] else 0
        used_tbl = set(); placed = []; nofit = []
        reach = reachable()
        need = sorted((x for x in ours if x not in reach and x not in rare_slots and grade_of.get(x, '') != '궁극체' and catch(x) > 5 and ORDER.get(grade_of.get(x, '').rstrip('ⅠⅡ'), 9) <= 4),
                      key=lambda x: (ORDER.get(grade_of.get(x, '').rstrip('ⅠⅡ'), 9), x))
        for x in (need if ev_rows else []):
            if x in reach: continue
            lvmin = max(minlvl.get(x, 0), STAGE_MIN.get(grade_of.get(x, ''), 0), WILD_MIN.get(grade_of.get(x, ''), 0))
            cands = []
            for i, d in enumerate(enc_files):
                if i in used_tbl or len(d) != ENC_SIZE or d[0] == 0: continue
                lv67 = min(d[8 + 6], d[8 + 7])
                if lvmin <= lv67 <= lvmin + 15: cands.append((abs(lv67 - (lvmin + 5)), i, lv67))   # 너무 이른 곳보다 레벨이 조금 높은 곳
            ok_put = False
            for _, i, lv67 in sorted(cands):
                old_d = enc_files[i]; b = bytearray(old_d)
                gone = {struct.unpack_from('<H', old_d, bo + 2 * k)[0] for bo in (0x14, 0x2C, 0x44) for k in (6, 7)}
                for base_off in (0x14, 0x2C, 0x44):
                    for k in (6, 7): struct.pack_into('<H', b, base_off + 2 * k, x)
                enc_files[i] = bytes(b)
                new_reach = reachable()
                if reach - new_reach:                          # 덮은 칸의 종을 얻을 길이 사라지면 되돌리고 다음 파일
                    enc_files[i] = old_d; continue
                used_tbl.add(i); placed.append((x, i, lv67, sorted(gone))); reach = new_reach; ok_put = True; break
            if not ok_put: nofit.append(x)
        names_of = {v: k for k, v in slot.items()}
        say('얻을 길 없던 종 %d → 야생에 넣음 %d (파일 번호는 HG1 encounters.tsv 로 장소 확인):' % (len(need), len(placed)))
        for x, i, lv, gone in placed: say('  %s → 야생 파일 %d 걷기 6·7번 칸(Lv%d), 덮은 종 %s' % (names_of.get(x, x), i, lv, [names_of.get(g, g) for g in gone]))
        low = sorted(names_of.get(x, x) for x in ours if x not in reach and catch(x) <= 5)
        if low: P('포획률 5 이하인데 이벤트표에도 없어 얻을 길 없는 종(이벤트표에 넣거나 포획률 확인):', ', '.join(map(str, low)))
        say('이벤트표로 얻는 종 %d (이벤트 작업 #17 전까지는 롬에서 아직 안 나옴)' % len(EVENT_SP))
        left = sorted(str(names_of.get(x, x)) for x in ours if x not in reach and catch(x) > 5 and x not in nofit and x not in {y for y, _, _, _ in placed})
        if left: say('아직 얻을 길 없는 종(궁극체 등 — 진화·이벤트 확인): ' + ', '.join(left))
        if nofit: P('얻을 길이 없는데 레벨 맞는 야생 칸이 없음(이벤트로 줄 것):', ', '.join(str(names_of.get(x, x)) for x in nofit))
        tr_instead = [0]; tr_moves = [0]; tr_stage = collections.Counter()
        # 10/16 진짜 롬 점검: 트레이너 1774마리 중 38마리가 레벨에 비해 너무 진화(트레이너 85 아포카리몬 Lv25, 완전체 Lv18~26, 성숙기 Lv10~13).
        #   진화 전 종이 없는 종(아포카리몬·피콜로몬·콩알몬 …)은 devolve 로 못 내려서 남았음 → 같은 타입에서 그 레벨에 맞는 단계의 비슷한 종으로
        TR_LIM = {'성숙기': 15, '아머체': 20, '완전체': 27, '궁극체': 42}
        RANK_T = {'유년기Ⅱ': 0, '유년기': 0, '성장기': 1, '성숙기': 2, '아머체': 2, '완전체': 3, '궁극체': 4}
        tr_memo = {}
        def tr_fix(y, lv):
            g = grade_of.get(y, '')
            if lv >= TR_LIM.get(g, 0) or y not in ours: return y
            if (y, lv) in tr_memo: return tr_memo[(y, lv)]
            want = 4 if lv >= 42 else 3 if lv >= 27 else 2 if lv >= 15 else 1
            t0 = pers[y]['type'][0] if y < len(pers) and pers[y] else None
            ok = [c for c in eligible if lv >= TR_LIM.get(grade_of.get(c, ''), 0) and grade_of.get(c, '') in RANK_T and not grade_of.get(c, '').startswith('유년기') and c not in NEVER]
            if not ok: tr_memo[(y, lv)] = y; return y
            z = min(ok, key=lambda c: (RANK_T[grade_of.get(c, '')] != want, pers[c]['type'][0] != t0, abs(bst(c) - bst(y)), c))
            tr_stage[(g, grade_of.get(z, ''))] += 1; tr_memo[(y, lv)] = z; return z
        learn_g = [hg1.learnset(f) for f in N['learn'].files]
        def moves_at_g(sp, lv):
            ls = [m for l, m in (learn_g[sp] if sp < len(learn_g) else []) if l <= lv]
            ls = list(dict.fromkeys(reversed(ls)))[:4][::-1]
            return (ls + [0, 0, 0, 0])[:4]
        for i, d in enumerate(src_trd):
            t = hg1.trdata(d)
            if not t or i >= len(src_trp): continue
            party, size = hg1.trpoke(src_trp[i], t['flags'], t['n'])
            if not party: P('트레이너 파티를 못 읽음:', i); continue
            b = bytearray(src_trp[i])
            for k, m in enumerate(party):
                o = k * size + 4
                y_ = devolve(remap(m['sp']), m['lv'])
                if y_ in INSTEAD and (y_ in NEVER or y_ in NEVER_J):        # 10/16 사용자: 데블몬 탑 수련자가 전부 추추몬 → 야생과 같은 「대신」 규칙(추추몬 → 피코데블몬)
                    y_ = INSTEAD[y_]; tr_instead[0] += 1
                y_ = tr_fix(y_, m['lv'])
                if not A.no_grow:                      # 10/16 저녁: 레벨에 비해 진화 전(Lv40 트레이너의 성장기 등 445마리) → 진화형(야생과 같은 기준, 「안 나옴」·2부 계열·궁극체로는 안 감)
                    seen_ = 0
                    while RANK.get(grade_of.get(y_, ''), 9) < rank_for(m['lv']) and seen_ < 4:
                        opts_ = [z_ for z_ in evo_up.get(y_, []) if z_ not in NEVER and z_ not in NEVER_J and grade_of.get(z_, '') != '궁극체']
                        if not opts_: break
                        y_ = opts_[(i + k) % len(opts_)]; seen_ += 1; tr_stage[('진화 전', '진화형')] += 1
                struct.pack_into('<H', b, o, y_)       # 폼 비트는 0, 레벨에 맞게 내림
                if t['flags'] & 1:                     # 10/16: 기술을 정해 둔 트레이너 — 원래 포켓몬 기술 대신 그 디지몬이 그 레벨까지 배우는 기술
                    mo = k * size + 6 + (2 if t['flags'] & 2 else 0)
                    mv4 = moves_at_g(y_, m['lv'])
                    if any(mv4): struct.pack_into('<4H', b, mo, *mv4); tr_moves[0] += 1
            trp[i] = bytes(b)
        say('트레이너 %d명 파티 바꿈 (「대신」 규칙으로 바꾼 마리 %d, 기술을 우리 기술표로 바꾼 마리 %d)' % (len(src_trd), tr_instead[0], tr_moves[0]))
        say('트레이너 레벨에 비해 너무 진화한 마리 바꿈 %d: %s' % (sum(tr_stage.values()), ', '.join('%s→%s %d' % (a, b_, n) for (a, b_), n in tr_stage.most_common())))
        # ---- 10/15 야생 표 밖(pret 조사): 박치기 나무 a/2/5/2 · 사파리 a/2/3/0 · 벌레잡기 대회 data/mushi/mushi_encount.bin · 사람과 교환 a/1/1/2
        #      사용자 완성 조건 「포켓몬 흔적 0」. 같은 규칙(remap → 레벨 안전장치 → 야생 규칙)으로 바꾼다. 파일이 없으면 건너뛰고 보고만.
        EXTRA_FILES = {}
        def conv(x, lv, rare_slot=False, water=False):
            y = remap(x)
            if not y: return 0
            y = devolve(y, lv)
            return wild_pick(y, lv, rare_slot, set(), {}, water)
        xlog = collections.Counter()
        cur_region[0] = '성도'          # 10/16: 박치기·사파리·벌레잡기 표는 지역을 모름 → 마지막 야생 표(관동)의 지역이 남지 않게 1부 규칙(엄하게)
        try:
            hb = NARC(rom.get('a/2/5/2')); hb_files = list(hb.files)
            for i, d in enumerate(hb_files):
                if len(d) < 0x4C: continue
                b = bytearray(d)
                for base in (0x04, 0x1C, 0x34):
                    for k in range(6):
                        o = base + 4 * k; x = struct.unpack_from('<H', b, o)[0]
                        if x: struct.pack_into('<H', b, o, conv(x, max(1, b[o + 2]), base == 0x34)); xlog['박치기'] += 1
                hb_files[i] = bytes(b)
            hb.files = hb_files; EXTRA_FILES['a/2/5/2'] = hb.build()
        except KeyError: P('박치기 나무 표(a/2/5/2)가 롬에 없음 — 건너뜀')
        try:
            sf = NARC(rom.get('a/2/3/0')); sf_files = list(sf.files)
            for i, d in enumerate(sf_files):
                if len(d) < 8: continue
                b = bytearray(d); nb = list(b[:5]); o = 8
                for t in range(5):
                    for _ in range(30):                               # 기본 칸 3시간대×10
                        x = struct.unpack_from('<H', b, o)[0]; lv = struct.unpack_from('<H', b, o + 2)[0]
                        if x: struct.pack_into('<H', b, o, conv(x, max(1, lv), water=t >= 1)); xlog['사파리'] += 1     # 10/16: 갈래 1~4 = 파도타기·낚싯대 3종 → 물 타입만
                        o += 4
                    for _ in range(3 * nb[t]):                        # 보너스 칸 아침·낮·밤 × n
                        x = struct.unpack_from('<H', b, o)[0]; lv = struct.unpack_from('<H', b, o + 2)[0]
                        if x: struct.pack_into('<H', b, o, conv(x, max(1, lv), water=t >= 1)); xlog['사파리'] += 1
                        o += 4
                    o += 4 * nb[t]                                    # 조건 칸(종 아님)
                sf_files[i] = bytes(b)
            sf.files = sf_files; EXTRA_FILES['a/2/3/0'] = sf.build()
        except KeyError: P('사파리 표(a/2/3/0)가 롬에 없음 — 건너뜀')
        mp = next((q for q in rom.paths if q.endswith('mushi_encount.bin')), None)
        if mp:
            b = bytearray(rom.get(mp))
            for o in range(0, len(b) - 7, 8):
                x = struct.unpack_from('<H', b, o)[0]
                if x: struct.pack_into('<H', b, o, conv(x, max(1, b[o + 2]))); xlog['벌레잡기'] += 1
            EXTRA_FILES[mp] = bytes(b)
        else: P('벌레잡기 대회 표(mushi_encount.bin)가 롬에 없음 — 건너뜀')
        try:
            tr_ = NARC(rom.get('a/1/1/2')); tr_files = list(tr_.files)
            for i, d in enumerate(tr_files):
                if len(d) < 0x50: continue
                b = bytearray(d)
                for o in (0x00, 0x4C):
                    x = struct.unpack_from('<I', b, o)[0]
                    if 1 <= x <= 493:
                        y = remap(x); y = devolve(y, 20) if y else y
                        if y: struct.pack_into('<I', b, o, y); xlog['교환'] += 1
                tr_files[i] = bytes(b)
            tr_.files = tr_files; EXTRA_FILES['a/1/1/2'] = tr_.build()
        except KeyError: P('사람과 교환 표(a/1/1/2)가 롬에 없음 — 건너뜀')
        say('야생 표 밖 바꿈: ' + (', '.join('%s %d칸' % kv for kv in xlog.items()) or '없음'))
        say('레벨 안전장치로 진화 전 종으로 내린 곳 %d (상위: %s)' % (sum(devolve_log.values()), ', '.join('%d→%d %d' % (a, b, n) for (a, b), n in devolve_log.most_common(10))))
        say('바꾼 종(원래 번호 → 우리 종) 상위:', ', '.join('%s→%s %d' % (k[0], k[1], v) for k, v in remap_log.most_common(30)))

    # ---- 3) 주요 트레이너 파티(수호자·4천왕·챔피언·라이벌·레드) — 하트골드 원래 이름(글 바꾸기 전 이름)으로 찾음
    if trainers and not A.no_boss:
        trnf = None
        for fi, (_, ent) in enumerate(MSG):
            if abs(len(ent) - len(src_trd)) <= 1:
                nm = [CM.dec(e) for e in ent]
                if sum(1 for x in nm if x and len(x) <= 6) > len(nm) * 0.5: trnf = (fi, nm); break
        clsf = hg2.find_table(MSG, CM, ['라이벌'], (100, 140))
        if not trnf: P('트레이너 이름표를 못 찾아 주요 트레이너는 건너뜀')
        else:
            TN = trnf[1]
            trd_now = list(src_trd if A.vanilla else N['trdata'].files)
            learnsets = [hg1.learnset(f) for f in N['learn'].files]
            def moves_at(sp, lv):
                ls = [m for l, m in (learnsets[sp] if sp < len(learnsets) else []) if l <= lv]
                ls = list(dict.fromkeys(reversed(ls)))[:4][::-1]
                return (ls + [0, 0, 0, 0])[:4]
            rgroups_b, rnotes_b = rival_groups(src_trd, src_trp, clsf)
            for x in rnotes_b: P(x)
            rival_slots = [i for g in rgroups_b for i in (g if g else [None, None, None])]   # 차수 순, 이상한 차수는 None
            rival_ids = [i for i in rival_slots if i is not None]
            groups = collections.defaultdict(list)
            for row in trainers: groups[row['키'].split('#')[0]].append(row)
            done = 0
            for key, rows_ in groups.items():
                if key.startswith('Rival'):
                    targets = rival_slots[:15] if key == 'Rival1' else rival_slots[15:21]
                    pairs = [(t_, r_) for t_, r_ in zip(targets, sorted(rows_, key=lambda r: int(r['키'].split('#')[1]))) if t_ is not None]
                elif all(re.match(r'^[^#()]+#\d+$', r_['하트골드 이름'].strip()) for r_ in rows_):
                    # 「아폴로#1」 = 하트골드 이름이 아폴로인 트레이너 중 번호 순 첫 번째(10/14: 간부는 사람마다 직업이 달라 이름으로 짝지음)
                    pairs = []
                    for r_ in rows_:
                        hn, _, nth = r_['하트골드 이름'].strip().rpartition('#')
                        ids = [i for i, n in enumerate(TN) if skel_name(n) == hn]
                        if len(ids) >= int(nth): pairs.append((ids[int(nth) - 1], r_))
                        else: P('주요 트레이너를 못 찾음:', r_['키'], r_['하트골드 이름'], '(그 이름 %d명)' % len(ids))
                elif rows_[0]['하트골드 이름'].strip().startswith('직업최고:'):
                    # 「직업최고:엘리트트레이너」 = 직업 이름에 그 말이 든 혼자 싸우는 트레이너 중 원래 파티 최고 레벨이 가장 높은 한 명(10/14 정우 자리)
                    word = rows_[0]['하트골드 이름'].strip().split(':', 1)[1]
                    _pk = pick_by_class(word, src_trd, src_trp, clsf[1] if clsf else None)
                    _lv = dict(_pk); cands = [i for i, _ in _pk if i not in rival_ids]; _mx = lambda i: _lv[i]
                    pairs = [(cands[0], rows_[0])] if cands else []
                    if cands: P('%s 자리 = 직업 「%s」 최고 레벨: 번호 %d 이름 %s Lv%d (다음 후보 %s)' % (key, word, cands[0], TN[cands[0]] if cands[0] < len(TN) else '?', _mx(cands[0]),
                                ', '.join('%d %s Lv%d' % (i, TN[i] if i < len(TN) else '?', _mx(i)) for i in cands[1:4])))
                else:
                    ids = [i for i, n in enumerate(TN) if skel_name(n) == rows_[0]['하트골드 이름']]
                    pairs = [(i, rows_[0]) for i in ids[:1]]      # 같은 이름이 여러 명(재대전)이면 첫 번째만(재대전은 일반 바꾸기 결과 유지)
                    if len(ids) > 1: P('재대전으로 보이는 같은 이름 %d명 — 첫 번째만 설계 파티:' % len(ids), key, ids)
                if not pairs: P('주요 트레이너를 못 찾음:', key, rows_[0]['하트골드 이름']); continue
                for i, row in pairs:
                    t = hg1.trdata(trd_now[i]); party = []
                    for tok in row['파티'].split(','):
                        nm, _, lv = tok.strip().rpartition(':')
                        if nm in slot and lv.isdigit(): party.append((slot[nm], int(lv)))
                        else: P('파티 종 칸 없음:', key, tok)
                    party = party[:6]
                    if not party: continue
                    _, size = hg1.trpoke(trp[i], t['flags'], t['n']) if trp[i] else (None, None)
                    capsule = 2 if (size is None or size == 6 + (2 if t['flags'] & 2 else 0) + (8 if t['flags'] & 1 else 0) + 2) else 0
                    b = b''
                    for sp, lv in party:
                        b += struct.pack('<BBHH', 100, 0, lv, sp)
                        if t['flags'] & 2: b += struct.pack('<H', 0)
                        if t['flags'] & 1: b += struct.pack('<4H', *moves_at(sp, lv))
                        if capsule: b += b'\0\0'
                    trp[i] = b
                    d = bytearray(trd_now[i]); d[3] = len(party); trd_now[i] = bytes(d); done += 1
            # ---- 빛의 무녀(기모노 소녀): 이브이 진화형 1마리만 가진 같은 직업 트레이너 → 원래 진화형 순서대로 짝(대사 1-8·스토리 3-1)
            #      원래 Lv 30 미만 = 가무연장(성숙기), 30 이상 = 방울탑(완전체). 무녀는 한 마리뿐이라 그 한 마리가 에이스(레벨 예외)
            kcls, kim = find_kimono(src_trd, src_trp, clsf[1] if clsf else None)
            if kim:
                kn = 0
                for i, sp0, lv in kim:
                    nm = KIMONO[sp0][0 if lv < 30 else 1]
                    if nm not in slot: P('무녀 종 칸 없음:', nm); continue
                    t = hg1.trdata(trd_now[i]); sp = slot[nm]
                    _, size = hg1.trpoke(src_trp[i], t['flags'], t['n'])
                    b = struct.pack('<BBHH', 100, 0, lv, sp)
                    if t['flags'] & 2: b += struct.pack('<H', 0)
                    if t['flags'] & 1: b += struct.pack('<4H', *moves_at(sp, lv))
                    if size is None or size == 6 + (2 if t['flags'] & 2 else 0) + (8 if t['flags'] & 1 else 0) + 2: b += b'\0\0'
                    trp[i] = b; d = bytearray(trd_now[i]); d[3] = 1; trd_now[i] = bytes(d); kn += 1
                say('빛의 무녀(기모노 소녀) %d명 파티 씀 (직업 번호 %s, 원래 Lv %s)' % (kn, kcls, sorted({lv for _, _, lv in kim})))
            else: P('빛의 무녀(이브이 진화형 1마리 트레이너가 4명 넘는 직업)를 못 찾음 — HG1 트레이너 목록으로 확인')
            say('주요 트레이너 파티 씀: %d명 (라이벌 직업 트레이너 %d명 찾음)' % (done, len(rival_ids)))
            trd_final = trd_now
    # ---- 쓰기
    out = NDS(raw)
    def rebuild(key, files):
        n = NARC(rom.get(hg1.NARC_PATHS[key])); n.files = files; return n.build()
    out.put(hg1.NARC_PATHS['msg'], rebuild('msg', msgfiles))
    if not A.no_wild:
        out.put(hg1.NARC_PATHS['enc'], rebuild('enc', enc_files)); out.put(hg1.NARC_PATHS['trpoke'], rebuild('trpoke', trp))
        for q, data in locals().get('EXTRA_FILES', {}).items(): out.put(q, data)
    if 'trd_final' in dir() or A.vanilla:
        out.put(hg1.NARC_PATHS['trdata'], rebuild('trdata', list(locals().get('trd_final', src_trd))))
        if A.no_wild: out.put(hg1.NARC_PATHS['trpoke'], rebuild('trpoke', trp))
    new_raw = bytes(out.d)

    # ---- 포켓몬 흔적 검사
    chk = NDS(new_raw); leftover = collections.Counter()
    for d in NARC(chk.get(hg1.NARC_PATHS['enc'])).files:
        if len(d) != ENC_SIZE: continue
        for off in ENC_SPECIES:
            x = struct.unpack_from('<H', d, off)[0]
            if x and x not in ours and x != 201: leftover['야생 %d' % x] += 1
    trd2 = NARC(chk.get(hg1.NARC_PATHS['trdata'])).files; trp2 = NARC(chk.get(hg1.NARC_PATHS['trpoke'])).files
    for i, d in enumerate(trd2):
        t = hg1.trdata(d)
        if not t or i >= len(trp2): continue
        party, _ = hg1.trpoke(trp2[i], t['flags'], t['n'])
        for m in party or []:
            if m['sp'] not in ours: leftover['트레이너 %d' % m['sp']] += 1
    say('포켓몬 흔적(우리 종 밖의 종): %d건 %s' % (sum(leftover.values()), dict(leftover.most_common(20))))
    open(os.path.join(A.out, 'hg3_test.nds'), 'wb').write(new_raw)
    base = open(A.base, 'rb').read() if A.base else raw
    patch = bps_make(base, new_raw); open(os.path.join(A.out, 'hg3.bps'), 'wb').write(patch)
    say('패치 %d바이트(기준: %s), 적용 확인 %s' % (len(patch), '원본 디지골드' if A.base else '입력 롬', 'OK' if bps_apply(base, patch) == new_raw else '실패'))
    say('\n== 문제·확인할 것 %d건' % len(problems)); [say('-', x) for x in problems[:200]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')
    print('\n끝 — %s/report.txt 를 설계자에게.' % A.out)

if __name__ == '__main__':
    try: main()
    except SystemExit: raise
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
