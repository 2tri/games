#!/usr/bin/env python3
"""HG4 2단계(가): 파티 아이콘 넣기 (2026-10-12, 가짜 롬으로만 시험 — 진짜 롬 형식은 hg_scan 보고로 확인)
사용:   python hg4_icons.py "<HG4 까지 거친 롬.nds>" <nds_art 폴더> [--base "<원본 디지골드 롬>"] [--paltab arm9:0x1A2B3C]
결과:   hg4i_out/hg4i_test.nds, hg4i_out/hg4i.bps, hg4i_out/report.txt
- 아이콘 NARC(a/0/2/0): 파일 0 = 공용 팔레트(16색 × 3벌), 파일 1~6 = 셀·애니, 파일 7+ = 종마다 아이콘(32x64, 4bpp, 두 장면 위아래).
  (hg_scan 보고의 「첫 RGCN 번호」가 7 이 아니면 --first 로)
- 종마다 art_nds 의 icon.png(16색)를 공용 팔레트 3벌 중 가장 비슷한 벌로 색을 바꿔 넣는다. 그림은 틀 파일을 복사해 픽셀만 바꿈.
- 어느 벌을 쓰는지는 arm9 의 「아이콘 팔레트 표」(종마다 1바이트) — hg_scan 보고 3절의 후보 자리를 --paltab arm9:오프셋 으로 주면 쓴다.
  arm9 가 압축돼 있거나 표를 모르면 표는 못 쓰고, 그 종이 지금 쓰는 벌(표 값)을 모르니 색이 틀릴 수 있다 → 보고에 적는다.
- 쓰고 나서 다시 풀어 픽셀을 대조한다."""
import os, sys, re, csv, struct, argparse, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1, hg2, hg4, art_nds, hg_scan
from hg1 import NDS, NARC, bps_make, bps_apply, say, R

def palettes(f):
    c = f.find(b'TTLP'); n = struct.unpack_from('<I', f, c + 0x10)[0] // 2; off = c + 0x18; cols = []
    for i in range(n):
        v = struct.unpack_from('<H', f, off + i * 2)[0]
        cols.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return [cols[k:k + 16] for k in range(0, len(cols) - 15, 16)]

def nearest(col, pal):
    return min(range(1, len(pal)), key=lambda i: sum((a - b) ** 2 for a, b in zip(col, pal[i])))

def encode(template, rows):
    """틀 RGCN(32x64) 의 픽셀을 rows(64행 × 32 색 번호)로 — 배치(타일/줄)는 틀 그대로"""
    c = template.find(b'RAHC'); ty, tx, bpp, mp, tiled, size = struct.unpack_from('<HHIIII', template, c + 8)
    if bpp != 3 or size != 1024: raise ValueError('틀이 32x64 4bpp 아이콘이 아님(bpp %d, 크기 %d)' % (bpp, size))
    px = [0] * 2048
    if tiled == 1:
        for y in range(64):
            for x in range(32): px[y * 32 + x] = rows[y][x]
    else:
        for t in range(32):
            tyy, txx = divmod(t, 4)
            for k in range(64): px[t * 64 + k] = rows[tyy * 8 + k // 8][txx * 8 + k % 8]
    b = bytes(px[i] | (px[i + 1] << 4) for i in range(0, 2048, 2))
    d = bytearray(template); d[c + 0x20:c + 0x20 + 1024] = b
    return bytes(d), tiled

def decode(f):
    c = f.find(b'RAHC'); ty, tx, bpp, mp, tiled, size = struct.unpack_from('<HHIIII', f, c + 8); b = f[c + 0x20:c + 0x20 + 1024]
    px = []
    for byte in b: px += [byte & 15, byte >> 4]
    rows = [[0] * 32 for _ in range(64)]
    if tiled == 1:
        for y in range(64):
            for x in range(32): rows[y][x] = px[y * 32 + x]
    else:
        for t in range(32):
            tyy, txx = divmod(t, 4)
            for k in range(64): rows[tyy * 8 + k // 8][txx * 8 + k % 8] = px[t * 64 + k]
    return rows

def put_fid(nds, fid, data):
    """파일 번호로 롬 끝에 놓고 FAT 만 고침(오버레이처럼 이름이 없는 파일용) → '제자리' 또는 '끝에'"""
    s0, e0 = nds.fat(fid)
    if len(data) <= e0 - s0:
        nds.d[s0:s0 + len(data)] = data; struct.pack_into('<II', nds.d, nds.fat_off + fid * 8, s0, s0 + len(data)); how = '제자리'
    else:
        ns = (nds.used_end() + 0x1FF) & ~0x1FF; ne = ns + len(data)
        if len(nds.d) < ne: nds.d += b'\xff' * (ne - len(nds.d))
        nds.d[ns:ne] = data; struct.pack_into('<II', nds.d, nds.fat_off + fid * 8, ns, ne)
        if ne > struct.unpack_from('<I', nds.d, 0x80)[0]: struct.pack_into('<I', nds.d, 0x80, ne)
        while (0x20000 << nds.d[0x14]) < len(nds.d): nds.d[0x14] += 1
        how = '끝에'
    struct.pack_into('<H', nds.d, 0x15E, hg1.crc16(bytes(nds.d[0:0x15E])))
    return how

def put_arm9(nds, data):
    """압축 푼 arm9 를 롬 끝 빈 곳에 놓고 머리말(위치·크기·사용 크기·CRC)을 고침. 뒤의 nitro 꼬리 12바이트도 같이 옮김(10/14)"""
    d = nds.d; o, n = struct.unpack_from('<I', d, 0x20)[0], struct.unpack_from('<I', d, 0x2C)[0]
    tail = bytes(d[o + n:o + n + 12]) if bytes(d[o + n:o + n + 4]) == bytes([0x21, 0x06, 0xC0, 0xDE]) else b''
    later = [x for x in nds._region_starts() if x > o]
    limit = min(later) if later else len(d)
    if len(data) + len(tail) <= limit - o:
        d[o:o + len(data)] = data; d[o + len(data):o + len(data) + len(tail)] = tail; how = '제자리'
    else:
        ns = (nds.used_end() + 0xFFF) & ~0xFFF; ne = ns + len(data) + len(tail)
        if len(d) < ne: d += b'\xff' * (ne - len(d))
        d[ns:ns + len(data)] = data; d[ns + len(data):ne] = tail
        struct.pack_into('<I', d, 0x20, ns)
        if ne > struct.unpack_from('<I', d, 0x80)[0]: struct.pack_into('<I', d, 0x80, ne)
        while (0x20000 << d[0x14]) < len(d): d[0x14] += 1
        how = '롬 끝(0x%X)' % ns
    struct.pack_into('<I', d, 0x2C, len(data))
    struct.pack_into('<H', d, 0x15E, hg1.crc16(bytes(d[0:0x15E])))
    return how

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('art'); ap.add_argument('--base'); ap.add_argument('--out', default='hg4i_out')
    ap.add_argument('--first', type=int, help='첫 아이콘 그림의 파일 번호(기본: 첫 RGCN)'); ap.add_argument('--paltab', help='arm9:0x오프셋 (hg_scan 3절 후보)')
    ap.add_argument('--draft', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'))
    ap.add_argument('--starters', default='', help='스타팅 표 바꾸기: 이벤트표 경로(기본 NDS_이벤트표.tsv). none = 안 바꿈')
    ap.add_argument('--dg-starters', default='252,261,287', help='디지골드가 넣어 둔 스타팅 칸(아구몬·파피몬·브이몬) — 이 값들도 찾아 바꿈')
    ap.add_argument('--mart', default='20:226:5,76:108:6,19:233:6,21:326:6', help='일반 상점 표에서 「옛 도구:새 도구:배지 단계」(쉼표로 여럿). 기본 = 얼음상태치료제→태그(배지 7개), 실버스프레이→어둠의돌·화상치료제→금속코트·잠깨는약→검은 톱니(배지 8개). 궁극의 문장은 상점에 없음(Lv55 로도 진화). none = 안 바꿈')
    ap.add_argument('--keep-compressed', action='store_true', help='arm9 를 압축 푼 채로 다시 넣지 않음(표는 읽기만 — 10/13 방식)')
    ap.add_argument('--dex-order', help='NDS_도감순서.tsv — 성도 도감 표(arm9 안 u16 256개)를 이 순서로 다시 씀(arm9 를 압축 풀어 넣을 때만)')
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== HG4 2단계(가) 아이콘 — 롬', rom.code)
    draft = list(csv.DictReader(open(A.draft, encoding='utf-8'), delimiter=chr(9)))
    slot = {r['이름']: int(r['NDS 칸']) for r in draft if r['NDS 칸'].isdigit()}
    dg_names = {r['이름'] for r in draft if r['출처'] == '디지골드' and not r['NDS 칸'].isdigit()}
    nar = NARC(rom.get('a/0/2/0')); files = list(nar.files); n_files = len(files)
    first = A.first if A.first is not None else next((i for i, f in enumerate(files) if f[:4] == b'RGCN'), None)
    palf = next((f for f in files if f[:4] == b'RLCN'), None)
    if first is None or palf is None: raise SystemExit('실패: 아이콘 NARC 에서 그림·팔레트를 못 찾음 — hg_scan 보고 2절을 설계자에게')
    pals = palettes(palf); say('아이콘 팔레트 %d벌, 첫 그림 파일 %d, 그림 %d장' % (len(pals), first, sum(1 for f in files if f[:4] == b'RGCN')))
    # 팔레트 표
    tab = None; tab_ro = None; a9dec = None; arm9_off = struct.unpack_from('<I', raw, 0x20)[0]; a9size = struct.unpack_from('<I', raw, 0x2C)[0]
    out_raw = bytearray(raw)
    if A.paltab:
        m = re.match(r'arm9:(0x[0-9a-fA-F]+|\d+)$', A.paltab)
        if not m: say('--paltab 형식은 arm9:0x오프셋 — 무시')
        else:
            off = int(m.group(1), 0); a9 = raw[arm9_off:arm9_off + a9size]
            comp = a9.find(bytes([0x21, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21]))
            if comp >= 0x1C and struct.unpack_from('<I', a9, comp - 8)[0]:
                dec = next((b for nm, b in hg_scan.binaries(rom) if nm.startswith('arm9')), None)
                if dec and off + 700 <= len(dec) and not A.keep_compressed:
                    # 10/14: arm9 를 압축 푼 채로 롬 끝에 다시 놓고(모듈 정보의 「압축 끝」= 0), 표를 종마다 가장 맞는 벌로 고친다
                    a9new = bytearray(dec); pm = a9new.find(bytes([0x21, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21]))
                    if pm >= 0x1C:
                        struct.pack_into('<I', a9new, pm - 8, 0); a9dec = (a9new, off)
                        say('arm9 를 압축 풀어 다시 넣음(%d → %d바이트) — 팔레트 표(오프셋 0x%X)를 종마다 고침' % (a9size, len(a9new), off))
                    else: say('풀린 arm9 에서 모듈 정보를 못 찾아 표는 읽기만')
                    tab_ro = bytes(dec[off:off + 700])
                elif dec and off + 700 <= len(dec): tab_ro = bytes(dec[off:off + 700]); say('arm9 가 압축돼 있어 팔레트 표는 읽기만(오프셋 0x%X) — 종마다 지금 표 값의 벌로 색 변환' % off)
                else: say('arm9 압축을 못 풀어 팔레트 표를 못 읽음')
            else: a9dec = (bytearray(a9), off); say('팔레트 표: arm9 오프셋 0x%X (arm9 가 압축 아님 — 그대로 고쳐 씀)' % off)
    else: say('팔레트 표 자리를 안 줘서(--paltab) 표는 안 씀 — 그 종의 지금 표 값과 다른 벌을 고르면 색이 틀릴 수 있음')
    if a9dec is None and not A.keep_compressed:
        # 10/16 진짜 롬 시험: arm9 가 압축 아님(또는 --paltab 없음)이면 a9dec 가 없어 스타팅·상점·도감 순서가 말없이 빠졌음 → 여기서 따로 준비
        dec = next((b for nm, b in hg_scan.binaries(rom) if nm.startswith('arm9')), None)
        if dec:
            a9new = bytearray(dec); pm = a9new.find(bytes([0x21, 0x06, 0xC0, 0xDE, 0xDE, 0xC0, 0x06, 0x21]))
            if pm >= 0x1C: struct.pack_into('<I', a9new, pm - 8, 0)
            a9dec = (a9new, None); say('arm9 준비(스타팅·상점·도감 순서용, 팔레트 표는 안 씀)')
    problems = []; done = 0; checks = []
    for d in sorted(os.listdir(A.art)):
        m = re.match(r'\d+_(.+)$', d)
        if not m: continue
        name = m.group(1) if m.group(1) in slot else hg2.RENAME.get(m.group(1), m.group(1))
        if name in dg_names or name not in slot: continue      # 10/16: 블랙워그레이몬도 아이콘을 넣음(전에는 건너뛰어 또가스 아이콘이 남음)
        ip = os.path.join(A.art, d, 'icon.png')
        if not os.path.exists(ip): continue
        s = slot[name]; fi = first + s
        if fi >= n_files or files[fi][:4] != b'RGCN': problems.append('아이콘 파일 없음: %s (파일 %d)' % (name, fi)); continue
        try:
            rows, cols = hg4.read_indexed(ip)
            if len(rows) != 64 or len(rows[0]) != 32: problems.append('icon.png 크기가 32x64 가 아님: %s' % name); continue
            # 표를 쓸 수 있으면 가장 비슷한 벌, 아니면 지금 표 값을 모르니 0번 벌로 고정(색은 보고에)
            cand = range(len(pals)) if (tab is not None or (a9dec is not None and a9dec[1] is not None)) else ([tab_ro[s] % len(pals)] if tab_ro is not None and s < len(tab_ro) else [0])
            best = None
            for k in cand:
                mp = {i: nearest(cols[i], pals[k]) for i in range(1, len(cols))}
                err = sum(sum((a - b) ** 2 for a, b in zip(cols[i], pals[k][mp[i]])) for i in range(1, len(cols)))
                if best is None or err < best[0]: best = (err, k, mp)
            err, k, mp = best
            new_rows = [[mp.get(v, 0) if v else 0 for v in r] for r in rows]
            files[fi], tiled = encode(files[fi], new_rows)
            if tab is not None: out_raw[tab + s] = k
            if a9dec is not None and a9dec[1] is not None: a9dec[0][a9dec[1] + s] = k
            checks.append((fi, new_rows)); done += 1
            if err > 3000 * max(1, len(cols) - 1): problems.append('색이 많이 달라짐(공용 팔레트 한계): %s 벌 %d' % (name, k))
        except Exception as ex:
            problems.append('아이콘 못 넣음: %s %s' % (name, ex))
    if len(files) != n_files: raise SystemExit('실패: 아이콘 파일 수가 바뀜')
    nar.files = files; out = NDS(bytes(out_raw)); out.put('a/0/2/0', nar.build())
    if A.dex_order and a9dec is not None:
        try:
            dr = [r for r in csv.DictReader((l for l in open(A.dex_order, encoding='utf-8') if not l.startswith('#')), delimiter=chr(9))]
            name2slot = dict(slot)
            for r in draft:                                  # 디지골드 종 칸(hg2 와 같은 규칙)
                mm_ = re.search(r'디지골드 칸: (\S+)', r['메모'])
                if r['이름'] in dg_names and mm_ and mm_.group(1) in hg2.REPLACED_DEX: name2slot[r['이름']] = hg2.REPLACED_DEX[mm_.group(1)]
            order = [name2slot[r['이름']] for r in dr if r['이름'] in name2slot]
            miss = [r['이름'] for r in dr if r['이름'] not in name2slot]
            pat = struct.pack('<9H', 152, 153, 154, 155, 156, 157, 158, 159, 160)
            vals = order[:256] + [0] * (256 - len(order[:256]))
            wrote = None
            # ① 도감 자료 묶음 a/0/7/4(zukan_data, 10/14 웹 조사: 「키·무게·순서」)의 멤버 안(압축 아님일 때만 제자리에 씀)
            if 'a/0/7/4' in out.paths:
                zn = NARC(out.get('a/0/7/4')); zf = list(zn.files); hits = [(mi, f.find(pat)) for mi, f in enumerate(zf) if f[:1] not in (b'\x10', b'\x11') and f.find(pat) >= 0]
                if len(hits) == 1:
                    mi, i = hits[0]; d_ = bytearray(zf[mi])
                    for k, v in enumerate(vals):
                        if i + 2 * k + 2 <= len(d_): struct.pack_into('<H', d_, i + 2 * k, v)
                    zf[mi] = bytes(d_); zn.files = zf; out.put('a/0/7/4', zn.build()); wrote = 'a/0/7/4 멤버 %d @0x%X' % (mi, i)
                elif len(hits) > 1: problems.append('도감 자료(a/0/7/4)에 순서 표 후보가 여럿 %s — 건너뜀' % hits[:4])
            # ② arm9
            if wrote is None:
                a9 = a9dec[0]; i = a9.find(pat)
                if i < 0: problems.append('성도 도감 표(152 153 154 …)를 a/0/7/4·arm9 에서 못 찾음 — hg_scan 0절·3b 절 참고, 도감 순서는 건너뜀')
                elif a9.find(pat, i + 2) >= 0: problems.append('성도 도감 표 후보가 arm9 에 둘 이상 — 건너뜀')
                else:
                    for k, v in enumerate(vals): struct.pack_into('<H', a9, i + 2 * k, v)
                    wrote = 'arm9 @0x%X' % i
            if wrote: say('성도 도감 순서 씀: %d종 (%s), 칸 못 찾은 이름 %d: %s' % (len(order), wrote, len(miss), miss[:8]))
        except Exception as ex: problems.append('도감 순서 못 씀: %s' % ex)
    elif A.dex_order: problems.append('도감 순서는 arm9 를 압축 풀어 넣을 때만 씀(--keep-compressed 와 같이 못 씀)')
    if a9dec is None and (A.mart != 'none' or A.starters != 'none'): problems.insert(0, '스타팅·상점 표를 못 고침 — arm9 를 못 풀었음(--keep-compressed 를 썼거나 압축 풀기 실패)')
    if a9dec is not None and A.mart != 'none':
        # 10/14 문장 상점 판매: 일반 상점 표(arm9, {도구 u16, 배지 단계 u16} — pret scrcmd_mart.c _020FBF22, 단계 1=배지0 2=1~2 3=3~4 4=5~6 5=7 6=8+)
        # 도구 번호 차례(4바이트 간격)로만 찾음(단계 값은 디지골드가 바꿨을 수 있음). 여러 칸 「옛:새:단계,옛:새:단계」
        try:
            # 10/16 집 보고 「못 찾음」 원인: 찾던 차례가 틀렸음. pret scrcmd_mart.c _020FBF22 실제 차례 =
            #   몬스터볼4·수퍼볼3·하이퍼볼2·상처약17·좋은상처약26·고급상처약25·풀회복약24·회복약23·기력의조각28·해독제18·마비치료제22·잠깨는약21·화상치료제19·얼음상태치료제20·만병통치제27·동굴탈출로프78·벌레회피스프레이79·실버스프레이76·골드스프레이77
            a9 = a9dec[0]; seq = (4, 3, 2, 17, 26, 25, 24, 23); i = -1
            for pos in range(0, len(a9) - 80):
                if all(struct.unpack_from('<H', a9, pos + 4 * k)[0] == v for k, v in enumerate(seq)):
                    if i >= 0: i = -2; break
                    i = pos
            if i < 0: problems.insert(0, '일반 상점 표를 arm9 에서 %s — 문장 판매 건너뜀' % ('못 찾음' if i == -1 else '둘 이상 찾음')); say('일반 상점 표: %s' % ('못 찾음' if i == -1 else '둘 이상'))
            else:
                tiers = [struct.unpack_from('<H', a9, i + 4 * k + 2)[0] for k in range(8)]
                done_m = []
                for spec in A.mart.split(','):
                    old_it, new_it, tier = (int(x) for x in spec.split(':')); hit = False
                    for k in range(60):
                        it, tr = struct.unpack_from('<HH', a9, i + 4 * k)
                        if it == 0xFFFF or it == 0 or tr > 8: break
                        if it == old_it: struct.pack_into('<HH', a9, i + 4 * k, new_it, tier); hit = True; break
                    done_m.append('%d→%d(단계 %d)%s' % (old_it, new_it, tier, '' if hit else ' 못 찾음'))
                say('일반 상점 표 @0x%X(단계 값 %s): %s' % (i, tiers, ', '.join(done_m)))
        except Exception as ex: problems.append('상점 표 못 고침: %s' % ex)
    # 10/15 스타팅 세 마리: 연구소 스크립트(ChooseStarter)가 아니라 게임 코드 안 표에 152·155·158 로 박혀 있음(pret T20R0101.s). arm9·오버레이에서 찾아 바꿈
    if a9dec is not None and A.starters != 'none':
        try:
            a9 = a9dec[0]
            ev_path = A.starters if os.path.exists(A.starters) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_이벤트표.tsv')
            evrows = [r for r in csv.DictReader((l for l in open(ev_path, encoding='utf-8') if not l.startswith('#')), delimiter='\t')]
            name2slot = dict(slot)
            for r in draft:
                mm_ = re.search(r'디지골드 칸: (\S+)', r['메모'])
                if mm_ and mm_.group(1) in hg2.REPLACED_DEX: name2slot[r['이름']] = hg2.REPLACED_DEX[mm_.group(1)]
            st = {}
            for r in evrows:
                if r['종류'].strip() == '스타팅' and r['번호'].strip().isdigit() and r['우리 종'].strip() in name2slot: st[int(r['번호'])] = name2slot[r['우리 종'].strip()]
            if all(k in st for k in (152, 155, 158)):
                # 10/16 집 보고 「스타팅 그대로」 원인: 표는 u16 이 아니라 int(4바이트) 배열이고(pret choose_starter.c `const int species[]`, choose_starter_app.c `sSpecies[]`),
                #   디지골드가 이미 자기 스타팅(아구몬·파피몬·브이몬 칸)으로 바꿔 둠 → 하트골드 원래 값과 디지골드 값(차례 6가지) 모두 4바이트로 찾음.
                #   (전에는 u16 152·155·158 을 찾아 오버레이 80·99 의 엉뚱한 자료를 바꿨음 — 이제 안 함)
                import itertools
                dgs = [int(x) for x in A.dg_starters.split(',') if x.strip()]
                olds = [struct.pack('<3I', 152, 155, 158)] + ([struct.pack('<3I', *pm) for pm in itertools.permutations(dgs)] if len(dgs) == 3 else [])
                new_t = struct.pack('<3I', st[152], st[155], st[158]); where = []
                for old_t in olds:
                    n9 = a9.count(old_t)
                    if n9: a9[:] = a9.replace(old_t, new_t); where.append('arm9 %d곳(%s)' % (n9, list(struct.unpack('<3I', old_t))))
                d_ = out.d; y9o, y9s = struct.unpack_from('<II', d_, 0x50)
                for k in range(y9s // 32):
                    e = list(struct.unpack_from('<8I', d_, y9o + 32 * k)); fid, flag = e[6], e[7]
                    s_, t_ = out.fat(fid); ob = bytes(d_[s_:t_])
                    dec = hg_scan.blz_decompress(ob) if flag & 0x01000000 else ob
                    if not dec: continue
                    hits = [(o_, dec.count(o_)) for o_ in olds if o_ in dec]
                    if not hits: continue
                    nd = dec
                    for o_, _c in hits: nd = nd.replace(o_, new_t)
                    how_o = put_fid(out, fid, nd)
                    e[7] = 0; struct.pack_into('<8I', out.d, y9o + 32 * k, *e)       # 압축 아님으로 표시(크기 0·깃발 0)
                    where.append('오버레이 %d(%s, 압축 풀어 %s)' % (e[0], ', '.join('%s %d곳' % (list(struct.unpack('<3I', o_)), c_) for o_, c_ in hits), how_o))
                if where: say('스타팅 표(4바이트 3칸) → %d·%d·%d: %s' % (st[152], st[155], st[158], ', '.join(where)))
                else: problems.append('스타팅 표(4바이트 152·155·158 또는 디지골드 %s)를 arm9·오버레이에서 못 찾음 — 연구소 스타팅은 그대로' % dgs)
                if len(where) < 2: problems.append('스타팅 표를 %d곳만 바꿈 — 원래 두 곳(필드·고르기 화면). 폰에서 고르기 화면과 받은 디지몬이 같은지 확인' % len(where))
            else: problems.append('이벤트표에 스타팅 152·155·158 줄이 없어 스타팅 표는 건너뜀')
        except Exception as ex: problems.append('스타팅 표 못 고침: %s' % ex)
    if a9dec is not None:
        how = put_arm9(out, bytes(a9dec[0])); say('arm9 놓은 곳:', how)
    new_raw = bytes(out.d)
    if a9dec is not None:                                   # 검산: 새 롬의 arm9 가 압축 아님 + 표 값이 들어갔는지
        d2 = new_raw; o2, s2 = struct.unpack_from('<I', d2, 0x20)[0], struct.unpack_from('<I', d2, 0x2C)[0]
        ok9 = bytes(d2[o2:o2 + s2]) == bytes(a9dec[0])
        say('arm9 검산(롬에서 다시 읽어 같음): %s' % ('OK' if ok9 else '실패'))
        if not ok9: problems.append('arm9 검산 실패 — --keep-compressed 로 다시 돌릴 것')
    g2 = NARC(NDS(new_raw).get('a/0/2/0')).files; bad = 0
    for fi, rows in checks:
        if decode(g2[fi]) != rows: bad += 1; problems.append('검산 실패: 파일 %d' % fi)
    say('아이콘 넣음: %d종, 검산 실패 %d' % (done, bad))
    open(os.path.join(A.out, 'hg4i_test.nds'), 'wb').write(new_raw)
    base = open(A.base, 'rb').read() if A.base else raw
    patch = bps_make(base, new_raw); open(os.path.join(A.out, 'hg4i.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(base, patch) == new_raw else '실패'))
    say('\n== 문제 %d건' % len(problems)); [say('-', x) for x in problems[:100]]
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
