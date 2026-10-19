import sys, os, subprocess, struct
sys.path.insert(0, r'C:\Users\skagn\OneDrive\Desktop\claude')
import hg1
from hg1 import NDS, NARC
from PIL import Image, ImageChops
SRC = r'C:\Users\skagn\OneDrive\Desktop\claude\hg4t_out\hg4t_test.nds'
E = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(E, '..', 'out10', 'bt'); os.makedirs(OUT, exist_ok=True)
def shot(rom, tag):
    subprocess.run([sys.executable, os.path.join(E, 'emu_run.py'), rom, '--load', os.path.join(E, 's_boot.dst'), '--do', 'w60 A*8 w40 s' + tag, '--out', OUT, '--scale', '1'], capture_output=True)
    return Image.open(os.path.join(OUT, tag + '.png')).convert('RGB').crop((0, 0, 256, 192))
base = shot(SRC, 'base')
raw = NDS(open(SRC, 'rb').read()); nar = NARC(raw.get('a/0/4/6')); files = list(nar.files)
for mem in (1, 3, 30, 31, 34, 36, 15, 7, 11):
    r = NDS(open(SRC, 'rb').read()); n = NARC(r.get('a/0/4/6')); f = list(n.files)
    m = bytearray(f[mem]); c = m.find(b'RAHC') + 0x20
    for i in range(c, len(m)): m[i] = 0x55
    f[mem] = bytes(m); n.files = f; r.put('a/0/4/6', n.build())
    p = os.path.join(OUT, 'b%d.nds' % mem); open(p, 'wb').write(bytes(r.d))
    im = shot(p, 'm%d' % mem)
    diff = ImageChops.difference(base, im).getbbox()
    cnt = sum(1 for px in ImageChops.difference(base, im).convert('L').getdata() if px > 20)
    print(mem, '바뀐 픽셀', cnt, diff, flush=True)
    os.remove(p)
