"""시험 롬: 전투 화면 2장(등장 대사 / 메뉴)을 GBC 배경 타일로 만들어 A 버튼으로 넘김.
화면을 파이썬으로 160×144 그림으로 짜고 → 8×8 타일로 쪼개 같은 타일은 하나로 → C 파일로 내보냄."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = sys.path[0]
FONT = sys.argv[1]
d = json.loads(open(HERE + '/../ai/sprites.js').read()[len('window.AISPR='):-1])
font = ImageFont.truetype(FONT, 10)

def text(scr, s, x, y, tone=3):
    im = Image.new('L', (160, 14), 0); ImageDraw.Draw(im).text((0, 1), s, font=font, fill=255)
    a = np.asarray(im) > 110
    ys, xs = np.where(a)
    for yy, xx in zip(ys, xs):
        if 0 <= x + xx < 160 and 0 <= y + yy < 144: scr[y + yy, x + xx] = tone
def rect(scr, x, y, w, h, t): scr[y:y + h, x:x + w] = t
def box(scr, x, y, w, h):
    rect(scr, x, y, w, h, 3); rect(scr, x + 1, y + 1, w - 2, h - 2, 0)
    rect(scr, x + 3, y + 3, w - 6, 1, 3); rect(scr, x + 3, y + h - 4, w - 6, 1, 3); rect(scr, x + 3, y + 3, 1, h - 6, 3); rect(scr, x + w - 4, y + 3, 1, h - 6, 3)
def spr(scr, name, x, y):
    t = np.array(d[name]); h, w = t.shape
    for yy in range(h):
        for xx in range(w):
            v = t[yy, xx]
            if v >= 0 and 0 <= y + yy < 144 and 0 <= x + xx < 160: scr[y + yy, x + xx] = v
def bar(scr, x, y, frac):
    rect(scr, x, y, 50, 4, 3); rect(scr, x + 1, y + 1, 48, 2, 0); rect(scr, x + 1, y + 1, int(48 * frac), 2, 2)
def base():
    s = np.zeros((144, 160), int)
    for yy in range(6):
        w = round(34 * np.sqrt(1 - ((yy - 2.5) / 3) ** 2)); s[58 + yy, 124 - w:124 + w] = 1
    g = np.array(d['gollum']); spr(s, 'gollum', 160 - g.shape[1] - 4, 64 - g.shape[0])
    b = np.array(d['frodosam_back']); spr(s, 'frodosam_back', 2, 104 - b.shape[0])
    text(s, '골룸', 4, 3); text(s, 'Lv12', 54, 3); text(s, 'HP', 6, 13); bar(s, 22, 17, 1.0); rect(s, 4, 23, 72, 1, 3); rect(s, 75, 15, 1, 9, 3)
    rect(s, 86, 62, 74, 34, 0); text(s, '프로도·샘', 89, 62); text(s, 'Lv14', 136, 62); text(s, 'HP', 90, 72); bar(s, 106, 76, 1.0)
    text(s, ' 52/ 52', 104, 82); rect(s, 86, 94, 72, 1, 3); rect(s, 86, 72, 1, 23, 3)
    box(s, 0, 96, 160, 48); return s
s1 = base(); text(s1, '야생의 골룸이 덤벼들었다!', 8, 105); text(s1, '「내 보물... 내 보물...」', 8, 121)
s2 = base(); text(s2, '프로도·샘은', 8, 105); text(s2, '어떻게 할까?', 8, 121)
box(s2, 80, 96, 80, 48); text(s2, '▶싸운다', 86, 105); text(s2, '가방', 128, 105); text(s2, '동료', 92, 121); text(s2, '도망', 128, 121)
screens = [s1, s2]
tiles = []; idx = {}; maps = []
for s in screens:
    m = []
    for ty in range(18):
        for tx in range(20):
            b = s[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]; key = b.tobytes()
            if key not in idx: idx[key] = len(tiles); tiles.append(b)
            m.append(idx[key])
    maps.append(m)
print('서로 다른 타일', len(tiles))
assert len(tiles) <= 512, '타일이 512개를 넘음'
def enc(b):
    out = []
    for row in b:
        lo = hi = 0
        for x, v in enumerate(row): lo |= (v & 1) << (7 - x); hi |= ((v >> 1) & 1) << (7 - x)
        out += [lo, hi]
    return out
data = sum((enc(t) for t in tiles), [])
with open(HERE + '/tiles.c', 'w') as f:
    f.write('#include <stdint.h>\n')
    n0 = min(256, len(tiles)); n1 = len(tiles) - n0
    f.write('const uint16_t NT0 = %d, NT1 = %d;\n' % (n0, n1))
    f.write('const uint8_t TILES0[] = {' + ','.join(map(str, data[:n0 * 16])) + '};\n')
    f.write('const uint8_t TILES1[] = {' + ','.join(map(str, data[n0 * 16:] or [0])) + '};\n')
    for k, m in enumerate(maps):
        f.write('const uint8_t MAP%d[] = {' % k + ','.join(str(v & 255) for v in m) + '};\n')
        f.write('const uint8_t ATTR%d[] = {' % k + ','.join('8' if v >= 256 else '0' for v in m) + '};\n')   # 8 = 타일을 VRAM 2번 칸에서
Image.fromarray(np.array([[248, 176, 96, 24][v] for v in np.concatenate(screens, 1).ravel()], np.uint8).reshape(144, 320)).resize((960, 432), Image.NEAREST).save(HERE + '/preview.png')
