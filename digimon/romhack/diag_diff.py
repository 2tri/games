"""맵 하나의 자료 구간에서 base 와 myver 가 다른 바이트 (10판 진단): python3 diag_diff.py SaffronGym"""
import sys, dmrom, romanat

pre = sys.argv[1] if len(sys.argv) > 1 else 'SaffronGym'
S = romanat.Sym()
D = next(v for at in ('by', 'syms', 'd') for v in [getattr(S, at, None)] if isinstance(v, dict))
syms = sorted((a, k) for k, a in D.items() if isinstance(a, int))
mine = [(a, k) for a, k in syms if k.startswith(pre)]
assert mine, '심볼 없음 ' + pre
lo = min(a for a, _ in mine)
hi = max(a for a, _ in mine)
nxt = next((a for a, k in syms if a > hi and not k.startswith(pre)), hi + 0x200)
print('%s 심볼 %d개: %X~%X (다음 심볼 %X)' % (pre, len(mine), lo, hi, nxt))
for a, k in mine: print('  %X %s' % (a, k))
b = open(dmrom.default_rom(), 'rb').read()
m = open(dmrom.WORK + '/myver.gbc', 'rb').read()
i = lo
runs = []
while i < nxt:
    if b[i] != m[i]:
        j = i
        while j < nxt and b[j] != m[j]: j += 1
        runs.append((i, j))
        i = j
    else:
        i += 1
print('다른 구간 %d개' % len(runs))
for i, j in runs:
    near = max((a, k) for a, k in mine if a <= i) if any(a <= i for a, _ in mine) else (0, '?')
    print('  %X~%X (%s+%X) base %s → myver %s' % (i, j, near[1], i - near[0], b[i:min(j, i + 24)].hex(), m[i:min(j, i + 24)].hex()))
