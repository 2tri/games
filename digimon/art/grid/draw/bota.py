from kit import C
c=C(36,33)
c.ell(2,6,33,32,2)
c.poly([(6,9),(9,0),(14,7)],2); c.poly([(21,7),(26,0),(29,9)],2)            # 귀
import math
cx,cy,rx,ry=17.5,19.5,15.5,12.8
for deg in range(-200,25,17):                                            # 털끝: 가장자리에 작은 삼각형
    a=math.radians(deg); ux,uy=math.cos(a),math.sin(a)
    bx,by=cx+rx*ux*0.92,cy-ry*uy*0.92; tx,ty=cx+(rx+2.4)*ux,cy-(ry+2.4)*uy
    px,py=-uy*1.8,-ux*1.8
    c.poly([(bx+px,by-py),(tx,ty),(bx-px,by+py)],2)
c.shade(3,v=3,only=(2,))
c.outline()
for (x,y) in [(11,8),(12,9),(17,7),(23,9),(6,22),(7,23),(28,22),(14,26),(15,27),(21,27),(4,17),(31,17)]:
    c.t[y,x]=3                                                            # 털 결
for ex in (8,20):
    c.ell(ex,13,ex+7,20,1); c.px([(ex+4,15),(ex+4,16),(ex+4,17)],3); c.px([(ex+2,14)],0)
c.save('../botamon-f.txt')
