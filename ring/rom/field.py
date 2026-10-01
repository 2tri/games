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
    wild=['dogW', 'dogW', 'crowW'], rate=12,
    npcs=[   # x, y, 대사
        (7, 5, '샘의 아버지 햄: 프로도 나리, 우리 샘 녀석 잘 부탁드려요. 손은 굼떠도 마음은 단단한 놈이에요.'),
        (13, 7, '호빗 아주머니: 동쪽 풀숲엔 매곳 영감네 개들이 돌아다녀요. 풀숲에 들어가면 조심하세요!'),
        (19, 5, '호빗 아이: 요즘 밤마다 검은 옷 입은 사람이 말 타고 돌아다닌대요. 「배긴스」를 찾는대요!'),
        (28, 8, '매곳네 일꾼: 영감님 밭에서 버섯 훔쳐 가면 개를 푼다니까!'),
    ],
    signs=[(8, 5, '호빗골 → 동쪽 매곳 농장 · 남동쪽 노루말 나루'), (23, 13, '이 길 끝은 노루말 나루. 강을 건너면 샤이어 밖이다.')],
    items=[(9, 13, 'herb'), (29, 13, 'herb'), (2, 7, 'lembas')],
    # 사건 자리 (x, y, w, h, 그 단계까지): 농장 어귀(동쪽으로 가려면 꼭 지나감) → 숲길
    triggers=[(22, 2, 2, 12, 1), (24, 16, 2, 1, 2)],
)]
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

def cstr(s): return json.dumps(s, ensure_ascii=False)
D = json.loads(__import__('subprocess').check_output(['node', HERE + '/extract.js']))
fids = list(D['FOES'])
out = ['#pragma bank %d' % FIELD_BANK, '#include <stdint.h>', '#include "field.h"']
out.append('const uint8_t FT_TILES[] = {%s};' % ','.join(map(str, sum((enc(t) for t in tiles), []))))
out.append('const uint8_t FT_N = %d;' % len(tiles))
out.append('const uint8_t MTDEF[][5] = {%s};' % ','.join('{%s}' % ','.join(map(str, r)) for r in mt_rows))
out.append('const uint8_t PLAYER_SPR[] = {%s};' % ','.join(map(str, pspr)))
out.append('const uint8_t NPC_SPR[] = {%s};' % ','.join(map(str, npc_spr)))
hdr = []
for i, m in enumerate(MAPS):
    g = grid_names(m); H, W = len(g), len(g[0])
    out.append('const uint8_t MAP%d_CELLS[] = {%s};' % (i, ','.join(str(names.index(n)) for r in g for n in r)))
    out.append('const Npc MAP%d_NPC[] = {%s};' % (i, ','.join('{%d,%d,%s}' % (x, y, cstr(t)) for x, y, t in m['npcs']) or '{0}'))
    out.append('const Sign MAP%d_SIGN[] = {%s};' % (i, ','.join('{%d,%d,%s}' % (x, y, cstr(t)) for x, y, t in m['signs']) or '{0}'))
    out.append('const Item MAP%d_ITEM[] = {%s};' % (i, ','.join('{%d,%d,%d,%d}' % (x, y, {'herb': 0, 'lembas': 1}[k], j) for j, (x, y, k) in enumerate(m['items'])) or '{0}'))
    out.append('const Trig MAP%d_TRIG[] = {%s};' % (i, ','.join('{%d,%d,%d,%d,%d}' % t for t in m['triggers']) or '{0}'))
    out.append('const uint8_t MAP%d_WILD[] = {%s};' % (i, ','.join(str(fids.index(f)) for f in m['wild'])))
    hdr.append('{%d,%d,MAP%d_CELLS,%d,MAP%d_NPC,%d,MAP%d_SIGN,%d,MAP%d_ITEM,%d,MAP%d_TRIG,%d,MAP%d_WILD,%d,%d,%d,%d,%d}' % (
        W, H, i, len(m['npcs']), i, len(m['signs']), i, len(m['items']), i, len(m['triggers']), i, len(m['wild']), i, m['rate'], *m['start'], names.index('grass')))
out.append('const MapDef MAPS[] = {%s};' % ','.join(hdr))
open(SRC + '/field_data.c', 'w').write('\n'.join(out) + '\n')
open(SRC + '/field.h', 'w').write('''#include <stdint.h>
#define FIELD_BANK %d
#define N_MAPS %d
#define MT_TREE0 %d
enum { MK_WALK, MK_SOLID, MK_GRASS, MK_WATER, MK_SIGN, MK_ITEM };
typedef struct { uint8_t x, y; const char *text; } Npc;
typedef struct { uint8_t x, y; const char *text; } Sign;
typedef struct { uint8_t x, y, kind, flag; } Item;
typedef struct { uint8_t x, y, w, h, step; } Trig;
typedef struct { uint8_t w, h; const uint8_t *cells; uint8_t nn; const Npc *npc; uint8_t ns; const Sign *sign; uint8_t ni; const Item *item;
                 uint8_t nt; const Trig *trig; uint8_t nw; const uint8_t *wild; uint8_t rate, sx, sy, sdir, grass; } MapDef;
extern const uint8_t FT_TILES[], FT_N, MTDEF[][5], PLAYER_SPR[], NPC_SPR[];
extern const MapDef MAPS[];
''' % (FIELD_BANK, len(MAPS), names.index('tree0')))

# ── 미리보기 ──
P = np.array([248, 176, 96, 24], np.uint8)
for i, m in enumerate(MAPS):
    g = grid_names(m); H, W = len(g), len(g[0])
    im = np.zeros((H * 16, W * 16), int)
    for y in range(H):
        for x in range(W): im[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = MT[g[y][x]][0]
    rgb = np.stack([P[im]] * 3, -1)
    for x, y, _ in m['npcs']: rgb[y * 16 + 4:y * 16 + 12, x * 16 + 4:x * 16 + 12] = [200, 60, 60]
    for x, y, w, h, s in m['triggers']: rgb[y * 16:(y + h) * 16, x * 16:(x + w) * 16, 2] = 255
    sx, sy, _ = m['start']; rgb[sy * 16 + 4:sy * 16 + 12, sx * 16 + 4:sx * 16 + 12] = [60, 60, 220]
    Image.fromarray(rgb.astype(np.uint8)).resize((W * 32, H * 32), 0).save(HERE + '/field_preview%d.png' % i)
print('필드 타일', len(tiles), '칸', len(names), '지도', len(MAPS))
