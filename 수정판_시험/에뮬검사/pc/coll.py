import sys,struct,json; sys.path.insert(0,r'C:\Users\skagn\OneDrive\Desktop\claude')
from hg1 import NDS,NARC
R=NDS(open('rom.nds','rb').read()); H=json.load(open('hdr.json'))
MX=NARC(R.get('a/0/4/1')).files; LD=NARC(R.get('a/0/6/5')).files
def grid(mp):
    raw=H[mp]['raw']; mat=raw[5]
    m=MX[mat]; w,h,hh,ha,nl=m[0],m[1],m[2],m[3],m[4]; o=5+nl
    if hh: o+=2*w*h
    if ha: o+=w*h
    land=struct.unpack_from('<%dH'%(w*h),m,o)
    G={}
    for j in range(h):
        for i in range(w):
            l=land[j*w+i]
            if l==0xFFFF: continue
            d=LD[l]; ps=struct.unpack_from('<I',d,0)[0]; base=0x14+struct.unpack_from('<H',d,0x12)[0]
            # HGSS 땅 자료 머리 0x14
            for y in range(32):
                for x in range(32):
                    v=struct.unpack_from('<H',d,base+2*(y*32+x))[0]
                    G[(i*32+x,j*32+y)]=v
    return mat,w,h,G
if __name__=='__main__':
    mp=int(sys.argv[1]); mat,w,h,G=grid(mp); print('matrix',mat,w,h)
    xs=[k[0] for k in G]; ys=[k[1] for k in G]
    x0,x1,y0,y1=int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5])
    for y in range(y0,y1):
        print('%3d '%y+''.join(('#' if G.get((x,y),0x8000)&0x8000 else ('.' if (G[(x,y)]&0xff)==0 else chr(97+(G[(x,y)]&0xff)%26))) for x in range(x0,x1)))
