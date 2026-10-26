import struct, json
from desmume.emulator import DeSmuME
emu=DeSmuME(); emu.open('rom.nds'); emu.volume_set(0); emu.savestate.load_file('ng/end.dst')
for _ in range(5): emu.cycle(False)
ram=bytes(emu.memory.unsigned[0x02000000:0x02400000])
print('pos A', struct.unpack('<5i', ram[0x27DEDC:0x27DEF0]), 'pos B', struct.unpack('<3I', ram[0x27de84:0x27de90]))
cands=[]
p=ram.find(struct.pack('<H',843))
while p!=-1:
    for k in range(0,24,2):
        base=p-k-61*24
        if base<0 or p%2: continue
        ok=True
        for i in range(540):
            v=struct.unpack_from('<H',ram,base+i*24+k)[0]
            if v>1100: ok=False;break
        if ok: cands.append((hex(0x02000000+base),k))
    p=ram.find(struct.pack('<H',843),p+1)
print(cands[:20])
