#!/usr/bin/env python3
"""디지몬 월드 DS(ADNE) 의 dat/MCHR(맵 위 걷기 그림) 뽑기 — 롬은 읽기만 한다 (2026-10-13, Claude 작성)
사용:   python ds_mchr.py "<Digimon World DS 롬.nds>" [--out 폴더] [--probe N]
형식(크기·헤더로 확인):
  한 마리 = 3파일  <번호>a · <번호>c · <번호>p
  <번호>c : LZ10 압축. 풀면 [컷 수 u32][컷 크기 u32] + 컷들. 컷 = 8x8 타일 4bpp. 컷 바이트 → 크기(눈으로 확인): 128 = 16x16, 256 = 16x32, 512 = 32x32, 1024 = 32x64, 2048 = 64x64
  <번호>p : 0x30 런렝스 압축. 풀면 32바이트 = BGR555 16색 (0번 색 = 투명)
  <번호>a : 0x30 런렝스 압축. 컷 순서·움직임 표(여기서는 쓰지 않음)
결과: <out>/<번호>.png (컷을 가로로 늘어놓은 그림, 2배 확대) + <out>/모음_NN.png (번호 붙은 모음) + <out>/목록.tsv"""
import os, sys, struct, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import hg1, dsprobe
from PIL import Image, ImageDraw

def rle(d):
    """GBA/DS BIOS RLUnComp(0x30)"""
    if not d or d[0] != 0x30: return None
    n = d[1] | d[2] << 8 | d[3] << 16; i = 4; out = bytearray()
    while len(out) < n and i < len(d):
        f = d[i]; i += 1
        if f & 0x80:
            out += bytes([d[i]]) * ((f & 0x7F) + 3); i += 1
        else:
            l = (f & 0x7F) + 1; out += d[i:i + l]; i += l
    return bytes(out[:n])

def palette(p):
    raw = rle(p) or p
    cols = []
    for k in range(0, min(len(raw), 32), 2):
        v = raw[k] | raw[k + 1] << 8
        cols.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return cols + [(0, 0, 0)] * (16 - len(cols))

def frames(c):
    y = dsprobe.lz_decompress(c) or c
    if len(y) < 8: return [], 0
    cnt, size = struct.unpack_from('<II', y, 0)
    if cnt == 0 or size == 0 or 8 + cnt * size != len(y): return [], 0
    return [y[8 + i * size:8 + (i + 1) * size] for i in range(cnt)], size

def frame_image(fr, cols, tw):
    """타일(8x8, 4bpp, 낮은 4비트 먼저)을 가로 tw 타일로 늘어놓음 → RGBA"""
    nt = len(fr) // 32; th = (nt + tw - 1) // tw
    im = Image.new('RGBA', (tw * 8, th * 8), (0, 0, 0, 0)); px = im.load()
    for t in range(nt):
        ox, oy = (t % tw) * 8, (t // tw) * 8
        for yy in range(8):
            for xx in range(4):
                b = fr[t * 32 + yy * 4 + xx]
                for k, v in ((0, b & 15), (1, b >> 4)):
                    if v: px[ox + xx * 2 + k, oy + yy] = cols[v] + (255,)
    return im

def tiles_wide(size, mode):
    # 눈으로 확인한 배치: 128바이트 = 16x16, 256 = 16x32, 512 = 32x32, 1024 = 32x64, 2048 = 64x64
    if size == 1024 and mode == 'wide': return 8
    return {128: 2, 256: 2, 512: 4, 1024: 4, 2048: 8}.get(size, 4)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default='mchr_out')
    ap.add_argument('--probe', help='이 번호 한 마리만 64x32·32x64 두 가지로 그려 비교(probe_번호.png)')
    ap.add_argument('--wide', action='store_true', help='1024바이트 컷을 64x32 로(기본 32x64)')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    rom = hg1.NDS(open(A.rom, 'rb').read())
    ids = sorted({p.split('/')[-1][:-1] for p in rom.paths if p.startswith('dat/MCHR/') and p[-1] == 'c'}, key=lambda s: (int(s, 16) if all(ch in '0123456789abcdefABCDEF' for ch in s) else 1 << 30, s))   # 파일 이름 = 16진수 번호 + a/c/p
    BG = (40, 60, 90, 255)
    if A.probe is not None:
        n = A.probe; fr, size = frames(rom.get('dat/MCHR/%sc' % n)); cols = palette(rom.get('dat/MCHR/%sp' % n))
        rows = []
        for tw in (2, 4, 8):
            ims = [frame_image(f, cols, tw) for f in fr[:8]]
            row = Image.new('RGBA', (sum(i.width for i in ims) + 2 * len(ims), max(i.height for i in ims)), BG); x = 0
            for i in ims: row.alpha_composite(i, (x, 0)); x += i.width + 2
            rows.append(row)
        sheet = Image.new('RGBA', (max(r.width for r in rows), sum(r.height for r in rows) + 6), (0, 0, 0, 255)); y = 0
        for r in rows: sheet.alpha_composite(r, (0, y)); y += r.height + 6
        sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
        sheet.save(os.path.join(A.out, 'probe_%s.png' % n)); print('probe', n, '컷', len(fr), '크기', size); return
    listing = ['번호\t컷 수\t컷 바이트\t그림 크기']; thumbs = []; ok = bad = 0
    for n in ids:
        try:
            fr, size = frames(rom.get('dat/MCHR/%sc' % n)); cols = palette(rom.get('dat/MCHR/%sp' % n))
        except KeyError:
            bad += 1; listing.append('%s\t(p 또는 c 없음)' % n); continue
        if not fr: bad += 1; listing.append('%s\t(형식 다름)' % n); continue
        tw = tiles_wide(size, 'wide' if A.wide else 'tall')
        ims = [frame_image(f, cols, tw) for f in fr]
        w, h = ims[0].size; per = 12
        sheet = Image.new('RGBA', (min(len(ims), per) * w, ((len(ims) + per - 1) // per) * h), BG)
        for k, i in enumerate(ims): sheet.alpha_composite(i, ((k % per) * w, (k // per) * h))
        sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(os.path.join(A.out, '%s.png' % n))
        listing.append('%s\t%d\t%d\t%dx%d' % (n, len(fr), size, w, h)); thumbs.append((n, ims[:4])); ok += 1
    # 번호 붙은 모음: 한 장에 10 x 8 마리, 마리마다 앞 4컷
    per_page = 80
    for pg in range(0, len(thumbs), per_page):
        cw, ch = 4 * 64 + 6, 64 + 14
        page = Image.new('RGBA', (10 * cw, 8 * ch), (20, 20, 20, 255)); dr = ImageDraw.Draw(page)
        for k, (n, ims) in enumerate(thumbs[pg:pg + per_page]):
            x0, y0 = (k % 10) * cw, (k // 10) * ch
            dr.rectangle([x0, y0 + 12, x0 + cw - 4, y0 + ch - 2], fill=BG)
            dr.text((x0 + 2, y0), str(n), fill=(255, 255, 0, 255))
            for j, i in enumerate(ims): page.alpha_composite(i, (x0 + j * 64, y0 + 13))
        page.save(os.path.join(A.out, '모음_%02d.png' % (pg // per_page + 1)))
    open(os.path.join(A.out, '목록.tsv'), 'w', encoding='utf-8').write('\n'.join(listing) + '\n')
    print('마리 %d, 뽑음 %d, 못 뽑음 %d → %s (모음 %d장)' % (len(ids), ok, bad, A.out, (len(thumbs) + per_page - 1) // per_page))

if __name__ == '__main__':
    main()
