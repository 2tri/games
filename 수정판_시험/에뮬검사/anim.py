import sys, os
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image
rom, st, out, total, step = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]); t0 = int(sys.argv[6]) if len(sys.argv) > 6 else 0; os.makedirs(out, exist_ok=True)
emu = DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(st)
def run(k):
    for _ in range(k): emu.cycle(False)
run(5); fr = []
for t in range(0, total, step):
    if t % 120 == 0:
        m = keymask(Keys.KEY_A); emu.input.keypad_add_key(m); run(4); emu.input.keypad_rm_key(m); run(step - 4)
    else: run(step)
    if t >= t0: im = emu.screenshot(); fr.append(im.copy())
# 위 화면(전투)만 모아 접촉 시트: 가로 8
tw, th = 128, 96; cols = 8; per = 48
for s in range(0, len(fr), per):
    chunk = fr[s:s + per]; rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th))
    for i, im in enumerate(chunk):
        top = im.crop((0, 0, 256, 192)).resize((tw, th)); sheet.paste(top, ((i % cols) * tw, (i // cols) * th))
    sheet.save('%s/sheet%02d.png' % (out, s // per))
fr[0].save(out + '/first.png'); print('frames', len(fr))
