#!/usr/bin/env python3
"""원인 파일 찾기 (2026-10-15) — 「정상 롬」과 「문제 롬」에서 다른 파일마다 하나씩 되돌린 시험 롬을 만든다.
사용:   python rom_bisect.py "<정상 롬>" "<문제 롬>" --out 가려내기\\        → 가려내기\\00_목록.txt + 되돌림_<n>_<이름>.nds 여러 개
        각 롬을 같은 세이브로 켜서 문제가 「사라지는」 롬의 파일이 원인. (되돌린 것 하나만 빼고 나머지는 문제 롬 그대로)
        --group 4 : 다른 파일이 많을 때 4개씩 묶어 되돌린 롬(먼저 묶음으로 좁히고, 걸린 묶음만 다시 하나씩)
다르게 보는 단위: 이름 있는 파일(a/0/2/7 등 NARC 통째, data/sound/… SDAT), arm9(압축을 풀어 롬 끝에 옮긴 것 포함), 오버레이 하나하나."""
import os, sys, struct, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS

def put_fid(nds, fid, data):
    ns = (nds.used_end() + 0x1FF) & ~0x1FF; ne = ns + len(data)
    if len(nds.d) < ne: nds.d += b'\xff' * (ne - len(nds.d))
    nds.d[ns:ne] = data; struct.pack_into('<II', nds.d, nds.fat_off + fid * 8, ns, ne)
    if ne > struct.unpack_from('<I', nds.d, 0x80)[0]: struct.pack_into('<I', nds.d, 0x80, ne)
    while (0x20000 << nds.d[0x14]) < len(nds.d): nds.d[0x14] += 1

def arm9(nds):
    o, s = struct.unpack_from('<I', nds.d, 0x20)[0], struct.unpack_from('<I', nds.d, 0x2C)[0]; return bytes(nds.d[o:o + s])

def overlays(nds):
    d = nds.d; y9o, y9s = struct.unpack_from('<II', d, 0x50); out = {}
    for k in range(y9s // 32):
        e = struct.unpack_from('<8I', d, y9o + 32 * k); s_, t_ = nds.fat(e[6]); out[e[0]] = (k, e, bytes(d[s_:t_]))
    return out

def diffs(good, bad):
    out = []
    for p in sorted(set(good.paths) & set(bad.paths)):
        if good.get(p) != bad.get(p): out.append(('file', p))
    if arm9(good) != arm9(bad) or bytes(good.d[0x20:0x30]) != bytes(bad.d[0x20:0x30]): out.append(('arm9', 'arm9'))
    og, ob = overlays(good), overlays(bad)
    for k in sorted(set(og) & set(ob)):
        if og[k][2] != ob[k][2] or og[k][1] != ob[k][1]: out.append(('overlay', k))
    return out

def revert(bad_raw, good, items):
    r = NDS(bad_raw)
    for kind, key in items:
        if kind == 'file': r.put(key, good.get(key))
        elif kind == 'arm9':
            a = arm9(good); ns = (r.used_end() + 0x1FF) & ~0x1FF
            if len(r.d) < ns + len(a): r.d += b'\xff' * (ns + len(a) - len(r.d))
            r.d[ns:ns + len(a)] = a
            struct.pack_into('<I', r.d, 0x20, ns); r.d[0x24:0x30] = good.d[0x24:0x30]
            if ns + len(a) > struct.unpack_from('<I', r.d, 0x80)[0]: struct.pack_into('<I', r.d, 0x80, ns + len(a))
        elif kind == 'overlay':
            og = overlays(good)[key]; ob = overlays(r)[key]
            put_fid(r, ob[1][6], og[2])
            y9o = struct.unpack_from('<I', r.d, 0x50)[0]; e = list(og[1]); e[6] = ob[1][6]
            struct.pack_into('<8I', r.d, y9o + 32 * ob[0], *e)
    struct.pack_into('<H', r.d, 0x15E, hg1.crc16(bytes(r.d[0:0x15E])))
    return bytes(r.d)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('good'); ap.add_argument('bad'); ap.add_argument('--out', default='가려내기'); ap.add_argument('--group', type=int, default=1)
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    graw = open(A.good, 'rb').read(); braw = open(A.bad, 'rb').read(); good = NDS(graw)
    ds = diffs(good, NDS(braw))
    L = ['== 다른 곳 %d개 (정상 %s / 문제 %s)' % (len(ds), A.good, A.bad)]
    groups = [ds[i:i + A.group] for i in range(0, len(ds), A.group)]
    for n, g in enumerate(groups):
        tag = '+'.join(str(k).replace('/', '') for _, k in g)[:60]
        fn = os.path.join(A.out, '되돌림_%02d_%s.nds' % (n, tag))
        open(fn, 'wb').write(revert(braw, good, g)); L.append('%02d  %s  → %s' % (n, ', '.join('%s %s' % x for x in g), os.path.basename(fn)))
    L.append('각 롬을 같은 세이브로 켜서 문제가 사라지는 번호를 찾으면, 그 줄의 파일이 원인.')
    open(os.path.join(A.out, '00_목록.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
