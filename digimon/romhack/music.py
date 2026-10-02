"""예전 GBC 판 곡(gbc/music/<곡>.json, 4채널 음표) → 금 음악 엔진 바이트 (사용자 지시 2026-10-02 「노래도 포켓몬 노래라 재미없는데 이전에 만들어둔 거 쓰면 되는 거 아닌가」)
json: {"bpm", "grid"(한 박 칸 수), "units", "once", "ch": [[[음, 길이], ...] × 4]}  음 = MIDI 번호(0 쉼), 4번 채널은 드럼 번호(1 킥 2 스네어 3 하이햇 4 열린 하이햇 5 크래시 6 톰)
금 엔진 (pokegold-kr audio/engine.asm·macros/scripts/audio.asm):
  음 길이(프레임) = 길이(1~16) × note_type 단위 × 템포 / 256  (단위×길이 ≤ 255) → 칸 하나 = 단위 1, 템포 = 256 × 프레임/칸
  octave n 의 도 = MIDI (n+2)×12 (네모파), 파형 채널은 같은 값이 한 옥타브 낮게 남 → (n+1)×12
  명령: octave d0+8-n · note_type d8 단위 [볼륨<<4|감쇠] · tempo da 높은 낮은 · duty db · volume e5 · toggle_noise e3 · sound_loop fd 횟수 주소 · sound_ret ff"""
import json, os

FPS = 59.7275
DRUM = {1: 4, 2: 1, 3: 5, 4: 3, 5: 12, 6: 11}         # 우리 드럼 → 금 드럼 모음 3 (Kick1·Snare12·Triangle5·Snare14·Crash2·Kick2)
ENV = {0: 0xb2, 1: 0x82, 2: 0x25}                     # 채널별 note_type 둘째 바이트 (네모파 볼륨·감쇠, 파형 볼륨·파형)
DUTY = {0: 2, 1: 1}


def tempo_of(js):
    return max(1, round(256 * FPS * 60 / (js['bpm'] * js['grid'])))


def chan_bytes(ch, notes, base, loop):
    """한 채널. base = 이 채널 바이트가 놓일 주소(뱅크 안 0x4000~), loop=True 면 처음으로 되돌아감"""
    out = bytearray()
    if ch == 0: out += bytes([0xda]) + 0 .to_bytes(2, 'big') + bytes([0xe5, 0x77])   # 템포는 song_bytes 에서 채움
    if ch in DUTY: out += bytes([0xdb, DUTY[ch]])
    if ch == 3: out += bytes([0xe3, 3])                                               # 드럼 모음 3
    start = base + len(out)
    speed = None; octv = None

    def note_type(s):
        nonlocal speed
        if s != speed:
            out.extend([0xd8, s] if ch == 3 else [0xd8, s, ENV[ch]]); speed = s

    def emit(code, L):
        """code = 음높이 칸(1~12) 또는 드럼 번호, 0 = 쉼. L 칸"""
        while L > 0:
            n = min(L, 255)
            s = 1 if n <= 16 else next(s for s in range(1, 256) if n % s == 0 and n // s <= 16)
            note_type(s); out.append((code << 4) | (n // s - 1)); L -= n

    for p, L in notes:
        if L <= 0: continue
        if p == 0: emit(0, L); continue
        if ch == 3:
            emit(DRUM.get(p, 1), L); continue
        n = p // 12 - (1 if ch == 2 else 2); q = p
        while n < 1: n += 1; q += 12
        while n > 8: n -= 1; q -= 12
        if n != octv: out.append(0xd0 + 8 - n); octv = n
        emit(q % 12 + 1, L)
    if loop: out += bytes([0xfd, 0]) + start.to_bytes(2, 'little')
    else: out.append(0xff)
    return bytes(out)


def song_bytes(js, base, loop=None):
    """곡 하나 → (머리 + 채널 4개) 바이트. base = 놓일 주소 (뱅크 안 0x4000~)"""
    loop = (not js.get('once')) if loop is None else loop
    head = 12; chans = []; p = base + head
    for ch in range(4):
        b = chan_bytes(ch, js['ch'][ch], p, loop); chans.append((p, b)); p += len(b)
    t = tempo_of(js); c0 = bytearray(chans[0][1]); c0[1:3] = t.to_bytes(2, 'big'); chans[0] = (chans[0][0], bytes(c0))
    out = bytearray()
    for i, (a, _) in enumerate(chans):
        out += bytes([(3 << 6 | i) if i == 0 else i]) + a.to_bytes(2, 'little')
    for _, b in chans: out += b
    return bytes(out)


def load(name):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return json.load(open(os.path.join(here, 'gbc', 'music', name + '.json')))


if __name__ == '__main__':
    for nm in ('title', 'town', 'field', 'village', 'battle', 'boss', 'evolve', 'heal', 'capture'):
        js = load(nm); print('%-8s bpm %5.1f grid %d 템포 %d → %d바이트' % (nm, js['bpm'], js['grid'], tempo_of(js), len(song_bytes(js, 0x4000))))
