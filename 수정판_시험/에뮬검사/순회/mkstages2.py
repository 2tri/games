import sys,struct,json; sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS,NARC
B=NDS(open('/home/user/games/최종_노래.nds','rb').read())
sc=NARC(B.get('a/0/1/2')).files; ev=NARC(B.get(hg1.NARC_PATHS['zone_event'])).files
H=json.load(open('../hdr.json'))
out=[]
for mp in range(540):
    h=H[mp]; e=h['event']
    # 레벨 스크립트: 장면(var,value,script)
    L=h['lvl']
    if L<len(sc):
        f=sc[L]; pos=0; ok=True
        while pos<len(f) and f[pos]!=0:
            t=f[pos]; v=struct.unpack_from('<I',f,pos+1)[0]; pos+=5
            if t==2 and v<len(f):
                q=v
                while q+6<=len(f):
                    var,val,scr=struct.unpack_from('<HHH',f,q)
                    if var==0: break
                    out.append(dict(kind='장면',map=mp,var=var,val=val,script=scr,x=None,y=None)); q+=6
    # 칸 이벤트
    if e and e<len(ev):
        g=ev[e]
        try:
            o=0; nb=struct.unpack_from('<I',g,o)[0]; o+=4+20*nb; no=struct.unpack_from('<I',g,o)[0]; o+=4+32*no
            nw=struct.unpack_from('<I',g,o)[0]; o+=4+12*nw; nc=struct.unpack_from('<I',g,o)[0]; o+=4
            for i in range(nc):
                s,x,y,w,hh,z,val,var=struct.unpack_from('<8H',g,o+16*i)
                out.append(dict(kind='칸',map=mp,var=var,val=val,script=s,x=x,y=y,w=w,h=hh))
        except Exception: pass
json.dump(out,open('stages2.json','w'))
from collections import Counter
print(len(out),Counter(o['kind'] for o in out))
