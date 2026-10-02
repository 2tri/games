"""위키몬 LCD 도트 → 실루엣 밑그림 (Claude 가 grid 로 그리거나 재미나이 1번 참고 그림으로)
    python3 lcd2sketch.py tunomon            romhack/order/lcd.json 의 주소에서 받아서
    python3 lcd2sketch.py tunomon --src x.gif
결과 (art/sketch/, 저장소에 안 올림):
  <id>.png        실루엣 밑그림: 바깥 테두리 1칸 검정, 안쪽 밝은 회색, 배경 흰
  <id>_x8.png     같은 그림 ×8 (재미나이 첨부 1장)
  <id>.txt        밑그림 글자 격자 (grid.py 글자)
  <id>_lcd.txt    같은 크기로 키운 LCD 원본 선 (+ = LCD 검은 칸, 무늬 자리 참고용)
  --color: art/grid/<id>-f.txt·-b.txt  LCD 선을 그대로 두고 안쪽에 색(lcdcolor.json), Scale2x 로 2배, 뒷모습은 반전·얼굴 지움·아래 1/4 자름
  <id>_base.txt   4톤 초안: 선 → 검정, 안쪽 → 밝은 톤 (Claude 가 이걸 고쳐 그림. LCD 점묘는 검정으로 나오니 어두운 톤으로)
크기: 등급(specs)으로 목표 40·48·56. 정수배(유년기 ×2, 성장기·성숙기 이상 ×3, 24칸 LCD 는 ×2)가 넘치면
목표 크기에 맞게 가장 가까운 칸으로 키움 (보고에 적음)."""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(WEB, 'romhack', 'order'))
import grid, specs, snapc

COLOR = os.path.join(WEB, 'art', 'grid', 'lcdcolor.json')

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


def flood(t, x, y, v):
    """검은 선(3)으로 막힌 안쪽 칸 덩어리를 v 로 (4방향)"""
    h, w = t.shape; old = t[y, x]
    if old in (3, -1) or old == v: return
    st = [(y, x)]; t[y, x] = v
    while st:
        Y, X = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = Y + dy, X + dx
            if 0 <= yy < h and 0 <= xx < w and t[yy, xx] == old: t[yy, xx] = v; st.append((yy, xx))


def edge_of(t):
    b = t >= 0; p = np.pad(b, 1)
    return b & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])


def apply_ops(t, ops):
    """칠하기 (원래 칸 좌표). 톤: 0 흰 1 밝은 2 어두운 3 검정
      ["seed", x, y, 톤]             선으로 막힌 덩어리 채우기
      ["rows", y0, y1, 톤]           그 행들의 안쪽 칸(선 제외)
      ["box", x0, y0, x1, y1, 톤]    네모 안 안쪽 칸(선 제외)
      ["boxall", x0, y0, x1, y1, 톤] 네모 안 몸 칸 전부(선 포함, 바깥 테두리 제외) — 뒷모습 얼굴 지우기
      ["ink", 톤]                    바깥 테두리가 아닌 검은 칸 전부
      ["px", 톤, [[x, y], ...]]      칸 하나씩
      ["clear", y0, y1]              그 행들을 지움(바닥 그림자 등)
      ["map", x0, y0, x1, y1, 톤a, 톤b] 네모 안 톤a 를 톤b 로"""
    for op in ops:
        k = op[0]; edge = edge_of(t); body = t >= 0
        if k == 'seed': flood(t, op[1], op[2], op[3])
        elif k in ('rows', 'box', 'boxall'):
            m = np.zeros_like(body)
            if k == 'rows': m[op[1]:op[2] + 1] = True; v = op[3]
            else: m[op[2]:op[4] + 1, op[1]:op[3] + 1] = True; v = op[5]
            m &= body & ((~edge) if k == 'boxall' else (t != 3))
            t[m] = v
        elif k == 'ink': t[(t == 3) & ~edge] = op[1]
        elif k == 'clear': t[op[1]:op[2] + 1] = -1
        elif k == 'map':
            m = np.zeros_like(body); m[op[2]:op[4] + 1, op[1]:op[3] + 1] = True; t[m & (t == op[5])] = op[6]
        elif k == 'px':
            for x, y in op[2]: t[y, x] = op[1]
    return t


def paint(a, ops):
    """LCD 원래 칸 → 선 3, 안쪽 1, 바깥 -1 에 ops 칠하기"""
    body = silhouette(a)
    t = -np.ones(a.shape, int); t[body] = 1; t[a & body] = 3
    return apply_ops(t, ops)


def scale2x(t):
    """Scale2x(EPX): 2배로 키우며 계단 모서리를 대각선으로 다듬음"""
    h, w = t.shape; p = np.pad(t, 1, constant_values=-1); o = np.zeros((h * 2, w * 2), int)
    for y in range(h):
        for x in range(w):
            P = p[y + 1, x + 1]; A = p[y, x + 1]; B = p[y + 1, x + 2]; C = p[y + 1, x]; D = p[y + 2, x + 1]
            e = [P] * 4
            if C == A and C != D and A != B: e[0] = A
            if A == B and A != C and B != D: e[1] = B
            if D == C and D != B and C != A: e[2] = C
            if B == D and B != A and D != C: e[3] = D
            o[2 * y, 2 * x], o[2 * y, 2 * x + 1], o[2 * y + 1, 2 * x], o[2 * y + 1, 2 * x + 1] = e
    return o


def scale3x(t):
    """Scale3x(AdvMAME3x): 3배로 키우며 모서리 다듬음 (16칸 LCD 용)"""
    h, w = t.shape; p = np.pad(t, 1, constant_values=-1); o = np.zeros((h * 3, w * 3), int)
    for y in range(h):
        for x in range(w):
            A, B, C = p[y, x], p[y, x + 1], p[y, x + 2]; D, E, F = p[y + 1, x], p[y + 1, x + 1], p[y + 1, x + 2]
            G, H, I = p[y + 2, x], p[y + 2, x + 1], p[y + 2, x + 2]
            e = [E] * 9
            if D == B and B != F and D != H: e[0] = D
            if (D == B and B != F and D != H and E != C) or (B == F and B != D and F != H and E != A): e[1] = B
            if B == F and B != D and F != H: e[2] = F
            if (D == B and B != F and D != H and E != G) or (D == H and D != B and H != F and E != A): e[3] = D
            if (B == F and B != D and F != H and E != I) or (H == F and D != H and B != F and E != C): e[5] = F
            if D == H and D != B and H != F: e[6] = D
            if (D == H and D != B and H != F and E != I) or (H == F and D != H and B != F and E != G): e[7] = H
            if H == F and D != H and B != F: e[8] = F
            o[3 * y:3 * y + 3, 3 * x:3 * x + 3] = np.array(e).reshape(3, 3)
    return o


def upscale(t, k):
    """k = 2(Scale2x) · 3(Scale3x) · 1.5(Scale3x 뒤 한 칸 걸러 뽑기, 큰 LCD 가 56 칸을 넘을 때)"""
    if k == 3: return scale3x(t)
    if k == 1.5: return scale3x(t)[1::2, 1::2]
    return scale2x(t)


def finish(t, shade=0, shade_on=(1,), ring=True, tone=2):
    """키운 뒤: 바깥에 닿은 색 칸에 검은 테두리 1칸, 오른쪽 아래 그늘 띠"""
    b = t >= 0; h, w = t.shape
    if shade:
        out = t.copy()
        for y in range(h):
            for x in range(w):
                if t[y, x] in shade_on:
                    for dx, dy in [(k, k) for k in range(1, shade + 1)] + [(k, 0) for k in range(1, shade + 1)] + [(0, k) for k in range(1, shade + 1)]:
                        X, Y = x + dx, y + dy
                        if not (0 <= X < w and 0 <= Y < h) or not b[Y, X]:
                            out[y, x] = tone; break
        t = out
    if ring:
        p = np.pad(b, 1); e = b & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]); t[e] = 3
    return t


def colored(a, cfg, side):
    """front: LCD 에 front.ops. back: 앞을 칠한 것을 좌우 반전 → back.ops(얼굴 지우기 등) → 아래 1/4 자름"""
    t = paint(a, cfg.get('front', {}).get('ops', []))
    c = cfg.get(side, {})
    if side == 'back': t = apply_ops(t[:, ::-1].copy(), c.get('ops', []))
    big = finish(upscale(t, cfg.get('scale', 2)), c.get('shade', cfg.get('shade', 0)), tuple(c.get('shade_on', cfg.get('shade_on', [1]))),
                 tone=cfg.get('shade_tone', 2))
    if side == 'back':
        ys = np.where((big >= 0).any(1))[0]; hh = ys.max() - ys.min() + 1
        big = big[:ys.max() + 1 - hh // 4]
    return grid.crop(big)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('id'); ap.add_argument('--src'); ap.add_argument('--grade')
    ap.add_argument('--color', action='store_true', help='art/grid/lcdcolor.json 대로 LCD 에 색을 입혀 앞·뒤 완성본 txt (art/grid/<id>-f.txt·-b.txt)')
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
    if a.color:
        cfg = json.load(open(COLOR, encoding='utf-8'))[a.id]
        for side, tag in (('front', 'f'), ('back', 'b')):
            t = colored(a0, cfg, side)
            open(os.path.join(WEB, 'art', 'grid', '%s-%s.txt' % (a.id, tag)), 'w', encoding='utf-8').write(grid.arr2txt(t))
            print('  %s %s %dx%d' % (a.id, tag, t.shape[1], t.shape[0]))
    b = base(a0, T)
    open(os.path.join(OUT, a.id + '_base.txt'), 'w', encoding='utf-8').write(grid.arr2txt(b))
    print('%s %s: LCD %dx%d (gif %d배) → %s → %dx%d, 목표 %d' % (a.id, grade, a0.shape[1], a0.shape[0], k0, how, t.shape[1], t.shape[0], T))


if __name__ == '__main__':
    main()
