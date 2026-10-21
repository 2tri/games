import sys,struct,json,csv; sys.path.insert(0,'/home/user/games')
import hg1, 글_넘침 as g
from hg1 import NDS,NARC
B=NDS(open('/home/user/games/최종_노래.nds','rb').read())
sc=NARC(B.get('a/0/1/2')).files; ev=NARC(B.get(hg1.NARC_PATHS['zone_event'])).files
H=json.load(open('../hdr.json'))
draft={r['이름'] for r in csv.DictReader(open('/home/user/games/NDS_종_초안.tsv',encoding='utf-8'),delimiter='\t')}
m=g.load('/home/user/games/최종_노래.nds'); CM,NF,_=hg1.infer_charmap(m,draft); nn=[CM.dec(e) for e in m[NF][1]]
def parse(f):
    o=0; nb=struct.unpack_from('<I',f,o)[0]; o+=4; bg=[struct.unpack_from('<HHiii',f,o+20*i) for i in range(nb)]; o+=20*nb
    no=struct.unpack_from('<I',f,o)[0]; o+=4; ob=[struct.unpack_from('<16H',f,o+32*i) for i in range(no)]; o+=32*no
    return bg,ob
def entries(f):
    ents=[];p=0
    while p+4<=len(f):
        v=struct.unpack_from('<I',f,p)[0]
        if (v&0xFFFF)==0xFD13: break
        ents.append(p+4+v); p+=4
    return ents
def feats(seg):
    out=[]
    for k in range(len(seg)-8):
        op=seg[k]|(seg[k+1]<<8)
        if op in (0x24d,0x2bd) and k+6<=len(seg):
            sp,lv=struct.unpack_from('<HH',seg,k+2)
            if 1<=sp<600 and 1<=lv<=100: out.append(('고정전투',nn[sp] if sp<len(nn) else sp,lv))
        if op==0x89 and k+6<=len(seg):
            sp,lv=struct.unpack_from('<HH',seg,k+2)
            if (1<=sp<600 or sp>=0x8000) and 1<=lv<=100: out.append(('선물종',nn[sp] if 0<sp<len(nn) else 'VAR%x'%sp,lv))
        if seg[k:k+4]==bytes([0x29,0,4,0x80]) and seg[k+6:k+10]==bytes([0x29,0,5,0x80]):
            it=struct.unpack_from('<H',seg,k+4)[0]; q=struct.unpack_from('<H',seg,k+10)[0]
            if b'\x14\x00\xf1\x07' in seg[k+10:k+40]: out.append(('선물도구',it,q))
        if op==0xd5 and k+4<=len(seg):
            tid=struct.unpack_from('<H',seg,k+2)[0]
            if 1<=tid<740: out.append(('트레이너',tid,0))
    return out
stages=[]
for mp in range(540):
    h=H[mp]; e=h['event']
    if e==0 or e>=len(ev): continue
    try: bg,ob=parse(ev[e])
    except Exception: continue
    f=sc[h['script']] if h['script']<len(sc) else b''
    ents=entries(f)
    ends=ents[1:]+[len(f)]
    users=[('npc%d'%o[0],o[12],o[13],o[5],o[4]) for o in ob if o[5]]+[('bg%d'%i,b[2],b[3],b[0],0) for i,b in enumerate(bg) if b[1] in (0,1)]
    for name,x,y,sid,flag in users:
        if 1<=sid<=len(ents):
            seg=f[ents[sid-1]:ends[sid-1]]
            fe=feats(seg)
            if fe: stages.append(dict(map=mp,event=e,obj=name,x=x,y=y,sid=sid,hide=flag,feat=fe))
json.dump(stages,open('stages.json','w'),ensure_ascii=False)
print(len(stages))
from collections import Counter
print(Counter(k for s in stages for k,_,_ in s['feat']))
