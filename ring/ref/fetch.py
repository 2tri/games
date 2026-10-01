import json, sys, urllib.parse, urllib.request, os
UA = "RingFanGameResearch/0.1 (personal non-commercial)"
API = "https://lotr.fandom.com/api.php"
def q(**p):
    p.setdefault('format', 'json')
    u = API + '?' + urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA}), timeout=30))
def images(title, n=200):
    d = q(action='query', titles=title, prop='images', imlimit=n, redirects=1)
    out = []
    for pg in d['query']['pages'].values():
        out += [i['title'] for i in pg.get('images', [])]
    return [t for t in out if t.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
def info(files, w=240):
    res = {}
    for i in range(0, len(files), 40):
        d = q(action='query', titles='|'.join(files[i:i + 40]), prop='imageinfo', iiprop='url|size', iiurlwidth=w)
        for pg in d['query']['pages'].values():
            ii = pg.get('imageinfo')
            if ii: res[pg['title']] = ii[0]
    return res
if __name__ == '__main__':
    name, title = sys.argv[1], sys.argv[2]
    fs = images(title)
    inf = info(fs)
    os.makedirs('cand/' + name, exist_ok=True)
    meta = []
    for k, (f, ii) in enumerate(inf.items()):
        p = f'cand/{name}/{k:02d}.jpg'
        try:
            data = urllib.request.urlopen(urllib.request.Request(ii['thumburl'], headers={'User-Agent': UA}), timeout=30).read()
            open(p, 'wb').write(data); meta.append({'i': k, 'file': f, 'url': ii['url'], 'w': ii['width'], 'h': ii['height']})
        except Exception as e:
            print('fail', f, e)
    json.dump(meta, open(f'cand/{name}/meta.json', 'w'), ensure_ascii=False, indent=1)
    print(name, len(meta))
