// 디지몬 GBC — 소리 엔진 (포켓몬 금처럼: 네모파1 멜로디 · 네모파2 화음 · 파형 베이스 · 잡음 드럼)
// build.py 가 만드는 build/gen/music.c 에 곡 자료와 함께 들어가 한 뱅크에 놓인다 (이 파일은 따로 컴파일하지 않음).
// 0번 뱅크는 VBL 마다 music_update() 만 부른다 (BANKED 라 뱅크 전환은 트램펄린이 함).
//
// 채널 자료 (바이트):
//   00 쉼 · 01~5F 음 (MIDI = 값 + 23, 잡음 채널은 드럼 번호) — 지금 길이만큼
//   80~BF 길이 = (값 & 3F) + 1 칸 · C0 n 길이 = n 칸 · D0~DF 악기 · FF 끝(처음으로, 한 번만 곡이면 멈춤)
// 곡 머리: 속도(2, 한 프레임에 나아가는 칸 × 256) · 한 번만(1) · 채널 4개 시작 위치(2씩, 곡 머리 기준)
#include <gb/gb.h>
#include <gb/hardware.h>

typedef struct { const uint8_t *p, *start; uint8_t left, len, ins, note, rel, age; uint16_t fq; } mch_t;
static mch_t MC[4];
static uint16_t mspeed, macc;
static uint8_t mon, monce;
uint8_t music_done, cur_song = 0xFF;

// 네모파 주파수 값 (MIDI 24~119). 파형은 한 옥타브 위 값을 쓰면 같은 음
static const uint16_t FQ[96] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    44, 157, 263, 363, 457, 547, 631, 711, 786, 856, 923, 986,
    1046, 1102, 1155, 1205, 1253, 1297, 1339, 1379, 1417, 1452, 1486, 1517,
    1547, 1575, 1602, 1627, 1650, 1673, 1694, 1714, 1732, 1750, 1767, 1783,
    1798, 1812, 1825, 1837, 1849, 1860, 1871, 1881, 1890, 1899, 1907, 1915,
    1923, 1930, 1936, 1943, 1949, 1954, 1959, 1964, 1969, 1974, 1978, 1982,
    1985, 1989, 1992, 1995, 1998, 2001, 2004, 2006, 2009, 2011, 2013, 2015,
    2017, 2018, 2020, 2022, 2023, 2025, 2026, 2027, 2028, 2029, 2030, 2031 };
// 네모파 악기: 듀티(NRx1), 엔벨로프(NRx2)
static const uint8_t PINS[8][2] = {
    { 0x80, 0xA3 },   // 0 멜로디 50% 또렷
    { 0x40, 0x93 },   // 1 멜로디 25%
    { 0x40, 0x62 },   // 2 화음 25% 작게
    { 0x00, 0x52 },   // 3 화음 12.5% 부드럽게
    { 0x80, 0xA6 },   // 4 멜로디 50% 길게 끌기
    { 0x40, 0x71 },   // 5 짧게 튕기기
    { 0xC0, 0x84 },   // 6 75% 두껍게
    { 0x80, 0xF1 } }; // 7 징글
// 파형 악기: 파형 번호, 소리 크기(NR32)
static const uint8_t WINS[4][2] = { { 0, 0x20 }, { 1, 0x20 }, { 0, 0x40 }, { 1, 0x40 } };
static const uint8_t WAVES[2][16] = {
    { 0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF, 0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54, 0x32, 0x10 },   // 삼각
    { 0x02, 0x46, 0x8A, 0xCE, 0xFF, 0xFF, 0xEE, 0xDD, 0xCC, 0xBB, 0x99, 0x77, 0x55, 0x33, 0x11, 0x00 } }; // 굵은 베이스
// 드럼: 엔벨로프(NR42), 잡음 높이(NR43) — 1 킥 2 스네어 3 하이햇 4 열린 하이햇 5 심벌 6 탐
static const uint8_t DRUMS[7][2] = { { 0, 0 }, { 0xA1, 0x71 }, { 0xB2, 0x52 }, { 0x61, 0x10 }, { 0x63, 0x11 }, { 0x95, 0x22 }, { 0x92, 0x5C } };

static void m_wave(uint8_t w) {
    uint8_t i; NR30_REG = 0;
    for (i = 0; i < 16; i++) AUD3WAVE[i] = WAVES[w][i];
}
static void m_silence(void) { NR12_REG = 0; NR22_REG = 0; NR30_REG = 0; NR42_REG = 0; }

static void m_note(uint8_t c, uint8_t b) {
    mch_t *m = &MC[c]; uint16_t x; uint8_t i;
    m->age = 0;
    if (c == 3) { if (b && b < 7) { NR42_REG = DRUMS[b][0]; NR43_REG = DRUMS[b][1]; NR44_REG = 0x80; } return; }
    m->note = b;
    if (!b) { if (c == 0) NR12_REG = 0; else if (c == 1) NR22_REG = 0; else NR32_REG = 0; return; }
    if (c == 2) {
        i = b + 11; if (i > 95) i = 95;
        x = FQ[i]; NR30_REG = 0x80; NR32_REG = WINS[m->ins][1]; NR33_REG = (uint8_t)x; NR34_REG = 0x80 | (uint8_t)(x >> 8);
    } else {
        i = b - 1; if (i > 95) i = 95;
        x = FQ[i];
        if (c == 0) { NR11_REG = PINS[m->ins][0]; NR12_REG = PINS[m->ins][1]; NR13_REG = (uint8_t)x; NR14_REG = 0x80 | (uint8_t)(x >> 8); }
        else { NR21_REG = PINS[m->ins][0]; NR22_REG = PINS[m->ins][1]; NR23_REG = (uint8_t)x; NR24_REG = 0x80 | (uint8_t)(x >> 8); }
    }
    m->fq = x;
}

static void m_tick(uint8_t c) {
    mch_t *m = &MC[c]; uint8_t b;
    if (m->left) {
        m->left--;
        if (m->left == 1 && m->rel && c != 3 && m->note) {      // 다음 음 직전에 살짝 끊기 (또렷하게)
            if (c == 0) NR12_REG = 0; else if (c == 1) NR22_REG = 0; else NR32_REG = 0;
        }
        if (m->left) return;
    }
    for (;;) {
        b = *m->p++;
        if (b == 0xFF) {
            if (monce) { mon = 0; music_done = 1; m_silence(); return; }
            m->p = m->start; continue;
        }
        if ((b & 0xF0) == 0xD0) { m->ins = b & 0x0F; if (c == 2) m_wave(WINS[m->ins][0]); continue; }
        if (b == 0xC0) { m->len = *m->p++; continue; }
        if (b & 0x80) { m->len = (b & 0x3F) + 1; continue; }
        break;
    }
    m->left = m->len; m->rel = m->len >= 4;
    m_note(c, b);
}

void music_update(void) BANKED {
    uint8_t c; mch_t *m;
    if (!mon) return;
    macc += mspeed;
    while (macc >= 256) {
        macc -= 256;
        for (c = 0; c < 4; c++) { m_tick(c); if (!mon) return; }
    }
    // 멜로디 떨림 (오래 끄는 음만)
    m = &MC[0];
    if (m->note && ++m->age > 18 && !(m->age & 3)) {
        uint16_t x = m->fq + ((m->age & 4) ? 1 : 0);
        NR13_REG = (uint8_t)x; NR14_REG = (uint8_t)(x >> 8);
    }
}

void music_stop(void) BANKED { mon = 0; m_silence(); cur_song = 0xFF; }

// 곡 바꾸기 (같은 곡이 이미 나오고 있으면 그대로)
void music_play(uint8_t s) BANKED {
    const uint8_t *h; uint8_t c;
    if (s == cur_song && (mon || !monce)) return;
    mon = 0; cur_song = s;
    if (s == 0xFF) { m_silence(); return; }
    NR52_REG = 0x80; NR50_REG = 0x77; NR51_REG = 0xFF;
    m_silence();
    h = SONGTAB[s];
    mspeed = h[0] | ((uint16_t)h[1] << 8); monce = h[2]; macc = 256;
    for (c = 0; c < 4; c++) {
        MC[c].start = MC[c].p = h + (h[3 + c * 2] | ((uint16_t)h[4 + c * 2] << 8));
        MC[c].left = 0; MC[c].len = 1; MC[c].ins = 0; MC[c].note = 0; MC[c].age = 0;
    }
    music_done = 0; mon = 1;
}
