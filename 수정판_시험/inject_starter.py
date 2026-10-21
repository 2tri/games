#!/usr/bin/env python3
"""python inject_starter.py <입력 롬> <출력 롬> — 스타팅 3종 중 파닥몬(슬롯 277)을 베타몬(슬롯 313)으로 (2026-10-20 사용자 결정)
이유: 조수의 알이 토코몬 → 파닥몬(→엔젤몬)으로 이어지므로 스타팅 파닥몬과 겹침. 베타몬(물·전기, 속성 데이터로 지정 — 케라몬이 바이러스라 백신·데이터·바이러스 3종을 유지): 첫 수호자 소라(비행)에 유리, 스타팅 타입이 불꽃·고스트악·물전기로 안 겹침.
무엇을: 스타팅 표(4바이트 3칸 [277, 252, 132] = 파닥몬·아구몬·케라몬)가 박힌 두 곳 — arm9 0x108C90, 오버레이 61 +0x1A98 — 의 첫 칸을 313 으로.
        오버레이 61 은 풀어서 고친 뒤 다시 압축해 넣음(blz_compress.py).
        볼 고를 때 확인 대사 2줄(msg189#1 「데이터 디지몬 파닥몬이다 … 하겠니?」, msg189#4 볼 터치)에 종 이름이 글자로 박혀 있어 베타몬으로 바꿈."""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import csv
import hg1, hg_attr, hg_scan
from blz_compress import blz_compress
from hg1 import NDS, NARC, msg_decode, msg_encode
OLD, NEW = 277, 313
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read())
trio = struct.pack('<III', OLD, 252, 132); done = []
# arm9(압축 아님)
a9o, a9s = struct.unpack_from('<I', nds.d, 0x20)[0], struct.unpack_from('<I', nds.d, 0x2C)[0]
a9 = bytes(nds.d[a9o:a9o + a9s]); k = a9.find(trio)
if k >= 0:
    assert a9.count(trio) == 1; struct.pack_into('<I', nds.d, a9o + k, NEW); done.append('arm9 0x%X' % k)
elif a9.find(struct.pack('<III', NEW, 252, 132)) >= 0: done.append('arm9 이미 바꿈')
else: raise SystemExit('arm9 에서 스타팅 표를 못 찾음')
# 오버레이 61
hg_attr.OV_ID = 61
pos, e = hg_attr.ov_entry(nds)
hg_attr.OV_RAM = e[1]
pos, e, ov, comp = hg_attr.ov_read(nds)
k = bytes(ov).find(trio)
if k >= 0:
    assert bytes(ov).count(trio) == 1
    struct.pack_into('<I', ov, k, NEW)
    if comp:
        cb = blz_compress(bytes(ov)); assert hg_scan.blz_decompress(cb) == bytes(ov)
        how = hg_attr.put_fid(nds, e[6], cb); e[7] = 0x01000000 | len(cb)
    else:
        how = hg_attr.put_fid(nds, e[6], bytes(ov)); e[7] = 0
    struct.pack_into('<8I', nds.d, pos, *e); done.append('오버레이61 +0x%X(%s)' % (k, how))
elif bytes(ov).find(struct.pack('<III', NEW, 252, 132)) >= 0: done.append('오버레이61 이미 바꿈')
else: raise SystemExit('오버레이 61 에서 스타팅 표를 못 찾음')
# 확인 대사(글자로 박힌 종 이름)
P = os.path.abspath(os.path.join(H, '..'))
draft = {r['이름'] for r in csv.DictReader(open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t')}
nar = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in nar.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
seed, ents = MSG[189]; ents = list(ents); files = list(nar.files); nt = 0
for ei in (1, 4):
    t = CM.dec(ents[ei])
    if '파닥몬' in t:
        t2 = t.replace('파닥몬', '베타몬'); enc = CM.enc(t2); assert CM.dec(enc) == t2, '확인 대사 검산 실패 msg189#%d' % ei
        ents[ei] = enc; nt += 1
    else: assert '베타몬' in t, 'msg189#%d 에 스타팅 이름이 없음: %s' % (ei, t)
if nt: files[189] = msg_encode(seed, ents); nar.files = files; done.append('확인 대사 %d줄(%s)' % (nt, nds.put(hg1.NARC_PATHS['msg'], nar.build())))
open(dst, 'wb').write(bytes(nds.d)); print('ok 스타팅 파닥몬 → 베타몬:', ', '.join(done))
