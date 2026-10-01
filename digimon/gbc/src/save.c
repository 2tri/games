// 디지몬 GBC — 배터리 저장 (MBC5 + RAM, 델타에서도 남음)
#include <gb/gb.h>
#include <string.h>
#include "engine.h"

#define SRAM ((uint8_t *)0xA000)
static game_t tmp;
static uint16_t sum_of(const game_t *g) {
    const uint8_t *p = (const uint8_t *)g; uint16_t s = 0x1234, i;
    for (i = 0; i < sizeof(game_t) - 2; i++) s = (s << 1 | s >> 15) + p[i];
    return s;
}
uint8_t save_game(void) {
    G.magic[0] = 'D'; G.magic[1] = 'G'; G.magic[2] = 'M'; G.magic[3] = '2';
    G.sum = sum_of(&G);
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy(SRAM, &G, sizeof(game_t));
    DISABLE_RAM;
    return 1;
}
uint8_t save_exists(void) {
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy(&tmp, SRAM, sizeof(game_t));
    DISABLE_RAM;
    return tmp.magic[0] == 'D' && tmp.magic[1] == 'G' && tmp.magic[2] == 'M' && tmp.magic[3] == '2' && tmp.sum == sum_of(&tmp);
}
uint8_t load_game(void) {
    if (!save_exists()) return 0;
    memcpy(&G, &tmp, sizeof(game_t));
    return 1;
}
