"""base 와 myver 가 다른 바이트를 심볼 단위로 (12판): python3 diag_diff.py SaffronGym OverworldSprites …
각 이름에 대해 ① 그 이름으로 시작하는 심볼마다 [심볼, 같은 뱅크의 다음 심볼) 구간을 비교하고 ② 그 심볼 바로 뒤 심볼 2개도 같이 본다."""
import sys, dmrom, romanat

S = romanat.Sym()
D = next(v for at in ('by', 'syms', 'd') for v in [getattr(S, at, None)] if isinstance(v, dict))
syms = sorted((a, k) for k, a in D.items() if isinstance(a, int))
b = open(dmrom.default_rom(), 'rb').read()
m = open(dmrom.WORK + '/myver.gbc', 'rb').read()


def span(i):
    a = syms[i][0]
    bank = a // 0x4000
    j = i + 1
    while j < len(syms) and syms[j][0] == a: j += 1
    nxt = syms[j][0] if j < len(syms) and syms[j][0] // 0x4000 == bank else (bank + 1) * 0x4000
    return a, min(nxt, a + 0x800)


def report(i):
    a, e = span(i)
    k = syms[i][1]
    runs = []
    x = a
    while x < e:
        if b[x] != m[x]:
            y = x
            while y < e and b[y] != m[y]: y += 1
            runs.append((x, y))
            x = y
        else:
            x += 1
    print('%06X~%06X %-40s 다른 구간 %d개' % (a, e, k, len(runs)))
    for x, y in runs[:12]:
        print('  +%04X (%d바이트) base %s → myver %s' % (x - a, y - x, b[x:min(y, x + 20)].hex(), m[x:min(y, x + 20)].hex()))


for pre in sys.argv[1:]:
    idx = [i for i, (a, k) in enumerate(syms) if k == pre] or [i for i, (a, k) in enumerate(syms) if k.startswith(pre)]
    if not idx:
        print('심볼 없음', pre)
        continue
    print('===', pre, '심볼 %d개' % len(idx))
    seen = set()
    for i in idx:
        for j in range(i, min(i + 3, len(syms))):
            if j not in seen:
                seen.add(j)
                report(j)
