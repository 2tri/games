"""예전 GBC 판 곡(gbc/music/<곡>.json, 4채널 음표) → 금 음악 엔진 바이트 (사용자 지시 2026-10-02 「노래도 포켓몬 노래라 재미없는데 이전에 만들어둔 거 쓰면 되는 거 아닌가」)
json: {"bpm", "grid"(한 박 칸 수), "units", "once", "ch": [[[음, 길이], ...] × 4]}  음 = MIDI 번호(0 쉼), 4번 채널은 드럼 번호(1 킥 2 스네어 3 하이햇 4 열린 하이햇 5 크래시 6 톰)
금 엔진 (pokegold-kr audio/engine.asm·macros/scripts/audio.asm):
  음 길이(프레임) = 길이(1~16) × note_type 단위 × 템포 / 256  (단위×길이 ≤ 255) → 칸 하나 = 단위 1, 템포 = 256 × 프레임/칸
  octave n 의 도 = MIDI (n+2)×12 (네모파), 파형 채널은 같은 값이 한 옥타브 낮게 남 → (n+1)×12
  명령: octave d0+8-n · note_type d8 단위 [볼륨<<4|감쇠] · tempo da 높은 낮은 · duty db · volume e5 · toggle_noise e3 · sound_loop fd 횟수 주소 · sound_ret ff"""
import json, math, os

FPS = 59.7275
DRUM = {1: 4, 2: 1, 3: 5, 4: 3, 5: 12, 6: 11}         # 우리 드럼 → 금 드럼 모음 3 (Kick1·Snare12·Triangle5·Snare14·Crash2·Kick2)
ENV = {0: 0xb2, 1: 0x82, 2: 0x25}                     # 채널별 note_type 둘째 바이트 (네모파 볼륨·감쇠, 파형 볼륨·파형)
DUTY = {0: 2, 1: 1}
# 곡 느낌 (rules.MUSIC_STYLE). calm = 잔잔한 배경음 (금 연두마을 newbarktown.asm 을 본뜸): 멜로디 볼륨 8·천천히 줄어듦(6)·떨림(vibrato 18,2,3),
#   화음 볼륨 5·얇은 네모파(duty 0), 베이스 파형 볼륨 1/4 (소리 크기는 파형 채널이 가장 큼 → 이것만 낮춰도 전체가 약 2/3).
#   2026-10-05 사용자 「노래는 배경음으로 깔리게, 안녕 디지몬 같은 노래는 잔잔하게」
# road = 도로 (금 29번 도로 route29.asm 을 본뜸: 멜로디 볼륨 11·감쇠 4, 떨림 18,3,6): 노래 멜로디가 또렷하게, 화음은 한 단계 낮게
STYLES = {'calm': dict(env={0: 0x86, 1: 0x55, 2: 0x35}, duty={0: 2, 1: 0}, vib={0: (18, 2, 3)}),
          'road': dict(env={0: 0xa4, 1: 0x73, 2: 0x25}, duty={0: 2, 1: 1}, vib={0: (18, 3, 6)})}


def tempo_of(js, ff=1):
    return max(1, round(256 * FPS * 60 * ff / (js['bpm'] * js['grid'])))


def chan_bytes(ch, notes, base, loop, cap=255, shift=0, ff=1, style=None, loop_at=0):
    """한 채널. base = 이 채널 바이트가 놓일 주소(뱅크 안 0x4000~), loop=True 면 처음으로 되돌아감
    cap = 명령 하나의 최대 칸 수 (엔진의 음 길이 = 칸×템포/256 프레임이 한 바이트라 255프레임을 넘으면 돌아감 → 나눠 씀)
    shift = 음높이 이동(반음, 드럼 채널 제외), style = STYLES 항목 (없으면 기본 ENV·DUTY)
    loop_at = 되돌아갈 칸 (0 = 처음). 앞부분(전주)은 한 번만 — 그 칸에서 음을 끊고, 옥타브·note_type 을 다시 써서 되돌아와도 같게"""
    st = style or {}; duty = st.get('duty', DUTY)
    out = bytearray()
    if ch == 0: out += bytes([0xda]) + 0 .to_bytes(2, 'big') + bytes([0xe5, 0x77])   # 템포는 song_bytes 에서 채움
    if ch in duty: out += bytes([0xdb, duty[ch]])
    if ch in st.get('vib', {}):                                                        # vibrato 지연(프레임)·폭·빠르기: 빨리감기면 ff배로 늘림
        dl, ex, rt = st['vib'][ch]; out += bytes([0xe1, min(255, round(dl * ff)), ex << 4 | min(15, round(rt * ff))])
    if ch == 3: out += bytes([0xe3, 3])                                               # 드럼 모음 3
    start = base + len(out)
    speed = None; octv = None

    env = st.get('env', ENV).get(ch, ENV.get(ch, 0))
    if ff != 1 and ch in (0, 1): env = (env & 0xf0) | min(7, round((env & 7) * ff))    # 소리 줄어드는 빠르기(실제 시간)도 ff배 느리게
    def note_type(s):
        nonlocal speed
        if s != speed:
            out.extend([0xd8, s] if ch == 3 else [0xd8, s, env]); speed = s

    def emit(code, L):
        """code = 음높이 칸(1~12) 또는 드럼 번호, 0 = 쉼. L 칸. cap 보다 긴 음은 나눠 쓰고, 네모파(소리가 줄어드는 채널)는 이어지는 조각을 쉼으로 (다시 치지 않게)"""
        first = True
        while L > 0:
            n = min(L, cap)
            s = 1 if n <= 16 else next(s for s in range(1, 256) if n % s == 0 and n // s <= 16)
            c = code if first or ch not in (0, 1) else 0
            note_type(s); out.append((c << 4) | (n // s - 1)); L -= n; first = False

    if loop_at:                                                                        # 되돌아갈 칸에 걸친 음은 둘로 나눔
        cut = []; u = 0
        for p, L in notes:
            if u < loop_at < u + L: cut += [[p, loop_at - u], [p if ch == 2 else 0, u + L - loop_at]]   # 이어지는 조각: 파형은 같은 음, 네모파·드럼은 쉼 (다시 안 침)
            else: cut.append([p, L])
            u += max(0, L)
        notes = cut
    u = 0
    for p, L in notes:
        if L <= 0: continue
        if loop_at and u == loop_at: start = base + len(out); speed = None; octv = None
        u += L
        if p == 0: emit(0, L); continue
        if ch == 3:
            emit(DRUM.get(p, 1), L); continue
        p += shift
        n = p // 12 - (1 if ch == 2 else 2); q = p
        while n < 1: n += 1; q += 12
        while n > 8: n -= 1; q -= 12
        if n != octv: out.append(0xd0 + 8 - n); octv = n
        emit(q % 12 + 1, L)
    if loop: out += bytes([0xfd, 0]) + start.to_bytes(2, 'little')
    else: out.append(0xff)
    return bytes(out)


def ff_shift(js, ch, ff):
    """빨리감기 ff배로 들으면 음이 ff배 높아짐 → 그만큼 내림 (반음). 채널이 소리 범위 밑으로 가면 채널 전체를 옥타브 올림"""
    if ff == 1 or ch == 3: return 0
    s = -round(12 * math.log2(ff)); lo, hi = (24, 119) if ch == 2 else (36, 131)
    ps = [p for p, L in js['ch'][ch] if p and L > 0]
    # 10% 넘게 범위 밑이면 채널 전체를 옥타브 올림 (음마다 올리면 멜로디가 뒤틀림 — 4배에서 길 곡 멜로디 42% 가 밑으로 감),
    #   아니면 밑으로 간 음만 그 음에서 옥타브 올림 (chan_bytes)
    while ps and sum(p + s < lo for p in ps) * 10 > len(ps) and max(ps) + s + 12 <= hi: s += 12
    return s


def under_lead(js, s, lo=36):
    """화음 채널을 멜로디와 같이 s 반음 내림 (빨리감기용). 소리 범위 밑으로 간 음은 옥타브 올리되 그때 울리는 멜로디보다 높아지면 쉼
    — 화음 채널만 통째로 옥타브 올리면 멜로디 위로 올라가 멜로디가 묻힘. 반환: 이미 옮긴 음 목록 (chan_bytes 에 shift 0 으로)"""
    lead = []
    for p, L in js['ch'][0]: lead += [p + s if p else 0] * max(0, L)
    out = []; t = 0
    for p, L in js['ch'][1]:
        q = p + s if p else 0
        if q and q < lo:
            while q < lo: q += 12
            lp = lead[t] if t < len(lead) else 0
            if lp and q >= lp: q = 0
        out.append([q, L]); t += max(0, L)
    return out


def song_bytes(js, base, loop=None, ff=1, slow=None, style=None, pitch=False):
    """곡 하나 → (머리 + 채널 4개) 바이트. base = 놓일 주소 (뱅크 안 0x4000~)
    ff = 델타 빨리감기 배수: 템포를 ff배 느리게 (빨리감기로 들으면 원래 곡). pitch=True 면 음도 12·log2(ff) 반음 낮춤 —
      델타는 빨리감기 때 AVAudioUnitTimePitch(rate) 로 음높이는 두고 빠르기만 바꿔서 기본은 False (DeltaCore AudioManager.swift)
    slow = 템포만 따로 (회복 징글은 게임이 정해진 프레임만 기다려서 늘이면 잘림 → 1)"""
    loop = (not js.get('once')) if loop is None else loop
    t = tempo_of(js, ff if slow is None else slow); cap = min(255, (65535 - 255) // t)
    head = 12; chans = []; p = base + head
    sh = [ff_shift(js, ch, ff) if pitch else 0 for ch in range(4)]; notes = [js['ch'][ch] for ch in range(4)]
    if sh[1] > sh[0]: notes[1], sh[1] = under_lead(js, sh[0]), 0
    for ch in range(4):
        b = chan_bytes(ch, notes[ch], p, loop, cap, sh[ch], ff, style, js.get('loop_at', 0)); chans.append((p, b)); p += len(b)
    c0 = bytearray(chans[0][1]); c0[1:3] = t.to_bytes(2, 'big'); chans[0] = (chans[0][0], bytes(c0))
    out = bytearray()
    for i, (a, _) in enumerate(chans):
        out += bytes([(3 << 6 | i) if i == 0 else i]) + a.to_bytes(2, 'little')
    for _, b in chans: out += b
    return bytes(out)


def load(name):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return json.load(open(os.path.join(here, 'gbc', 'music', name + '.json')))


if __name__ == '__main__':
    import rules
    for nm in rules.MUSIC:
        js = load(nm); st = rules.MUSIC_STYLE.get(nm)
        print('%-8s bpm %5.1f grid %d 템포 %d → %d바이트 %s' % (nm, js['bpm'], js['grid'], tempo_of(js), len(song_bytes(js, 0x4000, style=STYLES.get(st))), st or ''))
