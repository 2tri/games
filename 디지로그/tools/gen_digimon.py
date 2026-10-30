#!/usr/bin/env python3
"""디지골드 자료(data/digimon.json) → 포케로그 소스(src/) 에 디지몬 데이터·이름·그림을 넣는다.
python tools/gen_digimon.py   (디지로그 폴더에서)
- src/src/data/balance/digimon-data.ts  : 188종 데이터(능력치·타입·특성·레벨 기술·진화·시작 비용)
- src/locales/{ko,en}/pokemon.json        : 종 이름
- src/locales/{ko,en}/move.json           : 디지몬이 배우는 기술 이름(디지골드 한글 이름)
- src/locales/{ko,en}/pokemon-info.json   : 타입 이름(디지골드 이름)
- src/locales/{ko,en}/modifier-type.json  : 진화 도구 이름(태그·문장·디지멘탈·진화칩)
- src/assets/images/pokemon/**            : 전투 그림 앞·뒤·반짝이, 아이콘
여러 번 돌려도 같은 결과(원본은 처음 한 번 .orig 로 보관)."""
import json, os, re, shutil, colorsys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); SRC = os.path.join(ROOT, 'src')
D = json.load(open(os.path.join(ROOT, 'data', 'digimon.json'), encoding='utf-8'))
S = {int(k): v for k, v in D['species'].items()}

def enum_names(path, first_value):
    """TS enum 을 (값 → 이름) 으로. 명시값이 있으면 거기서부터 이어 셈"""
    out = {}; v = first_value - 1
    for line in open(path, encoding='utf-8'):
        m = re.match(r'\s*([A-Z0-9_]+)\s*(?:=\s*(-?\d+))?\s*,', line)
        if not m: continue
        v = int(m.group(2)) if m.group(2) is not None else v + 1
        out[v] = m.group(1)
    return out
SPC = enum_names(os.path.join(SRC, 'src/enums/species-id.ts'), 1)
MOV = enum_names(os.path.join(SRC, 'src/enums/move-id.ts'), 0)
ABL = enum_names(os.path.join(SRC, 'src/enums/ability-id.ts'), 0)
assert SPC[1] == 'BULBASAUR' and SPC[493] == 'ARCEUS', (SPC[1], SPC[493])
assert MOV[1] == 'POUND' and MOV[33] == 'TACKLE', (MOV[1], MOV[33])
assert ABL[65] == 'OVERGROW', ABL[65]

def camel(n): p = n.lower().split('_'); return p[0] + ''.join(x.title() for x in p[1:])

# 하트골드 타입 번호 → 포케로그 PokemonType (9번 ??? 칸은 디지골드에서 「빛」 → 페어리 자리)
def ptype(t): return 17 if t == 9 else (t if t < 9 else t - 1)
# 하트골드 성장 곡선 → 포케로그 GrowthRate
GROWTH = {0: 'MEDIUM_FAST', 1: 'ERRATIC', 2: 'FLUCTUATING', 3: 'MEDIUM_SLOW', 4: 'FAST', 5: 'SLOW'}
STAGE_LV = {'성장기': 1, '성숙기': 16, '완전체': 32, '궁극체': 48, '아머체': 25, '유년기Ⅱ': 1}
# 디지골드 진화 도구(아이템 번호) → 포케로그 진화 도구 칸, 표시 이름
SPECIAL = {227: ('SHINY_STONE', '궁극의 문장'), 108: ('DUSK_STONE', '어둠의 돌'), 82: ('FIRE_STONE', '용기의 디지멘탈'),
           83: ('THUNDER_STONE', '우정의 디지멘탈'), 80: ('SUN_STONE', '사랑의 디지멘탈'), 81: ('ICE_STONE', '지식의 디지멘탈'),
           84: ('WATER_STONE', '성실의 디지멘탈'), 85: ('LEAF_STONE', '순수의 디지멘탈'), 109: ('DAWN_STONE', '희망의 디지멘탈'),
           107: ('MOON_STONE', '빛의 디지멘탈'), 110: ('OVAL_STONE', '기적의 디지멘탈'), 326: ('DUBIOUS_DISC', '검은 톱니'),
           225: ('RAZOR_CLAW', '오메가블레이드'), 233: ('UPGRADE', '금속 코트')}
CHIPS = [('LINKING_CORD', '백신 진화칩', '백신'), ('SWEET_APPLE', '데이터 진화칩', '데이터'), ('TART_APPLE', '바이러스 진화칩', '바이러스'), ('PROTECTOR', '프리 진화칩', None)]
ITEM_NAMES = {k: v for k, v in SPECIAL.values()} | {c[0]: c[1] for c in CHIPS}
DEFAULT_STARTERS = ['아구몬', '텐타몬', '피요몬', '팔몬', '브이몬', '호크몬', '아르마몬', '케라몬', '베타몬']

pre = {}
for sid, v in S.items():
    for e in v['evos']: pre.setdefault(e[2], []).append(sid)
roots = [sid for sid in S if sid not in pre]
root_of = {}
def mark(sid, r):
    if sid in root_of: return
    root_of[sid] = r
    for e in S[sid]['evos']: mark(e[2], r)
for r in sorted(roots): mark(r, r)

def cost(bst):
    for c, lim in enumerate((300, 340, 380, 420, 460, 500, 540, 580, 620), 1):
        if bst <= lim: return c
    return 10
def egg_tier(c): return 'COMMON' if c <= 3 else 'RARE' if c <= 5 else 'EPIC' if c <= 7 else 'LEGENDARY'

# 서로 진화하는 순환(황제드라몬 ↔ 황제파이터 모드 등)은 되돌아가는 쪽을 뺀다
def reach(a, b, seen=None):
    seen = seen or set()
    if a == b: return True
    seen.add(a)
    return any(reach(t, b, seen) for _, _, t, _, _ in S[a]['evos'] if t not in seen)
for sid in sorted(S):
    S[sid]['evos'] = [e for e in S[sid]['evos'] if not reach(e[2], sid)]

recs = []
for sid in sorted(S):
    v = S[sid]; bst = sum(v['stats'])
    evos = []; used_chips = set(); first_level = True
    for m, prm, t, mname, tname in v['evos']:
        tstage = S[t]['stage']
        if m in (6, 7, 16, 17, 18, 19) and prm in SPECIAL and prm != 226:
            evos.append({'to': t, 'item': SPECIAL[prm][0]})
            continue
        lv = prm if m == 4 else STAGE_LV.get(tstage, 30) + (4 if m in (20, 21) else 0)
        if first_level:
            evos.append({'to': t, 'level': max(1, lv)}); first_level = False
        else:
            want = S[t].get('attr'); pick = None
            for c in CHIPS:
                if c[2] == want and c[0] not in used_chips: pick = c[0]; break
            if not pick:
                pick = next(c[0] for c in CHIPS if c[0] not in used_chips)
            used_chips.add(pick); evos.append({'to': t, 'item': pick, 'level': max(1, lv)})
    t1, t2 = ptype(v['types'][0]), ptype(v['types'][1])
    a1, a2 = v['abilities']
    is_root = sid in roots
    c = cost(bst) if is_root else None
    recs.append({
        'id': sid, 'enum': SPC[sid], 'name': v['name'], 'stage': v['stage'], 'attr': v.get('attr'),
        'type1': t1, 'type2': None if t2 == t1 else t2,
        'ability1': a1, 'ability2': a2 if a2 else a1, 'stats': v['stats'], 'bst': bst,
        'catch': v['catch'], 'exp': v['exp'], 'growth': GROWTH.get(v['growth'], 'MEDIUM_FAST'),
        'male': None if v['gender'] == 255 else 100 if v['gender'] == 0 else 0 if v['gender'] == 254 else round((256 - v['gender']) / 256 * 100, 1),
        'levelMoves': [[lv, mv] for lv, mv, _ in v['learnset'] if mv in MOV],
        'evos': evos, 'starter': root_of[sid], 'cost': c, 'eggTier': egg_tier(c) if c else None,
        'legendary': is_root and v['stage'] == '궁극체',
    })

defaults = [r['id'] for r in recs if r['name'] in DEFAULT_STARTERS and r['cost']]
assert len(defaults) == len(DEFAULT_STARTERS), defaults

ts = ['// 자동 생성: 디지로그/tools/gen_digimon.py — 직접 고치지 말 것', '/* biome-ignore-all lint: 생성 파일 */',
      'export interface DigimonRecord { id: number; enum: string; name: string; stage: string; attr: string | null; type1: number; type2: number | null; ability1: number; ability2: number;',
      '  stats: number[]; bst: number; catch: number; exp: number; growth: string; male: number | null; levelMoves: [number, number][];',
      '  evos: { to: number; level?: number; item?: string }[]; starter: number; cost: number | null; eggTier: string | null; legendary: boolean; }',
      'export const DIGIMON_RECORDS: DigimonRecord[] = ' + json.dumps(recs, ensure_ascii=False) + ';',
      'export const DIGIMON_DEFAULT_STARTERS: number[] = ' + json.dumps(defaults) + ';', '']
open(os.path.join(SRC, 'src/data/balance/digimon-data.ts'), 'w', encoding='utf-8').write('\n'.join(ts))

# ---------- 번역 ----------
def backup(p):
    if not os.path.exists(p + '.orig'): shutil.copyfile(p, p + '.orig')
    return json.load(open(p + '.orig', encoding='utf-8'))
used_moves = sorted({mv for r in recs for _, mv in r['levelMoves']})
for lang in ('ko', 'en'):
    base = os.path.join(SRC, 'locales', lang)
    p = os.path.join(base, 'pokemon.json'); j = backup(p)
    for r in recs: j[camel(r['enum'])] = r['name']
    json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    p = os.path.join(base, 'move.json'); j = backup(p)
    for mv in used_moves:
        k = camel(MOV[mv])
        if k in j and D['moves'][mv]: j[k]['name'] = D['moves'][mv]
    json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    p = os.path.join(base, 'pokemon-info.json'); j = backup(p)
    keys = ['normal', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel', None, 'fire', 'water', 'grass', 'electric', 'psychic', 'ice', 'dragon', 'dark']
    for i, k in enumerate(keys):
        if k: j['type'][k] = D['types'][i]
    j['type']['fairy'] = D['types'][9]
    json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    p = os.path.join(base, 'modifier-type.json'); j = backup(p)
    for k, n in ITEM_NAMES.items():
        if k in j['EvolutionItem']: j['EvolutionItem'][k] = n
    json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ---------- 그림 ----------
IMG = os.path.join(SRC, 'assets/images/pokemon'); SPR = os.path.join(ROOT, 'data/sprites')
def load_sprite(path):
    im = Image.open(path).convert('RGBA'); px = im.load(); bg = px[0, 0]
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == bg: px[x, y] = (0, 0, 0, 0)
    bb = im.getbbox() or (0, 0, 1, 1); return im.crop(bb)
def shiny(im):
    out = im.copy(); px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if not a: continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255); r2, g2, b2 = colorsys.hsv_to_rgb((h + .42) % 1, s, v)
            px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return out
def write_atlas(im, folder, sid):
    os.makedirs(folder, exist_ok=True)
    w, h = im.size
    im.save(os.path.join(folder, '%d.png' % sid))
    fr = {'filename': '0001.png', 'rotated': False, 'trimmed': False, 'sourceSize': {'w': w, 'h': h},
          'spriteSourceSize': {'x': 0, 'y': 0, 'w': w, 'h': h}, 'frame': {'x': 0, 'y': 0, 'w': w, 'h': h}}
    json.dump({'textures': [{'image': '%d.png' % sid, 'format': 'RGBA8888', 'size': {'w': w, 'h': h}, 'scale': 1, 'frames': [fr]}]},
              open(os.path.join(folder, '%d.json' % sid), 'w'))
def keep_orig(folder, sid):
    for ext in ('png', 'json'):
        p = os.path.join(folder, '%d.%s' % (sid, ext))
        if os.path.exists(p) and not os.path.exists(p + '.orig'): shutil.copyfile(p, p + '.orig')
icons = {}
for r in recs:
    sid = r['id']; f = load_sprite(os.path.join(SPR, '%03d_front.png' % sid)); b = load_sprite(os.path.join(SPR, '%03d_back.png' % sid))
    for folder, im in ((IMG, f), (os.path.join(IMG, 'back'), b), (os.path.join(IMG, 'shiny'), shiny(f)), (os.path.join(IMG, 'back/shiny'), shiny(b))):
        keep_orig(folder, sid); write_atlas(im, folder, sid)
    ic = f.copy(); ic.thumbnail((40, 30), Image.NEAREST); icons[sid] = ic
# 실험 그림·변형색 목록에서 디지몬 칸 빼기
ids = {str(r['id']) for r in recs}
p = os.path.join(SRC, 'assets/exp-sprites.json'); j = backup(p); json.dump([x for x in j if x.split('-')[0] not in ids], open(p, 'w'), indent=2)
for name in ('_masterlist.json', '_exp_masterlist.json'):
    p = os.path.join(IMG, 'variant', name); j = backup(p)
    if isinstance(j, dict): j = {k: v for k, v in j.items() if k.split('-')[0] not in ids}
    json.dump(j, open(p, 'w'), indent=2)
# 아이콘 시트(세대별): 디지몬 칸은 새 그림을 시트 아래에 붙이고 위치만 바꾼다
GEN = lambda sid: 1 if sid <= 151 else 2 if sid <= 251 else 3 if sid <= 386 else 4
for g in (1, 2, 3, 4):
    pj = os.path.join(SRC, 'assets/images/pokemon_icons_%d.json' % g); pp = pj[:-5] + '.png'
    j = backup(pj)
    if not os.path.exists(pp + '.orig'): shutil.copyfile(pp, pp + '.orig')
    sheet = Image.open(pp + '.orig').convert('RGBA')
    tex = j['textures'][0] if 'textures' in j else j
    mine = sorted(s for s in icons if GEN(s) == g)
    cols = max(1, sheet.width // 40); rows = (len(mine) + cols - 1) // cols
    new = Image.new('RGBA', (sheet.width, sheet.height + rows * 30)); new.paste(sheet, (0, 0))
    place = {}
    for i, s in enumerate(mine):
        x, y = (i % cols) * 40, sheet.height + (i // cols) * 30; ic = icons[s]
        new.paste(ic, (x + (40 - ic.width) // 2, y + (30 - ic.height)), ic); place[s] = (x, y)
    for fr in tex['frames']:
        m = re.match(r'^(\d+)(s?)$', fr['filename'])
        if m and int(m.group(1)) in place:
            x, y = place[int(m.group(1))]
            fr.update({'trimmed': False, 'sourceSize': {'w': 40, 'h': 30}, 'spriteSourceSize': {'x': 0, 'y': 0, 'w': 40, 'h': 30}, 'frame': {'x': x, 'y': y, 'w': 40, 'h': 30}})
    tex['size'] = {'w': new.width, 'h': new.height}
    new.save(pp); json.dump(j, open(pj, 'w'))
print('디지몬', len(recs), '기본 시작', [r['name'] for r in recs if r['id'] in defaults], '기술 이름', len(used_moves))
print('시작 후보', sum(1 for r in recs if r['cost']), '진화', sum(len(r['evos']) for r in recs), '도구 진화', sum(1 for r in recs for e in r['evos'] if 'item' in e))
