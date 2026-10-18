#!/usr/bin/env python3
"""DS 디지몬 롬의 「형식 모름」 폴더(dat/MCHR, dat/BTCHR, dat/spr, dat/dm, dat/en, dat/map …)를 뜯어 보기 — 읽기만 (2026-10-13)
사용:   python dsraw.py "<롬.nds>" <폴더 접두어> [--max N] [--out 폴더]
        예) python dsraw.py "Digimon World DS.nds" dat/MCHR --max 40
하는 일(파일마다):
 1) LZ 압축이면 푼다. 2) 「묶음」(앞에 개수·오프셋 표가 있는 자체 형식)이면 조각으로 쪼갠다(조각도 LZ 면 풀기).
 3) 조각/파일의 앞 32바이트를 16진수로 적고, 도트 그림이라 가정해 4bpp 타일(8x8)을 너비 4·8·16타일로 늘어놓은 PNG 를 만든다(회색 단계).
    BGR555 팔레트처럼 보이는 조각(16·32·256색 × 2바이트)은 「팔레트 후보」로 적는다.
사람이 PNG 를 보고 「어느 파일·너비에서 디지몬 모양이 보이는지」만 알려 주면 설계자가 추출기를 만든다.
결과: <out>/목록.txt + <파일>[_조각n]_w4.png / _w8.png / _w16.png"""
import os, sys, struct, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1, dsprobe

def unlz(f):
    if f and f[0] in (0x10, 0x11):
        y = dsprobe.lz_decompress(f)
        if y: return y, True
    return f, False

def split_archive(f):
    """자체 묶음 형식 추정: [개수 u32][오프셋 u32 × 개수] 또는 [오프셋 u32 × n, 끝 = 파일 길이]. 아니면 None"""
    n = len(f)
    if n < 8: return None
    cnt = struct.unpack_from('<I', f, 0)[0]
    if 1 < cnt <= 4096 and 4 + 4 * cnt <= n:
        offs = list(struct.unpack_from('<%dI' % cnt, f, 4))
        if all(0 < o <= n for o in offs) and offs == sorted(offs) and offs[0] >= 4 + 4 * cnt:
            return [f[a:b] for a, b in zip(offs, offs[1:] + [n])]
    # 개수 없이 오프셋 표만(첫 오프셋 = 표 길이)
    first = cnt
    if 8 <= first <= n and first % 4 == 0:
        cnt2 = first // 4
        offs = list(struct.unpack_from('<%dI' % cnt2, f, 0))
        if 1 < cnt2 <= 4096 and all(0 < o <= n for o in offs) and offs == sorted(offs):
            return [f[a:b] for a, b in zip(offs, offs[1:] + [n])]
    return None

def looks_palette(f):
    if len(f) not in (32, 64, 512) or len(f) % 2: return False
    vals = struct.unpack('<%dH' % (len(f) // 2), f)
    return all(v < 0x8000 for v in vals) and len(set(vals)) > 3

def tiles_png(data, tiles_w, path):
    from PIL import Image
    ntile = len(data) * 2 // 64
    if ntile == 0: return False
    px = []
    for b in data: px += [b & 15, b >> 4]
    tiles_h = (ntile + tiles_w - 1) // tiles_w; W, H = tiles_w * 8, tiles_h * 8
    im = Image.new('L', (W, H), 0); p = im.load()
    for t in range(ntile):
        ty, tx = divmod(t, tiles_w)
        for k in range(64): p[tx * 8 + k % 8, ty * 8 + k // 8] = px[t * 64 + k] * 17
    im.resize((W * 3, H * 3), Image.NEAREST).save(path); return True

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('prefix'); ap.add_argument('--max', type=int, default=40); ap.add_argument('--out')
    A = ap.parse_args()
    rom = hg1.NDS(open(A.rom, 'rb').read())
    out = A.out or ('raw_' + A.prefix.replace('/', '_')); os.makedirs(out, exist_ok=True)
    paths = sorted(p for p in rom.paths if p.startswith(A.prefix.rstrip('/') + '/'))
    L = ['== %s 의 %s: 파일 %d개 (앞 %d개만)' % (rom.code, A.prefix, len(paths), A.max)]
    npng = 0
    for path in paths[:A.max]:
        f = rom.get(path); name = os.path.basename(path)
        f, lz = unlz(f)
        parts = split_archive(f)
        L.append('%s: %d바이트%s 머리 %s%s' % (name, len(f), ' (LZ 풀음)' if lz else '', f[:32].hex(' '), ' → 묶음 %d조각' % len(parts) if parts else ''))
        chunks = [(name, f)] if not parts else [('%s_조각%d' % (name, k), c) for k, c in enumerate(parts)]
        for cname, c in chunks[:24]:
            c, lz2 = unlz(c)
            if parts: L.append('   %s: %d바이트%s 머리 %s%s' % (cname, len(c), ' (LZ 풀음)' if lz2 else '', c[:24].hex(' '), ' ★팔레트 후보' if looks_palette(c) else ''))
            if len(c) >= 64 and npng < 400:
                for w in (4, 8, 16): tiles_png(c, w, os.path.join(out, '%s_w%d.png' % (cname, w)))
                npng += 3
    L.append('\n사용자: _w4/_w8/_w16 중 디지몬 모양이 보이는 그림의 파일 이름과 너비를 알려 주세요. 설계자: 목록.txt 전문.')
    open(os.path.join(out, '목록.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(L[0]); print('→ %s/ (목록.txt + 그림 %d장)' % (out, npng))

if __name__ == '__main__':
    main()
