import sys,struct,json; sys.path.insert(0,r'C:\Users\skagn\OneDrive\Desktop\claude')
import hg1
from hg1 import NDS,NARC
R=NDS(open('rom.nds','rb').read()); ev=NARC(R.get(hg1.NARC_PATHS['zone_event'])).files
H=json.load(open('hdr.json'))
def parse(mp):
    g=ev[H[mp]['event']]; o=0
    nb=struct.unpack_from('<I',g,o)[0]; o+=4; bg=[struct.unpack_from('<HHiii',g,o+20*i) for i in range(nb)]; o+=20*nb
    no=struct.unpack_from('<I',g,o)[0]; o+=4; ob=[struct.unpack_from('<16H',g,o+32*i) for i in range(no)]; o+=32*no
    nw=struct.unpack_from('<I',g,o)[0]; o+=4; wp=[struct.unpack_from('<6H',g,o+12*i) for i in range(nw)]; o+=12*nw
    nc=struct.unpack_from('<I',g,o)[0]; o+=4; co=[struct.unpack_from('<8H',g,o+16*i) for i in range(nc)]
    return bg,ob,wp,co
for mp in map(int,sys.argv[1:]):
    bg,ob,wp,co=parse(mp); h=H[mp]
    print('== map',mp,'script',h['script'],'lvl',h['lvl'])
    for o in ob: print('  obj id%d spr%d scr%d flag%d x%d y%d dir%d type%d'%(o[0],o[1],o[5],o[4],o[12],o[13],o[6],o[3]))
    for w in wp: print('  warp x%d y%d -> map%d door%d'%(w[0],w[1],w[2],w[3]))
    for c in co: print('  coord scr%d x%d y%d w%d h%d var%x val%d'%(c[0],c[1],c[2],c[3],c[4],c[7],c[6]))
    for b in bg: print('  bg scr%d x%d y%d'%(b[0],b[2],b[3]))
