import sys,glob,os
from PIL import Image
d=sys.argv[1]; fs=sorted(glob.glob(d+'/c*/p*.png'))
# 가장 많은 쪽이 있는 후보 폴더 사용
best=max(glob.glob(d+'/c*'),key=lambda c:len(glob.glob(c+'/p*.png')))
fs=sorted(glob.glob(best+'/p*.png'))[:12]
ims=[Image.open(f).crop((0,100,256,192)) for f in fs]
if not ims: print('no pages'); sys.exit()
cols=3; rows=(len(ims)+cols-1)//cols
W=Image.new('RGB',(256*cols,92*rows))
for i,im in enumerate(ims): W.paste(im,((i%cols)*256,(i//cols)*92))
W.save(d+'/sheet.png'); print(d+'/sheet.png',len(fs))
