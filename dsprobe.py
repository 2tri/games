#!/usr/bin/env python3
"""다른 DS 디지몬 게임 롬(디지몬 월드 DS·Dawn/Dusk·로스트 에볼루션 등) 안의 그림 형식 조사 — 읽기만 한다 (2026-10-12)
목적: 그 게임의 걷기 그림(4방향: 아래 좌·우, 위 좌·우)이 어느 파일에 어떤 형식으로 들어 있는지 알아내서, 다음 단계에 추출기를 만든다.
사용:   python dsprobe.py "<롬.nds>"      → dsprobe_out/보고.txt + 후보 그림 모음 candidate_NN.png (설계자에게 보고.txt 전문과 PNG 몇 장)
하는 일
1) 롬의 파일 목록과 NARC(묶음 파일)마다 안에 든 파일 수·머리글(RGCN=도트, RLCN=팔레트, RECN=셀, RNAN=애니, BTX0=3D텍스처, 압축 LZ 등)
2) 도트(RGCN) 파일이 많은 NARC 는 그림 크기(타일 수)와 색 깊이를 세고, 처음 40장을 가장 가까운 팔레트로 그려 PNG 로 (사람이 보고 「이게 걷기 그림」이라고 알려 주면 됨)
3) LZ 압축(첫 바이트 0x10/0x11) 파일은 풀어서 같은 검사"""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1

def lz_decompress(d):
    """GBA/DS LZ10(0x10)·LZ11(0x11). 아니면 None"""
    if len(d) < 5 or d[0] not in (0x10, 0x11): return None
    n = d[1] | (d[2] << 8) | (d[3] << 16); out = bytearray(); i = 4; lz11 = d[0] == 0x11
    try:
        while len(out) < n:
            flags = d[i]; i += 1
            for b in range(8):
                if len(out) >= n: break
                if flags & (0x80 >> b):
                    if lz11:
                        x = d[i]; ind = x >> 4
                        if ind == 0: ln = (x << 4 | d[i + 1] >> 4) + 0x11; disp = ((d[i + 1] & 0xF) << 8 | d[i + 2]) + 1; i += 3
                        elif ind == 1: ln = ((x & 0xF) << 12 | d[i + 1] << 4 | d[i + 2] >> 4) + 0x111; disp = ((d[i + 2] & 0xF) << 8 | d[i + 3]) + 1; i += 4
                        else: ln = ind + 1; disp = ((x & 0xF) << 8 | d[i + 1]) + 1; i += 2
                    else:
                        ln = (d[i] >> 4) + 3; disp = ((d[i] & 0xF) << 8 | d[i + 1]) + 1; i += 2
                    if disp > len(out): return None
                    for _ in range(ln): out.append(out[-disp])
                else: out.append(d[i]); i += 1
    except IndexError: return None
    return bytes(out[:n]) if len(out) >= n else None

def magic(f):
    if not f: return 'empty'
    if f[:4] == b'NARC': return 'NARC'
    if f[:4] in (b'RGCN', b'RLCN', b'RECN', b'RNAN', b'RAMN', b'RCSN', b'RCMN', b'BTX0', b'BMD0', b'BCA0'): return f[:4].decode()
    if f[0] in (0x10, 0x11) and len(f) > 4: return 'LZ%02X' % f[0]
    return 'other'

def rahc(f):
    c = f.find(b'RAHC')
    if c < 0: return None
    ty, tx, bpp, mp, tiled, size = struct.unpack_from('<HHIIII', f, c + 8)
    return ty, tx, bpp, tiled, size

def draw_tiles(f, pal, maxw=80, maxh=80):
    """RGCN 의 4bpp 타일(8x8)을 가로 tx 타일로 늘어놓아 행 목록으로. ty·tx 가 0xFFFF 면 정사각에 가깝게"""
    r = rahc(f)
    if not r: return None
    ty, tx, bpp, tiled, size = r; c = f.find(b'RAHC'); px = f[c + 0x20:c + 0x20 + size]
    if bpp != 3: return None                                   # 4bpp 만
    ntile = len(px) * 2 // 64
    if tx in (0, 0xFFFF): tx = max(1, int(ntile ** 0.5)); ty = (ntile + tx - 1) // tx
    W, H = min(tx * 8, maxw), min(ty * 8, maxh)
    rows = [[0] * W for _ in range(H)]
    if tiled == 1:                                              # 줄 배치
        for y in range(H):
            for x in range(W):
                i = y * tx * 8 + x; byte = px[i // 2] if i // 2 < len(px) else 0
                rows[y][x] = byte & 15 if i % 2 == 0 else byte >> 4
    else:
        for t in range(min(ntile, tx * ty)):
            tyy, txx = divmod(t, tx)
            for k in range(64):
                i = t * 64 + k; byte = px[i // 2] if i // 2 < len(px) else 0
                v = byte & 15 if i % 2 == 0 else byte >> 4
                y, x = tyy * 8 + k // 8, txx * 8 + k % 8
                if y < H and x < W: rows[y][x] = v
    return rows

def main():
    raw = open(sys.argv[1], 'rb').read(); rom = hg1.NDS(raw)
    out_dir = 'dsprobe_out_' + ''.join(ch for ch in rom.code if ch.isalnum()); os.makedirs(out_dir, exist_ok=True)   # 롬마다 다른 폴더
    L = ['== DS 그림 형식 조사 — %s (%s), 파일 %d개' % (rom.title, rom.code, len(rom.paths))]
    dirs = collections.Counter(p.rsplit('/', 1)[0] if '/' in p else '' for p in rom.paths)
    L.append('폴더: ' + ', '.join('%s(%d)' % kv for kv in sorted(dirs.items())[:60]))
    cands = []; ncand = 0; other_sizes = collections.defaultdict(collections.Counter)
    for path in sorted(rom.paths):
        try: f = rom.get(path)
        except Exception: continue
        m = magic(f)
        if m.startswith('LZ'):
            y = lz_decompress(f)
            if y and y[:4] == b'NARC': f = y; m = 'NARC'; L.append('%s: LZ 압축을 푸니 NARC' % path)
        other_sizes[path.rsplit('/', 1)[0] if '/' in path else ''][m] += 1
        if m == 'NARC':
            try: files = hg1.NARC(f).files
            except Exception: L.append('%s: NARC 못 읽음' % path); continue
            kinds = collections.Counter()
            dec = []
            for x in files:
                k = magic(x)
                if k.startswith('LZ'):
                    y = lz_decompress(x); k = 'LZ→' + magic(y) if y else 'LZ?'
                    dec.append(y or x)
                else: dec.append(x)
                kinds[k] += 1
            L.append('%s: 파일 %d, 종류 %s, 크기 상위 %s' % (path, len(files), dict(kinds.most_common(6)), collections.Counter(len(x) for x in files).most_common(3)))
            if 300 <= len(files) <= 2600 and kinds.get('other', 0) >= len(files) * 0.8:
                L.append('   ★ 종 수와 비슷한 수의 「형식 모름」 파일 — 첫 파일 머리 32바이트: %s' % files[0][:32].hex(' '))
                for q in (1, 2):
                    if q < len(files): L.append('     파일 %d 머리: %s' % (q, files[q][:32].hex(' ')))
            inner = [x for x in dec if x[:4] == b'NARC']
            if inner: L.append('   안에 NARC 가 또 %d개(겹묶음) — 첫 것: %s' % (len(inner), dict(collections.Counter(magic(z) for z in hg1.NARC(inner[0]).files).most_common(5))))
            ncgr = [(i, x) for i, x in enumerate(dec) if x[:4] == b'RGCN']
            if len(ncgr) >= 40:
                dims = collections.Counter(rahc(x)[:2] + (rahc(x)[3],) for _, x in ncgr if rahc(x))
                L.append('   도트 파일 %d: (높이타일, 너비타일, 배치) 분포 %s' % (len(ncgr), dict(dims.most_common(6))))
                pals = [x for x in dec if x[:4] == b'RLCN']
                pal = hg1.nclr(pals[0]) if pals else None
                sh = hg1.Sheet(10, 6); n = 0
                for i, x in ncgr[:60]:
                    rows = draw_tiles(x, pal)
                    if rows: sh.put(n, rows, pal); sh.label(n, i); n += 1
                name = 'candidate_%02d.png' % ncand; sh.save(os.path.join(out_dir, name)); ncand += 1
                L.append('   → %s (처음 60장, 번호 = 파일 번호. 팔레트는 같은 NARC 첫 팔레트라 색은 틀릴 수 있음. 팔레트 파일 %d개)' % (name, len(pals)))
                cands.append(path)
        elif m.startswith('LZ') or m in ('RGCN', 'BTX0', 'RLCN'):
            L.append('%s: %s %d바이트' % (path, m, len(f)))
    L.append('\n== 폴더별 파일 종류(형식 모름 = other)')
    for d_, c_ in sorted(other_sizes.items()): L.append('  %s: %s' % (d_ or '(루트)', dict(c_)))
    L.append('\n== 도트가 많은 NARC(걷기·전투 그림 후보) %d개: %s' % (len(cands), ', '.join(cands)))
    L.append('사용자: candidate_NN.png 를 보고 「걷기 그림(작고 여러 방향)」이 든 번호를 알려 주세요. 설계자: 보고.txt 전문.')
    open(os.path.join(out_dir, '보고.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:3])); print('…', len(L), '줄 → %s/보고.txt, 후보 그림 %d장' % (out_dir, ncand))

if __name__ == '__main__':
    main()
