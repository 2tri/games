"""어드벤처(54화)·02(50화)·같은 시기 극장판에 나온 디지몬 목록 → adventure_digimon.json
위키몬 에피소드 문서의 =Characters= 절에 있는 {{Ch2|이름}} 을 모은다. 등급 칸(b 유년기, c 성장기, a 성숙기, p 완전체, u 궁극체 …)도 함께."""
import json, os, re, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
def parse(page):
    a = ['curl', '-sS', '-m', '40', '-G', 'https://wikimon.net/api.php']
    for k, v in {'action': 'parse', 'page': page, 'prop': 'wikitext', 'format': 'json', 'redirects': '1'}.items(): a += ['--data-urlencode', '%s=%s' % (k, v)]
    for i in range(4):
        try:
            d = json.loads(subprocess.run(a, capture_output=True, text=True).stdout)
            return d['parse']['wikitext']['*'] if 'parse' in d else None
        except Exception: time.sleep(2 ** i)
pages = ['Digimon Adventure - Episode %02d' % i for i in range(1, 55)] + ['Digimon Adventure 02 - Episode %02d' % i for i in range(1, 51)]
pages += ['Digimon Adventure (Movie)', 'Digimon Adventure: Our War Game!', 'Digimon Adventure 02: Vol. 1: Digimon Hurricane Landing!!/Vol. 2: Transcendent Evolution!! The Golden Digimentals', 'Digimon Adventure 02: Diablomon Strikes Back']
out = {}
for p in pages:
    w = parse(p)
    if not w: print('없음', p); continue
    m = re.search(r'^=\s*Characters\s*=\s*$(.*?)(?=^=[^=])', w, re.M | re.S)
    body = m.group(1) if m else w
    for lv, names in re.findall(r'\|(\w+)=((?:\{\{Ch2\|[^}]*\}\}[,\s]*)+)', body):
        for n in re.findall(r'\{\{Ch2\|([^}|]*)', names):
            e = out.setdefault(n.strip(), {'lv': set(), 'eps': []}); e['lv'].add(lv); e['eps'].append(p.replace('Digimon Adventure', 'DA'))
    print(p, len(out), flush=True)
json.dump({k: {'lv': sorted(v['lv']), 'first': v['eps'][0], 'n': len(v['eps'])} for k, v in sorted(out.items())},
          open(os.path.join(HERE, 'adventure_digimon.json'), 'w'), ensure_ascii=False, indent=0)
print('합계', len(out))
