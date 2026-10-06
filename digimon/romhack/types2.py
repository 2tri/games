"""타입 이름을 디지몬 용어로 (설계자 2026-10-06, rules.TYPE_RENAME). 상성표·타입 번호는 그대로, 이름표와 대사 속 「○○타입」만 바꿈.
이름표: 원본 금 심볼 TypeNames(포인터 표) → 글을 같은 뱅크 빈 곳에 다시 쓰고 포인터를 바꿈
대사: 「<옛이름>타입」이 든 덩어리를 S5 와 같은 방법(texts.py)으로 다시 씀 (길면 빈 뱅크로)
patch.build 에서 items2 다음에 `import types2; P.log += types2.apply(P)`"""
import re, struct
import krtext, rules
from dmrom import addr


def apply(P):
    import romanat, texts as TX
    log = []
    R = rules.TYPE_RENAME
    if not R:
        return ['타입 이름 바꾸기 없음']
    S = romanat.Sym()
    tn = S['TypeNames']
    bank = tn // 0x4000
    d = bytes(P.d)
    # 포인터 표 길이: 다음 심볼까지 또는 포인터가 같은 뱅크 안을 가리키는 동안 (금은 27칸: 타입 0~26, 중간에 안 쓰는 칸은 '???' 공유)
    ptrs = []
    for k in range(32):
        p = d[tn + 2 * k] | d[tn + 2 * k + 1] << 8
        if not 0x4000 <= p < 0x8000:
            break
        a = addr(bank, p)
        if a <= tn + 2 * k < a + 64 and k:
            break
        ptrs.append(p)
    names = {}
    for k, p in enumerate(ptrs):
        a = addr(bank, p)
        j = a
        while d[j] != 0x50:
            j += 2 if 1 <= d[j] <= 0x0b else 1
        names[k] = krtext.decode(d, a, j)
    changed = 0
    for k, nm in list(names.items()):
        if nm in R:
            e = krtext.encode(R[nm]) + b'\x50'
            b, p = P.sp.take(len(e), bank=bank)
            P.put(addr(b, p), e)
            P.put(tn + 2 * k, struct.pack('<H', p))
            changed += 1
    log.append('타입 이름 %d개 → %s (표 %d칸)' % (changed, ', '.join('%s→%s' % kv for kv in R.items()), len(ptrs)))
    # 대사 속 「○○타입」
    d = bytes(P.d)
    idx = TX.refs_index(d)
    done = set()
    n = 0
    pat = re.compile('(%s)타입' % '|'.join(map(re.escape, sorted(R, key=len, reverse=True))))
    for (bk, ptr) in sorted(idx):
        a = addr(bk, ptr)
        if a >= len(d) or a in done:
            continue
        t = TX.read_text(d, a)
        if not t or t[1] < 2:
            continue
        done.add(a)
        s0 = t[2]
        if not pat.search(s0):
            continue
        s = pat.sub(lambda m: R[m.group(1)] + '타입', s0)
        P.retext(a, s)
        n += 1
    log.append(' 대사 속 타입 이름 %d덩어리' % n)
    return log
