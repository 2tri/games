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
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--out', default='dsw_ow'); ap.add_argument('--table', default=os.path.join(HERE, 'dsw_번호표.tsv'))
    ap.add_argument('--design', default=os.path.join(HERE, '..', 'design.json'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = hg1.NDS(raw)
    design = json.load(open(A.design, encoding='utf-8')); en = {s['ko']: s['en'] for s in design['species']}
    path_of = {p.split('/')[-1].lower(): p for p in rom.paths if p.startswith('dat/MCHR/')}
    rows = [r for r in csv.reader(open(A.table, encoding='utf-8'), delimiter=chr(9))][1:]
    table = []; done = 0
    for ko, key, why in rows:
        key = key.upper()
        try:
            c = rom.get(path_of[key.lower() + 'c']); p = rom.get(path_of[key.lower() + 'p']); a = rom.get(path_of[key.lower() + 'a'])
        except KeyError:
            table.append((ko, key, '', '', '없음', 'MCHR 파일 없음')); continue
        fr, size = ds_mchr.frames(c); cols = ds_mchr.palette(p)
        if not fr: table.append((ko, key, '', '', '없음', '컷 형식 다름')); continue
        tw = ds_mchr.tiles_wide(size, 'tall')
        ims = [ds_mchr.frame_image(f, cols, tw) for f in fr]
        g = walk_groups(ds_mchr.rle(a) or b'')
        seqs = []
        for grp in g[:8]:
            if len(grp) == 4 and grp not in seqs: seqs.append(grp)
        if len(seqs) < 2: table.append((ko, key, '', '%d컷' % len(fr), '하', '걷기 묶음을 못 읽음(컷 %d개) — 안 씀' % len(fr))); continue
        A_, B_ = seqs[0], seqs[1]
        single = [grp for grp in g[8:] if len(grp) == 1]
        fc = single[0][0] if single else B_[0]
        def pick(i): return ims[i] if i < len(ims) else ims[0]
        rws = [(fc, fc + 1 if fc + 1 < len(ims) else fc), (A_[0], A_[1]), (B_[0], B_[1]), None]
        w, h = ims[0].size
        sheet = Image.new('RGBA', (2 * w + 4, 4 * h + 12), (0, 0, 0, 0))
        for r in range(4):
            for cidx in range(2):
                if r < 3: im = pick(rws[r][cidx])
                else:
                    from PIL import ImageOps
                    im = ImageOps.mirror(pick(rws[2][cidx]))
                sheet.alpha_composite(im, (cidx * (w + 4), r * (h + 4)))
        e = en.get(ko, '')
        fname = (re.sub(r'[^a-z0-9]+', '-', e.lower()).strip('-') + '-dsw-ow.png') if e else (ko + '_DSW걷기.png')
        sheet.save(os.path.join(A.out, fname)); done += 1
        table.append((ko, key, '', '%d컷 %dx%d' % (len(fr), w, h), '상', why + ' / 아래=컷 %d·위=컷 %s·옆=컷 %s' % (fc, A_[:2], B_[:2])))
    with open(os.path.join(A.out, '이름표.tsv'), 'w', encoding='utf-8', newline=chr(10)) as f:
        f.write('우리 종' + chr(9) + 'MCHR번호(16진)' + chr(9) + 'DS 영어 이름' + chr(9) + '컷' + chr(9) + '확신' + chr(9) + '어떻게 정했나' + chr(10))
        for r in table: f.write(chr(9).join(r) + chr(10))
    print('저장 %d / 번호표 %d줄' % (done, len(rows)))
    for r in table:
        if r[4] != '상': print('  못 씀:', r[0], r[1], r[5])

if __name__ == '__main__':
    main()
