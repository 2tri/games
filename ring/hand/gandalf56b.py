"""간달프 56×56 — 사진 자세를 보고 칸 위에 재질 구역을 직접 따라 그림(트레이싱),
명암·선은 규칙으로. 재질: H 모자 B 챙 S 피부 W 수염·머리 C 망토 R 긴옷 L 허리띠 K 칼집 G 칼자루 T 지팡이"""
import numpy as np
N = 56
mat = np.full((N, N), '.', dtype='<U1')
def span(y, x0, x1, m):
    mat[y, max(0, x0):min(N, x1 + 1)] = m
# ── 모자 (끝이 오른쪽으로 살짝 꺾임) ──
for y, (a, b) in enumerate([(30, 31), (29, 31), (28, 31), (27, 32), (26, 32), (25, 33), (24, 34)]): span(y, a, b, 'H')
span(7, 17, 39, 'B'); span(8, 13, 43, 'B'); span(9, 12, 17, 'B'); span(9, 39, 44, 'B')
# ── 얼굴·머리 ──
for y in range(9, 15):
    span(y, 18 - (y > 11), 21, 'W'); span(y, 22, 33, 'S'); span(y, 34, 37 + (y > 11), 'W')
span(14, 22, 33, 'W'); span(14, 22, 23, 'S'); span(14, 32, 33, 'S')
# ── 몸: 망토(뒤) → 소매 → 긴 옷 → 수염 ──
cloak = {15: (12, 43), 16: (9, 46), 17: (7, 48)}
for y in range(18, 55): cloak[y] = (int(7 - (y - 18) * 0.12), int(48 + (y - 18) * 0.12))
for y, (a, b) in cloak.items(): span(y, a, b, 'C')
for y in range(16, 31):                                   # 넓은 소매 (팔을 벌림)
    w = 4 + (y - 16) * 0.55
    span(y, int(11 - (y - 16) * 0.55), int(11 - (y - 16) * 0.55 + w + 3), 'A')
    span(y, int(44 + (y - 16) * 0.55 - w - 3), int(44 + (y - 16) * 0.55), 'A')
for y in range(19, 54): span(y, 18 + (y > 40), 37 - (y > 40), 'R')     # 앞섶 긴 옷
for y, (a, b) in {15: (15, 40), 16: (16, 39), 17: (16, 39), 18: (16, 39), 19: (16, 39), 20: (16, 39), 21: (17, 38), 22: (17, 38),
                  23: (18, 37), 24: (19, 36), 25: (20, 35), 26: (21, 34), 27: (23, 32), 28: (25, 30)}.items(): span(y, a, b, 'W')
span(33, 18, 37, 'L'); span(34, 18, 37, 'L')
# ── 칼 (허리 오른쪽에서 비스듬히) ──
for i in range(20):
    x = 38 + round(i * 0.45); span(35 + i, x, x + 2, 'K')
span(32, 36, 42, 'G'); span(31, 38, 39, 'G'); span(33, 38, 39, 'G')
# ── 손 ──
for y, (a, b) in {30: (8, 12), 31: (7, 12), 32: (8, 12), 33: (9, 11)}.items(): span(y, a, b, 'S')
for y, (a, b) in {30: (43, 47), 31: (43, 48), 32: (43, 47), 33: (44, 46)}.items(): span(y, a, b, 'S')
# ── 지팡이 (화면 왼쪽 손) ──
staff = [(y, 9, 10) for y in range(4, 55) if not (30 <= y <= 33)]
for y, a, b in staff: span(y, a, b, 'T')
for y, (a, b) in {0: (8, 10), 1: (7, 11), 2: (7, 12), 3: (8, 11)}.items(): span(y, a, b, 'T')
# ── 발 ──
span(54, 21, 25, 'C'); span(54, 30, 34, 'C')

# ── 명암 규칙 (빛은 왼쪽 위) ──
t = -np.ones((N, N), int)
for y in range(N):
    for x in range(N):
        m = mat[y, x]
        if m == '.': continue
        if m == 'H': v = 2 if x >= 31 else 1
        elif m == 'B': v = 3 if (y == 9 or (y == 8 and (x < 15 or x > 41))) else 2
        elif m == 'S': v = 1 if (x >= 31 or y == 9) else 0
        elif m == 'W':
            v = 1 if (x >= 35 or (x + 2 * y) % 5 == 0 or (x * 3 + y) % 7 == 0) else 0
        elif m == 'C': v = 3 if ((y > 36 and x % 5 == 2) or x > 45 or (x > 41 and y > 36 and (x + y) % 2 == 0)) else 2
        elif m == 'A': v = 2 if (x > 40 or (y > 22 and (x % 4 == 1))) else 1
        elif m == 'R': v = 2 if (x >= 31 or (y > 36 and x % 6 == 3)) else 1
        elif m == 'L': v = 0 if 26 <= x <= 29 and y == 33 else 3
        elif m == 'K': v = 1 if x == 38 + round((y - 35) * 0.45) + 1 else 2
        elif m == 'G': v = 0
        elif m == 'T': v = 1 if x == 9 else 2
        t[y, x] = v
# 재질 경계선: 우선순위 낮은(뒤) 재질 쪽에 검정
PRI = {'C': 0, 'A': 1.5, 'R': 1, 'L': 2, 'K': 3, 'W': 4, 'T': 5, 'S': 6, 'B': 7, 'H': 8, 'G': 9}
t2 = t.copy()
for y in range(N):
    for x in range(N):
        m = mat[y, x]
        if m == '.': continue
        for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= Y < N and 0 <= X < N and mat[Y, X] != '.' and mat[Y, X] != m and PRI[mat[Y, X]] > PRI[m]:
                t2[y, x] = 3; break
t = t2
# 실루엣 외곽선
o = t.copy()
for y in range(N):
    for x in range(N):
        if t[y, x] < 0 and any(0 <= y + dy < N and 0 <= x + dx < N and t[y + dy, x + dx] >= 0 for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y, x] = 3
t = o
# 얼굴 (손으로 찍기)
for (x, y, v) in [(25, 11, 3), (25, 12, 3), (30, 11, 3), (30, 12, 3), (24, 10, 1), (25, 10, 1), (26, 10, 1), (29, 10, 1), (30, 10, 1), (31, 10, 1),
                  (27, 13, 1), (28, 13, 2), (26, 12, 0), (31, 12, 1)]:
    t[y, x] = v
np.save('/home/user/games/ring/hand/gandalf56b.npy', t)
