"""14판: images/digimon 의 DS 그림(<id>-ds-f.png·<id>-ds-b.png)을 전부 GBC 그림으로 변환. python3 ds_all.py [--dry] [--only id,id]
지금 art/<id>-f.png·-b.png 는 art_bak/ 에 복사해 둠(되돌리기: python3 ds_all.py --revert id,id).
변환 뒤 python3 sheet_cmp.py 로 전·후를 한 장에 나란히 본다."""
import os, sys, glob, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
ART = os.path.join(WEB, 'art'); BAK = os.path.join(WEB, 'art_bak'); IMG = os.path.join(WEB, 'images', 'digimon')
os.makedirs(BAK, exist_ok=True)
args = sys.argv[1:]
if '--revert' in args:
    for did in args[args.index('--revert') + 1].split(','):
        for side in ('f', 'b'):
            b = os.path.join(BAK, '%s-%s.png' % (did, side))
            if os.path.exists(b):
                shutil.copy(b, os.path.join(ART, '%s-%s.png' % (did, side)))
                print('되돌림', did, side)
    sys.exit()
dry = '--dry' in args
only = set(args[args.index('--only') + 1].split(',')) if '--only' in args else None
done = []; fail = []; nob = []
for src in sorted(glob.glob(os.path.join(IMG, '*-ds-f.png'))):
    did = os.path.basename(src)[:-len('-ds-f.png')]
    if only and did not in only: continue
    srcb = os.path.join(IMG, did + '-ds-b.png')
    if dry:
        done.append(did + ('' if os.path.exists(srcb) else '(뒤 없음)'))
        continue
    for side in ('f', 'b'):
        cur = os.path.join(ART, '%s-%s.png' % (did, side))
        if os.path.exists(cur) and not os.path.exists(os.path.join(BAK, os.path.basename(cur))): shutil.copy(cur, BAK)
    ok = True
    for side, s in (('f', src), ('b', srcb)):
        if not os.path.exists(s):
            if side == 'b': nob.append(did)
            continue
        r = subprocess.run([sys.executable, os.path.join(HERE, 'ingest.py'), s, did, '--side', side], capture_output=True, text=True)
        if r.returncode:
            ok = False
            fail.append('%s-%s: %s' % (did, side, (r.stderr or r.stdout).strip().split('\n')[-1][:80]))
    if ok: done.append(did)
print('DS 그림 변환 %d: %s' % (len(done), ', '.join(done)))
if nob: print('뒤 없음(앞만 바꿈) %d: %s' % (len(nob), ', '.join(nob)))
if fail: print('실패 %d:\n  ' % len(fail) + '\n  '.join(fail))
