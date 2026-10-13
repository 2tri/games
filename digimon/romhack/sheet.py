"""14판 검수용: 롬에 들어간 전투 그림(앞·뒤)을 한 장에. python3 sheet.py [롬] → work/sheet_f.png, work/sheet_b.png, work/sheet_list.txt
칸마다 번호를 적고, 번호→이름은 sheet_list.txt 에. 번호 순서 = 도감 순서가 아니라 칸 번호."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
import dmrom, rules

rom = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else os.path.join(dmrom.WORK, 'myver.gbc')
r = dmrom.Rom(rom)
mons = [n for n in range(1, dmrom.NUM + 1) if r.name(n) != rules.EMPTY_NAME and not r.name(n).startswith('-') and n != 201]
COLS, SC = 12, 2
for back in (False, True):
    cell = (48 if back else 56) * SC + 4
    rows = (len(mons) + COLS - 1) // COLS
    sheet = Image.new('RGB', (COLS * cell, rows * (cell + 12)), (255, 255, 255))
    dr = ImageDraw.Draw(sheet)
    for k, n in enumerate(mons):
        try:
            a = r.pic(n, back=back)
            c1, c2 = r.palette(n)
            pal = np.array([(255, 255, 255), c1, c2, (0, 0, 0)], np.uint8)
            im = Image.fromarray(pal[a]).resize((a.shape[1] * SC, a.shape[0] * SC), Image.NEAREST)
        except Exception as ex:
            im = Image.new('RGB', (16, 16), (255, 0, 0))
        x, y = (k % COLS) * cell, (k // COLS) * (cell + 12)
        sheet.paste(im, (x + (cell - im.width) // 2, y + cell - im.height))
        dr.rectangle([x, y, x + cell - 1, y + cell + 11], outline=(200, 200, 200))
        dr.text((x + 2, y + cell), str(n), fill=(0, 0, 0))
    sheet.save(os.path.join(dmrom.WORK, 'sheet_%s.png' % ('b' if back else 'f')))
open(os.path.join(dmrom.WORK, 'sheet_list.txt'), 'w', encoding='utf-8').write('\n'.join('%d %s' % (n, r.name(n)) for n in mons))
print('work/sheet_f.png, sheet_b.png, sheet_list.txt (%d칸)' % len(mons))
