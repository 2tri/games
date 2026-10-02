"""디지몬스터 그림 주문서 · 모음 페이지 만들기 → work/디지몬_그림주문서.html (아티팩트로 올림)
지금 롬 그림(work/sp/번호-f.png·-b.png)은 롬에서 뽑아 work/ 에만 둔다."""
import json, base64, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(os.path.dirname(HERE)) + '/'
R = HERE + '/'                                   # order_tpl.html, keep.json, needs.json 이 있는 곳
SP = os.environ.get('ORDER_OUT', WEB + 'romhack/work/')   # 결과 HTML 은 롬 그림이 들어 있으므로 work/ (저장소에 안 올림)
sys.path.insert(0, WEB + 'romhack')
import dmrom
rom = dmrom.Rom(dmrom.WORK + '/myver.gbc')
S = json.load(open(WEB + 'romhack/series.json')); G = json.load(open(WEB + 'romhack/grades.json'))
keep = json.load(open(R + 'keep.json'))
KD = {int(a): b for a, b in json.load(open(R + 'keep_dirs.json')).items()}
needs = json.load(open(R + 'needs.json')) if os.path.exists(R + 'needs.json') else {}

def b64(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode() if os.path.exists(p) else ''

# ── 주문 (v3: 화풍만 바꾸는 「스타일 변환」, 앞·뒤 따로, 회색 4톤) ── 종별 값은 specs.py
import specs
LCD = json.load(open(R + 'lcd.json')) if os.path.exists(R + 'lcd.json') else {}
SERIES = {'qinglongmon': 'Digimon Adventure 02'}

def lst(xs): return '\n'.join('%d. %s' % (i + 1, x) for i, x in enumerate(xs))
def dash(xs): return '\n'.join('- ' + x for x in xs)
def tones(e):
    t = e['tones']
    return (f"  - white = {t['white']}\n  - light gray = {t['light']}\n  - dark gray = {t['dark']}\n  - black = outline, {t['black']}")

def front_prompt(e):
    lcd = ("The second attached image is its original LCD sprite from the Digimon virtual pet toys. Follow that silhouette and those proportions "
           "(only the silhouette; the size and facing below still apply).\n") if e['id'] in LCD_OF else ''
    return (f"This is {e['ko']} ({e['en']}), a Digimon from {SERIES.get(e['id'], 'Digimon Adventure')}. It is NOT any other creature. "
            f"Keep this exact character: same species, same silhouette, same proportions, same parts.\n{lcd}\n"
            "Task: convert the attached picture into a late-1990s Game Boy Color monster RPG battle sprite (FRONT view). Change only the art style, never the design.\n\n"
            "Composition:\n- ONE square image, pure white background, nothing else.\n"
            "- The character faces slightly to the left (3/4 view), whole body visible, standing on the bottom edge, filling about 90% of the image height.\n\n"
            f"Style:\n- VERY low resolution: the character is only about {specs.px(e['grade'])} pixels tall. Use big chunky pixels; every pixel is a crisp square of the same size. "
            "No anti-aliasing, no blur, no gradients, no dithering, no ground shadow.\n"
            "- Simplify like a real 8-bit sprite: strong silhouette, thick black outline, big flat shapes. Drop small details.\n"
            "- Exactly 4 tones, GRAYSCALE only: white, light gray, dark gray, black. No colors.\n" + tones(e) + "\n\n"
            f"MUST KEEP (most important first):\n{lst(e['keep'])}\n\nMUST NOT:\n{dash(e['not_'])}\n\n"
            "No text, no frame, no grid lines, no background scenery.")

def back_prompt(e):
    return (f"Attached: (1) the official picture of {e['ko']} ({e['en']}), a Digimon, and (2) the FRONT sprite I already accepted. "
            "Draw the BACK sprite of the SAME character in the SAME pixel style and the SAME 4 gray tones.\n\n"
            "View: three-quarter REAR view, like a monster standing in front of the player in a Game Boy battle. The camera is behind and a little above it. "
            "The character faces AWAY toward the upper-right corner, so we see its back, its right shoulder and right arm, and a thin sliver of the right side of its head. "
            "NOT straight from behind, NOT symmetrical, NOT a mirror of the front.\n\n"
            "Composition: ONE square image, pure white background. Only the upper body and head; the lower body is cut off by the bottom edge. "
            "The character fills about 90% of the image width, about 45 pixels wide.\n\n"
            "Style: same as the front: big chunky pixels, crisp squares, thick black outline, no anti-aliasing, no gradients, no dithering. "
            "Exactly 4 tones (white, light gray, dark gray, black), same part-to-tone mapping as the front:\n" + tones(e) + "\n\n"
            f"MUST KEEP from behind:\n{lst(e['keep_back'])}\n\n"
            f"MUST NOT:\n- Do not show the face from the front.\n- Do not make it symmetrical.\n{dash(e.get('not_back', []) + e['not_'])}\n\n"
            "No text, no frame, no grid lines, no background.")

def flat_prompt(e):
    return (f"This is {e['ko']} ({e['en']}), a Digimon. It is NOT any other creature. Keep this exact character.\n"
            "Redraw the attached picture as a simple flat cartoon illustration: thick black outline, flat fills, no shading gradients, no texture, "
            "no background, pure white background.\n"
            "Use only 4 tones, GRAYSCALE: white, light gray, dark gray, black.\n" + tones(e) + "\n"
            "Front view, 3/4 facing left, whole body, standing on the bottom edge, filling 90% of a square image.\n"
            "Simplify small details away; keep the big shapes only.\n\n"
            f"MUST KEEP (most important first):\n{lst(e['keep'])}\n\nMUST NOT:\n{dash(e['not_'])}")

LCD_OF = {s['id']: LCD[s['wiki']]['url'] for s in specs.S if s.get('wiki') in LCD and LCD[s['wiki']].get('url')}
TIER = {1: '1 · 지금 막힌 것', 2: '2 · 보스·암흑단·암흑 진화', 3: '3 · 갈래·유아기', 0: '후보 · 계획 결정 뒤'}
ess = []
dv = specs.DIGIVICE
ess.append({'id': 'digivice', 'ko': dv['ko'], 'en': dv['en'], 'grade': dv['grade'], 'tier': 1, 'use': dv['use'], 'size': '16×16', 'done': True,
            'got': {'f': b64(WEB + 'art/digivice.png')}, 'img': '', 'ref': 'https://wikimon.net/Digivice', 'lcd': ''})
for e in specs.S:
    p = {'f': front_prompt(e), 'b': back_prompt(e), 'flat': flat_prompt(e)}
    for k, v in p.items():
        assert 'pokemon' not in v.lower() and 'pokémon' not in v.lower(), (e['id'], k)
    got = {s: b64(WEB + 'art/%s-%s.png' % (e['id'], s)) for s in ('f', 'b') if os.path.exists(WEB + 'art/%s-%s.png' % (e['id'], s))}
    ess.append({'id': e['id'], 'ko': e['ko'], 'en': e['en'], 'grade': e['grade'], 'tier': e['tier'], 'use': e['use'],
                'size': '앞 약 %dpx · 뒤 약 45px' % specs.px(e['grade']), 'pal': [list(c) for c in e['pal']],
                'img': 'https://digimon.net/cimages/digimon/%s.jpg' % e['dir'], 'ref': 'https://digimon.net/reference_ko/detail.php?directory_name=' + e['dir'],
                'lcd': LCD_OF.get(e['id'], ''), 'prompt': p, 'got': got, 'front_done': bool(e.get('front_done'))})
TIERS = TIER

# ── 지금 롬 ──
REC = {4: '뒷모습이 머리만 남은 덩어리', 7: '뒷모습 모양이 어색함', 16: '뒷모습이 뭉개짐', 6: '색이 빠져 갑옷이 구분 안 됨',
       10: '색이 실제(노란 몸·빨강 검정 줄무늬)와 다름', 12: '회색 (실제는 검정·빨강)', 25: '뒷모습이 잘림', 74: '너무 작고 흐림',
       102: '뒷모습이 알 껍질만', 116: '뒷모습이 너무 작음', 126: '뒷모습이 노란 덩어리', 135: '뒷모습이 깨져 보임',
       172: '뒷모습이 잘림', 173: '너무 작고 흐림', 175: '너무 크고 얼굴이 잘림', 186: '뒷모습이 너무 작음'}
NEW = {161: '받은 그림으로 넣음', 212: '받은 그림으로 넣음', 217: '물음표 알 (필수 목록에서 주문)'}
romlist = []
for n in keep:
    g = (G.get(str(n)) or {}).get('grade') or {161: '유년기Ⅱ', 212: '완전체', 217: '완전체'}.get(n, '')
    romlist.append({'id': 'rom-%d' % n, 'no': n, 'ko': rom.name(n), 'grade': g, 'rec': REC.get(n, ''), 'note': NEW.get(n, ''),
                    'f': b64(SP + 'sp/%d-f.png' % n), 'b': b64(SP + 'sp/%d-b.png' % n),
                    'img': ('https://digimon.net/cimages/digimon/%s.jpg' % KD[n]) if KD.get(n) else '', 'ref': ('https://digimon.net/reference_ko/detail.php?directory_name=' + KD[n]) if KD.get(n) else ''})

# ── 빠지는 것 ──
drop = {'테이머즈': [], '그 밖의 작품': [], '애니에 안 나옴': [], '확인 안 됨': []}
for k, v in S.items():
    n = int(k)
    if n in keep: continue
    s = v['series']
    key = '테이머즈' if s == '테이머즈' or n in (152, 153, 154, 63, 64) else '그 밖의 작품' if s == '그 밖' else '애니에 안 나옴' if s == '애니 없음' else '확인 안 됨' if s == '모름' else None
    if key: drop[key].append(v['name'])

# ── 나중에 ──
essen = {e['dir'] for e in specs.S}
later = []
for k, v in needs.items():
    if not v.get('name') or v.get('dir') in essen: continue
    later.append({'id': 'need-' + re.sub(r'[^a-z0-9]', '', k.lower()), 'ko': v['name'], 'en': k, 'grade': v.get('grade') or '', 'n': v['n'],
                  'img': ('https://digimon.net/cimages/digimon/%s.jpg' % v['dir']) if v.get('dir') else '', 'ref': ('https://digimon.net/reference_ko/detail.php?directory_name=' + v['dir']) if v.get('dir') else '',
                  'first': v['first'].replace('DA 02 - Episode ', '02 ').replace('DA - Episode ', '어드벤처 ').replace('DA 02:', '02 극장판').replace('DA:', '극장판').replace('DA (Movie)', '극장판')})
ORDER = ['유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '성장기', '아머체', '성숙기', '완전체', '궁극체', '']
later.sort(key=lambda x: (ORDER.index(x['grade']) if x['grade'] in ORDER else 8, -x['n']))
unnamed = [k for k, v in needs.items() if not v.get('name')]

DATA = {'tiers': TIERS, 'ess': ess, 'rom': romlist, 'drop': drop, 'later': later, 'unnamed': unnamed,
        'koromon': {'f': b64(WEB + 'art/koromon-f.png'), 'b': b64(WEB + 'art/koromon-b.png')}}
tpl = open(R + 'order_tpl.html').read()
html = tpl.replace('/*DATA*/null', json.dumps(DATA, ensure_ascii=False))
# 제목 글꼴: 페이지에 쓰인 글자만
text = re.sub(r'<[^>]+>', '', re.sub(r'<style>.*?</style>|<script>.*?</script>', '', tpl, flags=re.S)) + json.dumps([e['ko'] for e in ess] + list(TIERS.values()) + ['필수', '지금 롬에 있는 디지몬', '나중에', '빠지는 디지몬', '모음', '그림 주문서'], ensure_ascii=False)
open(SP + 'chars.txt', 'w').write(''.join(sorted(set(text) | set('0123456789/ ·()×'))))
subprocess.run(['pyftsubset', WEB + 'Galmuri9.woff2', '--text-file=' + SP + 'chars.txt', '--flavor=woff2', '--output-file=' + SP + 'g.woff2'], check=True)
html = html.replace('__GALMURI__', base64.b64encode(open(SP + 'g.woff2', 'rb').read()).decode())
os.makedirs(SP, exist_ok=True); open(SP + '디지몬_그림주문서.html', 'w').write(html)
print('필수', len(ess), '롬', len(romlist), '나중', len(later), '이름 없음', len(unnamed), '크기', len(html))
