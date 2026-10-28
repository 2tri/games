#!/usr/bin/env python3
"""python inject_npc_walks.py <입력 롬> <출력 롬> [--preview 폴더] — 2부 인물 필드 걷기 그림 넣기 (2026-10-28, 사용자가 제미나이로 뽑아 준 시트)
롬 구조(에뮬·파싱 확인): 필드 사람 그림 = a/0/8/1 의 BTX0 파일, 32x32 텍스처 16장(공유 포함 12장) + 16색 팔레트 1개.
  스프라이트 번호(SPRITE_x)와 파일 번호는 같은 이름끼리 짝(pret include/constants/sprites.h ↔ mmodel.h): GSLEADER9 → 162 …
  텍스처 이름 x.1~4 = 위, 5~8 = 아래, 9~12 = 왼쪽, 13~16 = 오른쪽 · 방향마다 [서기, 걸음1, 서기, 걸음2] (1·3 이 같은 그림을 가리킴).
시트: games/digimon/art/src/people/*_walk_ds_ai.png (제미나이). 3열×4행(앞·뒤·옆·옆) 또는 매튜 5열×3행. 옆모습은 둘 다 오른쪽을 봐서 왼쪽은 거울.
여러 번 돌려도 같은 결과."""
import sys, os, struct, math, collections, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC
from PIL import Image, ImageOps
PEOPLE = os.path.join(ROOT, 'games', 'digimon', 'art', 'src', 'people')

# 이름, 시트, (열, 행), 높이(px), 파일 번호들, (프레임 고르기: 앞/뒤/옆 줄의 [서기, 걸음1, 걸음2] 열 번호)
CAST = [
    dict(name='산해', sheet='daisuke_walk_ds_ai.png', grid=(3, 4), members=[162]),
    dict(name='예지', sheet='miyako_walk_ds_ai.png', grid=(3, 4), members=[164]),
    dict(name='재하', sheet='iori_walk_ds_ai.png', grid=(3, 4), members=[166]),
    dict(name='정우', sheet='ken_walk_ds_ai.png', grid=(3, 4), body_w=0.85, members=[215]),            # 시눈 관장 모델(쓰이는 곳 없음) 자리
    dict(name='마일도', sheet='mildo_walk_ds_ai.png', grid=(3, 4), body_w=0.8, members=[170]),         # RED 자리(마일도 오브젝트)
    dict(name='매튜', sheet='yamato_walk_ds_ai.png', grid=(5, 3), members=[58], cols=(0, 1, 4)),   # GSRIVEL = 라이벌 전부
    dict(name='리키', sheet='takeru_walk_ds_ai.png', grid=(3, 4), members=[153, 169]),     # 1부·2부 8번째 수호자
    dict(name='겐나이', sheet='gennai_ai.png', grid=(2, 3), body_w=0.85, members=[54, 160], cols=(0, 1, 1), side='left'),   # DOCTOR(시작의 마을·연구소) · OOKIDO(관동 연구소·항구 터미널)
]
# 말하는 사람과 모습이 안 맞던 곳(스크립트로 확인): (이벤트 파일, 오브젝트 번호, 옛 그림, 새 그림)
OBJECT_FIXES = [(460, 5, 327, 126),      # 지도508 화산 섬: 「정우:」 대사를 하던 여자 NPC → 카이저 그림
                (441, 2, 338, 370)]      # 지도489 발전기 방: 「예지:」 대사를 하던 남자 조수 → 예지 그림(GSLEADER11)
# 디지몬 수호자 4명: 사람 관장 그림 → 디지골드 v1.6 이 이미 그려 둔 「데리고 걷기」 디지몬 그림(SPRITE_FOLLOWER_MON_종, pret sprites.h)
# 종 칸: 엔젤우몬=286(BRELOOM) · 릴리몬=276(TAILLOW) · 쥬드몬=260(SWAMPERT) · 스팅몬=269(DUSTOX). 모든 지도의 해당 오브젝트(수련장·재전 장소 등 12곳)
SPRITE_SWAP = {369: 747,     # GSLEADER10 → 엔젤우몬
               371: 737,     # GSLEADER12 → 릴리몬
               373: 721,     # GSLEADER14 → 쥬드몬
               374: 730}     # GSLEADER15 → 스팅몬

def is_bg(p): return max(p) - min(p) <= 30 and min(p) >= 105

def grid_bounds(im, n, axis):
    """격자선(어두운 줄, 길이의 80% 이상이 검정)을 찾아 칸 경계로. 못 찾으면 같은 간격."""
    W, H = im.size; px = im.load(); L = W if axis == 0 else H; other = H if axis == 0 else W; hits = []
    for a in range(L):
        dark = 0; tot = 0
        for b in range(0, other, 4):
            p = px[a, b] if axis == 0 else px[b, a]; tot += 1; dark += max(p) < 70
        if dark > tot * 0.8: hits.append(a)
    groups = []
    for a in hits:
        if groups and a - groups[-1][-1] <= 3: groups[-1].append(a)
        else: groups.append([a])
    inner = [(g[0] + g[-1]) / 2 for g in groups if 6 < g[0] < L - 6]
    if len(inner) == n - 1: return [0] + inner + [L]
    return [L * k / n for k in range(n + 1)]

def cell_cut(im, bx, by, c, r, margin=3):
    box = (int(bx[c]) + margin, int(by[r]) + margin, int(bx[c + 1]) - margin, int(by[r + 1]) - margin)
    cell = im.crop(box).convert('RGB'); w, h = cell.size; px = cell.load()
    mask = Image.new('L', (w, h), 255); mp = mask.load(); seen = bytearray(w * h)
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y * w + x] or not is_bg(px[x, y]): continue
        seen[y * w + x] = 1; mp[x, y] = 0
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    # 가장 큰 덩어리와 그 3% 이상인 덩어리만 남김(격자 찌꺼기·점 지움)
    lab = [0] * (w * h); comps = []
    for y0 in range(h):
        for x0 in range(w):
            if mp[x0, y0] and not lab[y0 * w + x0]:
                k = len(comps) + 1; st = [(x0, y0)]; lab[y0 * w + x0] = k; n = 0
                while st:
                    x, y = st.pop(); n += 1
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and mp[nx, ny] and not lab[ny * w + nx]: lab[ny * w + nx] = k; st.append((nx, ny))
                comps.append(n)
    assert comps, '칸에서 그림을 못 찾음'
    keep = {k + 1 for k, n in enumerate(comps) if n >= 0.03 * max(comps)}
    for y in range(h):
        for x in range(w):
            if mp[x, y] and lab[y * w + x] not in keep: mp[x, y] = 0
    rgba = cell.convert('RGBA'); rgba.putalpha(mask)
    return rgba.crop(rgba.getbbox())

def build_frames(cfg):
    im = Image.open(os.path.join(PEOPLE, cfg['sheet'])).convert('RGB'); gc, gr = cfg['grid']
    bx = grid_bounds(im, gc, 0); by = grid_bounds(im, gr, 1); cols = cfg.get('cols', (0, 1, 2))
    if gr == 4: rows = {'down': 0, 'up': 1, 'right': 2, 'left': 3}          # 옆 두 줄 모두 오른쪽 → 왼쪽은 아래 줄을 뒤집어 씀
    else: rows = {'down': 0, 'up': 1, 'right': 2, 'left': 2}
    flipped = 'right' if cfg.get('side') == 'left' else 'left'                # 옆모습 한 줄: 보는 쪽 반대는 거울
    if gr == 3: rows = {'down': 0, 'up': 1, 'left': 2, 'right': 2}
    fr = {}
    for d, r in rows.items():
        fr[d] = [cell_cut(im, bx, by, c, r) for c in cols]
        if d == flipped and (gr == 3 or d == 'left'): fr[d] = [ImageOps.mirror(f) for f in fr[d]]
    return fr

def palette_from(fr):
    hist = collections.Counter()
    for v in fr.values():
        for f in v:
            px = f.load(); w, h = f.size
            for y in range(0, h, 2):
                for x in range(0, w, 2):
                    if px[x, y][3] >= 128: hist[px[x, y][:3]] += 1
    strip = []
    for col, n in hist.items(): strip += [col] * max(1, int(n ** 0.8))              # 면적 비중 0.8제곱(옷과 살색이 안 섞이게)
    sw = 128; sh = (len(strip) + sw - 1) // sw
    simg = Image.new('RGB', (sw, sh), (0, 0, 0)); simg.putdata(strip + [strip[0]] * (sw * sh - len(strip)))
    pq = simg.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pp = pq.getpalette()[:45]
    return [tuple(pp[i * 3:i * 3 + 3]) for i in range(15)]

def to_indexed(f, cols):
    """원본 크기 컷을 팔레트 번호(1~15, 투명 0) 판으로"""
    w, h = f.size; px = f.load(); cache = {}
    def nearest(c):
        if c not in cache: cache[c] = 1 + min(range(15), key=lambda i: (c[0] - cols[i][0]) ** 2 + (c[1] - cols[i][1]) ** 2 + (c[2] - cols[i][2]) ** 2)
        return cache[c]
    return [[nearest(px[x, y][:3]) if px[x, y][3] >= 128 else 0 for x in range(w)] for y in range(h)]

def shrink(idx, w, h, tw, th, outline):
    """블록마다 가장 많은 색을 고르되 윤곽선(가장 어두운 색)이 30% 이상이면 윤곽선"""
    out = [[0] * tw for _ in range(th)]
    for ty in range(th):
        y0, y1 = int(ty * h / th), max(int(ty * h / th) + 1, int((ty + 1) * h / th))
        for tx in range(tw):
            x0, x1 = int(tx * w / tw), max(int(tx * w / tw) + 1, int((tx + 1) * w / tw)); c = collections.Counter(); n = 0
            for y in range(y0, y1):
                row = idx[y]
                for x in range(x0, x1): c[row[x]] += 1; n += 1
            op = n - c[0]
            if op < 0.45 * n: continue
            if c[outline] >= 0.30 * op: out[ty][tx] = outline
            else:
                c.pop(0, None); c.pop(outline, None)
                out[ty][tx] = max(c, key=c.get) if c else outline
    return out

def neck_frac(f):
    """서 있는 앞모습에서 목(머리 아래 가장 좁은 줄)의 높이 비율"""
    a = f.getchannel('A').load(); w, h = f.size
    prof = [sum(1 for x in range(w) if a[x, y]) for y in range(h)]
    return min(range(int(h * .25), int(h * .5)), key=lambda y: prof[y]) / h

# 10/28 사용자 「게임 안 인물은 대두 2등신인데 겉돈다」: 시트를 통째로 줄이면 3등신 그대로라 원래 NPC(머리 14줄·몸 10줄·발 29줄, 굵은 테두리)와 안 맞음.
# → 목에서 잘라 머리·몸을 따로 줄여 원래 NPC 비율로 맞춘다. 칸 안 줄 번호는 원래 NPC(파일 10·30 등)를 잰 값.
HEAD_ROWS, BODY_ROWS, FOOT = 13, 9, 28          # 테두리 안쪽 줄 수, 몸 마지막 줄(테두리는 29줄)
CX = 16                                          # 원래 NPC 가운데 x

def cut_part(f, y0, y1):
    p = f.crop((0, y0, f.width, y1)); bb = p.getchannel('A').getbbox()
    return p.crop(bb), bb

def chibi_tile(f, nf, cols, outline, body_w):
    w, h = f.size; ny = round(h * nf)
    head, hb = cut_part(f, 0, ny); body, bb = cut_part(f, ny, h)
    s = HEAD_ROWS / head.height                                           # 머리는 비율 그대로
    hw = min(22, max(1, round(head.width * s))); bw = min(26, max(1, round(body.width * s * body_w)))
    hi = shrink(to_indexed(head, cols), head.width, head.height, hw, HEAD_ROWS, outline)
    bi = shrink(to_indexed(body, cols), body.width, body.height, bw, BODY_ROWS, outline)
    tile = [[0] * 32 for _ in range(32)]
    hcx = (hb[0] + hb[2]) / 2; bcx = (bb[0] + bb[2]) / 2; mid = (hcx * head.width + bcx * body.width) / (head.width + body.width)
    def put(part, pw, ph, cx, top):
        ox = round(CX + (cx - mid) * s - pw / 2)
        for y in range(ph):
            for x in range(pw):
                if part[y][x] and 0 <= ox + x < 32: tile[top + y][ox + x] = part[y][x]
    put(bi, bw, BODY_ROWS, bcx, FOOT - BODY_ROWS + 1)
    put(hi, hw, HEAD_ROWS, hcx, FOOT - BODY_ROWS + 1 - HEAD_ROWS)
    # 바깥 테두리: 투명과 닿은 윤곽선 점을 걷고 바깥에 1칸 새로 두른다(원래 NPC처럼 굵고 고르게)
    edge = lambda x, y: any(not (0 <= x + dx < 32 and 0 <= y + dy < 32) or not tile[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    for y, x in [(y, x) for y in range(32) for x in range(32) if tile[y][x] == outline and edge(x, y)]: tile[y][x] = 0
    add = [(y, x) for y in range(32) for x in range(32) if not tile[y][x] and any(0 <= x + dx < 32 and 0 <= y + dy < 32 and tile[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for y, x in add: tile[y][x] = outline
    return tile

def build_indexed(cfg):
    fr = build_frames(cfg); cols = palette_from(fr)
    outline = 1 + min(range(15), key=lambda i: sum(cols[i]))
    nf = cfg.get('neck') or neck_frac(fr['down'][0])
    idx = {d: [chibi_tile(f, nf, cols, outline, cfg.get('body_w', 1.0)) for f in v] for d, v in fr.items()}
    return cols, idx

def bgr555(c): return (c[0] >> 3) | ((c[1] >> 3) << 5) | ((c[2] >> 3) << 10)

def btx_layout(buf):
    t = struct.unpack_from('<I', buf, 0x10)[0]; assert buf[t:t + 4] == b'TEX0'
    def d3(o):
        n = buf[o + 1]; p = o + 8 + (n + 1) * 4; esz, blk = struct.unpack_from('<HH', buf, p); p += 4
        ents = [bytes(buf[p + i * esz:p + (i + 1) * esz]) for i in range(n)]; p += n * esz
        return ents, [bytes(buf[p + i * 16:p + (i + 1) * 16]).rstrip(b'\0').decode('latin1') for i in range(n)]
    texdata = struct.unpack_from('<I', buf, t + 0x14)[0]; paldata = struct.unpack_from('<I', buf, t + 0x38)[0]
    te, tn = d3(t + struct.unpack_from('<H', buf, t + 0x0E)[0]); pe, pn = d3(t + struct.unpack_from('<I', buf, t + 0x34)[0])
    assert len(tn) == 16 and len(pn) == 1, (len(tn), len(pn))
    tex = {int(nm.split('.')[-1]): t + texdata + (struct.unpack_from('<H', e, 0)[0] << 3) for e, nm in zip(te, tn)}
    return tex, t + paldata + (struct.unpack_from('<H', pe[0], 0)[0] << 3)

def write_member(buf, cols, idx):
    buf = bytearray(buf); tex, pal = btx_layout(buf)
    struct.pack_into('<H', buf, pal, 0)
    for i, col in enumerate(cols): struct.pack_into('<H', buf, pal + 2 * (1 + i), bgr555(col))
    ORDER = [0, 1, 0, 2]
    for d, b0 in {'up': 1, 'down': 5, 'left': 9, 'right': 13}.items():
        for k in range(4):
            rows = idx[d][ORDER[k]]; o = tex[b0 + k]
            for y in range(32):
                for x in range(0, 32, 2): buf[o + y * 16 + x // 2] = rows[y][x] | (rows[y][x + 1] << 4)
    return bytes(buf)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out'); ap.add_argument('--preview', default=None); A = ap.parse_args()
    rom = NDS(open(A.rom, 'rb').read()); nar = NARC(rom.get('a/0/8/1')); files = list(nar.files); done = []
    for cfg in CAST:
        cols, idx = build_indexed(cfg)
        for m in cfg['members']: files[m] = write_member(files[m], cols, idx)
        done.append('%s → 파일 %s' % (cfg['name'], cfg['members']))
        if A.preview:
            os.makedirs(A.preview, exist_ok=True)
            pv = Image.new('RGB', (4 * 34, 4 * 34), (200, 200, 200)); pp = pv.load()
            for r, d in enumerate(('up', 'down', 'left', 'right')):
                for k in range(4):
                    rows = idx[d][[0, 1, 0, 2][k]]
                    for y in range(32):
                        for x in range(32):
                            if rows[y][x]: pp[k * 34 + 1 + x, r * 34 + 1 + y] = cols[rows[y][x] - 1]
            pv.resize((pv.width * 3, pv.height * 3), Image.NEAREST).save(os.path.join(A.preview, '걷기_%s.png' % cfg['name']))
    nar.files = files; rom.put('a/0/8/1', nar.build())
    ev = NARC(rom.get(hg1.NARC_PATHS['zone_event'])); EV = list(ev.files); changed = False
    for ei, oi, old, new in OBJECT_FIXES:
        g = bytearray(EV[ei]); o = 4 + 20 * struct.unpack_from('<I', g, 0)[0]; o += 4
        cur = struct.unpack_from('<H', g, o + 32 * oi + 2)[0]
        assert cur in (old, new), '이벤트 %d 오브젝트 %d 그림이 예상과 다름: %d' % (ei, oi, cur)
        if cur != new: struct.pack_into('<H', g, o + 32 * oi + 2, new); EV[ei] = bytes(g); changed = True; done.append('이벤트 %d 오브젝트 %d 그림 %d → %d' % (ei, oi, old, new))
    sw = 0
    for ei, f in enumerate(EV):
        if len(f) < 8: continue
        g = bytearray(f); o = 4 + 20 * struct.unpack_from('<I', g, 0)[0]; n = struct.unpack_from('<I', g, o)[0]; o += 4
        for i in range(n):
            cur = struct.unpack_from('<H', g, o + 32 * i + 2)[0]
            if cur in SPRITE_SWAP: struct.pack_into('<H', g, o + 32 * i + 2, SPRITE_SWAP[cur]); sw += 1
        if bytes(g) != f: EV[ei] = bytes(g); changed = True
    if sw: done.append('디지몬 수호자 4명 오브젝트 %d곳 → 디지몬 그림' % sw)
    if changed: ev.files = EV; rom.put(hg1.NARC_PATHS['zone_event'], ev.build())
    open(A.out, 'wb').write(bytes(rom.d))
    for d in done: print(' -', d)
    print('인물 걷기 그림 %d명' % len(done))
