#!/usr/bin/env python3
"""배포판(src/dist) 정리: .orig 보관본 지우기, 디지몬 칸이 아닌 포켓몬 그림·울음소리 지우기."""
import os, re, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); DIST = os.path.join(ROOT, 'src', 'dist')
recs = json.loads(re.search(r'DIGIMON_RECORDS: DigimonRecord\[\] = (\[.*?\]);\n', open(os.path.join(ROOT, 'src/src/data/balance/digimon-data.ts'), encoding='utf-8').read(), re.S).group(1))
keep = {str(r['id']) for r in recs}
gone = 0
def rm(p):
    global gone
    gone += os.path.getsize(p); os.remove(p)
for dp, dn, fn in os.walk(DIST):
    for f in fn:
        if f.endswith('.orig'): rm(os.path.join(dp, f))
P = os.path.join(DIST, 'images/pokemon')
for sub in ('', 'back', 'shiny', 'back/shiny', 'female', 'female/shiny', 'back/female', 'back/female/shiny'):
    d = os.path.join(P, sub)
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p) and f.split('.')[0] not in keep: rm(p)
for sub in ('exp', 'variant'):
    d = os.path.join(P, sub)
    for dp, dn, fn in os.walk(d):
        for f in fn:
            if not f.startswith('_'): rm(os.path.join(dp, f))
for dp, dn, fn in os.walk(os.path.join(P, 'icons')):
    for f in fn:
        if re.sub(r's?\..*$', '', f).split('-')[0] not in keep: rm(os.path.join(dp, f))
C = os.path.join(DIST, 'audio/cry')
for f in os.listdir(C):
    if f.split('.')[0].split('_')[0].split('-')[0] not in keep: rm(os.path.join(C, f))
print('지운 용량 %.0fMB' % (gone / 1e6))
# 배경음악 64kbps 로 다시 압축(한 번 만든 건 tools/_bgm_cache 에 보관해 다음 빌드에 재사용)
import subprocess, hashlib
FF = shutil.which('ffmpeg') or r'C:\Users\skagn\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe'
CACHE = os.path.join(HERE, '_bgm_cache'); os.makedirs(CACHE, exist_ok=True)
B = os.path.join(DIST, 'audio/bgm'); before = after = 0
for f in sorted(os.listdir(B)):
    if not f.endswith('.mp3'): continue
    p = os.path.join(B, f); data = open(p, 'rb').read(); before += len(data)
    c = os.path.join(CACHE, hashlib.sha1(data).hexdigest()[:16] + '.mp3')
    if not os.path.exists(c):
        subprocess.run([FF, '-y', '-loglevel', 'error', '-i', p, '-b:a', '64k', c], check=True)
    shutil.copyfile(c, p); after += os.path.getsize(p)
print('배경음악 %.0fMB → %.0fMB' % (before / 1e6, after / 1e6))
