"""바뀐 코드 보기: 원본 금 대비 코드(engine/·home/) 함수에서 바뀐 곳을 원본·이 판 역어셈블로 나란히,
그리고 바뀐 명령이 새로 부르는(원본에 없던 자리의) 코드를 따라가 역어셈블.
  python3 romcode.py ROM REG.json OUT.txt      (REG = romanat regions 결과)"""
import sys, json, difflib, os
import romanat, gbdis

S = romanat.Sym(); V = romanat.Vanilla()
LF = json.load(open(os.path.join(romanat.ANAT, 'labfile.json')))
TOPS = sorted((o, n) for o, n in S.rows if '.' not in n)


def lab(t, bank):
    if t >= 0x8000: return None
    o = romanat.off(bank if t >= 0x4000 else 0, t)
    n, rel = S.at(o)
    return n if rel == 0 else '%s+%d' % (n, rel)


def func_range(o):
    import bisect
    i = bisect.bisect_right([x[0] for x in TOPS], o) - 1
    s = TOPS[i][0]; e = TOPS[i + 1][0] if i + 1 < len(TOPS) else s + 0x100
    return s, min(e, s + 0x400), TOPS[i][1]


def dis_lines(d, s, e):
    return ['%-8s %s' % (h, t) for a, h, t in gbdis.block(d, s, e, lab)]


def follow_new(d, start, depth=2, seen=None, limit=160):
    """원본에 없던 코드: ret/jp 까지 역어셈블, 부르는 곳도 따라감"""
    seen = seen if seen is not None else set()
    if start in seen or depth < 0: return []
    seen.add(start); out = []; a = start; bank = start // 0x4000
    n = 0
    while n < limit and a < len(d):
        s, l, t, k = gbdis.one(d, a, (0x4000 - bank * 0x4000) if bank else 0)
        out.append('%06x %-8s %s' % (a, d[a:a + l].hex(), s))
        if k in ('call', 'jp', 'jpc') and t is not None and t < 0x8000:
            to = romanat.off(bank if t >= 0x4000 else 0, t)
            if not V.known[to]: out += ['    ↳ 새 코드 %06x' % to] + ['    ' + x for x in follow_new(d, to, depth - 1, seen)]
        if k in ('ret', 'jp') or s == 'jp hl': break
        a += l; n += 1
    return out


def main(rom, regp, outp):
    d = open(rom, 'rb').read(); R = json.load(open(regp))
    funcs = {}
    for c in R['changed']:
        f = LF.get(c['top'], '')
        if not (f.startswith('engine/') or f.startswith('home')): continue
        s, e, nm = func_range(c['off'])
        funcs.setdefault((s, e, nm, f), []).append(c)
    out = []
    for (s, e, nm, f), cs in sorted(funcs.items()):
        out.append('=' * 70); out.append('%s  (%s)  %02x:%04x  바뀐 바이트 %d' % (nm, f, s // 0x4000, s % 0x4000 + (0x4000 if s >= 0x4000 else 0), sum(c['n'] for c in cs)))
        a = dis_lines(V.a, s, e); b = dis_lines(d, s, e)
        for ln in difflib.unified_diff(a, b, '원본', '이 판', n=2, lineterm=''):
            if ln.startswith('---') or ln.startswith('+++'): continue
            out.append(ln)
        # 새로 부르는 곳
        for a0, h, t in gbdis.block(d, s, e):
            ss, l, tt, k = gbdis.one(d, a0, (0x4000 - (s // 0x4000) * 0x4000) if s >= 0x4000 else 0)
            if k in ('call', 'jp', 'jpc') and tt is not None and tt < 0x8000:
                to = romanat.off((s // 0x4000) if tt >= 0x4000 else 0, tt)
                if not V.known[to] and to < len(d):
                    out.append('  ↳ %s 가 부르는 새 코드 %06x:' % (ss, to))
                    out += ['      ' + x for x in follow_new(d, to)]
    open(outp, 'w').write('\n'.join(out))
    print('바뀐 코드 함수 %d개 → %s' % (len(funcs), outp))


if __name__ == '__main__':
    main(*sys.argv[1:4])
