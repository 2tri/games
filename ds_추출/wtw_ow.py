#!/usr/bin/env python3
"""WtW 「Dawn/Dusk·Lost Evo·SXW sprite topic」 시트에서 작은 걷기 그림을 잘라 dsw_ow 꼴(<한글>_DSW걷기.png)로 저장 (2026-10-19, 클라우드 Claude)
시트 구조(Zero_xm7 등): 큰 전투 그림들 아래에 작은 그림 줄 — 1줄 = 뒷모습 3컷 + 좌우반전 3컷, 2줄 = 앞모습 3컷 + 좌우반전 3컷.
결과: 2칸 x 4줄 (아래=앞 0·1, 위=뒤 0·1, 왼쪽=앞 0·1, 오른쪽=앞 3·4).
사용: python3 wtw_ow.py <시트 폴더> <출력 폴더>   (대응표는 아래 TABLE)"""
import os, sys
from PIL import Image
TABLE = {'플롯트몬': '042_Plotmon', '모노크로몬': '181_Monochromon', '울퉁몬': '035_Gotsumon', '나니몬': '179_Nanimon', '베이더몬': '268_Vademon',
         '레드베지몬': '171_RedVegiemon', '데블드라몬': '186_Devidramon', '플라이몬': '168_Flymon', '머슈룸몬': '078_Mushmon',
         '아포카리몬': '351_Apocalymon', '키메라몬': '243_Chimeramon', '벨리얼묘티': '333_BelialVamdemon', '마린데블몬': '236_MarineDevimon',
         '청룡몬': 'Qinglongmon', '백호몬': 'Baihumon', '주작몬': 'zhuqiaomon', '현무몬': 'Xuanwumon', '실러캔몬': '157_Coelamon',
         '가니몬': '062_Ganimon', '피콜로몬': '202_Piccolomon', '옥토몬': '155_Octomon', '레볼몬': '184_Revolmon', '무사몬': '189_Musyamon',
         '밀레니엄몬': '370_Milleniumon', '바이킹몬': '362_Vikemon', '메탈티라몬': '269_MetalTyranomon', '그란쿠와몬': '365_GranKuwagamon',
         '발키리몬': '360_Valkyrimon', '데비타마몬': '320_Devitamamon'}
SMALL = 60      # 작은 그림으로 볼 최대 크기(px)
# 뺀 종: 게소몬·맘몬(원본 시트가 흐릿함), 바이킹몬(작은 그림 줄 없음)

def load(path):
    im = Image.open(path).convert('RGBA'); p = im.load(); bg = p[0, 0]
    if bg[3]:                                   # 단색 바탕 → 투명
        for y in range(im.height):
            for x in range(im.width):
                if p[x, y][:3] == bg[:3]: p[x, y] = (0, 0, 0, 0)
    return im

def comps(im):
    w, h = im.size; a = im.getchannel('A').load(); seen = bytearray(w * h); out = []
    for y in range(h):
        for x in range(w):
            if seen[y*w+x] or a[x, y] < 128: continue
            st = [(x, y)]; seen[y*w+x] = 1; x0 = x1 = x; y0 = y1 = y; n = 0
            while st:
                u, v = st.pop(); n += 1
                x0, x1, y0, y1 = min(x0, u), max(x1, u), min(y0, v), max(y1, v)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        uu, vv = u+dx, v+dy
                        if 0 <= uu < w and 0 <= vv < h and not seen[vv*w+uu] and a[uu, vv] >= 128:
                            seen[vv*w+uu] = 1; st.append((uu, vv))
            if n >= 40: out.append([x0, y0, x1+1, y1+1])
    return out

def rows_of(cs):
    cs = sorted([c for c in cs if c[2]-c[0] <= SMALL and c[3]-c[1] <= SMALL], key=lambda c: (c[1]+c[3])/2)
    rows = []
    for c in cs:
        cy = (c[1]+c[3])/2
        if rows and abs(cy - rows[-1]['cy']) < 12: rows[-1]['c'].append(c); rows[-1]['cy'] = (rows[-1]['cy'] + cy) / 2
        else: rows.append({'cy': cy, 'c': [c]})
    return [sorted(r['c'], key=lambda c: c[0]) for r in rows if len(r['c']) >= 6]

def frames(im, row):
    row = row[:6]; y0 = min(c[1] for c in row) - 2; y1 = max(c[3] for c in row) + 2
    out = []
    for i, c in enumerate(row):
        xl = (row[i-1][2] + c[0]) // 2 if i else c[0] - 3
        xr = (c[2] + row[i+1][0]) // 2 if i < len(row) - 1 else c[2] + 3
        f = im.crop((xl, y0, xr, y1)); f = f.crop(f.getchannel('A').getbbox()); out.append(f)
    return out

def make(path, dst):
    im = load(path); rs = rows_of(comps(im))
    if len(rs) < 2: return 'small rows %d' % len(rs)
    back, front = frames(im, rs[0]), frames(im, rs[1])
    grid = [(front[0], front[1]), (back[0], back[1]), (front[0], front[1]), (front[3], front[4])]
    w = max(f.width for r in grid for f in r); h = max(f.height for r in grid for f in r)
    sheet = Image.new('RGBA', (2 * w + 4, 4 * h + 12), (0, 0, 0, 0))
    for r, pair in enumerate(grid):
        for c, f in enumerate(pair):
            sheet.alpha_composite(f, (c * (w + 4) + (w - f.width) // 2, r * (h + 4) + h - f.height))
    sheet.save(dst); return 'ok %dx%d' % (w, h)

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    for ko, base in TABLE.items():
        p = os.path.join(src, base + '.png')
        print(ko, base, make(p, os.path.join(out, ko + '_DSW걷기.png')) if os.path.exists(p) else '시트 없음')
