#!/usr/bin/env python3
"""글 넘침 화면 검사 (2026-10-20) — 원본보다 바뀐 대사를 연구소 NPC(msg538#12·13) 자리에 넣어 실제 대화창에 띄우고, 글이 상자 오른쪽 끝에 닿거나 잘리는지 본다.
사용:   python 글_화면검사.py <최종 롬> <ag4.dst 가 있는 폴더> <결과 폴더> [--min 18] [--shard i/n] [--labrom 연구소용 롬]
        1) 바뀐 한글 대사 중 가장 긴 줄 너비(글_넘침.py 기준)가 --min 이상인 것을 모음  2) 3개씩 묶어 시험 롬을 만들고  3) 에뮬로 A 를 눌러 가며 상자 모양을 찍음
        4) 줄 끝이 x≥228(상자 안쪽 끝 234)이면 「FLAG」 — 사람이 그 사진을 열어 잘림 여부 확인(상자 끝에 딱 맞는 것은 괜찮고, 글자가 반쯤 잘린 것만 고침)
        결과: <결과 폴더>/b<묶음>/p<쪽>.png , 끝에 FLAG 목록 출력. --shard 0/3 1/3 2/3 로 3개를 동시에 돌리면 3배 빠름.
주의: 한 번에 너무 긴 글(약 1000자 이상)을 한 대사에 넣으면 상자가 비어 나옴 → 3개씩만 묶음. ag4.dst(스타팅 받은 뒤 연구소) 상태에서 위쪽 NPC 앞 대사 자리(msg538#12·13)를 바꿔 쓰는 것이라 그 상태·그 롬 구조에서만 맞음.
        --labrom 은 ag4.dst 가 불러지는 롬(연구소 NPC 대사 구조가 같은 롬, 예: lab_final2.nds)."""
import sys, os, csv, re, glob, subprocess, argparse
H = os.path.dirname(os.path.abspath(__file__)); G = os.path.abspath(os.path.join(H, '..', '..'))
sys.path.insert(0, G); os.chdir(G)
import hg1, 글_넘침 as g
from hg1 import NDS, NARC, msg_encode
from PIL import Image
ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('dstdir'); ap.add_argument('out')
ap.add_argument('--base', default='포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds')
ap.add_argument('--min', type=float, default=18); ap.add_argument('--shard', default='0/1'); ap.add_argument('--labrom', default=None); ap.add_argument('--only', default=None, help='예: 219:135,268:36 — 이 대사들만 검사')
A = ap.parse_args(); si, sn = map(int, A.shard.split('/')); os.makedirs(A.out, exist_ok=True)
draft = {r['이름'] for r in csv.DictReader(open('NDS_종_초안.tsv', encoding='utf-8'), delimiter='\t')}
new, old = g.load(A.rom), g.load(A.base); CM = hg1.infer_charmap(new, draft)[0]
hang = re.compile('[가-힣]'); cands = []
for fi in range(min(len(new), len(old))):
    for ei in range(min(len(new[fi][1]), len(old[fi][1]))):
        if new[fi][1][ei] == old[fi][1][ei]: continue
        try: t = CM.dec(new[fi][1][ei])
        except Exception: continue
        if hang.search(t) and max(g.width(l) for l in g.lines(t)) >= A.min: cands.append((fi, ei))
if A.only: cands = [tuple(map(int, x.split(':'))) for x in A.only.split(',')]
B = 3; groups = [cands[i:i + B] for i in range(0, len(cands), B)]
print('후보 %d줄 → %d묶음, 내 몫 %s' % (len(cands), len(groups), A.shard), flush=True)
raw = open(A.labrom or A.rom, 'rb').read(); env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
for gi, grp in enumerate(groups):
    if gi % sn != si: continue
    big = '\\f'.join(CM.dec(new[fi][1][ei]) for fi, ei in grp)
    rom = NDS(raw); N = NARC(rom.get(hg1.NARC_PATHS['msg'])); seed, ents = hg1.msg_decode(N.files[538])
    for i in (12, 13): ents[i] = CM.enc(big)
    N.files[538] = msg_encode(seed, ents); out = NDS(raw); out.put(hg1.NARC_PATHS['msg'], N.build())
    rp = os.path.join(A.out, 'rom%d_%d.nds' % (si, sn)); open(rp, 'wb').write(bytes(out.d))
    d = os.path.join(A.out, 'b%03d' % gi); os.makedirs(d, exist_ok=True)
    for f in glob.glob(d + '/*.png'): os.remove(f)
    subprocess.run([sys.executable, os.path.join(H, '글_화면검사_촬영.py'), rp, os.path.join(A.dstdir, 'ag4.dst'), d], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    seen = set()
    for f in sorted(glob.glob(d + '/p*.png')):
        im = Image.open(f).convert('L'); px = im.load(); mx = 0
        for x in range(10, 235):
            if sum(1 for y in range(6, 44) if px[x, y] < 110) > 3: mx = max(mx, x)
        k = Image.open(f).convert('RGB').tobytes()
        if mx >= 228 and k not in seen: seen.add(k); print('FLAG', gi, grp, f, mx, flush=True)
    print('done', gi, grp, flush=True); os.remove(rp)
