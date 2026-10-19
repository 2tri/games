#!/usr/bin/env python3
"""풍성한 피아노판 만들기 (2026-10-14, 집 PC 전용)
사용:   python piano_get.py [--gbc 노래/gbc] [--only "Butter-Fly"] [--n 3]
준비:   pip install yt-dlp piano_transcription_inference   (torch 필요. 안 되면 pip install basic-pitch)
        ffmpeg (winget install ffmpeg)
        노래/gbc/ 에 GBC 세션이 올린 구간 MIDI 17개(digimon/music/nds_midi/*.mid 복사)
하는 일 (바탕곡마다, NDS_피아노출처.tsv 차례로)
 1) 후보 피아노 음원: 표의 「링크」(있으면 첫 후보) + 유튜브 검색 「검색어」 위 --n 개(8분 넘는 영상 뺌) → 노래/피아노/<바탕곡>_<k>.wav
 2) 피아노 자동 채보(piano_transcription_inference, 안 되면 basic-pitch) → 노래/피아노/<바탕곡>_<k>.mid   (피아노 독주 녹음이라 정확함)
 3) 후보마다 그 바탕곡의 GBC 구간들과 멜로디를 맞대어(midi_match) 평균 맞음 점수가 가장 높은 후보를 고름
 4) 고른 후보에서 GBC 구간마다 같은 부분을 잘라 노래/midi/<GBC 파일 이름>.mid (반복 시작·끝 표시 포함) → hg_song.py 가 그대로 씀
 결과: 피아노_고른것.txt (바탕곡마다 후보별 점수·고른 영상 제목·링크)  ※ 점수 0.7 아래뿐이면 「못 찾음」 — 링크를 표에 넣어 다시"""
import os, sys, re, csv, glob, json, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midi_match

def run(cmd):
    print('  $', ' '.join(cmd)); r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode: raise RuntimeError((r.stderr or r.stdout)[-500:])
    return r.stdout

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
            raise RuntimeError('채보 실패: %s / %s' % (str(e1)[-200:], str(e2)[-200:]))

def candidates(link, query, n):
    out = []
    if link: out.append(link)
    if query:
        try:
            js = run(['yt-dlp', '--flat-playlist', '-J', 'ytsearch%d:%s' % (n + 2, query)])
            for e in json.loads(js).get('entries', []):
                d = e.get('duration') or 0
                if d and d > 480: continue
                u = e.get('url') or ('https://www.youtube.com/watch?v=' + e['id'])
                if u not in out: out.append(u)
        except Exception as ex:
            print('  검색 실패:', str(ex)[-200:])
    return out[:n + (1 if link else 0)]

def main():
    H = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(); ap.add_argument('--gbc', default=os.path.join('노래', 'gbc'))
    ap.add_argument('--table', default=next((q for q in (os.path.join(H, 'NDS_피아노출처.tsv'), os.path.join(H, '..', 'NDS_피아노출처.tsv'), 'NDS_피아노출처.tsv') if os.path.exists(q)), 'NDS_피아노출처.tsv'))
    ap.add_argument('--only', default=''); ap.add_argument('--n', type=int, default=3)
    A = ap.parse_args()
    for d in ('노래/피아노', '노래/midi'): os.makedirs(d, exist_ok=True)
    rows = [r for r in csv.DictReader((l for l in open(A.table, encoding='utf-8') if not l.startswith('#')), delimiter='\t')]
    L = []
    for r in rows:
        base = r['바탕곡'].strip()
        if A.only and A.only != base: continue
        secs = [x.strip() for x in r['GBC 구간 파일'].split(',') if x.strip()]
        gfiles = [os.path.join(A.gbc, x + '.mid') for x in secs]
        gfiles = [g for g in gfiles if os.path.exists(g)]
        L.append('\n## %s — GBC 구간 %d개: %s' % (base, len(gfiles), ', '.join(secs)))
        if not gfiles: L.append('  GBC 구간 MIDI 없음(%s)' % A.gbc); continue
        safe = re.sub(r'[\\/:*?"<>|]', '_', base); best = None
        for k, url in enumerate(candidates(r.get('링크', '').strip(), r.get('검색어', '').strip(), A.n)):
            wav = os.path.join('노래', '피아노', '%s_%d.wav' % (safe, k)); mid = wav[:-4] + '.mid'
            try:
                title = '(전에 받은 것)'
                if not os.path.exists(mid):
                    title = run(['yt-dlp', '--get-title', '--no-playlist', url]).strip()
                    tmp = wav[:-4] + '_dl'
                    run(['yt-dlp', '-x', '--audio-format', 'wav', '--no-playlist', '-o', tmp + '.%(ext)s', url])
                    got = next(f for f in glob.glob(tmp + '.*'))
                    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', got, '-ac', '1', '-ar', '16000', wav])
                    tool = transcribe(wav, mid)
                else: tool = '(전에 만든 것)'
                scores = []
                for g in gfiles:
                    try: scores.append(midi_match.cut(mid, g, os.path.join('노래', '피아노', '_시험.mid'))['score'])
                    except Exception: scores.append(0.0)
                avg = sum(scores) / len(scores)
                L.append('  후보 %d: 평균 맞음 %.2f %s | %s | %s | 채보 %s' % (k, avg, [round(x, 2) for x in scores], title, url, tool))
                if best is None or avg > best[0]: best = (avg, mid, title, url)
            except Exception as e:
                L.append('  후보 %d 실패: %s | %s' % (k, url, str(e)[-200:]))
            print(L[-1])
        if not best or best[0] < 0.7:
            L.append('  → 못 찾음(가장 높은 점수 %.2f). 사용자에게 이 곡 피아노 영상 링크를 받아 NDS_피아노출처.tsv 「링크」에 넣고 --only 로 다시' % (best[0] if best else 0)); continue
        L.append('  → 고름: %s (%s)' % (best[2], best[3]))
        for g in gfiles:
            op = os.path.join('노래', 'midi', os.path.basename(g))
            try:
                c = midi_match.cut(best[1], g, op)
                L.append('     %s: 맞음 %.2f, 피아노 %.1f~%.1f초, 반복 시작 %.1f초, 음 %d개' % (os.path.basename(g), c['score'], c['start'], c['end'], c['loop'], c['notes']))
            except Exception as e:
                L.append('     %s: 자르기 실패 %s' % (os.path.basename(g), e))
    import shutil                                                          # 피아노판을 못 만든 구간은 GBC 판 그대로(소리는 나게)
    miss = []
    for g in sorted(glob.glob(os.path.join(A.gbc, '*.mid'))):
        op = os.path.join('노래', 'midi', os.path.basename(g))
        if not os.path.exists(op): shutil.copy(g, op); miss.append(os.path.basename(g))
    L.append('\n피아노판 없이 GBC 판 그대로 쓴 구간 %d: %s' % (len(miss), ', '.join(miss)))
    open('피아노_고른것.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L)); print('→ 피아노_고른것.txt')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
