"""대사 묶음 (설계자 2026-10-06): story.json 의 장면 대사를 롬 글 덩어리에 넣는다
story.json 항목 두 종류
 1. {"id":…, "find":[닻말, …], "text":"줄 / 줄 // 줄 / 줄"} — 닻말이 전부 든 덩어리가 꼭 하나일 때 그 덩어리를 통째로 바꿈
 2. {"id":…, "battle":[무리 이름, 순서], "pre":"…", "win":"…", "lose":"…"} — 트레이너 스크립트 구조로 찾음
    (없으면 맵 trainer 이벤트 구조: 직업·순서·본 글·이긴 글·0·스크립트)
    loadtrainer(0x5e 직업 순서) 앞 64바이트 안의 winlosstext(0x64 이김 2바이트 짐 2바이트), 그 앞 24바이트 안의 writetext(0x4d 2바이트)
    gym_lines 가 true 면 win 끝에 rules.GYM_LINES[직업] 두 줄을 덧붙임 (D-2 가 넣은 문장 줄을 유지)
글 표기: 「/」 줄 바꿈(첫 줄 뒤 <LINE>, 그 다음 <CONT>), 「//」 상자 넘김 <PARA>. 끝 표시는 원문 것(<DONE>/<PROMPT>/@)을 그대로 씀
원래 자리보다 길면 patch.retext 가 빈 뱅크로 옮김. 못 찾거나 둘 이상이면 로그에 후보(주소·첫 글)를 남기고 건너뜀
patch.build 에서 extra2 다음에 `import story2; P.log += story2.apply(P)`"""
import os, re, json
import dmrom, rules
from dmrom import addr

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = re.compile(r'<[A-Z_]+>|@')


def flat(s):
    """비교용: 명령 표시·빈칸 뺀 글"""
    return MARK.sub('', s).replace(' ', '').replace('　', '')


def conv(draft, tail='<DONE>'):
    import patch
    paras = []
    for para in draft.split('//'):
        lines = [x.strip() for x in para.strip().split('/') if x.strip()]
        if not lines:
            continue
        paras.append(lines[0] + ''.join(('<LINE>' if k == 1 else '<CONT>') + x for k, x in enumerate(lines[1:], 1)))
    return patch._wrap('<PARA>'.join(paras) + tail)


def tail_of(s):
    m = re.search(r'(<DONE>|<PROMPT>|@)$', s)
    return m.group(1) if m else '<DONE>'


def follow(d, a):
    """text_far(0x16 ptr bank) 로 옮겨진 글이면 옮긴 자리로 (3판: S5·D-2 가 옮긴 덩어리도 다시 쓸 수 있게)"""
    n = 0
    while a < len(d) and d[a] == 0x16 and n < 4:
        b, p = d[a + 3], d[a + 1] | d[a + 2] << 8
        if not (0 < b < 0x80 and 0x4000 <= p < 0x8000):
            break
        a = addr(b, p)
        n += 1
    return a


def blocks(P, TX):
    d = bytes(P.d)
    out = {}
    for (bank, ptr) in sorted(TX.refs_index(d)):
        a = follow(d, addr(bank, ptr))
        if a >= len(d) or d[a] != 0x00:
            continue
        t = TX.read_text(d, a)
        if t and t[1] >= 1 and t[2]:
            out[a] = t[2]
    return out


def groups():
    import encounters
    return re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())


def find_battle(d, cls, idx):
    """→ (pre 글 주소 또는 None, win 글 주소, lose 글 주소 또는 None)"""
    key = bytes([0x5e, cls, idx])
    p = -1
    hits = []
    while True:
        p = d.find(key, p + 1)
        if p < 0:
            break
        w = d.rfind(b'\x64', max(0, p - 128), p)
        if w < 0:
            continue
        bank = p // 0x4000
        win = int.from_bytes(d[w + 1:w + 3], 'little')
        lose = int.from_bytes(d[w + 3:w + 5], 'little')
        if not 0x4000 <= win < 0x8000:
            continue
        wa = follow(d, addr(bank, win))
        la = follow(d, addr(bank, lose)) if 0x4000 <= lose < 0x8000 else None
        if d[wa] != 0x00:
            continue
        t = d.rfind(b'\x4d', max(0, w - 24), w)
        pa = None
        if t >= 0:
            pp = int.from_bytes(d[t + 1:t + 3], 'little')
            if 0x4000 <= pp < 0x8000 and d[follow(d, addr(bank, pp))] == 0x00:
                pa = follow(d, addr(bank, pp))
        hits.append((pa, wa, la))
    return hits


def find_trainer_event(d, cls, idx):
    """맵의 trainer 이벤트(직업·순서·본 글·이긴 글·0·스크립트) → [(seen 글 주소, win 글 주소, None)]"""
    hits = []
    key = bytes([cls, idx])
    p = -1
    while True:
        p = d.find(key, p + 1)
        if p < 0:
            break
        bank = p // 0x4000
        seen, win, lose, scr = (int.from_bytes(d[p + 2 + 2 * i:p + 4 + 2 * i], 'little') for i in range(4))
        if not (0x4000 <= seen < 0x8000 and 0x4000 <= win < 0x8000 and lose == 0 and 0x4000 <= scr < 0x8000):
            continue
        sa, wa = follow(d, addr(bank, seen)), follow(d, addr(bank, win))
        if sa >= len(d) or wa >= len(d) or d[sa] != 0x00 or d[wa] != 0x00:
            continue
        hits.append((sa, wa, None))
    return hits


def apply(P):
    import texts as TX
    log = []
    path = os.path.join(HERE, 'story.json')
    if not os.path.exists(path):
        return ['대사: story.json 없음']
    ST = json.load(open(path, encoding='utf-8'))
    B = blocks(P, TX)
    FL = {a: flat(s) for a, s in B.items()}
    G = groups()
    n_ok = n_far = 0
    miss = []

    def put(a, new):
        nonlocal n_ok, n_far
        a = follow(bytes(P.d), a)
        r = P.retext(a, new)
        if r == 'in':
            n_ok += 1
        else:
            n_far += 1

    for e in ST:
        try:
            if 'find' in e:
                keys = [flat(k) for k in e['find']]
                cand = [a for a, f in FL.items() if all(k in f for k in keys)]
                if 'not' in e:
                    cand = [a for a in cand if not any(flat(k) in FL[a] for k in e['not'])]
                texts = {B[a] for a in cand}
                if not cand or len(texts) > 1:
                    miss.append('%s: 후보 %d%s' % (e['id'], len(cand), ''.join(' [%X]%s' % (a, MARK.sub(' ', B[a])[:20]) for a in cand[:4])))
                    continue
                for a in cand:
                    put(a, conv(e['text'], tail_of(B[a])))
                log.append('대사 %s: %X %s' % (e['id'], cand[0], MARK.sub(' ', B[cand[0]])[:14]))
            elif 'battle' in e:
                g, idx = e['battle']
                cls = G.index(g) + 1
                hits = find_battle(bytes(P.d), cls, idx) or find_trainer_event(bytes(P.d), cls, idx)
                if len(hits) != 1:
                    miss.append('%s: 전투 스크립트 %d개' % (e['id'], len(hits)))
                    continue
                pa, wa, la = hits[0]
                done = []
                if e.get('pre') and pa is not None:
                    put(pa, conv(e['pre'], tail_of(B.get(pa, ''))))
                    done.append('전')
                if e.get('win'):
                    w = e['win']
                    if e.get('gym_lines'):
                        l1, l2 = rules.GYM_LINES[cls]
                        w = w + ' // ' + l1 + ' / ' + l2
                    if e.get('after'):
                        w = w + ' // ' + e['after']
                    put(wa, conv(w, tail_of(B.get(wa, ''))))
                    done.append('이김')
                if e.get('lose') and la is not None:
                    put(la, conv(e['lose'], tail_of(B.get(la, ''))))
                    done.append('짐')
                log.append('대사 %s: %s' % (e['id'], '·'.join(done) or '글 없음'))
        except Exception as ex:
            miss.append('%s: 실패 %r' % (e['id'], ex))
    P.r.d = P.d
    head = '대사 묶음: %d항목, 덩어리 %d개 넣음 (제자리 %d, 옮김 %d), 못 넣은 항목 %d' % (len(ST), n_ok + n_far, n_ok, n_far, len(miss))
    return [head] + ['대사 못 넣음 ' + m for m in miss] + log
