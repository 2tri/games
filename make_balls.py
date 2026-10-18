#!/usr/bin/env python3
"""디지볼 색 바꾸기 (2026-10-14) — 사용자가 만든 디지볼 그림 하나로 4종(디지볼·슈퍼·하이퍼·마스터)을 만든다.
사용:   python make_balls.py "<digiball_ai.png>" [--out <폴더>]
- 원본의 「위쪽 주황 계열」 색만 골라 색상을 돌린다(흰색·검은 테두리·창은 그대로).
  슈퍼 = 파랑, 하이퍼 = 노랑·검정 느낌(노랑), 마스터 = 보라. 결과: digiball.png, superdigiball.png, hyperdigiball.png, masterdigiball.png
- 64x64 이상이면 그대로 두고, 넣는 도구가 크기를 맞춘다."""
import os, sys, colorsys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_nds

HUES = {'digiball': None, 'superdigiball': 0.60, 'hyperdigiball': 0.15, 'masterdigiball': 0.78}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--out', default='balls_out'); A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    w, h, img = art_nds.png_read(A.src)
    from PIL import Image
    for name, hue in HUES.items():
        im = Image.new('RGBA', (w, h)); px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = img[y][x] if len(img[y][x]) == 4 else img[y][x] + (255,)
                if hue is not None and a:
                    hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                    if ss > 0.35 and 0.0 <= hh <= 0.14 and 0.2 < ll < 0.85:        # 주황·빨강 부분만
                        r2, g2, b2 = colorsys.hls_to_rgb(hue, ll, ss); r, g, b = int(r2 * 255), int(g2 * 255), int(b2 * 255)
                px[x, y] = (r, g, b, a)
        im.save(os.path.join(A.out, name + '.png'))
    print('→', A.out, list(HUES))

if __name__ == '__main__':
    main()
