"""14판: 등급보다 크게 들어간 그림을 다시 변환. python3 reingest.py [--dry]
art/src/<id>-f_ai.*(ingest 가 남긴 원본)마다 등급 한도(ingest.FRONT, 뒤는 48)를 보고, 지금 art/<id>-f.png 가 한도보다 크면 ingest 를 다시 돌린다 (뒤도 같이).
2번 꾸러미 때(등급 찾기 전) 변환된 38장이 전부 56 으로 들어간 것을 고침."""
import os, sys, glob, subprocess
from PIL import Image
import ingest

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE); ART = os.path.join(WEB, 'art')
dry = '--dry' in sys.argv
redo = []; keep = []; nograde = []
for src in sorted(glob.glob(os.path.join(ART, 'src', '*-f_ai.*'))):
    did = os.path.basename(src).split('-f_ai')[0]
    g = ingest.grade_of(did)
    if not g:
        nograde.append(did)
        continue
    lim = ingest.FRONT.get(g, 56)
    cur = os.path.join(ART, did + '-f.png')
    if not os.path.exists(cur): continue
    w, h = Image.open(cur).size
    if max(w, h) <= lim:
        keep.append('%s(%s %d)' % (did, g, max(w, h)))
        continue
    redo.append('%s(%s %d→%d)' % (did, g, max(w, h), lim))
    if dry: continue
    for side in ('f', 'b'):
        s = glob.glob(os.path.join(ART, 'src', '%s-%s_ai.*' % (did, side)))
        if not s: continue
        r = subprocess.run([sys.executable, os.path.join(HERE, 'ingest.py'), s[0], did, '--side', side], capture_output=True, text=True)
        if r.returncode: print('  실패', did, side, (r.stderr or r.stdout).strip().split('\n')[-1])
print('다시 변환 %d: %s' % (len(redo), ', '.join(redo)))
print('그대로 %d' % len(keep))
if nograde: print('등급 못 찾음 %d: %s' % (len(nograde), ', '.join(nograde)))
