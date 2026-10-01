// 디지몬 GBC — 시작
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"

static void new_game(void) {
    memset(&G, 0, sizeof(G));
    G.map = START_MAP; G.x = START_X; G.y = START_Y; G.dir = START_DIR;
    G.heal_map = START_MAP; G.heal_x = START_X; G.heal_y = START_Y; G.heal_dir = START_DIR;
}

void main(void) {
    DISPLAY_OFF;
    LCDC_REG = LCDCF_OFF | LCDCF_WIN9C00 | LCDCF_BG8000 | LCDCF_BG9800 | LCDCF_OBJ16 | LCDCF_OBJON | LCDCF_BGON;
    set_1bpp_colors(3, 1);
    load_ui();
    fade_lv = 0; pal_apply();
    hide_sprites(); move_win(7, 144);
    DISPLAY_ON;
    for (;;) {
        cur_map = 0xFF; scene = SCENE_NONE;
        if (title_screen() == 1 && load_game()) {
            fade_out(0);
            field_enter(G.map, G.x, G.y, G.dir, 0);
            say(S_CONT); tb_close();
        } else {
            new_game();
            run_script(MISC_BANK, opening, 0);
        }
        field_loop();
    }
}
