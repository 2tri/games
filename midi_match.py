#!/usr/bin/env python3
"""피아노 편곡에서 GBC 구간 잘라 내기 (2026-10-14)
사용:   python midi_match.py "<피아노 전곡.mid>" "<GBC 구간.mid>" --out "노래/midi/<곡>.mid"
        python midi_match.py "<피아노 전곡.mid>" 노래/gbc/*.mid --out-dir 노래/midi      (한 바탕곡에서 여러 구간)
하는 일
 - GBC 구간 MIDI(GBC 세션이 올린 것)의 멜로디(첫 파트)를 피아노 전곡의 「맨 윗음 줄」에서 찾는다.
   음 높이 차례로 맞대며(조옮김 12가지·옥타브 무시, 빠르기 무시 — 부분 DTW) 가장 잘 맞는 자리를 고른다.
 - 그 자리의 피아노 음 전부(양손)를 잘라 0초부터 다시 적고, GBC 의 반복 시작(loopStart)에 해당하는 자리에 loopStart, 끝에 loopEnd 마커를 넣는다.
 - 맞음 점수 = 멜로디 음 중 같은 음으로 짝지어진 비율(0~1). 0.7 아래면 다른 곡이거나 편곡이 많이 다른 것 → 다른 피아노 음원으로.
 - 피아노 편곡의 빠르기·조는 그대로 둔다(편곡자 연주 그대로)."""
import os, sys, struct, argparse, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg_song

def skyline(notes, gap=0.04):
    """동시에 친 음 묶음마다 맨 윗음 → [(시작초, 음)]"""
    out = []; cur = []
    for n in sorted(notes):
        if cur and n[0] - cur[0][0] > gap:
            out.append((cur[0][0], max(c[2] for c in cur))); cur = []
        cur.append(n)
    if cur: out.append((cur[0][0], max(c[2] for c in cur)))
    return out

def gbc_melody(path):
    parts, loop = hg_song.midi_parse(path); end = parts.pop(('끝', 0), None)
    keys = sorted(k for k in parts if k[1] != 9)
    mel = parts[keys[0]] if keys else []
    return [(n[0], n[2]) for n in sorted(mel)], loop or 0.0, (end[0][1] if end else max(n[1] for n in mel))

def subseq_dtw(q, s):
    """q 짧은 줄(음 높이), s 긴 줄 → (비용/길이, s 시작, s 끝, 경로 q→s). 조옮김 12가지 중 최선. 음 높이 차는 반음 차(옥타브 무시)."""
    best = None
    qa = np.array(q); sa = np.array(s)
    for tr in range(12):
        d = (qa[:, None] + tr - sa[None, :]) % 12; C = np.minimum(d, 12 - d) / 6.0     # 0~1
        n, m = C.shape; D = np.full((n, m), np.inf); B = np.zeros((n, m), np.int8)
        D[0] = C[0]
        for i in range(1, n):
            up = D[i - 1]; diag = np.r_[np.inf, D[i - 1][:-1]]
            # 왼쪽(같은 q 음에 s 여러 개 = 피아노 꾸밈음)은 줄 단위로 누적
            row = np.minimum(up + 0.5, diag)                     # 위로 = q 음 건너뜀(벌점), 대각선 = 짝
            src = np.where(diag <= up + 0.5, 1, 0)
            cur = row + C[i]
            k = 0.15 * np.arange(m)                               # 왼쪽 = s 음 건너뜀(꾸밈음, 작은 벌점): cur'[j] = min_k≤j cur[k] + 0.15(j-k)
            left = np.minimum.accumulate(cur - k) + k
            src = np.where(left < cur - 1e-12, 2, src); cur = np.minimum(cur, left)
            D[i] = cur; B[i] = src
        j_end = int(np.argmin(D[-1])); cost = D[-1][j_end] / n
        if best is None or cost < best[0]:
            path = []; i, j = n - 1, j_end
            while i > 0:
                path.append((i, j)); b = B[i][j]
                if b == 1: i, j = i - 1, j - 1
                elif b == 2: j -= 1
                else: i -= 1
            path.append((0, j)); path.reverse()
            best = (cost, path[0][1], j_end, path, tr)
    return best

def write_midi(path, parts, loop_sec, end_sec):
    """parts = [[(시작초, 끝초, 음, 세기)]] → 형식 1, 템포 120, 4분음표 480(1초 = 960틱)"""
    T = lambda x: int(round(x * 960))
    def trk(evs):
        evs.sort(key=lambda e: (e[0], e[1])); out = bytearray(); now = 0
        for t, _, b in evs: out += hg_song.vlq(t - now) + b; now = t
        out += b'\x00\xFF\x2F\x00'; return b'MTrk' + struct.pack('>I', len(out)) + bytes(out)
    t0 = [(0, 0, b'\xFF\x51\x03' + (500000).to_bytes(3, 'big')), (T(loop_sec), 1, b'\xFF\x06\x09loopStart'), (T(end_sec), 2, b'\xFF\x06\x07loopEnd')]
    tracks = [trk(t0)]
    for ch, ns in enumerate(parts):
        ev = [(0, 0, bytes([0xC0 | ch, 0]))]
        for s0, e, n, v in ns: ev.append((T(s0), 2, bytes([0x90 | ch, n, v]))); ev.append((T(e), 1, bytes([0x80 | ch, n, 0])))
        tracks.append(trk(ev))
    open(path, 'wb').write(b'MThd' + struct.pack('>IHHH', 6, 1, len(tracks), 480) + b''.join(tracks))

def cut(full_path, gbc_path, out_path):
    fparts, _ = hg_song.midi_parse(full_path); fparts.pop(('끝', 0), None)
    fall = sorted(n for ns in fparts.values() for n in ns)
    sky = skyline(fall); mel, loop, gend = gbc_melody(gbc_path)
    if len(mel) < 4 or len(sky) < len(mel) // 2: raise ValueError('음이 너무 적음')
    q = [p for _, p in mel]; sq = [p for _, p in sky]
    cost, js, je, path, tr = subseq_dtw(q, sq)
    hit = {i for i, j in path if (q[i] + tr - sq[j]) % 12 == 0}
    score = len(hit) / len(q)                                        # 멜로디 음 중 같은 음(조옮김 뒤)으로 짝지어진 비율
    t_start = sky[js][0]
    # GBC 곡 끝 = 마지막 멜로디 음 뒤 여유만큼, 같은 비율로
    q_dur = (mel[-1][0] - mel[0][0]) or 1; s_dur = (sky[je][0] - sky[js][0]) or 1; ratio = s_dur / q_dur
    t_end = sky[je][0] + (gend - mel[-1][0]) * ratio
    # 반복 시작: GBC loopStart 직후 첫 멜로디 음이 짝지어진 피아노 음
    li = next((i for i, (t, _) in enumerate(mel) if t >= loop - 1e-6), 0)
    lj = next((j for i, j in path if i == li), js)
    t_loop = max(0.0, sky[lj][0] - t_start - (mel[li][0] - loop) * ratio) if loop > 0 else 0.0
    out = []
    for k in sorted(fparts):
        ns = [(max(0.0, s0 - t_start), min(e, t_end) - t_start, n, v) for s0, e, n, v in fparts[k] if t_start - 0.02 <= s0 < t_end - 0.02]
        ns = [x for x in ns if x[1] > x[0]]
        if ns: out.append(ns)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    write_midi(out_path, out, t_loop, t_end - t_start)
    return dict(score=score, start=t_start, end=t_end, loop=t_loop, notes=sum(len(x) for x in out), transpose=tr, ratio=ratio)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('full'); ap.add_argument('gbc', nargs='+')
    ap.add_argument('--out'); ap.add_argument('--out-dir', default=os.path.join('노래', 'midi'))
    A = ap.parse_args(); log = []
    gl = [g for pat in A.gbc for g in (glob.glob(pat) or [pat])]
    for g in gl:
        op = A.out if (A.out and len(gl) == 1) else os.path.join(A.out_dir, os.path.basename(g))
        try:
            r = cut(A.full, g, op)
            m = '%s ← %s: 맞음 %.2f%s, 피아노 %d:%04.1f~%d:%04.1f, 반복 시작 %.1f초, 음 %d개, 빠르기 비 %.2f → %s' % (
                os.path.basename(g), os.path.basename(A.full), r['score'], ' (낮음 — 다른 음원으로)' if r['score'] < 0.7 else '',
                r['start'] // 60, r['start'] % 60, r['end'] // 60, r['end'] % 60, r['loop'], r['notes'], r['ratio'], op)
        except Exception as e:
            m = '%s ← %s: 실패 %s' % (os.path.basename(g), os.path.basename(A.full), e)
        print(m); log.append(m)
    open('피아노_맞춤.txt', 'a', encoding='utf-8').write('\n'.join(log) + '\n')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
