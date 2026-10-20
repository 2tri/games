import sys
sys.path.insert(0,'.')
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import ImageChops
emu=DeSmuME(); emu.open(sys.argv[1]); emu.volume_set(0); import os; emu.savestate.load_file(os.environ.get('STATE','ag4.dst')); d=sys.argv[2]
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k,hold=4,gap=40):
    m=keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k,n):
    m=keymask(k); emu.input.keypad_add_key(m); run(16*n); emu.input.keypad_rm_key(m); run(10)
run(5)
if not os.environ.get('NOLEFT'): walk(Keys.KEY_LEFT,1); press(Keys.KEY_A); run(300); walk(Keys.KEY_RIGHT,1)
walk(Keys.KEY_UP,1); press(Keys.KEY_A)
run(300); a=emu.screenshot().convert('RGB'); a.save(d+'/a.png')
run(120); b=emu.screenshot().convert('RGB'); b.save(d+'/b.png')
top=a.crop((0,0,256,192)); nz=sum(1 for p in top.getdata() if sum(p)>60)/ (256*192)
# 조작 가능 여부: 한 칸 걷기 입력 후 화면 변화
press(Keys.KEY_DOWN,20,40); c=emu.screenshot().convert('RGB'); c.save(d+'/c.png')
chg=ImageChops.difference(b.crop((0,0,256,192)),c.crop((0,0,256,192))).getbbox() is not None
print('nonblack %.2f moved %s'%(nz,chg))
