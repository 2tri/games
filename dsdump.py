#!/usr/bin/env python3
"""DS 롬의 그림 묶음(NARC) 하나를 통째로 PNG 로 뽑기 — 읽기만 한다 (2026-10-12). dsprobe.py 로 「어느 묶음이 걷기 그림인지」 안 뒤에 쓴다.
사용:   python dsdump.py "<롬.nds>" <NARC 경로>  [--out 폴더] [--pal auto|N] [--max N]
        예) python dsdump.py dawn.nds a/0/3/1 --out dump_a031
- NARC 안의 도트 파일(RGCN, LZ 압축이면 풀어서)을 번호 순서로 <번호>.png 로 저장(4bpp·8bpp).
- 팔레트: --pal auto(기본) = 팔레트 파일(RLCN)이 도트 파일과 수가 같으면 같은 순번, 아니면 첫 팔레트. --pal 3 = 3번째 RLCN 파일 고정.
  (색이 틀리면 --pal 로 바꿔 보면 됨. 걷기 그림인지 구별하는 데는 색이 틀려도 지장 없음)
- 결과 폴더의 목록.txt 에 번호·크기·타일 배치. 설계자에게는 목록.txt 와 그림 몇 장."""
import os, sys, argparse, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1, dsprobe

def rows_of(f, pal16):
    """RGCN → (RGBA 행, (높이타일, 너비타일, bpp, 배치))"""
    r = dsprobe.rahc(f)
    if not r: return None, None
    ty, tx, bpp, tiled, size = r; c = f.find(b'RAHC'); px = f[c + 0x20:c + 0x20 + size]
    if bpp == 3:
        idx = dsprobe.draw_tiles(f, None, maxw=4096, maxh=4096)
    elif bpp == 4:                                   # 8bpp
        ntile = len(px) // 64
        if tx in (0, 0xFFFF): tx = max(1, int(ntile ** 0.5)); ty = (ntile + tx - 1) // tx
        W, H = tx * 8, ty * 8; idx = [[0] * W for _ in range(H)]
        for t in range(min(ntile, tx * ty)):
            tyy, txx = divmod(t, tx)
            for k in range(64):
                y, x = tyy * 8 + k // 8, txx * 8 + k % 8
                if tiled == 1: v = px[y * W + x] if y * W + x < len(px) else 0
                else: v = px[t * 64 + k]
                idx[y][x] = v
    else: return None, None
    if not idx: return None, None
    out = []
    for row in idx:
        out.append([(0, 0, 0, 0) if v == 0 else (pal16[v % len(pal16)] + (255,) if pal16 else ((v * 37) % 256, (v * 91) % 256, (v * 53) % 256, 255)) for v in row])
    return out, (ty, tx, bpp, tiled)

def all_pal(f):
    """RLCN 의 모든 색(16색씩 여러 벌일 수 있음)"""
    c = f.find(b'TTLP')
    if c < 0: return None
    n = struct.unpack_from('<I', f, c + 0x10)[0] // 2; off = c + 0x18; cols = []
    for i in range(n):
        v = struct.unpack_from('<H', f, off + i * 2)[0]
        cols.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return cols

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('narc'); ap.add_argument('--out'); ap.add_argument('--pal', default='auto'); ap.add_argument('--max', type=int, default=100000)
    A = ap.parse_args()
    from PIL import Image
    raw = open(A.rom, 'rb').read(); rom = hg1.NDS(raw)
    files = hg1.NARC(rom.get(A.narc)).files
    dec = []
    for x in files:
        y = dsprobe.lz_decompress(x) if (x and x[0] in (0x10, 0x11)) else None
        dec.append(y or x)
    gfx = [(i, x) for i, x in enumerate(dec) if x[:4] == b'RGCN']
    pals = [(i, x) for i, x in enumerate(dec) if x[:4] == b'RLCN']
    out = A.out or ('dump_' + A.narc.replace('/', ''))
    os.makedirs(out, exist_ok=True)
    L = ['== %s 의 %s: 파일 %d, 도트 %d, 팔레트 %d' % (rom.code, A.narc, len(files), len(gfx), len(pals))]
    for k, (i, x) in enumerate(gfx[:A.max]):
        if A.pal == 'auto': pf = pals[k][1] if len(pals) == len(gfx) else (pals[0][1] if pals else None)
        else: pf = pals[int(A.pal)][1] if pals else None
        cols = all_pal(pf) if pf else None
        rows, info = rows_of(x, cols[:256] if cols else None)
        if not rows: L.append('%d: 못 읽음' % i); continue
        im = Image.new('RGBA', (len(rows[0]), len(rows)))
        im.putdata([p for r in rows for p in r]); im.save(os.path.join(out, '%04d.png' % i))
        L.append('%04d.png: %dx%d (높이타일 %d, 너비타일 %d, bpp %s, 배치 %s)' % (i, len(rows[0]), len(rows), info[0], info[1], '4' if info[2] == 3 else '8', '줄' if info[3] == 1 else '타일'))
    open(os.path.join(out, '목록.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(L[0]); print('→ %s/ (%d장) — 목록.txt 와 그림 몇 장을 설계자에게' % (out, min(len(gfx), A.max)))

if __name__ == '__main__':
    main()
