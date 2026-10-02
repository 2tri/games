"""위키몬 LCD 도트 → 실루엣 밑그림 (Claude 가 grid 로 그리거나 재미나이 1번 참고 그림으로)
    python3 lcd2sketch.py tunomon            romhack/order/lcd.json 의 주소에서 받아서
    python3 lcd2sketch.py tunomon --src x.gif
결과 (art/sketch/, 저장소에 안 올림):
  <id>.png        실루엣 밑그림: 바깥 테두리 1칸 검정, 안쪽 밝은 회색, 배경 흰
  <id>_x8.png     같은 그림 ×8 (재미나이 첨부 1장)
  <id>.txt        밑그림 글자 격자 (grid.py 글자)
  <id>_lcd.txt    같은 크기로 키운 LCD 원본 선 (+ = LCD 검은 칸, 무늬 자리 참고용)
  <id>_base.txt   4톤 초안: 선 → 검정, 안쪽 → 밝은 톤 (Claude 가 이걸 고쳐 그림. LCD 점묘는 검정으로 나오니 어두운 톤으로)
크기: 등급(specs)으로 목표 40·48·56. 정수배(유년기 ×2, 성장기·성숙기 이상 ×3, 24칸 LCD 는 ×2)가 넘치면
목표 크기에 맞게 가장 가까운 칸으로 키움 (보고에 적음)."""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(WEB, 'romhack', 'order'))
import grid, specs, snapc

OUT = os.path.join(WEB, 'art', 'sketch')
TARGET = {'유아기Ⅰ': 40, '유아기Ⅱ': 40, '유년기Ⅰ': 40, '유년기Ⅱ': 40, '유년기': 40, '성장기': 48}
MUL = {40: 2, 48: 3, 56: 3}


def native(path):
    """LCD gif → 원래 칸 (True = 검은 칸). 위키몬 gif 는 2배로 키워져 있으니 가장 짧은 줄 길이로 되돌림"""
    a = np.asarray(Image.open(path).convert('L')) < 128
    runs = []
    for m in (a, a.T):
        for r in m:
            d = np.diff(np.r_[0, r.astype(int), 0]); s = np.where(d == 1)[0]; e = np.where(d == -1)[0]
            runs += list(e - s)
    k = min(runs) if runs else 1
    a = a[::k, ::k]
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], k


def scale(a, T, grade):
    n = max(a.shape); k = 2 if n > 16 else MUL[T]
    if n * k <= T: return np.kron(a, np.ones((k, k), bool)), '×%d' % k
    h, w = a.shape; f = T / n
    H, W = max(1, round(h * f)), max(1, round(w * f))
    yi = np.minimum((np.arange(H) / f).astype(int), h - 1); xi = np.minimum((np.arange(W) / f).astype(int), w - 1)
    return a[yi][:, xi], '×%.2f (정수배 %d×%d=%d 가 %d 를 넘음)' % (f, n, k, n * k, T)


def silhouette(a):
    """바깥에서 흰 칸을 따라 채운 곳 = 배경. 나머지(선·안쪽·점묘) = 몸"""
    h, w = a.shape; p = np.pad(a, 1); bg = np.zeros_like(p); st = [(0, 0)]; bg[0, 0] = True
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            Y, X = y + dy, x + dx
            if 0 <= Y < h + 2 and 0 <= X < w + 2 and not bg[Y, X] and not p[Y, X]:
                bg[Y, X] = True; st.append((Y, X))
    return ~bg[1:-1, 1:-1]


def tones(a):
    """LCD 원래 칸 → 4톤 초안: 바깥 -1, 검은 칸 3, 안쪽 흰 칸 1. LCD 점묘(회색 표현)도 검정으로 나오니 Claude 가 어두운 톤으로 고침"""
    body = silhouette(a)
    t = -np.ones(a.shape, int); t[body] = 1; t[a & body] = 3
    return t


def base(a, T):
    """4톤 초안을 목표 크기로: ×4 로 키운 뒤 snapc.shrink2 (바깥 테두리 1칸 다시 그림)"""
    t = tones(a); big = np.kron(t, np.ones((4, 4), int))
    n = max(a.shape); k = 2 if n > 16 else MUL[T]
    m = min(T, n * k)
    return snapc.shrink2(big, m, m, 0.30)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('id'); ap.add_argument('--src'); ap.add_argument('--grade')
    a = ap.parse_args()
    sp = specs.by_id(a.id) or {}
    grade = a.grade or sp.get('grade') or '성숙기'; T = TARGET.get(grade, 56)
    os.makedirs(OUT, exist_ok=True)
    src = a.src
    if not src:
        lcd = json.load(open(os.path.join(WEB, 'romhack', 'order', 'lcd.json')))
        key = sp.get('wiki') or a.id
        if key not in lcd: raise SystemExit('lcd.json 에 %s 없음 → --src 로 알려 주거나 C 방식(밑그림 없이)' % key)
        src = os.path.join(OUT, a.id + '_lcd.gif')
        if not os.path.exists(src): subprocess.run(['curl', '-sS', '-o', src, lcd[key]['url']], check=True)
    a0, k0 = native(src)
    big, how = scale(a0, T, grade)
    body = silhouette(big)
    # 바깥 테두리 1칸: 몸 칸 중 상하좌우에 배경이 있는 칸
    p = np.pad(body, 1)
    edge = body & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    t = -np.ones(body.shape, int); t[body] = 1; t[edge] = 3
    d = -np.ones(body.shape, int); d[body] = 1; d[big] = 2; d[edge] = 3
    grid.arr2img(t, grid.GRAY, 1, grid.GRAY[0]).save(os.path.join(OUT, a.id + '.png'))
    grid.arr2img(t, grid.GRAY, 8, grid.GRAY[0]).save(os.path.join(OUT, a.id + '_x8.png'))
    open(os.path.join(OUT, a.id + '.txt'), 'w', encoding='utf-8').write(grid.arr2txt(t))
    open(os.path.join(OUT, a.id + '_lcd.txt'), 'w', encoding='utf-8').write(grid.arr2txt(d))
    b = base(a0, T)
    open(os.path.join(OUT, a.id + '_base.txt'), 'w', encoding='utf-8').write(grid.arr2txt(b))
    print('%s %s: LCD %dx%d (gif %d배) → %s → %dx%d, 목표 %d' % (a.id, grade, a0.shape[1], a0.shape[0], k0, how, t.shape[1], t.shape[0], T))


if __name__ == '__main__':
    main()
