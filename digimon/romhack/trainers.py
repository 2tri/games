"""트레이너가 데리고 있는 종 읽기 → work/trainers.json, 아직 포켓몬인 종을 쓰는 트레이너 목록
  python3 trainers.py
표 위치는 ReadTrainerParty 코드 모양으로 찾는다. 트레이너 무리 이름은 pokegold-kr 디스어셈블리에서."""
import json, os, re
import dmrom, krtext

KR = os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr')
EXTRA = {0: 0, 1: 4, 2: 1, 3: 5}          # 트레이너 종류 → 종 다음에 붙는 바이트 (기술 4 / 도구 1)


def main():
    r = dmrom.Rom(dmrom.default_rom()); d = bytes(r.d)
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(KR, 'data/trainers/party_pointers.asm')).read())
    orig = [re.search(r'dname "(.*)"', l).group(1) for l in open(os.path.join(KR, 'data/pokemon/names.asm')) if 'dname' in l]
    out = [{'group': groups[t['group']], 'name': t['name'], 'mons': [(lv, sp) for lv, sp, _ in t['mons']]} for t in r.trainers(len(groups))]
    json.dump(out, open(os.path.join(dmrom.WORK, 'trainers.json'), 'w'), ensure_ascii=False, indent=0)
    pk = [t for t in out if any(r.name(sp) == orig[sp - 1] for _, sp in t['mons'])]
    used = {}
    for t in pk:
        for lv, sp in t['mons']:
            if r.name(sp) == orig[sp - 1]: used.setdefault(sp, []).append(t['group'])
    print('트레이너 %d명, 그중 포켓몬을 데리고 있는 트레이너 %d명, 쓰이는 포켓몬 종 %d' % (len(out), len(pk), len(used)))
    for sp, gs in sorted(used.items(), key=lambda x: -len(x[1]))[:30]:
        print('  %3d %-6s %2d명  %s' % (sp, r.name(sp), len(gs), ', '.join(sorted(set(gs))[:6])))
    for t in out:
        if t['group'] in ('Falkner', 'Bugsy', 'Whitney', 'Morty', 'Chuck', 'Jasmine', 'Pryce', 'Clair', 'Rival1'):
            print('  [%s] %s: %s' % (t['group'], t['name'], ', '.join('%s Lv%d' % (r.name(sp), lv) for lv, sp in t['mons'])))


if __name__ == '__main__':
    main()
