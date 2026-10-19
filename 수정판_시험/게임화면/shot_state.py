import sys,os
from desmume.emulator import DeSmuME
rom,state,out=sys.argv[1:4]
emu=DeSmuME(); emu.open(rom); emu.volume_set(0); emu.savestate.load_file(state)
for _ in range(30): emu.cycle(False)
im=emu.screenshot().crop((0,0,256,192)); im.save(out); 
# 따라다니는 칸 확대
im.crop((90,60,170,140)).resize((320,320)).save(out.replace('.png','_zoom.png'))
