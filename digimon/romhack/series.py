"""롬의 디지몬 칸마다 '애니 어디에 나왔나' → series.json
  python3 series.py
이름 → 공식 도감(digimon.net) 영문 디렉터리 이름 → 위키몬(wikimon.net) 문서의 Anime 절 제목들.
분류: 어드벤처(TV 1·02, 같은 시기 극장판) / 테이머즈 / 그 밖 (프런티어·세이버즈·크로스워즈 등) / 애니 없음"""
import json, os, re, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'series.json')
ADV_TV = {'Digimon Adventure', 'Digimon Adventure 02'}          # 1999·2000 TV ('Digimon Adventure:' 는 2020년판)
# 같은 시기 극장판 (우리들의 워 게임, 허리케인 상륙, 디아블로몬의 역습 등). tri.·2020·키즈나·02 The Beginning 은 뺌
ADV_MOVIE = ('Digimon Adventure (Movie)', 'Digimon Adventure: Our War Game', 'Digimon Adventure 02: Vol.', 'Digimon Adventure 02: Digimon Hurricane',
             'Digimon Adventure 02: Diablomon', 'Digimon Adventure 3D', 'Digimon Hurricane')
TAMERS = 'Digimon Tamers'
# 공식 도감 이름이 롬 이름과 달라 자동으로 못 찾은 칸 → 위키몬 문서 제목 (한국 방영판 이름 기준으로 직접 짝지음)
MANUAL = {'5': 'Greymon', '12': 'Okuwamon', '26': 'Prince Mamemon', '29': 'Dorumon', '30': 'Dorugamon', '31': 'Doruguremon',
          '32': 'Dorimon', '33': 'Raptordramon', '40': 'Holydramon', '45': 'Atlur Kabuterimon (Red)', '65': 'Kerpymon (Good)',
          '67': 'Cyberdramon', '68': 'Justimon', '102': 'Digitamamon', '130': 'Mega Seadramon', '131': 'Dolphmon', '141': 'Hi Andromon',
          '147': 'Agumon', '148': 'Geo Greymon', '149': 'Shine Greymon', '150': 'Beelzebumon: Blast Mode', '178': 'Aero V-dramon',
          '194': 'XV-mon', '195': 'Imperialdramon: Dragon Mode', '196': 'Ulforce V-dramon', '197': 'Imperialdramon: Paladin Mode',
          '225': 'Peckmon', '240': 'Petitmeramon', '248': 'Mirage Gaogamon', '250': 'Dukemon: Crimson Mode'}


def curl(url, params):
    args = ['curl', '-sS', '-m', '30', '-G', url]
    for k, v in params.items(): args += ['--data-urlencode', '%s=%s' % (k, v)]
    for i in range(4):
        r = subprocess.run(args + ['-H', 'X-Requested-With: XMLHttpRequest', '-H', 'Referer: https://digimon.net/reference_ko/'], capture_output=True, text=True)
        try: return json.loads(r.stdout)
        except Exception: time.sleep(2 ** i)
    return None


def directory(name):
    d = curl('https://digimon.net/reference_ko/request.php', {'digimon_name': name}) or {}
    rows = [x for x in d.get('rows', []) if x['name'] == name]
    return rows[0]['directory_name'] if rows else None


def anime_titles(dirname):
    """위키몬 문서의 ==Anime== 절 안 ===제목=== 들"""
    for title in (dirname, dirname.capitalize(), dirname.replace('-', ' ').title()):
        d = curl('https://wikimon.net/api.php', {'action': 'parse', 'page': title, 'prop': 'wikitext', 'format': 'json', 'redirects': '1'})
        if d and 'parse' in d:
            w = d['parse']['wikitext']['*']; page = d['parse']['title']
            m = re.search(r'^==\s*Anime\s*==\s*$(.*?)(?=^==[^=])', w, re.M | re.S)
            if not m: return page, []
            heads = re.findall(r'^===(.*?)===\s*$', m.group(1), re.M)
            titles = []
            for h in heads:
                titles += [t.split('|')[0].strip() for t in re.findall(r'\{\{hdr\|([^}]*)\}\}', h)] or [re.sub(r'[\[\]\'{}]', '', h).strip()]
            return page, titles
    d = curl('https://wikimon.net/api.php', {'action': 'opensearch', 'search': re.sub(r'_\d+$', '', dirname), 'limit': '1', 'format': 'json'})
    if d and len(d) > 1 and d[1] and d[1][0] != dirname: return anime_titles(d[1][0])
    return None, []


def classify(titles):
    if any(t in ADV_TV for t in titles): return '어드벤처'
    if any(t.startswith(ADV_MOVIE) for t in titles): return '어드벤처 극장판'
    if TAMERS in titles or any(t.startswith('Digimon Tamers') for t in titles): return '테이머즈'
    if titles: return '그 밖'
    return '애니 없음'


def main():
    G = json.load(open(os.path.join(HERE, 'grades.json')))
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    out = {}
    for k, v in G.items():
        if k in old and old[k].get('page'):
            out[k] = dict(old[k], series=classify(old[k]['anime'])); continue
        nm = v.get('dex') or v['name']
        dn = MANUAL.get(k) or directory(nm)
        page, titles = anime_titles(dn) if dn else (None, [])
        out[k] = {'name': v['name'], 'dex': v.get('dex'), 'dir': dn, 'page': page, 'anime': titles, 'series': classify(titles) if page else '모름'}
        print(k, v['name'], dn, page, out[k]['series'])
        json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
    json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
    from collections import Counter
    print(Counter(o['series'] for o in out.values()))


if __name__ == '__main__':
    main()
