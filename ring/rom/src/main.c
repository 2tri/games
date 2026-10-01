// 「반지 원정」 GBC — 웹판 이야기 1~8장 + 덧붙이는 장을 그대로 옮김 (story.js 가 index.html 에서 자동 변환)
#include <gb/gb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"
#include "story.h"
#include "steps.h"

static void titleScene(void) {
    rect(0, 0, 160, 144, 3);
    text("반지 원정", 80 - text_w("반지 원정") / 2, 22, 0);
    blit(SP_FRODOSAM_FRONT, (80 - spr_w(SP_FRODOSAM_FRONT) / 2) & 0xF8, 104 - spr_h(SP_FRODOSAM_FRONT), 0);
}
static void newGame(void) {
    memset(&S, 0, sizeof S);
    S.hero = HE_FRODOSAM; S.lv = 5; S.np = 0; addMember(HE_FRODOSAM, 5);
    S.hp = statOf(HE_FRODOSAM, 5, ST_HP); S.lembas = 3; S.herb = 2;
}
static const char * const T_NEW[] = { "처음부터" };
static const char * const T_CONT[] = { "이어하기", "처음부터" };
void main(void) {
    uint8_t has_save, c, before;
    eng_init();
    for (;;) {
        has_save = load() && !S.done && S.step > 0;
        scene = titleScene; titleScene();
        c = has_save ? choose(0, T_CONT, 2, NOCANCEL) : (choose(0, T_NEW, 1, NOCANCEL), 1);
        if (c == 1) newGame();
        while (S.step < N_STEPS) { before = S.step; run_step(S.step); (void)before; }
        S.done = 1; save();
    }
}
