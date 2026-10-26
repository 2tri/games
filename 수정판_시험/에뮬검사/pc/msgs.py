import sys, os, csv, json, re
R0=r'C:\Users\skagn\OneDrive\Desktop\claude'; sys.path.insert(0,R0)
import hg1
from hg1 import NDS, NARC, msg_decode
def load(rom):
    nds=NDS(open(rom,'rb').read())
    draft={r['이름'] for r in csv.DictReader((l for l in open(os.path.join(R0,'NDS_종_초안.tsv'),encoding='utf-8') if not l.startswith('#')),delimiter='\t')}
    mn=NARC(nds.get(hg1.NARC_PATHS['msg'])); M=[]
    for f in mn.files:
        try: M.append(msg_decode(f))
        except Exception: M.append((0,[]))
    CM=hg1.infer_charmap(M,draft)[0]
    return [[CM.dec(e).replace('{01DE}',' ') for e in ents] for _,ents in M]
if __name__=='__main__':
    T=load(sys.argv[1]); pat=re.compile(sys.argv[2])
    H=json.load(open('hdr.json')); b2m={}
    for i,h in enumerate(H): b2m.setdefault(h['msg'],[]).append(i)
    for b,ents in enumerate(T):
        for i,s in enumerate(ents):
            if pat.search(s): print('%d:%d maps%s  %s'%(b,i,b2m.get(b,''),s[:110]))
