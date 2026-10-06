"""백로그 C5-4 — 도구 이름·설명에 남은 포켓몬 흔적 (설계자 2026-10-06)
이름: rules.ITEM_RENAME (상수 이름 → 새 이름), 설명: rules.ITEM_DESC (상수 이름 → 2줄).
설명은 설명 뱅크의 안 쓰는 구간(digi2.desc_free_runs)에 넣고 포인터만 바꿈. 자리가 모자라면 그 설명은 건너뛰고 로그에 남김 (이름은 항상 바뀜).
patch.build 에서 boss2 다음에 `import items2; P.log += items2.apply(P)`"""
import struct
import krtext, rules, digi2, boss2
from dmrom import addr


def apply(P):
    log = []
    ids = boss2.item_ids()
    names = {ids[c]: nm for c, nm in rules.ITEM_RENAME.items() if c in ids}
    miss = [c for c in rules.ITEM_RENAME if c not in ids]
    nil = digi2.rename_many(P, names)
    log.append('도구 이름 %d개 (InitList %d)%s' % (len(names), nil, ' — 상수 없음: ' + ', '.join(miss) if miss else ''))
    at, dtab, bk = digi2.item_tables(P)
    runs = digi2.desc_free_runs(P, dtab, bk)
    done = []
    skip = []
    for c, lines in rules.ITEM_DESC.items():
        if c not in ids:
            skip.append(c + '(상수 없음)')
            continue
        e = b'\x59'.join(krtext.encode(l) for l in lines) + b'\x50'
        k = next((i for i, r in enumerate(runs) if r[1] - r[0] >= len(e)), None)
        if k is None:
            skip.append(c + '(자리 없음)')
            continue
        a, b = runs[k]
        P.put(a, e)
        runs[k] = (a + len(e), b)
        P.put(dtab + 2 * (ids[c] - 1), struct.pack('<H', 0x4000 + a % 0x4000))
        done.append(c)
    log.append('도구 설명 %d개 바꿈%s' % (len(done), ' — 건너뜀: ' + ', '.join(skip) if skip else ''))
    return log
