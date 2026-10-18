"""piano_get.py 를 고치지 않고 실행하는 얇은 껍데기 (Claude 작성, 2026-10-14).
이유: piano_get.candidates() 가 유튜브 「flat 검색」 결과에 길이가 안 실려 오면(duration 없음) 8분 넘는 영상도 통과시킨다 → 55분짜리 영상을 받아 채보하느라 몇 시간이 걸림.
하는 일: transcribe() 앞에서 wav 길이를 보고 8분(480초) 넘으면 바로 실패로 돌려 다음 후보로 넘어가게 한다. 나머지는 piano_get 그대로."""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piano_get
_orig = piano_get.transcribe
def transcribe(wav, mid):
    with wave.open(wav, 'rb') as w: sec = w.getnframes() / float(w.getframerate())
    if sec > 480:
        try: os.remove(wav)
        except OSError: pass
        raise RuntimeError('영상이 %.0f분이라 건너뜀(8분 넘음)' % (sec / 60))
    return _orig(wav, mid)
piano_get.transcribe = transcribe
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    piano_get.main()
