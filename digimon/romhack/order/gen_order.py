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
needs = json.load(open(R + 'needs.json')) if os.path.exists(R + 'needs.json') else {}

def b64(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode() if os.path.exists(p) else ''

# ── 필수 ──
ESS = [
 # id, 이름, 영문(검색), 등급, 쓰임, 몸 색(밝은, 어두운), 특징, 공식 도감 디렉터리
 ('digivice', '디지바이스', 'Digivice (Digimon Adventure)', '도구', '공박사 연구소에서 볼 대신 탁자 위에 놓고 고르는 스타팅 선택 물건', ('light gray', 'dark gray'),
  '', ''),
 ('metalgreymon', '메탈그레이몬', 'MetalGreymon', '완전체', '그레이몬 → (용기 문장) → 메탈그레이몬 → 워그레이몬. 지금은 물음표 알', ('orange', 'steel blue-gray'),
  'orange dinosaur with blue stripes, a silver metal helmet covering the upper face with one horn, a huge silver metal LEFT arm with three long claws, a metal chest plate with a hatch, torn purple bat-like wings on the back', 'metalgreymon-v'),
 ('weregarurumon', '워가루몬', 'WereGarurumon', '완전체', '가루몬 → (우정 문장) → 워가루몬 → 메탈가루몬. 지금은 물음표 알', ('light blue', 'dark blue'),
  'a muscular werewolf standing upright, white-and-blue striped fur and a blue mane, ripped blue jeans, brown leather belts and a shoulder strap with a spiked shoulder pad, bandaged fists, big claws', 'weregarrumon'),
 ('tunomon', '뿔몬', 'Tsunomon', '유년기Ⅱ', '29~32번 도로의 흔한 야생 (지금 러브리몬 자리) → 파피몬', ('orange-brown', 'dark brown'),
  'a small round furry blob, orange-brown fur on top and back, a white face, ONE long curved horn on top of the head, red eyes, pink cheeks. No arms, no legs', 'tunomon'),
 ('tokomon', '토코몬', 'Tokomon', '유년기Ⅱ', '29~31번 도로 밤 야생 (지금 팔코몬 자리) → 파닥몬', ('light pink', 'red'),
  'a tiny white round marshmallow-like creature, two very short stubby feet and two tiny arms, two long thin ear-like feelers on top, small red eyes, a small mouth', 'tokomon'),
 ('pyocomon', '어니몬', 'Yokomon (Pyocomon)', '유년기Ⅱ', '32·33번 도로 야생 (지금 통통코=포켓몬) → 피요몬', ('pink', 'blue'),
  'a pale pink onion-bulb shaped body, a big blue flower on top of the head with a curly stamen, small eyes, a few tiny root stubs under the body. No arms, no legs', 'pyocomon'),
 ('mochimon', '모티몬', 'Motimon', '유년기Ⅱ', '32번 도로 야생 (지금 메리프=포켓몬) → 텐타몬', ('light pink', 'dark pink'),
  'a soft pink rice-cake (mochi) creature shaped like a little ghost, two stubby arms with tiny dark claws, wavy bottom edge with NO legs, big round black eyes, an open happy mouth', 'mochimon'),
 ('tanemon', '시드몬', 'Tanemon', '유년기Ⅱ', '너도밤나무 숲 야생 (지금 파라스=포켓몬) → 팔몬', ('light green', 'dark green'),
  'an onion-bulb body, green on top and a cream face, big eyes, small cat-like mouth, long green leaves sprouting from the top of the head, four tiny root-like feet. No arms', 'tanemon'),
 ('pukamon', '둥실몬', 'Bukamon (Pukamon)', '유년기Ⅱ', '낚시로 만남 (지금 콘치=포켓몬) → 쉬라몬', ('light gray', 'orange-red'),
  'a small floating seal-like baby, gray body with a white belly, a flame-shaped orange-red tuft of hair on top of the head, two small front flippers, a long fish-like tail with a fin. No legs', 'pukamon'),
 ('gazimon', '가지몬', 'Gazimon', '성장기', '어둠의 동굴 야생 (지금 노고치=포켓몬)', ('light gray', 'dark purple-gray'),
  'a small gray rabbit-like Digimon standing on two legs, long pointed ears with dark stripes, sharp red eyes, a sly grin, long sharp claws on both hands', 'gazimon'),
 ('bakemon', '고스몬', 'Bakemon', '성숙기', '모다피의 탑·밤 길 트레이너 (지금 임프몬=테이머즈 자리)', ('light gray', 'red'),
  'a floating ghost wrapped in a white sheet like a hooded cloak, a dark face opening with glowing eyes and a toothy mouth, two clawed hands sticking out of the sheet, the bottom of the sheet ends in a wavy tail. No legs', 'bakemon'),
 ('kuwagamon', '쿠가몬', 'Kuwagamon', '성숙기', '초반 벌레잡이 트레이너·우두머리 (애니 1화의 첫 적)', ('red', 'dark gray'),
  'a red giant stag beetle standing upright, two huge red pincers on its head with jagged white inner edges, a mouth full of teeth between them, four thin red arms with claws, insect wings', 'kuwagamon'),
 ('shellmon', '쉘몬', 'Shellmon', '성숙기', '낚시꾼·물가 트레이너, 해변 우두머리', ('pink', 'blue-gray'),
  'a pink dinosaur-like sea creature crawling low on four short legs, green seaweed-like hair, a big gray-blue spiked conch shell carried on its BACK like a hermit crab, small eyes, an open mouth', 'shellmon'),
 ('monochromon', '모노크로몬', 'Monochromon', '성숙기', '등산가 트레이너 (지금 롱스톤=포켓몬)', ('light gray', 'dark gray'),
  'a gray armored triceratops-like dinosaur on four legs, one long black horn on its nose, gray and black armor plates on its back and head frill', 'monochromon'),
 ('numemon', '워매몬', 'Numemon', '성숙기', '초반 트레이너 (지금 질퍽이=포켓몬), 실패 진화', ('yellow-green', 'purple'),
  'a green slug with two long eye stalks topped with big bloodshot eyes, a huge open mouth with big white teeth and a pink tongue sticking out, purple spots. No arms, no legs', 'numemon'),
 ('seadramon', '시드라몬', 'Seadramon', '성숙기', '낚시꾼·바다 트레이너 (지금 콘치 진화형=포켓몬)', ('yellow', 'teal'),
  'a long teal sea serpent with a yellow armored mask over its face, blue eyes, a red fin at the tail tip, the body coils in an S shape. No arms, no legs', 'seadramon'),
 ('centalmon', '켄터스몬', 'Centarumon', '성숙기', '초반 트레이너 (지금 켄타로스=포켓몬)', ('light brown', 'blue'),
  'a centaur: an armored humanoid upper body with blue armor plates and a helmet with ONE eye, an arm cannon on one arm, a brown horse-like lower body with four legs', 'centalmon'),
]

def front_size(grade):
    return 40 if grade.startswith(('유아기', '유년기')) else 48 if grade == '성장기' else 56

def prompt(e):
    did, ko, en, grade, use, (c1, c2), feat, _ = e
    if did == 'digivice':
        return ("Use the attached picture of the Digivice from Digimon Adventure (1999) as the reference. "
                "Redraw it as a tiny Game Boy Color overworld object sprite in the style of Pokemon Gold/Silver "
                "(like the Poke Ball item lying on the ground): the device lying on a table, seen from slightly above.\n"
                "- ONE image, square, pure white background. The sprite is a 16x16 pixel grid, enlarged so every pixel is a crisp square of the same size.\n"
                "- Exactly 4 colors: white, light gray, dark gray, and a black 1-pixel outline.\n"
                "- Keep the round screen, the white body and the small buttons recognizable at this tiny size.\n"
                "- No text, no frame, no grid lines, no shadow, no background.")
    F = front_size(grade)
    return (f"Use the attached official picture of {en} ({ko}) as the reference. Redraw it as a Game Boy Color battle sprite "
            f"in the style of Pokemon Gold/Silver.\n"
            f"Output ONE wide image (2:1), pure white background, two sprites side by side with empty white space between them:\n"
            f"- LEFT: FRONT sprite on a {F}x{F} pixel grid. The Digimon faces slightly to the left (3/4 view), whole body visible, standing on the bottom edge.\n"
            f"- RIGHT: BACK sprite on a 48x48 pixel grid. The same Digimon seen from behind and slightly above, facing up-right; the lower body may be cut off by the bottom edge.\n"
            f"- Real pixel art: every pixel is a crisp square of the same size, enlarged evenly. No anti-aliasing, no blur, no gradients, no dithering, no drop shadow.\n"
            f"- Exactly 4 colors: white, a black 1-pixel outline (around the body and on the main inner lines), {c1} (light) and {c2} (dark). Small details also use only these 4 colors.\n"
            f"- Keep these features from the picture: {feat}.\n"
            f"- No text, no frame, no grid lines, no background scenery.")

ess = []
for e in ESS:
    did, ko, en, grade, use, cols, feat, dirn = e
    got = {}
    for side in ('f', 'b'):
        p = WEB + 'art/%s-%s.png' % (did, side)
        if os.path.exists(p): got[side] = b64(p)
    ess.append({'id': did, 'ko': ko, 'en': en, 'grade': grade, 'use': use, 'size': '16×16' if did == 'digivice' else '%d×%d · 48×48' % (front_size(grade), front_size(grade)),
                'ref': ('https://digimon.net/reference_ko/detail.php?directory_name=' + dirn) if dirn else '', 'prompt': prompt(e), 'got': got})

# ── 지금 롬 ──
REC = {4: '뒷모습이 머리만 남은 덩어리', 7: '뒷모습 모양이 어색함', 16: '뒷모습이 뭉개짐', 6: '색이 빠져 갑옷이 구분 안 됨',
       10: '색이 실제(노란 몸·빨강 검정 줄무늬)와 다름', 12: '회색 (실제는 검정·빨강)', 25: '뒷모습이 잘림', 74: '너무 작고 흐림',
       102: '뒷모습이 알 껍질만', 116: '뒷모습이 너무 작음', 126: '뒷모습이 노란 덩어리', 135: '뒷모습이 깨져 보임',
       172: '뒷모습이 잘림', 173: '너무 작고 흐림', 175: '너무 크고 얼굴이 잘림', 186: '뒷모습이 너무 작음'}
NEW = {161: '받은 그림으로 넣음', 212: '물음표 알 (필수 목록에서 주문)', 217: '물음표 알 (필수 목록에서 주문)'}
romlist = []
for n in keep:
    g = (G.get(str(n)) or {}).get('grade') or {161: '유년기Ⅱ', 212: '완전체', 217: '완전체'}.get(n, '')
    romlist.append({'id': 'rom-%d' % n, 'no': n, 'ko': rom.name(n), 'grade': g, 'rec': REC.get(n, ''), 'note': NEW.get(n, ''),
                    'f': b64(SP + 'sp/%d-f.png' % n), 'b': b64(SP + 'sp/%d-b.png' % n)})

# ── 빠지는 것 ──
drop = {'테이머즈': [], '그 밖의 작품': [], '애니에 안 나옴': [], '확인 안 됨': []}
for k, v in S.items():
    n = int(k)
    if n in keep: continue
    s = v['series']
    key = '테이머즈' if s == '테이머즈' or n in (152, 153, 154, 63, 64) else '그 밖의 작품' if s == '그 밖' else '애니에 안 나옴' if s == '애니 없음' else '확인 안 됨' if s == '모름' else None
    if key: drop[key].append(v['name'])

# ── 나중에 ──
essen = {e[7] for e in ESS}
later = []
for k, v in needs.items():
    if not v.get('name') or v.get('dir') in essen: continue
    later.append({'id': 'need-' + re.sub(r'[^a-z0-9]', '', k.lower()), 'ko': v['name'], 'en': k, 'grade': v.get('grade') or '', 'n': v['n'],
                  'first': v['first'].replace('DA 02 - Episode ', '02 ').replace('DA - Episode ', '어드벤처 ').replace('DA 02:', '02 극장판').replace('DA:', '극장판').replace('DA (Movie)', '극장판')})
ORDER = ['유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '성장기', '아머체', '성숙기', '완전체', '궁극체', '']
later.sort(key=lambda x: (ORDER.index(x['grade']) if x['grade'] in ORDER else 8, -x['n']))
unnamed = [k for k, v in needs.items() if not v.get('name')]

DATA = {'ess': ess, 'rom': romlist, 'drop': drop, 'later': later, 'unnamed': unnamed,
        'koromon': {'f': b64(WEB + 'art/koromon-f.png'), 'b': b64(WEB + 'art/koromon-b.png')}}
tpl = open(R + 'order_tpl.html').read()
html = tpl.replace('/*DATA*/null', json.dumps(DATA, ensure_ascii=False))
# 제목 글꼴: 페이지에 쓰인 글자만
text = re.sub(r'<[^>]+>', '', re.sub(r'<style>.*?</style>|<script>.*?</script>', '', tpl, flags=re.S)) + json.dumps([e['ko'] for e in ess] + ['필수', '지금 롬에 있는 디지몬', '나중에', '빠지는 디지몬', '모음'], ensure_ascii=False)
open(SP + 'chars.txt', 'w').write(''.join(sorted(set(text) | set('0123456789/ ·()×'))))
subprocess.run(['pyftsubset', WEB + 'Galmuri9.woff2', '--text-file=' + SP + 'chars.txt', '--flavor=woff2', '--output-file=' + SP + 'g.woff2'], check=True)
html = html.replace('__GALMURI__', base64.b64encode(open(SP + 'g.woff2', 'rb').read()).decode())
os.makedirs(SP, exist_ok=True); open(SP + '디지몬_그림주문서.html', 'w').write(html)
print('필수', len(ess), '롬', len(romlist), '나중', len(later), '이름 없음', len(unnamed), '크기', len(html))
