"""GBC 판 편곡(music/<곡>.json) → 표준 MIDI (형식 1) — 2부(NDS)에서 DS 악기로 다시 넣기용 (2026-10-14 설계자 요청)
  python3 tools/json2mid.py          → ../music/nds_midi/<곡 이름>.mid + README.md
트랙: 0 = 템포·마커(loopStart, 곡 끝 = 반복 끝) / 1 멜로디(펄스1) / 2 화음(펄스2) / 3 베이스(웨이브) / 4 북(노이즈 → GM 드럼, 채널 10)
템포 = 롬 엔진에 들어간 정수 템포에서 거꾸로 계산한 실제 빠르기 (빨리감기 배수 MUSIC_FF 를 빼고 1배 기준).
옥타브: midi2gb 의 채널 단위 옮김(lead_shift·harm_shift·bass_shift)은 되돌림. 소스 하나만 옮긴 것·음역 맞추기(자동 옥타브 접기)는 음마다 기록이 없어 그대로."""
import os, sys, json
import mido

HERE = os.path.dirname(os.path.abspath(__file__)); GBC = os.path.dirname(HERE)
MUS = os.path.join(GBC, 'music'); OUT = os.path.join(os.path.dirname(GBC), 'music', 'nds_midi')
sys.path.insert(0, HERE); import midi2gb as M
sys.path.insert(0, os.path.join(os.path.dirname(GBC), 'romhack')); import music as RM

TPB = 480
GM = {1: 36, 2: 38, 3: 42, 4: 46, 5: 49, 6: 45}      # 우리 드럼 번호 → GM 타악기
# (파일 이름, json, 원래 곡, MIDI 출처, GBC 장면)
SONGS = [
    ('Butter-Fly', 'title', 'Butter-Fly (디지몬 어드벤처 OP) 앞 96박', '출처 기록 없음', '제목·오프닝·명예의 전당'),
    ('Butter-Fly_전체', 'trainer', 'Butter-Fly 0~160박', '출처 기록 없음', '트레이너 전투 (도로 앞쪽 road1 도 같은 구간, 북만 약하게)'),
    ('찬란한 빛', 'victory', '「찬란한 빛」 없음 → Butter-Fly 뒷부분 128~160박을 대신 씀', '출처 기록 없음', '트레이너·야생·관장 이김'),
    ('Butter-Fly_피아노판', 'village', 'Butter-Fly 피아노판 앞 96박', '출처 기록 없음', '도라지·금빛·인주·디지몬센터·자연공원'),
    ('Butter-Fly_피아노판_동굴', 'cave', 'Butter-Fly 피아노판 96~192박 (84bpm, 북 없음)', '출처 기록 없음', '동굴·탑·등대·유적'),
    ('내일은 나의 바람이 분다', 'town', '내일은 나의 바람이 분다 앞 128박', '출처 기록 없음', '성도 마을·겐나이 연구소·라디오 이야기'),
    ('내일은 나의 바람이 분다_뒷부분', 'town2', '내일은 나의 바람이 분다 128~224박', '출처 기록 없음', '관동 도시·석영고원·배·자기열차·게임코너'),
    ('Target', 'field', 'Target ~붉은 섬광~ 앞 96박', '출처 기록 없음', '파도타기·자전거·벌레잡기 대회'),
    ('Brave Heart', 'boss', 'Brave Heart 앞 112박', '출처 기록 없음', '관장·챔피언·라이벌 전투'),
    ('Brave Heart_체육관', 'gym', 'Brave Heart 112~208박', '출처 기록 없음', '체육관·암흑단 아지트·챔피언 로드'),
    ('Power Up!', 'evolve', '「Power Up!」 없음 → Brave Heart 기타 전주(0~48박) + 후렴(112~176박)을 대신 씀', '출처 기록 없음', '진화 장면'),
    ('Break Up!', 'breakup', 'Break Up! (02 2기 OP) 0~208박', 'animezen 공개 MIDI', '롬에 안 넣음 (만들어만 둠)'),
    ('안녕 디지몬', 'annyeong', '안녕 디지몬 (KBS 엔딩) 전주 1마디 + 1절 8마디', 'midiex 공개 미리듣기 30초', '연두마을·엄마·처음 메뉴·자장가·엔딩'),
    ('The Biggest Dreamer', 'road2', 'The Biggest Dreamer (테이머즈 OP) 전주 16박 + 48~144박', 'bitmidi', '34번 이후 도로·관동 11~15·26·27번 도로'),
    ('digimon 록', 'battle', '「digimon 록」 편곡 앞 112박 (원곡 이름 기록 없음)', '출처 기록 없음', '야생 전투'),
    ('digimon 록_눈마주침', 'encounter', '「digimon 록」 앞 32박', '출처 기록 없음', '트레이너·라이벌·암흑단 눈 마주침'),
    ('볼레로', 'bolero', '라벨 볼레로 작은북 2마디 + 플루트 주제', 'bitmidi', '롬에 안 넣음 (만들어만 둠)'),
]


def real_bpm(js):
    t = RM.tempo_of(js, 1)
    return 256 * RM.FPS * 60 / (t * js['grid'])


def unshift(name):
    sp = M.SONGS.get(name, {})
    return [-sp.get(k + '_shift', 0) for k in ('lead', 'harm', 'bass')] + [0]


def build(fn, name):
    js = json.load(open(os.path.join(MUS, name + '.json')))
    tick = TPB // js['grid']; bpm = real_bpm(js); undo = unshift(name)
    mf = mido.MidiFile(type=1, ticks_per_beat=TPB)
    t0 = mido.MidiTrack(); mf.tracks.append(t0)
    t0.append(mido.MetaMessage('track_name', name=name, time=0))
    t0.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    t0.append(mido.MetaMessage('time_signature', numerator=3 if name == 'bolero' else 4, denominator=4, time=0))
    loop = js.get('loop_at', 0) * tick; end = js['units'] * tick
    t0.append(mido.MetaMessage('marker', text='loopStart', time=loop))
    t0.append(mido.MetaMessage('marker', text='loopEnd', time=end - loop))
    t0.append(mido.MetaMessage('end_of_track', time=0))
    for ch, (tn, prog) in enumerate((('Melody (Pulse1)', 0), ('Harmony (Pulse2)', 0), ('Bass (Wave)', 32), ('Drums (Noise)', 0))):
        tr = mido.MidiTrack(); mf.tracks.append(tr); mc = 9 if ch == 3 else ch
        tr.append(mido.MetaMessage('track_name', name=tn, time=0))
        if ch < 3: tr.append(mido.Message('program_change', channel=mc, program=prog, time=0))
        gap = 0
        for p, n in js['ch'][ch]:
            if p:
                note = GM.get(p, 0) if ch == 3 else p + undo[ch]
                if note:
                    dur = n * tick if ch < 3 else min(n * tick, tick * 3)
                    tr.append(mido.Message('note_on', channel=mc, note=note, velocity=96 if ch < 3 else 90, time=gap))
                    tr.append(mido.Message('note_off', channel=mc, note=note, velocity=0, time=dur)); gap = n * tick - dur; continue
            gap += n * tick
        tr.append(mido.MetaMessage('end_of_track', time=gap))
    mf.save(os.path.join(OUT, fn + '.mid'))
    return dict(len=end / TPB * 60 / bpm, loop=loop / TPB * 60 / bpm, bpm=bpm, tracks=len(mf.tracks), undo=undo)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for fn, name, what, src, scene in SONGS:
        r = build(fn, name)
        rows.append('| %s | %.1f | %.1f | %d | %.1f | %s | %s | %s |' % (fn, r['len'], r['loop'], r['tracks'], r['bpm'], what, src, scene))
        print(fn, '%.1f초 반복 %.1f초 %.1fbpm' % (r['len'], r['loop'], r['bpm']), '옥타브 되돌림' if any(r['undo']) else '')
    open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write(
        '# GBC 판 노래 → MIDI (2부 NDS 편곡용)\n\n'
        '만든 법: `digimon/gbc/tools/json2mid.py` — GBC 롬에 넣은 편곡(`digimon/gbc/music/<곡>.json`)을 그대로 MIDI 로 되돌림.\n'
        '원본 MIDI(편곡 전)는 저장소에 없어 「_원본구간」 파일은 없음.\n\n'
        '- 트랙: 0 템포·마커 / 1 멜로디(펄스1) / 2 화음(펄스2) / 3 베이스(웨이브) / 4 북(노이즈 → GM 드럼, 채널 10)\n'
        '- 마커: `loopStart` = 반복 시작, `loopEnd` = 곡 끝(반복 끝). 전주가 없는 곡은 `loopStart` 가 0초(처음부터 통째로 반복)\n'
        '- 템포: 롬 엔진에 들어간 정수 템포에서 계산한 실제 빠르기(1배). 롬은 델타 빨리감기용으로 이 반의 빠르기로 들어 있음(MUSIC_FF=2)\n'
        '- 옥타브: 채널 단위로 옮긴 것(안녕 디지몬 멜로디 −12, digimon 록·The Biggest Dreamer 베이스 −12)은 되돌림. Brave Heart 화음의 반짝이 반복음(한 소스만 −12)과 '
        'GBC 음역(펄스 C2~C7, 웨이브 E1~C5)에 맞춘 자동 옥타브 접기는 음마다 기록이 없어 GBC 높이 그대로\n'
        '- 화음·베이스는 원곡에서 한 번에 한 음만 고른 것 (GBC 채널 한계)\n\n'
        '| 파일 | 길이(초) | 반복 시작(초) | 트랙 수 | bpm | 원래 곡·구간 | 원래 MIDI 출처 | GBC 장면 |\n|---|---|---|---|---|---|---|---|\n'
        + '\n'.join(rows) + '\n')
