"""창 없이 DS 롬을 돌리고 화면을 PNG 로 저장 (py-desmume). 롬은 복사본만 쓴다.
사용: python emu_run.py <rom> [--load 상태파일] [--save 상태파일] --do "<동작들>" [--out 폴더]
동작(띄어쓰기로 구분):
  w120        120프레임 기다림
  A  B  X  Y  L  R  START  SELECT  UP  DOWN  LEFT  RIGHT     한 번 누름(4프레임 누르고 12프레임 쉼)
  A*20        20번 반복        UP:30   30프레임 동안 누르고 있음       A:4/40  4프레임 누르고 40프레임 쉼
  t128,100    아래 화면 (128,100) 터치
  s이름       지금 화면을 <out>/이름.png 로 저장 (위·아래 화면, 2배)"""
import sys, os, argparse, time
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image

KEYMAP = {'A': Keys.KEY_A, 'B': Keys.KEY_B, 'X': Keys.KEY_X, 'Y': Keys.KEY_Y, 'L': Keys.KEY_L, 'R': Keys.KEY_R,
          'START': Keys.KEY_START, 'SELECT': Keys.KEY_SELECT, 'UP': Keys.KEY_UP, 'DOWN': Keys.KEY_DOWN,
          'LEFT': Keys.KEY_LEFT, 'RIGHT': Keys.KEY_RIGHT}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--load'); ap.add_argument('--save')
    ap.add_argument('--do', default=''); ap.add_argument('--out', default='shots'); ap.add_argument('--scale', type=int, default=2)
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    emu = DeSmuME(); emu.open(A.rom); emu.volume_set(0)
    if A.load: emu.savestate.load_file(A.load)
    frames = 0; t0 = time.time()
    def run(n):
        nonlocal frames
        for _ in range(n): emu.cycle(False); frames += 1
    def shot(name):
        im = emu.screenshot()
        if A.scale != 1: im = im.resize((im.width * A.scale, im.height * A.scale), Image.NEAREST)
        im.save(os.path.join(A.out, name + '.png'))
    for tok in A.do.split():
        if tok[0] == 'w' and tok[1:].isdigit(): run(int(tok[1:])); continue
        if tok[0] == 's' and tok.upper().split('*')[0].split(':')[0] not in KEYMAP: shot(tok[1:]); continue
        if tok[0] == 't' and ',' in tok:
            x, y = (int(v) for v in tok[1:].split(','))
            emu.input.touch_set_pos(x, y); run(4); emu.input.touch_release(); run(12); continue
        rep = 1
        if '*' in tok: tok, r = tok.split('*'); rep = int(r)
        hold, gap = 4, 12
        if ':' in tok:
            tok, h = tok.split(':')
            if '/' in h: h, g = h.split('/'); gap = int(g)
            hold = int(h)
        k = keymask(KEYMAP[tok.upper()])
        for _ in range(rep):
            emu.input.keypad_add_key(k); run(hold); emu.input.keypad_rm_key(k); run(gap)
    if A.save: emu.savestate.save_file(A.save)
    print('프레임 %d, %.1f초 (%.0f fps)' % (frames, time.time() - t0, frames / max(0.001, time.time() - t0)))
    emu.destroy()

if __name__ == '__main__':
    main()
