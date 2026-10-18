#!/usr/bin/env python3
"""HG4 2단계(나): 데리고 다니는 디지몬 그림 — art_nds 의 ow.png 를 필드 그림(a/0/8/1, BTX0 「tsure_poke」)에 넣는다. (2026-10-14)
사용:   python hg4_follow.py "<HG4 아이콘까지 거친 롬.nds>" <nds_art 폴더> --base "<원본 디지골드 롬.nds>"
결과:   hg4f_out/hg4f_test.nds, hg4f_out/hg4f.bps, hg4f_out/report.txt
        hg4f_out/짝_확인.png   — 칸마다 [원본 전투 앞모습 | 짝지은 원본 필드 그림 아래 보기] (같은 생물이면 짝이 맞음)
        hg4f_out/넣은_그림.png — 새로 넣은 종마다 [넣은 필드 그림 8장]
- 10/14 집 보고: 케라몬(칸 132)을 데리고 다니면 이브이가 나옴 → 필드 그림은 전투 그림과 다른 파일이고 아무도 안 바꿨음.
- 칸 → 필드 그림 번호 짝: ① arm9·오버레이에서 「종 번호 순으로 1씩 늘어나는 표」를 찾고, ② 없으면 전투 그림 팔레트와 필드 그림 팔레트의
  색을 칸 순서대로 맞춰 봄(가운데 끼어 있는 암컷·폼 그림은 건너뛰며). 집 관찰(칸 1~3 → 296+칸, 4~25 → 297+칸, 26~134 → 298+칸)과 대조해 보고.
- 텍스처 8장 순서(집 보고 추정: 1·2 뒤, 3·4 앞, 5~8 옆): --order 로 바꿀 수 있음. 기본 up,up,down,down,left,left,right,right
- 디지골드 종(원래 디지몬)의 칸은 건드리지 않는다. 텍스처·팔레트는 제자리에 같은 크기로 덮어써서 파일 크기가 안 바뀜."""
import os, sys, re, csv, struct, argparse, colorsys, traceback, collections, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, bps_make, bps_apply, say, R
import art_nds
import hg2
try:
    import hg_scan
except Exception:
    hg_scan = None

def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def u32(d, o): return struct.unpack_from('<I', d, o)[0]

def btx_layout(d):
    """BTX0 → {'tex': [(이름, 너비, 높이, 형식, 절대 오프셋)], 'pal': [(이름, 절대 오프셋)]} 또는 None"""
    if d[:4] != b'BTX0': return None
    t = u32(d, 0x10)
    if d[t:t + 4] != b'TEX0': return None
    def dict_entries(off, esz):
        cnt = d[off + 1]; base = off + 16 + 4 * cnt
        ents = [d[base + esz * k: base + esz * (k + 1)] for k in range(cnt)]
        nb = base + esz * cnt
        names = [bytes(d[nb + 16 * k: nb + 16 * (k + 1)]).rstrip(bytes(1)).decode('latin1') for k in range(cnt)]
        return ents, names
    tex_data = t + u32(d, t + 0x14); pal_data = t + u32(d, t + 0x38)
    ti = t + u16(d, t + 0x0E); pi = t + u32(d, t + 0x34)
    ents, names = dict_entries(ti, 8)
    tex = []
    for e, nm in zip(ents, names):
        p = u32(e, 0)
        tex.append((nm, 8 << ((p >> 20) & 7), 8 << ((p >> 23) & 7), (p >> 26) & 7, tex_data + ((p & 0xFFFF) << 3)))
    pents, pnames = dict_entries(pi, 4)
    pal = [(nm, pal_data + (u16(e, 0) << 3)) for e, nm in zip(pents, pnames)]
    return {'tex': tex, 'pal': pal}

def tex_order(lay):
    """tsure_poke.1 … .8 를 숫자 순서로"""
    def num(nm):
        m = re.search(r'(\d+)$', nm); return int(m.group(1)) if m else 999
    return sorted(lay['tex'], key=lambda t: num(t[0]))

def read_pal(d, off, n=16):
    out = []
    for i in range(n):
        v = u16(d, off + 2 * i); out.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return out

def write_pal(d, off, cols):
    for i in range(16):
        r, g, b = cols[i] if i < len(cols) else (0, 0, 0)
        struct.pack_into('<H', d, off + 2 * i, (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))

def read_tex4(d, off, w, h):
    rows = []
    for y in range(h):
        r = []
        for x in range(0, w, 2):
            b = d[off + (y * w + x) // 2]; r += [b & 15, b >> 4]
        rows.append(r)
    return rows

def write_tex4(d, off, rows):
    h, w = len(rows), len(rows[0])
    for y in range(h):
        for x in range(0, w, 2):
            d[off + (y * w + x) // 2] = (rows[y][x] & 15) | ((rows[y][x + 1] & 15) << 4)

def is_follow(lay):
    return lay and len(lay['tex']) == 8 and all(t[0].startswith('tsure_poke') and t[3] == 3 and t[1] == t[2] and t[1] in (32, 64) for t in lay['tex']) and lay['pal']

LUT_SIG = bytes([0, 0, 0, 0, 1, 0, 2, 0, 4, 0, 5, 0, 6, 0, 7, 0])   # pret follow_mon.c sModelIndexLUT[494] 시작(10/15 조사): 파일 = 297 + 값, 암컷 그림이 따로면 +1
def find_lut(rom, nsp, members=None):
    # 10/16 진짜 롬 시험: 기준을 「첫 tsure_poke 파일」로 잡으면 진짜 롬은 201~206 에 따로 있는 특별 모형 6개 때문에 201 → 96칸씩 밀려 남의 종 그림을 덮음.
    #   기준 = 표의 모든 칸(1~493, 암컷 +1)이 tsure_poke 파일을 가리키는 번호. 297(pret·집 관찰)을 먼저 봄
    """arm9(압축 풀어서)에서 sModelIndexLUT 서명으로 칸→필드 그림 파일 번호 표. 암컷 그림이 따로 있는 칸은 두 파일 모두(값, 값+1)"""
    if hg_scan is None: return None, '서명 찾기 건너뜀(hg_scan 없음)'
    try: bins = hg_scan.binaries(rom)
    except Exception as ex: return None, '실행 파일 읽기 실패: %s' % ex
    hits = []
    for name, data in bins:
        a = data.find(LUT_SIG)
        while a >= 0:
            if a + 2 * 494 <= len(data):
                vals = [u16(data, a + 2 * k) for k in range(494)]
                if all(0 <= vals[k + 1] - vals[k] <= 30 for k in range(1, 493)) and vals[493] <= 900: hits.append((name, a, vals))   # 10/16 집 패치: ≤3 → ≤30
            a = data.find(LUT_SIG, a + 2)
    if not hits: return None, '서명 없음'
    name, a, vals = hits[0]
    mset = set(members or [])
    top = min(nsp, 493)
    def fits(b): return all((b + vals[s_]) in mset and (s_ == 493 or vals[s_ + 1] - vals[s_] < 2 or (b + vals[s_] + 1) in mset) for s_ in range(1, top + 1))
    first_file = next((b for b in [297] + sorted(mset) if fits(b)), None) if mset else 297
    if first_file is None: return None, '서명 표는 있으나 모든 칸이 데리고 다니는 그림을 가리키는 기준 번호가 없음(%s @0x%X)' % (name, a)
    mp = {}
    for s_ in range(1, min(nsp, 493) + 1):
        files = [first_file + vals[s_]]
        if s_ < 493 and vals[s_ + 1] - vals[s_] >= 2: files.append(first_file + vals[s_] + 1)      # 암컷(또는 폼) 그림
        mp[s_] = files
    return mp, '%s @0x%X (서명 %d곳, 파일 = %d + 표 값)' % (name, a, len(hits), first_file)

def find_table(rom, first, last, nsp):
    """arm9·오버레이(압축 풀어서)에서 종 번호 순 필드 그림 번호 표 찾기: 값이 first~last, 칸 1~nsp 동안 거의 1씩 늘어남"""
    if hg_scan is None: return None, '표 찾기 건너뜀(hg_scan 없음)'
    try: bins = hg_scan.binaries(rom)
    except Exception as ex: return None, '실행 파일 읽기 실패: %s' % ex
    found = []
    for name, data in bins:
        n = len(data)
        for stride in (2, 4, 6, 8, 12):
            lim = n - stride * (nsp + 1)
            for a in range(0, max(0, lim), 2):
                v1 = data[a + stride] | (data[a + stride + 1] << 8)
                if not (first - 4 <= v1 <= first + 4): continue
                v2 = data[a + 2 * stride] | (data[a + 2 * stride + 1] << 8)
                if not (0 <= v2 - v1 <= 3): continue
                vals = [u16(data, a + stride * k) for k in range(nsp + 1)]
                steps = [vals[k + 1] - vals[k] for k in range(1, nsp)]
                if min(steps) < 0 or max(steps) > 40: continue
                if sum(1 for x in steps if x == 1) < nsp * 0.8: continue
                if vals[-1] > last + 4: continue
                found.append((name, a, stride, vals))
                if len(found) > 6: break
    if not found: return None, '표 없음'
    if any(f[3] != found[0][3] for f in found):
        return None, '후보 %d개(서로 다름): %s' % (len(found), [(f[0], hex(f[1]), f[2]) for f in found[:6]])
    f = found[0]
    return {s_: f[3][s_] for s_ in range(1, nsp + 1)}, '%s @0x%X 칸 간격 %d' % (f[0], f[1], f[2])

def pal_cost(bp, fp):
    """전투 팔레트(bp)와 필드 팔레트(fp)의 색 차이 0~1: 필드 색마다 가장 가까운 전투 색까지 거리 평균"""
    fs = [c for c in fp[1:] if c != (0, 0, 0)] or fp[1:]
    bs = [c for c in bp[1:] if c != (0, 0, 0)] or bp[1:]
    if not fs or not bs: return 1.0
    tot = 0
    for c in fs: tot += min(((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2 + (c[2] - b[2]) ** 2) ** 0.5 for b in bs)
    return tot / len(fs) / 441.0

def align(bpals, members, fpals, nsp, maxskip=40, skip_pen=0.12, reach=110):
    """칸 1..nsp 를 필드 그림 순서(members)에 차례로 짝지음. 사이에 낀 그림(암컷·폼)은 건너뜀(벌점). → {칸: 번호}, 평균 비용"""
    M = len(members); INF = 1e18
    cost_cache = {}
    def cost(s_, j):
        k = (s_, j)
        if k not in cost_cache: cost_cache[k] = pal_cost(bpals.get(s_, [(0, 0, 0)] * 16), fpals[j])
        return cost_cache[k]
    prev = {}; backs = []
    for s_ in range(1, nsp + 1):
        cur = {}; bk = {}
        lo_j, hi_j = s_ - 1, min(M - 1, s_ - 1 + reach)
        for j in range(lo_j, hi_j + 1):
            if s_ == 1:
                if j > 20: break
                best, arg = 0.0, -1
            else:
                best, arg = INF, None
                for jp in range(j - 1, max(-1, j - 2 - maxskip), -1):
                    if jp in prev:
                        v = prev[jp] + skip_pen * (j - jp - 1)
                        if v < best: best, arg = v, jp
                if arg is None: continue
            cur[j] = best + cost(s_, j); bk[j] = arg
        if not cur: break
        backs.append(bk); prev = cur
    j = min(prev, key=prev.get); total = prev[j]; last = len(backs)
    mp = {}
    for s_ in range(last, 0, -1):
        mp[s_] = members[j]; j = backs[s_ - 1][j]
    return mp, total / max(1, last)

def rgba_sheet(path, blocks, cell_w, cell_h, cols):
    """blocks: [[(행 목록, 팔레트) 또는 None] 줄마다] → 색 있는 PNG(팔레트 256색 안으로)"""
    pal_all = {(255, 255, 255): 0, (200, 200, 210): 1}
    def ci(c):
        if c not in pal_all:
            if len(pal_all) >= 256: return min(pal_all.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[0], c)))[1]
            pal_all[c] = len(pal_all)
        return pal_all[c]
    sheet = []
    for row in blocks:
        rows = [[0] * (cell_w * cols) for _ in range(cell_h)]
        for k, blk in enumerate(row):
            if not blk: continue
            img, pal = blk
            for y in range(min(cell_h, len(img))):
                for x in range(min(cell_w, len(img[y]))):
                    v = img[y][x]
                    if v: rows[y][k * cell_w + x] = ci(pal[v])
            for y in range(cell_h): rows[y][k * cell_w + cell_w - 1] = 1
        sheet += rows
    pal = sorted(pal_all, key=pal_all.get)
    art_nds.png_write(path, sheet, pal + [(0, 0, 0)] * (256 - len(pal)), transparent0=False)

def read_ow(path):
    """art_nds ow.png(칸 2개 × 4줄: 아래·위·왼쪽·오른쪽) → {방향: [프레임0, 프레임1]}, 팔레트(0=투명)"""
    w, h, img = art_nds.png_read(path)
    cell = w // 2
    pal = {}; idx = []
    for r in img:
        row = []
        for p in r:
            if len(p) > 3 and p[3] < 128: row.append(0); continue
            c = tuple(p[:3])
            if c not in pal: pal[c] = len(pal) + 1
            row.append(pal[c])
        idx.append(row)
    cols = [(0, 0, 0)] + sorted(pal, key=pal.get)
    if len(cols) > 16: raise ValueError('걷기 그림 색이 15색 넘음(%d)' % (len(cols) - 1))
    fr = {}
    for k, dname in enumerate(('down', 'up', 'left', 'right')):
        fr[dname] = [[r[f * cell:(f + 1) * cell] for r in idx[k * cell:(k + 1) * cell]] for f in range(2)]
    return fr, cols, cell

def fit_cell(rows, size):
    """cell×cell → size×size: 크면 2배(가장 가까운 픽셀), 바닥 가운데 맞춤"""
    c = len(rows)
    if c == size: return rows
    k = max(1, size // c)
    big = [[v for v in r for _ in range(k)] for r in rows for _ in range(k)]
    out = [[0] * size for _ in range(size)]
    off_x = (size - len(big[0])) // 2; off_y = size - len(big)
    for y, r in enumerate(big):
        for x, v in enumerate(r):
            if 0 <= y + off_y < size and 0 <= x + off_x < size: out[y + off_y][x + off_x] = v
    return out

def battle_frames(folder, size):
    """10/16 집 보고 D12: 큰 필드 모형(텍스처 64 등)에 32칸 걷기 그림을 2배로 키우면 도트가 거침 → 전투 앞·뒷모습(front.png·back.png, 같은 팔레트)을 그 크기로 줄여 씀"""
    fp_, bp_ = os.path.join(folder, 'front.png'), os.path.join(folder, 'back.png')
    if not (os.path.exists(fp_) and os.path.exists(bp_)): return None
    imgs = []
    for pth in (fp_, bp_):
        w, h, img = art_nds.png_read(pth)
        b = art_nds.bbox(img)
        if not b: return None
        c = art_nds.crop(img, b)
        sc = art_nds.scale_to(c, size - 2, size - 2)
        imgs.append(art_nds.place(sc, size, size, bottom=1))
    pal = []
    for im in imgs:
        for r in im:
            for p in r:
                if len(p) > 3 and p[3] < 128: continue
                if tuple(p[:3]) not in pal: pal.append(tuple(p[:3]))
    if len(pal) > 15:                                      # 줄이며 섞인 색이 생기면 많이 쓴 15색으로
        cnt = collections.Counter(tuple(p[:3]) for im in imgs for r in im for p in r if not (len(p) > 3 and p[3] < 128))
        pal = [c for c, _ in cnt.most_common(15)]
    def near(c): return 1 + min(range(len(pal)), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], c)))
    idx = [[[0 if (len(p) > 3 and p[3] < 128) else near(p[:3]) for p in r] for r in im] for im in imgs]
    front, back = idx
    mirror = [list(reversed(r)) for r in front]
    return {'down': [front, front], 'up': [back, back], 'left': [front, front], 'right': [mirror, mirror]}, [(0, 0, 0)] + pal

def shiny(cols):
    out = []
    for i, (r, g, b) in enumerate(cols):
        if i == 0: out.append((r, g, b)); continue
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        r2, g2, b2 = colorsys.hls_to_rgb((h + 0.33) % 1.0, l, s)
        out.append((int(r2 * 255), int(g2 * 255), int(b2 * 255)))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('art'); ap.add_argument('--base', required=True); ap.add_argument('--out', default='hg4f_out')
    ap.add_argument('--order', default='up,up,down,down,left,left,right,right', help='텍스처 1~8 이 어느 방향인지(프레임은 0,1 순)')
    ap.add_argument('--map', choices=('auto', 'table', 'align', 'home'), default='auto', help='칸→필드 그림 짝 찾는 방법')
    ap.add_argument('--dry', action='store_true', help='짝 확인 그림만 만들고 롬은 안 씀')
    ap.add_argument('--bwg-src', type=int, default=257, help='블랙워그레이몬 필드 그림을 가져올 칸(디지골드 「워그레이몬」 두 번째 칸)')
    ap.add_argument('--draft', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw); base = NDS(open(A.base, 'rb').read())
    say('== HG4 2단계(나) 데리고 다니는 그림 — 롬', rom.code)
    draft = list(csv.DictReader(open(A.draft, encoding='utf-8'), delimiter=chr(9)))
    slot = {r['이름']: int(r['NDS 칸']) for r in draft if r['NDS 칸'].isdigit()}
    dg_names = {r['이름'] for r in draft if r['출처'] == '디지골드' and not r['NDS 칸'].isdigit()}
    if 'a/0/8/1' not in base.paths or 'a/0/8/1' not in rom.paths: raise SystemExit('실패: 롬에 필드 그림 묶음(a/0/8/1)이 없음 — 하트골드 구조 롬인지 확인')
    mm = NARC(base.get('a/0/8/1')); files_b = mm.files
    lays = {i: btx_layout(f) for i, f in enumerate(files_b)}
    members = [i for i in sorted(lays) if is_follow(lays[i])]
    say('필드 그림 파일 %d개 중 데리고 다니는 그림(tsure_poke, 텍스처 8장) %d개: %d ~ %d' % (len(files_b), len(members), members[0] if members else -1, members[-1] if members else -1))
    gra = NARC(base.get('a/0/0/4')).files; nsp = min(493, len(gra) // 6 - 1)
    bpals = {}; bfront = {}
    for s in range(1, nsp + 1):
        try:
            bpals[s] = hg1.nclr(gra[s * 6 + 4]) or [(0, 0, 0)] * 16
            rows, _m = hg1.ncgr_rows(gra[s * 6 + 3]); bfront[s] = [r[:80] for r in rows] if rows else None
        except Exception: bpals[s] = [(0, 0, 0)] * 16; bfront[s] = None
    fpals = [read_pal(files_b[m], lays[m]['pal'][0][1]) for m in members]
    # ---- 짝 찾기
    def home_rule(s):
        return (296 + s) if s <= 3 else (297 + s) if s <= 25 else (298 + s)
    mp, how = None, ''; extra_files = {}
    if A.map in ('auto', 'table', 'lut'):
        lut, why0 = find_lut(rom, nsp, members)
        say('짝 ⓪ arm9 서명 표(sModelIndexLUT):', why0)
        if lut:
            mp = {s_: v[0] for s_, v in lut.items()}; extra_files = {s_: v[1:] for s_, v in lut.items() if len(v) > 1}; how = '서명 표'
            say('  암컷·폼 그림이 따로 있어 두 파일에 넣는 칸 %d개' % len(extra_files))
    if mp is None and A.map in ('auto', 'table'):
        mp, why = find_table(rom, members[0] if members else 297, members[-1] if members else 900, nsp)
        say('짝 ① 실행 파일 속 표:', why)
        if mp: how = '표'
    if mp is None and A.map in ('auto', 'align'):
        mp, avg = align(bpals, members, fpals, nsp)
        how = '색 맞추기'; say('짝 ② 색 맞추기: 칸 %d개, 평균 색 차이 %.3f (0 에 가까울수록 잘 맞음)' % (len(mp), avg))
    if mp is None or A.map == 'home':
        mp = {s: home_rule(s) for s in range(1, min(nsp, 134) + 1)}; how = '집 관찰 규칙(칸 134까지만)'
    elif how == '색 맞추기':                              # 10/16 집 패치: 색 맞추기는 칸 4·25 를 한 칸 틀림(콩알몬이 피카츄) → 확인된 칸 1~134 는 집 규칙
        for s_ in range(1, 135):
            if s_ in mp: mp[s_] = home_rule(s_)
    agree = sum(1 for s in range(1, 135) if mp.get(s) == home_rule(s)); say('집 관찰 규칙(칸 1~134)과 같은 칸: %d/134' % agree)
    diffs = [(s, mp.get(s), home_rule(s)) for s in range(1, 135) if mp.get(s) != home_rule(s)]
    if diffs: say('  다른 칸(칸, 찾은 번호, 집 규칙): %s' % diffs[:20])
    # ---- 우리가 바꿀 칸
    targets = []; art_dir = {}
    grade_of = {r['이름']: r['단계'] for r in draft}
    for d in sorted(os.listdir(A.art)):
        m = re.match(r'\d+_(.+)$', d)
        if not m: continue
        name = m.group(1) if m.group(1) in slot else hg2.RENAME.get(m.group(1), m.group(1))
        if name in dg_names or name == '블랙워그레이몬' or name not in slot: continue
        owp = os.path.join(A.art, d, 'ow.png')
        if grade_of.get(name, '').startswith('유년기') and os.path.exists(os.path.join(A.art, '공용_알_걷기.png')):
            owp = os.path.join(A.art, '공용_알_걷기.png')      # 10/16 집 패치: 유년기는 공용 알(전에는 안 읽어서 원래 포켓몬이 남음)
        if os.path.exists(owp): targets.append((name, slot[name], owp))
        art_dir[name] = os.path.join(A.art, d)
    say('새로 넣을 종 %d (짝 방법: %s)' % (len(targets), how))
    # ---- 짝 확인 그림: 새로 넣을 칸 + 표본 칸
    sample = sorted({s for _, s, _ in targets} | set(range(1, nsp + 1, max(1, nsp // 40))))
    blocks = []
    for k in range(0, len(sample), 6):
        row = []
        for s in sample[k:k + 6]:
            fm = mp.get(s)
            row.append((bfront[s], bpals[s]) if bfront.get(s) else None)
            if fm is not None and fm in lays and is_follow(lays[fm]):
                tx = tex_order(lays[fm]); t = tx[2]
                img = read_tex4(files_b[fm], t[4], t[1], t[2])
                img = fit_cell(img, 80) if t[1] < 80 else img
                row.append((img, read_pal(files_b[fm], lays[fm]['pal'][0][1])))
            else: row.append(None)
        blocks.append(row)
    rgba_sheet(os.path.join(A.out, '짝_확인.png'), blocks, 80, 80, 12)
    say('짝_확인.png: 줄마다 [전투 앞 | 필드 그림] × 6칸, 칸 순서: %s' % ' '.join(map(str, sample)))
    if A.dry:
        open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n'); return
    # ---- 넣기
    order = [x.strip() for x in A.order.split(',')]
    if sorted(set(order)) != ['down', 'left', 'right', 'up'] or len(order) != 8: raise SystemExit('실패: --order 는 up/down/left/right 8개')
    cur = NARC(rom.get('a/0/8/1')); files = list(cur.files); n0 = len(files); sizes0 = [len(f) for f in files]
    problems = []; done = 0; shown = []; ins = []
    def put_into(fm2, name, owp, frs):
        lay = btx_layout(files[fm2])
        if not is_follow(lay): problems.append('짝 파일이 데리고 다니는 그림이 아님: %s → %d' % (name, fm2)); return None
        fr, cols, cell = frs
        big = max(t[1] for t in tex_order(lay))
        how_ = '걷기'
        if big > cell and name in art_dir:
            bf = battle_frames(art_dir[name], big)
            if bf: fr, cols = bf; how_ = '전투 그림(큰 모형 %d)' % big
        d = bytearray(files[fm2]); used = collections.Counter(); imgs = []
        for t, dname in zip(tex_order(lay), order):
            f_i = used[dname]; used[dname] += 1
            img = fit_cell(fr[dname][f_i % 2], t[1])
            write_tex4(d, t[4], img); imgs.append(img)
        write_pal(d, lay['pal'][0][1], cols)
        if len(lay['pal']) > 1: write_pal(d, lay['pal'][1][1], shiny(cols))
        if len(d) != len(files[fm2]): problems.append('크기 바뀜: %s' % name); return None
        files[fm2] = bytes(d)
        return imgs, cols, how_
    owp_of = {}
    for name, s, owp in targets:
        fm = mp.get(s)
        if fm is None or fm >= len(files): problems.append('짝 없음: %s 칸 %d' % (name, s)); continue
        try:
            frs = read_ow(owp)
        except Exception as ex:
            problems.append('걷기 그림 못 읽음: %s %s' % (name, ex)); continue
        owp_of[name] = (owp, frs)
        ok_any = False
        for fm2 in [fm] + [x for x in extra_files.get(s, []) if x < len(files)]:     # 암컷·폼 그림 파일에도 같은 그림(안 넣으면 그 성별만 포켓몬이 남음)
            r_ = put_into(fm2, name, owp, frs)
            if r_ and not ok_any:
                done += 1; shown.append((name, r_[0], r_[1])); ok_any = True; ins.append((name, s, fm2, r_[2]))
    # 10/16 블랙워그레이몬(칸 109): 두 번째 「워그레이몬」 칸(디지골드 검은 워그레이몬 그림을 쓰는 칸)의 필드 그림 복사 + 보통·색다른 색 맞바꿈(전투 그림과 같게 검정이 보통 색)
    bw_, wg2_ = slot.get('블랙워그레이몬'), A.bwg_src
    if bw_ is not None and mp.get(bw_) is not None and mp.get(wg2_) is not None:
        a_, b_ = mp[bw_], mp[wg2_]
        lay_b = btx_layout(files_b[b_])
        if len(files[a_]) == len(files_b[b_]) and is_follow(lay_b) and len(lay_b['pal']) == 2:
            dd = bytearray(files_b[b_]); o0, o1 = lay_b['pal'][0][1], lay_b['pal'][1][1]
            p0, p1 = bytes(dd[o0:o0 + 32]), bytes(dd[o1:o1 + 32]); dd[o0:o0 + 32], dd[o1:o1 + 32] = p1, p0
            files[a_] = bytes(dd); say('블랙워그레이몬 따라다니는 그림: 칸 %d(파일 %d) ← 칸 %d(파일 %d) 복사 + 보통·색다른 색 맞바꿈' % (bw_, a_, wg2_, b_)); ins.append(('블랙워그레이몬', bw_, a_, '복사'))
        else: problems.append('블랙워그레이몬 따라다니는 그림 복사 못 함: 크기·형식 다름')
    # 10/16 집 보고 D5: 고정·심볼 디지몬의 지도 위 모습(전룡·프리져 등)은 원래 포켓몬 칸의 필드 그림을 씀 → 이벤트표의 원래 번호 칸 파일에 우리 종 그림
    ev_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_이벤트표.tsv')
    mapfix = []
    if os.path.exists(ev_p):
        for r in csv.DictReader((l for l in open(ev_p, encoding='utf-8') if not l.startswith('#')), delimiter=chr(9)):
            kind, num, ours_ = (r.get('종류') or '').strip(), (r.get('번호') or '').strip(), (r.get('우리 종') or '').strip()
            if kind not in ('고정', '심볼', '떠돌이', '추적', '맵그림') or not num.isdigit() or ours_ not in owp_of: continue
            n_ = int(num)
            if n_ == slot.get(ours_) or mp.get(n_) is None: continue
            for fm2 in [mp[n_]] + list(extra_files.get(n_, [])):
                if fm2 < len(files) and put_into(fm2, ours_, *owp_of[ours_]): mapfix.append('%s(칸 %d 파일 %d) ← %s' % (r.get('하트골드 원래', ''), n_, fm2, ours_))
    say('지도 위 고정·심볼 모습 바꿈 %d: %s' % (len(mapfix), '; '.join(mapfix[:40])))
    if len(files) != n0 or [len(f) for f in files] != sizes0: raise SystemExit('실패: 필드 그림 파일 수·크기가 바뀜 — 롬을 쓰지 않음')
    cur.files = files; out = NDS(raw); out.put('a/0/8/1', cur.build()); new_raw = bytes(out.d)
    # 검산: 다시 읽어 넣은 픽셀·팔레트 대조
    chk = NARC(NDS(new_raw).get('a/0/8/1')).files; bad = 0
    for name, s, owp in targets:
        fm = mp.get(s)
        if fm is None or fm >= len(chk): continue
        lay = btx_layout(chk[fm])
        if not is_follow(lay): continue
        if chk[fm] != files[fm]: bad += 1
    say('데리고 다니는 그림 넣음: %d종, 검산 실패 %d' % (done, bad))
    got_ = {n for n, _, _, _ in ins}
    miss_ = [n for n, s_ in sorted(slot.items(), key=lambda kv: kv[1]) if n not in got_ and n not in dg_names]
    with open(os.path.join(A.out, '넣은_종.tsv'), 'w', encoding='utf-8') as fo:
        fo.write('이름' + chr(9) + '칸' + chr(9) + '필드 파일' + chr(9) + '그림' + chr(10))
        for x in ins: fo.write(chr(9).join(str(v) for v in x) + chr(10))
    say('따라다니는 그림이 빠진 종 %d: %s' % (len(miss_), ' '.join(miss_[:60])))
    blocks = []
    for k in range(0, len(shown), 2):
        row = []
        for name, imgs, cols in shown[k:k + 2]:
            row += [(fit_cell(im, 64) if len(im) < 64 else im, cols) for im in imgs]
        blocks.append(row)
    if blocks: rgba_sheet(os.path.join(A.out, '넣은_그림.png'), blocks, 64, 64, 16)
    say('넣은_그림.png: 줄마다 두 종 × 텍스처 8장(순서 %s)' % A.order)
    open(os.path.join(A.out, 'hg4f_test.nds'), 'wb').write(new_raw)
    braw = open(A.base, 'rb').read(); patch = bps_make(braw, new_raw); open(os.path.join(A.out, 'hg4f.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(braw, patch) == new_raw else '실패'))
    say('\n== 문제 %d건' % len(problems)); [say('-', x) for x in problems[:100]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
