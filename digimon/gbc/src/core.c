// 디지몬 GBC — 바탕 기능: 입력, 뱅크, 팔레트, 글(한글 8×16), 메뉴, 그림, 디지몬 계산
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"

game_t G;
uint8_t joy, joy_new;
static uint8_t joy_old;
uint16_t frames;
static uint16_t seed = 0xACE1;

void frame(void) {
    wait_vbl_done();
    joy_old = joy; joy = joypad(); joy_new = joy & ~joy_old;
    frames++;
    if (scene == SCENE_FIELD) G.time++;
}
void wait_frames(uint8_t n) { while (n--) frame(); }
uint8_t wait_press(void) {
    for (;;) { frame(); if (joy_new & (J_A | J_B)) return joy_new; }
}
uint16_t rnd(void) {
    seed ^= seed << 7; seed ^= seed >> 9; seed ^= seed << 8;
    return seed ^ frames ^ DIV_REG;
}
uint8_t rnd8(uint8_t n) { return n ? (uint8_t)((rnd() & 0xFF) * n >> 8) : 0; }

// ───────── 뱅크 ─────────
uint8_t far_u8(uint8_t bank, const uint8_t *p) {
    uint8_t s = CURRENT_BANK, v; SWITCH_ROM(bank); v = *p; SWITCH_ROM(s); return v;
}
uint16_t far_u16(uint8_t bank, const uint8_t *p) {
    uint8_t s = CURRENT_BANK; uint16_t v; SWITCH_ROM(bank); v = p[0] | (p[1] << 8); SWITCH_ROM(s); return v;
}
void far_copy(void *dst, uint8_t bank, const void *src, uint16_t n) {
    uint8_t s = CURRENT_BANK; SWITCH_ROM(bank); memcpy(dst, src, n); SWITCH_ROM(s);
}
void far_vram(uint8_t vbank, uint8_t first, uint8_t n, uint8_t bank, const uint8_t *src) {
    uint8_t s = CURRENT_BANK; SWITCH_ROM(bank);
    VBK_REG = vbank; set_bkg_data(first, n, src); VBK_REG = 0;
    SWITCH_ROM(s);
}

void far_sprite(uint8_t vbank, uint8_t first, uint8_t n, uint8_t bank, const uint8_t *src) {
    uint8_t s = CURRENT_BANK; SWITCH_ROM(bank);
    VBK_REG = vbank; set_sprite_data(first, n, src); VBK_REG = 0;
    SWITCH_ROM(s);
}

// ───────── 팔레트 ─────────
uint16_t bgpal[32], obpal[32];
uint8_t fade_lv, fade_white;
static uint16_t mixc(uint16_t c) {
    uint8_t r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31, t = fade_white ? 31 : 0;
    r = r + ((int16_t)(t - r) * fade_lv) / 8; g = g + ((int16_t)(t - g) * fade_lv) / 8; b = b + ((int16_t)(t - b) * fade_lv) / 8;
    return r | (g << 5) | ((uint16_t)b << 10);
}
void pal_apply(void) {
    static uint16_t tmp[32];
    uint8_t i;
    for (i = 0; i < 32; i++) tmp[i] = mixc(bgpal[i]);
    set_bkg_palette(0, 8, tmp);
    for (i = 0; i < 32; i++) tmp[i] = mixc(obpal[i]);
    set_sprite_palette(0, 8, tmp);
}
void fade_out(uint8_t white) {
    if (fade_lv == 8) return;
    fade_white = white;
    while (fade_lv < 8) { fade_lv++; pal_apply(); frame(); frame(); }
}
void fade_in(void) {
    while (fade_lv) { fade_lv--; pal_apply(); frame(); frame(); }
}
void flash(uint8_t n) {
    uint8_t keep = fade_lv, kw = fade_white;
    while (n--) {
        fade_white = 1; fade_lv = 8; pal_apply(); wait_frames(4);
        fade_lv = 4; pal_apply(); wait_frames(3);
        fade_lv = 0; pal_apply(); wait_frames(4);
    }
    fade_lv = keep; fade_white = kw; pal_apply();
}
void shake(uint8_t n) {
    uint8_t sx = SCX_REG, sy = SCY_REG;
    while (n--) { SCX_REG = sx + ((n & 1) ? 2 : -2); SCY_REG = sy + ((n & 2) ? 1 : -1); frame(); frame(); }
    SCX_REG = sx; SCY_REG = sy;
}
static const uint16_t HPCOL[] = { RGB(3, 21, 6), RGB(21, 28, 20), RGB(31, 23, 0), RGB(31, 28, 19), RGB(29, 7, 3), RGB(31, 21, 18) };
void set_hp_color(uint8_t palno, uint8_t lvl) {
    bgpal[palno * 4 + 0] = RGB(31, 31, 31); bgpal[palno * 4 + 1] = HPCOL[lvl * 2 + 1]; bgpal[palno * 4 + 2] = HPCOL[lvl * 2]; bgpal[palno * 4 + 3] = RGB(3, 3, 3);
    pal_apply();
}

// ───────── 타일 놓기 ─────────
uint8_t win_top = 12;
void put_tile(uint8_t tgt, uint8_t x, uint8_t y, uint8_t tile, uint8_t attr) {
    if (tgt == TGT_WIN) {
        y -= win_top;
        VBK_REG = 1; set_win_tile_xy(x, y, attr); VBK_REG = 0; set_win_tile_xy(x, y, tile);
    } else {
        VBK_REG = 1; set_bkg_tile_xy(x, y, attr); VBK_REG = 0; set_bkg_tile_xy(x, y, tile);
    }
}
#define UIA 0x80     // 화면 부품: 팔레트 0, 스프라이트보다 앞
// ───────── 창 (위에 덮는 층) ─────────
void ui_open(uint8_t top) {
    // top 줄부터 창이 덮음. 덮이는 곳 중 글상자(12줄~) 위쪽은 배경 타일을 그대로 베껴 옴
    static uint8_t row[20], arow[20];
    uint8_t y, x, bx = SCX_REG >> 3, by = SCY_REG >> 3;
    HIDE_WIN;                       // 베끼는 동안 지저분하게 보이지 않게
    win_top = top;
    for (y = top; y < 18; y++) {
        for (x = 0; x < 20; x++) {
            VBK_REG = 0; row[x] = get_bkg_tile_xy((bx + x) & 31, (by + y) & 31);
            VBK_REG = 1; arow[x] = get_bkg_tile_xy((bx + x) & 31, (by + y) & 31);
        }
        VBK_REG = 1; set_win_tiles(0, y - top, 20, 1, arow);
        VBK_REG = 0; set_win_tiles(0, y - top, 20, 1, row);
    }
    move_win(7, top << 3);
    SHOW_WIN;
}
void ui_close(void) { HIDE_WIN; win_top = 12; move_win(7, 144); tb_shown = 0; }

// ───────── 한글 글자 ─────────
static const uint8_t ZERO16[16];
static void glyph_to(uint16_t ch, uint8_t vbank, uint8_t tile) {
    uint8_t s = CURRENT_BANK, fi = 0;
    while (ch >= FONT_PER) { ch -= FONT_PER; fi++; }
    SWITCH_ROM(FONTS[fi].bank);
    VBK_REG = vbank; set_bkg_1bpp_data(tile, 2, FONTS[fi].ptr + ch * 16); VBK_REG = 0;
    SWITCH_ROM(s);
}

// 글 펼치기: 문자열 → 글자 번호 목록 (변수·조사 풀어 씀)
#define T_END 0xFFFF
#define T_NL 0xFFFE
#define T_PG 0xFFFD
static uint16_t tbuf[160];
static uint8_t tlen;
uint8_t var_sp[2];
uint16_t var_num[2];
uint8_t var_mv, var_item;
static uint8_t sbuf[200];
static uint16_t last_ch;

static void emit(uint16_t c) { if (tlen < 159) { tbuf[tlen++] = c; } if (c < 0xFFF0) last_ch = c; }
static void expand_bytes(const uint8_t *p, uint8_t depth);
static void expand_sid(uint16_t sid, uint8_t depth) {
    static uint8_t buf2[40];
    farptr_t f;
    far_copy(&f, MISC_BANK, &STRTAB[sid], sizeof(farptr_t));      // 목록표는 MISC 뱅크에
    if (depth == 0) { far_copy(sbuf, f.bank, f.ptr, 200); expand_bytes(sbuf, 0); }
    else { far_copy(buf2, f.bank, f.ptr, 40); expand_bytes(buf2, 1); }
}
static void emit_num(uint16_t v) {
    uint8_t d[5], n = 0;
    do { d[n++] = v % 10; v /= 10; } while (v);
    while (n) emit(DIGCH[d[--n]]);
}
static uint8_t comp_kid(void) { return G.kid == COMP_KID ? COMP_ALT : COMP_KID; }
static void emit_var(uint8_t v, uint8_t depth) {
    uint8_t sp;
    switch (v) {
    case 0: expand_sid(KID_NAME[G.kid], depth + 1); break;
    case 1: expand_sid(SPECIES[G.party[0].sp].name, depth + 1); break;
    case 2: expand_sid(KID_NAME[comp_kid()], depth + 1); break;
    case 3: expand_sid(SPECIES[KID_BABY[G.kid]].name, depth + 1); break;
    case 4: expand_sid(SPECIES[KID_PARTNER[G.kid]].name, depth + 1); break;
    case 5: expand_sid(SPECIES[var_sp[0]].name, depth + 1); break;
    case 6: expand_sid(SPECIES[var_sp[1]].name, depth + 1); break;
    case 7: emit_num(var_num[0]); break;
    case 8: expand_sid(MOVES[var_mv].name, depth + 1); break;
    case 9: expand_sid(IT_NAME[var_item], depth + 1); break;
    case 10: emit_num(var_num[1]); break;
    case 11: sp = G.party[0].sp; expand_sid(MOVES[SPECIES[sp].sig[0]].name, depth + 1); break;
    }
}
static void expand_bytes(const uint8_t *p, uint8_t depth) {
    uint8_t b, f;
    for (;;) {
        b = *p++;
        if (b == 0) break;
        if (b == 1) emit(T_NL);
        else if (b == 2) emit(T_PG);
        else if (b == 3) emit_var(*p++, depth);
        else if (b == 4) {
            b = *p++; f = CHARFLAG[last_ch];
            // 0 이/가 1 은/는 2 을/를 3 와/과 4 으로/로  — JOSACH: 이 가 은 는 을 를 과 와 으 로
            if (b == 0) emit(JOSACH[(f & 1) ? 0 : 1]);
            else if (b == 1) emit(JOSACH[(f & 1) ? 2 : 3]);
            else if (b == 2) emit(JOSACH[(f & 1) ? 4 : 5]);
            else if (b == 3) emit(JOSACH[(f & 1) ? 6 : 7]);
            else { if ((f & 1) && !(f & 2)) emit(JOSACH[8]); emit(JOSACH[9]); }
        }
        else if (b >= 0xF0) { emit(224 + ((uint16_t)(b - 0xF0) << 8) + *p++); }
        else emit(b - 0x10);
    }
}
static void expand(uint16_t sid) { tlen = 0; last_ch = CH_SPACE; expand_sid(sid, 0); tbuf[tlen] = T_END; }

// ───────── 글상자 (창 12~17줄) ─────────
uint8_t tb_shown;
#define TB_T0 80
static void tb_clear(void) {
    uint8_t i;
    for (i = 0; i < 36; i++) set_bkg_1bpp_data(TB_T0 + i * 2, 2, ZERO16);
}
static void tb_more(uint8_t on) { put_tile(TGT_WIN, 18, 17, on ? T_F_BMORE : T_F_B, UIA); }
void tb_open(void) {
    uint8_t l, c;
    if (tb_shown) return;
    if (!(LCDC_REG & LCDCF_WINON) || win_top > 12) { win_top = 12; move_win(7, 96); }
    tb_clear();
    draw_frame(TGT_WIN, 0, 12, 20, 6, 0);
    for (l = 0; l < 2; l++) for (c = 0; c < 18; c++) {
        put_tile(TGT_WIN, 1 + c, 13 + l * 2, TB_T0 + (l * 18 + c) * 2, UIA);
        put_tile(TGT_WIN, 1 + c, 14 + l * 2, TB_T0 + (l * 18 + c) * 2 + 1, UIA);
    }
    SHOW_WIN; tb_shown = 1;
}
void tb_close(void) { ui_close(); }
void tb_place(void) {   // 글자 타일은 그대로 두고 글상자 틀·칸만 지금 창 자리에 다시 놓기
    uint8_t l, c;
    draw_frame(TGT_WIN, 0, 12, 20, 6, 0);
    for (l = 0; l < 2; l++) for (c = 0; c < 18; c++) {
        put_tile(TGT_WIN, 1 + c, 13 + l * 2, TB_T0 + (l * 18 + c) * 2, UIA);
        put_tile(TGT_WIN, 1 + c, 14 + l * 2, TB_T0 + (l * 18 + c) * 2 + 1, UIA);
    }
}

static void tb_run(uint8_t wait_end) {
    uint8_t i = 0, line = 0, col = 0, fast = 0;
    uint16_t c;
    tb_open(); tb_clear(); tb_more(0);
    for (;;) {
        c = tbuf[i];
        if (c == T_END) break;
        i++;
        if (c == T_NL) { if (line == 0) { line = 1; col = 0; continue; } c = T_PG; }
        if (c == T_PG) {
            tb_more(1);
            while (!(joy_new & (J_A | J_B))) { frame(); tb_more(((frames >> 4) & 1) == 0); }
            tb_more(0); tb_clear(); line = 0; col = 0; fast = 0; frame();
            continue;
        }
        if (col >= 18) { if (line == 0) { line = 1; col = 0; } else { tb_more(1); wait_press(); tb_more(0); tb_clear(); line = 0; col = 0; fast = 0; } }
        glyph_to(c, 0, TB_T0 + (line * 18 + col) * 2);
        col++;
        if (!fast) { frame(); if (joy_new & (J_A | J_B)) fast = 1; }
    }
    if (wait_end) {
        tb_more(1);
        while (!(joy_new & (J_A | J_B))) { frame(); tb_more(((frames >> 4) & 1) == 0); }
        tb_more(0);
    }
}
void say(uint16_t sid) { expand(sid); tb_run(1); }
void say_nowait(uint16_t sid) { expand(sid); tb_run(0); }

// ───────── 이름표 글자 (재사용 칸) ─────────
// 필드 위 메뉴: 1번 VRAM 192~255 (32칸)
// 화면 전체(전투·목록): 0번 VRAM 152~255 (52칸) + 1번 VRAM 214~255 (21칸) — 1번 128~213은 디지몬 그림 자리
static uint16_t pool_ch[73];
static uint8_t pool_n, pool_full;
void pool_reset(uint8_t full) { pool_n = 0; pool_full = full; }
uint8_t pool_mark(void) { return pool_n; }
void pool_release(uint8_t m) { pool_n = m; }
static uint8_t slot_tile(uint8_t i, uint8_t *vb) {
    if (!pool_full) { *vb = 1; return 192 + i * 2; }
    if (i < 52) { *vb = 0; return 152 + i * 2; }
    *vb = 1; return 214 + (i - 52) * 2;
}
static uint8_t pool_get(uint16_t ch, uint8_t *attr) {
    uint8_t i, vb, t;
    for (i = 0; i < pool_n; i++) if (pool_ch[i] == ch) break;
    if (i == pool_n) {
        if (pool_n >= (pool_full ? 73 : 32)) i = pool_n - 1;   // 넘치면 마지막 칸을 덮어씀
        else pool_n++;
        pool_ch[i] = ch;
        t = slot_tile(i, &vb); glyph_to(ch, vb, t);
    }
    t = slot_tile(i, &vb);
    *attr = UIA | (vb ? 0x08 : 0);
    return t;
}
uint8_t print_max = 255;
static uint8_t print_buf(uint8_t tgt, uint8_t x, uint8_t y) {
    uint8_t i, a, t, n = 0;
    for (i = 0; i < tlen && n < print_max; i++) {
        uint16_t c = tbuf[i];
        if (c >= 0xFFF0) continue;
        if (c == CH_SPACE) { put_tile(tgt, x + n, y, T_PAPER, UIA); put_tile(tgt, x + n, y + 1, T_PAPER, UIA); n++; continue; }
        t = pool_get(c, &a);
        put_tile(tgt, x + n, y, t, a); put_tile(tgt, x + n, y + 1, t + 1, a);
        n++;
    }
    return n;
}
uint8_t print_at(uint8_t tgt, uint8_t x, uint8_t y, uint16_t sid) { expand(sid); return print_buf(tgt, x, y); }
uint8_t print_right(uint8_t tgt, uint8_t xr, uint8_t y, uint16_t sid) {
    uint8_t i, n = 0;
    expand(sid);
    for (i = 0; i < tlen; i++) if (tbuf[i] < 0xFFF0) n++;
    return print_buf(tgt, xr - n, y);
}
// ───────── 그림 ─────────
static void ui_pals(void) {     // 0: 글·테두리, 3: HP 표시(노랑)·경험치(파랑)
    bgpal[0] = RGB(31, 31, 31); bgpal[1] = RGB(31, 31, 31); bgpal[2] = RGB(13, 13, 13); bgpal[3] = RGB(3, 3, 3);
    bgpal[12] = RGB(31, 31, 31); bgpal[13] = RGB(31, 26, 14); bgpal[14] = RGB(9, 18, 30); bgpal[15] = RGB(3, 3, 3);
}
void hide_sprites(void) { uint8_t i; for (i = 0; i < 40; i++) move_sprite(i, 0, 0); }
void screen_clear(void) {
    static uint8_t row[32];
    uint8_t y;
    memset(row, T_BLANK, 32);
    for (y = 0; y < 32; y++) { VBK_REG = 1; memset(row, 0, 32); set_bkg_tiles(0, y, 32, 1, row); VBK_REG = 0; memset(row, T_BLANK, 32); set_bkg_tiles(0, y, 32, 1, row); }
    move_bkg(0, 0); hide_sprites(); ui_close(); ui_pals();
}
void load_ui(void) {
    far_vram(0, 0, N_UI_TILES, MISC_BANK, ui_tiles);
    ui_pals();
}
uint8_t pic_load(uint8_t pic, uint8_t vbank, uint8_t tile0, uint8_t palno) {
    farptr_t fp; const farptr_t *f = &fp;
    uint8_t s = CURRENT_BANK, w, h, i;
    far_copy(&fp, MISC_BANK, &PICTAB[pic], sizeof(farptr_t));
    SWITCH_ROM(f->bank);
    w = f->ptr[0]; h = f->ptr[1];
    for (i = 0; i < 4; i++) bgpal[palno * 4 + i] = f->ptr[2 + i * 2] | (f->ptr[3 + i * 2] << 8);
    VBK_REG = vbank; set_bkg_data(tile0, w * h, f->ptr + 10); VBK_REG = 0;
    SWITCH_ROM(s);
    return w;
}
void pic_place(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tile0, uint8_t attr) {
    uint8_t i, j;
    for (j = 0; j < h; j++) for (i = 0; i < w; i++) put_tile(TGT_BG, x + i, y + j, tile0 + j * w + i, attr);
}
void pic_screen(uint8_t sp) {
    screen_clear();
    scene = SCENE_OTHER;
    if (sp != 0xF0) {
        pic_load(SPECIES[sp].front, 1, 128, 4);
        pic_place(6, 2, 7, 7, 128, 4 | 0x08);
    }
    pal_apply();
}

// ───────── 깃발 ─────────
uint8_t flag_get(uint16_t f) { return f == 0xFFFF ? 0 : (G.flags[f >> 3] >> (f & 7)) & 1; }
void flag_set(uint16_t f) { if (f != 0xFFFF) G.flags[f >> 3] |= 1 << (f & 7); }
void flag_clr(uint16_t f) { if (f != 0xFFFF) G.flags[f >> 3] &= ~(1 << (f & 7)); }
