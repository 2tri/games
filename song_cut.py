#!/usr/bin/env python3
"""노래 받기·자르기·채보 (2026-10-14) — 「노래_링크.txt」 줄마다 소리를 받아 구간을 자르고 MIDI 를 만든다(집 PC 전용).
사용:   python song_cut.py [노래_링크.txt] [--len 50] [--only "Butter-Fly"] [--no-sep]
줄 형식:  곡 이름 | 유튜브 링크 | 구간
  구간 = 「0:14~1:30」(그대로) / 「0:14~」(거기서 16마디 — 게임 반복곡처럼 마디 단위로 끊음, --bars 로 바꿈)
        / 「참고 <하이라이트 영상 링크>」 또는 「참고 <링크> @3:10~3:55」(누가 만든 하이라이트·TV판 영상에서 이 곡이 나오는 자리)
          → 그 영상 소리와 원곡 소리를 맞대어 「같은 부분」을 원곡에서 찾아 원곡 음원으로 자른다(@ 를 안 주면 가장 길게 겹치는 부분)
필요: yt-dlp, ffmpeg (없으면 pip install yt-dlp / winget install ffmpeg), numpy.
      채보 = piano_transcription_inference(먼저) → 안 되면 basic-pitch. 보컬 분리 = demucs(있으면, 없으면 통째로 채보).
하는 일
 1) yt-dlp 로 소리만 → 노래/원본/<곡>.wav (22050Hz 모노로 바꿈)
 2) 구간: 「참고」면 하이라이트 영상과 원곡을 화음 모양(크로마)으로 맞대어 같은 부분을 찾는다(빠르기가 같은 음원일 때 잘 맞음).
    시작·끝은 박자 맞춤(소리 세기가 튀는 자리)으로 살짝 옮겨 반복할 때 덜 튀게 한다. → 노래/구간/<곡>.wav, 고른 자리는 노래/구간/고른자리.txt
 3) demucs 가 있으면 보컬 → 멜로디(<곡>_멜로디.mid), 나머지(보컬 뺀 소리) → 반주(<곡>.mid). 없으면 통째로 <곡>.mid
    hg_song.py 는 <곡>_멜로디.mid 가 있으면 그걸 멜로디 트랙으로 쓴다."""
import os, sys, re, wave, struct, shutil, argparse, subprocess
import numpy as np

SR = 22050

def run(cmd):
    print('  $', ' '.join(cmd)); r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode: raise RuntimeError((r.stderr or r.stdout)[-600:])
    return r.stdout

def tsec(s):
    s = s.strip()
    if not s: return None
    p = [float(x) for x in s.split(':')]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0]

def read_wav(p):
    w = wave.open(p, 'rb'); n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
    a = np.frombuffer(w.readframes(n), dtype=np.int16 if sw == 2 else np.int32).astype(np.float32)
    a = a.reshape(-1, ch).mean(1) / (32768.0 if sw == 2 else 2 ** 31); return a, w.getframerate()

def write_wav(p, a, sr=SR):
    a = np.clip(a, -1, 1); w = wave.open(p, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((a * 32767).astype(np.int16).tobytes()); w.close()

# ------------------------------------------------------------- 특징
HOP = 2048            # 약 0.093초
def features(a, sr=SR):
    n = 4096; win = np.hanning(n); frames = max(1, (len(a) - n) // HOP)
    idx = np.arange(n)[None, :] + HOP * np.arange(frames)[:, None]
    spec = np.abs(np.fft.rfft(a[idx] * win, axis=1))
    freqs = np.fft.rfftfreq(n, 1 / sr); ok = (freqs > 55) & (freqs < 4000)
    pc = np.round(12 * np.log2(freqs[ok] / 440.0)).astype(int) % 12
    chroma = np.zeros((frames, 12))
    for k in range(12): chroma[:, k] = spec[:, ok][:, pc == k].sum(1)
    chroma /= chroma.sum(1, keepdims=True) + 1e-9
    rms = np.sqrt((a[idx] ** 2).mean(1))
    flux = np.r_[0, np.maximum(0, np.diff(np.log1p(spec[:, :200]), axis=0)).sum(1)]
    return chroma, rms, flux

def find_chorus(a, length, sr=SR, skip_intro=8.0):
    """→ (시작초, 끝초, 점수). 창 = length 초. 반복 = 같은 창이 lag≥length/2 떨어진 다른 자리와 얼마나 닮았나."""
    chroma, rms, flux = features(a, sr); F = len(chroma); W = int(length * sr / HOP); step = max(1, int(1.0 * sr / HOP))
    if F <= W + 2: return 0.0, len(a) / sr, 0.0
    # 박자 맞춤용으로 1초 단위 요약
    S = chroma @ chroma.T                                                  # 프레임끼리 닮음
    best = (-1, 0)
    starts = range(int(skip_intro * sr / HOP), F - W, step)
    loud = rms / (rms.max() + 1e-9)
    for s in starts:
        rep = 0.0
        for o in range(0, F - W, step):
            if abs(o - s) < W // 2: continue
            d = np.diagonal(S[s:s + W, o:o + W]).mean()
            rep = max(rep, d)
        score = rep * 0.7 + loud[s:s + W].mean() * 0.3
        if score > best[0]: best = (score, s)
    s = best[1]
    def snap(f):                                                           # 근처 ±0.5초 안 소리 튐이 가장 큰 프레임
        r = max(1, int(0.5 * sr / HOP)); lo, hi = max(0, f - r), min(F - 1, f + r)
        return lo + int(np.argmax(flux[lo:hi + 1])) if hi > lo else f
    s2 = snap(s); e2 = snap(s2 + W)
    return s2 * HOP / sr, e2 * HOP / sr, float(best[0])

def _norm(c):
    return c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-9)

def match_ref(a, ref, sr=SR, win=None):
    """원곡 a 안에서 참고 소리 ref 와 같은 부분 → (원곡 시작초, 원곡 끝초, 닮음 0~1, 참고 시작초).
       win=(시작,끝) 이면 참고의 그 구간을 원곡에서 미끄러뜨려 가장 닮은 자리. 없으면 대각선마다 「계속 닮은 가장 긴 줄」."""
    A = _norm(features(a, sr)[0]).astype(np.float32); B = _norm(features(ref, sr)[0]).astype(np.float32)
    fs = HOP / sr
    if win:
        b0, b1 = int(win[0] / fs), int(win[1] / fs); Bw = B[b0:b1]; W = len(Bw)
        if W < 4 or W >= len(A): raise ValueError('참고 구간이 너무 짧거나 원곡보다 김')
        S = A @ Bw.T
        sc = np.array([np.trace(S[o:o + W]) / W for o in range(len(A) - W)])
        o = int(np.argmax(sc)); return o * fs, (o + W) * fs, float(sc[o]), win[0]
    S = A @ B.T; best = (0, 0, 0, 0.0)                                  # (길이, 원곡 시작, 참고 시작, 닮음)
    k = 5; ker = np.ones(k) / k
    for d in range(-(len(B) - 1), len(A)):
        diag = np.diagonal(S, offset=-d) if d >= 0 else np.diagonal(S, offset=-d)
        if len(diag) < 20: continue
        sm = np.convolve(diag, ker, 'same'); good = sm > 0.85
        run = 0
        for i, g in enumerate(good):
            run = run + 1 if g else 0
            if run > best[0]:
                st = i - run + 1; ai, bi = (st + d, st) if d >= 0 else (st, st - d)
                best = (run, ai, bi, float(diag[st:i + 1].mean()))
    n, ai, bi, simv = best
    if n == 0: raise ValueError('겹치는 부분 못 찾음 — 다른 음원(편곡·키 다름)일 수 있음')
    return ai * fs, (ai + n) * fs, simv, bi * fs

def bars_len(a, st, bars=16, sr=SR):
    """시작점부터 마디 수만큼의 길이(초). 빠르기는 소리 튐의 자기상관으로 60~180 BPM 사이에서 어림, 4/4 박자로 봄."""
    seg = a[int(st * sr):int((st + 60) * sr)]; h = 256; fs = h / sr
    env = np.log1p(100 * np.sqrt((seg[:len(seg) // h * h].reshape(-1, h) ** 2).mean(1)))
    f = np.maximum(0, np.diff(env)); f = f - f.mean(); ac = np.correlate(f, f, 'full')[len(f) - 1:]
    lags = np.arange(len(ac)) * fs; ok = np.where((lags >= 60 / 180) & (lags <= 60 / 60))[0]
    if len(ok):
        i = ok[int(np.argmax(ac[ok]))]
        if 0 < i < len(ac) - 1:                                             # 꼭짓점 보간
            y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]; dd = (y0 - y2) / (2 * (y0 - 2 * y1 + y2) + 1e-12); beat = (i + dd) * fs
        else: beat = i * fs
    else: beat = 0.5
    L = bars * 4 * beat
    while L > 70: L /= 2
    while L < 25: L *= 2
    return L, 60 / beat

def snap_range(a, st, en, sr=SR):
    _, _, flux = features(a, sr); F = len(flux)
    def snap(t):
        f = int(t * sr / HOP); r = max(1, int(0.3 * sr / HOP)); lo, hi = max(0, f - r), min(F - 1, f + r)
        return (lo + int(np.argmax(flux[lo:hi + 1]))) * HOP / sr if hi > lo else t
    return snap(st), snap(en)

# ------------------------------------------------------------- 채보
def transcribe(wav, mid):
    try:
        from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
        import torch
        audio, _ = load_audio(wav, sr=sample_rate, mono=True)
        PianoTranscription(device='cuda' if torch.cuda.is_available() else 'cpu', checkpoint_path=None).transcribe(audio, mid)
        return 'piano_transcription_inference'
    except Exception as e1:
        try:
            from basic_pitch.inference import predict
            _, md, _ = predict(wav); md.write(mid); return 'basic-pitch'
        except Exception as e2:
            raise RuntimeError('채보 도구 둘 다 실패: %s / %s' % (str(e1)[-200:], str(e2)[-200:]))

def separate(wav, outdir):
    """demucs 로 보컬·나머지 → (보컬 wav, 반주 wav) 또는 None"""
    if not shutil.which('demucs'):
        try: import demucs  # noqa
        except Exception: return None
    try:
        run([sys.executable, '-m', 'demucs', '--two-stems', 'vocals', '-o', outdir, wav])
        base = os.path.splitext(os.path.basename(wav))[0]
        for root, _, fs in os.walk(outdir):
            if os.path.basename(root) == base and 'vocals.wav' in fs:
                return os.path.join(root, 'vocals.wav'), os.path.join(root, 'no_vocals.wav')
    except Exception as e:
        print('  demucs 실패:', str(e)[-200:])
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('links', nargs='?', default='노래_링크.txt')
    ap.add_argument('--len', type=float, default=50.0); ap.add_argument('--bars', type=int, default=16); ap.add_argument('--only', default=''); ap.add_argument('--no-sep', action='store_true')
    ap.add_argument('--cut-only', action='store_true', help='채보 없이 자르기까지만')
    A = ap.parse_args()
    for d in ('노래/원본', '노래/구간', '노래/midi', '노래/분리'): os.makedirs(d, exist_ok=True)
    log = []
    for line in open(A.links, encoding='utf-8'):
        if not line.strip() or line.startswith('#'): continue
        c = [x.strip() for x in line.split('|')] + ['', '']
        name, url, rng = c[0], c[1], c[2]
        if A.only and A.only != name: continue
        safe = re.sub(r'[\\/:*?"<>|]', '_', name)
        try:
            src = os.path.join('노래', '원본', safe + '.wav')
            if not os.path.exists(src):
                tmp = os.path.join('노래', '원본', safe + '_dl')
                run(['yt-dlp', '-x', '--audio-format', 'wav', '--no-playlist', '-o', tmp + '.%(ext)s', url])
                got = next(f for f in os.listdir(os.path.join('노래', '원본')) if f.startswith(safe + '_dl'))
                run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join('노래', '원본', got), '-ac', '1', '-ar', str(SR), src])
            a, _ = read_wav(src)
            if rng.startswith('참고'):
                m = re.match(r'참고\s+(\S+)(?:\s*@\s*([\d:.]+)\s*~\s*([\d:.]+))?', rng)
                rurl, w0, w1 = m.group(1), m.group(2), m.group(3)
                rp = os.path.join('노래', '원본', safe + '_참고.wav')
                if not os.path.exists(rp):
                    tmp = os.path.join('노래', '원본', safe + '_참고dl')
                    run(['yt-dlp', '-x', '--audio-format', 'wav', '--no-playlist', '-o', tmp + '.%(ext)s', rurl])
                    got = next(f for f in os.listdir(os.path.join('노래', '원본')) if f.startswith(safe + '_참고dl'))
                    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join('노래', '원본', got), '-ac', '1', '-ar', str(SR), rp])
                ref, _ = read_wav(rp)
                st, en, simv, rs = match_ref(a, ref, win=(tsec(w0), tsec(w1)) if w0 else None)
                st, en = snap_range(a, st, en)
                how = '참고 영상 %d:%04.1f 부분과 같은 자리(닮음 %.2f%s)' % (rs // 60, rs % 60, simv, ' — 낮음, 다른 편곡일 수 있음' if simv < 0.8 else '')
            elif rng in ('', '자동'):
                st, en, sc = find_chorus(a, A.len); how = '자동(반복·큰 소리 기준 — 참고 영상이 없을 때만 임시)' 
            else:
                st, en = (rng.split('~') + [''])[:2]; st = tsec(st) or 0.0; en = tsec(en); how = '지정 %s' % rng
                if en is None:
                    L, bpm = bars_len(a, st, A.bars); en = st + L; how += ' → %d마디(빠르기 약 %d) %.1f초' % (A.bars, bpm, L)
                st, en = snap_range(a, st, en)
            en = min(en, len(a) / SR)
            seg = a[int(st * SR):int(en * SR)].copy(); f = int(0.02 * SR)
            if len(seg) > 2 * f: seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
            cut = os.path.join('노래', '구간', safe + '.wav'); write_wav(cut, seg)
            msg = '%s: %d:%04.1f~%d:%04.1f (%.1f초) %s' % (name, st // 60, st % 60, en // 60, en % 60, en - st, how)
            if not A.cut_only:
                mid = os.path.join('노래', 'midi', safe + '.mid'); sep = None if A.no_sep else separate(cut, os.path.join('노래', '분리'))
                if sep:
                    t1 = transcribe(sep[0], os.path.join('노래', 'midi', safe + '_멜로디.mid')); t2 = transcribe(sep[1], mid)
                    msg += ' / 보컬 분리 O, 멜로디=%s 반주=%s' % (t1, t2)
                else:
                    msg += ' / 분리 X, 채보=%s' % transcribe(cut, mid)
            print(msg); log.append(msg)
        except Exception as e:
            m = '%s: 실패 — %s' % (name, str(e)[-300:]); print(m); log.append(m)
    open(os.path.join('노래', '구간', '고른자리.txt'), 'w', encoding='utf-8').write('\n'.join(log) + '\n')
    print('→ 노래/구간/고른자리.txt')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
