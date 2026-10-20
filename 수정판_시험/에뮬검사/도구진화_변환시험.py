import sys, struct, subprocess, os, json
sys.path.insert(0,'/home/user/games')
import hg1
from hg1 import NDS, NARC
S='/tmp/claude-0/-home-user/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/'
E_='/tmp/claude-0/-home-user-home/cff20347-9f80-55de-9e0d-8d6d822db27a/scratchpad/emu/'
N={}
for l in open('/home/user/games/hg2_out/slots.tsv',encoding='utf-8').read().splitlines()[1:]:
    p=l.split('\t'); N[p[0]]=int(p[1])
rows=[l.rstrip('\n').split('\t') for l in open('/home/user/games/NDS_진화.tsv',encoding='utf-8')][1:]
rows=[r for r in rows if r[2]=='도구사용']
shard,n=map(int,sys.argv[1].split('/'))
raw=open(S+'final_new.nds','rb').read(); force=open(S+'force_new.nds','rb').read()
for k,r in enumerate(rows):
    if k%n!=shard: continue
    src,tgt=N[r[0]],N[r[1]]
    rom=NDS(force); nar=NARC(rom.get(hg1.NARC_PATHS['evo'])); f=bytearray(nar.files[src])
    f[:]=struct.pack('<3H',4,20,tgt)+bytes(len(f)-6); nar.files[src]=bytes(f); rom.put(hg1.NARC_PATHS['evo'],nar.build())
    p=E_+'ie_%d.nds'%k; open(p,'wb').write(bytes(rom.d))
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    out=subprocess.run(['python3','/home/user/games/수정판_시험/에뮬검사/evo.py',p,E_+'ie_out_%d'%k,str(src),'4','20',str(tgt)],env=env,capture_output=True,text=True).stdout.strip().splitlines()
    print(k,r[0],r[3],r[1],out[-1] if out else 'NO OUTPUT',flush=True); os.remove(p)
