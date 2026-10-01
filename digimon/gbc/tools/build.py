#!/usr/bin/env python3
"""디지몬 GBC 롬 만들기: 웹판 자료 + story.py → C 데이터 → GBDK 로 digimon.gbc
사용: python3 tools/build.py   (gbc 폴더 안에서)"""
import json, os, sys, subprocess, re, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                  # digimon/gbc
WEB = os.path.dirname(ROOT)                   # digimon
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import gfx
from gfx import Tiles, enc2bpp, enc1bpp, hexrgb, rgb15
from text import Strings, batchim, VARS
import dsl
import story

GEN = os.path.join(ROOT, 'build', 'gen'); os.makedirs(GEN, exist_ok=True)
subprocess.run(['node', os.path.join(HERE, 'export_web.cjs'), os.path.join(ROOT, 'build', 'web.json')], check=True)
W = json.load(open(os.path.join(ROOT, 'build', 'web.json')))
FONT = W['font']

# ───────── 번호 매기기 ─────────
SPECIES = list(W['species'].keys())
SPI = {k: i for i, k in enumerate(SPECIES)}
TIERS = ['baby', 'baby2', 'rookie', 'champion', 'ultimate', 'mega']
ATTRS = ['백신', '데이터', '바이러스', '프리', '없음', '불명']
KIDS = story.KIDS; KIDI = {k: i for i, k in enumerate(KIDS)}
MAPNAMES = list(story.MAPS.keys()); MAPI = {k: i for i, k in enumerate(MAPNAMES)}
DIRS = {'down': 0, 'up': 1, 'left': 2, 'right': 3}
ITEMI = {it[0]: i for i, it in enumerate(story.ITEMS)}
CRESTI = {c: i for i, c in enumerate(story.CRESTS)}

S = Strings()
def sid(t): return S.add(t)
def dname(sp): return re.sub(r'\(.*?\)', '', W['species'][sp]['name']).strip()

# ───────── 기술 ─────────
POW = W['power']
BASIC = [('부딪치기', 40, 100, 35, 0), ('할퀴기', 40, 100, 35, 0), ('물기', 60, 100, 25, 0), ('노려보기', 0, 100, 30, 1), ('웅크리기', 0, 100, 30, 2)]
MOVES = []; MOVEI = {}
for (n, p, a, pp, e) in BASIC: MOVEI[n] = len(MOVES); MOVES.append((n, p, a, pp, e, 0))
sigtier = {}
for sp in SPECIES:
    t = W['species'][sp]['tier']
    for n in W['species'][sp]['sig']:
        if n not in sigtier or TIERS.index(t) < TIERS.index(sigtier[n]): sigtier[n] = t
for sp in SPECIES:
    for n in W['species'][sp]['sig']:
        if n in MOVEI: continue
        t = sigtier[n]; pp = 5 if t == 'mega' else 8 if t == 'ultimate' else 12
        MOVEI[n] = len(MOVES); MOVES.append((n, POW[t], 95, pp, 0, 1))
TIER_BASIC = {'baby': ['부딪치기'], 'baby2': ['부딪치기', '노려보기'], 'rookie': ['할퀴기', '노려보기'],
              'champion': ['물기', '웅크리기'], 'ultimate': ['물기', '웅크리기'], 'mega': ['물기', '웅크리기']}

# ───────── 엔진 문자열 ─────────
ES = {
    'yes': '예', 'no': '아니오',
    'm_dex': '도감', 'm_mon': '디지몬', 'm_bag': '가방', 'm_save': '저장', 'm_close': '닫기',
    'name_s0': '{s0}', 'name_m0': '{m0}', 'name_i0': '{i0}', 'b_what1': '{s0}{은/는}', 'b_what2': '무엇을 할까?',
    'b_fight': '싸우다', 'b_bag': '가방', 'b_mon': '디지몬', 'b_run': '도망치다', 'b_what': '{s0}{은/는}\n무엇을 할까?',
    'wild_appear': '앗! 야생 {s0}{이/가} 나타났다!', 'boss_appear': '{s0}{이/가} 덤벼들었다!', 'go': '가랏! {s0}!',
    'use': '{s0}의 {m0}!', 'use_w': '야생 {s0}의 {m0}!', 'miss': '그러나 빗나갔다!', 'crit': '급소에 맞았다!',
    'super': '효과가 굉장했다!', 'weak': '효과가 별로인 듯하다…', 'noeff': '효과가 없었다!',
    'defdn': '{s0}의 방어가 떨어졌다!', 'defdn_w': '야생 {s0}의 방어가 떨어졌다!',
    'defup': '{s0}의 방어가 올라갔다!', 'defup_w': '야생 {s0}의 방어가 올라갔다!',
    'faint': '{s0}{은/는} 쓰러졌다!', 'faint_w': '야생 {s0}{은/는} 쓰러졌다!',
    'exp': '{s0}{은/는} 경험치 {n0}{을/를} 얻었다!', 'lvup': '{s0}의 레벨이 {n0}{이/가} 되었다!',
    'learn': '{s0}{은/는} {m0}{을/를} 익혔다!', 'evo1': '어라…!? {s0}의 모습이…!', 'evo2': '축하합니다! {s0}{은/는}\n{s1}{으로/로} 진화했다!',
    'join': '{s0}{이/가} 일어나 동료가 되고 싶은 듯 이쪽을 보고 있다!\f{s0}{을/를} 데려갈까?',
    'joined': '{s0}{이/가} 동료가 되었다!', 'joined_box': '{s0}{이/가} 동료가 되었다!\n(보관함으로 보냈다)', 'left': '{s0}{은/는} 숲으로 돌아갔다…',
    'run_ok': '무사히 도망쳤다!', 'run_ng': '도망칠 수 없었다!', 'no_run': '도망칠 수 없다!', 'no_pp': '기술을 쓸 힘이 남아 있지 않다!',
    'back': '돌아와, {s0}!', 'cant': '{s0}{은/는} 싸울 힘이 없다!', 'already': '{s0}{은/는} 이미 싸우고 있다!', 'egg_cant': '디지타마는 싸울 수 없다!',
    'wo1': '{kid}에게는 싸울 수 있는 디지몬이 없다!', 'wo2': '눈앞이 캄캄해졌다…', 'wo3': '…정신을 차려 보니 쉴 곳으로 돌아와 있었다.\f디지몬들이 모두 기운을 되찾았다.',
    'hatch1': '어라…?', 'hatch2': '디지타마가 부화해서\n{s0}{이/가} 태어났다!',
    'healed': '{s0}의 체력이 {n0} 회복되었다!', 'useless': '써도 효과가 없다.', 'cantuse': '지금은 쓸 수 없다.',
    'p_pick': '디지몬을 고르세요', 'p_send': '누구를 내보낼까?', 'p_use': '누구에게 쓸까?', 'p_move': '어느 자리로 옮길까?',
    'p_menu1': '능력 보기', 'p_menu2': '순서 바꾸기', 'p_menu3': '닫기', 'no_mon': '함께하는 디지몬이 없다.',
    'egg': '디지타마', 'egg_info': '디지타마다. 걷다 보면 깨어날 것 같다…',
    'st_attr': '속성', 'st_type': '유형', 'st_atk': '공격', 'st_def': '방어', 'st_spd': '스피드', 'st_next': '다음 레벨까지',
    'st_moves': '기술', 'k_basic': '기본기', 'k_sig': '필살기', 'st_pow': '위력', 'st_chg': '변화', 'st_pp': 'PP',
    'save_q': '지금까지의 모험을 기록할까?', 'saved': '{kid}{은/는} 모험을 기록했다!',
    't_cont': '이어서 하기', 't_new': '새로 시작', 't_over': '새로 시작하면 지금의 기록은 덮어쓰게 된다. 괜찮을까?', 'cont': '이어서 한다.',
    'kp_title': '선택받은 아이',  'kp_q': '누구와 함께 모험을 떠날까?', 'kp_partner': '파트너', 'kp_ok': '{kid}{이/가} 맞느냐?',
    'bag': '가방', 'bag_quit': '그만두다', 'bag_none': '가방이 비어 있다.',
    'dex': '디지몬 도감', 'dex_seen': '만남', 'dex_own': '함께', 'dex_none': '아직 만난 디지몬이 없다', 'dex_q': '?????',
    'card_title': '선택받은 아이', 'card_crest': '문장', 'card_time': '모험 시간',
    'title_sub': '팬 게임 (가제)', 'press': 'START를 누르세요',
    'got_item': '{i0}{을/를} {n0}개 받았다!', 'crest_got': '{f0}의 문장을 손에 넣었다!',
    'cap_dv': '{kid}{은/는} 디지바이스를 내밀었다!', 'cap_net': '{kid}{은/는} {i0}{을/를} 던졌다!',
    'cap_boss': '이 디지몬의 데이터는 너무 강해서 받아들일 수 없다!', 'cap_nomore': '디지바이스의 빛이 다했다…\n(한 번 싸움에 3번까지)',
    'cap_strong': '{s0}의 데이터가 너무 강해서 튕겨 나갔다!', 'cap_ok': '해냈다!\n{s0}의 데이터를 받아들였다!', 'cap_ng': '앗! 데이터가 흩어져 버렸다…',
    'got_bits': '{n0} 비트를 얻었다!', 'shop_title': '상점', 'shop_ask': '{i0}{을/를} {n0} 비트에 살까?', 'shop_poor': '비트가 모자란다!',
    'shop_thx': '고맙습니다!\n{i0}{을/를} 샀다!', 'shop_full': '더 이상 가질 수 없다!', 'shop_bits': '가진 비트', 'shop_quit': '그만두다', 'card_bits': '비트',
}
ESID = {k: sid(v) for k, v in ES.items()}

# 디지몬·기술·도구·아이 이름
SP_NAME = [sid(dname(sp)) for sp in SPECIES]
SP_GRADE = [sid(W['species'][sp]['grade']) for sp in SPECIES]
SP_TYPE = [sid(W['species'][sp]['type']) for sp in SPECIES]
ATTR_NAME = [sid(a) for a in ATTRS]
MV_NAME = [sid(m[0]) for m in MOVES]
IT_NAME = [sid(it[0]) for it in story.ITEMS]
IT_DESC = [sid(it[2]) for it in story.ITEMS]
KID_NAME = [sid(W['kids'][k]['name']) for k in KIDS]
KID_CRESTS = [sid(story.KID_CREST[k] + '의 문장') for k in KIDS]
KID_DESC = [sid(story.KID_DESC[k]) for k in KIDS]
CREST_NAME = [sid(c) for c in story.CRESTS]

# ───────── 스크립트 ─────────
def sp_code(x):
    if isinstance(x, int): return x
    return SPI[x]
CTX = {'str': sid, 'map': lambda m: MAPI[m], 'dir': lambda d: DIRS[d] if d else 0xFF, 'sp': sp_code,
       'item': lambda i: ITEMI[i], 'crest': lambda c: CRESTI[c], 'kid': lambda k: KIDI[k]}

# ───────── 글자·글꼴 ─────────
# 지도·스크립트를 먼저 조립해야 모든 글이 모임 → 지도 처리 뒤 finalize
# (여기서는 미리 모든 스크립트를 한 번 훑어 문자열을 등록)
def walk_scripts():
    yield story.OPENING
    for m in story.MAPS.values():
        if m.on_enter: yield m.on_enter
        for n in m.npcs: yield n.script
        for s_ in m.signs: yield s_.script
        for t in m.triggers: yield t.script
for sc in walk_scripts():
    for it in sc:
        if isinstance(it, tuple) and it[0] in ('SAY', 'ASK'): sid(it[1])
for m in story.MAPS.values(): sid(m.name)          # 지도 이름 글자도
CHARS = S.finalize(extra='▶▼?!.…')
print('글자 수', len(CHARS))
# 글꼴: 글자마다 8×16 1bpp = 16바이트
FONTDATA = []
for ch in CHARS: FONTDATA += enc1bpp(gfx.glyph16(FONT, ch))
CHARFLAG = [batchim(ch) for ch in CHARS]

# ───────── 화면 부품 타일 (VRAM 0번 칸 0~79) ─────────
UI = {}; UIT = []          # 이름 → 번호, 타일 목록
def ui_add(name, t):
    UI[name] = len(UIT); UIT.append(np.asarray(t, np.uint8))
ui_add('BLANK', np.zeros((8, 8)))
ui_add('PAPER', np.ones((8, 8)))
c = np.ones((24, 24), np.uint8); gfx.frame(c, 0, 0, 24, 24); c[c == 0] = 1
for n, (x, y) in zip(['F_TL', 'F_T', 'F_TR', 'F_L', 'F_R', 'F_BL', 'F_B', 'F_BR'], [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]):
    ui_add(n, c[y * 8:y * 8 + 8, x * 8:x * 8 + 8])
t = c[16:24, 8:16].copy(); gfx.more(t, 1, 0); ui_add('F_BMORE', t)
c = np.ones((24, 24), np.uint8); gfx.frame2(c, 0, 0, 24, 24); c[c == 0] = 1
for n, (x, y) in zip(['G_TL', 'G_T', 'G_TR', 'G_L', 'G_R', 'G_BL', 'G_B', 'G_BR'], [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]):
    ui_add(n, c[y * 8:y * 8 + 8, x * 8:x * 8 + 8])
c = np.ones((16, 8), np.uint8); gfx.cursor(c, 2, 3); ui_add('CUR_T', c[:8]); ui_add('CUR_B', c[8:])
for d in '0123456789':
    c = np.ones((8, 8), np.uint8); gfx.num(c, d, 0, 1); ui_add('D' + d, c)
c = np.ones((8, 8), np.uint8); gfx.num(c, '/', 0, 1); ui_add('SLASH', c)
c = np.ones((8, 8), np.uint8); gfx.num(c, ':L', 0, 1); ui_add('LV', c)
# HP 표시 (팔레트 3: 0흰 1노랑 2파랑 3검정) — 막대는 타일 줄 1~6
TAGC = 1
c = np.zeros((8, 24), np.uint8)
c[1:7, 0:16] = 3; c[0, 1:16] = 3
for (i, j) in [(2, 1), (2, 2), (2, 3), (2, 4), (3, 2), (4, 1), (4, 2), (4, 3), (4, 4), (6, 1), (6, 2), (6, 3), (6, 4), (7, 1), (8, 1), (8, 2), (7, 3), (11, 1), (11, 4)]:
    c[1 + j, i] = TAGC
ui_add('TAG0', c[:, 0:8]); ui_add('TAG1', c[:, 8:16])
# HP 막대 칸 (팔레트 1·2: 0흰 1옅은색 2진한색 3검정): 채움 0~8
for k in range(9):
    c = np.zeros((8, 8), np.uint8); c[6, :] = 3
    c[2, :k] = 1; c[5, :k] = 1; c[3:5, :k] = 2
    ui_add('BAR%d' % k, c)
c = np.zeros((8, 8), np.uint8); c[1:7, 0:3] = 3; c[0, 0:2] = 3; ui_add('BARCAP', c)
# 경험치 막대 (팔레트 3: 파랑=2), 아래 6번째 줄은 꺾쇠 선
for k in range(9):
    c = np.zeros((8, 8), np.uint8); c[5, :] = 3
    if k: c[3:5, 8 - k:] = 2
    ui_add('EXP%d' % k, c)
NUI_FIXED = len(UIT)
print('화면 부품 타일', NUI_FIXED)

# 전투 화면 고정 부분 (꺾쇠): 그림으로 그려 잘라 붙임
def battle_static():
    cv = np.zeros((144, 160), np.uint8)
    # 상대 꺾쇠: 세로줄 (10,17)~, 아래줄
    x, y = 10, 17
    cv[y:y + 11, x:x + 4] = 3; cv[y + 11, x + 1:x + 5] = 3; cv[y + 12, x + 2:x + 6] = 3
    cv[y + 13, x + 3:x + 77] = 3
    for i in range(4): cv[y + 10 + i, x + 70 + i:x + 76] = 3
    cv[y + 13, x + 70:x + 78] = 3
    # 내 꺾쇠: 세로줄 (145,73)
    x, y = 145, 73
    cv[y + 1:y + 20, x:x + 4] = 3; cv[y, x - 1:x + 2] = 3
    cv[y + 20, x - 73:x + 3] = 3
    for i in range(4): cv[y + 17 + i, x - 73 + 3 - i:x - 73 + 7] = 3
    return cv
BS = battle_static()
BTILES = []; BMAP = {}
for ty in range(18):
    for tx in range(20):
        b = BS[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
        if b.any():
            b = b.copy(); b[b == 0] = 1
            k = b.tobytes()
            found = None
            for i, u in enumerate(UIT):
                if u.tobytes() == k: found = i
            if found is None: found = len(UIT); UIT.append(b)
            BMAP[(tx, ty)] = found
print('전투 고정 타일 포함', len(UIT))
assert len(UIT) <= 80

# ───────── 전투 그림 (앞 7×7, 뒤 6×6 타일) ─────────
ATTRCOL = {'백신': ('#a8c8f8', '#3868c0'), '데이터': ('#a8e0a0', '#3c9048'), '바이러스': ('#d8a8e8', '#7840a0'),
           '프리': ('#f8e0a0', '#b88830'), '없음': ('#e0e0e0', '#888888'), '불명': ('#c8c8c8', '#585858')}

def draw_glyph(cv, ch, x, y, v):
    g = gfx.glyph16(FONT, ch)
    for j in range(16):
        for i in range(8):
            if g[j, i] and 0 <= y + j < cv.shape[0] and 0 <= x + i < cv.shape[1]: cv[y + j, x + i] = v

def card(sp, back):
    """그림 없는 디지몬 임시 카드 48×48: 0흰 1밝은 2진한 3검정"""
    a = np.zeros((48, 48), np.uint8)
    yy, xx = np.mgrid[0:48, 0:48] + 0.5
    def ell(cx, cy, r): return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    a[ell(24, 28, 19)] = 3; a[ell(24, 28, 17)] = 1; a[ell(28, 32, 13) & ell(24, 28, 17)] = 2; a[ell(23, 27, 13)] = 1
    a[16:18, 14:17] = 0
    if not back: a[25:29, 17:20] = 3; a[25:29, 28:31] = 3
    ch = W['species'][sp]['name'][0]
    draw_glyph(a, ch, 20, 20 if back else 28, 3)
    c1, c2 = ATTRCOL[W['species'][sp]['attr']]
    return a, [gfx.WHITE, hexrgb(c1), hexrgb(c2), gfx.BLACK]

def load_png(path):
    im = Image.open(path).convert('RGBA'); a = np.asarray(im)
    h, w = a.shape[:2]; idx = np.zeros((h, w), np.uint8); pal = {}
    cols = []
    for y in range(h):
        for x in range(w):
            r, g, b, al = a[y, x]
            if al < 128: continue
            cols.append((int(r), int(g), int(b)))
    uniq = sorted(set(cols), key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
    # 흰색 → 0, 검정 → 3, 나머지 밝은 순 1·2 (5번째 강조색은 가장 가까운 색으로)
    white = [c for c in uniq if min(c) > 230]; black = [c for c in uniq if max(c) < 60]
    mid = [c for c in uniq if c not in white and c not in black]
    counts = {c: cols.count(c) for c in mid}
    mid = sorted(mid, key=lambda c: -counts[c])[:2]
    mid = sorted(mid, key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
    while len(mid) < 2: mid.append(mid[-1] if mid else (128, 128, 128))
    palc = [gfx.WHITE, mid[0], mid[1], gfx.BLACK]
    for y in range(h):
        for x in range(w):
            r, g, b, al = a[y, x]
            if al < 128: idx[y, x] = 0; continue
            cc = np.array([r, g, b], float)
            idx[y, x] = int(np.argmin([((cc - np.array(p)) ** 2).sum() for p in palc]))
    return idx, palc

def place(a, W_, H_):
    """그림을 W_×H_ 칸 바닥 가운데에"""
    out = np.zeros((H_, W_), np.uint8)
    h, w = a.shape
    if h > H_ or w > W_:
        a = a[max(0, h - H_):, max(0, (w - W_) // 2):max(0, (w - W_) // 2) + W_]; h, w = a.shape
    oy, ox = H_ - h, (W_ - w) // 2
    out[oy:oy + h, ox:ox + w] = a
    return out

def pic_bytes(a, pal):
    th, tw = a.shape[0] // 8, a.shape[1] // 8
    b = [tw, th]
    for c in pal: v = rgb15(c); b += [v & 255, v >> 8]
    for t in gfx.cut(a, tw, th): b += enc2bpp(t)
    return b

PICS = []      # (이름, 바이트)
def add_pic(name, a, pal):
    PICS.append((name, pic_bytes(a, pal))); return len(PICS) - 1
ART = os.path.join(WEB, 'art')
SP_FRONT = []; SP_BACK = []
for sp in SPECIES:
    f = os.path.join(ART, sp + '-f.png'); b = os.path.join(ART, sp + '-b.png')
    if os.path.exists(f): a, pal = load_png(f)
    else: a, pal = card(sp, False)
    SP_FRONT.append(add_pic(sp + '_f', place(a, 56, 56), pal))
    if os.path.exists(b): a, pal = load_png(b)
    else: a, pal = card(sp, True)
    SP_BACK.append(add_pic(sp + '_b', place(a, 48, 48), pal))
# 디지타마 (알)
egg = np.zeros((40, 32), np.uint8); yy, xx = np.mgrid[0:40, 0:32] + 0.5
inside = ((xx - 16) / 13) ** 2 + ((yy - 22) / 17) ** 2 <= 1
edge_ = ((xx - 16) / 14) ** 2 + ((yy - 22) / 18) ** 2 <= 1
egg[edge_] = 3; egg[inside] = 0
for (x, y) in [(10, 14), (19, 20), (12, 27), (21, 30), (16, 9), (8, 22)]: egg[y:y + 3, x:x + 3] = np.where(inside[y:y + 3, x:x + 3], 1, egg[y:y + 3, x:x + 3])
egg[inside & (xx > 22) & (yy > 18)] = np.where(egg[inside & (xx > 22) & (yy > 18)] == 0, 2, egg[inside & (xx > 22) & (yy > 18)])
PIC_EGG = add_pic('egg', place(egg, 56, 56), [gfx.WHITE, hexrgb('#f89830'), hexrgb('#e0d8c0'), gfx.BLACK])
print('전투 그림', len(PICS))

# ───────── 필드: 지도 칸(16×16) → 8×8 타일 + 팔레트 맞추기 ─────────
TP = W['tiles']
def tile_rgb(name):
    t = TP[name]; w, h = t['w'], t['h']
    a = np.zeros((h, w, 3), np.uint8)
    for i, c in enumerate(t['p']):
        a[i // w, i % w] = hexrgb(c) if c else hexrgb('#c8e8a0')
    return a
BIG = {'tent': (2, 2), 'blockHouse': (2, 2), 'palm': (1, 2), 'booth': (1, 2)}
SOLID = {'tree', 'dtree', 'sea', 'shore', 'crib', 'egg', 'sign', 'blockR', 'blockB', 'blockY', 'fire'} | set(BIG)
GRASS = {'tall'}

# 이미지 AI 배경에서 잘라 낸 조각 (tools/assets.py): 이름 → {img, w, h, solid, door, walk}
import assets as _assets, palfit
AS = _assets.load_all()
def big_of(o): return (AS[o]['w'], AS[o]['h']) if o in AS else BIG.get(o, (1, 1))

def mt_split(mt):
    if '@' in mt:
        n, xy = mt.split('@'); x, y = map(int, xy.split(',')); return n, x, y
    return mt, 0, 0

def mt_pixels(mt):
    """'tree' 또는 'tent@1,0' → 16×16×3"""
    n, x, y = mt_split(mt)
    src = AS[n]['img'] if n in AS else tile_rgb(n)
    return src[y * 16:y * 16 + 16, x * 16:x * 16 + 16]

def mt_flags(mt):
    n, x, y = mt_split(mt)
    if n in AS:
        a = AS[n]
        solid = a['solid'] and (x, y) != a.get('door') and (x, y) not in a.get('walk', [])
        return (MT_SOLID if solid else 0) | (MT_GRASS if a.get('grass') else 0)
    return (MT_SOLID if n in SOLID else 0) | (MT_GRASS if n in GRASS else 0)
MT_SOLID, MT_GRASS = 1, 2

def reduce_colors(cols, counts, k):
    """색을 k개로: 가장 덜 쓰는 색을 가장 가까운 색에 합침"""
    cols = list(cols); counts = list(counts)
    while len(cols) > k:
        i = int(np.argmin(counts))
        others = [j for j in range(len(cols)) if j != i]
        j = min(others, key=lambda j: sum((a - b) ** 2 for a, b in zip(cols[i], cols[j])))
        counts[j] += counts[i]; del cols[i]; del counts[i]
    return cols

def dist2(a, b): return sum((x - y) ** 2 for x, y in zip(a, b))

def fit_palettes(subtiles, weights, maxp=7):
    """subtiles: [8×8×3], weights: 지도에서 쓰이는 횟수 → (팔레트[4색] 목록, 타일마다 (팔레트, 8×8 색번호))
    많이 보이는 색(길·풀)이 지워지지 않게 쓰는 양으로 무게를 둠"""
    cw = {}; sets = []
    for st, w in zip(subtiles, weights):
        u = {}
        for p in [tuple(int(v) for v in q) for q in st.reshape(-1, 3)]: u[p] = u.get(p, 0) + 1
        for c, n in u.items(): cw[c] = cw.get(c, 0) + n * w
        sets.append(frozenset(reduce_colors(list(u.keys()), [u[c] * w for c in u], 4)))
    # 같은 색 묶음은 하나로, 무게 순
    uniq = {}
    for st, w in zip(sets, weights): uniq[st] = uniq.get(st, 0) + w * 64
    pals = []
    for st in sorted(uniq, key=lambda x: (-len(x), -uniq[x])):
        if any(st <= p for p in pals): continue
        best = None
        for p in pals:
            un = p | st
            if len(un) <= 4 and (best is None or len(un) - len(p) < best[0]): best = (len(un) - len(p), p)
        if best: pals.remove(best[1]); pals.append(best[1] | st)
        else: pals.append(frozenset(st))
    def merge_cost(p, q):
        un = list(p | q)
        red = reduce_colors(un, [cw.get(c, 1) for c in un], 4)
        return sum(cw.get(c, 1) * min(dist2(c, r) for r in red) for c in un), frozenset(red)
    while len(pals) > maxp:
        best = None
        for i in range(len(pals)):
            for j in range(i + 1, len(pals)):
                cost, red = merge_cost(pals[i], pals[j])
                if best is None or cost < best[0]: best = (cost, i, j, red)
        _, i, j, red = best
        pals = [p for k, p in enumerate(pals) if k not in (i, j)] + [red]
    pals = [sorted(p, key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114)) for p in pals]
    pals = [(p + [p[-1]] * 4)[:4] for p in pals]
    out = []
    for st in subtiles:
        px = st.reshape(-1, 3).astype(float); best = None
        for pi, p in enumerate(pals):
            pa = np.array(p, float); d = ((px[:, None] - pa[None]) ** 2).sum(2); e = d.min(1).sum()
            if best is None or e < best[0]: best = (e, pi, d.argmin(1).reshape(8, 8))
        out.append((best[1], best[2]))
    return pals, out

# ───────── 걷는 그림 (OBJ 8×16) ─────────
SKIN = hexrgb('#f8c898')
def spr3(pic):
    """웹 걷는 그림 16×16 → (0 투명 1밝은 2주색 3검정), 주색"""
    w, h = pic['w'], pic['h']; a = np.zeros((h, w), np.uint8); mains = {}
    for i, c in enumerate(pic['p']):
        if not c: continue
        r, g, b = hexrgb(c); L = r * .299 + g * .587 + b * .114
        if L < 100: a[i // w, i % w] = 3
        elif (r, g, b) == SKIN or L > 200: a[i // w, i % w] = 1
        else: a[i // w, i % w] = 2; mains[(r, g, b)] = mains.get((r, g, b), 0) + 1
    main = max(mains, key=mains.get) if mains else (128, 128, 128)
    return a, main
def obj_frame(a):
    """16×16 → 8×16 두 장 (왼쪽 위·아래, 오른쪽 위·아래) 타일 4개"""
    return [a[0:8, 0:8], a[8:16, 0:8], a[0:8, 8:16], a[8:16, 8:16]]
import people as _people
def tall_frame(a):
    """16×32 → 8×16 네 장: 위 왼쪽·위 오른쪽·아래 왼쪽·아래 오른쪽 (타일 8개)"""
    return obj_frame(a[0:16]) + obj_frame(a[16:32])
def kid_frames(k, full=True, nfr=3):
    """사람 걷기 그림 16×32. 이미지 AI 그림이 있으면 그것, 없으면 웹판 16×16 을 아래쪽에 붙임
    full: 앞0 앞1 뒤0 뒤1 옆0 옆1 / 아니면 nfr 장 (3: 앞·뒤·옆, 2: 앞·옆, 1: 앞)"""
    pick = [0, 1, 2, 3, 4, 5] if full else {3: [0, 2, 4], 2: [0, 4], 1: [0]}[nfr]
    ai = _people.frames(k)
    if ai:
        frs, pal = ai
        return sum((tall_frame(frs[i]) for i in pick), []), pal
    wk = W['walks'][k]
    src = [wk['down'][0], wk['down'][1], wk['up'][0], wk['up'][1], wk['left'][0], wk['left'][1]]
    tiles = []; mains = {}
    for i in pick:
        a, m = spr3(src[i]); mains[m] = mains.get(m, 0) + 1
        t = np.zeros((32, 16), np.uint8); t[16:] = a; tiles += tall_frame(t)
    main = max(mains, key=mains.get)
    return tiles, [gfx.WHITE, SKIN, main, gfx.BLACK]
def single_frame(pic, pal_override=None):
    a, m = spr3(pic)
    return obj_frame(a), [gfx.WHITE, SKIN if pal_override is None else pal_override[0], m if pal_override is None else pal_override[1], gfx.BLACK]
def blob_frames(sp):
    c1, c2 = ATTRCOL[W['species'][sp]['attr']]
    b = W['blob']; a = np.zeros((16, 16), np.uint8)
    for i, c in enumerate(b['p']):
        if not c: continue
        r, g, bb = hexrgb(c); L = r * .299 + g * .587 + bb * .114
        a[i // 16, i % 16] = 3 if L < 60 else 1 if L > 230 else (1 if L > 150 else 2)
    return obj_frame(a), [gfx.WHITE, hexrgb(c1), hexrgb(c2), gfx.BLACK]

# ───────── 음악 (music/*.json ← tools/midi2gb.py) ─────────
SONG_NAMES = ['title', 'town', 'field', 'village', 'battle', 'boss', 'evolve', 'heal']
SONGI = {n: i for i, n in enumerate(SONG_NAMES)}
SONG_INS = {'title': (0, 2, 1), 'town': (4, 3, 0), 'field': (1, 2, 1), 'village': (4, 3, 0),
            'battle': (6, 2, 3), 'boss': (0, 2, 3), 'evolve': (0, 2, 3), 'heal': (7, 2, 0)}   # 멜로디·화음 네모파 악기, 파형 악기
def enc_channel(ev, ch, ins):
    out = [0xD0 | ins]; cur = None
    for p, n in ev:
        if n != cur:
            out += [0x80 | (n - 1)] if n <= 64 else [0xC0, n]; cur = n
        out.append(p if ch == 3 else (0 if p == 0 else max(1, min(0x5F, p - 23))))
    return out + [0xFF]
SONGDATA = []
for n in SONG_NAMES:
    d = json.load(open(os.path.join(ROOT, 'music', n + '.json')))
    ins = SONG_INS[n]
    chans = [enc_channel(d['ch'][c], c, (ins[c] if c < 3 else 0)) for c in range(4)]
    speed = round(d['bpm'] * d['grid'] / 3600 * 256)
    head = [speed & 255, speed >> 8, 1 if d.get('once') else 0]
    off = 3 + 8; offs = []
    for c in chans: offs += [off & 255, off >> 8]; off += len(c)
    SONGDATA.append(head + offs + sum(chans, []))
print('음악', ' '.join('%s %dB' % (n, len(b)) for n, b in zip(SONG_NAMES, SONGDATA)), '합', sum(len(b) for b in SONGDATA))

# ───────── 지도 조립 ─────────
def u16(v): return [v & 255, (v >> 8) & 255]
def s8(v): return v & 255
MAPC = {}
for mname, M in story.MAPS.items():
    rows = [list(r) for r in M.rows]; H = len(rows); Wd = len(rows[0])
    cells = [[M.key[ch] for ch in r] for r in rows]
    for (o, ox, oy) in M.objs:
        bw, bh = big_of(o)
        for j in range(bh):
            for i in range(bw): cells[oy + j][ox + i] = o + ('@%d,%d' % (i, j) if bw * bh > 1 else '')
    border2 = None; split = 0xFF
    if M.border_fn:
        for x in range(-10, 40):
            if M.border_fn(x, 0) != M.border: split = x; border2 = M.border_fn(x, 0); break
    mts = []
    def mtid(n):
        if n not in mts: mts.append(n)
        return mts.index(n)
    cell_ids = [mtid(n) for r in cells for n in r]
    border_id = mtid(M.border); border2_id = mtid(border2) if border2 else border_id
    opens = [(o[0], o[1], o[2], o[3], mtid(o[4])) for o in M.open]
    # NPC 그림 묶음
    sprsets = []; sprtiles = []; objpals = []
    def objpal(pal):
        v = [rgb15(c) for c in pal]
        if v not in objpals: objpals.append(v)
        return objpals.index(v) + 1
    nkid = len({k for n in M.npcs for k in ((story.COMP if n.spr == 'COMP' else (n.spr,)))if k in KIDS})
    kid_nfr = 3 if nkid * 24 <= 64 else 2 if nkid * 16 <= 64 else 1      # OBJ 칸(48~111)에 맞춤
    def sprset(key):
        for i, (k2, *_r) in enumerate(sprsets):
            if k2 == key: return i
        if key in KIDS: tiles, pal = kid_frames(key, full=False, nfr=kid_nfr); nfr = kid_nfr
        elif key.startswith('blob:'): tiles, pal = blob_frames(key[5:]); nfr = 1
        else: tiles, pal = single_frame(W['walk1'][key], (hexrgb('#f8f8f8'), hexrgb('#e04838'))) if key == 'elecmon' else single_frame(W['walk1'][key]); nfr = 1
        base = 48 + len(sprtiles); sprtiles.extend(tiles)
        sprsets.append((key, base, nfr, objpal(pal))); return len(sprsets) - 1
    npcs = []
    scripts = []
    def scr(s_):
        scripts.append(s_); return len(scripts) - 1
    for n in M.npcs:
        if n.spr == 'COMP': a_ = sprset(story.COMP[0]); b_ = sprset(story.COMP[1]); altkid = KIDI[story.COMP[0]]
        else: a_ = sprset(n.spr); b_ = a_; altkid = 0xFF
        cond = 0xFFFF; ctype = 0
        if n.show_if: cond = dsl.flag(n.show_if); ctype = 1
        if n.hide_if: cond = dsl.flag(n.hide_if); ctype = 2
        tall = 8 if (n.spr == 'COMP' or n.spr in KIDS) else 0
        npcs.append((n.x, n.y, a_, b_, altkid, DIRS[n.dir], (1 if n.fixed else 0) | (ctype << 1) | tall, cond,
                     KIDI[n.hide_kid] if n.hide_kid else 0xFF, scr(n.script)))
    signs = [(s_.x, s_.y, scr(s_.script)) for s_ in M.signs]
    trigs = [(t.x, t.y, t.w, t.h, dsl.flag(t.once) if t.once else 0xFFFF, dsl.flag(t.need) if t.need else 0xFFFF,
              dsl.flag(t.unless) if t.unless else 0xFFFF, scr(t.script)) for t in M.triggers]
    on_enter = scr(M.on_enter) if M.on_enter else None
    blob, starts = dsl.assemble(scripts, CTX)
    assert len(objpals) <= 7, (mname, len(objpals))
    assert 48 + len(sprtiles) <= 112, (mname, len(sprtiles))
    # 8×8 타일 + 팔레트
    subs = []; wts = []
    use = {}
    for n in cell_ids: use[n] = use.get(n, 0) + 1
    for k_ in (border_id, border2_id): use[k_] = use.get(k_, 0) + 30
    for o in opens: use[o[4]] = use.get(o[4], 0) + 10
    for i_, n in enumerate(mts):
        px = mt_pixels(n)
        for (y, x) in [(0, 0), (0, 8), (8, 0), (8, 8)]: subs.append(px[y:y + 8, x:x + 8]); wts.append(use.get(i_, 1))
    t1_base = max(64, 48 + len(sprtiles))      # 1번 VRAM: 0~47 주인공, 48~ NPC, t1_base~191 지도 타일
    NT0, NT1 = 104, 192 - t1_base
    ai = any(mt_split(n)[0] in AS for n in mts)
    if ai:      # 이미지 AI 조각: 색을 k-평균으로 줄이고, 비슷한 타일을 합쳐 칸 수에 맞춤
        pals, fit = palfit.fit2(subs, 7, weights=wts)
        tlist, rep, reppal, thr = palfit.merge_tiles(fit, NT0 + NT1)
        fit = [(reppal[r], None) for r in rep]; tid = rep
    else:
        pals, fit = fit_palettes(subs, wts, 7)
        tl = {}; tlist = []; tid = []
        for pi, a in fit:
            k = a.astype(np.uint8).tobytes()
            if k not in tl: tl[k] = len(tlist); tlist.append(a.astype(np.uint8))
            tid.append(tl[k])
    mtdata = []
    for i, n in enumerate(mts):
        ids = [tid[i * 4 + q] for q in range(4)]; attrs = [fit[i * 4 + q][0] + 1 for q in range(4)]
        mtdata.append((ids, attrs, mt_flags(n)))
    assert len(tlist) <= NT0 + NT1, (mname, len(tlist))
    mt_bytes = []
    for ids, attrs, fl in mtdata:
        for t in ids: mt_bytes.append((152 + t) & 255 if t < NT0 else (t1_base + t - NT0))
        for t, a in zip(ids, attrs): mt_bytes.append(a | (0x08 if t >= NT0 else 0))
        mt_bytes.append(fl)
    tiles0 = sum((enc2bpp(t) for t in tlist[:NT0]), []); tiles1 = sum((enc2bpp(t) for t in tlist[NT0:]), [])
    # 확인용 그림: build/maps/<지도>.png (롬에 들어가는 색·타일 그대로, 바깥 2칸 포함)
    os.makedirs(os.path.join(ROOT, 'build', 'maps'), exist_ok=True)
    PV = np.zeros(((H + 4) * 16, (Wd + 4) * 16, 3), np.uint8)
    def mt_at_(x, y):
        if 0 <= x < Wd and 0 <= y < H: return cell_ids[y * Wd + x]
        for o in opens:
            if o[0] <= x <= o[2] and o[1] <= y <= o[3]: return o[4]
        return border2_id if split != 0xFF and x >= split else border_id
    for y in range(-2, H + 2):
        for x in range(-2, Wd + 2):
            i = mt_at_(x, y); ids, attrs, _f = mtdata[i]
            for q, (dy, dx) in enumerate([(0, 0), (0, 8), (8, 0), (8, 8)]):
                pal = np.array(pals[attrs[q] - 1], np.uint8)
                PV[(y + 2) * 16 + dy:(y + 2) * 16 + dy + 8, (x + 2) * 16 + dx:(x + 2) * 16 + dx + 8] = pal[tlist[ids[q]]]
    Image.fromarray(PV).save(os.path.join(ROOT, 'build', 'maps', mname + '.png'))
    palw = []
    for p in pals: palw += [rgb15(c) for c in p]
    while len(palw) < 28: palw.append(rgb15(gfx.WHITE))
    MAPC[mname] = dict(W=Wd, H=H, cells=cell_ids, border=border_id, split=split, border2=border2_id, opens=opens,
                       mt=mt_bytes, nmt=len(mts), tiles0=tiles0, n0=min(NT0, len(tlist)), tiles1=tiles1, n1=max(0, len(tlist) - NT0), t1_base=t1_base,
                       pal=palw, npcs=[(a[0], a[1], sprsets[a[2]][1], sprsets[a[2]][2], sprsets[a[2]][3], sprsets[a[3]][1], sprsets[a[3]][2], sprsets[a[3]][3], a[4], a[5], a[6], a[7], a[8], starts[a[9]]) for a in npcs],
                       signs=[(a[0], a[1], starts[a[2]]) for a in signs],
                       warps=[(s8(w.x), s8(w.y), MAPI[w.to], w.tx, w.ty, DIRS[w.dir] if w.dir else 0xFF) for w in M.warps],
                       trigs=[(a[0], a[1], a[2], a[3], a[4], a[5], a[6], starts[a[7]]) for a in trigs],
                       enc=M.enc, script=blob, on_enter=starts[on_enter] if on_enter is not None else 0xFFFF,
                       objpal=sum(objpals, []), nobjpal=len(objpals), spr=sum((enc2bpp(t) for t in sprtiles), []), nspr=len(sprtiles),
                       name=sid(M.name), song=SONGI[story.MAP_SONG[mname]])
    print('지도 %-8s %2d×%2d 칸종류 %2d 타일 %3d 팔레트 %d NPC %d 스크립트 %dB%s' % (mname, Wd, H, len(mts), len(tlist), len(pals), len(npcs), len(blob), ' (AI 합침 %d)' % thr if ai else ''))
OPEN_BLOB, OPEN_STARTS = dsl.assemble([story.OPENING], CTX)

# 주인공 걷는 그림 (8명 × 24타일)
KIDSPR = []; KIDPAL = []
for k in KIDS:
    tiles, pal = kid_frames(k, True); KIDSPR.append(sum((enc2bpp(t) for t in tiles), [])); KIDPAL.append([rgb15(c) for c in pal])

# ───────── 제목 화면 (금판 오마주: 위 로고 + 이미지 AI 그림) ─────────
# 팔레트 0: 글상자용, 1: 로고(밤하늘·주황·진한주황·검정), 2~7: 그림
sys.path.insert(0, os.path.join(WEB, 'tools'))
import scene as _scene, palfit
def text_px(s_, x, y, layer, v):
    cx = x
    for ch in s_:
        if ch == ' ': cx += 4; continue
        dw, w_, h_, xo, yo, rows = gfx.glyph_bits(FONT, ch)
        top = y + 12 - h_ - yo
        for j, r in enumerate(rows):
            for i, bit in enumerate(r):
                if bit and 0 <= top + j < 144 and 0 <= cx + xo + i < 160: layer[top + j, cx + xo + i] = v
        cx += dw
def text_w(s_):
    return sum(4 if ch == ' ' else gfx.glyph_bits(FONT, ch)[0] for ch in s_)
NAVY = (30, 41, 94)
TITLE_SRC = os.path.join(WEB, 'art', 'src', 'bg', 'title_ai.png')
def build_title():
    img = np.zeros((144, 160, 3), np.uint8); img[:] = NAVY
    if os.path.exists(TITLE_SRC):
        nat, _ = _scene.native(TITLE_SRC)
        band = 0
        while band < nat.shape[0] and nat[band, 80].min() > 180: band += 1      # 위쪽 빈 하늘 띠
        part = nat[band:, :160]
        h = min(144 - 40, part.shape[0]); img[144 - h:, :part.shape[1]] = part[:h]
        if part.shape[1] < 160: img[144 - h:, part.shape[1]:] = part[:h, -1:]
    # 밤하늘 별
    for (x, y) in [(12, 6), (40, 30), (70, 3), (110, 8), (150, 26), (132, 35), (25, 36), (95, 34)]: img[y, x] = (200, 220, 255)
    # 로고 (3배)
    logo = np.zeros((16, 28), np.uint8)
    for i, ch in enumerate('디지몬'): draw_glyph(logo, ch, 2 + i * 8, 0, 1)
    big = np.kron(logo, np.ones((3, 3), np.uint8)); h_, w_ = big.shape
    ox, oy = (160 - 84) // 2, -1
    ys, xs = np.where(big); sh = np.zeros_like(big)
    for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1), (1, 2), (0, 2), (2, 2), (2, 3), (1, 3)]:
        y2, x2 = ys + dy, xs + dx; ok = (y2 >= 0) & (y2 < h_) & (x2 >= 0) & (x2 < w_); sh[y2[ok], x2[ok]] = 1
    LOGO = [NAVY, (248, 168, 48), (200, 96, 24), (24, 24, 24)]
    lmask = np.zeros((144, 160), bool)
    for y in range(h_):
        for x in range(w_):
            Y, X = oy + y, ox + x
            if not (0 <= Y < 144 and 0 <= X < 160): continue
            if big[y, x]: img[Y, X] = LOGO[1] if (y // 3) % 4 < 2 else LOGO[2]; lmask[Y, X] = True
            elif sh[y, x]: img[Y, X] = LOGO[3]; lmask[Y, X] = True
    # START 글씨 (깜빡임: 글씨 없는 판도 만듦)
    plain = img.copy()
    tl = np.zeros((144, 160), np.uint8); msg = 'START를 누르세요'
    text_px(msg, (160 - text_w(msg)) // 2, 129, tl, 1)
    for y, x in zip(*np.where(tl)):
        img[y, x] = (248, 248, 248)
        for dy, dx in ((1, 0), (0, 1), (1, 1)):
            if y + dy < 144 and x + dx < 160 and not tl[y + dy, x + dx]: img[y + dy, x + dx] = (40, 36, 80)
    logo_tiles = {(ty, tx) for ty in range(18) for tx in range(20) if lmask[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].any() and ty < 5}
    subs = []; order = []
    for ty in range(18):
        for tx in range(20):
            if (ty, tx) in logo_tiles: continue
            subs.append(img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]); order.append((ty, tx))
    text_rows = sorted({y // 8 for y, x in zip(*np.where(tl))})
    for ty in text_rows:
        for tx in range(20): subs.append(plain[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]); order.append(('alt', ty, tx))
    # 글씨 줄은 따로: 그 줄의 구름 색 3개 + 흰색 (글씨가 뭉개지지 않게)
    tr = set(text_rows)
    main_i = [i for i, k in enumerate(order) if (k[0] if k[0] != 'alt' else k[1]) not in tr]
    text_i = [i for i, k in enumerate(order) if (k[0] if k[0] != 'alt' else k[1]) in tr]
    pals, res_m = palfit.fit([subs[i] for i in main_i], 5, k=24)
    rows_px = np.concatenate([plain[r * 8:r * 8 + 8].reshape(-1, 3) for r in text_rows]).astype(float)
    tc = palfit.kmeans_colors(rows_px, None, 3)
    tc = sorted([tuple(int(round(v)) for v in c) for c in tc], key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
    TPAL = [(248, 248, 248)] + tc
    TA = np.array(TPAL, float)
    res = [None] * len(subs)
    for i, r in zip(main_i, res_m): res[i] = r
    for i in text_i:
        px = subs[i].reshape(-1, 3).astype(float)
        res[i] = (5, ((px[:, None] - TA[None]) ** 2).sum(2).argmin(1).reshape(8, 8).astype(np.uint8))
    pals = pals + [TPAL]
    allp = [LOGO] + pals                       # 팔레트 1 = 로고, 2~6 = 그림, 7 = 글씨 줄
    tiles = Tiles(0); tmap = [0] * 360; amap = [0] * 360; alt = []
    for (key, (pi, t)) in zip(order, res):
        ti = tiles.add(t)
        if key[0] == 'alt': alt.append((key[1] * 20 + key[2], ti, pi + 2)); continue
        ty, tx = key; tmap[ty * 20 + tx] = ti; amap[ty * 20 + tx] = pi + 2
    LA = np.array(LOGO, float)
    for (ty, tx) in logo_tiles:
        blk = img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].reshape(-1, 3).astype(float)
        t = ((blk[:, None] - LA[None]) ** 2).sum(2).argmin(1).reshape(8, 8).astype(np.uint8)
        tmap[ty * 20 + tx] = tiles.add(t); amap[ty * 20 + tx] = 1
    # VRAM: 0번 칸 80~255 (176) → 1번 칸 0~191
    def place(ti):
        return (80 + ti, 0) if ti < 176 else (ti - 176, 0x08)
    vmap = []; vattr = []
    for ti, a_ in zip(tmap, amap): v, bnk = place(ti); vmap.append(v); vattr.append(a_ | bnk)
    valt = []
    for (pos, ti, a_) in alt: v, bnk = place(ti); valt += [pos & 255, pos >> 8, v, a_ | bnk]
    return tiles, vmap, vattr, allp, valt
TT, TMAP, TATTR, TPALS, TALT = build_title()
assert len(TT.list) <= 176 + 192, len(TT.list)
print('제목 타일', len(TT.list), '팔레트', len(TPALS))

# ───────── C 파일 쓰기 ─────────
def arr(name, data, typ='uint8_t', static=True):
    s = ('static ' if static else '') + 'const %s %s[] = {' % (typ, name)
    s += ','.join(str(int(v)) for v in data) + '};\n'
    return s

BANKS = []     # [(파일이름, 내용, 크기)]
def emit(fname, body, size):
    BANKS.append([fname, body, size])

# 글꼴
FONT_PER = 960    # 한 묶음 글자 수 (15KB)
NFONT = (len(CHARS) + FONT_PER - 1) // FONT_PER
for i in range(NFONT):
    part = FONTDATA[i * FONT_PER * 16:(i + 1) * FONT_PER * 16]
    emit('font%d.c' % i, arr('font%d' % i, part, static=False), len(part))
# 문자열 (묶음 12KB)
STRB = []; cur = []; cursz = 0; STRLOC = []
for i, s_ in enumerate(S.items):
    b = S.encode(s_)
    if cursz + len(b) > 12000: STRB.append(cur); cur = []; cursz = 0
    STRLOC.append((len(STRB), cursz)); cur.append(b); cursz += len(b)
STRB.append(cur)
for i, chunk in enumerate(STRB):
    emit('str%d.c' % i, arr('strs%d' % i, sum(chunk, []), static=False), sum(len(b) for b in chunk))
# 그림
PICB = []; cur = []; cursz = 0; PICLOC = []
for name, b in PICS:
    if cursz + len(b) > 15500: PICB.append(cur); cur = []; cursz = 0
    PICLOC.append((len(PICB), cursz)); cur.append(b); cursz += len(b)
PICB.append(cur)
for i, chunk in enumerate(PICB):
    emit('pics%d.c' % i, arr('pics%d' % i, sum(chunk, []), static=False), sum(len(b) for b in chunk))
# 화면 부품 + 제목 + 주인공 그림 + 오프닝
misc = arr('ui_tiles', sum((enc2bpp(t) for t in UIT), []), static=False)
TD = TT.data()
misc += arr('title_tiles', TD[:176 * 16], static=False) + arr('title_tiles1', TD[176 * 16:] or [0], static=False) + arr('title_map', TMAP, static=False) + arr('title_attr', TATTR, static=False) + arr('title_alt', TALT or [0], static=False)
misc += arr('kid_spr', sum(KIDSPR, []), static=False)
misc += arr('opening', OPEN_BLOB, static=False)
emit('misc.c', misc, len(UIT) * 16 + len(TT.list) * 16 + 720 + len(sum(KIDSPR, [])) + len(OPEN_BLOB) + 3 * (len(STRLOC) + len(PICLOC)) + 64)   # 문자열·그림 목록표는 뱅크가 정해진 뒤 덧붙임
# 지도
for mname, d in MAPC.items():
    b = ''
    b += arr('cells', d['cells']) + arr('mt', d['mt']) + arr('t0', d['tiles0'] or [0]) + arr('t1', d['tiles1'] or [0])
    b += arr('pal', d['pal'], 'uint16_t') + arr('objpal', d['objpal'] or [0], 'uint16_t') + arr('spr', d['spr'] or [0])
    opens = sum(([s8(o[0]), s8(o[1]), s8(o[2]), s8(o[3]), o[4]] for o in d['opens']), [])
    b += arr('opens', opens or [0])
    npc = sum(([a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10]] + u16(a[11]) + [a[12]] + u16(a[13]) for a in d['npcs']), [])
    b += arr('npcs', npc or [0])
    b += arr('signs', sum(([a[0], a[1]] + u16(a[2]) for a in d['signs']), []) or [0])
    b += arr('warps', sum((list(w) for w in d['warps']), []) or [0])
    b += arr('trigs', sum(([a[0], a[1], a[2], a[3]] + u16(a[4]) + u16(a[5]) + u16(a[6]) + u16(a[7]) for a in d['trigs']), []) or [0])
    enc = d['enc']
    encb = [] if not enc else sum(([SPI[e[0]], e[1], e[2], e[3]] for e in enc[1]), [])
    b += arr('enc', encb or [0])
    b += arr('script', d['script'] or [0])
    b += ('const map_t map_%s = { %d, %d, %d, %d, %d, %d, opens, cells, %d, mt, %d, t0, %d, t1, pal, %d, npcs, %d, signs, %d, warps, %d, trigs, %d, %d, enc, script, %d, %d, objpal, %d, spr, %d, %d, %d };\n'
          % (mname, d['W'], d['H'], d['border'], d['split'], d['border2'], len(d['opens']), d['nmt'], d['n0'], d['n1'],
             len(d['npcs']), len(d['signs']), len(d['warps']), len(d['trigs']), enc[0] if enc else 0, len(enc[1]) if enc else 0,
             d['on_enter'], d['nobjpal'], d['nspr'], d['name'], d['t1_base'], d['song']))
    size = len(d['cells']) + len(d['mt']) + len(d['tiles0']) + len(d['tiles1']) + 56 + len(d['objpal']) * 2 + len(d['spr']) + len(d['script']) + 600
    emit('map_%s.c' % mname, b, size)

# 음악: 소리 엔진 + 곡 자료를 한 뱅크에
mb = ''
for i, b in enumerate(SONGDATA): mb += arr('song%d' % i, b)
mb += 'static const uint8_t * const SONGTAB[] = {' + ','.join('song%d' % i for i in range(len(SONGDATA))) + '};\n'
mb += '#include "../../src/music_drv.inc"\n'
assert sum(len(b) for b in SONGDATA) + 1500 < 16000, '음악이 한 뱅크를 넘음'
emit('music.c', mb, 16000)

# 묶음을 뱅크에 담기 (코드 뱅크 1·2 다음부터)
FIRST_DATA_BANK = 3
banks = []     # [[크기, [파일...]]]
for f in sorted(BANKS, key=lambda x: -x[2]):
    for bk in banks:
        if bk[0] + f[2] <= 16000: bk[0] += f[2]; bk[1].append(f); break
    else: banks.append([f[2], [f]])
BANKOF = {}
for i, bk in enumerate(banks):
    for f in bk[1]: BANKOF[f[0]] = FIRST_DATA_BANK + i
B = BANKOF
for bk in BANKS:
    if bk[0] == 'misc.c':      # 0번 뱅크를 비우려고 목록표를 MISC 뱅크로
        bk[1] += 'const farptr_t STRTAB[] = {' + ','.join('{%d,strs%d+%d}' % (B['str%d.c' % b_], b_, o) for (b_, o) in STRLOC) + '};\n'
        bk[1] += 'const farptr_t PICTAB[] = {' + ','.join('{%d,pics%d+%d}' % (B['pics%d.c' % b_], b_, o) for (b_, o) in PICLOC) + '};\n'
        bk[1] = ''.join('extern const uint8_t strs%d[];\n' % i for i in range(len(STRB))) + ''.join('extern const uint8_t pics%d[];\n' % i for i in range(len(PICB))) + bk[1]
for fname, body, size in BANKS:
    with open(os.path.join(GEN, fname), 'w') as fh:
        fh.write('#pragma bank %d\n#include <gbdk/platform.h>\n#include <stdint.h>\n#include "../../src/data.h"\n' % BANKOF[fname] + body)
NBANKS = FIRST_DATA_BANK + len(banks)
print('데이터 뱅크', len(banks), '(전체 롬 뱅크', NBANKS, ')')

# 표 (0번 뱅크)
B = BANKOF
t = '#include <gbdk/platform.h>\n#include <stdint.h>\n#include "../../src/data.h"\n#include "gen.h"\n'
for i in range(NFONT): t += 'extern const uint8_t font%d[];\n' % i
for i in range(len(STRB)): t += 'extern const uint8_t strs%d[];\n' % i
for i in range(len(PICB)): t += 'extern const uint8_t pics%d[];\n' % i
t += 'extern const uint8_t ui_tiles[], title_tiles[], title_tiles1[], title_map[], title_attr[], title_alt[], kid_spr[], opening[];\n'
for m in MAPNAMES: t += 'extern const map_t map_%s;\n' % m
t += 'const farptr_t FONTS[] = {' + ','.join('{%d,font%d}' % (B['font%d.c' % i], i) for i in range(NFONT)) + '};\n'
t += 'const farmap_t MAPTAB[] = {' + ','.join('{%d,&map_%s}' % (B['map_%s.c' % m], m) for m in MAPNAMES) + '};\n'
t += 'const uint8_t MISC_BANK = %d;\n' % B['misc.c']
t += arr('CHARFLAG', CHARFLAG, static=False)
sp_rows = []
for i, sp in enumerate(SPECIES):
    d = W['species'][sp]; evo = (d.get('evo') or [None])[0]
    need = 0xFF if not evo or not evo.get('need') else (0xFE if evo['need'] == 'event' else CRESTI[evo['need']])
    sig = [MOVEI[n] for n in d['sig']][:3] + [0xFF] * 3
    sp_rows.append('{%d,%d,{%s},%d,%d,%d,%d,{%d,%d,%d},%d,%d,%d,%d,%d}' % (
        TIERS.index(d['tier']), ATTRS.index(d['attr']), ','.join(str(v) for v in d['base']), d['exp'],
        SPI[evo['to']] if evo else 0xFF, evo['lv'] if evo else 0, need, sig[0], sig[1], sig[2],
        SP_NAME[i], SP_GRADE[i], SP_TYPE[i], SP_FRONT[i], SP_BACK[i]))
t += 'const species_t SPECIES[] = {' + ','.join(sp_rows) + '};\n'
t += 'const move_t MOVES[] = {' + ','.join('{%d,%d,%d,%d,%d,%d}' % (MV_NAME[i], m[1], m[2], m[3], m[4], m[5]) for i, m in enumerate(MOVES)) + '};\n'
tb = []
for tr in TIERS:
    l = [MOVEI[n] for n in TIER_BASIC[tr]] + [0xFF]; tb += l[:2]
t += arr('TIER_BASIC', tb, static=False)
t += arr('ATTR_NAME', ATTR_NAME, 'uint16_t', static=False)
t += arr('KID_NAME', KID_NAME, 'uint16_t', static=False) + arr('KID_CRESTS', KID_CRESTS, 'uint16_t', static=False) + arr('KID_DESC', KID_DESC, 'uint16_t', static=False)
t += arr('KID_PARTNER', [SPI[story.PARTNER[k]] for k in KIDS], static=False)
t += arr('KID_BABY', [SPI[story.BABY[k]] for k in KIDS], static=False)
t += arr('KID_PAL', sum(KIDPAL, []), 'uint16_t', static=False)
t += arr('EGGS', [SPI[e] for e in story.EGGS], static=False)
t += arr('IT_NAME', IT_NAME, 'uint16_t', static=False) + arr('IT_DESC', IT_DESC, 'uint16_t', static=False)
t += arr('IT_HEAL', [it[1] for it in story.ITEMS], static=False) + arr('IT_KIND', [it[3] for it in story.ITEMS], static=False)
t += arr('IT_PRICE', [it[4] for it in story.ITEMS], 'uint16_t', static=False)
t += arr('CREST_NAME', CREST_NAME, 'uint16_t', static=False)
t += arr('TITLE_PAL', sum(([rgb15(c) for c in p] for p in TPALS), []), 'uint16_t', static=False)
# 글자 번호 (엔진에서 쓰는 것)
DIG = [S.charidx[d] for d in '0123456789']
t += arr('DIGCH', DIG, 'uint16_t', static=False)
JO = [S.charidx[c] for c in '이가은는을를과와으로']
t += arr('JOSACH', JO, 'uint16_t', static=False)
t += arr('BMAP', sum(([x, y, v] for (x, y), v in sorted(BMAP.items())), []), static=False)
open(os.path.join(GEN, 'tables.c'), 'w').write(t)

h = '#ifndef GEN_H\n#define GEN_H\n'
h += '#define N_SPECIES %d\n#define N_MOVES %d\n#define N_MAPS %d\n#define N_KIDS %d\n#define N_ITEMS %d\n#define N_CRESTS %d\n#define N_CHARS %d\n#define FONT_PER %d\n#define N_EGGS %d\n#define N_BMAP %d\n' % (
    len(SPECIES), len(MOVES), len(MAPNAMES), len(KIDS), len(story.ITEMS), len(story.CRESTS), len(CHARS), FONT_PER, len(story.EGGS), len(BMAP))
h += '#define N_TITLE0 %d\n#define N_TITLE1 %d\n#define N_TITLE_PAL %d\n#define N_TITLE_ALT %d\n#define N_UI_TILES %d\n#define PIC_EGG %d\n' % (min(176, len(TT.list)), max(0, len(TT.list) - 176), len(TPALS), len(TALT) // 4, len(UIT), PIC_EGG)
for k, v in UI.items(): h += '#define T_%s %d\n' % (k, v)
for k, v in ESID.items(): h += '#define S_%s %d\n' % (k.upper(), v)
for k, v in SPI.items(): h += '#define SP_%s %d\n' % (k.upper(), v)
for k, v in MAPI.items(): h += '#define MAP_%s %d\n' % (k.upper(), v)
for k, v in KIDI.items(): h += '#define KID_%s %d\n' % (k.upper(), v)
for k, v in dsl.OP.items(): h += '#define OP_%s %d\n' % (k, v)
h += '#define START_MAP %d\n#define START_X %d\n#define START_Y %d\n#define START_DIR %d\n' % (MAPI[story.START[0]], story.START[1], story.START[2], DIRS[story.START[3]])
h += '#define N_FLAGS %d\n' % len(dsl.FLAGS)
h += '#define CH_SPACE %d\n' % S.charidx[' ']
h += '#define COMP_KID %d\n#define COMP_ALT %d\n' % (KIDI[story.COMP[0]], KIDI[story.COMP[1]])
for k, v in SONGI.items(): h += '#define SONG_%s %d\n' % (k.upper(), v)
h += '#endif\n'
open(os.path.join(GEN, 'gen.h'), 'w').write(h)
print('깃발', len(dsl.FLAGS), '문자열', len(S.items), '기술', len(MOVES))

# ───────── 컴파일 ─────────
SRC = os.path.join(ROOT, 'src')
srcs = [os.path.join(SRC, f) for f in sorted(os.listdir(SRC)) if f.endswith('.c')]
gens = [os.path.join(GEN, f) for f in sorted(os.listdir(GEN)) if f.endswith('.c')]
romb = 1
while romb < NBANKS: romb *= 2
OUT = os.path.join(ROOT, 'digimon.gbc')
cmd = ['/opt/gbdk/bin/lcc', '-Wl-m', '-Wl-j', '-Wm-yC', '-Wm-yn"DIGIMON"', '-Wl-yt0x1B', '-Wl-yo%d' % romb, '-Wl-ya1', '-I' + GEN, '-o', OUT] + srcs + gens
if '--nocompile' not in sys.argv:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.join(ROOT, 'build'))
    print(r.stdout[-3000:], r.stderr[-6000:])
    if r.returncode: sys.exit(r.returncode)
    print('롬', OUT, os.path.getsize(OUT), 'bytes')
