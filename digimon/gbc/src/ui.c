// 디지몬 GBC — 화면 부품: 테두리, 숫자, 커서, 메뉴, 예/아니오, HP 막대 (뱅크 2)
#pragma bank 2
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"
#define UIA 0x80

void fill_tiles(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tile, uint8_t attr) BANKED {
    uint8_t i, j;
    for (j = 0; j < h; j++) for (i = 0; i < w; i++) put_tile(tgt, x + i, y + j, tile, attr);
}
void draw_frame(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t style) BANKED {
    uint8_t i, j, b = style ? T_G_TL : T_F_TL;
    // 순서: TL T TR L R BL B BR
    put_tile(tgt, x, y, b, UIA); put_tile(tgt, x + w - 1, y, b + 2, UIA);
    put_tile(tgt, x, y + h - 1, b + 5, UIA); put_tile(tgt, x + w - 1, y + h - 1, b + 7, UIA);
    for (i = 1; i < w - 1; i++) { put_tile(tgt, x + i, y, b + 1, UIA); put_tile(tgt, x + i, y + h - 1, b + 6, UIA); }
    for (j = 1; j < h - 1; j++) {
        put_tile(tgt, x, y + j, b + 3, UIA); put_tile(tgt, x + w - 1, y + j, b + 4, UIA);
        for (i = 1; i < w - 1; i++) put_tile(tgt, x + i, y + j, T_PAPER, UIA);
    }
}

void print_num(uint8_t tgt, uint8_t x, uint8_t y, uint16_t v, uint8_t w) BANKED {
    uint8_t d[5], n = 0, i;
    do { d[n++] = v % 10; v /= 10; } while (v && n < 5);
    for (i = 0; i < w; i++) {
        uint8_t k = w - 1 - i;
        put_tile(tgt, x + i, y, k < n ? T_D0 + d[k] : T_PAPER, UIA);
    }
}
void print_lv(uint8_t tgt, uint8_t x, uint8_t y, uint8_t lv) BANKED {
    put_tile(tgt, x, y, T_LV, UIA);
    if (lv >= 100) { print_num(tgt, x + 1, y, lv, 3); }
    else { print_num(tgt, x + 1, y, lv, lv >= 10 ? 2 : 1); }
}
void draw_cursor(uint8_t tgt, uint8_t x, uint8_t y, uint8_t on) BANKED {
    put_tile(tgt, x, y, on ? T_CUR_T : T_PAPER, UIA); put_tile(tgt, x, y + 1, on ? T_CUR_B : T_PAPER, UIA);
}

// 메뉴: (x,y) 이중선 상자, 항목은 한 줄 2칸 높이
uint8_t choose(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, const uint16_t *items, uint8_t n, uint8_t start, uint8_t cancel) BANKED {
    uint8_t i, sel = start, m = pool_mark();
    draw_frame(tgt, x, y, w, n * 2 + 2, 0);
    for (i = 0; i < n; i++) print_at(tgt, x + 2, y + 1 + i * 2, items[i]);
    for (;;) {
        for (i = 0; i < n; i++) draw_cursor(tgt, x + 1, y + 1 + i * 2, i == sel);
        frame();
        if (joy_new & J_UP) sel = sel ? sel - 1 : n - 1;
        if (joy_new & J_DOWN) sel = (sel + 1 == n) ? 0 : sel + 1;
        if (joy_new & J_A) { sfx_play(SFX_SELECT); break; }
        if ((joy_new & J_B) && cancel) { sel = 0xFF; break; }
    }
    pool_release(m);
    return sel;
}
static const uint16_t YESNO[2] = { S_YES, S_NO };
uint8_t ask(uint16_t sid) BANKED {
    uint8_t r;
    say_nowait(sid);
    // 글상자 위 오른쪽에 예/아니오 (창을 6줄부터 펼침)
    ui_open(6);
    tb_shown = 0; win_top = 6;
    tb_place();
    r = choose(TGT_WIN, 13, 6, 7, YESNO, 2, 0, 1);
    // 다시 글상자만
    win_top = 12; move_win(7, 96); tb_shown = 0; tb_open();
    return r == 0;
}

// HP 막대: (x,y)에 표시2 + 막대6 + 마개 = 9칸
uint8_t hp_level(uint16_t hp, uint16_t mx) BANKED {
    if (hp * 2 > mx) return 0;
    if (hp * 5 > mx) return 1;
    return 2;
}
void hp_bar(uint8_t tgt, uint8_t x, uint8_t y, uint16_t hp, uint16_t mx, uint8_t pal) BANKED {
    uint8_t px = mx ? (uint8_t)(((uint32_t)hp * 48 + mx - 1) / mx) : 0, i, k;
    if (hp == 0) px = 0;
    put_tile(tgt, x, y, T_TAG0, 0x80 | 3); put_tile(tgt, x + 1, y, T_TAG1, 0x80 | 3);
    for (i = 0; i < 6; i++) {
        k = px > 8 ? 8 : px; px -= k;
        put_tile(tgt, x + 2 + i, y, T_BAR0 + k, 0x80 | pal);
    }
    put_tile(tgt, x + 8, y, T_BARCAP, 0x80 | pal);
}

