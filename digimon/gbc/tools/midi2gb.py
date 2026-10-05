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
    # 2026-10-05 사용자 「브레이브 하트 맞는데 느낌이 없었네」: 전에는 멜로디 채널을 반짝이 반복음(7번 트랙, C7-B6-A6-G6)이 차지해 노래 선율이 안 들림
    #   → 멜로디 = 보컬(12번, 옥타브 겹침 중 C6 아래 맨 위) + 전주는 피아노(1번), 반짝이 반복음은 화음 채널로 한 옥타브 내림, 베이스 = 11번 → 8번
    #   사용자 「기타 소리 초반부가 핵심, 그게 나오면서 진화하니까 그 부분 살려」: 전주(0~48박) = 9번 기타 파워코드(F·G·Em·Am, 4박씩)를 화음 채널, 그 위 긴 선율(1번 A-E-D-G-B-C, 19번 C-B-C-G 받는 음)을 멜로디로
    'boss': dict(mid='braveheart.mid', start=0, end=112, grid=12,
                 lead=[('t', 12, 'top', 0, 83), ('t', 1, 'top'), ('t', 19, 'top')], harm=[('t', 9, 'top'), ('t', 7, 'top', 0, 127, -12), ('t', 18, 'top')], bass=[('t', 8, 'bottom'), ('t', 11, 'bottom')],
                 drums=[('t', 2), ('t', 3), ('t', 10)], drummap={34: KICK, 35: KICK, 36: KICK, 40: SNARE, 38: SNARE, 41: HAT, 46: OHAT, 44: HAT, 30: 0}),
    # 진화 = 애니 진화 장면 노래(사용자가 준 영상 「Digimon Adventure 01 Evolution Song」 = Brave Heart)
    #   진화 = 기타 전주(0~48박) 한 번 → 후렴(112~176박) 되풀이. 진화 장면 길이는 설계자 결정(기획.md 다음 작업 3)
    'evolve': dict(mid='braveheart.mid', intro=(0, 48), start=112, end=176, grid=12,
                   lead=[('t', 12, 'top', 0, 83), ('t', 1, 'top'), ('t', 19, 'top')], harm=[('t', 9, 'top'), ('t', 7, 'top', 0, 127, -12), ('t', 8, 'second')], bass=[('t', 8, 'bottom'), ('t', 11, 'bottom')],
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
    #   사용자 「맵 옮길 때마다 처음부터 나오는데 앞의 띠딩띠딩 4번이 거슬림, 한 번만 하고 바로 노래」: 전주는 1마디만 한 번, 반복은 1절부터
    # 2026-10-05 사용자 「대중적인 노래가 도로에서 나오면 좋겠네」: 도로 곡 두 개
    #   road1 = Butter-Fly 한 곡 전체 (절·후렴 160박, 전주 없음), road2 = The Biggest Dreamer (디지몬 테이머즈 OP, bitmidi):
    #   전주 리프는 1번만(0~16박), 반복은 48박부터 끝까지. 오른손 = 1번 트랙, 화음 = 2번 트랙 위, 베이스 = 3번 트랙 아래 한 옥타브 내림
    'road1': dict(SONGS['title'], start=0, end=160, drums='soft'),
    # 2026-10-05 사용자 「(트레이너 전투) Butter-Fly 는 자주 들리는 게 좋아, 아주 유명하고 감성 있으니까」 (Target·Brave Heart 는 모름): Butter-Fly 한 곡 전체, 드럼 그대로
    'trainer': dict(SONGS['title'], start=0, end=160),
    # 2026-10-05 사용자가 좋아하는 노래 — 「샘플링해 두고 나중에 쓸 수 있게」 (아직 게임 배치 안 함, 설계자와 정함)
    #   breakup = Break Up! (02 2기 오프닝, 한국판 파워디지몬 진화 테마) animezen 공개 미디: 박이 어긋나 있어 실제 박(0.94, 약 133bpm)으로 맞춤.
    #     멜로디 = 보컬(채널 5) → 전주 오보에(0) → 기타 리프(2), 화음 = 기타(4·8) → 전자피아노 둘째 음(3), 베이스 = 1
    'breakup': dict(mid='breakup.mid', start=0, end=208, grid=12, beat=0.94, phase=-0.117,
                    lead=[('c', 5, 'top'), ('c', 0, 'top'), ('c', 2, 'top')], harm=[('c', 4, 'top'), ('c', 8, 'top'), ('c', 3, 'second')],
                    bass=[('c', 1, 'bottom')], drums=[('c', 9)]),
    #   bolero = 라벨 「볼레로」 (애니 「우리들의 워 게임!」 오메가몬 장면) bitmidi 오케스트라 미디, 3/4·72bpm: 작은북 2마디 한 번 → 플루트 주제(15~63박) 되풀이.
    #     작은북(43번 = 이 미디의 작은북)·현악 피치카토 반주
    'bolero': dict(mid='bolero.mid', intro=(9, 15), start=15, end=63, grid=12,
                   lead=[('t', 1, 'top')], harm=[('t', 26, 'top')], bass=[('t', 26, 'bottom')], drums=[('t', 23)], drummap={43: SNARE}),
    'road2': dict(mid='bigdreamer.mid', intro=(0, 16), start=48, end=144, grid=12,
                  lead=[('t', 1, 'top')], harm=[('t', 2, 'top')], bass=[('t', 3, 'bottom')], bass_shift=-12, drums='soft'),
    'annyeong': dict(mid='annyeong.mid', intro=(12, 16), start=16, end=48, grid=12, bpm=100,
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
    grid = sp['grid']
    # intro=(시작, 끝): 곡 앞에 한 번만 나오는 구간 (그 뒤 start~end 를 반복, json loop_at = 반복 시작 칸)
    parts = ([sp['intro']] if 'intro' in sp else []) + [(sp['start'], sp['end'])]
    chs = [[] for _ in range(4)]; U = 0
    for start, end in parts:
        Up = int(round((end - start) * grid))
        for ch, key in enumerate(('lead', 'harm', 'bass')):
            p, o = voice(notes, sp[key], start, end, grid, ch, sp.get(key + '_shift', 0)); chs[ch] += runs(p, o)
        hit = drum_voice(notes, sp['drums'], start, end, grid, sp.get('drummap'))
        if sp.get('addkick'):       # 킥이 없는 MIDI: 1·3박에 킥
            for u in range(0, Up, grid * 2):
                if hit[u] in (0, HAT, OHAT): hit[u] = KICK
        chs[3] += runs(hit, [bool(h) for h in hit]); U += Up
    d = dict(bpm=sp.get('bpm', round(bpm, 2)), grid=grid, units=U, once=sp.get('once', False), ch=chs)
    if 'intro' in sp: d['loop_at'] = int(round((sp['intro'][1] - sp['intro'][0]) * grid))
    return d


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
