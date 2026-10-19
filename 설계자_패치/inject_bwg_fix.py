#!/usr/bin/env python3
"""블랙워그레이몬(칸 109)의 파티 아이콘·따라다니는 그림을 맞춘다. (Claude 작성, 2026-10-16)
사용:   python inject_bwg_fix.py <입력 롬.nds> <출력 롬.nds> [--slot 109] [--src-slot 257] [--art nds_art/057_블랙워그레이몬] [--paltab 0x10023B]
왜:     hg4_icons·hg4_follow 는 이름이 「블랙워그레이몬」이면 건너뜀(전투 그림은 hg4 가 워그레이몬 6파일을 복사하고 보통·색다른 색을 맞바꿈).
        → 파티 아이콘은 원래 포켓몬(칸 109 = 또가스) 그대로, 따라다니는 그림은 보통 색(금색) 워그레이몬(전투 그림은 검정) 이라 어긋남.
방법:   ① 따라다니는 그림: 칸 109 의 필드 그림 파일(= 칸 257 것을 복사해 둔 것)의 팔레트 두 벌(보통·색다른 색)을 맞바꿈 → 전투 그림처럼 검정이 보통 색.
        ② 아이콘: nds_art/057_블랙워그레이몬/icon.png(32x64, 16색)를 hg4_icons 와 같은 방법(공용 팔레트 3벌 중 가장 가까운 벌, arm9 팔레트 표 = 압축 푼 arm9 + paltab + 칸)으로."""
import sys, os, struct, argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
import hg1, hg4, hg4_icons as HI, hg4_follow as HF
from hg1 import NDS, NARC

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--slot', type=int, default=109); ap.add_argument('--src-slot', type=int, default=257)
ap.add_argument('--art', default='nds_art/057_블랙워그레이몬'); ap.add_argument('--paltab', default='0x10023B')
ap.add_argument('--follow-file', type=int, default=None, help='칸 109 의 필드 그림 파일 번호(기본: hg4_follow 보고에서 407)')
ap.add_argument('--src-file', type=int, default=None)
A = ap.parse_args()

raw = bytearray(open(A.rom, 'rb').read()); nd = NDS(bytes(raw))
msgs = []
# ① 따라다니는 그림 — 두 팔레트 맞바꿈
fol = NARC(nd.get('a/0/8/1')); ff = list(fol.files)
ffile = A.follow_file; sfile = A.src_file
if ffile is None or sfile is None:
    # 같은 내용의 필드 그림 파일 쌍 중 8장 따라다니는 그림(tsure_poke)인 것: 종 칸 109 와 257 만 보고 싶으나 번호 표가 없으니 기본값을 쓰고 확인
    ffile, sfile = 407, 587
lay = HF.btx_layout(ff[ffile])
if not HF.is_follow(lay) or len(lay['pal']) != 2: sys.exit('필드 그림 파일 %d 가 따라다니는 그림(팔레트 2벌)이 아님' % ffile)
if ff[ffile] == ff[sfile]:
    d = bytearray(ff[ffile]); o0, o1 = lay['pal'][0][1], lay['pal'][1][1]
    a, b = bytes(d[o0:o0 + 32]), bytes(d[o1:o1 + 32])
    d[o0:o0 + 32], d[o1:o1 + 32] = b, a
    ff[ffile] = bytes(d); msgs.append('따라다니는 그림: 파일 %d 팔레트 두 벌 맞바꿈(검정이 보통 색)' % ffile)
else:
    msgs.append('경고: 필드 그림 파일 %d 와 %d 가 같지 않음 — 이미 바꿨거나 다른 롬. 따라다니는 그림은 건드리지 않음' % (ffile, sfile))
fol.files = ff
out = NDS(bytes(raw)); out.put('a/0/8/1', fol.build())
raw = bytearray(out.d)

# ② 아이콘
nar = NARC(NDS(bytes(raw)).get('a/0/2/0')); files = list(nar.files)
first = next(i for i, f in enumerate(files) if f[:4] == b'RGCN')
palf = next(f for f in files if f[:4] == b'RLCN'); pals = HI.palettes(palf)
fi = first + A.slot
ip = os.path.join(A.art, 'icon.png')
if os.path.exists(ip) and files[fi][:4] == b'RGCN':
    rows, cols = hg4.read_indexed(ip)
    best = None
    for k in range(len(pals)):
        mp = {i: HI.nearest(cols[i], pals[k]) for i in range(1, len(cols))}
        err = sum(sum((a - b) ** 2 for a, b in zip(cols[i], pals[k][mp[i]])) for i in range(1, len(cols)))
        if best is None or err < best[0]: best = (err, k, mp)
    err, k, mp = best
    new_rows = [[mp.get(v, 0) if v else 0 for v in r] for r in rows]
    files[fi], _t = HI.encode(files[fi], new_rows)
    nar.files = files
    out = NDS(bytes(raw)); out.put('a/0/2/0', nar.build()); raw = bytearray(out.d)
    a9o = struct.unpack_from('<I', raw, 0x20)[0]; off = int(A.paltab, 0)
    old = raw[a9o + off + A.slot]; raw[a9o + off + A.slot] = k
    msgs.append('아이콘: 파일 %d ← %s, 팔레트 벌 %d(표 값 %d → %d), 색 차이 %d' % (fi, ip, k, old, k, err))
else:
    msgs.append('아이콘: %s 없음 또는 파일 %d 가 그림이 아님 — 건너뜀' % (ip, fi))
open(A.out, 'wb').write(bytes(raw))
print('\n'.join(msgs)); print('저장:', A.out)
