// 「반지 원정」 GBC — 웹판 이야기 1~8장 + 덧붙이는 장을 그대로 옮김 (story.js 가 index.html 에서 자동 변환)
#include <gb/gb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"
#include "story.h"
#include "steps.h"
#include "fieldrt.h"
#include "music.h"

// 걷는 화면이 맡는 이야기 단계 (지금은 샤이어: 1~2단계). 그 밖은 이야기 장면을 차례로
#include "field.h"
#define FIELD_FIRST 1          // FIELD_END 는 field.py 가 지도 사건에서 계산

static void titleScene(void) {
    rect(0, 0, 160, 144, 3);
    text("반지 원정", 80 - text_w("반지 원정") / 2, 22, 0);
    blit(SP_RING_ITEM, (80 - spr_w(SP_RING_ITEM) / 2) & 0xF8, 96 - spr_h(SP_RING_ITEM), 0);
}
static void newGame(void) {
    memset(&S, 0, sizeof S);
    S.hero = HE_FRODOSAM; S.lv = 5; S.np = 0; addMember(HE_FRODOSAM, 5);
    S.hp = statOf(HE_FRODOSAM, 5, ST_HP); S.lembas = 3; S.herb = 2;
    S.map = 0; field_start_pos();
#ifdef START_STEP   // 시험용: 중간 단계부터
    S.step = START_STEP; S.lv = 19; S.hp = statOf(HE_FRODOSAM, 19, ST_HP); S.mlv[0] = 19; S.lembas = 6; S.herb = 3; S.shadow = 4;
    S.dagger = S.sting = S.mithril = S.cloak = S.phial = S.gollum = 1;
#endif
}
static const char * const T_NEW[] = { "처음부터" };
static const char * const T_CONT[] = { "이어하기", "처음부터" };
void main(void) {
    uint8_t has_save, c, before, ev;
    eng_init();
    for (;;) {
        has_save = load() && !S.done && S.step > 0;
        music_play(MUS_TITLE);
        set_scene(titleScene); titleScene();
        c = has_save ? choose(0, T_CONT, 2, NOCANCEL) : (choose(0, T_NEW, 1, NOCANCEL), 1);
        if (c == 1) newGame();
        while (S.step < N_STEPS) {
            if (S.step >= FIELD_FIRST && S.step < FIELD_END) {
                field_enter();
                ev = field_loop();          // 야생·길 막는 적·여관·상점·메뉴는 안에서 처리, 사건 자리만 돌아옴
                if (ev == EV_TRIG) {
                    // 건너뛴 단계가 있으면 차례로 (사건 순서가 꼬이지 않게)
                    while (S.step <= ev_arg && S.step < N_STEPS) { before = S.step; run_step(S.step); if (S.step == before) break; }
                    if (warp_map != 255 && S.step > ev_arg) { S.map = warp_map; S.x = warp_x; S.y = warp_y; S.dir = 1; warp_map = 255; save(); }
                }
            } else {
                // 이야기 장면 곡: 1부 메인 테마 · 2부 미나스 티리스 · 3부 곤도르 · 끝 Into the West
                music_play(S.step >= 40 ? MUS_END : S.step >= 32 ? MUS_STORY3 : S.step >= 25 ? MUS_STORY2 : MUS_STORY1);
                before = S.step; run_step(S.step); (void)before;
            }
        }
        S.done = 1; save();
    }
}
