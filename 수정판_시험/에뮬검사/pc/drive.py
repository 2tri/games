"""python drive.py <롬> <in.dst> <out.dst> <폴더> "<토큰들>"
토큰: U3 D L2 R (걷기) / uN dN lN rN (방향만) / A B S / W프레임 / AUTO[최대] (대화·전투 자동) / SHOT이름 / P(위치)"""
import sys, os, struct, hashlib, json
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom, si, so, out, seq = sys.argv[1:6]; os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(si)
K = {'U': Keys.KEY_UP, 'D': Keys.KEY_DOWN, 'L': Keys.KEY_LEFT, 'R': Keys.KEY_RIGHT, 'A': Keys.KEY_A, 'B': Keys.KEY_B, 'S': Keys.KEY_START, 'Y': Keys.KEY_Y, 'X': Keys.KEY_X}
def run(n):
    for _ in range(n): emu.cycle(False)
def hold(k, fr, gap=10):
    m = keymask(k); emu.input.keypad_add_key(m); run(fr); emu.input.keypad_rm_key(m); run(gap)
def touch(x, y, h=8, g=40):
    emu.input.touch_set_pos(x, y); run(h); emu.input.touch_release(); run(g)
u = lambda a: struct.unpack('<I', bytes(emu.memory.unsigned[a:a + 4]))[0]
def pos(): return (u(0x0227de78), u(0x0227de80), u(0x0227de84))
def is_dialog(im):
    t = im.crop((10, 155, 246, 185)).convert('L'); d = list(t.getdata()); return sum(1 for v in d if v > 225) / len(d) > 0.55
def is_field(im):
    p = im.getpixel((128, 300)); return abs(p[0] - 24) < 20 and abs(p[1] - 200) < 20 and abs(p[2] - 112) < 20
def is_menu(im):
    p = im.crop((0, 192, 256, 384)).convert('RGB').getpixel((128, 70)); return p[0] > 180 and p[1] < 90 and p[2] < 90
log = []; nshot = [0]
def shot(name=None):
    nshot[0] += 1; emu.screenshot().save('%s/%s.png' % (out, name or 's%03d' % nshot[0]))
def auto(maxit):
    last = None; idle = 0; busy = 0; battles = 0; pages = 0
    for it in range(maxit):
        im = emu.screenshot().convert('RGB')
        if is_menu(im):
            mv = [(64, 55), (192, 55), (64, 115), (192, 115)][battles % 4]; battles += 1; touch(128, 70, 8, 30); touch(*mv, 8, 60); run(120); idle = 0; busy = 0; continue
        if is_dialog(im):
            idle = 0
            h = hashlib.md5(im.crop((0, 140, 256, 192)).tobytes()).hexdigest()
            if h != last:
                pages += 1; im.crop((0, 0, 256, 192)).save('%s/d%03d.png' % (out, nshot[0])); nshot[0] += 1; last = h
            yn = im.crop((200, 100, 256, 190)).convert('L'); yn = sum(1 for v in yn.getdata() if v > 225) / (56 * 90)
            hold(Keys.KEY_B if '교체' in '' else Keys.KEY_A, 4, 0); run(45)
        elif is_field(im):
            idle += 1; busy = 0
            if idle >= 6: break
            run(40)
        else:
            if os.environ.get('BSHOT') and busy % 3 == 0: im.save('%s/b%03d.png' % (out, nshot[0])); nshot[0] += 1
            busy += 1; idle = 0
            if busy > 200: break
            if busy % 4 == 0:
                if busy % 8 == 0: hold(Keys.KEY_A, 4, 0); run(20)
                else: touch(240, 173, 8, 20)
            else: run(40)
    log.append(dict(auto=it + 1, battles=battles, pages=pages, pos=pos()))
run(5)
for tok in seq.split():
    if tok.startswith('TOMENU'):
        for it in range(int(tok[6:] or 300)):
            im = emu.screenshot().convert('RGB')
            if is_menu(im): break
            hold(Keys.KEY_A, 4, 0); run(40)
        log.append(dict(tomenu=it)); continue
    if tok.startswith('AUTO'): auto(int(tok[4:] or 400)); continue
    if tok.startswith('SHOT'): shot(tok[4:] or None); continue
    if tok.startswith('M'):
        a, v = tok[1:].split('='); a = int(a, 16); v = int(v)
        for i in range(4): emu.memory.unsigned[a + i] = (v >> (8 * i)) & 255
        continue
    if tok == 'P': log.append(dict(pos=pos())); continue
    if tok.startswith('W'): run(int(tok[1:])); continue
    if tok.startswith('T'): x, y = map(int, tok[1:].split(',')); touch(x, y); continue
    k = tok[0]; n = int(tok[1:]) if len(tok) > 1 else 1
    if k in 'UDLR':
        hold(K[k], 16 * n, 10)
    elif k in 'udlr':
        hold(K[k.upper()], 3, 10)
    else:
        for _ in range(n): hold(K[k], 4, 40)
run(20); shot('end'); emu.savestate.save_file(so); log.append(dict(end=pos()))
print(json.dumps(log, ensure_ascii=False))
