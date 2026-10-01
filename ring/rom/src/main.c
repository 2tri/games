// 「반지 원정」 GBC — 전투 시험판: 진짜 메뉴·기술·가방·동료 교대·레벨업이 도는 연속 전투
#include <gb/gb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"

static void titleScene(void) {
    rect(0, 0, 160, 144, 3);
    text("반지 원정", 80 - text_w("반지 원정") / 2, 40, 0);
    text("전투 시험판", 80 - text_w("전투 시험판") / 2, 58, 1);
    blit(SP_FRODOSAM_FRONT, 80 - spr_w(SP_FRODOSAM_FRONT) / 2 & 0xF8, 128 - spr_h(SP_FRODOSAM_FRONT), 0);
    text("A 버튼", 80 - text_w("A 버튼") / 2, 130, 0);
}
static void blank(void) { rect(0, 0, 160, 144, 0); }
static const uint8_t ORDER[] = { FO_GOBLIN, FO_GOLLUMB, FO_ORC, FO_WARG, FO_RIDER, FO_SHELOB };
void main(void) {
    uint8_t i, r;
    eng_init();
    for (;;) {
        scene = titleScene; titleScene();
        while (key_wait() != K_A) ;
        memset(&S, 0, sizeof S);
        S.hero = HE_FRODOSAM; S.lv = 14; S.np = 0; addMember(HE_FRODOSAM, 14); addMember(HE_ARAGORN, 14);
        S.hp = statOf(HE_FRODOSAM, 14, ST_HP); S.lembas = 3; S.herb = 2; S.sting = 1; S.dagger = 1; S.phial = 1; S.cloak = 1;
        for (i = 0; i < sizeof ORDER; ) {
            r = battle(ORDER[i], 0);
            scene = blank; blank();
            if (r == R_LOSE) { say("눈앞이 캄캄해졌다..."); say("잠시 쉬고 다시 맞선다."); }
            else if (r == R_RUN) say("숨을 고르고 다시 맞선다.");
            else { i++; say("잠시 쉬어 모두 기운을 되찾았다."); }
            if (r == R_LOSE && S.hero != S.party[0]) swapTo(S.party[0]);
            healAll();
        }
        say("시험판의 마지막 적까지 쓰러뜨렸다! 고맙습니다.");
    }
}
