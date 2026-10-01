"""디지몬스터 롬 조사: 종마다 이름·능력치·속성(타입)·진화·그림 → work/audit.json, work/sheet*.png"""
import os, re, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import dmrom, krtext
r = dmrom.Rom(dmrom.default_rom())
KR = os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr')      # github.com/Narishma-gb/pokegold-kr 받은 곳
NAMES = os.path.join(KR, 'data/pokemon/names.asm')
ORIG = [re.search(r'dname "(.*)"', l).group(1) for l in open(NAMES) if 'dname' in l] if os.path.exists(NAMES) else []
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 12)
out = []
for sp in range(1, 252):
    nm = r.name(sp); bs = r.base_stats(sp)
    try: ev, mv = r.evos_attacks(sp)
    except Exception: ev, mv = [], []
    still_pkmn = bool(ORIG) and nm == ORIG[sp - 1]
    out.append({'no': sp, 'name': nm, 'orig': ORIG[sp - 1] if ORIG else '', 'pokemon': still_pkmn, 'type': bs['type'], 'catch': bs['catch'],
                'stats': [bs[k] for k in ('hp', 'atk', 'def', 'spd', 'sat', 'sdf')], 'evos': ev, 'moves': mv})
json.dump(out, open(os.path.join(dmrom.WORK, 'audit.json'), 'w'), ensure_ascii=False, indent=0)
print('포켓몬 그대로', sum(o['pokemon'] for o in out), '/ 251')
# 그림 묶음
cell = 72
for page in range(0, 251, 64):
    im = Image.new('RGB', (8 * cell, 8 * (cell + 16)), (40, 44, 52)); dr = ImageDraw.Draw(im)
    for i, sp in enumerate(range(page + 1, min(page + 65, 252))):
        x, y = (i % 8) * cell, (i // 8) * (cell + 16)
        a = r.pic(sp)
        if a is not None:
            c1, c2 = r.palette(sp)
            pal = np.array([(248, 248, 248), c1, c2, (24, 24, 24)], np.uint8)
            p = Image.fromarray(pal[a]); im.paste(p, (x + (cell - p.width) // 2, y + 16 + (56 - p.height)))
        col = (255, 120, 120) if out[sp - 1]['pokemon'] else (180, 230, 180)
        dr.text((x + 2, y), '%d %s' % (sp, out[sp - 1]['name']), fill=col, font=FONT)
    im.save(os.path.join(dmrom.WORK, 'sheet%d.png' % (page // 64)))
