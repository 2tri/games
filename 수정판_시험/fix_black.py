"""nds_art 의 front·back PNG 에서 불투명 순수 검정 (0,0,0) 을 (1,1,1) 로 바꾼다 — hg4.read_indexed 가 투명(0번=(0,0,0))과 같은 색으로 보고 번호를 밀기 때문 (Claude 작성, 2026-10-14)"""
import os, sys
from PIL import Image
n = 0
for d in sorted(os.listdir('nds_art')):
    for nm in ('front.png', 'back.png'):
        p = os.path.join('nds_art', d, nm)
        if not os.path.exists(p): continue
        im = Image.open(p)
        if im.mode != 'P': continue
        pal = im.getpalette(); tr = im.info.get('transparency'); used = set(im.get_flattened_data()) if hasattr(im, 'get_flattened_data') else set(im.getdata()); ch = False
        for i in range(len(pal) // 3):
            if i not in used or pal[i * 3:i * 3 + 3] != [0, 0, 0]: continue
            if isinstance(tr, int) and i == tr: continue
            if isinstance(tr, (bytes, bytearray)) and i < len(tr) and tr[i] == 0: continue
            pal[i * 3:i * 3 + 3] = [1, 1, 1]; ch = True
        if ch:
            im.putpalette(pal)
            im.save(p, transparency=tr) if tr is not None else im.save(p); n += 1
print('보정한 그림', n)
