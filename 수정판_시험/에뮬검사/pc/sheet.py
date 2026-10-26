import sys, glob
from PIL import Image
d, outp = sys.argv[1], sys.argv[2]; fs = sorted(glob.glob(d + '/*.png'))
if len(sys.argv) > 3: fs = fs[int(sys.argv[3]):int(sys.argv[4])]
cols = 6; w, h = 256, 192; rows = (len(fs) + cols - 1) // cols
W = Image.new('RGB', (cols * w // 2, rows * h // 2), 'white')
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB').crop((0, 0, 256, 192)).resize((w // 2, h // 2)); W.paste(im, ((i % cols) * w // 2, (i // cols) * h // 2))
W.save(outp); print(len(fs))
