"""게임 도트 시트(원더스완·GBA·NDS) → art/<id>-f.png (4색, 배경 투명). 시트는 art/src/rip/ 에 받아 둠(저장소에 안 올림 — 용량)
    python3 rip2art.py                    목록 전부 변환 → art/src/rip/out/ + 한눈에 보기 _rip_preview.png
    python3 rip2art.py --only pagumon     한 종만
    python3 rip2art.py --install          승인된 것만 art/<id>-f.png 로 (이미 있는 그림은 --force 일 때만 덮음)
변환은 sheet2gbc.py 와 같은 단계(배경 → 4톤 → 줄이기 → 테두리). 몸 색 두 개는 원본에서 k-평균으로 뽑음 — 롬은 그림의 색을 팔레트로 씀.
이미 뒷모습이 있는 종은 그 뒷모습의 색으로 맞춤(롬은 앞·뒤가 팔레트 하나)."""
import argparse, os, sys, urllib.request, re
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
sys.path.insert(0, HERE); import sheet2gbc as S
RIP = os.path.join(WEB, 'art', 'src', 'rip'); OUT = os.path.join(RIP, 'out')
TSR = 'https://www.spriters-resource.com'
SPLIT = 'lum'                                                         # 'lum' 밝기로 / 'color' k-평균 색으로

# 시트: 이름 → (The Spriters Resource 페이지, 칸 나누기)
SHEETS = {
    'ruby': ('/game_boy_advance/digimonrubybootleg/asset/269064/', 'Digimon Ruby (GBA 해적판) 「Digimon」 64칸 앞모습'),
    'd1_in': ('/wonderswan_wsc/digimonadventure02d1tamer/asset/127906/', '디지몬 어드벤처 02 D-1 테이머즈 유년기'),
    'd1_champ': ('/wonderswan_wsc/digimonadventure02d1tamer/asset/127993/', 'D-1 테이머즈 성숙기'),
    'd1_ult': ('/wonderswan_wsc/digimonadventure02d1tamer/asset/128682/', 'D-1 테이머즈 완전체'),
    'ds2_pagumon': ('/ds_dsi/digimonworldds2/asset/40900/', 'Digimon World Dawn/Dusk 퍼그몬'),
    'ds2_kunemon': ('/ds_dsi/digimonworldds2/asset/40908/', 'Dawn/Dusk 쿠네몬'),
    'ds2_gotsumon': ('/ds_dsi/digimonworldds2/asset/41528/', 'Dawn/Dusk 돌몬'),
}


def ruby(r, c): y = 8 + 72 * r if r < 12 else (872, 944)[r - 12]; x = 8 + 72 * c; return (x, y, x + 64, y + 62)  # 아래 2칸은 색 막대
def d1c(r, c): return (int(c * 134.5) + 3, int(r * 134) + 3, int((c + 1) * 134.5) - 3, int((r + 1) * 134) - 3)
def d1u(r, c): return (int(c * 139.3) + 3, int(r * 139.3) + 3, int((c + 1) * 139.3) - 3, int((r + 1) * 139.3) - 3)
def d1i(r, c): return (int(c * 95.75) + 3, int(r * 94.75) + 3, int((c + 1) * 95.75) - 3, int((r + 1) * 94.75) - 3)


# id, 시트, 범위(x0,y0,x1,y1 또는 ('n', 시트 안 몇 번째 덩어리)), 칸 크기, 메모(종 판정 근거·확신)
LIST = [
    ('chibimon', 'ruby', ruby(1, 0), 40, '브이몬 줄 첫 칸 (다음 칸 브이몬·엑스브이몬)'),
    ('chibimon~d1', 'd1_in', d1i(2, 3), 40, 'D-1 판 (점프 자세)'),
    ('poromon', 'ruby', ruby(2, 0), 40, '호크몬 줄 첫 칸'),
    ('poromon~d1', 'd1_in', d1i(3, 0), 40, 'D-1 판'),
    ('minomon', 'ruby', ruby(1, 7), 40, '잎몬(1,6) → 데롱몬 → 추추몬(1,8) 줄'),
    ('minomon~d1', 'd1_in', d1i(3, 2), 40, 'D-1 판'),
    ('pagumon', 'ds2_pagumon', (4, 2, 62, 54), 40, 'Dawn/Dusk 퍼그몬 (페이지 이름으로 확인)'),
    ('kunemon', 'ds2_kunemon', ('n', 0), 48, 'Dawn/Dusk 쿠네몬 (페이지 이름으로 확인)'),
    ('gottsumon', 'ds2_gotsumon', ('n', 0), 48, 'Dawn/Dusk 돌몬 (페이지 이름으로 확인)'),
    ('plotmon', 'ruby', ruby(2, 6), 48, '다음 칸 가트몬'),
    ('monochromon', 'd1_champ', d1c(3, 0), 56, '회색 뿔 공룡'),
    ('devimon', 'd1_champ', d1c(4, 6), 56, '찢어진 날개·팔 붉은 띠'),
    ('flymon', 'ruby', ruby(7, 10), 56, '말벌'),
    ('drimogemon', 'ruby', ruby(8, 11), 56, '드릴 두더지'),
    ('kiwimon', 'ruby', ruby(7, 1), 56, '긴 부리 새'),
    ('vegimon', 'ruby', ruby(7, 7), 56, '머리 보라 잎·덩굴 채찍 (확신 중간)'),
    ('meramon', 'ruby', ruby(11, 7), 56, '불꽃 몸'),
    ('whamon', 'ruby', ruby(10, 8), 56, '고래'),
    ('digmon', 'ruby', ruby(3, 3), 56, '아르마딜로몬 줄 노란 드릴 아머체'),
    ('mamemon', 'd1_ult', d1u(0, 0), 56, '작은 공 몸·큰 주먹 (다음 칸 메탈마메몬)'),
    ('okuwamon', 'd1_ult', d1u(1, 2), 56, '큰 사슴벌레 (확신 중간)'),
    ('mammon', 'd1_ult', d1u(2, 5), 56, '긴 엄니 매머드'),
    ('andromon', 'ruby', ruby(7, 12), 56, '은색 안드로이드'),
    ('monzaemon', 'ruby', ruby(12, 1), 56, '노란 곰 인형'),
    ('imperialdramondragonmode', 'ruby', ruby(1, 11), 56, '네 발 용 (다음 칸 파이터 모드)'),
]


def sheet(name):
    os.makedirs(RIP, exist_ok=True); p = os.path.join(RIP, name + '.png')
    if not os.path.exists(p):
        page = urllib.request.urlopen(TSR + SHEETS[name][0], timeout=60).read().decode('utf-8', 'ignore')
        u = re.search(r'/media/assets/[^"?]+', page).group(0)
        open(p, 'wb').write(urllib.request.urlopen(TSR + u, timeout=60).read())
    return np.asarray(Image.open(p).convert('RGBA'))


def drop_shadow(rgba, fg):
    """NDS·GBA 발밑 그림자(아래쪽의 아주 어두운 한 가지 색 타원) 지우기: 아래 40% 안에서 가장 많은 어두운 색과 같은 칸"""
    h = rgba.shape[0]; a = rgba[..., :3].astype(int); low = np.zeros_like(fg); low[int(h * .6):] = True
    dark = fg & low & (S.lum(a) < 60)
    if dark.sum() < 12: return fg
    cols, n = np.unique(a[dark].reshape(-1, 3), axis=0, return_counts=True); c = cols[np.argmax(n)]
    sh = low & (np.abs(a - c).max(2) <= 6)
    return fg & ~sh


def drop_halo(rgba, fg, n=2):
    """원더스완 시트의 바깥 흰 테두리(배경과 닿은 흰 칸) 벗기기"""
    a = rgba[..., :3].astype(float); white = (S.lum(a) >= 200) & ((a.max(2) - a.min(2)) < 40)
    for _ in range(n):
        p = np.pad(fg, 1); edge = fg & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        if not (edge & white).any(): break
        fg = fg & ~(edge & white)
    return fg


def convert(e, pal=None):
    pal_in = pal
    did, sh, box, size, _ = e
    a = sheet(sh)
    if box[0] == 'n':
        fg = ~S.background(a); fg = drop_shadow(a, fg); bs = S.sprites(fg, 3, 64); y0, x0, y1, x1 = bs[box[1]]
        a = a[y0:y1, x0:x1]
    else:
        x0, y0, x1, y1 = box; a = a[y0:y1, x0:x1]
    fg = ~S.background(a); fg = drop_shadow(a, fg)
    b = S.sprites(fg, 3, 32)
    y0, x0 = min(v[0] for v in b), min(v[1] for v in b); y1, x1 = max(v[2] for v in b), max(v[3] for v in b)
    a, fg = a[y0:y1, x0:x1], fg[y0:y1, x0:x1]
    fg = drop_halo(a, fg)
    L = S.lum(a[..., :3].astype(float)); black = float(np.clip(np.percentile(L[fg], 10) + 10, 30, 70))   # 어두운 몸(데블몬 등)이 통째로 검정이 되지 않게
    t, pal = S.tones(a[..., :3], fg, pal, black=black)
    if SPLIT == 'lum' and pal_in is None:                             # 밝기로 반 나누기: 색이 여러 가지인 종도 「밝은 면·그늘」로 갈라져 금판 그림처럼 보임
        mid = fg & (t > 0) & (t < 3); Lm = L[mid]; cut = np.median(Lm)
        t[mid] = np.where(Lm >= cut, 1, 2)
        rgb = a[..., :3].astype(float)
        pal = [tuple(int(v) for v in rgb[mid & (L >= cut)].mean(0)), tuple(int(v) for v in rgb[mid & (L < cut)].mean(0))]
    t = S.outline(S.drop_specks(S.shrink(t, size)))
    ys, xs = np.where(t >= 0); t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return t, pal


def to_rgba(t, pal):
    cols = np.array([S.WHITE + (255,), tuple(pal[0]) + (255,), tuple(pal[1]) + (255,), S.BLACK + (255,)], np.uint8)
    out = np.zeros(t.shape + (4,), np.uint8); out[t >= 0] = cols[t[t >= 0]]
    return Image.fromarray(out, 'RGBA')


def back_pal(did):
    """이미 있는 뒷모습의 몸 색 두 개 (밝은 순)"""
    p = os.path.join(WEB, 'art', did + '-b.png')
    if not os.path.exists(p): return None
    a = np.asarray(Image.open(p).convert('RGBA')); c = {tuple(x[:3]) for x in a[a[..., 3] > 128]}
    mids = sorted((x for x in c if 40 <= S.lum(np.array(x, float)) <= 235), key=lambda x: -S.lum(np.array(x, float)))
    return [mids[0], mids[-1]] if len(mids) >= 2 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--only'); ap.add_argument('--install', nargs='*', help='art/ 에 넣을 id (~d1 같은 다른 판도 이름 그대로)')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--split', choices=['lum', 'color'], default='lum')
    a = ap.parse_args(); os.makedirs(OUT, exist_ok=True)
    global SPLIT; SPLIT = a.split
    done = []
    for e in LIST:
        if a.only and e[0].split('~')[0] != a.only: continue
        did = e[0].split('~')[0]
        t, pal = convert(e, back_pal(did))
        im = to_rgba(t, pal); im.save(os.path.join(OUT, e[0] + '-f.png')); done.append((e, im))
        print('%-26s %-12s %2dx%-2d %s' % (e[0], e[1], im.width, im.height, e[4]))
    if a.install is not None:
        for name in a.install:
            did = name.split('~')[0]; dst = os.path.join(WEB, 'art', did + '-f.png')
            if os.path.exists(dst) and not a.force: print('있음, 건너뜀 (--force):', dst); continue
            Image.open(os.path.join(OUT, name + '-f.png')).save(dst); print('→', dst)
    if done:                                                          # 한눈에 보기: 칸마다 ×3 + 이름
        from PIL import ImageDraw
        cols = 6; s = 56 * 3 + 16; rows = (len(done) + cols - 1) // cols
        sh = Image.new('RGB', (cols * s, rows * (s + 14)), (232, 240, 232)); d = ImageDraw.Draw(sh)
        for i, (e, im) in enumerate(done):
            x, y = (i % cols) * s, (i // cols) * (s + 14); big = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
            sh.paste(big, (x + 8 + (168 - big.width) // 2, y + 14 + 168 - big.height), big); d.text((x + 6, y + 2), e[0], fill=(0, 0, 0))
        sh.save(os.path.join(OUT, '_rip_preview.png')); print('→', os.path.join(OUT, '_rip_preview.png'))


if __name__ == '__main__':
    main()
