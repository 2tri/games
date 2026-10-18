// 음악 재생: 화면 갱신(VBL)마다 한 번. 사각파1 = 멜로디, 사각파2 = 화음, 파형 = 베이스
#include <gb/gb.h>
#include "music.h"
typedef struct { uint16_t fpt; const uint8_t *ch[3]; } Song;
extern const Song SONGS[];

// 음 높이(MIDI 번호) → 게임보이 주파수 값. 사각파: 2048 - 131072/f, 파형: 2048 - 65536/f
static const uint16_t SQ[] = {   // MIDI 36(C2) ~ 107
    44,157,263,363,457,547,631,711,786,856,923,986,1046,1102,1155,1205,1253,1297,1339,1379,1417,1452,1486,1517,1547,1575,1602,1627,1650,1673,1694,1714,1732,1750,1767,1783,1798,1812,1825,1837,1849,1860,1871,1881,1890,1899,1907,1915,1923,1930,1936,1943,1949,1954,1959,1964,1969,1974,1978,1982,1985,1989,1992,1995,1998,2001,2004,2006,2009,2011,2013,2015 };
static const uint8_t WAVE[16] = { 0x01,0x23,0x45,0x67,0x89,0xAB,0xCD,0xEF,0xFE,0xDC,0xBA,0x98,0x76,0x54,0x32,0x10 };   // 세모꼴
static uint8_t cur = MUS_NONE, bank_sv;
static const uint8_t *pos[3], *start[3];
static uint8_t left[3];
static uint16_t acc, fpt;

static uint16_t freq(uint8_t ch, uint8_t m) {
    if (ch == 2) m += 12;                 // 파형 채널은 한 옥타브 낮게 나므로 표에서 한 칸 위
    if (m < 36) m = 36; if (m > 107) m = 107;
    return SQ[m - 36];
}
static void note_on(uint8_t ch, uint8_t m) {
    uint16_t f;
    if (!m) {   // 쉼표
        if (ch == 0) NR12_REG = 0x00, NR14_REG = 0x80; else if (ch == 1) NR22_REG = 0x00, NR24_REG = 0x80; else NR32_REG = 0x00;
        return;
    }
    f = freq(ch, m);
    if (ch == 0) { NR10_REG = 0; NR11_REG = 0x80; NR12_REG = 0xA3; NR13_REG = (uint8_t)f; NR14_REG = 0x80 | (f >> 8); }
    else if (ch == 1) { NR21_REG = 0x40; NR22_REG = 0x62; NR23_REG = (uint8_t)f; NR24_REG = 0x80 | (f >> 8); }
    else { NR30_REG = 0x80; NR32_REG = 0x40; NR33_REG = (uint8_t)f; NR34_REG = 0x80 | (f >> 8); }
}
static void music_isr(void) {
    uint8_t c, sv;
    if (cur == MUS_NONE) return;
    acc += 256;
    if (acc < fpt) return;
    acc -= fpt;
    sv = _current_bank; SWITCH_ROM(MUSIC_BANK);
    for (c = 0; c < 3; c++) {
        if (left[c] && --left[c]) continue;
        if (*pos[c] == 255) pos[c] = start[c];          // 끝나면 처음부터
        note_on(c, pos[c][0]); left[c] = pos[c][1]; pos[c] += 2;
    }
    SWITCH_ROM(sv);
}
static uint8_t inited;
void music_play(uint8_t id) {
    uint8_t c, sv;
    if (id == cur) return;
    if (!inited) {
        inited = 1;
        NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
        NR30_REG = 0; for (c = 0; c < 16; c++) AUD3WAVE[c] = WAVE[c];
        add_VBL(music_isr);
    }
    disable_interrupts();
    sv = _current_bank; SWITCH_ROM(MUSIC_BANK);
    fpt = SONGS[id].fpt;
    for (c = 0; c < 3; c++) { start[c] = pos[c] = SONGS[id].ch[c]; left[c] = 0; }
    SWITCH_ROM(sv);
    acc = fpt; cur = id;
    enable_interrupts();
}
void music_stop(void) { cur = MUS_NONE; NR12_REG = 0; NR22_REG = 0; NR32_REG = 0; NR14_REG = 0x80; NR24_REG = 0x80; }
uint8_t music_cur(void) { return cur; }
