"""21판: 내 쪽 뒷모습 방향 검수 페이지 (아티팩트용 HTML). python3 flips_picker.py [롬] [출력.html]
기본 롬 work/myver_prevflip.gbc (반전을 하나도 안 넣은 상태). 사용자가 「왼쪽을 보는 것」을 눌러 표시 → db flips/n<칸번호> → rules.FLIP_BACK_ALL 로."""
import os, sys, json, base64, io
import numpy as np
from PIL import Image
import dmrom, rules

HERE = os.path.dirname(os.path.abspath(__file__))
rom = sys.argv[1] if len(sys.argv) > 1 else os.path.join(dmrom.WORK, 'myver_prevflip.gbc')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(dmrom.WORK, 'flips.html')
r = dmrom.Rom(rom)
mons = [n for n in range(1, dmrom.NUM + 1) if r.name(n) != rules.EMPTY_NAME and not r.name(n).startswith('-') and n != 201]
rows = []
for k, n in enumerate(mons):
    a = r.pic(n, back=True); c1, c2 = r.palette(n)
    pal = np.array([(255, 255, 255), c1, c2, (0, 0, 0)], np.uint8)
    im = Image.fromarray(pal[a]).convert('P', palette=Image.ADAPTIVE, colors=8)
    b = io.BytesIO(); im.save(b, 'PNG', optimize=True)
    rows.append({'n': n, 'k': 'n%d' % n, 'no': k + 1, 'ko': r.name(n), 'img': 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), 'w': a.shape[1], 'h': a.shape[0]})
tpl = open(os.path.join(HERE, 'flips_tpl.html'), encoding='utf-8').read()
open(out, 'w', encoding='utf-8').write(tpl.replace('/*DATA*/[]', json.dumps(rows, ensure_ascii=False, separators=(',', ':'))))
print('%s (%d종, %.0f KB)' % (out, len(rows), os.path.getsize(out) / 1024))
