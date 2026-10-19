#!/usr/bin/env python3
"""HG4 2단계(다): 사람 트레이너 전투 그림 넣기 (2026-10-14, 진짜 롬 형식은 오늘 밤 hg_scan 트레이너_그림.png 로 확인)
사용:   python hg4_trainer.py "<앞 단계 롬.nds>" "<그림 폴더(…/people)>" --base "<원본 롬>" [--probe]
        --probe : 안 바꾸고, 설계 표의 트레이너마다 「직업 번호·그림 파일 번호·지금 그림」만 hg4t_out/짝_확인.png 로(짝 맞는지 눈으로)
짝 규칙: NDS_트레이너.tsv 의 하트골드 이름 → 롬 트레이너 번호 → 직업 번호 = 그림 묶음 번호(a/0/5/8: 직업마다 5파일 [RGCN 80x80(?), RLCN, RECN, RNAN, RGCN 160x80]).
         이 규칙이 틀리면 --probe 그림에서 바로 보인다(관장 자리에 다른 사람). 그림 파일: NDS_트레이너그림.tsv (키 → png 파일 이름).
그림: png(아무 크기, 배경 투명) → 도트 되살리기 → 80x80 안 15색 → 작은 그림(80x80)과 큰 그림(160x80, 두 장면 같게)에 씀. 암호화 방식은 원래 파일에서 읽어(dp/pt/none) 같은 방식으로."""
import os, sys, re, csv, struct, argparse, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1, hg3, hg4, art_nds
from hg1 import NDS, NARC, bps_make, bps_apply, say, R

def decode_any(f):
    """RGCN(80x80 또는 160x80 4bpp) → (행, 방식, 너비). 크기 칸이 0 이어도 길이로 판단"""
    c = f.find(b'RAHC')
    if c < 0: return None, None, 0
    body = f[c + 0x20:]
    if len(body) >= 6400: w, h, n = 160, 80, 3200
    elif len(body) >= 3200: w, h, n = 80, 80, 1600
    else: return None, None, 0
    words = list(struct.unpack('<%dH' % n, body[:2 * n]))
    best = None
    for name, v in (('pt', hg1.lcg_dec(words, True)), ('dp', hg1.lcg_dec(words, False)), ('none', words)):
        b = struct.pack('<%dH' % n, *v); p = []
        for byte in b: p += [byte & 15, byte >> 4]
        rows = [p[y * w:(y + 1) * w] for y in range(h)]
        score = sum(1 for x in range(w) if rows[0][x] == 0) + sum(1 for x in range(w) if rows[h - 1][x] == 0)
        if best is None or score > best[0]: best = (score, rows, name)
    return best[1], best[2], w

def encode_any(template, rows, mode):
    c = template.find(b'RAHC'); w = len(rows[0]); n = w * 80 // 4
    px = []
    for r in rows: px += r
    if mode == 'dp': px[:4] = [0, 0, 0, 0]
    if mode == 'pt': px[-4:] = [0, 0, 0, 0]
    b = bytes(px[i] | (px[i + 1] << 4) for i in range(0, len(px), 2))
    words = list(struct.unpack('<%dH' % n, b))
    if mode == 'dp': enc = hg4.encrypt_dp(words, 0x1234)
    elif mode == 'pt': enc = hg4.encrypt_pt(words, 0x1234)
    else: enc = words
    d = bytearray(template); d[c + 0x20:c + 0x20 + 2 * n] = struct.pack('<%dH' % n, *enc)
    return bytes(d)

def load_png(path):
    w, h, img = art_nds.png_read(path); img = art_nds.remove_bg(img); b = art_nds.bbox(img)
    if not b: raise ValueError('그림이 비었음')
    img = art_nds.crop(img, b); nat = art_nds.native(img)
    nat = art_nds.scale_to(nat, 78, 78) if (len(nat) > 78 or len(nat[0]) > 78) else nat
    cell = art_nds.place(nat, 80, 80, bottom=1)
    (ci,), pal = art_nds.quantize([cell], 15)
    return ci, [(0, 0, 0)] + list(pal[1:]) if pal and pal[0] == (0, 0, 0) else [(0, 0, 0)] + list(pal)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('art'); ap.add_argument('--base', required=True); ap.add_argument('--out', default='hg4t_out')
    ap.add_argument('--probe', action='store_true'); ap.add_argument('--map', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_트레이너그림.tsv'))
    ap.add_argument('--trainers', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_트레이너.tsv'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== HG4 2단계(다) 트레이너 그림 — 롬', rom.code)
    if 'a/0/5/8' not in rom.paths: raise SystemExit('실패: 트레이너 그림 묶음(a/0/5/8)이 없음')
    nar = NARC(rom.get('a/0/5/8')); files = list(nar.files); n0 = len(files); sizes0 = [len(f) for f in files]
    per = 5 if n0 % 5 == 0 else None
    if not per: raise SystemExit('실패: 트레이너 그림 파일 수 %d 가 5의 배수가 아님 — 묶음 모양을 설계자에게' % n0)
    trd = NARC(rom.get(hg1.NARC_PATHS['trdata'])).files
    MSG = []
    for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
        try: MSG.append(hg1.msg_decode(f))
        except Exception: MSG.append((0, []))
    CM, NAMEF, _ = hg1.infer_charmap(MSG, set())
    TN = None
    for fi, (_, ent) in enumerate(MSG):
        if abs(len(ent) - len(trd)) <= 1:
            nm = [CM.dec(e) for e in ent]
            if sum(1 for x in nm if x and len(x) <= 6) > len(nm) * 0.5: TN = nm; break
    if TN is None: raise SystemExit('실패: 트레이너 이름표를 못 찾음')
    rows = list(csv.DictReader(open(A.trainers, encoding='utf-8'), delimiter='\t'))
    pics = {}
    if os.path.exists(A.map):
        for r in csv.DictReader((l for l in open(A.map, encoding='utf-8') if not l.startswith('#')), delimiter='\t'): pics[r['키']] = r['파일']
    pairs = []
    for r in rows:
        key = r['키'].split('#')[0]; hn = r['하트골드 이름'].strip().split('#')[0]
        if hn.startswith('(') or not hn: continue
        want_ = {hg3.skel_name(hn), hg3.skel_name(r.get('새 이름', ''))} - {''}          # HG3 뒤 롬은 새 이름(소라)으로 바뀌어 있음
        ids = [i for i, x in enumerate(TN) if hg3.skel_name(x) in want_]
        if not ids: continue
        t = hg1.trdata(trd[ids[0]])
        if not t: continue
        cls = t['class']
        if cls * per + per > n0: continue
        pairs.append((key, r['새 이름'], ids[0], cls, pics.get(key) or pics.get(r['키'])))
    seen = set(); uniq = []
    for p_ in pairs:
        if p_[3] in seen: continue
        seen.add(p_[3]); uniq.append(p_)
    say('설계 트레이너 %d명 → 직업(그림 묶음) %d개: %s' % (len(pairs), len(uniq), ', '.join('%s=%d' % (k, c) for k, _, _, c, _ in uniq)))
    # 짝 확인 그림: 직업마다 지금 큰 그림
    blocks = []; row = []
    for key, nm, tid, cls, png in uniq:
        big = files[cls * per + per - 1]; rws, mode, w = decode_any(big)
        if rws: row.append(([r_[:80] for r_ in rws], hg1.nclr(files[cls * per + 1]) or [(0, 0, 0)] * 16))
        else: row.append(None)
        if len(row) == 8: blocks.append(row); row = []
    if row: blocks.append(row)
    if blocks:
        import hg4_follow
        hg4_follow.rgba_sheet(os.path.join(A.out, '짝_확인.png'), blocks, 80, 80, 8)
        say('짝_확인.png: 순서 = %s (칸마다 그 직업의 지금 그림 — 관장 자리에 맞는 사람인지 확인)' % ' '.join(k for k, _, _, _, _ in uniq))
    if A.probe:
        open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n'); return
    problems = []; done = 0; checks = []
    draft = list(csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='	'))
    slot = {r['이름']: int(r['NDS 칸']) for r in draft if r['NDS 칸'].isdigit()}
    import hg2
    for r in draft:
        mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
        if r['출처'] == '디지골드' and mm and mm.group(1) in hg2.REPLACED_DEX: slot[r['이름']] = hg2.REPLACED_DEX[mm.group(1)]
    gra = NARC(rom.get('a/0/0/4')).files
    def species_pic(name):
        """「종:레오몬」 → 그 디지몬의 전투 앞모습(80x80)과 팔레트를 트레이너 그림으로(10/14: 디지몬이 수호자인 자리)"""
        s_ = slot.get(name)
        if s_ is None or (s_ + 1) * 6 > len(gra): raise ValueError('종 칸 없음 ' + name)
        rows, mode = hg1.ncgr_rows(gra[s_ * 6 + 3]); pal = hg1.nclr(gra[s_ * 6 + 4])
        if rows is None or pal is None: raise ValueError('전투 그림 못 읽음 ' + name)
        return [r_[:80] for r_ in rows], pal
    for key, nm, tid, cls, png in uniq:
        if not png: problems.append('그림 파일 없음(표에 없음): %s' % key); continue
        try:
            if png.startswith('종:'): rows80, pal = species_pic(png[2:].strip())
            else:
                path = os.path.join(A.art, png)
                if not os.path.exists(path): problems.append('그림 파일 없음: %s %s' % (key, png)); continue
                rows80, pal = load_png(path)
        except Exception as ex: problems.append('그림 못 읽음 %s: %s' % (png, ex)); continue
        base_i = cls * per
        for k in (0, per - 1):
            f = files[base_i + k]
            if f[:4] != b'RGCN': continue
            old, mode, w = decode_any(f)
            if old is None: problems.append('그림 형식을 못 읽음: %s 파일 %d' % (key, base_i + k)); continue
            new_rows = [r_ + r_ for r_ in rows80] if w == 160 else rows80
            files[base_i + k] = encode_any(f, new_rows, mode); checks.append((base_i + k, new_rows, mode))
        pf = files[base_i + 1]
        if pf[:4] == b'RLCN': files[base_i + 1] = hg4.nclr_with_colors(pf, pal)
        else: problems.append('팔레트 파일이 RLCN 이 아님: %s' % key)
        done += 1
    if [len(f) for f in files] != sizes0 or len(files) != n0: raise SystemExit('실패: 파일 수·크기가 바뀜 — 롬을 쓰지 않음')
    nar.files = files; out = NDS(raw); out.put('a/0/5/8', nar.build()); new_raw = bytes(out.d)
    chk = NARC(NDS(new_raw).get('a/0/5/8')).files; bad = 0
    for idx, rows_, mode in checks:
        got, m2, w = decode_any(chk[idx])
        if got != rows_: bad += 1; problems.append('검산 실패: 파일 %d(%s→%s)' % (idx, mode, m2))
    say('트레이너 그림 넣음: %d명, 검산 %d파일 중 실패 %d' % (done, len(checks), bad))
    open(os.path.join(A.out, 'hg4t_test.nds'), 'wb').write(new_raw)
    braw = open(A.base, 'rb').read(); patch = bps_make(braw, new_raw); open(os.path.join(A.out, 'hg4t.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(braw, patch) == new_raw else '실패'))
    say('\n== 문제 %d건' % len(problems)); [say('-', x) for x in problems[:60]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
