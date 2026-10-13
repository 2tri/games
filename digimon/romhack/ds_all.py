"""14판(17판: ds_convert 로 도트를 그대로 줄임): images/digimon 의 DS 그림(-ds-f.png·-ds-b.png)을 전부 GBC 그림으로 변환.
python3 ds_all.py [--dry] [--only id,id]
지금 art/<id>-f.png·-b.png 는 art_bak/ 에 복사해 둠(되돌리기: python3 ds_all.py --revert id,id).
변환 뒤 python3 sheet_cmp.py 로 전·후를 한 장에 나란히 본다."""
import os, sys, glob, shutil
import ingest, ds_convert

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
ART = os.path.join(WEB, 'art'); BAK = os.path.join(WEB, 'art_bak'); IMG = os.path.join(os.path.dirname(WEB), 'images', 'digimon')      # 저장소 루트의 images/digimon
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
    pal = None
    g = ingest.grade_of(did)
    fmax = ingest.FRONT.get(g, 56) if g else 56      # 17판: 등급 한도 (유년기 40·성장기 48·그 밖 56), 뒤 48
    for side, s in (('f', src), ('b', srcb)):
        if not os.path.exists(s):
            if side == 'b': nob.append(did)
            continue
        dst = os.path.join(ART, '%s-%s.png' % (did, side))
        tmp = dst + '.tmp.png'      # 너무 작게 나오면 기존 그림을 덮지 않도록 임시 파일로 먼저 (확인 뒤 옮김)
        try:
            size, pal = ds_convert.convert(s, tmp, fmax if side == 'f' else 48, pal)      # 뒤는 앞 몸색 그대로
            if min(size) < 12: raise ValueError('너무 작음 %dx%d' % size)
            os.replace(tmp, dst)
        except Exception as ex:
            ok = False
            fail.append('%s-%s: %s' % (did, side, str(ex)[:80]))
            if os.path.exists(tmp): os.remove(tmp)
    if ok: done.append(did + ('(%s%d)' % (g or '?', fmax)))
print('DS 그림 변환 %d: %s' % (len(done), ', '.join(done)))
if nob: print('뒤 없음(앞만 바꿈) %d: %s' % (len(nob), ', '.join(nob)))
if fail: print('실패 %d:\n  ' % len(fail) + '\n  '.join(fail))
