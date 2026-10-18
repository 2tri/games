#!/usr/bin/env python3
"""HG4 (1단계: 전투 그림) — art_nds.py 가 만든 front.png·back.png(80x80, 16색)를 새 종의 전투 그림으로 롬에 넣는다. (2026-10-08, 가짜 롬으로만 시험)
사용:   python hg4.py "<HG3 까지 거친 롬.nds>" <nds_art 폴더> [--base "<원본 디지골드 롬.nds>"]
결과:   hg4_out/hg4_test.nds, hg4_out/hg4.bps, hg4_out/report.txt
- 전투 그림 NARC(a/0/0/4): 종마다 6파일 [암컷 뒤, 수컷 뒤, 암컷 앞, 수컷 앞, 보통 색, 색다른 색] 으로 본다(HG1 의 front_sheet 로 확인할 것).
- 그림 파일은 같은 칸의 원래 파일을 틀로 써서 머리말은 그대로 두고, 픽셀(160x80 = 두 장면, 둘 다 같은 그림)만 하트골드식(앞에서부터, dp)으로 암호화해 바꾼다.
- 색다른 색은 보통 색에서 색상을 돌려 자동으로 만든다.
- 블랙워그레이몬(109칸): 디지골드의 검은 워그레이몬 그림을 복사한다. 이름이 「워그레이몬」인 칸이 둘이면 두 번째 칸 6파일을 통째로,
  하나뿐이면(검은 것이 색다른 색) 워그레이몬 그림을 복사하고 보통 색·색다른 색을 맞바꾼다. 어느 쪽이었는지 보고서에 남긴다.
- 아이콘·걷기 그림·트레이너 그림은 2단계(HG1 결과로 형식을 확인한 뒤).
- 쓰고 나서 다시 풀어 원래 그림과 한 픽셀씩 대조한다(색 번호 + 롬 팔레트로 칠한 색).
- 10/14: 뒷모습 색 번호를 색 기준으로 언제나 바꿈, 그림 바닥 줄을 같은 칸 원래 그림 바닥 줄에 맞춤(너무 크면 줄임)."""
import os, sys, re, csv, struct, argparse, random, colorsys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC, bps_make, bps_apply, say, R
import art_nds
import hg2


def encrypt_dp(words, seed):
    """하트골드·디지골드 전투 그림식(hg1 의 'dp'): 앞에서부터 LCG 키를 xor. 첫 암호 단어 = 씨앗이므로 첫 평문 단어는 0 이어야 한다(집 보고 10/12: 원본 1808/1812, 디지골드 1972/1976 이 dp)."""
    v = list(words); assert v[0] == 0, '첫 픽셀 단어가 0 이 아님(왼쪽 위 4픽셀이 투명해야 함)'
    out = []; s = seed
    for w in v:
        out.append(w ^ (s & 0xFFFF)); s = (s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
    return out

def encrypt_pt(words, seed):
    """플래티넘·하트골드식: 끝에서부터 LCG 키를 xor. 풀 때는 마지막 암호 단어를 씨앗으로 쓰므로, 마지막 평문 단어는 0 이어야 한다."""
    v = list(words); n = len(v)
    assert v[-1] == 0, '마지막 픽셀 단어가 0 이 아님(오른쪽 아래 4픽셀이 투명해야 함)'
    out = [0] * n; s = seed
    for i in range(n - 1, -1, -1):
        out[i] = v[i] ^ (s & 0xFFFF); s = (s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
    return out

def ncgr_with_pixels(template, rows80):
    """틀 NCGR 의 RAHC 픽셀 6400바이트를 rows80(80x80 색 번호)을 두 장면으로 이은 그림으로 바꿈"""
    c = template.find(b'RAHC')
    if c < 0: raise ValueError('틀에 RAHC 없음')
    rows = [r + r for r in rows80]                         # 160x80: 왼쪽·오른쪽 장면 같게
    px = []
    for r in rows: px += r
    px[:4] = [0, 0, 0, 0]                                  # dp: 첫 평문 단어 = 0 → 왼쪽 위 4픽셀은 투명
    b = bytes(px[i] | (px[i + 1] << 4) for i in range(0, len(px), 2))
    words = list(struct.unpack('<3200H', b))
    if words[0] != 0: raise ValueError('왼쪽 위가 투명이 아님')
    enc = encrypt_dp(words, random.randint(1, 0xFFFF))
    data = bytearray(template)
    data[c + 0x20:c + 0x20 + 6400] = struct.pack('<3200H', *enc)
    return bytes(data)

def nclr_with_colors(template, cols):
    c = template.find(b'TTLP')
    if c < 0: raise ValueError('틀에 TTLP 없음')
    data = bytearray(template)
    for i in range(16):
        r, g, b = cols[i] if i < len(cols) else (0, 0, 0)
        struct.pack_into('<H', data, c + 0x18 + 2 * i, (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10))
    return bytes(data)

def shiny(cols):
    out = []
    for i, (r, g, b) in enumerate(cols):
        if i == 0: out.append((r, g, b)); continue
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        r2, g2, b2 = colorsys.hls_to_rgb((h + 0.33) % 1.0, l, s)
        out.append((int(r2 * 255), int(g2 * 255), int(b2 * 255)))
    return out

def read_indexed(path):
    """art_nds 가 쓴 16색 PNG → (80행 색 번호, 팔레트)"""
    w, h, img = art_nds.png_read(path)
    pal = {}; rows = []
    for r in img:
        row = []
        for p in r:
            if p[3] == 0: row.append(0); continue
            if p[:3] not in pal: pal[p[:3]] = len(pal) + 1
            row.append(pal[p[:3]])
        rows.append(row)
    cols = [(0, 0, 0)] + sorted(pal, key=pal.get)
    return rows, cols

def opaque_box(rows, w=80):
    """색 번호 0 이 아닌 픽셀의 (위, 아래, 왼쪽, 오른쪽). 없으면 None"""
    ys = [y for y, r in enumerate(rows) if any(v for v in r[:w])]
    if not ys: return None
    xs = [x for r in rows for x, v in enumerate(r[:w]) if v]
    return ys[0], ys[-1], min(xs), max(xs)

FLOOR = 48          # 원래 그림 바닥 줄이 이보다 위면 이 줄에 맞춤(아주 작은 원래 그림 때문에 새 그림이 너무 작아지지 않게)

def fit_bottom(rows, target, top=1):
    """그림의 맨 아래 줄을 target 줄에 맞춤(집 보고 10/14: 새 그림 바닥 78줄 → 원래 그림 바닥 51~66줄이라 이름판에 가림).
    위로 올리면 머리가 잘릴 만큼 크면 가운데를 지키며 줄인다(가장 가까운 픽셀). → (새 80x80, 설명)"""
    box = opaque_box(rows)
    if box is None: return rows, '빈 그림'
    t, b, l, r = box; target = max(min(target, 79), FLOOR)
    h, w = b - t + 1, r - l + 1; avail = target - top + 1
    out = [[0] * 80 for _ in range(80)]
    if h <= avail:
        d = target - b
        for y in range(t, b + 1):
            out[y + d][:80] = list(rows[y][:80])
        return out, ('그대로' if d == 0 else '%+d줄' % (-d))
    f = avail / h; nh = avail; nw = max(1, int(round(w * f)))
    cx = (l + r) / 2.0; x0 = int(round(cx - (nw - 1) / 2.0)); x0 = max(0, min(80 - nw, x0))
    for yy in range(nh):
        sy = t + min(h - 1, int((yy + 0.5) / f))
        for xx in range(nw):
            sx = l + min(w - 1, int((xx + 0.5) / f))
            out[target - nh + 1 + yy][x0 + xx] = rows[sy][sx]
    return out, '줄임 %d%%' % round(f * 100)

def q5(c): return tuple(((v >> 3) & 31) * 255 // 31 for v in c)

EGG_SLOTS = (494, 495)      # 하트골드 전투 그림 NARC 의 알 그림 칸(494 = 보통 알, 495 = 마나피 알). 폰 확인으로 맞는지 봄(10/14)

def digitama(seed=0):
    """디지타마(디지몬 알) 80x80 색 번호 그림 + 팔레트(0 투명). 주황 바탕에 흰 물결무늬 띠 두 줄·검은 테두리(10/14 사용자: 물결무늬)"""
    import math
    pal = [(0, 0, 0), (40, 32, 32), (248, 160, 48), (255, 208, 96), (255, 248, 224), (200, 110, 30), (255, 255, 255)]
    rows = [[0] * 80 for _ in range(80)]
    cx, cy, rx, ry = 40, 46, 20, 27
    def wave(y, x, base, amp=3.0, period=14.0, thick=3.0):
        return abs((y - base) - amp * math.sin((x - cx) / period * 2 * math.pi)) < thick / 2
    for y in range(80):
        for x in range(80):
            yy = (y - cy) / ry; xx = (x - cx) / (rx * (1.0 + 0.12 * (1 - yy)))   # 아래가 조금 넓은 달걀꼴
            d = xx * xx + yy * yy
            if d > 1: continue
            c = 2
            if d > 0.86: c = 1                                   # 테두리
            elif wave(y, x, 38) or wave(y, x, 54): c = 4         # 물결무늬 띠 두 줄
            elif xx < -0.45 and yy < -0.1: c = 3                 # 왼쪽 위 하이라이트
            elif xx > 0.5 or yy > 0.6: c = 5                     # 오른쪽·아래 그늘
            rows[y][x] = c
    rows[30][29] = rows[31][29] = 6                                # 반짝임
    return rows, pal

def put_egg(files, problems, checks):
    """알 칸 두 개(494·495)의 앞·뒤 그림과 팔레트를 디지타마로. 칸이 없으면 보고만"""
    rows, pal = digitama()
    n = 0
    for s in EGG_SLOTS:
        base_i = s * 6
        if base_i + 5 >= len(files): problems.append('알 칸 %d 가 그림 NARC 밖(파일 %d개) — 알 그림 건너뜀' % (s, len(files))); continue
        for k in (1, 3):
            tmpl = files[base_i + k] if files[base_i + k][:4] == b'RGCN' else next((f for f in files if f[:4] == b'RGCN'), None)
            files[base_i + k] = ncgr_with_pixels(tmpl, rows)
            if files[base_i + k - 1][:4] == b'RGCN': files[base_i + k - 1] = files[base_i + k]
            exp = [[pal[v] if v else None for v in r] for r in rows]
            checks.append((base_i + k, rows, exp, base_i + 4, '디지타마 %d' % s))
        ptmpl = files[base_i + 4] if files[base_i + 4][:4] == b'RLCN' else next((f for f in files if f[:4] == b'RLCN'), None)
        files[base_i + 4] = nclr_with_colors(ptmpl, pal); files[base_i + 5] = nclr_with_colors(ptmpl, pal)
        n += 1
    return n

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('art'); ap.add_argument('--base'); ap.add_argument('--out', default='hg4_out')
    ap.add_argument('--no-fit', action='store_true', help='그림 바닥 줄 맞추기를 끔')
    ap.add_argument('--no-egg', action='store_true', help='알 그림(디지타마) 넣기를 끔')
    ap.add_argument('--draft', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== HG4(전투 그림) — 롬', rom.code)
    draft = list(csv.DictReader(open(A.draft, encoding='utf-8'), delimiter=chr(9)))
    slot = {r['이름']: int(r['NDS 칸']) for r in draft if r['NDS 칸'].isdigit()}
    gra = NARC(rom.get('a/0/0/4')); files = list(gra.files)
    n_files = len(files)
    problems = []; done = 0; checks = []; fit_log = []
    dg_names = {r['이름'] for r in draft if r['출처'] == '디지골드' and not r['NDS 칸'].isdigit()}
    for r in draft:                                     # 디지골드 종의 칸(HG2·HG3 와 같은 규칙)
        mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
        if r['이름'] in dg_names and mm and mm.group(1) in hg2.REPLACED_DEX: slot[r['이름']] = hg2.REPLACED_DEX[mm.group(1)]
    # ---- 블랙워그레이몬: 디지골드의 검은 워그레이몬 그림을 109칸으로
    try:
        MSG = []
        for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
            try: MSG.append(hg1.msg_decode(f))
            except Exception: MSG.append((0, []))
        CM, NAMEF, _ = hg1.infer_charmap(MSG, {r['이름'] for r in draft})
        NAMES = [CM.dec(e) for e in MSG[NAMEF][1]]
        wg, bw = slot.get('워그레이몬'), slot.get('블랙워그레이몬')
        if wg is None or bw is None: raise ValueError('초안에 워그레이몬·블랙워그레이몬 칸이 없음')
        k = hg2.skel('워그레이몬')
        others = [i for i, n in enumerate(NAMES) if hg2.skel(n) == k and i != wg and i != bw and (i + 1) * 6 <= len(files)]
        if (bw + 1) * 6 > len(files) or (wg + 1) * 6 > len(files): raise ValueError('워그레이몬·블랙워그레이몬 칸이 그림 NARC 밖')
        if others:
            src = others[0]; files[bw * 6:bw * 6 + 6] = files[src * 6:src * 6 + 6]
            say('블랙워그레이몬: 이름이 「워그레이몬」인 두 번째 칸 %d 의 그림 6파일을 칸 %d 로 복사' % (src, bw))
            if len(others) > 1: problems.append('「워그레이몬」 칸이 셋 이상: %s — 첫 번째를 썼음, 폰으로 색 확인' % ([wg] + others,))
        else:
            blk = files[wg * 6:wg * 6 + 6]; blk[4], blk[5] = blk[5], blk[4]; files[bw * 6:bw * 6 + 6] = blk
            say('블랙워그레이몬: 「워그레이몬」 칸이 하나뿐 → 워그레이몬(칸 %d) 그림을 복사하고 보통 색·색다른 색을 맞바꿈(칸 %d). 폰으로 검은색인지 확인' % (wg, bw))
    except Exception as ex:
        problems.append('블랙워그레이몬 그림 못 넣음: %s' % ex)
    for d in sorted(os.listdir(A.art)):
        m = re.match(r'\d+_(.+)$', d)
        if not m: continue
        name = m.group(1) if m.group(1) in slot else hg2.RENAME.get(m.group(1), m.group(1))   # 그림 폴더는 설계 이름(데스메라몬 → 초안 데드메라몬)
        if name == '블랙워그레이몬': problems.append('블랙워그레이몬은 디지골드 검은 워그레이몬 그림을 써서 건너뜀: %s' % d); continue
        if name in dg_names: problems.append('디지골드 그림을 쓰는 종이라 건너뜀: %s' % d); continue
        if name not in slot: problems.append('초안에 없는 이름이라 건너뜀: %s' % d); continue
        s = slot[name]; base_i = s * 6
        fp, bp = os.path.join(A.art, d, 'front.png'), os.path.join(A.art, d, 'back.png')
        if not (os.path.exists(fp) and os.path.exists(bp)): continue
        if base_i + 5 >= len(files): problems.append('칸이 그림 NARC 밖: %s %d' % (name, s)); continue
        try:
            fr, fcols = read_indexed(fp); br, bcols = read_indexed(bp)
            # 바닥 줄 맞추기: 같은 칸 원래 그림(디지골드)의 바닥 줄에 새 그림 바닥을 맞춤
            fits = []
            if not A.no_fit:
                for k, which in ((3, 'f'), (1, 'b')):
                    orig, _m = hg1.ncgr_rows(files[base_i + k]) if files[base_i + k][:4] == b'RGCN' else (None, None)
                    ob = opaque_box(orig) if orig else None
                    if ob is None: fits.append(which + ':원래 없음'); continue
                    if which == 'f': fr, why = fit_bottom(fr, ob[1])
                    else: br, why = fit_bottom(br, ob[1])
                    fits.append('%s:%s(원래 바닥 %d)' % (which, why, ob[1]))
                fit_log.append('%s 칸 %d %s' % (name, s, ' '.join(fits)))
            # 앞·뒤가 한 팔레트(보통 색 파일 하나)를 같이 쓴다 → 뒷모습 번호를 「색」 기준으로 언제나 앞 팔레트 번호로 바꿈
            # (10/14 집 보고: 색 집합이 같아도 번호 순서가 달라서, 번호를 그대로 쓰면 뒷모습 색이 뒤바뀌었음 — 110종 중 78종)
            allc = list(dict.fromkeys(fcols + bcols[1:]))
            if len(allc) > 16: problems.append('앞·뒤 합친 색이 %d개(16 넘음) — 넘친 색은 비슷한 색으로: %s' % (len(allc), name))
            cols = allc[:16]
            def near(c):
                if c in cols: return cols.index(c)
                return min(range(1, len(cols)), key=lambda i: sum((a - b) ** 2 for a, b in zip(cols[i], c)))
            remap = {0: 0}; remap.update({i: near(c) for i, c in enumerate(bcols) if i})
            exp_b = [[bcols[v] if v else None for v in r] for r in br]          # 검산용: 뒷모습 원래 색
            exp_f = [[fcols[v] if v else None for v in r] for r in fr]
            br = [[remap[v] for v in r] for r in br]
            for k, rows, exp in ((1, br, exp_b), (3, fr, exp_f)):              # 수컷 뒤·앞
                tmpl = files[base_i + k] if files[base_i + k][:4] == b'RGCN' else next((f for f in files if f[:4] == b'RGCN'), None)
                files[base_i + k] = ncgr_with_pixels(tmpl, rows)
                if files[base_i + k - 1][:4] == b'RGCN': files[base_i + k - 1] = files[base_i + k]   # 암컷 그림이 있으면 같게
                checks.append((base_i + k, rows, exp, base_i + 4, name))
            ptmpl = files[base_i + 4] if files[base_i + 4][:4] == b'RLCN' else next((f for f in files if f[:4] == b'RLCN'), None)
            files[base_i + 4] = nclr_with_colors(ptmpl, cols); files[base_i + 5] = nclr_with_colors(ptmpl, shiny(cols))
            done += 1
        except Exception as ex:
            problems.append('그림 못 넣음: %s %s' % (name, ex))
    if not A.no_egg:
        ne = put_egg(files, problems, checks); say('알 그림(디지타마) 넣음: 칸 %s 중 %d (10/14, 폰에서 알 화면 확인)' % (EGG_SLOTS, ne))
    if len(files) != n_files: raise SystemExit('실패: 그림 파일 수가 바뀜(%d → %d) — 롬을 쓰지 않고 멈춤' % (n_files, len(files)))
    gra.files = files
    out = NDS(raw); out.put('a/0/0/4', gra.build()); new_raw = bytes(out.d)
    # 검산: 다시 풀어 ① 색 번호가 같은지 ② 롬 팔레트로 칠한 「색」이 원래 그림 색과 같은지(10/14: 번호만 보면 색 뒤바뀜을 못 잡음)
    g2 = NARC(NDS(new_raw).get('a/0/0/4')).files; bad = 0; bad_rgb = []
    for idx, rows, exp, pi, nm in checks:
        got, mode = hg1.ncgr_rows(g2[idx])
        if mode != 'dp' or [r[:80] for r in got] != [list(r) for r in rows]: bad += 1; problems.append('검산 실패: 파일 %d (복호 %s)' % (idx, mode)); continue
        pal = hg1.nclr(g2[pi]); tot = diff = 0
        for y in range(80):
            for x in range(80):
                if (y, x) < (0, 4): continue
                e = exp[y][x]
                if e is None: continue
                tot += 1
                if got[y][x] == 0 or pal[got[y][x]] != q5(e): diff += 1
        if tot and diff * 100 > tot * 2: bad_rgb.append((nm, idx, diff * 100 // tot))
    say('색 검산(롬 팔레트로 칠한 색 = 원래 색): %d파일 중 2%% 넘게 다름 %d' % (len(checks), len(bad_rgb)))
    for nm, idx, pc in bad_rgb[:30]: problems.append('색 검산 실패: %s 파일 %d 색 %d%% 다름' % (nm, idx, pc))
    if fit_log:
        say('바닥 줄 맞추기(f=앞, b=뒤; +n줄 = 위로 올림):')
        for x in fit_log: say('  ' + x)
    say('전투 그림 넣음: %d종, 검산 %d파일 중 실패 %d' % (done, len(checks), bad))
    open(os.path.join(A.out, 'hg4_test.nds'), 'wb').write(new_raw)
    base = open(A.base, 'rb').read() if A.base else raw
    patch = bps_make(base, new_raw); open(os.path.join(A.out, 'hg4.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(base, patch) == new_raw else '실패'))
    say('\n== 문제 %d건' % len(problems)); [say('-', x) for x in problems[:100]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
