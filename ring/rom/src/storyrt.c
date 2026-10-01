#include <gb/gb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"
#include "story.h"

static char place[64]; static uint8_t sprId;
static void storyScene(void) {
    uint8_t w;
    rect(0, 0, 160, 96, 0);
    if (place[0]) { box(0, 0, 160, 20); text(place, 80 - text_w(place) / 2, 5, 3); }
    if (sprId != 255) { w = spr_w(sprId); blit(sprId, (80 - w / 2) & 0xF8, 88 - spr_h(sprId), 0); }
    box(0, 96, 160, 48);
}
void story(const char *p, uint8_t spr, const char * const *lines, uint8_t n) {
    uint8_t i;
    if (p) { strncpy(place, p, 63); place[63] = 0; } else place[0] = 0;
    sprId = spr; scene = storyScene; storyScene();
    for (i = 0; i < n; i++) say(lines[i]);
}
static char ta[48], tb[48];
static void titleCard(void) {
    rect(0, 0, 160, 144, 3);
    text(ta, 80 - text_w(ta) / 2, 56, 0); text(tb, 80 - text_w(tb) / 2, 72, 1);
}
void chapterTitle(const char *a, const char *b) {
    strncpy(ta, a, 47); ta[47] = 0; strncpy(tb, b, 47); tb[47] = 0;
    scene = titleCard; titleCard();
    wait_frames(20); key_wait();
}
static void darkScene(void) { rect(0, 0, 160, 144, 3); text("눈앞이 캄캄해졌다...", 30, 60, 0); }
void lose(void) {
    scene = darkScene; darkScene(); wait_frames(30); key_wait();
    healAll(); save();       // 마지막 쉼터에서 다시
}
// ── 저장: 카트리지 배터리 램(SRAM). Delta 도 .sav 로 보관 ──
#define MAGIC 0x52494E47UL   // "RING"
void save(void) {
    uint32_t m = MAGIC;
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy((uint8_t *)0xA000, &m, 4); memcpy((uint8_t *)0xA004, &S, sizeof S);
    DISABLE_RAM;
}
uint8_t load(void) {
    uint32_t m;
    ENABLE_RAM; SWITCH_RAM(0);
    memcpy(&m, (uint8_t *)0xA000, 4);
    if (m == MAGIC) memcpy(&S, (uint8_t *)0xA004, sizeof S);
    DISABLE_RAM;
    return m == MAGIC;
}
