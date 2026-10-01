"""GBC 그림 도구: 2bpp 타일, 팔레트, 금판식 화면 부품(테두리·숫자·HP 막대), 한글 8×16 글자칸"""
import numpy as np

WHITE, BLACK = (248, 248, 248), (24, 24, 24)
GRAY = [(248, 248, 248), (168, 168, 168), (88, 88, 88), (24, 24, 24)]


def rgb15(c):
    r, g, b = c
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def hexrgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def enc2bpp(t):
    """8×8 칸(값 0~3) → 16바이트"""
    out = []
    for row in t:
        lo = hi = 0
        for x, v in enumerate(row):
            lo |= (int(v) & 1) << (7 - x)
            hi |= ((int(v) >> 1) & 1) << (7 - x)
        out += [lo, hi]
    return out


def enc1bpp(t):
    out = []
    for row in t:
        b = 0
        for x, v in enumerate(row):
            if v: b |= 1 << (7 - x)
        out.append(b)
    return out


def cut(img, tw, th):
    """(h,w) 배열을 8×8 타일 목록으로 (줄 우선)"""
    return [img[y * 8:y * 8 + 8, x * 8:x * 8 + 8] for y in range(th) for x in range(tw)]


class Tiles:
    """같은 타일은 하나로 합치는 타일 모음"""
    def __init__(self, start=0):
        self.start = start; self.list = []; self.idx = {}

    def add(self, t):
        t = np.asarray(t, np.uint8); k = t.tobytes()
        if k not in self.idx:
            self.idx[k] = self.start + len(self.list); self.list.append(t)
        return self.idx[k]

    def data(self):
        return sum((enc2bpp(t) for t in self.list), [])


# ── 한글 글꼴 (font.js 갈무리11 Condensed) → 8×16 칸, 기준선 12 ──
def glyph_bits(font, ch):
    d = font.get(ch) or font.get('?')
    dw, w, h, xo, yo, hx, hl = d
    rows = []
    for i in range(h):
        v = int(hx[i * hl:(i + 1) * hl], 16); bits = hl * 4
        rows.append([(v >> (bits - 1 - x)) & 1 for x in range(w)])
    return dw, w, h, xo, yo, rows


def glyph16(font, ch):
    """한 글자 → 16×8 (0/1). 한글(폭 8)은 그대로, 좁은 글자는 가운데쯤"""
    a = np.zeros((16, 8), np.uint8)
    if ch == ' ': return a
    dw, w, h, xo, yo, rows = glyph_bits(font, ch)
    base = 12
    x0 = xo if dw >= 7 else max(0, (8 - w) // 2)
    top = base - h - yo
    for j, r in enumerate(rows):
        for i, v in enumerate(r):
            y, x = top + j, x0 + i
            if v and 0 <= y < 16 and 0 <= x < 8: a[y, x] = 1
    return a


# ── 금판식 부품 (ui.js 와 같은 모양) ──
def frame(c, x, y, w, h):
    c[y:y + h, x:x + w] = 0
    c[y, x + 2:x + w - 2] = 3; c[y + h - 1, x + 2:x + w - 2] = 3; c[y + 2:y + h - 2, x] = 3; c[y + 2:y + h - 2, x + w - 1] = 3
    for (px, py) in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)): c[py, px] = 3
    c[y + 2:y + 4, x + 3:x + w - 3] = 3; c[y + h - 4:y + h - 2, x + 3:x + w - 3] = 3
    c[y + 3:y + h - 3, x + 2:x + 4] = 3; c[y + 3:y + h - 3, x + w - 4:x + w - 2] = 3


def frame2(c, x, y, w, h):
    c[y:y + h, x:x + w] = 0
    c[y:y + 2, x + 2:x + w - 2] = 3; c[y + h - 2:y + h, x + 2:x + w - 2] = 3
    c[y + 2:y + h - 2, x:x + 2] = 3; c[y + 2:y + h - 2, x + w - 2:x + w] = 3
    for (px, py) in ((x + 1, y + 1), (x + w - 3, y + 1), (x + 1, y + h - 3), (x + w - 3, y + h - 3)): c[py:py + 2, px:px + 2] = 3


def cursor(c, x, y):
    for i in range(4): c[y + i:y + i + 7 - i * 2, x + i] = 3


def more(c, x, y):
    for j in range(4): c[y + j, x + j:x + j + 7 - j * 2] = 3


DIG = {
    '0': ['.#####.', '##...##', '##...##', '##...##', '##...##', '##...##', '.#####.'],
    '1': ['...##..', '..###..', '...##..', '...##..', '...##..', '...##..', '..####.'],
    '2': ['.#####.', '##...##', '.....##', '...###.', '.###...', '##.....', '#######'],
    '3': ['######.', '.....##', '.....##', '.#####.', '.....##', '.....##', '######.'],
    '4': ['...###.', '..####.', '.##.##.', '##..##.', '#######', '....##.', '....##.'],
    '5': ['#######', '##.....', '######.', '.....##', '.....##', '##...##', '.#####.'],
    '6': ['.#####.', '##.....', '######.', '##...##', '##...##', '##...##', '.#####.'],
    '7': ['#######', '##...##', '.....##', '....##.', '...##..', '..##...', '..##...'],
    '8': ['.#####.', '##...##', '##...##', '.#####.', '##...##', '##...##', '.#####.'],
    '9': ['.#####.', '##...##', '##...##', '.######', '.....##', '.....##', '.#####.'],
    '/': ['.....##', '....##.', '...##..', '..##...', '.##....', '##.....', '#......'],
    ':': ['..', '##', '##', '..', '##', '##', '..'],
    'L': ['##....', '##....', '##....', '##....', '##....', '##....', '#####.'],
}


def num(c, s, x, y):
    cx = x
    for ch in s:
        if ch == ' ': cx += 8; continue
        d = DIG[ch]
        for j, r in enumerate(d):
            for i, v in enumerate(r):
                if v == '#': c[y + j, cx + i] = 3
        cx += 2 if ch == ':' else 6 if ch == 'L' else 8
    return cx
