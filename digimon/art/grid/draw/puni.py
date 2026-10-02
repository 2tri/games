from kit import C
c=C(38,34)
c.ell(5,1,13,10,1); c.ell(15,0,22,8,1); c.ell(24,1,32,10,1)          # 뿔 혹 3개
c.ell(1,5,36,44,1); c.t[33:,:]=-1                                     # 젤리 돔(바닥 평평)
c.shade(3)
c.outline()
c.line([(13,8),(14,6)],3); c.line([(24,6),(23,8)],3)                  # 혹 사이 골
c.px([(6,10),(7,9),(8,8),(9,8),(6,11)],0)                              # 젤리 광택
for ex in (8,22):
    c.ell(ex,14,ex+7,22,0); c.outline() if False else None
    c.line([(ex,18),(ex,17)],3)
for ex in (8,22):
    m=c._mask(lambda d:d.ellipse((ex,14,ex+7,22),outline=1)); c.t[m]=3
    c.rect(ex+3,17,ex+4,19,3)
c.px([(17,26),(18,27),(19,27),(20,26)],3)                              # 입
c.save('../punimon-f.txt')
