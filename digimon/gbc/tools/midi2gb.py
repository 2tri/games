"""MIDI → GBC 4채널 편곡 (포켓몬 금 소리 구성)
  ch1 네모파: 멜로디 · ch2 네모파: 화음/대선율 · ch3 파형: 베이스 · ch4 잡음: 드럼
MIDI 원본(music/src/*.mid)은 저장소에 올리지 않고, 편곡 결과(music/<곡>.json)만 올린다.
  python3 tools/midi2gb.py            # 모든 곡 다시 변환
json: {"bpm", "grid"(한 박 칸 수), "units"(곡 길이), "ch": [[[음, 길이], ...] × 4]}  음 0 = 쉼, 잡음 채널은 드럼 번호"""
import os, sys, json
import mido

HERE = os.path.dirname(os.path.abspath(__file__))
MUS = os.path.join(os.path.dirname(HERE), 'music')
SRC = os.path.join(MUS, 'src')

# 드럼 번호 (noise 채널) — 소리 엔진 DRUM 표와 같은 순서
KICK, SNARE, HAT, OHAT, CRASH, TOM = 1, 2, 3, 4, 5, 6
GM_DRUM = {35: KICK, 36: KICK, 37: SNARE, 38: SNARE, 39: SNARE, 40: SNARE, 42: HAT, 44: HAT, 46: OHAT,
           49: CRASH, 57: CRASH, 52: CRASH, 55: CRASH, 51: HAT, 59: HAT, 53: HAT,
           41: TOM, 43: TOM, 45: TOM, 47: TOM, 48: TOM, 50: TOM}
DRUM_PRIO = {CRASH: 6, SNARE: 5, KICK: 4, TOM: 3, OHAT: 2, HAT: 1}

# 곡 목록. 고르는 법: ('t', 트랙) 또는 ('c', 채널), 방식 top(가장 높은 음)·bottom(가장 낮은 음)·second(두 번째 높은 음)
# lo/hi: 그 음 범위만, 여섯째 값: 그 소스만 옮김(반음), <채널>_shift: 채널 전체 옮김(반음), 구간 start/end 는 박 단위
SONGS = {
    'title': dict(mid='butterfly.mid', start=0, end=96, grid=12,
                  lead=[('t', 1, 'top', 60, 127)], harm=[('t', 1, 'second', 48, 127)], bass=[('t', 1, 'bottom', 0, 57)],
                  drums='beat8'),
    'town': dict(mid='ashita.mid', start=0, end=128, grid=12,
                 lead=[('t', 1, 'top', 62, 127)], harm=[('t', 1, 'second', 52, 127)], bass=[('t', 1, 'bottom', 0, 60)],
                 drums='soft'),
    'field': dict(mid='target.mid', start=0, end=96, grid=12, beat=0.786, phase=0.285,      # 이 MIDI는 박이 어긋나 있어 실제 박(약 159bpm)으로 맞춤
                  lead=[('c', 0, 'top'), ('c', 1, 'top')], harm=[('c', 3, 'top')], bass=[('c', 8, 'bottom')],
                  drums=[('c', 9)], drummap={55: HAT, 51: HAT}),
    'village': dict(mid='butterfly_piano.mid', start=0, end=96, grid=12, bpm=96,
                    lead=[('t', 1, 'top'), ('t', 3, 'top')], harm=[('t', 3, 'second')], bass=[('t', 4, 'bottom')], drums='soft'),
    'battle': dict(mid='digimon_rock.mid', start=0, end=112, grid=12,
                   lead=[('c', 5, 'top'), ('c', 3, 'top'), ('c', 0, 'top')], harm=[('c', 1, 'top')], bass=[('c', 0, 'bottom')], bass_shift=-12,
                   drums=[('c', 9)], drummap={55: HAT, 59: HAT, 51: HAT, 53: HAT, 54: HAT, 31: KICK, 57: CRASH, 49: CRASH}, addkick=True),
    'boss': dict(mid='braveheart.mid', start=0, end=112, grid=12,
                 lead=[('t', 12, 'top'), ('t', 7, 'top')], harm=[('t', 1, 'top')], bass=[('t', 8, 'bottom')],
                 drums=[('t', 2), ('t', 3), ('t', 10)], drummap={34: KICK, 35: KICK, 36: KICK, 40: SNARE, 38: SNARE, 41: HAT, 46: OHAT, 44: HAT, 30: 0}),
    'evolve': dict(mid='braveheart.mid', start=0, end=24, grid=12, once=True,
                   lead=[('t', 7, 'top')], harm=[('t', 1, 'top')], bass=[('t', 8, 'bottom')],
                   drums=[('t', 2), ('t', 10)], drummap={34: KICK, 35: KICK, 36: KICK, 40: SNARE, 38: SNARE, 41: HAT, 46: OHAT, 44: HAT, 30: 0}),
}
# 롬판 추가 곡 (2026-10-04, 사용자 「게임 곳곳 디지몬 노래 배치」): 같은 MIDI 의 아직 안 쓴 구간 — 16박(4마디) 단위로 자름
SONGS.update({
    'town2': dict(SONGS['town'], start=128, end=224),                          # 내일은 나의 바람이 분다 뒷부분 → 관동 도시
    'field2': dict(SONGS['field'], start=96, end=192),                         # Target 뒷부분 → 관동 도로
    'cave': dict(SONGS['village'], start=96, end=192, bpm=84, drums='none'),    # Butterfly 피아노판 뒷부분, 느리게·드럼 없이 → 동굴·탑·유적
    'gym': dict(SONGS['boss'], start=112, end=208),                            # Brave Heart 뒷부분 → 체육관·아지트 걷기
    'encounter': dict(SONGS['battle'], start=0, end=32),                       # digimon 록 앞 2블록 → 트레이너·라이벌 눈 마주침
    'victory': dict(SONGS['title'], start=128, end=160),                       # Butter-Fly 뒷부분 8마디 → 승리
    # 2026-10-05 사용자 「안녕 디지몬 같은 노래는 잔잔하게 배경음으로」: 장숙희 「안녕 디지몬」(KBS 엔딩, 마장조) 피아노 MIDI 의 앞 12마디
    #   (전주 4 + 1절 8, midiex 공개 미리듣기 30초 — 전체 파일은 로그인·댓글이 있어야 받음). 오른손 = 멜로디(한 옥타브 내림), 왼손 위 = 펼침화음, 왼손 아래 = 베이스, 드럼 없음
    'annyeong': dict(mid='annyeong.mid', start=0, end=48, grid=12, bpm=100,
                     lead=[('t', 1, 'top')], lead_shift=-12, harm=[('t', 2, 'top', 50, 127), ('t', 1, 'second', 0, 127, -12)], bass=[('t', 2, 'bottom', 0, 49)], drums='none'),
})
# 회복 징글 (직접 작곡, 포켓몬 센터 느낌의 짧은 아르페지오) — [음(MIDI), 길이(칸)]
HEAL = dict(bpm=120, grid=12, once=True, ch=[
    [[72, 3], [76, 3], [79, 3], [84, 6], [0, 3], [79, 3], [84, 12], [0, 3]],
    [[64, 3], [67, 3], [72, 3], [76, 6], [0, 3], [72, 3], [76, 12], [0, 3]],
    [[48, 9], [0, 3], [43, 6], [48, 12], [0, 6]],
    [[0, 36]]])


# 짧은 징글 (직접 작곡): 물건 얻음 · 레벨업 · 포획 성공
JINGLES = {
    'item': dict(bpm=150, grid=12, once=True, ch=[
        [[79, 3], [79, 3], [79, 3], [84, 12], [0, 6]], [[76, 3], [76, 3], [76, 3], [79, 12], [0, 6]],
        [[48, 9], [55, 12], [0, 6]], [[3, 3], [3, 3], [3, 3], [5, 12], [0, 6]]]),
    'levelup': dict(bpm=150, grid=12, once=True, ch=[
        [[72, 3], [76, 3], [79, 3], [84, 6], [0, 3], [83, 3], [84, 12], [0, 3]], [[64, 3], [67, 3], [72, 3], [76, 6], [0, 3], [74, 3], [76, 12], [0, 3]],
        [[48, 12], [43, 6], [48, 18]], [[0, 36]]]),
    'capture': dict(bpm=140, grid=12, once=True, ch=[
        [[67, 3], [72, 3], [76, 3], [79, 6], [76, 3], [79, 18], [0, 3]], [[64, 3], [67, 3], [72, 3], [76, 6], [72, 3], [76, 18], [0, 3]],
        [[48, 12], [55, 6], [48, 18], [0, 3]], [[1, 6], [3, 6], [2, 6], [5, 18], [0, 3]]]),
}

def load(path):
    m = mido.MidiFile(path); tpb = m.ticks_per_beat
    notes = []; bpm = None
    for ti, t in enumerate(m.tracks):
        now = 0; on = {}
        for msg in t:
            now += msg.time
            if msg.type == 'set_tempo' and bpm is None: bpm = mido.tempo2bpm(msg.tempo)
            if msg.type == 'note_on' and msg.velocity > 0: on[(msg.channel, msg.note)] = now
            elif msg.type in ('note_off', 'note_on') and (msg.channel, msg.note) in on:
                s = on.pop((msg.channel, msg.note)); notes.append((ti, msg.channel, s / tpb, now / tpb, msg.note))
    return notes, bpm or 120


def pick(notes, sel):
    kind, n = sel[0], sel[1]
    return [x for x in notes if (x[0] if kind == 't' else x[1]) == n]


def voice(notes, sels, start, end, grid, ch, shift=0):
    """여러 소스(앞쪽 우선) → 칸마다 한 음. 반환: pitch[u], onset[u]"""
    U = int(round((end - start) * grid))
    pitch = [0] * U; onset = [False] * U; owner = [-1] * U
    for si, sel in enumerate(sels):
        mode = sel[2]; lo = sel[3] if len(sel) > 3 else 0; hi = sel[4] if len(sel) > 4 else 127
        sh = sel[5] if len(sel) > 5 else 0                                  # 이 소스만 옮김 (반음)
        src = [x[:4] + (x[4] + sh,) for x in pick(notes, sel) if lo <= x[4] <= hi]
        # 칸마다 그 소스에서 울리는 음들
        active = [[] for _ in range(U)]
        for (_, _, s, e, p) in src:
            a = int(round((s - start) * grid)); b = int(round((e - start) * grid))
            if b <= a: b = a + 1
            for u in range(max(0, a), min(U, b)): active[u].append((p, u == a))
        for u in range(U):
            if owner[u] != -1 or not active[u]: continue
            ps = sorted(active[u], key=lambda t: (-t[0], not t[1]))      # 같은 음이면 막 친 음 먼저
            if mode == 'top': c = ps[0]
            elif mode == 'bottom': c = min(active[u], key=lambda t: (t[0], not t[1]))
            elif mode == 'second':
                if len(ps) < 2: continue
                c = ps[1]
            pitch[u] = c[0]; onset[u] = c[1]; owner[u] = si
    # 음이 바뀌면 새로 침
    for u in range(U):
        if pitch[u] and (u == 0 or pitch[u - 1] != pitch[u] or owner[u - 1] != owner[u]): onset[u] = True
    # 음역 맞추기: 네모파 C2(36)~, 파형 C1(24)~
    lo, hi = (36, 96) if ch < 2 else (28, 72)
    for u in range(U):
        p = pitch[u] + shift if pitch[u] else 0
        while p and p < lo: p += 12
        while p and p > hi: p -= 12
        pitch[u] = p
    return pitch, onset


def drum_voice(notes, spec, start, end, grid, dmap):
    U = int(round((end - start) * grid))
    hit = [0] * U
    if isinstance(spec, list):
        for sel in spec:
            for (_, _, s, e, p) in pick(notes, sel):
                d = dmap.get(p, GM_DRUM.get(p, 0)) if dmap else GM_DRUM.get(p, 0)
                u = int(round((s - start) * grid))
                if d and 0 <= u < U and DRUM_PRIO[d] > DRUM_PRIO.get(hit[u], 0): hit[u] = d
    elif spec in ('beat8', 'soft'):          # 직접 만드는 박자: 8분 하이햇, 1·3 킥, 2·4 스네어
        g8 = grid // 2
        for u in range(0, U, g8):
            beat = (u // grid) % 4; on = (u % grid) == 0
            if spec == 'beat8':
                hit[u] = KICK if on and beat in (0, 2) else SNARE if on and beat in (1, 3) else HAT
            else:
                hit[u] = KICK if on and beat == 0 else HAT if on else 0
    return hit


def runs(pitch, onset):
    ev = []
    for u, p in enumerate(pitch):
        if ev and not onset[u] and ev[-1][0] == p: ev[-1][1] += 1
        elif ev and p == 0 and ev[-1][0] == 0: ev[-1][1] += 1
        else: ev.append([p, 1])
    out = []
    for p, n in ev:
        while n > 255: out.append([p, 255]); n -= 255
        out.append([p, n])
    return out


def convert(name, sp):
    notes, bpm = load(os.path.join(SRC, sp['mid']))
    if 'beat' in sp:        # MIDI 박 → 실제 박
        b, ph = sp['beat'], sp.get('phase', 0)
        notes = [(t, c, (s - ph) / b, (e - ph) / b, p) for (t, c, s, e, p) in notes]; bpm = bpm / b
    start, end, grid = sp['start'], sp['end'], sp['grid']
    U = int(round((end - start) * grid))
    chs = []
    for ch, key in enumerate(('lead', 'harm', 'bass')):
        p, o = voice(notes, sp[key], start, end, grid, ch, sp.get(key + '_shift', 0)); chs.append(runs(p, o))
    hit = drum_voice(notes, sp['drums'], start, end, grid, sp.get('drummap'))
    if sp.get('addkick'):       # 킥이 없는 MIDI: 1·3박에 킥
        for u in range(0, U, grid * 2):
            if hit[u] in (0, HAT, OHAT): hit[u] = KICK
    chs.append(runs(hit, [bool(h) for h in hit]))
    return dict(bpm=sp.get('bpm', round(bpm, 2)), grid=grid, units=U, once=sp.get('once', False), ch=chs)


if __name__ == '__main__':
    only = set(sys.argv[1:])                    # 곡 이름을 주면 그 곡만 (예: python3 tools/midi2gb.py cave gym)
    for name, sp in SONGS.items():
        if only and name not in only: continue
        if not os.path.exists(os.path.join(SRC, sp['mid'])): print('없음', sp['mid']); continue
        d = convert(name, sp)
        json.dump(d, open(os.path.join(MUS, name + '.json'), 'w'), separators=(',', ':'))
        print('%-8s %s bpm %.0f %d칸 이벤트 %s' % (name, sp['mid'], d['bpm'], d['units'], [len(c) for c in d['ch']]))
    if only: sys.exit()
    h = dict(HEAL); h['units'] = sum(n for _, n in h['ch'][0])
    json.dump(h, open(os.path.join(MUS, 'heal.json'), 'w'), separators=(',', ':'))
    for jn, j in JINGLES.items():
        j = dict(j); j['units'] = sum(n for _, n in j['ch'][0])
        json.dump(j, open(os.path.join(MUS, jn + '.json'), 'w'), separators=(',', ':'))
