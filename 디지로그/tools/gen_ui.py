#!/usr/bin/env python3
"""디지로그 화면 손질: 타입 표시 그림(디지골드 타입 이름), 시작 디지몬 사탕 색, 화면 문구(포켓몬→디지몬 등). 여러 번 돌려도 같은 결과."""
import json, os, shutil, re, glob
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); SRC = os.path.join(ROOT, 'src')
def orig(p):
    if not os.path.exists(p + '.orig'): shutil.copyfile(p, p + '.orig')
    return p + '.orig'
# 1) 타입 표시 그림
NEW = {'bug': '곤충', 'dark': '암흑', 'dragon': '용', 'electric': '번개', 'fairy': '빛', 'fire': '화염', 'flying': '바람',
       'grass': '식물', 'ground': '대지', 'rock': '암석', 'steel': '기계'}
font = ImageFont.truetype(os.path.join(HERE, 'Galmuri9.ttf'), 12)
pj = os.path.join(SRC, 'assets/images/types_ko.json'); pp = pj[:-5] + '.png'
j = json.load(open(orig(pj), encoding='utf-8')); im = Image.open(orig(pp)).convert('RGBA')
for fr in (j['textures'][0] if 'textures' in j else j)['frames']:
    name = fr['filename']
    if name not in NEW: continue
    f = fr['frame']; x0, y0, w, h = f['x'], f['y'], f['w'], f['h']
    tile = im.crop((x0, y0, x0 + w, y0 + h)); px = tile.load()
    for y in range(1, h - 1):                                  # 줄마다 왼쪽 안쪽(글자 없는 곳) 색으로 바탕 다시 칠하기
        c = px[2, y]
        if sum(c[:3]) > 690 and y + 1 < h - 1: c = px[2, y + 1]   # 흰 테두리 줄은 피하기
        for x in range(2, w - 2): px[x, y] = c
    shade = tuple(max(0, v - 70) for v in px[2, h // 2][:3]) + (255,)
    d = ImageDraw.Draw(tile); d.fontmode = '1'; text = NEW[name]
    tw = d.textlength(text, font=font); tx = round((w - tw) / 2); ty = round((h - 12) / 2)
    d.text((tx, ty + 1), text, font=font, fill=shade)
    d.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    im.paste(tile, (x0, y0))
im.save(pp)
# 2) 시작 디지몬 사탕 색(앞모습 그림에서 진한 색·밝은 색 두 개)
recs = json.loads(re.search(r'DIGIMON_RECORDS: DigimonRecord\[\] = (\[.*?\]);\n', open(os.path.join(SRC, 'src/data/balance/digimon-data.ts'), encoding='utf-8').read(), re.S).group(1))
pc = os.path.join(SRC, 'assets/starter-colors.json'); col = json.load(open(orig(pc)))
for r in recs:
    if not r['cost']: continue
    s = Image.open(os.path.join(SRC, 'assets/images/pokemon/%d.png' % r['id'])).convert('RGBA')
    pix = [p[:3] for p in s.getdata() if p[3] > 0 and sum(p[:3]) > 60]
    q = Image.new('RGB', (len(pix), 1)); q.putdata(pix); q = q.quantize(4)
    pal = q.getpalette()[:12]; cnt = sorted(q.getcolors(), reverse=True)
    cs = [tuple(pal[i * 3:i * 3 + 3]) for _, i in cnt]
    cs.sort(key=lambda c: sum(c)); dark, light = cs[0], cs[-1]
    col[str(r['id'])] = ['%02x%02x%02x' % dark, '%02x%02x%02x' % light]
json.dump(col, open(pc, 'w'))
# 3) 화면 문구
REP = [('포켓로그', '디지로그'), ('PokéRogue', '디지로그'), ('포켓몬', '디지몬'), ('몬스터볼', '디지볼'), ('슈퍼볼', '슈퍼디지볼'), ('하이퍼볼', '울트라디지볼'), ('마스터볼', '마스터디지볼')]
def fix(v):
    if isinstance(v, str):
        for a, b in REP: v = v.replace(a, b)
        return v
    if isinstance(v, dict): return {k: fix(x) for k, x in v.items()}
    if isinstance(v, list): return [fix(x) for x in v]
    return v
SKIP = {'pokemon.json', 'move.json', 'pokemon-info.json', 'modifier-type.json'}   # gen_digimon.py 가 관리(그쪽 원본에서 다시 만들어짐)
n = 0
for p in glob.glob(os.path.join(SRC, 'locales/ko/**/*.json'), recursive=True):
    base = os.path.basename(p)
    src = p + '.orig' if os.path.exists(p + '.orig') else p
    if base in SKIP: j = json.load(open(p, encoding='utf-8'))
    else: j = json.load(open(orig(p), encoding='utf-8'))
    k = fix(j)
    if k != j: n += 1
    json.dump(k, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('타입 그림', len(NEW), '사탕 색', sum(1 for r in recs if r['cost']), '문구 파일', n)
