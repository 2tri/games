import sys, json, glob
from PIL import Image, ImageDraw
name = sys.argv[1]
fs = sorted(glob.glob(f'cand/{name}/*.jpg'))
ims = []
for f in fs:
    try:
        im = Image.open(f).convert('RGB'); im.thumbnail((150, 150)); ims.append((f.split('/')[-1][:2], im))
    except Exception: pass
cols = 10; rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * 156, rows * 170), (32, 36, 42)); d = ImageDraw.Draw(S)
for k, (lab, im) in enumerate(ims):
    x, y = (k % cols) * 156, (k // cols) * 170
    S.paste(im, (x + 3, y + 16)); d.text((x + 4, y + 2), lab, fill=(255, 255, 0))
S.save(f'cand/{name}_sheet.png'); print(name, len(ims), S.size)
