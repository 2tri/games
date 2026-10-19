#!/usr/bin/env python3
"""노래 바꾸기 (2026-10-14) — MIDI 를 DS 곡(SSEQ)으로 바꿔 롬의 SDAT 곡 자리에 넣는다. 롬 원본은 고치지 않고 새 롬을 쓴다.
사용:   python hg_song.py "<롬.nds>" --dry                       → 노래_배정결과.txt (어느 곡 자리에 무엇이 들어갈지만)
        python hg_song.py "<롬.nds>" [--midi 노래/midi] [--only 타이틀] [--out 노래.nds]
하는 일
 - NDS_노래배정.tsv 의 줄마다 「롬 곡 이름 규칙」에 맞는 곡(SEQ_GS_…)을 찾는다. 「_」로 끝나는 규칙은 앞머리, 아니면 이름 안에 든 것.
   「~」로 시작하면 정규식. 표의 위 줄이 먼저 잡는다. 곡이 「그대로」면 건드리지 않음.
 - <midi 폴더>/<곡>.mid 를 읽어(템포 바뀜·서스테인 페달 처리) 초 단위로 바꾼 뒤 템포 120, 48틱/박으로 다시 적는다.
   파트가 나뉜 MIDI(GBC 내보내기: 멜로디·화음·베이스·북)면 파트 그대로(북 = 10번 채널은 버림), 한 덩어리면 가장 높은 음 = 멜로디, 나머지 = 반주.
   마커 loopStart = 반복 시작, loopEnd = 곡 끝.
 - 악기: 원래 곡이 쓰던 뱅크를 그대로 두고, 원래 곡에서 음이 가장 많은 트랙의 악기 → 멜로디, 둘째 → 반주(--program 으로 강제 가능).
 - 곡 끝에서 처음으로 되돌아가 반복한다. 같은 곡을 여러 자리에 넣을 때는 SDAT 안에 데이터를 한 번만 넣고 위치표만 같이 가리킨다(뱅크가 다르면 따로).
 - 새 곡이 원래보다 많이 크면(3배 넘음) 경고 — 소리 메모리가 모자라 안 나올 수 있으니 구간을 줄이거나 --max-notes 를 낮춘다."""
import os, sys, re, csv, struct, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, bps_make, say
import sdat_scan

TPS = 96          # 템포 120, 48틱/박 → 1초 = 96틱
SDAT_PATH = 'data/sound/gs_sound_data.sdat'

# ---------------------------------------------------------------- MIDI 읽기
def vlq_read(d, p):
    v = 0
    while True:
        b = d[p]; p += 1; v = (v << 7) | (b & 0x7F)
        if not b & 0x80: return v, p

def midi_parse(path):
    """→ (파트 {(트랙, 채널): [(시작초, 끝초, 음, 세기)]}, 반복 시작초 또는 None)
       반복 표시 = 글·마커 메타에 「loop」(loopStart 등) 또는 CC111. 드럼 채널(10)은 버림, 서스테인 페달은 음 길이로."""
    d = open(path, 'rb').read()
    if d[:4] != b'MThd': raise ValueError('MIDI 가 아님: %s' % path)
    hl = struct.unpack_from('>I', d, 4)[0]; fmt, ntr, div = struct.unpack_from('>HHH', d, 8)
    if div & 0x8000: raise ValueError('SMPTE 시간 MIDI 는 못 읽음')
    p = 8 + hl; evs = []; tempos = [(0, 500000)]; loop_tick = None; end_tick = None
    for ti in range(ntr):
        if d[p:p + 4] != b'MTrk': break
        ln = struct.unpack_from('>I', d, p + 4)[0]; q = p + 8; end = q + ln; t = 0; rs = 0
        while q < end:
            dt, q = vlq_read(d, q); t += dt; st = d[q]
            if st & 0x80: q += 1
            else: st = rs
            if st == 0xFF:
                ty = d[q]; ml, q2 = vlq_read(d, q + 1); data = d[q2:q2 + ml]; q = q2 + ml
                if ty == 0x51: tempos.append((t, int.from_bytes(data, 'big')))
                if ty in (0x01, 0x06) and b'loop' in data.lower():
                    if b'end' in data.lower(): end_tick = t
                    elif loop_tick is None: loop_tick = t
                if ty == 0x2F: break
                continue
            if st in (0xF0, 0xF7):
                ml, q = vlq_read(d, q); q += ml; continue
            rs = st; hi = st & 0xF0; ch = st & 0x0F
            if hi in (0xC0, 0xD0): q += 1; continue
            x, y = d[q], d[q + 1]; q += 2
            if ch == 9: continue
            key = (ti, ch)
            if hi == 0x90 and y: evs.append((t, 'on', x, y, key))
            elif hi == 0x80 or (hi == 0x90 and not y): evs.append((t, 'off', x, 0, key))
            elif hi == 0xB0 and x == 64: evs.append((t, 'ped', y >= 64, 0, key))
            elif hi == 0xB0 and x == 111 and loop_tick is None: loop_tick = t
        p = end
    tempos.sort()
    def sec(tick):
        s0 = 0.0; lt, lu = 0, 500000
        for tt, us in tempos:
            if tt >= tick: break
            s0 += (tt - lt) * lu / div / 1e6; lt, lu = tt, us
        return s0 + (tick - lt) * lu / div / 1e6
    evs.sort(key=lambda e: (e[0], e[1] != 'off'))
    on = {}; parts = collections.defaultdict(list); ped = collections.defaultdict(bool); held = collections.defaultdict(list)
    for t, k, x, y, key in evs:
        s0 = sec(t)
        if k == 'on':
            if (key, x) in on: parts[key].append((on[key, x][0], s0, x, on[key, x][1]))
            on[key, x] = (s0, y)
        elif k == 'off':
            if (key, x) in on:
                if ped[key]: held[key].append(x)
                else: parts[key].append((on[key, x][0], s0, x, on[key, x][1])); del on[key, x]
        else:
            ped[key] = x
            if not x:
                for n in held[key]:
                    if (key, n) in on: parts[key].append((on[key, n][0], s0, n, on[key, n][1])); del on[key, n]
                held[key] = []
    last = max([e[1] for ns in parts.values() for e in ns] + [0])
    for (key, n), (s0, v) in on.items(): parts[key].append((s0, last, n, v))
    cut = sec(end_tick) if end_tick else 1e9                              # loopEnd 뒤 음은 버리고, 걸친 음은 거기서 끊음
    out = {k: sorted((a0, min(e, a0 + 2.0, cut), n, v) for a0, e, n, v in ns if e > a0 and a0 < cut - 1e-6) for k, ns in parts.items()}
    out = {k: v for k, v in out.items() if v}
    if end_tick and out: out[('끝', 0)] = [(cut - 0.01, cut, 0, 1)]         # 곡 길이를 loopEnd 에 맞추는 표시(아래에서 뺌)
    return out, (sec(loop_tick) if loop_tick else None)

def midi_notes(path):
    """→ [(시작초, 끝초, 음, 세기)] 파트를 다 합친 것"""
    return sorted(n for k, ns in midi_parse(path)[0].items() if k != ('끝', 0) for n in ns)

def cap_poly(notes, k=3):
    keep = []
    for n in sorted(notes, key=lambda n: (n[0], -n[3])):
        if len([q for q in keep if q[1] > n[0]]) < k: keep.append(n)
    return sorted(keep)

# ---------------------------------------------------------------- 나누기
def split(notes, max_acc=3, max_notes=2500, all_acc=False):
    """가장 높은 음 → 멜로디(한 음씩), 나머지 → 반주(동시 max_acc 음)."""
    notes = sorted(notes)[:max_notes * 2]
    groups = []; cur = []
    for n in notes:
        if cur and n[0] - cur[0][0] > 0.03: groups.append(cur); cur = []
        cur.append(n)
    if cur: groups.append(cur)
    mel = []; acc = []
    for g in groups:
        top = max(g, key=lambda n: n[2])
        if top[2] >= 55 and not all_acc: mel.append(top); rest = [n for n in g if n is not top]
        else: rest = g
        acc += rest
    for i in range(len(mel) - 1):                                   # 멜로디는 다음 음에서 끊음
        if mel[i][1] > mel[i + 1][0]: mel[i] = (mel[i][0], mel[i + 1][0], mel[i][2], mel[i][3])
    keep = []
    for n in sorted(acc, key=lambda n: (n[0], -n[3])):
        alive = [k for k in keep if k[1] > n[0]]
        if len(alive) < max_acc: keep.append(n)
    keep.sort()
    return mel[:max_notes], keep[:max_notes]

# ---------------------------------------------------------------- SSEQ 쓰기
def vlq(n):
    n = max(0, int(n)); b = [n & 0x7F]; n >>= 7
    while n: b.append(0x80 | (n & 0x7F)); n >>= 7
    return bytes(reversed(b))

def track_bytes(notes, prog, total, loop_t=0, vol=127, pan=64):
    """한 트랙 → (머리, 반복 몸통). 머리 = 악기·볼륨 + 반복 시작 전 음(도입), 몸통 = 반복 시작부터 끝까지.
       노트는 기다리지 않게(C7 00) 두고 쉼표로 시간을 민다."""
    head = bytearray(b'\x81' + vlq(prog) + bytes([0xC1, vol, 0xC0, pan, 0xC7, 0]))
    def emit(buf, ns, now, until):
        for s0, e, n, v in ns:
            t = int(round(s0 * TPS)); dur = max(1, int(round((e - s0) * TPS)))
            if t > now: buf += b'\x80' + vlq(t - now); now = t
            buf += bytes([n & 0x7F, max(1, min(127, v))]) + vlq(dur)
        if until > now: buf += b'\x80' + vlq(until - now)
    pre = [n for n in notes if int(round(n[0] * TPS)) < loop_t]; post = [n for n in notes if int(round(n[0] * TPS)) >= loop_t]
    if loop_t: emit(head, pre, 0, loop_t)
    body = bytearray(); emit(body, post, loop_t, total)
    return bytes(head), bytes(body)

def make_sseq(tracks, loop_sec=None, tempo=120, end_sec=None):
    """tracks = [(notes, prog)] → SSEQ 파일. 0번 트랙이 다른 트랙을 열고(93), 모두 몸통 끝에서 반복 시작점으로 뛴다(94)."""
    total = int(round(end_sec * TPS)) if end_sec else int(round(max([n[1] for ns, _ in tracks for n in ns] + [1]) * TPS)) + 24
    loop_t = int(round(loop_sec * TPS)) if loop_sec and loop_sec * TPS < total else 0
    parts = [track_bytes(ns, pg, total, loop_t) for ns, pg in tracks]
    mask = (1 << len(parts)) - 1
    t0_pre = 3 + 5 * (len(parts) - 1) + 3                          # FE mask, 93×(n-1), E1 tempo
    offs = []; o = t0_pre
    for h, b in parts: offs.append(o); o += len(h) + len(b) + 4   # +94 jump(4)
    data = bytearray(b'\xFE' + struct.pack('<H', mask))
    for i in range(1, len(parts)): data += bytes([0x93, i]) + offs[i].to_bytes(3, 'little')
    data += b'\xE1' + struct.pack('<H', tempo)
    for i, (h, b) in enumerate(parts):
        assert len(data) == offs[i]
        data += h; loop = len(data); data += b + b'\x94' + loop.to_bytes(3, 'little')
    data += b'\xFF'
    while len(data) % 4: data += b'\0'
    size = 0x1C + len(data)
    return b'SSEQ' + struct.pack('<HHIHH', 0xFEFF, 0x0100, size, 0x10, 1) + b'DATA' + struct.pack('<II', size - 0x10, 0x1C) + bytes(data)

def sbnk_instruments(f):
    """→ [(번호, 종류)] 빈 칸 뺌. 종류 1 PCM 2 PSG 3 잡음 16 드럼 17 건반나눔"""
    if f[:4] != b'SBNK': return []
    n = struct.unpack_from('<I', f, 0x38)[0]; out = []
    for i in range(min(n, 512)):
        ty = f[0x3C + 4 * i]
        if ty: out.append((i, ty))
    return out

KIND = {1: 'PCM', 2: 'PSG', 3: '잡음', 16: '드럼', 17: '건반나눔'}
def instrument_test(insts):
    """악기마다 2.5초: 도·미·솔·높은도. → (SSEQ, 표 줄)"""
    data = bytearray(b'\xFE\x01\x00\xE1' + struct.pack('<H', 120) + bytes([0xC1, 127, 0xC0, 64, 0xC7, 1]))
    rows = []
    for k, (i, ty) in enumerate(insts):
        t = k * 2.5; rows.append('%d:%04.1f  악기 %d (%s)' % (t // 60, t % 60, i, KIND.get(ty, ty)))
        data += b'\x81' + vlq(i)
        for n, du in ((60, 24), (64, 24), (67, 24), (72, 48)): data += bytes([n, 110]) + vlq(du)
        data += b'\x80' + vlq(120)
    data += b'\xFF'
    while len(data) % 4: data += b'\0'
    size = 0x1C + len(data)
    return b'SSEQ' + struct.pack('<HHIHH', 0xFEFF, 0x0100, size, 0x10, 1) + b'DATA' + struct.pack('<II', size - 0x10, 0x1C) + bytes(data), rows

# ---------------------------------------------------------------- SSEQ 읽기(원래 곡의 악기 고르기·검사용)
ARG1 = set(range(0xC0, 0xD8))
def sseq_tracks(f):
    """→ {트랙: {'prog': [..], 'notes': [음..]}} (부르기·조건은 따라가지 않는 단순 훑기)"""
    if f[:4] != b'SSEQ': return {}
    base = struct.unpack_from('<I', f, 0x18)[0]; d = f[base:]
    starts = {0: 0}; info = {}
    p = 0
    if d[:1] == b'\xFE': p = 3
    while p < len(d) and d[p] == 0x93:
        starts[d[p + 1]] = int.from_bytes(d[p + 2:p + 5], 'little'); p += 5
    starts[0] = p
    for tr, st in starts.items():
        r = info.setdefault(tr, {'prog': [], 'notes': []}); p = st; steps = 0
        while p < len(d) and steps < 200000:
            steps += 1; c = d[p]; p += 1
            pre = 0
            if c in (0xA0, 0xA1, 0xA2):
                pre = c; c = d[p]; p += 1
            if c < 0x80:
                p += 1
                if pre == 0xA0: p += 4
                elif pre == 0xA1: p += 1
                else: _, p = vlq_read(d, p)
                r['notes'].append(c)
            elif c in (0x80, 0x81):
                if pre == 0xA0: p += 4
                elif pre == 0xA1: p += 1
                else:
                    v, p = vlq_read(d, p)
                    if c == 0x81: r['prog'].append(v)
            elif c == 0x93: p += 4
            elif c == 0x94: break
            elif c == 0x95: p += 3
            elif 0xB0 <= c <= 0xBD: p += 3 if pre != 0xA0 else 5
            elif c in ARG1: p += 1 if not pre else (4 if pre == 0xA0 else 1)
            elif c in (0xE0, 0xE1, 0xE3): p += 2 if not pre else (4 if pre == 0xA0 else 1)
            elif c == 0xFE: p += 2
            elif c in (0xFC, 0xFD): continue
            elif c == 0xFF: break
            else: break
    return info

FALLBACK_BANK = 750      # 멜로디 악기가 있는 뱅크(10/16 집: 뱅크 750 = PCM 42 + 건반나눔 39)
MELODIC = {1, 17}           # SBNK 악기 종류: 1 PCM, 17 건반나눔 = 음높이 있는 악기. 2 PSG(삑삑)·3 잡음·16 드럼 세트는 멜로디로 안 씀

def bank_types(d, info, fat, bank):
    """뱅크 번호 → {악기 번호: 종류}"""
    try:
        bfid = struct.unpack_from('<H', info['BANK'][bank], 0)[0]
        return dict(sbnk_instruments(d[fat[bfid][0]:fat[bfid][0] + fat[bfid][1]]))
    except Exception: return {}

def pick_programs(orig, types=None):
    """원래 곡에서 음이 많은 트랙의 악기 차례로 — 10/15: 드럼(16)·잡음(3)·PSG(2)·빈 칸은 빼고 고름(집 보고: 39번 드럼 세트를 멜로디로 골라 「맞는 소리」가 남)"""
    tr = sorted(sseq_tracks(orig).values(), key=lambda r: -len(r['notes']))
    progs = []
    for r in tr:
        for pg in r['prog']:
            if r['notes'] and (types is None or types.get(pg) in MELODIC) and pg not in progs: progs.append(pg)
    if not progs and types: progs = [k for k, v in sorted(types.items()) if v in MELODIC][:2]
    if not progs: return 0, 0
    return progs[0], progs[1] if len(progs) > 1 else progs[0]

def check_sseq(f, types=None):
    """만든 곡 검사 → 문제 목록(빈 목록이면 통과). 트랙 수·끝 표시·뛰는 자리·악기 종류·크기"""
    bad = []
    if f[:4] != b'SSEQ': return ['머리말 SSEQ 아님']
    size = struct.unpack_from('<I', f, 8)[0]
    if size != len(f): bad.append('크기 칸 %d ≠ 실제 %d' % (size, len(f)))
    base = struct.unpack_from('<I', f, 0x18)[0]; d = f[base:]
    if d[:1] != b'\xFE': bad.append('첫 명령이 트랙 할당(FE) 아님')
    mask = struct.unpack_from('<H', d, 1)[0]; n = bin(mask).count('1')
    if n > 8: bad.append('트랙 %d개(8 넘음)' % n)
    p = 3
    while p < len(d) and d[p] == 0x93:
        off = int.from_bytes(d[p + 2:p + 5], 'little')
        if off >= len(d): bad.append('트랙 시작 자리 %d 가 곡 밖' % off)
        p += 5
    q = 0
    while True:
        q = d.find(b'\x94', q)
        if q < 0: break
        tgt = int.from_bytes(d[q + 1:q + 4], 'little') if q + 4 <= len(d) else -1
        q += 1
    info = sseq_tracks(f)
    if len(info) != n: bad.append('트랙 할당 %d 인데 읽힌 트랙 %d' % (n, len(info)))
    for t, r in info.items():
        if not r['notes']: bad.append('트랙 %d 음 없음' % t)
        for pg in r['prog']:
            if types is not None and types.get(pg) not in MELODIC: bad.append('트랙 %d 악기 %d 종류 %s(멜로디 악기 아님)' % (t, pg, types.get(pg, '없음')))
    if len(f) > 12000: bad.append('곡이 %d바이트(12000 넘음 — 소리 메모리 부족 위험)' % len(f))
    return bad

# ---------------------------------------------------------------- SDAT 고치기
def sdat_put_files(d, newfiles):
    """newfiles = {파일번호: 데이터} → FILE 블록 끝에 붙이고 위치표를 바꾼 새 SDAT. 같은 데이터는 한 번만 붙인다."""
    d = bytearray(d)
    fat_o = struct.unpack_from('<I', d, 0x20)[0]; file_o, file_s = struct.unpack_from('<II', d, 0x28)
    end = file_o + file_s
    if end != len(d): d = d[:max(end, len(d))]
    placed = {}
    for fid, data in newfiles.items():
        key = bytes(data)
        if key not in placed:
            while len(d) % 0x20: d += b'\0'
            placed[key] = len(d); d += data
        struct.pack_into('<II', d, fat_o + 12 + 16 * fid, placed[key], len(data))
    while len(d) % 0x20: d += b'\0'
    struct.pack_into('<I', d, 0x2C, len(d) - file_o); struct.pack_into('<I', d, file_o + 4, len(d) - file_o)
    struct.pack_into('<I', d, 0x08, len(d))
    return bytes(d)

def seq_entry_off(d, i):
    info_o = struct.unpack_from('<I', d, 0x18)[0]
    ro = struct.unpack_from('<I', d, info_o + 8)[0]; eo = struct.unpack_from('<I', d, info_o + ro + 4 + 4 * i)[0]
    return info_o + eo if eo else None

# ---------------------------------------------------------------- 배정
def load_rules(path):
    """표 줄 차례 그대로(위 줄이 먼저 잡음)"""
    out = []
    for r in csv.DictReader((l for l in open(path, encoding='utf-8') if not l.startswith('#')), delimiter='	'):
        k = (r.get('우리 칸') or '').strip()
        if k: out.append((k, (r.get('곡') or '').strip(), [x.strip() for x in (r.get('롬 곡 이름 규칙(SEQ_GS_… 접두어, 쉼표 = 여럿)') or '').split(',') if x.strip()]))
    return out

def match(name, pats):
    n = name.upper()
    for pre in ('SEQ_GS_', 'SEQ_'):
        if n.startswith(pre): n = n[len(pre):]; break
    for p in pats:
        if p.startswith('~'):
            if re.search(p[1:], n): return True
        elif p.endswith('_'):
            if n.startswith(p.upper()): return True
        elif p.upper() in n: return True
    return False

def assign(names, rules):
    """→ {곡 번호: (자리, 노래)}. 10/16 집 보고: 효과음(SEQ_SE_…)까지 규칙(T_·GAME·SLOT 등)에 걸려 창 열기·슬롯 소리가 노래로 바뀌던 것 → 효과음은 절대 안 바꿈"""
    got = {}
    for i, nm in enumerate(names):
        if not nm or nm.upper().startswith('SEQ_SE'): continue
        for slot, song, pats in rules:
            if match(nm, pats): got[i] = (slot, song); break
    return got

def main():
    H = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(); ap.add_argument('rom')
    ap.add_argument('--table', default=next((q for q in (os.path.join(H, 'NDS_노래배정.tsv'), os.path.join(H, '..', 'NDS_노래배정.tsv'), 'NDS_노래배정.tsv') if os.path.exists(q)), 'NDS_노래배정.tsv')); ap.add_argument('--midi', default=os.path.join('노래', 'midi'))
    ap.add_argument('--out', default='노래.nds'); ap.add_argument('--only', default=''); ap.add_argument('--dry', action='store_true')
    ap.add_argument('--program', default='', help='악기 번호 강제: 하나면 모든 트랙(피아노), 쉼표면 트랙 차례로')
    ap.add_argument('--bank', type=int, default=-1, help='바꾼 곡이 쓸 뱅크를 이 번호로(피아노가 든 뱅크 — 악기 시험 때 쓴 뱅크)')
    ap.add_argument('--test-instruments', action='store_true', help='타이틀 곡 자리에 악기 시험곡을 넣음 → 악기표.txt')
    ap.add_argument('--max-notes', type=int, default=2500)
    ap.add_argument('--speed', type=float, default=0.5, help='빠르기 배율(10/15 사용자: 폰 빠른 배속에서 정상으로 들리게 절반)')
    ap.add_argument('--poly', type=int, default=5, help='반주 트랙 동시 음 수(피아노 풍성함). 소리가 끊기거나 안 나면 3으로')
    A = ap.parse_args()
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    sp = SDAT_PATH if SDAT_PATH in rom.paths else next((p for p in rom.paths if p.lower().endswith('.sdat')), None)
    if sp is None: print('실패: 롬에 소리 묶음(SDAT)이 없음 — 하트골드 구조 롬인지 확인'); sys.exit(1)
    d = rom.get(sp); names, info, fat = sdat_scan.parse_sdat(d)
    rules = load_rules(A.table); got = assign(names['SEQ'], rules)
    L = ['== 노래 배정 — %s (곡 %d개 중 %d개가 규칙에 걸림)' % (sp, len(names['SEQ']), len(got))]
    per = collections.defaultdict(list)
    for i, (slot, song) in sorted(got.items()): per[(slot, song)].append(i)
    for slot, song, pats in rules:
        ids = per.get((slot, song), [])
        L.append('\n[%s] 곡 「%s」 규칙 %s → %d곡' % (slot, song, ','.join(pats), len(ids)))
        L += ['   %4d %s' % (i, names['SEQ'][i]) for i in ids]
    left = [i for i, nm in enumerate(names['SEQ']) if nm and i not in got and info['SEQ'][i]]
    L.append('\n[안 걸린 곡 %d개 — 설계자가 규칙을 더함]' % len(left)); L += ['   %4d %s' % (i, names['SEQ'][i]) for i in left]
    newfiles = {}; made = {}; bank_set = []; own_bank = {}; placed = set()
    if A.test_instruments:
        tid = next((i for i, (slot, _) in sorted(got.items()) if slot == '타이틀'), None)
        if tid is None: tid = next(i for i, nm in enumerate(names['SEQ']) if 'TITLE' in nm.upper())
        fid, _u, bank = struct.unpack_from('<HHH', info['SEQ'][tid], 0)
        bfid = struct.unpack_from('<H', info['BANK'][bank], 0)[0]
        insts = sbnk_instruments(d[fat[bfid][0]:fat[bfid][0] + fat[bfid][1]])
        seq, rows = instrument_test(insts); newfiles[fid] = seq
        open('악기표.txt', 'w', encoding='utf-8').write('타이틀 화면(%s, 뱅크 %d)에서 시작부터 들으며 피아노처럼 들리는 시각을 찾아 그 줄의 악기 번호를 적으세요.\n2.5초마다 도·미·솔·도 한 번. 끝나면 처음부터 다시 나오지 않으니 타이틀을 다시 띄우세요.\n\n' % (names['SEQ'][tid], bank) + '\n'.join(rows) + '\n')
        L.append('악기 시험곡 → %s (뱅크 %d, 악기 %d개) — 악기표.txt' % (names['SEQ'][tid], bank, len(insts)))
    # 10/16: 곡 파일 하나를 여러 곡 항목이 같이 씀(예: 타이틀과 29번도로가 파일 1) → 규칙 표 위쪽(먼저 적힌 자리)이 그 파일을 차지하고, 뒤 자리는 덮지 않음
    rule_rank = {slot_: k for k, (slot_, _s, _p) in enumerate(rules)}
    file_owner = {}
    order_ = sorted(got.items(), key=lambda kv: (rule_rank.get(kv[1][0], 999), kv[0]))
    for i, (slot, song) in (order_ if not (A.test_instruments or A.dry) else []):
        if song == '그대로' or (A.only and A.only not in (slot, song)): continue
        e0 = info['SEQ'][i]
        if e0:
            fid0 = struct.unpack_from('<H', e0, 0)[0]
            if fid0 in file_owner:
                if file_owner[fid0][1] != song: L.append('건너뜀 %4d %s ← %s: 곡 파일 %d 을 먼저 「%s」(%s)가 차지 — 같은 파일이라 따로 못 넣음' % (i, names['SEQ'][i], song, fid0, file_owner[fid0][1], file_owner[fid0][0]))
                continue
            file_owner[fid0] = (slot, song)
        mp = os.path.join(A.midi, song + '.mid')
        if not os.path.exists(mp): L.append('MIDI 없음: %s (%s)' % (mp, slot)); continue
        e = info['SEQ'][i]
        if not e: continue
        fid, _u, bank = struct.unpack_from('<HHH', e, 0)
        orig = d[fat[fid][0]:fat[fid][0] + fat[fid][1]]
        types = bank_types(d, info, fat, A.bank if A.bank >= 0 else bank)
        # 10/16 집: 뱅크 701 처럼 삑삑이(PSG)·잡음뿐이라 멜로디 악기가 없는 뱅크의 곡 항목은 멜로디 악기가 많은 뱅크(750)로 바꿔 쓴다(안 그러면 「악기 0 종류 2」로 검사 실패 → 원래 곡이 남음)
        if A.bank < 0 and not any(v in MELODIC for v in types.values()):
            types = bank_types(d, info, fat, FALLBACK_BANK); own_bank[i] = FALLBACK_BANK; bank = FALLBACK_BANK
        if A.program: pl = [int(x) for x in A.program.split(',')]
        else: pl = list(pick_programs(orig, types))
        key = (song, tuple(pl))
        if key not in made:
            parts, loop = midi_parse(mp); endmark = parts.pop(('끝', 0), None)
            mp2 = os.path.join(A.midi, song + '_멜로디.mid')
            if len(parts) >= 2 and not os.path.exists(mp2):                 # 이미 나뉜 편곡(GBC 처럼 멜로디·화음·베이스): 파트 그대로, 많은 차례로 8개까지
                tr = sorted(parts.values(), key=lambda ns: -len(ns))[:8]
                tracks = [(cap_poly(ns, A.poly), pl[k % len(pl)]) for k, ns in enumerate(tr)]
                desc = '파트 %d개 그대로' % len(tracks)
            else:
                if os.path.exists(mp2):
                    mel, _ = split(midi_notes(mp2), max_notes=A.max_notes); _, acc = split(midi_notes(mp), max_acc=A.poly, max_notes=A.max_notes, all_acc=True)
                else:
                    mel, acc = split(midi_notes(mp), max_acc=A.poly, max_notes=A.max_notes)
                tracks = [(mel, pl[0]), (acc, pl[1 % len(pl)])]; desc = '멜로디 %d음, 반주 %d음' % (len(mel), len(acc))
            made[key] = make_sseq(tracks, loop, tempo=max(20, int(round(120 * A.speed))), end_sec=endmark[0][1] if endmark else None)
            bad_ = check_sseq(made[key], types)
            if bad_:
                L.append('검사 실패 「%s」 악기 %s: %s → 이 곡은 넣지 않음(원래 곡 그대로)' % (song, pl, '; '.join(bad_[:4]))); made[key] = None
            L.append('만듦 「%s」 악기 %s: %s, 반복 시작 %s, %d바이트' % (song, pl, desc, '%.1f초' % loop if loop else '처음', len(made[key] or b'')))
        if made[key] is None: continue
        # 10/16 집 패치: 같은 곡 파일을 뱅크가 다른 항목이 같이 쓰면, 그 뱅크들로도 검사를 통과해야 덮음
        _bad_sh = []
        for _j, _x in enumerate(info['SEQ']):
            if not _x or _j == i: continue
            _f2, _u2, _b2 = struct.unpack_from('<HHH', _x, 0)
            if _f2 != fid or _b2 == bank: continue
            _r = check_sseq(made[key], bank_types(d, info, fat, A.bank if A.bank >= 0 else _b2))
            if _r: _bad_sh.append((_j, _b2, _r[0]))
        if _bad_sh:
            L.append('건너뜀 %4d %s ← %s: 곡 파일 %d 을 같이 쓰는 %d개 항목의 뱅크로는 검사 실패(예: 곡 %d 뱅크 %d: %s) → 덮지 않음(원래 곡 그대로)' % (i, names['SEQ'][i], song, fid, len(_bad_sh), _bad_sh[0][0], _bad_sh[0][1], _bad_sh[0][2])); continue
        newfiles[fid] = made[key]; placed.add(i)
        if A.bank >= 0: bank_set.append(i)
        if len(made[key]) > 3 * max(1, len(orig)): L.append('경고 %d %s: 새 곡 %d바이트 > 원래 %d의 3배 — 소리가 안 나면 구간을 줄이세요' % (i, names['SEQ'][i], len(made[key]), len(orig)))
        L.append('넣음 %4d %s ← %s (뱅크 %d%s)' % (i, names['SEQ'][i], song, bank, ' → %d' % A.bank if A.bank >= 0 else (' → %d(멜로디 악기가 없는 뱅크라 바꿈)' % own_bank[i] if i in own_bank else ' 그대로')))
    if not A.dry or A.test_instruments:
        if newfiles:
            nd = bytearray(sdat_put_files(d, newfiles))
            for i in bank_set: struct.pack_into('<H', nd, seq_entry_off(nd, i) + 4, A.bank)
            for i, b_ in own_bank.items():
                if i in placed: struct.pack_into('<H', nd, seq_entry_off(nd, i) + 4, b_)
            nd = bytes(nd); how = rom.put(sp, nd)
            new_raw = bytes(rom.d); open(A.out, 'wb').write(new_raw)
            open(os.path.splitext(A.out)[0] + '.bps', 'wb').write(bps_make(raw, new_raw))
            L.append('\n→ %s (SDAT %d → %d바이트, %s)' % (A.out, len(d), len(nd), how))
        else: L.append('\n바꾼 곡 없음(MIDI 가 없거나 --dry)')
    open('노래_배정결과.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:3])); print('… 전체는 노래_배정결과.txt')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
