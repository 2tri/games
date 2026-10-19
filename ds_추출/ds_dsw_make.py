#!/usr/bin/env python3
"""디지몬 월드 DS 걷기 그림(MCHR)을 우리 종 이름으로 뽑아 dsw_ow\\ 에 저장 (2026-10-14, Claude 작성 — 설계자 스크립트 아님)
사용: python ds_추출\\ds_dsw_make.py "<Digimon World DS 롬>" [--out dsw_ow]
- 이름표: 롬 안 영어 이름 표(1174832 번지부터 0xFFFF 로 끝나는 UTF16 글자열, 글자 = 값-0x29 에 대소문자가 뒤바뀐 글꼴 번호)
  MCHR 번호 = 37 + 표 순번 (처음 10마리를 그림으로 확인)
- 컷 → 방향: <번호>a 의 움직임 표에서 [15,Y,12,10,1,컷,12] 토막을 8방향 걷기 묶음으로 읽는다.
  걷기 묶음의 컷 두 종류: A(컷 0·1 = 위쪽을 보는 비스듬한 뒷모습), B(컷 3·4 = 왼쪽 아래를 보는 모습)
  아래(정면) = 단독 묶음의 컷(보통 6)과 다음 컷, 위 = A, 왼쪽 = B, 오른쪽 = B 를 좌우로 뒤집음
- 저장: 2칸 × 4줄(줄 = 아래·위·왼쪽·오른쪽), 칸 사이 4픽셀, 배경 투명, 크기 그대로"""
import os, sys, re, json, struct, csv, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import ds_mchr, hg1
from PIL import Image

# 우리 종 → DS 이름표의 이름 (눈으로·철자로 확인한 것). 자동 일치(철자 0.92↑)는 따로.
MANUAL = {
 '릴리몬': 'Lillymon', '메탈가루몬': 'MGarurumon', '피요몬': 'Biyomon', '아르마몬': 'Armadillomn', '가트몬': 'Gatomon',
 '피코데블몬': 'DemiDevimon', '아트라캅테리몬': ('MKabuterimnR', 0), '다크리자몬': 'Flarerizamon', '다이버몬': 'Divermon',
 '꼬끼몬': 'Kokatorimon', '데라몬': 'Deramon', '슈카몬': 'Sukamon', '베놈묘티몬': 'VnmMyotismn', '우가몬': 'Ogremon',
 '블랙워그레이몬': 'BWarGreymn', '베지몬': 'Veggiemon', '브이몬': 'Veemon', '화염드라몬': ('Flamedramn', 0), '데이터몬': 'Datamon',
 '오메가몬': 'Omnimon', '디아블로몬': ('Diaboromon', 0), '묘티스몬': 'Myotismon', '엑스브이몬': 'ExVeemon',
 '가베지몬': 'Garbagemon', '다크티라몬': 'DarkTyrann', '마왕몬': ('Daemon', 0), '토르토몬': 'Tortomon', '미노타루몬': 'Minotarumon',
 '블랙워가루몬': 'WGarurumonBk', '워가루몬': 'WGarurumonBl', '메탈시드라몬': 'MtlSeadrmn', '파워드라몬': None,
 '맘몬': None, '다고몬': None, '콩알몬': 'Mamemon', '벨리얼묘티': None,
}
CONF_MID = {'가트몬', '다이버몬', '메탈시드라몬', '아트라캅테리몬', '화염드라몬', '마왕몬', '디아블로몬', '베놈묘티몬', '블랙워그레이몬', '워가루몬', '블랙워가루몬', '가베지몬', '다크리자몬'}

def ch(x):
    v = (x - 0x29) & 0xFFFF
    if 0x27 <= v <= 0x40: return chr(v + 0x1A)
    if 0x41 <= v <= 0x5A: return chr(v + 0x20)
    return '?'

def read_names(raw, pos=1174832):
    names = []
    while len(names) < 700:
        s = ''; p = pos; bad = False
        while True:
            x = struct.unpack_from('<H', raw, p)[0]; p += 2
            if x == 0xFFFF: break
            s += ch(x)
            if len(s) > 30: bad = True; break
        if bad: break
        names.append(s); pos = p
    return names

def mean_color(ims):
    n = 0; r = g = b = 0
    for im in ims:
        for (R, G, B, Aa) in im.getdata():
            if Aa > 128: r += R; g += G; b += B; n += 1
    return (r / n, g / n, b / n) if n else None

def cdist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

def walk_groups(a):
    w = struct.unpack('<%dH' % (len(a) // 2), a[:len(a) // 2 * 2])
    out = []; cur = []; i = 0
    while i < len(w):
        if w[i] == 0xFFFF:
            if cur: out.append(cur); cur = []
            i += 1; continue
        if i + 6 < len(w) and w[i + 2] == 12 and w[i + 3] == 10 and w[i + 4] == 1 and w[i + 6] == 12:
            cur.append(w[i + 5]); i += 7; continue
        i += 1
    if cur: out.append(cur)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default='dsw_ow')
    ap.add_argument('--design', default=os.path.join(HERE, '..', 'design.json')); ap.add_argument('--draft', default=os.path.join(HERE, '..', 'NDS_종_초안.tsv'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = hg1.NDS(raw)
    names = read_names(raw)
    by_name = {}
    for i, n in enumerate(names):
        if n: by_name.setdefault(n, []).append(37 + i)
    design = json.load(open(A.design, encoding='utf-8')); en = {s['ko']: s['en'] for s in design['species']}
    ours = [r['이름'] for r in csv.DictReader(open(A.draft, encoding='utf-8'), delimiter='\t') if r['이름'] != '토코몬']
    lower = {n.lower(): n for n in by_name}
    def auto(ko):
        t = re.sub(r'[^a-z]', '', en.get(ko, '').lower())
        return lower.get(t)
    path_of = {p.split('/')[-1].lower(): p for p in rom.paths if p.startswith('dat/MCHR/')}
    table = []; done = 0
    for ko in ours:
        if ko in MANUAL:
            m = MANUAL[ko]; nm, k = (m if isinstance(m, tuple) else (m, 0)) if m else (None, 0)
            conf, how = ('중', '이름 철자·종류로 짝지음') if ko in CONF_MID else ('상', '이름 표 일치')
        else:
            nm, k = auto(ko), 0; conf, how = '상', '이름 표 철자 일치'
        if not nm or nm not in by_name:
            table.append((ko, '', '', '', '없음', 'DS 이름 표에 대응하는 종 없음')); continue
        base_id = by_name[nm][k]
        # 표 번호 → 그림 번호 어긋남(표에 그림 없는 줄이 끼어 있음, 큰 종은 -2 근처): 우리 앞모습 평균 색과 가장 가까운 번호를 고른다
        ref_im = None
        for dname in os.listdir(os.path.join(HERE, '..', 'nds_art')):
            if dname.endswith('_' + ko) and os.path.exists(os.path.join(HERE, '..', 'nds_art', dname, 'front.png')):
                ref_im = Image.open(os.path.join(HERE, '..', 'nds_art', dname, 'front.png')).convert('RGBA')
        ref = mean_color([ref_im]) if ref_im else None
        best = None
        for off in ((0,) if base_id <= 0x64 else ((-2,) if base_id <= 0x89 else (-3, -4))):
            cid = base_id + off
            kk = '%X' % cid
            if kk.lower() + 'c' not in path_of or kk.lower() + 'p' not in path_of: continue
            try:
                f2, s2 = ds_mchr.frames(rom.get(path_of[kk.lower() + 'c'])); c2 = ds_mchr.palette(rom.get(path_of[kk.lower() + 'p']))
            except Exception: continue
            if not f2: continue
            im2 = [ds_mchr.frame_image(x, c2, ds_mchr.tiles_wide(s2, 'tall')) for x in f2[:6]]
            mc = mean_color(im2)
            if mc is None or ref is None: continue
            dist = cdist(mc, ref)
            if best is None or dist < best[0]: best = (dist, cid, off)
        mid = best[1] if best else base_id
        key = '%X' % mid
        try:
            c = rom.get(path_of[key.lower() + 'c']); p = rom.get(path_of[key.lower() + 'p']); a = rom.get(path_of[key.lower() + 'a'])
        except KeyError:
            table.append((ko, key, nm, '', '없음', 'MCHR 파일 없음')); continue
        lim = 70 if base_id <= 0x64 else (42 if base_id <= 0x89 else 30)
        if best is None or best[0] > lim:
            table.append((ko, key, nm, '', '하', '색 차이 큼(%s) — 짝이 맞는지 확신 못 해 안 씀' % ('?' if best is None else '%.0f' % best[0]))); continue
        if best[2] != 0:
            how += ' / 표 번호 %X → 그림 번호 %X (표에 그림 없는 줄 %d개 앞섬, 색 거리 %.0f)' % (base_id, mid, -best[2], best[0]); conf = '중'
        else:
            how += ' / 색 거리 %.0f' % best[0]
        fr, size = ds_mchr.frames(c); cols = ds_mchr.palette(p)
        if not fr: table.append((ko, key, nm, '', '없음', '컷 형식 다름')); continue
        tw = ds_mchr.tiles_wide(size, 'tall')
        ims = [ds_mchr.frame_image(f, cols, tw) for f in fr]
        g = walk_groups(ds_mchr.rle(a) or b'')
        seqs = []
        for grp in g[:8]:
            if len(grp) == 4 and grp not in seqs: seqs.append(grp)
        if len(seqs) < 2: table.append((ko, key, nm, '%d컷' % len(fr), '하', '걷기 묶음을 못 읽음')); continue
        A_, B_ = seqs[0], seqs[1]
        single = [grp for grp in g[8:] if len(grp) == 1]
        fc = single[0][0] if single else B_[0]
        def pick(i): return ims[i] if i < len(ims) else ims[0]
        rows = [(fc, fc + 1 if fc + 1 < len(ims) else fc), (A_[0], A_[1]), (B_[0], B_[1]), None]
        w, h = ims[0].size
        sheet = Image.new('RGBA', (2 * w + 4, 4 * h + 12), (0, 0, 0, 0))
        for r in range(4):
            for cidx in range(2):
                if r < 3: im = pick(rows[r][cidx])
                else:
                    from PIL import ImageOps
                    im = ImageOps.mirror(pick(rows[2][cidx]))
                sheet.alpha_composite(im, (cidx * (w + 4), r * (h + 4)))
        e = en.get(ko, '')
        fname = (re.sub(r'[^a-z0-9]+', '-', e.lower()).strip('-') + '-dsw-ow.png') if e else (ko + '_DSW걷기.png')
        sheet.save(os.path.join(A.out, fname)); done += 1
        table.append((ko, key, nm, '%d컷 %dx%d' % (len(fr), w, h), conf, how + ' / 아래=컷 %d·위=컷 %s·옆=컷 %s' % (fc, A_[:2], B_[:2])))
    with open(os.path.join(A.out, '이름표.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('우리 종\tMCHR번호(16진)\tDS 영어 이름\t컷\t확신\t어떻게 정했나\n')
        for r in table: f.write('\t'.join(r) + '\n')
    print('이름 붙인 우리 종 %d / %d' % (done, len(ours)))

if __name__ == '__main__':
    main()
