"""디지몬 공식 한국어 도감(digimon.net/reference_ko)에서 참고 그림·프로필 모으기 → art/ref/ (저장소에 안 올림)
그림 주문 프롬프트를 쓸 때 실제 생김새(팔다리 유무·몸 구조·색)를 확인하는 용도.
  python3 tools/ref_fetch.py            # species.js 의 모든 디지몬
  python3 tools/ref_fetch.py koromon    # 몇 마리만"""
import json, os, re, sys, html, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
OUT = os.path.join(WEB, 'art', 'ref')
BASE = 'https://digimon.net'

def curl(url, path=None):
    for i in range(5):
        cmd = ['curl', '-sS', '-m', '30', url] + (['-o', path] if path else [])
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and (path is None or os.path.getsize(path) > 1000): return r.stdout
        time.sleep(2 ** i)
    raise RuntimeError('받기 실패: ' + url)

def profile(d):
    s = curl(BASE + '/reference_ko/detail.php?directory_name=' + d).decode('utf-8', 'replace')
    i = s.find('p-refDetail__content')
    if i < 0: return None
    t = re.sub(r'<script.*?</script>', '', s[i:i + 9000], flags=re.S)
    L = [l.strip() for l in html.unescape(re.sub(r'<[^>]+>', '\n', t)).split('\n') if l.strip()]
    after = lambda k: L[L.index(k) + 1] if k in L else None
    p = {'id': d, 'en': L[0], 'name': L[1] if L[1] != '다른 일러스트 보기' else L[0],
         'grade': after('등급'), 'type': after('유형'), 'attr': after('속성'), 'profile': after('프로필')}
    if p['name'] == p['en'] and len(L) > 2: p['name'] = L[2]
    return p

def main(ids):
    os.makedirs(OUT, exist_ok=True)
    js = open(os.path.join(WEB, 'species.js')).read()
    sp, _ = json.JSONDecoder().raw_decode(js[js.index('root.DigiSpecies=') + 17:])
    want = ids or list(sp)
    for k in want:
        d = sp[k]['src'] if k in sp else k
        img = os.path.join(OUT, k + '.jpg'); meta = os.path.join(OUT, k + '.json')
        if not os.path.exists(img):
            try: curl('%s/cimages/digimon/%s.jpg' % (BASE, d), img)
            except RuntimeError as ex: print('그림 없음', k, d, ex); continue
        if not os.path.exists(meta):
            p = profile(d)
            if p: json.dump(p, open(meta, 'w'), ensure_ascii=False, indent=1)
        print('ok', k, d)

if __name__ == '__main__':
    main(sys.argv[1:])
