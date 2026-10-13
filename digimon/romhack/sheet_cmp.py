"""14판 검수용: art_bak(전) 과 art(후) 의 그림을 종마다 나란히 한 장에. python3 sheet_cmp.py → work/sheet_cmp.png
한 칸 = [전 앞 | 후 앞 | 전 뒤 | 후 뒤], 아래에 id. 전이 없으면 빈 칸."""
import os, glob
from PIL import Image, ImageDraw
import dmrom

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
ART = os.path.join(WEB, 'art'); BAK = os.path.join(WEB, 'art_bak')
ids = sorted({os.path.basename(p)[:-6] for p in glob.glob(os.path.join(ART, '*-f.png')) if not os.path.basename(p).startswith('_')})
ids = [i for i in ids if os.path.exists(os.path.join(BAK, i + '-f.png')) or os.path.exists(os.path.join(BAK, i + '-b.png'))] or ids
SC, CW, CH, COLS = 2, 56 * 2 * 4 + 10, 56 * 2 + 14, 4
rows = (len(ids) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * CW, rows * CH), (255, 255, 255))
dr = ImageDraw.Draw(sheet)
for k, did in enumerate(ids):
    x0, y0 = (k % COLS) * CW, (k // COLS) * CH
    for j, (folder, side) in enumerate(((BAK, 'f'), (ART, 'f'), (BAK, 'b'), (ART, 'b'))):
        p = os.path.join(folder, '%s-%s.png' % (did, side))
        x = x0 + j * 56 * SC
        if os.path.exists(p):
            im = Image.open(p).convert('RGBA')
            bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im).convert('RGB')
            im = im.resize((im.width * SC, im.height * SC), Image.NEAREST)
            sheet.paste(im, (x + (56 * SC - im.width) // 2, y0 + 56 * SC - im.height))
        dr.line([x, y0, x, y0 + CH], fill=(220, 220, 220))
    dr.rectangle([x0, y0, x0 + CW - 1, y0 + CH - 1], outline=(180, 180, 180))
    dr.text((x0 + 2, y0 + 56 * SC + 1), '%d %s  (old f | new f | old b | new b)' % (k + 1, did), fill=(0, 0, 0))
sheet.save(os.path.join(dmrom.WORK, 'sheet_cmp.png'))
open(os.path.join(dmrom.WORK, 'sheet_cmp_list.txt'), 'w', encoding='utf-8').write('\n'.join('%d %s' % (k + 1, i) for k, i in enumerate(ids)))
print('work/sheet_cmp.png (%d종)' % len(ids))
