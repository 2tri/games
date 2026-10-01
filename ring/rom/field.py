"""걷는 화면(필드) 자료: 타일 → 16×16 칸(메타타일) → 글자 격자 지도 + 사람·표지판·물건·사건 자리 → src/field_data.c
타일은 무료(CC0) gb-mini-pixel-world 와 직접 그린 길·물·나루. 제미나이 배경 그림이 오면 여기 칸만 바꾸면 된다.
사용: python3 field.py   (미리보기: field_preview.png)"""
import os, json
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = HERE + '/src'
GBM = HERE + '/../ref/tiles/gb-mini-pixel-world/gb-mini-pixel-world/'
FIELD_BANK = 11
GREEN = {(155, 188, 15): 0, (139, 172, 15): 1, (48, 98, 48): 2, (15, 56, 15): 3}

def load_tones(path):
    a = np.asarray(Image.open(path).convert('RGB'))
    return np.vectorize(lambda r, g, b: GREEN[(r, g, b)])(a[..., 0], a[..., 1], a[..., 2]).astype(int)
TS = load_tones(GBM + 'tileset.png')
def cell(cx, cy): return TS[cy * 16:cy * 16 + 16, cx * 16:cx * 16 + 16]
def draw(rows):   # 직접 그린 칸: ' ' 흰, '-' 밝은회, '+' 어두운회, '#' 검정
    return np.array([[' -+#'.index(ch) for ch in r] for r in rows])

PATH = np.array([[(' -+#'.index(ch) if i < len(r) else 1) for i, ch in enumerate((r + '-' * 16)[:16])] for r in [
    '----------------', '------ ---------', '----------------', '--  -------- ---', '----------------', '-------- -------',
    '----------------', '--- ---------- -', '----------------', '----------------', '------ ---------', '-- -------------',
    '----------------', '---------- -----', '----------------', '----- ----------']])
WATER = draw([
    '++++++++++++++++', '++++++++++++++++', '++--++++++++++++', '+-++-+++++++++++', '++++++++++++--++', '+++++++++++-++-+',
    '++++++++++++++++', '++++++++++++++++', '++++++++++++++++', '+++++--+++++++++', '++++-++-++++++++', '++++++++++++++++',
    '++++++++++++++++', '+--+++++++++++++', '-++-++++++++++++', '++++++++++++++++'])
DOCK = draw([
    '################', '+++++++++++++++#', '---------------#', '+++++++++++++++#', '################', '+++++++++++++++#',
    '---------------#', '+++++++++++++++#', '################', '+++++++++++++++#', '---------------#', '+++++++++++++++#',
    '################', '+++++++++++++++#', '---------------#', '+++++++++++++++#'])
BAG = draw([   # 땅에 떨어진 물건 (작은 보따리)
    '                ', '                ', '                ', '       ##       ', '      #--#      ', '     ######     ',
    '    #------#    ', '   #--------#   ', '   #---++---#   ', '   #--------#   ', '   #--------#   ', '    #------#    ',
    '     ######     ', '                ', '                ', '                '])

# 종류: 0 걷기, 1 막힘, 2 풀숲(야생 만남), 3 물(막힘), 4 표지판(막힘, A로 읽기), 5 물건(밟으면 줍기)
MT = {}   # 이름 → (16×16 그림, 종류)
def mt(name, img, kind): MT[name] = (np.array(img), kind)
mt('grass', cell(2, 3), 0); mt('dots', cell(2, 1), 0); mt('flower', cell(0, 3), 0)
mt('tall', cell(0, 5), 2); mt('bush', cell(0, 2), 1); mt('crop', cell(4, 2), 1)
mt('fence', cell(2, 2), 1); mt('post', cell(1, 3), 1); mt('sign', cell(4, 4), 4); mt('cat', cell(0, 4), 1)
mt('barrel', cell(4, 3), 1); mt('pot', cell(4, 8), 1)
mt('path', PATH, 0); mt('water', WATER, 3); mt('dock', DOCK, 0); mt('bag', BAG, 5)
for i, (cx, cy) in enumerate([(3, 0), (4, 0), (3, 1), (4, 1)]): mt('tree%d' % i, cell(cx, cy), 1)
for i, (cx, cy) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]): mt('house%d' % i, cell(cx, cy), 1)
OBJ = {'tree': ['tree0', 'tree1', 'tree2', 'tree3'], 'house': ['house0', 'house1', 'house2', 'house3']}
KEY = {'.': 'grass', 'g': 'dots', '*': 'flower', ',': 'tall', 'b': 'bush', 'c': 'crop', '-': 'fence', '|': 'post',
       ':': 'path', '~': 'water', '=': 'dock', 'S': 'sign', 'k': 'cat', 'o': 'barrel', 'p': 'pot'}

# ── 샤이어 지도: 큰 칸(2×2) 밑그림으로 숲·물·밭을 잡고(나무가 반쪽으로 잘리지 않게), 길·집·울타리를 덧그림 ──
COARSE = [            # T 숲  . 빈터  , 풀숲  F 밭  W 물
    'TTTTTTTTTTTTTTTT',
    'T.......T....FFT',
    'T.......T....FFT',
    'T..............T',
    'T........,,....T',
    'T.....,,.,,..,,T',
    'TTTT..,,.....,,T',
    'TTTTTTTTTTTT.TTT',
    'TTTTTTTTTTTT.TTT',
    'TTTTTTTTTTTT.TTT',
    'WWWWWWWWWWWW.WWW',
    'WWWWWWWWWWWWWWWW',
]
def build(coarse, paints):
    H, W = len(coarse) * 2, len(coarse[0]) * 2
    g = [['.'] * W for _ in range(H)]
    for cy, r in enumerate(coarse):
        for cx, ch in enumerate(r):
            v = {'T': 'T', '.': '.', ',': ',', 'F': 'c', 'W': '~'}[ch]
            for dy in range(2):
                for dx in range(2): g[cy * 2 + dy][cx * 2 + dx] = v
    for ch, cells in paints:
        for x, y in cells: g[y][x] = ch
    return [''.join(r) for r in g]
def hline(y, x0, x1): return [(x, y) for x in range(min(x0, x1), max(x0, x1) + 1)]
def vline(x, y0, y1): return [(x, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
SHIRE = build(COARSE, [
    (':', hline(6, 3, 26) + vline(5, 4, 6) + vline(11, 4, 6) + vline(5, 6, 10) + vline(24, 6, 21) + vline(25, 14, 19)),
    ('=', [(24, 20), (25, 20), (24, 21), (25, 21)]),                    # 노루말 나루
    ('-', hline(8, 2, 3) + hline(8, 8, 9) + [(16, 8), (17, 8)]),         # 정원 울타리
    ('*', [(2, 4), (8, 3), (13, 3), (3, 10), (9, 10), (14, 5), (20, 4)]),
    ('g', [(7, 9), (12, 9), (18, 2), (22, 3)]),
    ('o', [(27, 7)]), ('p', [(7, 3)]),
])
MAPS = [dict(
    name='샤이어', rows=SHIRE, start=(5, 4, 0),
    objs=[('house', 4, 2), ('house', 10, 2), ('house', 4, 8), ('house', 26, 6)],
    wild=[('dogW', 3, 5)], rate=12,                               # 샤이어: 매곳네 개들
    npcs=[   # (x, y, 대사) 말하기 · ('inn'|'shop', x, y, 대사) · ('trainer', x, y, 보는 방향, 적, 은화, 덤빌 때, 진 뒤)
        (7, 5, '샘의 아버지 햄: 프로도 나리, 우리 샘 녀석 잘 부탁드려요. 손은 굼떠도 마음은 단단한 놈이에요.'),
        ('inn', 12, 5, '초록용 주막 주인: 어서 오세요! 쉬어 가시겠어요? 한숨 자고 나면 기운이 날 거예요.'),
        ('shop', 3, 6, '호빗골 장터: 길 떠나는 분께 필요한 것들 있어요!'),
        ('trainer', 20, 9, 'up', 'dogT', 40, '테드 샌디맨: 배긴스네 도련님이 어딜 가시나? 우리 사냥개랑 한판 붙어 보시지!', '테드 샌디맨: 쳇, 개가 겁을 먹다니…'),
        (13, 7, '호빗 아주머니: 동쪽 풀숲엔 매곳 영감네 개들이 돌아다녀요. 풀숲에 들어가면 조심하세요!'),
        (19, 5, '호빗 아이: 요즘 밤마다 검은 옷 입은 사람이 말 타고 돌아다닌대요. 「배긴스」를 찾는대요!'),
        (28, 8, '매곳네 일꾼: 영감님 밭에서 버섯 훔쳐 가면 개를 푼다니까!'),
    ],
    signs=[(8, 5, '호빗골 → 동쪽 매곳 농장 · 남동쪽 노루말 나루'), (23, 13, '이 길 끝은 노루말 나루. 강을 건너면 샤이어 밖이다.')],
    items=[(9, 13, 'herb'), (29, 13, 'herb'), (2, 7, 'lembas')],
    # 사건 자리 (x, y, w, h, 그 단계까지): 농장 어귀(동쪽으로 가려면 꼭 지나감) → 숲길
    triggers=[(22, 2, 2, 12, 1), (24, 16, 2, 1, 2, 1, 2, 20)],   # 숲길 사건 뒤 나룻배로 강 건너 묵은숲(지도 1)
    exits=[(24, 21, 1, 2, 21, 3), (25, 21, 1, 2, 21, 3)],          # 나루 → 묵은숲 (x, y, 지도, 도착 x, y, 필요한 단계)
)]
# ── 묵은숲·무덤 언덕 ──
OLDFOREST = build([
    'TTTTTTTTTTTTTTTT',
    'T....TT......,,T',
    'T.TT.TT.TTTT.,,T',
    'T.TT....T..T...T',
    'T....TT.T.WWW..T',
    'TTT.TTT...WWW..T',
    'T...T.....WWWTTT',
    'T.TTT.TTT..W...T',
    'W.....T,,,.....T',
    'WT.TTTT,,,TTTT.T',
    'W......,,,.....T',
    'TTTTTTTTTTTTTTTT',
], [
    (':', hline(21, 1, 13) + vline(2, 12, 21) + hline(12, 2, 6) + vline(6, 6, 12) + hline(6, 6, 18) + vline(18, 6, 15) + hline(15, 18, 30) + vline(28, 4, 15)),
    ('b', [(26, 2), (29, 6), (27, 5)]), ('*', [(9, 16), (21, 4)]), ('g', [(14, 3), (5, 17)]),
])
MAPS.append(dict(
    name='묵은숲', rows=OLDFOREST, start=(2, 21, 1),
    objs=[('house', 25, 16), ('tree', 8, 12)],
    wild=[('rootW', 5, 7), ('rootW', 5, 7), ('rootW', 6, 7), ('wightW', 7, 8)], rate=14,   # 묵은숲: 성난 나무, 가끔 무덤 안개
    npcs=[
        ('inn', 27, 17, '톰 봄바딜: 헤이 돌! 메리 돌! 지친 나그네여, 톰의 집에서 쉬어 가렴!'),
        (4, 19, '샘: 이 숲은 나무들이 우릴 노려보는 것 같아요, 나리. 길에서 벗어나지 말아요.'),
    ],
    signs=[(3, 20, '묵은숲. 길은 자꾸 강가로 이어진다.')],
    items=[(13, 3, 'herb'), (29, 2, 'lembas'), (15, 17, 'herb')],
    triggers=[(18, 11, 1, 2, 3), (28, 4, 1, 1, 4, 2, 2, 12)],       # 버드나무 영감(강가) → 무덤 언덕 → 브리로
    exits=[(1, 21, 0, 25, 20, 3), (30, 15, 2, 2, 12, 5)],
))
# ── 브리 (5단계: 달리는 조랑말) ──
BREE = build([
    'TTTTTTTTTTTTTTTT',
    'T..............T',
    'T..............T',
    'T..............T',
    'T..............T',
    'T..............T',
    'T..............T',
    'T..............T',
    'T..............T',
    'TT,,,......,,,TT',
    'TT,,,......,,,TT',
    'TTTTTTTTTTTTTTTT',
], [
    ('-', hline(2, 2, 29) + hline(16, 2, 29)), ('|', vline(2, 3, 10) + vline(2, 14, 15) + vline(29, 3, 10) + vline(29, 14, 15)),
    (':', hline(12, 0, 31) + hline(13, 0, 31) + vline(15, 5, 12) + vline(8, 6, 12) + vline(22, 6, 12) + hline(5, 9, 21)),
    ('*', [(5, 4), (26, 4), (11, 9), (19, 9)]), ('o', [(12, 4), (13, 4), (25, 8)]), ('g', [(4, 10), (27, 10)]),
])
MAPS.append(dict(
    name='브리', rows=BREE, start=(2, 12, 3),
    objs=[('house', 4, 4), ('house', 7, 4), ('house', 14, 3), ('house', 16, 3), ('house', 21, 4), ('house', 24, 4), ('house', 5, 8), ('house', 23, 8)],
    wild=[('dogW', 6, 8), ('dogW', 6, 8), ('wolfW', 7, 8)], rate=10,   # 브리 주변: 들개, 늑대
    npcs=[
        ('inn', 18, 6, '버터버: 「달리는 조랑말」에 어서 오십쇼! 방 하나 내 드릴까요? 푹 쉬고 가세요.'),
        ('shop', 11, 11, '브리 장사꾼: 길 떠나는 분들 필요한 건 다 있습죠!'),
        (6, 11, '브리 사람: 요즘 큰길에 수상한 자들이 많아요. 검은 옷 입은 기사들 말이에요.'),
        (25, 11, '브리 아낙: 동쪽 문 밖은 황야예요. 늑대가 내려온대요.'),
        ('trainer', 20, 14, 'left', 'fernyT', 60, '빌 퍼니: 꼬마 호빗들이 어딜 가시나? 내 개들 맛 좀 봐라!', '빌 퍼니: 흥, 두고 보자고…'),
    ],
    signs=[(13, 11, '브리. 「달리는 조랑말」 여관은 마을 한가운데.'), (28, 11, '동쪽 문 → 황야 · 바람마루')],
    items=[(3, 15, 'herb'), (28, 3, 'lembas')],
    triggers=[(15, 5, 1, 1, 5)],                                    # 여관 문 앞: 성큼걸이를 만남
    exits=[(0, 12, 1, 29, 15, 5), (0, 13, 1, 29, 15, 5), (31, 12, 3, 1, 12, 6), (31, 13, 3, 1, 12, 6)],
))
# ── 황야: 미지워터 늪(6) · 바람마루(7) · 트롤숲(8) · 브루이넨 여울(9) ──
WILDS = build([
    'TTTTTTTTTTTTTTTT',
    'T......TT......T',
    'T.,,,.T..T.TT..T',
    'T.,,,.T..T.TT,,T',
    'T.WW.,.TT..TT,,T',
    'T.WW.,,......,.T',
    '.,,..,,TTTT....T',
    'T..WW..TTTT.TT.W',
    'T..WW,,......T.W',
    'T.....,,.TT..T.W',
    'T..,,....TT....W',
    'TTTTTTTTTTTTTTTT',
], [
    (':', hline(12, 0, 6) + vline(6, 4, 12) + hline(4, 6, 17) + vline(17, 4, 17) + hline(17, 17, 29) + vline(29, 13, 21) + hline(13, 26, 29)),
    ('b', [(15, 2), (16, 2), (14, 3), (18, 3), (15, 6), (16, 6)]),       # 바람마루 꼭대기 돌무더기
    ('=', [(30, 20), (31, 20), (30, 21), (31, 21)]),                     # 여울
])
MAPS.append(dict(
    name='황야', rows=WILDS, start=(1, 12, 3),
    objs=[('tree', 24, 18), ('tree', 26, 16)],
    wild=[('wolfW', 8, 11), ('wolfW', 8, 11), ('wolfW', 9, 11), ('trollW', 10, 12)], rate=14,   # 황야: 늑대, 트롤숲 근처 어린 트롤
    npcs=[(9, 13, '순찰자의 흔적이 있다. 「바람마루 꼭대기에서 기다리시오. — 간달프」라고 적힌 쪽지가 박혀 있다.')],
    signs=[(5, 11, '서쪽 → 브리 · 동쪽 → 바람마루')],
    items=[(3, 5, 'herb'), (14, 20, 'lembas'), (27, 3, 'herb')],
    triggers=[(6, 9, 1, 2, 6), (17, 4, 1, 1, 7), (17, 15, 1, 2, 8), (29, 20, 1, 2, 9)],
    exits=[(0, 12, 2, 30, 12, 6)],
))
D = json.loads(__import__('subprocess').check_output(['node', HERE + '/extract.js']))
fids = list(D['FOES'])
TRAINER_FLAG0 = 96
def npc_norm(m):
    out = []
    for n in m['npcs']:
        if isinstance(n[0], int): out.append((n[0], n[1], 0, 0, 0, 0, n[2], ''))
        elif n[0] in ('inn', 'shop'): out.append((n[1], n[2], 1 if n[0] == 'inn' else 2, 0, 0, 0, n[3], ''))
        else:
            _, x, y, d, foe, money, t1, t2 = n
            out.append((x, y, 3, ['down', 'up', 'left', 'right'].index(d), fids.index(foe), money, t1, t2))
    return out
def grid_names(m):
    H, W = len(m['rows']), len(m['rows'][0])
    g = [[None] * W for _ in range(H)]
    for y, r in enumerate(m['rows']):
        assert len(r) == W, (m['name'], y, len(r))
        for x, ch in enumerate(r):
            if ch == 'T':
                bx, by = x & ~1, y & ~1
                whole = all(0 <= by + j < H and 0 <= bx + i < W and m['rows'][by + j][bx + i] == 'T' for j in range(2) for i in range(2))
                g[y][x] = 'tree%d' % ((x & 1) + 2 * (y & 1)) if whole else 'bush'
            else: g[y][x] = KEY[ch]
    for o, ox, oy in m['objs']:
        for i, n in enumerate(OBJ[o]): g[oy + i // 2][ox + i % 2] = n
    for x, y, _ in m['signs']: g[y][x] = 'sign'
    for x, y, _ in m['items']: g[y][x] = 'bag'
    return g

# ── 8×8 타일 모으기 (같은 타일은 하나로) ──
tiles, tindex = [], {}
def tid(b):
    k = b.tobytes()
    if k not in tindex: tindex[k] = len(tiles); tiles.append(b)
    return tindex[k]
names = list(MT)
mt_rows = []
for n in names:
    img, kind = MT[n]
    q = [tid(img[0:8, 0:8]), tid(img[0:8, 8:16]), tid(img[8:16, 0:8]), tid(img[8:16, 8:16])]
    mt_rows.append(q + [kind])
assert len(tiles) <= 240, '필드 타일이 너무 많음'

def enc(b):
    out = []
    for row in b:
        lo = hi = 0
        for x, v in enumerate(row): lo |= (int(v) & 1) << (7 - x); hi |= ((int(v) >> 1) & 1) << (7 - x)
        out += [lo, hi]
    return out
# ── 주인공·사람 그림 (OBJ, 8×16 두 장 = 16×16). 바깥 배경은 투명(0), 얼굴 흰색은 1 ──
def sprite16(path):
    t = load_tones(path) if isinstance(path, str) else path; h, w = t.shape
    out = np.where(t == 0, 1, t)                     # 흰 → 1 (팔레트 1 = 흰)
    out = np.where(t == 1, 1, out)
    seen = np.zeros_like(t, bool); st = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    while st:
        y, x = st.pop()
        if 0 <= y < h and 0 <= x < w and not seen[y, x] and t[y, x] == 0:
            seen[y, x] = True; out[y, x] = 0; st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return out
def obj_tiles(img):   # 8×16 순서: 왼쪽 위·아래, 오른쪽 위·아래
    return enc(img[0:8, 0:8]) + enc(img[8:16, 0:8]) + enc(img[0:8, 8:16]) + enc(img[8:16, 8:16])
import sys as _s; _s.path.insert(0, HERE + '/art'); import frodo_walk
pspr = sum((obj_tiles(np.array(frodo_walk.tones(f))) for f in frodo_walk.FRAMES), [])   # 프로도 (임시 손그림)
npc_spr = obj_tiles(sprite16(TS[0:16, 32:48]))   # 마을 사람 (타일 묶음의 사람 칸)
EXCL = draw(['                ', '      ####      ', '     #----#     ', '     #----#     ', '     #----#     ', '     #----#     ', '      #--#      ', '      #--#      ',
             '      #--#      ', '       ##       ', '      ####      ', '      #--#      ', '      ####      ', '                ', '                ', '                '])
excl_spr = obj_tiles(np.where(EXCL == 0, 0, EXCL))

def cstr(s): return json.dumps(s, ensure_ascii=False)
out = ['#pragma bank %d' % FIELD_BANK, '#include <stdint.h>', '#include "field.h"']
out.append('const uint8_t FT_TILES[] = {%s};' % ','.join(map(str, sum((enc(t) for t in tiles), []))))
out.append('const uint8_t FT_N = %d;' % len(tiles))
out.append('const uint8_t MTDEF[][5] = {%s};' % ','.join('{%s}' % ','.join(map(str, r)) for r in mt_rows))
out.append('const uint8_t PLAYER_SPR[] = {%s};' % ','.join(map(str, pspr)))
out.append('const uint8_t NPC_SPR[] = {%s};' % ','.join(map(str, npc_spr)))
out.append('const uint8_t EXCL_SPR[] = {%s};' % ','.join(map(str, excl_spr)))
hdr = []
tcount = [0]
mapfiles = {}; mbank, mused = 13, 0
for i, m in enumerate(MAPS):
    start_len = len(out)
    g = grid_names(m); H, W = len(g), len(g[0])
    out.append('const uint8_t MAP%d_CELLS[] = {%s};' % (i, ','.join(str(names.index(n)) for r in g for n in r)))
    nl = []
    for (x, y, k, d, a, a2, t1, t2) in npc_norm(m):
        fl = 0
        if k == 3: fl = TRAINER_FLAG0 + tcount[0]; tcount[0] += 1
        nl.append('{%d,%d,%d,%d,%d,%d,%d,%s,%s}' % (x, y, k, d, a, a2, fl, cstr(t1), cstr(t2) if t2 else '0'))
    out.append('const Npc MAP%d_NPC[] = {%s};' % (i, ','.join(nl) or '{0}'))
    out.append('const Sign MAP%d_SIGN[] = {%s};' % (i, ','.join('{%d,%d,%s}' % (x, y, cstr(t)) for x, y, t in m['signs']) or '{0}'))
    out.append('const Item MAP%d_ITEM[] = {%s};' % (i, ','.join('{%d,%d,%d,%d}' % (x, y, {'herb': 0, 'lembas': 1}[k], j) for j, (x, y, k) in enumerate(m['items'])) or '{0}'))
    out.append('const Trig MAP%d_TRIG[] = {%s};' % (i, ','.join('{%d,%d,%d,%d,%d,%d,%d,%d}' % (tuple(t) + (255, 0, 0))[:8] for t in m['triggers']) or '{0}'))
    out.append('const uint8_t MAP%d_WILD[] = {%s};' % (i, ','.join('%d,%d,%d' % (fids.index(f), lo, hi) for f, lo, hi in m['wild'])))
    out.append('const Exit MAP%d_EXIT[] = {%s};' % (i, ','.join('{%d,%d,%d,%d,%d,%d}' % e for e in m.get('exits', [])) or '{0}'))
    chunk = out[start_len:]; del out[start_len:]
    size = sum(len(c.encode()) for c in chunk) // 3          # C 소스 → 대략 바이트
    if mused + size > 14000: mbank += 1; mused = 0
    mused += size; mapfiles.setdefault(mbank, []).extend(chunk)
    hdr.append('{%d,%d,%d,MAP%d_CELLS,%d,MAP%d_NPC,%d,MAP%d_SIGN,%d,MAP%d_ITEM,%d,MAP%d_TRIG,%d,MAP%d_WILD,%d,MAP%d_EXIT,%d,%d,%d,%d,%d}' % (
        mbank, W, H, i, len(m['npcs']), i, len(m['signs']), i, len(m['items']), i, len(m['triggers']), i, len(m['wild']), i, len(m.get('exits', [])), i, m['rate'], *m['start'], names.index('grass')))
for bk, chunk in mapfiles.items():
    open(SRC + '/maps_%d.c' % bk, 'w').write('#pragma bank %d\n#include <stdint.h>\n#include "field.h"\n' % bk + '\n'.join(chunk) + '\n')
    for c in chunk: out.insert(3, 'extern ' + c.split('=')[0].strip() + ';')
assert mbank <= 14, '지도 은행이 모자람'
out.append('const MapDef MAPS[] = {%s};' % ','.join(hdr))
import glob as _g
for f in _g.glob(SRC + '/maps_*.c'):
    if int(f.split('_')[-1][:-2]) not in mapfiles: os.remove(f)
open(SRC + '/field_data.c', 'w').write('\n'.join(out) + '\n')
open(SRC + '/field.h', 'w').write('''#include <stdint.h>
#define FIELD_BANK %d
#define N_MAPS %d
#define MT_TREE0 %d
#define FIELD_END %d
extern const uint8_t EXCL_SPR[];
enum { MK_WALK, MK_SOLID, MK_GRASS, MK_WATER, MK_SIGN, MK_ITEM };
enum { NK_TALK, NK_INN, NK_SHOP, NK_TRAINER };
typedef struct { uint8_t x, y, kind, dir, arg, arg2, flag; const char *text, *text2; } Npc;
typedef struct { uint8_t x, y; const char *text; } Sign;
typedef struct { uint8_t x, y, kind, flag; } Item;
typedef struct { uint8_t x, y, w, h, step, wmap, wx, wy; } Trig;   // wmap != 255 이면 사건 뒤 그 지도로
typedef struct { uint8_t x, y, map, tx, ty, need; } Exit;   // 밟으면 다른 지도로 (need 단계부터)
typedef struct { uint8_t bank, w, h; const uint8_t *cells; uint8_t nn; const Npc *npc; uint8_t ns; const Sign *sign; uint8_t ni; const Item *item;
                 uint8_t nt; const Trig *trig; uint8_t nw; const uint8_t *wild; uint8_t ne; const Exit *exit; uint8_t rate, sx, sy, sdir, grass; } MapDef;
extern const uint8_t FT_TILES[], FT_N, MTDEF[][5], PLAYER_SPR[], NPC_SPR[];
extern const MapDef MAPS[];
''' % (FIELD_BANK, len(MAPS), names.index('tree0'), max(t[4] for m in MAPS for t in m['triggers']) + 1))

# ── 미리보기 ──
P = np.array([248, 176, 96, 24], np.uint8)
for i, m in enumerate(MAPS):
    g = grid_names(m); H, W = len(g), len(g[0])
    im = np.zeros((H * 16, W * 16), int)
    for y in range(H):
        for x in range(W): im[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = MT[g[y][x]][0]
    rgb = np.stack([P[im]] * 3, -1)
    for n in npc_norm(m): x, y = n[0], n[1]; rgb[y * 16 + 4:y * 16 + 12, x * 16 + 4:x * 16 + 12] = [[200, 60, 60], [60, 180, 60], [200, 160, 40], [140, 40, 160]][n[2]]
    for t in m['triggers']:
        x, y, w, h = t[:4]; rgb[y * 16:(y + h) * 16, x * 16:(x + w) * 16, 2] = 255
    sx, sy, _ = m['start']; rgb[sy * 16 + 4:sy * 16 + 12, sx * 16 + 4:sx * 16 + 12] = [60, 60, 220]
    Image.fromarray(rgb.astype(np.uint8)).resize((W * 32, H * 32), 0).save(HERE + '/field_preview%d.png' % i)
print('필드 타일', len(tiles), '칸', len(names), '지도', len(MAPS))
