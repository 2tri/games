"""20판 검수 페이지 만들기: 디지몬마다 칸을 나눠, 후보 그림 중 맞는 것을 사람이 고르는 HTML (아티팩트용).
python3 picker.py [출력.html]   → 기본 work/picker.html
칸 = 롬 안의 모든 종. 후보 = 현재 롬 그림 / 이전 그림(art_bak) / DS 원본(위키몬, 현재가 DS 변환이 아닐 때만).
고른 결과는 페이지 db(picks/<id>) 에 저장 → 세션이 읽어서 반영 (적용은 apply_picks.py)."""
import os, sys, json, glob, base64, io
import numpy as np
from PIL import Image
import dmrom, rules

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
ART, BAK = os.path.join(WEB, 'art'), os.path.join(WEB, 'art_bak')
IMG = os.path.join(os.path.dirname(WEB), 'images', 'digimon')
EXTRA_ID = {'아르케니몬': 'arachnemon', '블랙워그몬': 'blackwargreymon', '다크티라몬': 'darktyranomon', '로제몬': 'rosemon'}      # 롬 이름과 art id 가 다른 종
JUST_REFETCHED = {'drimogemon', 'darklizamon', 'ankylomon', 'minomon'}                  # 19판: 위키몬에서 올바른 페이지로 다시 받은 종
NOT_FOUND = {'플롯트몬', '다이버몬', '스콜피오몬', '트리케라몬', '브이몬', '데이터몬', '엑스브이몬', '황제드라몬', '왕개굴몬', '지로몬'}      # 위키몬에서 못 찾음
GRADES = ['유년기Ⅰ', '유년기Ⅱ', '성장기', '성숙기', '완전체', '궁극체', '아머체', '기타']


def uri(im):
    """PIL → data URI (작은 PNG). 투명은 흰색으로 깔아 둠"""
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert('RGB')
    try: im = im.convert('P', palette=Image.ADAPTIVE, colors=32)
    except Exception: pass
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), im.size


def file_uri(p):
    return uri(Image.open(p)) if os.path.exists(p) else (None, None)


def same(a, b):
    if not (os.path.exists(a) and os.path.exists(b)): return False
    return open(a, 'rb').read() == open(b, 'rb').read()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(dmrom.WORK, 'picker.html')
    sl = json.load(open(os.path.join(HERE, 'slots.json'), encoding='utf-8'))['mons']
    am = json.load(open(os.path.join(HERE, 'order', 'allmons.json'), encoding='utf-8'))
    name2id = dict(EXTRA_ID)
    for tab in ('REDRAW', 'FRONT_ONLY', 'BACK_ONLY', 'FRONT_ART_BIG_BACK'):
        for nm, i in getattr(rules, tab, {}).items(): name2id.setdefault(nm, i)
    for x in sl: name2id.setdefault(x['name'], x['id'])
    for x in am:
        if x.get('id'): name2id.setdefault(x['ko'], x['id'])
    try:
        import ingest
        grade_of = ingest.grade_of
    except Exception: grade_of = lambda i: None
    try:
        import wikimon_ds as W
        EN, FIX, TIT = W.EN, W.FIX_TITLE, W.TITLE
    except Exception: EN, FIX, TIT = {}, {}, {}
    r = dmrom.Rom(os.path.join(dmrom.WORK, 'myver.gbc'))
    mons = [n for n in range(1, dmrom.NUM + 1) if r.name(n) != rules.EMPTY_NAME and not r.name(n).startswith('-') and n != 201]
    rows = []
    for n in mons:
        ko = r.name(n); did = name2id.get(ko)
        c1, c2 = r.palette(n)
        pal = np.array([(255, 255, 255), c1, c2, (0, 0, 0)], np.uint8)
        tiles = []
        cf, cb = [], []
        for back in (False, True):
            a = r.pic(n, back=back)
            u, sz = uri(Image.fromarray(pal[a]))
            (cb if back else cf).extend([u, sz[0], sz[1]])
        ds_f = os.path.join(IMG, '%s-ds-f.png' % did) if did else ''
        bak_f = os.path.join(BAK, '%s-f.png' % did) if did else ''
        art_f = os.path.join(ART, '%s-f.png' % did) if did else ''
        from_ds = bool(did) and os.path.exists(ds_f) and os.path.exists(art_f) and not same(art_f, bak_f)      # DS 가 있고 art 가 이전(bak)과 다르면 DS 변환본 (bak 없는 새 art 도 포함)
        tiles.append({'k': 'cur', 'label': '현재 롬 그림' + (' (DS 변환)' if from_ds else ''), 'f': cf, 'b': cb})
        if did and os.path.exists(bak_f) and not same(art_f, bak_f):
            f, fs = file_uri(bak_f); b, bs = file_uri(os.path.join(BAK, '%s-b.png' % did))
            tiles.append({'k': 'bak', 'label': '이전 그림 (DS 적용 전)', 'f': [f, fs[0], fs[1]], 'b': [b, bs[0], bs[1]] if b else None})
        if did and os.path.exists(ds_f) and not from_ds:
            f, fs = file_uri(ds_f); b, bs = file_uri(os.path.join(IMG, '%s-ds-b.png' % did))
            tiles.append({'k': 'ds', 'label': 'DS 원본 (위키몬)', 'f': [f, fs[0], fs[1]], 'b': [b, bs[0], bs[1]] if b else None})
        title = FIX.get(ko) or TIT.get(EN.get(ko, ''), '') or (EN.get(ko, '') or '').replace(' ', '_')
        flag = ''
        if did in JUST_REFETCHED: flag = '방금 위키몬에서 다시 받음'
        elif ko in NOT_FOUND: flag = '위키몬에서 못 찾음'
        rows.append({'n': n, 'ko': ko, 'id': did or ('slot%d' % n), 'grade': ((grade_of(did) if did else None) or '기타').replace('유아기', '유년기'), 'tiles': tiles, 'wiki': title, 'flag': flag})
    rows.sort(key=lambda x: (GRADES.index(x['grade']) if x['grade'] in GRADES else 99, x['n']))
    tpl = open(os.path.join(HERE, 'picker_tpl.html'), encoding='utf-8').read()
    html = tpl.replace('/*DATA*/[]', json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    open(out, 'w', encoding='utf-8').write(html)
    print('%s (%d종, %.0f KB)' % (out, len(rows), len(html) / 1024))


if __name__ == '__main__':
    main()
