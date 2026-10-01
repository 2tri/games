"""야생 출현표 읽기 → work/wild.json, 그리고 '아직 포켓몬인데 풀숲·물에 나오는 칸' 우선순위
  python3 wild.py
지도 이름은 pokegold-kr 디스어셈블리(data/maps)에서 한글 지명을 가져온다. 표 위치는 롬에서 모양으로 찾는다."""
import json, os, re
import dmrom

KR = os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr')
GRASS_PCT = [30, 30, 20, 10, 5, 4, 1]          # 풀숲 7칸 확률 (data/wild/probabilities.asm)
WATER_PCT = [60, 30, 10]


def map_names():
    """(그룹, 번호) → 한글 지명"""
    consts = [l.split()[1].rstrip(',') for l in open(os.path.join(KR, 'constants/landmark_constants.asm')) if l.strip().startswith('const ')]
    lm = open(os.path.join(KR, 'data/maps/landmarks.asm')).read()
    labels = re.findall(r'^\s*landmark\s+[-\d]+,\s*[-\d]+,\s*(\w+)', lm, re.M)
    text = dict(re.findall(r'^(\w+):\s*db\s*"([^"]*)"', lm, re.M))
    ko = {c: text.get(lb, lb).replace('@', '').replace('¯', ' ') for c, lb in zip(consts, labels)}
    out, g, n = {}, 0, 0
    for l in open(os.path.join(KR, 'data/maps/maps.asm')):
        if re.match(r'^MapGroup_\w+:', l): g += 1; n = 0
        m = re.match(r'^\s*map\s+(\w+),\s*\w+,\s*\w+,\s*(\w+)', l)
        if m and g: n += 1; out[(g, n)] = (m.group(1), ko.get(m.group(2), m.group(2)))
    return out


def find_tables(d, rec, ok, minrec=8):
    """rec 바이트짜리 항목이 이어지다 FF 로 끝나는 표를 모두 찾음"""
    found, i = [], 0
    while i < len(d) - rec * minrec:
        j, k = i, 0
        while j + rec < len(d) and d[j] != 0xff and ok(d[j:j + rec]): j += rec; k += 1
        if k >= minrec and d[j] == 0xff: found.append((i, k)); i = j + 1
        else: i += 1
    return found


def main():
    r = dmrom.Rom(dmrom.default_rom()); d = bytes(r.d); names = map_names()
    sp_ok = lambda s: 1 <= s <= 251
    def grass_ok(e):
        return (e[0], e[1]) in names and all(1 <= e[5 + 2 * k] <= 100 and sp_ok(e[6 + 2 * k]) for k in range(21)) and all(e[2 + t] <= 100 for t in range(3))
    def water_ok(e):
        return (e[0], e[1]) in names and e[2] <= 100 and all(1 <= e[3 + 2 * k] <= 100 and sp_ok(e[4 + 2 * k]) for k in range(3))
    grass = find_tables(d, 47, grass_ok)
    water = find_tables(d, 9, water_ok, 4)
    seen = {}                                    # 종 → [(지명, 시간, 레벨, 확률)]
    rows = []
    for kind, tabs, rec in (('풀숲', grass, 47), ('물', water, 9)):
        for a, k in tabs:
            for i in range(k):
                e = d[a + rec * i:a + rec * (i + 1)]; key, place = names[(e[0], e[1])]
                if kind == '풀숲':
                    for t, tn in enumerate(('아침', '낮', '밤')):
                        for s in range(7):
                            lv, sp = e[5 + 14 * t + 2 * s], e[6 + 14 * t + 2 * s]
                            seen.setdefault(sp, []).append((place, kind, tn, lv, GRASS_PCT[s]))
                else:
                    for s in range(3):
                        lv, sp = e[3 + 2 * s], e[4 + 2 * s]
                        seen.setdefault(sp, []).append((place, kind, '', lv, WATER_PCT[s]))
                rows.append({'kind': kind, 'map': key, 'place': place, 'raw': e.hex()})
    orig = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(KR, 'data/pokemon/names.asm')) if 'dname' in l]
    res = []
    for sp, lst in seen.items():
        places = sorted({x[0] for x in lst}); lvs = [x[3] for x in lst]
        res.append({'no': sp, 'name': r.name(sp), 'pokemon': r.name(sp) == orig[sp - 1], 'places': places,
                    'min_lv': min(lvs), 'max_lv': max(lvs), 'weight': sum(x[4] for x in lst)})
    res.sort(key=lambda o: (o['min_lv'], -o['weight']))
    json.dump({'grass_tables': len(grass), 'water_tables': len(water), 'species': res}, open(os.path.join(dmrom.WORK, 'wild.json'), 'w'), ensure_ascii=False, indent=0)
    print('풀숲 표 %s, 물 표 %s' % ([hex(a) + '×%d' % k for a, k in grass], [hex(a) + '×%d' % k for a, k in water]))
    pk = [o for o in res if o['pokemon']]
    print('야생에 나오는 종 %d (그중 아직 포켓몬 %d)' % (len(res), len(pk)))
    for o in pk[:40]:
        print('  %3d %-6s Lv%2d~%-2d 비중%4d  %s' % (o['no'], o['name'], o['min_lv'], o['max_lv'], o['weight'], ', '.join(o['places'][:5])))


if __name__ == '__main__':
    main()
