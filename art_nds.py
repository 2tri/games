#!/usr/bin/env python3
"""디지몬 그림 → 하트골드(NDS)용 그림 한 벌 만들기. 롬에는 아직 넣지 않는다(넣기는 HG 다음 단계).
   python art_nds.py <그림폴더> [--out nds_art] [--only 아구몬,파피몬]
   python art_nds.py <그림폴더> --survey --out gbc_survey     GBC 때 받은 앞·뒤 중 그대로 쓸 만한 것 고르기
   **Pillow 필요**: 제미나이가 주는 그림은 이름이 .png 여도 속은 jpg 다 → python -m pip install pillow

그림폴더에서 종마다 찾는 파일 (이름은 한글 이름 또는 GBC 때 영문 id 둘 다 됨):
  앞모습   agumon-ds-f.png (DS 배틀 그림, 있으면 먼저) → 없으면 agumon-f.png (GBC 4색) 또는 아구몬_앞.png
  뒷모습   agumon-ds-b.png → 없으면 agumon-b.png 또는 아구몬_뒤.png
  걷기     아구몬_걷기.png                          (제미나이 걷기 그림. 없으면 앞·뒷모습으로 자동)
만드는 것 (out/<번호>_<이름>/):
  front.png 80x80 · back.png 80x80   전투 그림, 16색(0번 = 투명)
  icon.png  32x64                     파티 아이콘 2프레임(위·아래), 앞모습에서 자동
  ow.png    칸 2개 x 4줄               따라다니기 그림: 줄 = 아래·위·왼쪽·오른쪽, 칸 = 걷기 2프레임 (유년기는 안 만듦 — 공용_알_걷기.png 를 씀, 유아기는 게임에서 뺌)
                                       칸 크기 32(모든 단계, 디지골드와 같게). 키는 OW_PX(성장기 20 ~ 궁극체 28)
  out/미리보기_01.png …                20종씩 한 쪽 (종마다 한 줄: 번호·앞·뒤·아이콘·걷기 아래·위·왼·오)
  out/보고.txt                         종마다 무엇으로 만들었는지(자동/제미나이), 빠진 그림"""
import os, sys, struct, zlib, json, argparse, collections, math, colorsys
try: sys.stdout.reconfigure(errors='replace')
except Exception: pass

try:
    from PIL import Image
except ImportError:
    Image = None

# ============================================================ PNG 읽기·쓰기 (Pillow 없을 때)
def png_read(path):
    """→ (w, h, [[(r,g,b,a)]])"""
    if Image is not None:
        im = Image.open(path).convert('RGBA'); w, h = im.size; px = list(im.getdata())
        return w, h, [px[y * w:(y + 1) * w] for y in range(h)]
    d = open(path, 'rb').read()
    if d[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('속이 png 가 아님(제미나이 그림은 jpg) → python -m pip install pillow 뒤 다시: ' + path)
    p = 8; idat = b''; plte = None; trns = None
    while p < len(d):
        ln, = struct.unpack('>I', d[p:p + 4]); t = d[p + 4:p + 8]; c = d[p + 8:p + 8 + ln]; p += 12 + ln
        if t == b'IHDR': w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', c)
        elif t == b'PLTE': plte = [tuple(c[i:i + 3]) for i in range(0, len(c), 3)]
        elif t == b'tRNS': trns = c
        elif t == b'IDAT': idat += c
    if il: raise ValueError('인터레이스 png 는 못 읽음: ' + path)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bpp = max(1, ch * bd // 8); stride = (w * ch * bd + 7) // 8
    raw = zlib.decompress(idat); rows = []; prev = bytearray(stride); q = 0
    for y in range(h):
        f = raw[q]; line = bytearray(raw[q + 1:q + 1 + stride]); q += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c2 = prev[i - bpp] if i >= bpp else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                pp = a + b - c2; pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c2)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c2)) & 255
        rows.append(bytes(line)); prev = line
    out = []
    for line in rows:
        if bd < 8:
            vals = []
            for byte in line:
                for k in range(8 // bd): vals.append((byte >> (8 - bd * (k + 1))) & ((1 << bd) - 1))
            vals = vals[:w * ch]
        elif bd == 16: vals = [line[i] for i in range(0, len(line), 2)]
        else: vals = list(line)
        r = []
        for x in range(w):
            if ct == 3:
                i = vals[x]; col = plte[i]; a = trns[i] if trns and i < len(trns) else 255; r.append(col + (a,))
            elif ct == 0:
                g = vals[x] * (255 // ((1 << bd) - 1)) if bd < 8 else vals[x]; r.append((g, g, g, 255))
            elif ct == 4: g, a = vals[x * 2:x * 2 + 2]; r.append((g, g, g, a))
            elif ct == 2: r.append(tuple(vals[x * 3:x * 3 + 3]) + (255,))
            else: r.append(tuple(vals[x * 4:x * 4 + 4]))
        out.append(r)
    return w, h, out

def png_write(path, rows, pal, transparent0=True):
    """rows = 색 번호 행 목록, pal = [(r,g,b)] (0번은 투명)"""
    h = len(rows); w = len(rows[0])
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    pal = list(pal) + [(0, 0, 0)] * (16 - len(pal)) if len(pal) < 16 else list(pal)
    data = b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0)) + ch(b'PLTE', bytes(c for col in pal for c in col))
    if transparent0: data += ch(b'tRNS', b'\x00')
    open(path, 'wb').write(data + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))

# ============================================================ 그림 다루기 (RGBA 행 목록, a=0 이면 투명)
T = (0, 0, 0, 0)

def remove_bg(img):
    """테두리와 이어진 배경색을 투명으로. 이미 투명한 그림이면 그대로"""
    h, w = len(img), len(img[0])
    if sum(1 for r in img for p in r if p[3] < 128) > w * h * 0.05:
        return [[p if p[3] >= 128 else T for p in r] for r in img]
    seeds = [img[0][0], img[0][w - 1], img[h - 1][0], img[h - 1][w - 1]]
    bg = collections.Counter(s[:3] for s in seeds).most_common(1)[0][0]
    checker = min(bg) >= 185 and max(bg) - min(bg) <= 28            # 10/16 집 보고(에렉몬): 밝은 회색 체크무늬 — 두 가지 회색·흰색을 다 배경으로
    def near(p):
        if checker and min(p[:3]) >= 185 and max(p[:3]) - min(p[:3]) <= 28: return True
        return sum((a - b) ** 2 for a, b in zip(p[:3], bg)) < 45 ** 2
    out = [list(r) for r in img]; seen = [[False] * w for _ in range(h)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if seen[y][x]: continue
        seen[y][x] = True
        if not near(img[y][x]): continue
        out[y][x] = T
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]: stack.append((nx, ny))
    if True:                                            # 몸 사이에 갇힌 배경(흰 잔사): 배경색과 거의 같은 덩어리 중 큰 것만(눈·반짝임처럼 작은 흰 점은 남김)
        # 10/16: 정한 종(HOLE_SPECIES)은 지우고, 나머지 종은 「흰 잔사 의심」으로 세기만 함(보고 → 눈으로 보고 HOLE_SPECIES 에 더함)
        lim = max(24, w * h // 2000); seen2 = [[False] * w for _ in range(h)]
        for y0 in range(h):
            for x0 in range(w):
                if seen2[y0][x0] or out[y0][x0][3] == 0 or not near(out[y0][x0]): continue
                comp = []; st = [(x0, y0)]; seen2[y0][x0] = True
                while st:
                    x, y = st.pop(); comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen2[ny][nx] and out[ny][nx][3] and near(out[ny][nx]): seen2[ny][nx] = True; st.append((nx, ny))
                if len(comp) >= lim:
                    HOLE_COUNT[0] += 1
                    if HOLES[0]:
                        for x, y in comp: out[y][x] = T
    return out

HOLE_COUNT = [0]

HOLES = [False]
HOLE_SPECIES = {'츄몬'}     # 10/16 사용자: 츄몬 몸 사이 흰 잔사 — 이 종들만 갇힌 배경도 지움(가트몬처럼 흰 몸 종을 지우지 않게 종을 정해서)

def bbox(img):
    ys = [y for y, r in enumerate(img) if any(p[3] for p in r)]
    if not ys: return None
    xs = [x for x in range(len(img[0])) if any(img[y][x][3] for y in ys)]
    return xs[0], ys[0], xs[-1] + 1, ys[-1] + 1

def crop(img, b):
    x0, y0, x1, y1 = b
    return [r[x0:x1] for r in img[y0:y1]]

def scale_to(img, maxw, maxh):
    """도트 그림을 줄임: 칸마다 덮인 원래 칸의 가장 흔한 색(40% 이상 덮였을 때만). 이미 작으면 그대로"""
    h, w = len(img), len(img[0])
    f = max(w / maxw, h / maxh)
    if f <= 1: return img
    nw, nh = max(1, round(w / f)), max(1, round(h / f))
    out = []
    for y in range(nh):
        r = []
        y0, y1 = int(y * h / nh), max(int(y * h / nh) + 1, int((y + 1) * h / nh))
        for x in range(nw):
            x0, x1 = int(x * w / nw), max(int(x * w / nw) + 1, int((x + 1) * w / nw))
            cnt = collections.Counter(); tot = 0
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    tot += 1; p = img[yy][xx]
                    if p[3]: cnt[(p[0] // 8 * 8, p[1] // 8 * 8, p[2] // 8 * 8)] += 1
            op = sum(cnt.values())
            if op >= tot * 0.4:
                # 눈·반짝임처럼 주변과 밝기가 크게 다른 색은 적어도 살린다(줄일 때 사라지지 않게)
                avg = sum(sum(c) * n for c, n in cnt.items()) / (3 * op)
                best = max(cnt.items(), key=lambda cn: cn[1] * (2.5 if abs(sum(cn[0]) / 3 - avg) > 50 and cn[1] >= tot * 0.2 else 1))[0]
                r.append(best + (255,))
            else: r.append(T)
        out.append(r)
    return out

def native(img):
    """제미나이 「큰 도트」 그림 → 원래 도트 크기로 (칸 크기를 색 경계 간격에서 찾음). 못 찾으면 그대로"""
    h, w = len(img), len(img[0])
    if max(w, h) < 200: return img          # DS 원본 그림(위키몬, 최대 160쯤)은 이미 1도트 — 제미나이 그림(1024)만 큰 도트 찾기
    def diff(p, q):
        if (p[3] > 0) != (q[3] > 0): return True
        return p[3] and sum(abs(a - b) for a, b in zip(p[:3], q[:3])) > 60
    gaps = collections.Counter()
    for y in range(0, h, max(1, h // 60)):
        last = None
        for x in range(1, w):
            if diff(img[y][x - 1], img[y][x]):
                if last is not None and 3 <= x - last <= 64: gaps[x - last] += 1
                last = x
    for x in range(0, w, max(1, w // 60)):
        last = None
        for y in range(1, h):
            if diff(img[y - 1][x], img[y][x]):
                if last is not None and 3 <= y - last <= 64: gaps[y - last] += 1
                last = y
    if not gaps: return img
    # 가장 흔한 간격과 그 정수배를 함께 셈 → 가장 잘 맞는 칸 크기
    best = max(range(3, 41), key=lambda b: sum(n for g, n in gaps.items() if abs(g / b - round(g / b)) < 0.15 and round(g / b) >= 1) * (1 + b / 400))
    nw, nh = max(1, round(w / best)), max(1, round(h / best))
    sx, sy = w / nw, h / nh
    out = []
    for j in range(nh):
        r = []
        for i in range(nw):
            cnt = collections.Counter(); tot = 0
            for yy in (int((j + 0.3) * sy), int((j + 0.5) * sy), int((j + 0.7) * sy)):
                for xx in (int((i + 0.3) * sx), int((i + 0.5) * sx), int((i + 0.7) * sx)):
                    p = img[min(h - 1, yy)][min(w - 1, xx)]; tot += 1
                    if p[3]: cnt[(p[0] // 8 * 8, p[1] // 8 * 8, p[2] // 8 * 8)] += 1
            r.append(cnt.most_common(1)[0][0] + (255,) if sum(cnt.values()) * 2 > tot else T)
        out.append(r)
    return out

def enlarge(img, maxw, maxh):
    """원래 도트를 정수배로 키움(칸이 일정하게) — 판에 들어가는 만큼만"""
    h, w = len(img), len(img[0])
    k = max(1, min(maxw // w, maxh // h))
    if k == 1: return img
    return [[p for p in r for _ in range(k)] for r in img for _ in range(k)]

def grow_to(img, tgt):
    """가장 가까운 픽셀로 키움(키가 tgt 가 되게, 정수배가 아니어도)"""
    h, w = len(img), len(img[0]); f = tgt / max(h, w)
    if f <= 1: return img
    nh, nw = max(1, round(h * f)), max(1, round(w * f))
    return [[img[min(h - 1, int(y / f))][min(w - 1, int(x / f))] for x in range(nw)] for y in range(nh)]

def fit(img, maxw, maxh, target=None):
    """큰 도트 그림 → 원래 도트 → 크면 줄이고, 작으면 그대로(1배) 둠.
    10/12: 2배로 키우면 도트가 큼직해져 디지골드 그림(DS 원래 도트) 옆에서 거칠어 보임 → 30픽셀도 안 되는 아주 작은 그림만 2배
    10/16 사용자 「가지몬 크기 작음」: 단계 목표 키(target)의 70% 도 안 되면 목표 키의 85% 까지 키움"""
    n = native(img)
    if len(n[0]) <= maxw and len(n) <= maxh:
        if max(len(n), len(n[0])) < 30: return enlarge(n, maxw, maxh)
        if target and max(len(n), len(n[0])) < target * 0.7: return grow_to(n, min(maxw, maxh, int(target * 0.85)))
        return n
    return scale_to(n, maxw, maxh)

# 주문문의 단계별 목표 크기(앞모습 키, DS 도트) — 이보다 많이 작게 나오면 보고에 「다시 주문」 표시
PX_TARGET = {'유년기Ⅰ': 40, '유년기Ⅱ': 40, '유년기': 40, '성장기': 52, '성숙기': 64, '아머체': 64, '완전체': 72, '궁극체': 76}

def mirror(img): return [list(reversed(r)) for r in img]

def place(img, W, H, bottom=0, shift_up=0):
    """W x H 판의 가운데 아래에 붙임 (넘치면 잘림)"""
    out = [[T] * W for _ in range(H)]
    h, w = len(img), len(img[0])
    ox = (W - w) // 2; oy = H - bottom - h - shift_up
    for y in range(h):
        for x in range(w):
            X, Y = ox + x, oy + y
            if 0 <= X < W and 0 <= Y < H and img[y][x][3]: out[Y][X] = img[y][x]
    return out

def outline(img, col=(16, 16, 16, 255)):
    """투명 칸 중 그림에 붙은 칸을 검은 테두리로 (아이콘·작은 걷기 그림이 뭉개지지 않게)"""
    h, w = len(img), len(img[0]); out = [list(r) for r in img]
    for y in range(h):
        for x in range(w):
            if img[y][x][3]: continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and img[y + dy][x + dx][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = col
    return out

def quantize(imgs, n=15):
    """여러 그림이 한 팔레트를 같이 쓰도록 n 색으로 → (색 번호 그림들, 팔레트[0=투명])"""
    cols = collections.Counter(p[:3] for img in imgs for r in img for p in r if p[3])
    cols = collections.Counter({c: n ** 0.5 for c, n in cols.items()})   # 드문 색(눈 등)도 제 몫을 받게
    if len(cols) <= n: pal = list(cols)
    else:
        boxes = [list(cols.items())]
        while len(boxes) < n:
            boxes.sort(key=lambda b: -max(max(c[0][k] for c in b) - min(c[0][k] for c in b) for k in range(3)) * (len(b) > 1))
            b = boxes.pop(0)
            if len(b) < 2: boxes.append(b); break
            k = max(range(3), key=lambda k: max(c[0][k] for c in b) - min(c[0][k] for c in b))
            b.sort(key=lambda c: c[0][k])
            tot = sum(c[1] for c in b); acc = 0; cut = 1
            for i, c in enumerate(b):
                acc += c[1]
                if acc >= tot / 2: cut = max(1, min(len(b) - 1, i + 1)); break
            boxes += [b[:cut], b[cut:]]
        pal = []
        for b in boxes:
            t = sum(c[1] for c in b)
            pal.append(tuple(round(sum(c[0][k] * c[1] for c in b) / t) for k in range(3)))
    pal = [(0, 0, 0)] + pal                       # 0번 = 투명
    memo = {}
    def idx(c):
        if c not in memo: memo[c] = 1 + min(range(len(pal) - 1), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i + 1], c)))
        return memo[c]
    return [[[idx(p[:3]) if p[3] else 0 for p in r] for r in img] for img in imgs], pal

def components(img, min_px):
    """그림 속 떨어진 덩어리(8방향 연결) 상자 목록"""
    h, w = len(img), len(img[0]); seen = [[False] * w for _ in range(h)]; out = []
    for y in range(h):
        for x in range(w):
            if img[y][x][3] and not seen[y][x]:
                st = [(x, y)]; seen[y][x] = True; xs, ys = [x, x], [y, y]; n = 0
                while st:
                    a, b = st.pop(); n += 1
                    xs[0] = min(xs[0], a); xs[1] = max(xs[1], a); ys[0] = min(ys[0], b); ys[1] = max(ys[1], b)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            na, nb = a + dx, b + dy
                            if 0 <= na < w and 0 <= nb < h and not seen[nb][na] and img[nb][na][3]:
                                seen[nb][na] = True; st.append((na, nb))
                if n >= min_px: out.append((xs[0], ys[0], xs[1] + 1, ys[1] + 1, n))
    return out

def split_sheet(img):
    """제미나이 걷기 그림 → ([아래1, 아래2, 위1, 위2, 왼1, 왼2, 오1, 오2], 메모) 또는 (None, 이유)
    8칸(2칸 x 4줄) 또는 4칸(아래·위·왼·오 한 장씩)을 받는다. 4칸이면 걸음 2는 자동(아래·위는 좌우 뒤집기, 옆은 같은 그림).
    오른쪽 아래 구석의 제미나이 표시(반짝이)는 떨어져 있으면 버리고, 자세에 겹치면 메모로 알린다."""
    h, w = len(img), len(img[0])
    zone = (w * 0.78, h * 0.86)                       # 반짝이가 찍히는 오른쪽 아래 구석
    comps = components(img, max(20, w * h // 2000))
    big = max((c[4] for c in comps), default=0)
    comps = [c for c in comps if c[4] >= big * 0.15 and not (c[0] >= zone[0] and c[1] >= zone[1] and c[4] < big * 0.4)]
    merged = True
    while merged and len(comps) > 8:
        merged = False
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                a, b = comps[i], comps[j]
                gap = max(a[0] - b[2], b[0] - a[2], a[1] - b[3], b[1] - a[3])
                if gap < max(w, h) * 0.02:
                    comps[i] = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]); comps.pop(j); merged = True; break
            if merged: break
    memo = []
    if len(comps) == 8:
        comps.sort(key=lambda c: (c[1] + c[3]) / 2)
        rows = [sorted(comps[i * 2:i * 2 + 2], key=lambda c: c[0]) for i in range(4)]
        order = [c for r in rows for c in r]
        poses = [crop(img, c[:4]) for c in order]
    elif len(comps) == 4:
        comps.sort(key=lambda c: (c[1] + c[3]) / 2)
        cy = [(c[1] + c[3]) / 2 for c in comps]
        if cy[1] - cy[0] < (comps[0][3] - comps[0][1]) * 0.5:        # 2칸 x 2줄
            order = sorted(comps[:2], key=lambda c: c[0]) + sorted(comps[2:], key=lambda c: c[0])
        else:                                                          # 1칸 x 4줄
            order = comps
        d, u, l, r = [crop(img, c[:4]) for c in order]
        poses = [d, mirror(d), u, mirror(u), l, l, mirror(l), mirror(l)]   # 오른쪽 = 왼쪽 뒤집기(제미나이가 오른쪽에 눈을 둘 그리는 일이 잦음)
        memo.append('4칸 → 걸음 2 자동, 오른쪽 = 왼쪽 뒤집기')
    else:
        return None, '덩어리 %d개(8개 또는 4개여야 함)' % len(comps)
    last = order[-1]
    if last[2] > zone[0] and last[3] > zone[1]: memo.append('마지막 자세가 제미나이 표시 자리와 겹칠 수 있음 — 확인')
    return poses, ', '.join(memo) or 'OK'

def apply_fix(poses, rule):
    """rule 예: '6=5, 8=7r' → 6번 자리에 5번, 8번 자리에 7번 좌우 뒤집기 (번호 1~8: 아래1·아래2·위1·위2·왼1·왼2·오1·오2)"""
    src = list(poses); out = list(poses)
    for part in rule.replace(' ', '').split(','):
        if not part: continue
        dst, val = part.split('=')
        flip = val.endswith('r'); k = int(val.rstrip('r'))
        out[int(dst) - 1] = mirror(src[k - 1]) if flip else src[k - 1]
    return out

def load_fixes(folder):
    """그림폴더/ow_fix.txt — 한 줄에 한 종: 「botamon: 6=5, 8=7」 또는 「깜몬: 6=5」 (# 뒤는 메모)"""
    fx = {}
    p = os.path.join(folder, 'ow_fix.txt')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            line = line.split('#')[0].strip()
            if ':' in line:
                k, v = line.split(':', 1); fx[norm(k)] = v.strip(); fx[k.strip()] = v.strip()
    return fx

# ============================================================ 종 하나
GRADE_SMALL = ('유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '유년기', '성장기')
EXTRA_SPECIES = [('슈퍼스타몬', 'SuperStarmon', '완전체'), ('호우오몬', 'Hououmon', '궁극체'), ('헤라캅테몬', 'HerculesKabuterimon', '궁극체'), ('바이킹몬', 'Vikemon', '궁극체'),
                 ('하이안드몬', 'HiAndromon', '궁극체'), ('메탈티라몬', 'MetalTyrannomon', '완전체'), ('그란쿠와몬', 'GranKuwagamon', '궁극체'),
                 ('리리스몬', 'Lilithmon', '궁극체'), ('발키리몬', 'Valkyrimon', '궁극체'), ('데비타마몬', 'Devitamamon', '궁극체'), ('데드메라몬', 'Death Meramon', '완전체')]
# 걷기 그림 키(32칸 안, DS 도트) — 10/12 디지골드 스크린샷 기준: 파피몬(성장기) 약 18, 워그레이몬(궁극체) 약 27, 둘 다 32칸
OW_PX = {'성장기': 20, '성숙기': 24, '아머체': 24, '완전체': 26, '궁극체': 28}
# 10/15 사용자: 데리고 다니는 그림을 다른 종 것으로 빌림(새 종 그림이 작게 줄이면 뭉개질 때) — 종: (빌릴 종, 색 바꿈). 빌릴 종 그림이 없으면 자기 그림으로 자동
OW_BORROW = {'슈퍼스타몬': ('스타몬', 'gold')}

def recolor(img, mode):
    """gold: 은색(채도 낮은 회색, 원작 스타몬 몸)과 노랑~주황 계열을 금색으로. 검은 외곽선·흰 반짝임·다른 색(파란 장갑 등)은 그대로
    (10/15 사용자: 원작 스타몬은 은색 → 슈퍼스타몬은 금색)"""
    if not mode: return img
    out = []
    for r in img:
        row = []
        for p in r:
            if len(p) > 3 and p[3] == 0: row.append(p); continue
            h, s_, v = colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)
            if mode == 'gold' and 0.07 <= h <= 0.20 and s_ > 0.25:
                h, s_, v = 0.125, min(1, s_ * 1.2 + 0.05), min(1, v * 1.05)
            elif mode == 'gold' and s_ < 0.18 and 0.30 < v < 0.96:      # 은색 → 금색(밝기는 살림)
                h, s_, v = 0.125, 0.80, min(1, v * 1.02)
            q = colorsys.hsv_to_rgb(h, s_, v)
            row.append((round(q[0] * 255), round(q[1] * 255), round(q[2] * 255)) + tuple(p[3:]))
        out.append(row)
    return out

def norm(s): return ''.join(ch for ch in s.lower() if ch.isalnum())

# 그림 파일 이름(영문 id)이 design.json 영문 이름과 다른 종 (10/14 집 보고 + GBC 세션 답). 앞에 있는 것부터 찾는다
ALIAS = {'츄몬': ['chuumon', 'chuchumon'], '고릴라몬': ['gorillamon'], '크리사리몬': ['chrysalimon'], '백호몬': ['baihumon'], '주작몬': ['zhuqiaomon'],
         '현무몬': ['xuanwumon', 'ebonwumon'], '가트몬': ['gatomon', 'tailmon'], '슈카몬': ['sukamon', 'scumon'], '할세몬': ['halsemon', 'holsmon'],
         '페가수몬': ['pegasusmon', 'pegasmon'], '베놈묘티몬': ['venommyotismon', 'venomvamdemon'], '가지몬': ['gazimon'], '메라몬': ['meramon'],
         '다크퍼펫몬': ['warumonzaemon'], '퍼펫몬': ['monzaemon'], '에이프몬': ['apemon', 'hanumon'], '돌핀몬': ['dolphmon', 'rukamon'],
         '고래몬': ['whamon'], '펌프몬': ['pumpmon'], '스컬사탄몬': ['skullsatamon'], '에렉몬': ['elecmon'], '데드메라몬': ['deathmeramon'],
         '다크그레몬': ['metalgreymonvirus', 'darkgreymon', 'metalgreymonv'], '황제파이터': ['imperialdramonfightermode', 'imperialdramonfm', 'imperialdramonfighter'],
         '아트라캅테리몬': ['atlurkabuterimonred', 'megakabuterimon', 'megakabuterimonred', 'atlurkabuterimon'], '아르케니몬': ['arukenimon', 'arachnemon'],
         '아라크네몬': ['arukenimon', 'arachnemon'], '번개콩알몬': ['metalmamemon'], '하이안드몬': ['hiandromon'], '슈퍼스타몬': ['superstarmon']}
try:
    from wikimon_get import EN_X as _WK_X          # 위키몬 받기에서 쓴 영문 이름(그 이름으로 <id>-wk-f.png 를 저장함)
except Exception:
    _WK_X = {}

def keys_for(sp):
    ks = []
    for e in [sp.get('en') or '', _WK_X.get(sp['ko'], '')] + ALIAS.get(sp['ko'], []) + ALIAS.get(sp.get('rom', ''), []):
        k = norm(e)
        if k and k not in ks: ks.append(k)
    return ks

_GRAY = {}
def is_gray(path):
    """GBC 때 받은 회색 4톤 그림(제미나이 v3 등)은 NDS 에 못 씀 → 건너뛰고 다음 후보"""
    if path in _GRAY: return _GRAY[path]
    try:
        w, h, img = png_read(path); n = g = 0
        step = max(1, (w * h) // 20000)
        flat = [p for r in img for p in r][::step]
        for p in flat:
            if len(p) > 3 and p[3] < 128: continue
            if min(p[:3]) >= 236: continue                 # 10/15: 흰 배경은 세지 않음(은색 디지몬 + 흰 배경을 회색 그림으로 잘못 보던 위험)
            n += 1
            if max(p[:3]) - min(p[:3]) <= 14: g += 1
        _GRAY[path] = n > 0 and g >= n * 0.985
    except Exception:
        _GRAY[path] = False
    return _GRAY[path]

SKIPPED_GRAY = []
ALLOW_GRAY = [False]       # 10/15: 다른 그림이 하나도 없을 때만 회색 그림이라도 씀(포켓몬 그림이 남는 것보다 나음)
def find_file(folder_index, keys, suffixes):
    """suffixes 순서가 먼저(좋은 출처 먼저), 그다음 이름 후보 순. 회색 그림은 건너뜀(ALLOW_GRAY 면 씀)"""
    for s in suffixes:
        for k in keys:
            p = folder_index.get(k + s)
            if p:
                if is_gray(p) and not ALLOW_GRAY[0]: SKIPPED_GRAY.append(os.path.basename(p)); continue
                return p
    return None

def same_shape(a, b):
    """두 그림의 윤곽이 얼마나 겹치나(0~1). 뒷모습이 앞모습 윤곽을 그대로 베꼈는지 보는 데 씀"""
    na, nb = scale_to(native(a), 40, 40), scale_to(native(b), 40, 40)
    def mask(img):
        h, w = len(img), len(img[0]); m = set()
        for y in range(h):
            for x in range(w):
                if img[y][x][3]: m.add((round(x * 39 / max(1, w - 1)), round(y * 39 / max(1, h - 1))))
        return m
    A, B = mask(na), mask(nb)
    return len(A & B) / max(1, len(A | B))

def build_one(sp, files, out_dir):
    note = []
    HOLES[0] = sp['ko'] in HOLE_SPECIES
    if HOLES[0]: note.append('몸 사이에 갇힌 배경도 지움')
    def load(path):
        w, h, img = png_read(path); img = remove_bg(img); b = bbox(img)
        if not b: raise ValueError('그림이 비었음: ' + path)
        return crop(img, b)
    HOLE_COUNT[0] = 0
    front = load(files['f']) if files.get('f') else None
    if HOLE_COUNT[0] and not HOLES[0]: note.append('흰 잔사 의심 %d곳(몸 사이에 갇힌 배경색 덩어리 — 미리보기로 보고 맞으면 HOLE_SPECIES 에 더함)' % HOLE_COUNT[0])
    back = load(files['b']) if files.get('b') else None
    if front is None:
        return build_ow_only(sp, files, out_dir)
    if back is None: back = mirror(front); note.append('뒷모습 없음 → 앞모습 뒤집기')
    elif files.get('b') and '-wk-atk' in os.path.basename(files['b']).lower():
        back = mirror(back); note.append('뒷모습 = 위키몬 공격 자세 뒤집기(사용자 10/12: 역동적인 자세)')
    elif files.get('b') and 'ds' in os.path.basename(files['b']).lower():
        sim, simm = same_shape(front, back), same_shape(front, mirror(back))
        if sim > 0.8 and sim > simm:
            back = mirror(back); note.append('뒷모습이 앞 윤곽을 베낌(겹침 %.0f%%) → 좌우 뒤집어 씀' % (sim * 100))
    big = sp['grade'] not in GRADE_SMALL
    if files.get('f') and 'ds' in os.path.basename(files['f']).lower():
        hn = len(native(front)); tgt = PX_TARGET.get(sp['grade'], 64)
        if hn < tgt * 0.7: note.append('앞모습이 작게 나옴(원래 도트 %d줄, 목표 약 %d) — 「잘 안 나올 때」 6번 문장을 붙여 다시 주문 권장' % (hn, tgt))
    F = place(fit(front, 76, 76, PX_TARGET.get(sp['grade'])), 80, 80, bottom=2)
    B = place(fit(back, 80, 72, PX_TARGET.get(sp['grade'])), 80, 80, bottom=0)
    (Fi, Bi), bpal = quantize([F, B], 15)
    png_write(os.path.join(out_dir, 'front.png'), Fi, bpal); png_write(os.path.join(out_dir, 'back.png'), Bi, bpal)
    # 아이콘
    fr_n = native(front)
    ic = outline(place(scale_to(fr_n, 26, 24), 32, 32, bottom=3))
    ic2 = outline(place(scale_to(fr_n, 26, 24), 32, 32, bottom=4))
    (I1, I2), ipal = quantize([ic, ic2], 15)
    png_write(os.path.join(out_dir, 'icon.png'), I1 + I2, ipal)
    # 걷기 (유년기는 공용 알을 쓰므로 만들지 않음)
    if sp['grade'] in BABY:
        note.append('걷기 = 공용 알')
        E = [[0] * 32 for _ in range(32)]
        return (Fi, Bi, I1, E, E, E, E, bpal, ipal, bpal, 32), note
    cell = 32; fitpx = OW_PX.get(sp['grade'], 24)     # 10/12: 큰 디지몬도 32칸(디지골드와 같게)
    poses = None
    dsw = bool(files.get('ow')) and ('dsw' in os.path.basename(files['ow']).lower() or 'DSW' in os.path.basename(files['ow']))
    if files.get('ow'):
        poses, why = read_ow(files)
        if poses is None: note.append('걷기 그림을 못 나눔(%s) → 자동' % why)
        else: note.append('걷기 = %s (%s)' % ('DS 월드 도트(크기 그대로)' if dsw else '제미나이', why))
        if poses is not None and dsw: fitpx = None          # 이미 DS 도트 → 줄이거나 늘리지 않음(칸보다 크면만 줄임)
    if poses is None and files.get('ow_src'):
        sf, sb, mode, sname = files['ow_src']
        try:
            f2 = recolor(load(sf), mode); b2 = recolor(load(sb), mode) if sb else mirror(f2)
            d, u = fit_small(f2, fitpx), fit_small(b2, fitpx)
            poses = [d, d, u, u, d, d, mirror(d), mirror(d)]; note.append('걷기 = %s 그림 빌림(%s)' % (sname, mode or '색 그대로'))
        except Exception as e: note.append('걷기 빌림 실패(%s) → 자동' % e)
    if poses is None:
        d, u = fit_small(front, fitpx), fit_small(back, fitpx)
        poses = [d, d, u, u, d, d, mirror(d), mirror(d)]
        if not files.get('ow'): note.append('걷기 = 자동(앞·뒷모습)')
    cells = ow_cells(poses, cell, fitpx)
    ci, opal = quantize(cells, 15)
    sheet = []
    for r in range(4):
        for y in range(cell): sheet.append(ci[r * 2][y] + ci[r * 2 + 1][y])
    png_write(os.path.join(out_dir, 'ow.png'), sheet, opal)
    return (Fi, Bi, I1, ci[0], ci[2], ci[4], ci[6], bpal, ipal, opal, cell), note

def read_ow(files):
    w, h, img = png_read(files['ow']); poses, why = split_sheet(remove_bg(img))
    if poses is not None and files.get('fix'):
        poses = apply_fix(poses, files['fix']); why += ', 고침 ' + files['fix']
    return poses, why

def fit_small(p, px):
    n = native(p)
    return scale_to(n, px, px)

def ow_cells(poses, cell, fitpx):
    cells = []
    for i, p in enumerate(poses):
        if fitpx is None:                                   # DS 도트 그대로(걸음 흔들림도 원래 그림에 있으므로 올리지 않음)
            h, w = len(p), len(p[0])
            q = p if max(h, w) <= cell - 1 else scale_to(p, cell - 1, cell - 1)
            cells.append(place(q, cell, cell, bottom=1, shift_up=0)); continue
        c = place(fit_small(p, fitpx), cell, cell, bottom=2 if cell == 32 else 4, shift_up=(i % 2) * (1 if cell == 32 else 2))
        cells.append(outline(c) if cell == 32 else c)
    return cells

def build_ow_only(sp, files, out_dir):
    """앞모습 없이 걷기 그림만 (걷기 그림 시험용)"""
    if not files.get('ow'): raise ValueError('앞모습도 걷기 그림도 없음')
    big = sp['grade'] not in GRADE_SMALL
    cell = 32; fitpx = OW_PX.get(sp['grade'], 24)     # 10/12: 큰 디지몬도 32칸(디지골드와 같게)
    poses, why = read_ow(files)
    if poses is None: raise ValueError('걷기 그림을 못 나눔(%s)' % why)
    ci, opal = quantize(ow_cells(poses, cell, fitpx), 15)
    sheet = []
    for r in range(4):
        for y in range(cell): sheet.append(ci[r * 2][y] + ci[r * 2 + 1][y])
    png_write(os.path.join(out_dir, 'ow.png'), sheet, opal)
    E = [[0] * 80 for _ in range(80)]
    return (E, E, [[0] * 32 for _ in range(32)], ci[0], ci[2], ci[4], ci[6], opal, opal, opal, cell), ['앞모습 없음 → 걷기만', '걷기 = 제미나이 (%s)' % why]

# ============================================================ 본체
def survey(A, design, idx):
    """--survey: GBC 때 받은 앞·뒤 그림(<id>-f.png, -b.png) 중 NDS 배틀 그림으로 그대로 쓸 만한 것 고르기.
    회색 4톤(GBC 주문문 v3 결과)은 못 씀, 색이 있으면 NDS 크기로 바꿔 「후보」 쪽에 모은다. Claude 가 그림을 열 필요 없음."""
    rep = ['GBC 그림 조사 — 색 있음 = 후보(후보_NN.png 에서 눈으로 확인), 회색 = DS 주문 필요', '']
    cand = []; gray = []; none = []
    for n, sp in enumerate(design['species'], 1):
        if sp['ko'] == '디지문자': continue
        keys_en = [norm(sp['en'])] if sp['en'] else []
        f = next((idx[k + 'f'] for k in keys_en if k + 'f' in idx), None); b = next((idx[k + 'b'] for k in keys_en if k + 'b' in idx), None)   # 조사는 회색도 봐야 하므로 거르지 않음
        if not f: none.append('%d %s' % (n, sp['ko'])); continue
        info = []
        imgs = {}
        for side, path in (('앞', f), ('뒤', b)):
            if not path: info.append('%s 없음' % side); continue
            w, h, img = png_read(path); img = remove_bg(img); bb = bbox(img)
            if not bb: info.append('%s 빈 그림' % side); continue
            img = crop(img, bb)
            op = [p for r in img for p in r if p[3]]
            colorful = sum(1 for p in op if max(p[:3]) - min(p[:3]) > 40) / max(1, len(op))
            nat = native(img)
            cols = len(set(p[:3] for r in nat for p in r if p[3]))
            imgs[side] = (img, colorful)
            info.append('%s %s(색 비율 %.0f%%, 원래 도트 %dx%d, %d색)' % (side, '색' if colorful > 0.01 else '회색', colorful * 100, len(nat[0]), len(nat), cols))
        line = '%3d %-8s %s' % (n, sp['ko'], ' / '.join(info))
        if imgs and all(c > 0.01 for _, c in imgs.values()): cand.append((n, sp['ko'], imgs)); rep.append('후보 ' + line)
        else: gray.append(line)
    rep += [''] + ['DS 주문 필요 ' + x for x in gray] + ['', 'GBC 그림 없음 %d종: ' % len(none) + ', '.join(none)]
    # 후보 쪽: 20종씩, 앞·뒤를 NDS 크기(80x80)로
    DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001',
           '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111']
    for page in range((len(cand) + 19) // 20):
        chunk = cand[page * 20:(page + 1) * 20]; W, rowh, LM = 16 + 170, 82, 16
        pal = {(255, 255, 255): 0, (0, 0, 0): 1, (228, 232, 236): 2}; sheet = []
        def ci(c):
            if c not in pal:
                if len(pal) >= 256: return min(pal.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[0], c)))[1]
                pal[c] = len(pal)
            return pal[c]
        for num, name, imgs in chunk:
            rows = [[0] * W for _ in range(rowh)]
            for y in range(80):
                for x in range(LM, W): rows[y][x] = 2
            for k, d in enumerate(str(num)):
                for i, bit in enumerate(DIG[int(d)]):
                    if bit == '1': rows[4 + i // 3][1 + k * 4 + i % 3] = 1
            for j, side in enumerate(('앞', '뒤')):
                if side not in imgs: continue
                im = place(fit(imgs[side][0], 76, 76) if side == '앞' else fit(imgs[side][0], 80, 72), 80, 80, bottom=2 if side == '앞' else 0)
                (q,), qp = quantize([im], 15)
                for y in range(80):
                    for x in range(80):
                        if q[y][x]: rows[y][LM + j * 88 + x] = ci(qp[q[y][x]])
            sheet += rows
        big = [[v for v in r for _ in range(2)] for r in sheet for _ in range(2)]
        P = sorted(pal, key=pal.get)
        png_write(os.path.join(A.out, '후보_%02d.png' % (page + 1)), big, P + [(0, 0, 0)] * (256 - len(P)), transparent0=False)
        rep.append('후보_%02d.png: %s' % (page + 1, ' '.join('%d %s' % (c[0], c[1]) for c in chunk)))
    open(os.path.join(A.out, '조사.txt'), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
    print('후보 %d종, DS 주문 필요 %d종, GBC 그림 없음 %d종 → %s/조사.txt, 후보_NN.png' % (len(cand), len(gray), len(none), A.out))

BABY = ('유년기Ⅰ', '유년기Ⅱ', '유년기')        # 맵에서 공용 알로 따라다님(사용자 10/8)
DROP_GRADE = ('유아기Ⅰ', '유아기Ⅱ')                # 게임에서 뺌(사용자 10/8)

def make_egg_sheet(out_dir):
    """공용 디지타마(알) 걷기 그림 32x32 칸 2 x 4줄. 흰 알 + 파란 점, 진한 테두리, 걸음 2는 한 칸 들썩임"""
    def egg(shift):
        img = [[T] * 32 for _ in range(32)]
        cx, cy, rx, ry = 15.5, 18.5 - shift, 9.5, 12
        for y in range(32):
            for x in range(32):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1:
                    col = (248, 248, 240, 255)
                    if d > 0.78: col = (40, 40, 56, 255)
                    elif ((x - 11) ** 2 + (y - 14 + shift) ** 2 < 6) or ((x - 19) ** 2 + (y - 21 + shift) ** 2 < 8) or ((x - 13) ** 2 + (y - 25 + shift) ** 2 < 4):
                        col = (64, 128, 216, 255)
                    elif x > cx + 3 and y > cy: col = (208, 212, 224, 255)
                    img[y][x] = col
        return img
    cells = [egg(0), egg(1)] * 4
    ci, pal = quantize(cells, 15)
    sheet = []
    for r in range(4):
        for y in range(32): sheet.append(ci[r * 2][y] + ci[r * 2 + 1][y])
    png_write(os.path.join(out_dir, '공용_알_걷기.png'), sheet, pal)

def load_design(path):
    g = globals()
    if 'DESIGN_B64' in g and '@@' not in g['DESIGN_B64']:
        import base64
        return json.loads(zlib.decompress(base64.b64decode(''.join(g['DESIGN_B64'].split()))).decode('utf-8'))
    return json.load(open(path, encoding='utf-8'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', nargs='+', help='그림 폴더(여럿 가능, 앞 폴더가 우선): 예) games/images/digimon games/digimon/art/src'); ap.add_argument('--out', default='nds_art'); ap.add_argument('--only', default=''); ap.add_argument('--survey', action='store_true', help='GBC 그림 중 그대로 쓸 만한 것 고르기')
    ap.add_argument('--design', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'design.json'))
    A = ap.parse_args()
    design = load_design(A.design)
    have = {s['ko'] for s in design['species']}
    for ko, en, gr in EXTRA_SPECIES:                       # GBC 마지막 주 추가 9종(design.json 에 없음)
        if ko not in have: design['species'].append({'ko': ko, 'en': en, 'grade': gr, 'rom': ko, 'use': '추가'})
    idx = {}
    for folder in A.folder:                                # 앞 폴더가 우선(같은 이름이면 덮지 않음)
        if not os.path.isdir(folder): print('알림: 그림 폴더 없음 — 건너뜀:', folder); continue
        for root, dirs_, fs in os.walk(folder):
            dirs_[:] = [d_ for d_ in dirs_ if not d_.startswith('제외')]      # 10/16 집 보고: dsw_ow\제외_틀림\ 의 그림까지 읽히던 것
            for fn in sorted(fs):
                base, ext = os.path.splitext(fn)
                if ext.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
                    idx.setdefault(norm(base), os.path.join(root, fn))
                    idx.setdefault(base.replace(' ', ''), os.path.join(root, fn))
    os.makedirs(A.out, exist_ok=True)
    if A.survey: return survey(A, design, idx)
    only = set(x.strip() for x in A.only.split(',') if x.strip())
    rep = []; used = set(); prev = []; fixes = {}
    for folder in A.folder:
        if os.path.isdir(folder): fixes.update(load_fixes(folder))
    make_egg_sheet(A.out)
    for n, sp in enumerate(design['species'], 1):
        if sp['grade'] in DROP_GRADE: continue
        if only and sp['ko'] not in only: continue
        keys_ko = [sp['ko'].replace(' ', ''), sp['rom'].replace(' ', '')]
        keys_en = keys_for(sp)
        # 앞: DS 배틀 그림(<id>-ds-f) → 위키몬(-wk-f, DS 디지몬 스토리 원본) → 한글 이름 → 사용자 원본(-f) → 제미나이 원본(-f_ai, 회색이면 건너뜀)
        f = (find_file(idx, keys_en, ['dsf']) or find_file(idx, keys_ko, ['_DS앞', '_ds앞']) or find_file(idx, keys_en, ['wkf'])
             or find_file(idx, keys_ko, ['_앞', '-앞', '앞']) or find_file(idx, keys_en, ['f', 'fai']) or find_file(idx, keys_ko, ['']))
        # 뒤: DS 뒤 → 한글 → 위키몬 공격 자세(뒤집어 씀, 10/12 「역동적인 자세」) → 사용자 원본(-b) → 제미나이 원본(-b_ai)
        b = (find_file(idx, keys_en, ['dsb']) or find_file(idx, keys_ko, ['_DS뒤', '_ds뒤']) or find_file(idx, keys_ko, ['_뒤', '-뒤', '뒤'])
             or find_file(idx, keys_en, ['wkatk']) or find_file(idx, keys_en, ['b', 'bai']))
        # 걷기: DS 월드 진짜 걷기 그림(<id>-dsw-ow.png, 10/14 사용자 「실제 걷기가 나오게」) → 제미나이 걷기 → 그 밖의 <id>-ow
        ow = find_file(idx, keys_en, ['dswow']) or find_file(idx, keys_ko, ['_DSW걷기', '_걷기', '-걷기', '걷기']) or find_file(idx, keys_en, ['ow'])
        if not f and not ow:                               # 10/15: 회색이라 건너뛴 그림밖에 없으면 그거라도 씀
            ALLOW_GRAY[0] = True
            f = (find_file(idx, keys_en, ['dsf']) or find_file(idx, keys_ko, ['_DS앞', '_ds앞']) or find_file(idx, keys_en, ['wkf'])
                 or find_file(idx, keys_ko, ['_앞', '-앞', '앞']) or find_file(idx, keys_en, ['f', 'fai']) or find_file(idx, keys_ko, ['']))
            b = b or find_file(idx, keys_en, ['dsb', 'b', 'bai']) or find_file(idx, keys_ko, ['_뒤', '-뒤', '뒤'])
            ALLOW_GRAY[0] = False
            if f: rep.append('%3d %s: ※ 회색 그림밖에 없어 그것을 씀 — 컬러 그림 필요(그림 주문 목록에 올림)' % (n, sp['ko']))
        if not f and not ow:
            rep.append('%3d %s: 그림 없음 — 건너뜀' % (n, sp['ko'])); continue
        ow_src = None
        if sp['ko'] in OW_BORROW and not ow:
            src_ko, mode = OW_BORROW[sp['ko']]; ssp = next((x for x in design['species'] if x['ko'] == src_ko), None)
            if ssp:
                sk_ko = [ssp['ko'], ssp.get('rom', ssp['ko'])]; sk_en = keys_for(ssp)
                sf = (find_file(idx, sk_en, ['dsf']) or find_file(idx, sk_ko, ['_DS앞', '_ds앞']) or find_file(idx, sk_en, ['wkf'])
                      or find_file(idx, sk_ko, ['_앞', '-앞', '앞']) or find_file(idx, sk_en, ['f', 'fai']) or find_file(idx, sk_ko, ['']))
                sb = (find_file(idx, sk_en, ['dsb']) or find_file(idx, sk_ko, ['_DS뒤', '_ds뒤']) or find_file(idx, sk_ko, ['_뒤', '-뒤', '뒤']) or find_file(idx, sk_en, ['b', 'bai']))
                if sf: ow_src = (sf, sb, mode, src_ko)
        used.update(x for x in (f, b, ow) if x)
        d = os.path.join(A.out, '%03d_%s' % (n, sp['ko'])); os.makedirs(d, exist_ok=True)
        try:
            fix = next((fixes[k] for k in keys_ko + keys_en if k in fixes), None)
            res, note = build_one(sp, {'f': f, 'b': b, 'ow': ow, 'fix': fix, 'ow_src': ow_src}, d)
            prev.append((n, sp['ko'], res)); rep.append('%3d %s: %s' % (n, sp['ko'], ', '.join(note) or 'OK'))
        except Exception as e:
            rep.append('%3d %s: 실패 %s' % (n, sp['ko'], e))
    # 10/15 사용자 완성 조건: 데리고 다니는 그림이 모든 종 뭉개지지 않아야 함 → 출처별 수와 「자동(전투 그림 줄임)」 종 목록을 맨 끝 요약에
    kinds = collections.OrderedDict([('진짜 걷기(DS 도트)', '걷기 = DS 월드'), ('제미나이 걷기', '걷기 = 제미나이'), ('다른 종 빌림', '그림 빌림'), ('자동(전투 그림 줄임)', '걷기 = 자동'), ('공용 알', '걷기 = 공용 알')])
    cnt = {k: [] for k in kinds}
    for line in rep:
        for k, w in kinds.items():
            if w in line: cnt[k].append(line.split(':')[0].strip().split(' ', 1)[-1]); break
    sus_ = [l.split(':')[0].strip() for l in rep if '흰 잔사 의심' in l]
    rep.append(chr(10) + '== 흰 잔사 의심 %d종(눈으로 확인 → 맞으면 art_nds.py 의 HOLE_SPECIES 에 이름을 더하고 다시): %s' % (len(sus_), ' '.join(sus_)))
    rep.append('== 데리고 다니는 그림 출처: ' + ' / '.join('%s %d' % (k, len(v)) for k, v in cnt.items()))
    keep_dg = set()                                    # 디지골드 자기 칸 종은 hg4_follow 가 안 바꿈(디지골드 원래 걷기 그림) → 후보에서 뺌
    dp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv')
    if os.path.exists(dp):
        for l in open(dp, encoding='utf-8').read().split(chr(10))[1:]:
            r = l.split(chr(9))
            if len(r) > 4 and r[4] == '디지골드' and not r[1].isdigit(): keep_dg.add(r[2])
    todo = [x for x in cnt['자동(전투 그림 줄임)'] if x not in keep_dg]
    rep.append('자동(전투 그림 줄임) 중 새 그림 칸 %d종 — 진짜 걷기 그림으로 바꿔야 할 후보: %s' % (len(todo), ' '.join(todo)))
    if SKIPPED_GRAY: rep.append(chr(10) + '회색 4톤이라 안 쓴 그림 %d개: %s' % (len(set(SKIPPED_GRAY)), ' '.join(sorted(set(SKIPPED_GRAY))[:60])))
    left = sorted(set(idx.values()) - used)
    rep.append('\n어느 종에도 안 쓴 파일 %d개(이름이 틀렸을 수 있음):' % len(left)); rep += ['  ' + os.path.basename(x) for x in left]
    # 미리보기: 20종씩 한 쪽, 2배 크기, 줄 앞에 종 번호 (사용자가 눈으로 보거나, Claude 에게 쪽 단위로만 보여 줌)
    DIG = ['111101101101111', '010110010010111', '111001111100111', '111001111001111', '101101111001001',
           '111100111001111', '111100111101111', '111001001001001', '111101111101111', '111101111001111']
    PER, Z, LM = 20, 2, 16
    for page in range((len(prev) + PER - 1) // PER):
        chunk = prev[page * PER:(page + 1) * PER]
        rowh = 80; W = LM + 80 + 80 + 32 + 4 * 64
        sheet = []; pal_all = {(255, 255, 255): 0, (0, 0, 0): 1, (228, 232, 236): 2}
        def ci(c):
            if c not in pal_all:
                if len(pal_all) >= 256: return min(pal_all.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[0], c)))[1]
                pal_all[c] = len(pal_all)
            return pal_all[c]
        for num, name, (Fi, Bi, I1, od, ou, ol, orr, bpal, ipal, opal, cell) in chunk:
            rows = [[0] * W for _ in range(rowh)]
            for y in range(rowh - 2):
                for x in range(LM, W): rows[y][x] = 2
            for k, d in enumerate(str(num)):
                for i, bit in enumerate(DIG[int(d)]):
                    if bit == '1': rows[4 + i // 3][1 + k * 4 + i % 3] = 1
            def blit(img, pal, ox, oy=0):
                for y, r in enumerate(img):
                    for x, v in enumerate(r):
                        if v and 0 <= oy + y < rowh: rows[oy + y][ox + x] = ci(pal[v])
            blit(Fi, bpal, LM); blit(Bi, bpal, LM + 80); blit(I1, ipal, LM + 160, 24)
            for k, o in enumerate((od, ou, ol, orr)): blit(o, opal, LM + 192 + k * 64, 80 - cell)
            sheet += rows
        big = [[v for v in r for _ in range(Z)] for r in sheet for _ in range(Z)]
        pal = sorted(pal_all, key=pal_all.get)
        png_write(os.path.join(A.out, '미리보기_%02d.png' % (page + 1)), big, pal + [(0, 0, 0)] * (256 - len(pal)), transparent0=False)
        rep.append('미리보기_%02d.png: %s' % (page + 1, ' '.join('%d %s' % (c[0], c[1]) for c in chunk)))
    open(os.path.join(A.out, '보고.txt'), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
    print('\n'.join(rep[-40:])); print('끝: %d종 → %s (미리보기_*.png 로 확인)' % (len(prev), A.out))

DESIGN_B64 = '@@'

if __name__ == '__main__':
    main()
