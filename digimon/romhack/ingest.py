"""받은 그림 한 장(왼쪽 앞모습 · 오른쪽 뒷모습) → 롬에 넣을 앞·뒤 그림
  python3 ingest.py 받은그림.png metalgreymon 완전체
  → art/src/metalgreymon_ai.png (원본 보관), art/metalgreymon-f.png · -b.png (4색 도트), art/_metalgreymon_sheet.png (확인용)
앞모습 크기는 등급으로: 유아기·유년기 40, 성장기 48, 성숙기 이상 56 (디지몬스터 칸 크기 5·6·7). 뒷모습은 48.
나누는 곳: 두 그림 사이의 흰 세로 띠 (없으면 가운데)."""
import os, sys, shutil
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WEB, 'tools'))
import snapc

FRONT = {'유아기Ⅰ': 40, '유아기Ⅱ': 40, '유년기Ⅰ': 40, '유년기Ⅱ': 40, '유년기': 40, '성장기': 48}


def split(im):
    a = np.asarray(im.convert('L')).astype(int); h, w = a.shape
    ink = (a < 235).sum(0)                                   # 세로줄마다 그림이 있는 칸 수
    mid = range(int(w * .3), int(w * .7))
    empty = [x for x in mid if ink[x] <= h * 0.002]
    if empty:                                                 # 가운데 근처 빈 띠 중 가장 긴 것의 가운데
        runs, s = [], empty[0]
        for p, q in zip(empty, empty[1:] + [None]):
            if q != p + 1: runs.append((s, p)); s = q
        s, e = max(runs, key=lambda r: r[1] - r[0]); cut = (s + e) // 2
    else: cut = w // 2
    return im.crop((0, 0, cut, h)), im.crop((cut, 0, w, h))


def convert(part, maxs, fixed=None):
    t, pal, cell = snapc.snap(part, accent=False, fixed=fixed)
    t = snapc.drop_small(t, 8); t = snapc.shrink2(t, maxs, maxs); t = snapc.drop_small(t, 3)
    return t, pal, cell


def main(src, did, grade):
    im = Image.open(src)
    keep = os.path.join(WEB, 'art', 'src', did + '_ai' + os.path.splitext(src)[1])
    if os.path.abspath(src) != keep: shutil.copy(src, keep)
    f, b = split(im)
    out = []; body = None
    for part, side, maxs in ((f, 'f', FRONT.get(grade, 56)), (b, 'b', 48)):
        t, pal, cell = convert(part, maxs, body)          # 롬은 앞·뒤가 팔레트 하나를 같이 쓰므로 뒷모습도 앞모습의 몸 색 두 개로
        body = [list(pal[1]), list(pal[2])]
        snapc.to_image(t, pal).save(os.path.join(WEB, 'art', '%s-%s.png' % (did, side)))
        out.append(snapc.to_image(t, pal, 4, (248, 248, 248)))
        print(side, '칸', tuple(round(x, 2) for x in cell), '→', t.shape[::-1], '색', pal[:4])
    W = sum(o.width for o in out) + 24; H = max(o.height for o in out)
    sheet = Image.new('RGB', (W, H), (248, 248, 248)); x = 0
    for o in out: sheet.paste(o, (x, H - o.height)); x += o.width + 24
    sheet.save(os.path.join(WEB, 'art', '_%s_sheet.png' % did))


if __name__ == '__main__':
    main(*sys.argv[1:4])
