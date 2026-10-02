"""제목 화면 로고 「디지몬스터」 (사용자 지시 2026-10-02: 「제목은 형태는 좋으니까 한글로 디지몬스터라고」)
1.4 로고(デジモンアドベンチャー)와 같은 꾸밈: 주황 판 + 검은 외곽선 + 검은 글자. 글꼴 Black Han Sans (OFL, Google Fonts)
  python3 title_logo.py [글꼴.ttf]  → ../art/title/logo.png (화면 160×48 중 로고 칸, 색 0 하늘·1 주황·3 검정)
로고 칸(배경 타일 0x00~0x7E 중 로고 자리): 0~4줄 1~16칸 (0줄 9칸은 빈 타일 0x08 이라 못 씀), 2~4줄 17~18칸, 5줄 1~15칸"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
OUT = os.path.join(WEB, 'art', 'title', 'logo.png')
SKY, ORANGE, BLACK = (120, 160, 248), (248, 152, 80), (0, 0, 0)


def drawable():
    m = np.zeros((6, 20), bool)
    m[0:5, 1:17] = True; m[0, 9] = False; m[5, 1:16] = True          # 2~4줄 17~18칸은 팔레트가 달라 비움
    return m


def dilate(a, r):
    out = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r: out |= np.roll(np.roll(a, dy, 0), dx, 1)
    return out


def make(font_path, text='디지몬스터', H=22, top=100, bottom=128, cx=72, y0=13):      # 17~18칸은 팔레트가 달라(올리브) 안 씀
    """글자를 높이 H 로 그리고, 위는 top·아래는 bottom 폭이 되게 사다리꼴로 늘림 (원래 로고처럼 아래가 넓음)"""
    K = 4                                                         # 4배로 그려 사다리꼴로 늘린 뒤 줄임 (계단 줄이기)
    for size in range(240, 40, -2):
        f = ImageFont.truetype(font_path, size)
        im = Image.new('L', (2400, 600), 0); ImageDraw.Draw(im).text((20, 20), text, font=f, fill=255)
        a = np.array(im) > 110
        ys, xs = np.nonzero(a)
        if ys.max() - ys.min() + 1 <= H * K: break
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; h, w = a.shape
    big = np.zeros((48 * K, 160 * K), np.float32); oy = (y0 + (H - h / K) / 2) * K
    for y in range(h):
        tw = (top + (bottom - top) * y / max(1, h - 1) - 10) * K       # 판 두께만큼 줄임
        x0 = cx * K - tw / 2
        X = np.arange(int(x0), int(x0 + tw) + 1); sx = ((X - x0) / tw * (w - 1) + 0.5).astype(int)
        ok = (sx >= 0) & (sx < w); big[int(oy) + y, X[ok]] = a[y, sx[ok]]
    can = big.reshape(48, K, 160, K).mean((1, 3)) >= 0.5
    plate = dilate(can, 3); edge = dilate(plate, 1) & ~plate
    img = np.zeros((48, 160), np.uint8)      # 0 하늘
    img[plate] = 1; img[can] = 3; img[edge] = 3
    shadow = np.roll(plate | edge, 1, 0) & ~(plate | edge); shadow[40:] = False; img[shadow] = 3      # 판 아래 그림자 한 줄 (5줄은 안 씀)
    return img


def check(img):
    m = drawable(); bad = []
    for r in range(6):
        for c in range(20):
            if not m[r, c] and img[r * 8:r * 8 + 8, c * 8:c * 8 + 8].any(): bad.append((r, c))
    return bad


if __name__ == '__main__':
    font = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('FONTS', '.'), 'BlackHanSans-Regular.ttf')
    img = make(font)
    bad = check(img)
    pal = np.array([SKY, ORANGE, (255, 255, 255), BLACK], np.uint8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    Image.fromarray(pal[img]).save(OUT)
    Image.fromarray(pal[img]).resize((640, 192), Image.NEAREST).save(os.path.join(WEB, 'art', 'title', '_logo_x4.png'))
    print('로고 →', OUT, '못 쓰는 칸에 걸침:', bad)
