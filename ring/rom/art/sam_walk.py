"""샘 걷기 그림 16×16 (임시, 제미나이 그림이 오면 교체): 프로도 그림에서 머리를 밝게, 등에 큰 배낭."""
import frodo_walk as F
def light_hair(f, rows=5):
    out = []
    for y, r in enumerate(f):
        if y < rows:
            r = ''.join('+' if c == '#' and 0 < x < 15 and r[x - 1] != '.' and r[x + 1] != '.' else c for x, c in enumerate(r))
        out.append(r)
    return out
def backpack(f):   # 뒷모습: 등에 배낭
    out = [list(r) for r in f]
    for y in range(7, 13):
        for x in range(4, 12):
            out[y][x] = '#' if y in (7, 12) or x in (4, 11) else ('1' if (x + y) % 3 else '+')
    return [''.join(r) for r in out]
def side_pack(f, left=True):   # 옆모습: 등 쪽에 배낭
    out = [list(r) for r in f]
    xs = range(9, 13) if left else range(3, 7)
    for y in range(7, 12):
        for x in xs:
            out[y][x] = '#' if y in (7, 11) or x in (xs[0], xs[-1]) else '1'
    return [''.join(r) for r in out]
FRAMES = [light_hair(F.DOWN), light_hair(F.DOWN2), backpack(light_hair(F.UP, 7)), backpack(light_hair(F.UP2, 7)),
          side_pack(light_hair(F.LEFT)), side_pack(light_hair(F.LEFT2))]
FRAMES += [F.mirror(FRAMES[4]), F.mirror(FRAMES[5])]
def tones(f): return F.tones(f)
