"""나리 걷기 시트(96x128, 32x32칸) 옆모습(왼쪽 3행 · 오른쪽 4행) 머리를 손으로 그린 도트 머리로 바꿈 (10/19 v1.1).
원인: chibi_walk.py 가 원본 옆얼굴의 1칸 코를 1.3배로 키우며 2~3칸 「피노키오 코」가 됨. 태일 옆모습처럼 얼굴을 앞머리 밑에 넣고 앞쪽을 평평하게.
사용: python fix_side_head.py <입력 시트.png> <출력 시트.png>"""
import sys
from PIL import Image, ImageOps

HEAD = """
.....OOOOOO.....
...OOHHhhHHOO...
..OHHhhhhhHHHO..
.OHhhHHHHHHHHHO.
.OHHHHHHHHHPPHO.
OHHHHHHHHHHPpHHO
OHHHHHHHHHHHHHHO
OHHHHDHHHHHHHHHO
OSSSSDHHHHHHHHHO
OSSSSSDHHHHHHHHO
OSEESSSDHHHHHHHO
OSEWSSSSDHHHHHHO
OSSSSSSSsDHHHHO.
.OSSSSSssOOHHO..
..OOOOOOO..OO...
"""
COL = {'O': (40, 32, 40), 'H': (92, 53, 20), 'h': (145, 93, 53), 'D': (55, 29, 10), 'S': (238, 183, 141), 's': (196, 140, 100),
       'E': (20, 8, 4), 'W': (255, 250, 245), 'P': (230, 110, 165), 'p': (170, 52, 110)}

def head_img(clip=True):
    rows = [r for r in HEAD.strip('\n').split('\n')]
    if not clip: rows = [r.replace('P', 'H').replace('p', 'H') for r in rows]     # 핀은 왼쪽 머리에만(앞모습 기준) → 오른쪽을 볼 때는 안 보임
    w, h = max(len(r) for r in rows), len(rows)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); p = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in COL: p[x, y] = COL[c] + (255,)
    return im

def main():
    sheet = Image.open(sys.argv[1]).convert('RGBA'); H = head_img(); H2 = head_img(False); hw, hh = H.size
    for row, mirror in ((2, False), (3, True)):
        for col in range(3):
            fx, fy = col * 32, row * 32
            f = sheet.crop((fx, fy, fx + 32, fy + 32)); p = f.load()
            top = min(y for y in range(32) if any(p[x, y][3] for x in range(32)))
            # 목(옷깃) 줄: 위에서부터 분홍(옷) 점이 처음 나오는 줄
            collar = next(y for y in range(top + 8, 32) if any(p[x, y][3] and p[x, y][0] > 150 and p[x, y][1] < 140 and p[x, y][2] > 100 for x in range(32)))
            body = [x for x in range(32) if p[x, collar + 1][3]]
            a, b = min(body), max(body)
            # 옛 머리 지움(옷깃 줄 위 전부 + 옷깃 줄에서 몸통 폭 밖)
            for y in range(0, collar):
                for x in range(32): p[x, y] = (0, 0, 0, 0)
            for x in range(32):
                if x < a - 1 or x > b + 1: p[x, collar] = (0, 0, 0, 0)
            hd = ImageOps.mirror(H2) if mirror else H
            x0 = (b + 2 - (hw - 1)) if mirror else (a - 2)
            y0 = collar - hh
            f.alpha_composite(hd, (x0, y0))
            sheet.paste(f, (fx, fy))
    sheet.save(sys.argv[2])
    print('저장:', sys.argv[2])

if __name__ == '__main__':
    main()
