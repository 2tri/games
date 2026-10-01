"""반지의 제왕 영화 음악(온라인 시퀀서 편곡) → 게임보이 소리 3채널(포켓몬처럼)
가장 높은 음 = 멜로디(사각파1), 두 번째 = 화음(사각파2), 가장 낮은 음 = 베이스(파형 채널) → src/music_data.c"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import osq
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = HERE + '/../src'
MUSIC_BANK = 12
# 이름, 온라인 시퀀서 번호, 쓸 길이(16분음표 칸, 0=전부)
SONGS = [
    ('TITLE', 5739553, 0),      # 원정대 테마
    ('SHIRE', 5228855, 576),    # Concerning Hobbits (앞부분 반복)
    ('BATTLE', 5213925, 0),     # 로한 — 황금 궁전의 왕
    ('BOSS', 5330844, 0),       # 나즈굴 행진
    ('STORY1', 5771384, 0),     # 반지의 제왕 메인 테마
    ('STORY2', 2750359, 0),     # 미나스 티리스
    ('STORY3', 2174072, 0),     # 곤도르
    ('END', 4233195, 0),        # Into the West
]
def voices(notes, limit):
    """같은 시작 칸끼리 묶어 높은 음·둘째 음·낮은 음으로 세 줄을 만든다."""
    by = {}
    for n in notes:
        t = int(round(n['time']))
        if limit and t >= limit: continue
        by.setdefault(t, []).append((n['type'] + 12, max(1, int(round(n['len'])))))
    end = limit or max(t + max(l for _, l in v) for t, v in by.items())
    lines = [[], [], []]
    for t in sorted(by):
        ps = sorted(set(p for p, _ in by[t]), reverse=True); ln = {p: l for p, l in by[t]}
        top = ps[0]; low = ps[-1] if len(ps) > 1 and ps[-1] <= top - 7 else None
        mid = next((p for p in ps[1:] if p != low and p < top), None)
        lines[0].append((t, top, ln[top]))
        if mid is not None: lines[1].append((t, mid, ln[mid]))
        if low is not None: lines[2].append((t, low, ln[low]))
    return lines, end
def fit(p, lo, hi):
    while p < lo: p += 12
    while p > hi: p -= 12
    return p
def stream(line, end, lo, hi):
    """(시작, 음, 길이) → [음, 칸] 바이트. 쉼표는 음 0."""
    out = []; cur = 0
    for i, (t, p, l) in enumerate(line):
        if t > cur: out += [(0, t - cur)]; cur = t
        nxt = line[i + 1][0] if i + 1 < len(line) else end
        d = max(1, min(l, nxt - t)); out += [(fit(p, lo, hi), d)]; cur = t + d
        if nxt > cur: out += [(0, nxt - cur)]; cur = nxt
    if end > cur: out += [(0, end - cur)]
    b = []
    for p, d in out:
        while d > 255: b += [p, 255]; d -= 255; p = 0 if p == 0 else p
        b += [p, d]
    return b + [255]
out = ['#pragma bank %d' % MUSIC_BANK, '#include <stdint.h>']
tab = []
total = 0
for name, sid, limit in SONGS:
    bpm, notes = osq.load(sid)
    lines, end = voices(notes, limit)
    chs = [stream(lines[0], end, 48, 96), stream(lines[1], end, 48, 90), stream(lines[2], end, 28, 64)]
    for c, b in enumerate(chs): out.append('const uint8_t M_%s_%d[] = {%s};' % (name, c, ','.join(map(str, b)))); total += len(b)
    fpt = round(3600 / (bpm * 4) * 256)        # 한 칸(16분음표)이 몇 프레임인지 (8.8 고정소수)
    tab.append('{%d, {M_%s_0, M_%s_1, M_%s_2}}' % (fpt, name, name, name))
    print(name, 'bpm', bpm, '칸', end, '바이트', sum(map(len, chs)))
out.append('typedef struct { uint16_t fpt; const uint8_t *ch[3]; } Song;')
out.append('const Song SONGS[] = {%s};' % ','.join(tab))
assert total < 16000, total
open(SRC + '/music_data.c', 'w').write('\n'.join(out) + '\n')
open(SRC + '/music.h', 'w').write('#include <stdint.h>\n#define MUSIC_BANK %d\nenum { %s, MUS_NONE = 255 };\nvoid music_play(uint8_t id);\nvoid music_stop(void);\nuint8_t music_cur(void);\n' % (
    MUSIC_BANK, ', '.join('MUS_' + n for n, _, _ in SONGS)))
print('합계', total, '바이트')
