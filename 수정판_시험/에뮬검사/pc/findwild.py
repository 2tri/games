import sys,struct,json; sys.path.insert(0,r'C:\Users\skagn\OneDrive\Desktop\claude')
import hg1
from hg1 import NDS,NARC
R=NDS(open('rom.nds','rb').read()); sc=NARC(R.get('a/0/1/2')).files
H=json.load(open('hdr.json')); s2m={}
for i,h in enumerate(H): s2m.setdefault(h['script'],[]).append(i)
tg={int(x) for x in sys.argv[1:]} or {185,130,131,128}
for fi,f in enumerate(sc):
    for k in range(0,len(f)-6):
        op=f[k]|(f[k+1]<<8)
        if op in (0x24d,0x2bd,0x89):
            sp,lv=struct.unpack_from('<HH',f,k+2)
            if sp in tg and 1<=lv<=100: print('file',fi,'@%x'%k,'op',hex(op),'sp',sp,'lv',lv,'maps',s2m.get(fi))
