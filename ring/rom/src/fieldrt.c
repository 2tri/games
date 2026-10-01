// 걷는 화면: 지도 그리기·스크롤, 주인공·사람 그림, 걷기, 말 걸기·표지판, 물건 줍기, 사건 자리, 풀숲 야생 만남
// (디지몬 세션 field.c 구조를 참고: 16×16 칸 지도, 화면 밖 한 칸까지 미리 그려 두고 스크롤)
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"
#include "story.h"
#include "field.h"
#include "fieldrt.h"

static MapDef MD;
static int16_t camx, camy;
static const int8_t DX[4] = { 0, 0, -1, 1 }, DY[4] = { 1, -1, 0, 0 };   // 아래·위·왼쪽·오른쪽
static const palette_color_t OBJPAL[4] = { RGB(31, 31, 31), RGB(31, 31, 30), RGB(11, 11, 11), RGB(2, 2, 2) };
static const palette_color_t BGPAL[4] = { RGB(30, 30, 29), RGB(21, 21, 20), RGB(11, 11, 11), RGB(2, 2, 2) };
static const palette_color_t FLASHPAL[4] = { RGB(2, 2, 2), RGB(11, 11, 11), RGB(21, 21, 20), RGB(30, 30, 29) };
uint8_t ev_arg;

static uint8_t flag_get(uint8_t f) { return S.flags[f >> 3] & (1 << (f & 7)); }
static void flag_set(uint8_t f) { S.flags[f >> 3] |= 1 << (f & 7); }
#define ITEM_FLAG(m, i) ((m) * 16 + (i))

static uint8_t raw_at(int8_t x, int8_t y) {
    if (x < 0 || y < 0 || x >= (int8_t)MD.w || y >= (int8_t)MD.h) return MT_TREE0 + (x & 1) + 2 * (y & 1);
    return MD.cells[(uint16_t)y * MD.w + x];
}
static uint8_t item_idx(int8_t x, int8_t y) { uint8_t i; for (i = 0; i < MD.ni; i++) if (MD.item[i].x == (uint8_t)x && MD.item[i].y == (uint8_t)y) return i; return 255; }
static uint8_t cell_at(int8_t x, int8_t y) {
    uint8_t c = raw_at(x, y), i;
    if (MTDEF[c][4] == MK_ITEM) { i = item_idx(x, y); if (i == 255 || flag_get(ITEM_FLAG(S.map, i))) c = MD.grass; }
    return c;
}
static uint8_t npc_at(int8_t x, int8_t y) { uint8_t i; for (i = 0; i < MD.nn; i++) if (MD.npc[i].x == (uint8_t)x && MD.npc[i].y == (uint8_t)y) return i; return 255; }
static uint8_t passable(int8_t x, int8_t y) {
    uint8_t k = MTDEF[cell_at(x, y)][4];
    return (k == MK_WALK || k == MK_GRASS || k == MK_ITEM) && npc_at(x, y) == 255;
}
static void draw_mt(int8_t mx, int8_t my) {
    static uint8_t t[4]; static const uint8_t a[4] = { 0, 0, 0, 0 };
    const uint8_t *p = MTDEF[cell_at(mx, my)];
    uint8_t bx = ((uint8_t)mx << 1) & 31, by = ((uint8_t)my << 1) & 31;
    t[0] = p[0]; t[1] = p[1]; t[2] = p[2]; t[3] = p[3];
    VBK_REG = 1; set_bkg_tiles(bx, by, 2, 2, a); VBK_REG = 0; set_bkg_tiles(bx, by, 2, 2, t);
}
static void draw_row(int8_t my) { int8_t x; for (x = (int8_t)S.x - 5; x <= (int8_t)S.x + 6; x++) draw_mt(x, my); }
static void draw_col(int8_t mx) { int8_t y; for (y = (int8_t)S.y - 5; y <= (int8_t)S.y + 5; y++) draw_mt(mx, y); }
static void render_all(void) { int8_t y; for (y = (int8_t)S.y - 5; y <= (int8_t)S.y + 5; y++) draw_row(y); }

// ── 그림(OBJ): 8×16 두 장이 16×16 한 명. 주인공 0·1번, 사람 2번부터 ──
static void spr16(uint8_t k, uint8_t tile, int16_t sx, int16_t sy) {
    if (sx < -16 || sx > 168 || sy < -16 || sy > 160) { move_sprite(k, 0, 0); move_sprite(k + 1, 0, 0); return; }
    set_sprite_tile(k, tile); set_sprite_tile(k + 1, tile + 2);
    set_sprite_prop(k, 0x08); set_sprite_prop(k + 1, 0x08);       // VRAM 1번 칸의 그림
    move_sprite(k, (uint8_t)(sx + 8), (uint8_t)(sy + 16)); move_sprite(k + 1, (uint8_t)(sx + 16), (uint8_t)(sy + 16));
}
#define PLAYER_TILE 128
#define NPC_TILE 160
static void draw_player(uint8_t step) { spr16(0, PLAYER_TILE + (S.dir * 2 + step) * 4, 64, 60); }
static void draw_npcs(void) {
    uint8_t i;
    for (i = 0; i < MD.nn && i < 8; i++) spr16(2 + i * 2, NPC_TILE, (int16_t)MD.npc[i].x * 16 - camx, (int16_t)MD.npc[i].y * 16 - camy - 4);
}
static void set_cam(int8_t ox, int8_t oy) {
    camx = (int16_t)S.x * 16 - 64 + ox; camy = (int16_t)S.y * 16 - 64 + oy;
    move_bkg((uint8_t)camx, (uint8_t)camy);
}

void field_enter(void) {
    uint8_t sv = CURRENT_BANK, r, c, row[20];
    DISPLAY_OFF;
    field_mode = 1;
    SWITCH_ROM(FIELD_BANK);
    memcpy(&MD, &MAPS[S.map], sizeof MD);
    VBK_REG = 0; set_bkg_data(0, FT_N, FT_TILES);
    VBK_REG = 1; set_sprite_data(PLAYER_TILE, 32, PLAYER_SPR); set_sprite_data(NPC_TILE, 4, NPC_SPR); VBK_REG = 0;
    if (_cpu == CGB_TYPE) { set_bkg_palette(0, 1, BGPAL); set_sprite_palette(0, 1, OBJPAL); }
    OBP0_REG = 0xE4;
    for (r = 0; r < 6; r++) {   // 글상자 창: VRAM 1번 칸 0~119
        for (c = 0; c < 20; c++) row[c] = 8;
        VBK_REG = 1; set_win_tiles(0, r, 20, 1, row);
        for (c = 0; c < 20; c++) row[c] = r * 20 + c;
        VBK_REG = 0; set_win_tiles(0, r, 20, 1, row);
    }
    move_win(7, 96); HIDE_WIN;
    SPRITES_8x16; SHOW_SPRITES;
    for (r = 0; r < 40; r++) move_sprite(r, 0, 0);
    render_all(); set_cam(0, 0); draw_npcs(); draw_player(0);
    DISPLAY_ON;
    SWITCH_ROM(sv);
}
static void talk(const char *t) {   // 글상자 아래로 내려가는 그림은 잠시 숨김
    uint8_t i;
    for (i = 2; i < 18; i += 2) if (shadow_OAM[i].y >= 96 + 16 - 8) { shadow_OAM[i].y = 0; shadow_OAM[i + 1].y = 0; }
    SHOW_WIN; say(t); HIDE_WIN; draw_npcs();
}
static void encounter_fx(void) {   // 띠리링: 화면 세 번 번쩍 + 소리
    uint8_t i;
    NR52_REG = 0x80; NR51_REG = 0xFF; NR50_REG = 0x77;
    NR10_REG = 0x16; NR11_REG = 0x80; NR12_REG = 0xF3; NR13_REG = 0x00; NR14_REG = 0x87;
    for (i = 0; i < 3; i++) {
        if (_cpu == CGB_TYPE) set_bkg_palette(0, 1, FLASHPAL); else BGP_REG = 0x1B;
        wait_frames(4);
        if (_cpu == CGB_TYPE) set_bkg_palette(0, 1, BGPAL); else BGP_REG = 0xE4;
        wait_frames(4);
    }
}
static void walk(uint8_t d) {
    uint8_t i;
    int8_t nx = (int8_t)S.x + DX[d], ny = (int8_t)S.y + DY[d];
    if (d == 0) draw_row(ny + 5); else if (d == 1) draw_row(ny - 5); else if (d == 2) draw_col(nx - 5); else draw_col(nx + 6);
    for (i = 1; i <= 8; i++) {
        set_cam(DX[d] * i * 2, DY[d] * i * 2);
        draw_npcs(); draw_player(i >= 2 && i <= 6);
        wait_vbl_done();
    }
    S.x = nx; S.y = ny; set_cam(0, 0); draw_npcs(); draw_player(0);
}
// 한 걸음 뒤: 물건·사건·풀숲. 돌려주는 값: EV_NONE / EV_TRIG(ev_arg=단계) / EV_WILD(ev_arg=적)
static uint8_t after_step(void) {
    uint8_t i, c = raw_at(S.x, S.y);
    if (MTDEF[c][4] == MK_ITEM && (i = item_idx(S.x, S.y)) != 255 && !flag_get(ITEM_FLAG(S.map, i))) {
        flag_set(ITEM_FLAG(S.map, i)); draw_mt(S.x, S.y);
        if (MD.item[i].kind == 0) { S.herb++; talk("약초를 주웠다! 가방에 넣었다."); } else { S.lembas++; talk("렘바스를 주웠다! 가방에 넣었다."); }
    }
    for (i = 0; i < MD.nt; i++) {
        const Trig *t = &MD.trig[i];
        if (S.x >= t->x && S.x < t->x + t->w && S.y >= t->y && S.y < t->y + t->h && S.step <= t->step) { ev_arg = t->step; return EV_TRIG; }
    }
    if (MTDEF[cell_at(S.x, S.y)][4] == MK_GRASS && rnd100() < MD.rate) {
        ev_arg = MD.wild[rnd() % MD.nw]; encounter_fx(); return EV_WILD;
    }
    return EV_NONE;
}
static void interact(void) {
    int8_t fx = (int8_t)S.x + DX[S.dir], fy = (int8_t)S.y + DY[S.dir];
    uint8_t i = npc_at(fx, fy);
    if (i != 255) { talk(MD.npc[i].text); return; }
    if (MTDEF[cell_at(fx, fy)][4] == MK_SIGN) for (i = 0; i < MD.ns; i++) if (MD.sign[i].x == (uint8_t)fx && MD.sign[i].y == (uint8_t)fy) { talk(MD.sign[i].text); return; }
}
uint8_t field_loop(void) {
    uint8_t sv = CURRENT_BANK, k, h, d, ev;
    SWITCH_ROM(FIELD_BANK);
    for (;;) {
        frame();
        k = key_poll(); h = key_held();
        if (k == K_A) { interact(); continue; }
        if (k == K_START) { save(); talk("여기까지 기록했다."); continue; }
        d = (h & J_DOWN) ? 0 : (h & J_UP) ? 1 : (h & J_LEFT) ? 2 : (h & J_RIGHT) ? 3 : 255;
        if (d == 255) continue;
        if (S.dir != d) { S.dir = d; draw_player(0); }
        if (!passable((int8_t)S.x + DX[d], (int8_t)S.y + DY[d])) continue;
        walk(d);
        ev = after_step();
        if (ev) { SWITCH_ROM(sv); return ev; }
    }
}
void field_start_pos(void) { uint8_t sv = CURRENT_BANK; SWITCH_ROM(FIELD_BANK); S.x = MAPS[S.map].sx; S.y = MAPS[S.map].sy; S.dir = MAPS[S.map].sdir; SWITCH_ROM(sv); }
