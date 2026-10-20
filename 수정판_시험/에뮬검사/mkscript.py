# python mkscript.py <롬> <출력> <명령 바이트 16진> — 연구소 스크립트(843) 진입점마다 그 바이트열(+ End 0x0002)을 덮어씀
import sys, struct
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS, NARC
src,out,hexs=sys.argv[1],sys.argv[2],sys.argv[3]
code=bytes.fromhex(hexs)+struct.pack('<H',2)
rom=NDS(open(src,'rb').read()); nar=NARC(rom.get('a/0/1/2')); f=bytearray(nar.files[843]); p=0
while p+4<=len(f):
    v=struct.unpack_from('<I',f,p)[0]
    if (v&0xFFFF)==0xFD13: break
    tg=p+4+v
    if 0<tg<len(f)-len(code): f[tg:tg+len(code)]=code
    p+=4
nar.files[843]=bytes(f); rom.put('a/0/1/2',nar.build()); open(out,'wb').write(bytes(rom.d)); print('ok')
