"""G단계 메뉴 아이콘 10종 — 위키몬 원작 디지털 몬스터(Ver.1~5) LCD 도트(16×16)로 금 파티 메뉴 아이콘(16×32 = 16×16 두 프레임, 4톤) 만들기
  python3 tools/icons.py        → art/icons/<분류>.png (롬에 넣는 그림) + art/icons/_preview_x8.png (확인용)
LCD 검은 칸 = 검정 외곽선, 바깥과 이어지지 않은 안쪽 = 밝은 톤, 바깥 = 흰(투명).
1프레임은 아래에서 한 칸 띄워 두고 2프레임은 한 칸 내림 (금 아이콘처럼 통통 뛰는 움직임).
LCD gif 는 art/sketch/<이름>_dm.gif (위키몬 File:<이름>_vpet_dm.gif, 주소는 미디어위키 규칙 md5 경로. 저장소에 안 올림).
새 판(dv·20주년)은 24~32칸이라 16칸으로 줄이면 선이 깨져서 원작(dm) 16칸만 씀."""
import hashlib, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lcd2sketch

OUT = os.path.join(WEB, 'art', 'icons')
# 분류 → (대표 디지몬 LCD, 덮어쓸 금 아이콘 번호 = constants/icon_constants.asm 순서)
CATS = {'유년기': ('Koromon', 2),        # ICON_JIGGLYPUFF (코로몬·유년기가 이미 쓰던 칸)
        '공룡': ('Agumon', 8),           # ICON_MONSTER
        '짐승': ('Gabumon', 15),         # ICON_FOX
        '새': ('Piyomon', 7),            # ICON_BIRD
        '벌레': ('Kuwagamon', 11),       # ICON_BUG
        '식물': ('Palmon', 10),          # ICON_ODDISH
        '바다': ('Seadramon', 6),        # ICON_FISH
        '기계': ('Andromon', 20),        # ICON_VOLTORB
        '천사': ('Angemon', 9),          # ICON_CLEFAIRY
        '악마': ('Devimon', 12)}         # ICON_GHOST
TONE = {0: 255, 1: 170, 2: 85, 3: 0}


def lcd(name):
    src = os.path.join(WEB, 'art', 'sketch', name.lower() + '_dm.gif')
    if not os.path.exists(src):
        fn = name + '_vpet_dm.gif'; h = hashlib.md5(fn.encode()).hexdigest()
        os.makedirs(os.path.dirname(src), exist_ok=True)
        subprocess.run(['curl', '-sS', '-f', '-m', '30', '-o', src, 'https://wikimon.net/images/%s/%s/%s' % (h[0], h[:2], fn)], check=True)
    return lcd2sketch.native(src)[0]


def fit16(a):
    """16칸보다 크면 가장 가까운 칸으로 줄임"""
    h, w = a.shape; f = min(1.0, 16 / max(h, w))
    if f == 1.0: return a
    H, W = max(1, round(h * f)), max(1, round(w * f))
    return a[np.minimum((np.arange(H) / f).astype(int), h - 1)][:, np.minimum((np.arange(W) / f).astype(int), w - 1)]


def frame(a, down):
    """bool 칸(검정) → 16×16 4톤 (0 흰, 1 밝은, 3 검정). 아래 맞춤, down 칸 내림"""
    a = fit16(a); h, w = a.shape
    c = np.zeros((16, 16), int); top = max(0, 16 - h - 1 + down); left = (16 - w) // 2
    blk = np.zeros((16, 16), bool)
    hh = min(h, 16 - top); blk[top:top + hh, left:left + w] = a[:hh]
    out = np.ones((16, 16), bool); stack = [(y, x) for y in range(16) for x in (0, 15)] + [(y, x) for x in range(16) for y in (0, 15)]
    seen = set()
    while stack:                                                  # 바깥(흰) 찾기
        y, x = stack.pop()
        if (y, x) in seen or not (0 <= y < 16 and 0 <= x < 16) or blk[y, x]: continue
        seen.add((y, x)); stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    for y in range(16):
        for x in range(16):
            c[y, x] = 3 if blk[y, x] else (0 if (y, x) in seen else 1)
    return c


def icon(name):
    a = lcd(name)
    return np.vstack([frame(a, 0), frame(a, 1)])


def main():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for cat, (name, _) in CATS.items():
        g = icon(name)
        Image.fromarray(np.vectorize(TONE.get)(g).astype(np.uint8), 'L').save(os.path.join(OUT, cat + '.png'))
        tiles.append(g); print(cat, name, 'LCD', lcd(name).shape)
    # 확인용: 분류마다 두 프레임 ×8
    W = len(tiles) * 18 * 8; prev = Image.new('L', (W, 34 * 8), 255)
    for i, g in enumerate(tiles):
        im = Image.fromarray(np.vectorize(TONE.get)(g).astype(np.uint8), 'L').resize((16 * 8, 32 * 8), Image.NEAREST)
        prev.paste(im, (i * 18 * 8, 8))
    prev.save(os.path.join(OUT, '_preview_x8.png'))


if __name__ == '__main__':
    main()
