import sys, os, subprocess
sys.path.insert(0, r'C:\Users\skagn\OneDrive\Desktop\claude')
import hg1
from hg1 import NDS, NARC
from PIL import Image, ImageChops
SRC = r'C:\Users\skagn\OneDrive\Desktop\claude\_t7.nds'
E = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(E, '..', 'out10', 'bc'); os.makedirs(OUT, exist_ok=True)
def shot(rom, tag, extra=''):
    subprocess.run([sys.executable, os.path.join(E, 'emu_run.py'), rom, '--load', os.path.join(E, 's_stage_b.dst'), '--do', 'w30 X w90 t125,36 w150 s' + tag + ' ' + extra, '--out', OUT, '--scale', '1'], capture_output=True)
    return Image.open(os.path.join(OUT, tag + '.png')).convert('RGB')
base = shot(SRC, 'base')
cands = [int(x) for x in sys.argv[1].split(',')]
for mem in cands:
    r = NDS(open(SRC, 'rb').read()); n = NARC(r.get('a/0/4/9')); f = list(n.files)
    m = bytearray(f[mem]); c = m.find(b'RAHC') + 0x20
    for i in range(c, len(m)): m[i] = 0x55
    f[mem] = bytes(m); n.files = f; r.put('a/0/4/9', n.build())
    p = os.path.join(OUT, 'b%d.nds' % mem); open(p, 'wb').write(bytes(r.d))
    im = shot(p, 'm%d' % mem)
    d = ImageChops.difference(base, im)
    cnt = sum(1 for px in d.convert('L').getdata() if px > 20)
    print(mem, '바뀐 픽셀', cnt, d.getbbox(), flush=True)
    os.remove(p)
