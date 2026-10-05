"""롬의 대사를 모두 뽑고, 원본 금의 어느 장면(스크립트 라벨) 대사였는지 짝지음
  python3 romtext.py ROM OUT.json
대사를 가리키는 명령 자리(스크립트 쪽)는 대개 원본과 같은 자리에 있으므로, 그 자리의 원본 라벨·원본 대사를 붙인다.
→ 대사를 다른 곳으로 옮겨도(포인터만 바뀜) 원래 장면과 짝이 맞는다. 원작 대사라 work/ 에만."""
import os, sys, json, collections
import romanat, texts

S = romanat.Sym(); V = romanat.Vanilla()
LF = json.load(open(os.path.join(romanat.ANAT, 'labfile.json')))
VAN = V.a


def owner(at):
    lab, rel = S.at(at, top=True)
    f = LF.get(lab, '')
    area = f.split('/')[-1].replace('.asm', '') if f.startswith('maps/') else f
    return lab, area


def van_text_at_ref(at, op):
    """원본에서 같은 명령 자리가 가리키던 대사"""
    if not all(V.known[at:at + 4]): return None
    if VAN[at] != op: return None
    p = VAN[at + 1] | VAN[at + 2] << 8
    bank = VAN[at + 3] if op in (0x4c, 0x16) else at // 0x4000
    a = romanat.off(bank, p)
    if a >= len(VAN) or not V.known[a]: return None
    t = texts.read_text(VAN, a)
    return (a, t[2]) if t else None


def collect(path):
    d = open(path, 'rb').read(); idx = texts.refs_index(d); out = []
    for (bank, ptr), rf in idx.items():
        p = romanat.off(bank, ptr)
        if p >= len(d): continue
        t = texts.read_text(d, p)
        if not t or t[1] < 2: continue
        end, n, s = t
        refs = []; van = None
        for at, op in rf:
            lab, area = owner(at)
            refs.append([at, op, lab, area])
            v = van_text_at_ref(at, op)
            if v and van is None: van = v
        # 대사 자리 자체가 원본 대사 자리인가
        here = None
        if V.known[p]:
            tv = texts.read_text(VAN, p)
            if tv: here = tv[2]
        out.append(dict(addr=p, end=end, chars=n, text=s, refs=refs, van=van[1] if van else None, van_addr=van[0] if van else None,
                        van_here=here, moved=bool(van and van[0] != p)))
    out.sort(key=lambda o: o['addr'])
    return out


def pair_ref(T, refpath, key):
    """다른 판(REF)에서 같은 명령 자리가 가리키는 대사를 붙임 → t[key]"""
    R = open(refpath, 'rb').read()
    for t in T:
        for at, op, *_ in t['refs']:
            if R[at] != op: continue
            p = R[at + 1] | R[at + 2] << 8
            bank = R[at + 3] if op in (0x4c, 0x16) else at // 0x4000
            if not (0x4000 <= p < 0x8000) or not (0 < bank < 0x80): continue
            tv = texts.read_text(R, romanat.off(bank, p))
            if tv: t[key] = tv[2]; t[key + '_addr'] = romanat.off(bank, p); break
    return T


def van_corpus():
    """원본 금 대사 전부 (원본 값을 아는 자리만) → [(주소, 글, 장면 라벨, 맵 파일)]"""
    idx = texts.refs_index(VAN); out = {}
    for (bank, ptr), rf in idx.items():
        p = romanat.off(bank, ptr)
        if p >= len(VAN) or not V.known[p]: continue
        rf = [x for x in rf if all(V.known[x[0]:x[0] + 3])]
        if not rf: continue
        t = texts.read_text(VAN, p)
        if not t or t[1] < 2: continue
        lab, area = owner(rf[0][0])
        out[p] = (p, t[2], lab, area)
    return list(out.values())


def map_owner(at, maps):
    """옮긴 스크립트: 같은 뱅크에서 바로 앞에 있는 맵 스크립트 시작점의 맵"""
    best = None
    for m in maps:
        s = m.get('scripts_at')
        if s is None or s // 0x4000 != at // 0x4000 or s > at: continue
        if best is None or s > best[0]: best = (s, m['label'], m['area'])
    return best


def pair_moved(T, maps):
    import difflib
    corpus = van_corpus()
    used = {t['van_addr'] for t in T if t['van_addr'] is not None}
    byarea = collections.defaultdict(list)
    for c in corpus: byarea[c[3]].append(c)
    norm = lambda s: s.replace('<LINE>', ' ').replace('<PARA>', ' ').replace('<CONT>', ' ').replace('<DONE>', '').replace('<PROMPT>', '')
    for t in T:
        if t['van'] is not None: continue
        mo = map_owner(t['refs'][0][0], maps) if t['refs'] else None
        t['map'] = [mo[1], mo[2]] if mo else None
        cands = byarea.get(mo[1], []) if mo else []
        best = (0, None)
        for pool in (cands, corpus):
            for c in pool:
                if c[0] in used: continue
                r = difflib.SequenceMatcher(None, norm(t['text']), norm(c[1]), autojunk=False).ratio()
                if r > best[0]: best = (r, c)
            if best[0] >= 0.6: break
        if best[0] >= 0.45:
            c = best[1]; t['van'] = c[1]; t['van_addr'] = c[0]; t['moved'] = True; t['match'] = round(best[0], 2)
            t['van_scene'] = c[2]; used.add(c[0])
    return T


if __name__ == '__main__':
    T = collect(sys.argv[1])
    if len(sys.argv) > 3: T = pair_moved(T, json.load(open(sys.argv[3]))['maps'])
    if len(sys.argv) > 4: T = pair_ref(T, sys.argv[4], 't14')
    json.dump(T, open(sys.argv[2], 'w'), ensure_ascii=False)
    st = collections.Counter()
    for t in T:
        if t['van'] is None: st['원본 짝 없음(새 대사 또는 원본 모름)'] += 1
        elif t['van'] == t['text']: st['원본 그대로'] += 1
        else: st['고침' + (' (옮김)' if t['moved'] else ' (제자리)')] += 1
    print(len(T), dict(st))
    if any('t14' in t for t in T):
        c = collections.Counter('1.4 짝 없음' if 't14' not in t else ('1.4 와 같음' if t['t14'] == t['text'] else '1.4 와 다름') for t in T)
        print('  1.4 대비:', dict(c))
