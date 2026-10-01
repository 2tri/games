"""롬의 디지몬 칸마다 공식 세대(유년기~궁극체) → grades.json (포획 규칙에 씀)
  python3 grades.py            # work/base.gbc 기준으로 다시 만듦
이미 있는 grades.json 은 '이름 → 세대' 기억으로 쓴다 → 손으로 채운 값(src: manual)이 판이 바뀌어도(2.0판) 이어짐.
처음 보는 이름만 디지몬 공식 한국어 도감(digimon.net/reference_ko) 검색으로 찾는다. 같은 이름이 없으면 None (patch.py 가 진화 줄로 판단)."""
import json, os, re, subprocess, time
import dmrom

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'grades.json')
KR = os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr')


def search(q):
    for i in range(5):
        r = subprocess.run(['curl', '-sS', '-m', '25', '-G', 'https://digimon.net/reference_ko/request.php', '--data-urlencode', 'digimon_name=' + q,
                            '-H', 'X-Requested-With: XMLHttpRequest', '-H', 'Referer: https://digimon.net/reference_ko/'], capture_output=True, text=True)
        try: return (json.loads(r.stdout) or {}).get('rows', [])
        except Exception: time.sleep(2 ** i)
    return []


def main():
    r = dmrom.Rom(dmrom.default_rom())
    names_asm = os.path.join(KR, 'data/pokemon/names.asm')
    orig = [re.search(r'dname "(.*)"', l).group(1) for l in open(names_asm) if 'dname' in l]
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    memo = {v['name']: v for v in old.values()}
    out = {}
    for no in range(1, dmrom.NUM + 1):
        nm = r.name(no)
        if nm == orig[no - 1]: continue                    # 아직 포켓몬인 칸
        if nm in memo: out[str(no)] = memo[nm]; continue
        rows = search(nm)
        exact = [x for x in rows if x['name'] == nm]
        out[str(no)] = {'name': nm, 'grade': exact[0]['level'] if exact else None, 'dex': exact[0]['name'] if exact else None,
                        'cands': ['%s/%s' % (x['name'], x['level']) for x in rows[:5]]}
        print(no, nm, out[str(no)]['grade'])
    json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
    print('디지몬 칸 %d, 세대 모름 %d → %s' % (len(out), sum(v['grade'] is None for v in out.values()), OUT))


if __name__ == '__main__':
    main()
