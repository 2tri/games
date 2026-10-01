// 디지몬 GBC — 필드: 지도 그리기·스크롤, 주인공·NPC 그림, 걷기, 말 걸기, 지도 이동, 야생 만남
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"

uint8_t scene, cur_map = 0xFF;
uint8_t warp_pending, wp_map, wp_x, wp_y, wp_dir;
uint8_t field_idle;        // 필드에서 입력을 기다리는 중 (자동 시험용 표시)
static uint8_t map_bank;
static map_t M;
static uint8_t px, py;
static int16_t camx, camy;

typedef struct { uint8_t x, y, dir, base, nfr, pal, flags; uint16_t script; } npcrt_t;
static npcrt_t NP[10];
static uint8_t nn;

static const int8_t DX[4] = { 0, 0, -1, 1 }, DY[4] = { 1, -1, 0, 0 };
#define MAPB() SWITCH_ROM(map_bank)

static uint8_t mt_at(int8_t x, int8_t y) {
    uint8_t i; const uint8_t *o;
    if (x >= 0 && y >= 0 && x < (int8_t)M.w && y < (int8_t)M.h) return M.cells[(uint16_t)y * M.w + x];
    for (i = 0; i < M.n_open; i++) {
        o = M.opens + i * 5;
        if (x >= (int8_t)o[0] && y >= (int8_t)o[1] && x <= (int8_t)o[2] && y <= (int8_t)o[3]) return o[4];
    }
    if (M.split != 0xFF && x >= (int8_t)M.split) return M.border2;
    return M.border;
}
static void draw_mt(int8_t mx, int8_t my) {
    static uint8_t t[4], a[4];
    const uint8_t *p = M.mt + mt_at(mx, my) * 9;
    uint8_t bx = ((uint8_t)mx << 1) & 31, by = ((uint8_t)my << 1) & 31;
    t[0] = p[0]; t[1] = p[1]; t[2] = p[2]; t[3] = p[3]; a[0] = p[4]; a[1] = p[5]; a[2] = p[6]; a[3] = p[7];
    VBK_REG = 1; set_bkg_tiles(bx, by, 2, 2, a); VBK_REG = 0; set_bkg_tiles(bx, by, 2, 2, t);
}
static void draw_col(int8_t mx) { int8_t y; for (y = (int8_t)py - 5; y <= (int8_t)py + 5; y++) draw_mt(mx, y); }
static void draw_row(int8_t my) { int8_t x; for (x = (int8_t)px - 5; x <= (int8_t)px + 6; x++) draw_mt(x, my); }
static void render_all(void) { int8_t y; for (y = (int8_t)py - 5; y <= (int8_t)py + 5; y++) draw_row(y); }

static void map_load(uint8_t m) {
    uint8_t i;
    cur_map = m; map_bank = MAPTAB[m].bank;
    far_copy(&M, map_bank, MAPTAB[m].map, sizeof(map_t));
    MAPB();
    VBK_REG = 0; set_bkg_data(152, M.n_t0, M.t0);
    if (M.n_t1) { VBK_REG = 1; set_bkg_data(M.t1_base, M.n_t1, M.t1); VBK_REG = 0; }
    memcpy(&bgpal[4], M.pal, 56);
    music_play(M.song);
    if (M.n_spr) { VBK_REG = 1; set_sprite_data(48, M.n_spr, M.spr); VBK_REG = 0; }
    for (i = 0; i < M.n_objpal * 4; i++) obpal[4 + i] = M.objpal[i];
    { uint8_t s = CURRENT_BANK; SWITCH_ROM(MISC_BANK); VBK_REG = 1; set_sprite_data(0, 48, kid_spr + (uint16_t)G.kid * 768); VBK_REG = 0; SWITCH_ROM(s); }
    for (i = 0; i < 4; i++) obpal[i] = KID_PAL[G.kid * 4 + i];
}

static void npc_refresh(void) {
    uint8_t i; const uint8_t *d; uint16_t cond; uint8_t ct, vis;
    MAPB(); nn = 0;
    for (i = 0; i < M.n_npc && nn < 9; i++) {
        d = M.npcs + i * NPC_SIZE;
        cond = d[NPC_COND] | (d[NPC_COND + 1] << 8); ct = (d[NPC_FLAGS] >> 1) & 3; vis = 1;
        if (ct == 1 && !flag_get(cond)) vis = 0;
        if (ct == 2 && flag_get(cond)) vis = 0;
        if (d[NPC_HIDEKID] != 0xFF && d[NPC_HIDEKID] == G.kid) vis = 0;
        if (!vis) continue;
        NP[nn].x = d[NPC_X]; NP[nn].y = d[NPC_Y]; NP[nn].dir = d[NPC_DIR]; NP[nn].flags = d[NPC_FLAGS];
        if (d[NPC_ALTKID] == G.kid) { NP[nn].base = d[NPC_BASE2]; NP[nn].nfr = d[NPC_NFR2]; NP[nn].pal = d[NPC_PAL2]; }
        else { NP[nn].base = d[NPC_BASE]; NP[nn].nfr = d[NPC_NFR]; NP[nn].pal = d[NPC_PAL]; }
        NP[nn].script = d[NPC_SCRIPT] | (d[NPC_SCRIPT + 1] << 8);
        nn++;
    }
}
static void spr_pair(uint8_t k, uint8_t tl, uint8_t prop, int16_t sx, int16_t sy) {
    // 16×16 = 8×16 두 장. prop 에 0x20(좌우 뒤집기)이면 오른쪽 반을 왼쪽에
    uint8_t flip = prop & 0x20;
    if (sx < -16 || sx > 168 || sy < -16 || sy > 152) { move_sprite(k, 0, 0); move_sprite(k + 1, 0, 0); return; }
    set_sprite_tile(k, flip ? tl + 2 : tl); set_sprite_tile(k + 1, flip ? tl : tl + 2);
    set_sprite_prop(k, prop); set_sprite_prop(k + 1, prop);
    move_sprite(k, (uint8_t)(sx + 8), (uint8_t)(sy + 16)); move_sprite(k + 1, (uint8_t)(sx + 16), (uint8_t)(sy + 16));
}
// 사람(키 큰 그림 16×32, flags 8)은 OBJ 4장: k·k+1 아래 반, k+2·k+3 위 반. 그림 한 장 = 타일 8개(위 4·아래 4)
// OBJ 순서: 주인공 아래 반 0·1 (맨 앞), NPC 2~37, 주인공 머리 38·39 (맨 뒤: 작은 NPC가 머리에 가려지지 않게)
static void person(uint8_t k, uint8_t kt, uint8_t tl, uint8_t prop, int16_t sx, int16_t sy, uint8_t tall) {
    if (tall) { spr_pair(k, tl + 4, prop, sx, sy); spr_pair(kt, tl, prop, sx, sy - 16); }
    else { spr_pair(k, tl, prop, sx, sy); move_sprite(kt, 0, 0); move_sprite(kt + 1, 0, 0); }
}
static void npcs_draw(void) {
    uint8_t i, fr, flip, tall;
    for (i = 0; i < nn; i++) {
        npcrt_t *n = &NP[i];
        fr = 0; flip = 0; tall = n->flags & 8;
        if (n->nfr == 3) { fr = n->dir == 0 ? 0 : n->dir == 1 ? 1 : 2; flip = n->dir == 3; }
        else if (n->nfr == 2 && n->dir >= 2) { fr = 1; flip = n->dir == 3; }
        person(2 + i * 4, 4 + i * 4, n->base + fr * (tall ? 8 : 4), 0x08 | n->pal | (flip ? 0x20 : 0),
               (int16_t)n->x * 16 - camx, (int16_t)n->y * 16 - camy - 4, tall);
    }
    for (i = 2 + nn * 4; i < 38; i++) move_sprite(i, 0, 0);
}
static uint8_t step_foot, hopy, slide;
static void player_draw(uint8_t walking) {
    uint8_t d = G.dir, fr, flip = 0;
    if (d == 0) fr = 0; else if (d == 1) fr = 2; else { fr = 4; flip = d == 3; }
    if (walking) { fr++; if (d < 2 && step_foot) flip = 1; }
    person(0, 38, fr * 8, 0x08 | (flip ? 0x20 : 0), 64, 60 - hopy, 1);
}
static void set_cam(int16_t ox, int16_t oy) {
    camx = (int16_t)px * 16 - 64 + ox; camy = (int16_t)py * 16 - 64 + oy;
    move_bkg((uint8_t)camx, (uint8_t)camy);
}

static void field_show(void) {
    DISPLAY_OFF;
    hide_sprites(); HIDE_WIN; win_top = 12; tb_shown = 0; pool_reset(0);
    map_load(cur_map); render_all(); npc_refresh();
    set_cam(0, 0); npcs_draw(); player_draw(0);
    pal_apply();
    scene = SCENE_FIELD;
    DISPLAY_ON;
}
void field_restore(void) { uint8_t sb = CURRENT_BANK; if (cur_map != 0xFF) field_show(); SWITCH_ROM(sb); }

static void post_script(void) {
    if (cur_map == 0xFF) return;
    if (scene != SCENE_FIELD) field_show();
    tb_close(); MAPB(); npc_refresh(); npcs_draw(); player_draw(0);
}

void field_enter(uint8_t map, uint8_t x, uint8_t y, uint8_t dir, uint8_t run_enter) {
    uint8_t sb = CURRENT_BANK;      // 다른 뱅크 코드(스크립트)에서 불려도 돌아갈 때 그 뱅크로
    if (fade_lv < 8) fade_out(0);
    cur_map = map; px = x; py = y; if (dir != 0xFF) G.dir = dir;
    G.map = map; G.x = x; G.y = y;
    field_show();
    fade_in();
    if (run_enter) {
        MAPB();
        if (M.on_enter != 0xFFFF) { run_script(map_bank, M.script, M.on_enter); post_script(); }
    }
    SWITCH_ROM(sb);
}
void do_warp(uint8_t map, uint8_t x, uint8_t y, uint8_t dir) { field_enter(map, x, y, dir, 1); }

static void whiteout(void) {
    say(S_WO1); say(S_WO2); tb_close();
    fade_out(0);
    heal_all();
    cur_map = 0xFF;
    field_enter(G.heal_map, G.heal_x, G.heal_y, G.heal_dir, 0);
    say(S_WO3); tb_close();
}
uint8_t field_battle(uint8_t sp, uint8_t lv, uint8_t kind) {
    uint8_t sb = CURRENT_BANK, r = battle(sp, lv, kind);
    if (r == 0) whiteout(); else field_show();
    SWITCH_ROM(sb);
    return r;
}

static uint8_t npc_at(uint8_t x, uint8_t y) {
    uint8_t i; for (i = 0; i < nn; i++) if (NP[i].x == x && NP[i].y == y) return i;
    return 0xFF;
}
static uint8_t warp_at(uint8_t x, uint8_t y) {
    uint8_t i; const uint8_t *w;
    for (i = 0; i < M.n_warp; i++) { w = M.warps + i * 6; if (w[0] == x && w[1] == y) return i; }
    return 0xFF;
}
static uint8_t walkable(uint8_t x, uint8_t y) {
    if (x >= M.w || y >= M.h) return warp_at(x, y) != 0xFF;
    if (M.mt[mt_at(x, y) * 9 + 8] & MT_SOLID) return 0;
    if (npc_at(x, y) != 0xFF) return 0;
    return 1;
}

static void wild(void) {
    uint8_t i, tot = 0, r, sp = 0, lv = 1; const uint8_t *e;
    for (i = 0; i < M.n_enc; i++) tot += M.enc[i * 4 + 3];
    r = rnd8(tot);
    for (i = 0; i < M.n_enc; i++) {
        e = M.enc + i * 4;
        if (r < e[3]) { sp = e[0]; lv = e[1] + rnd8(e[2] - e[1] + 1); break; }
        r -= e[3];
    }
    field_battle(sp, lv, 0);
}

static void arrive(void) {
    uint8_t i, w; const uint8_t *t; uint16_t once, need, unl, scr;
    G.x = px; G.y = py;
    // 디지타마 걸음
    for (i = 0; i < G.nparty; i++) {
        if (G.party[i].egg && G.party[i].steps) {
            if (--G.party[i].steps == 0) { hatch_scene(i); field_show(); }
        }
    }
    MAPB();
    w = warp_at(px, py);
    if (w != 0xFF) {
        t = M.warps + w * 6;
        do_warp(t[2], t[3], t[4], t[5]); return;
    }
    for (i = 0; i < M.n_trig; i++) {
        t = M.trigs + i * 12;
        if (px < t[0] || py < t[1] || px >= t[0] + t[2] || py >= t[1] + t[3]) continue;
        once = t[4] | (t[5] << 8); need = t[6] | (t[7] << 8); unl = t[8] | (t[9] << 8); scr = t[10] | (t[11] << 8);
        if (once != 0xFFFF && flag_get(once)) continue;
        if (need != 0xFFFF && !flag_get(need)) continue;
        if (unl != 0xFFFF && flag_get(unl)) continue;
        flag_set(once);
        run_script(map_bank, M.script, scr); post_script();
        return;
    }
    for (i = 0; i < nn; i++) {          // 눈이 마주치면 덤비는 디지몬 (트레이너 오마주)
        npcrt_t *n = &NP[i]; int8_t dx, dy;
        if (!(n->flags & 16)) continue;
        dx = (int8_t)px - (int8_t)n->x; dy = (int8_t)py - (int8_t)n->y;
        if ((n->dir == 0 && !dx && dy > 0 && dy <= 4) || (n->dir == 1 && !dx && dy < 0 && dy >= -4) ||
            (n->dir == 2 && !dy && dx < 0 && dx >= -4) || (n->dir == 3 && !dy && dx > 0 && dx <= 4)) {
            G.dir = n->dir ^ 1; player_draw(0);
            run_script(map_bank, M.script, n->script); post_script();
            return;
        }
    }
    if ((M.mt[mt_at(px, py) * 9 + 8] & MT_GRASS) && M.n_enc && alive_count()) {
        if (rnd8(255) < M.enc_rate) wild();
    }
}

static void interact(void) {
    uint8_t tx = px + DX[G.dir], ty = py + DY[G.dir], i; const uint8_t *s;
    i = npc_at(tx, ty);
    if (i != 0xFF) {
        if (!(NP[i].flags & 1)) { NP[i].dir = G.dir ^ 1; npcs_draw(); }
        run_script(map_bank, M.script, NP[i].script); post_script();
        return;
    }
    for (i = 0; i < M.n_sign; i++) {
        s = M.signs + i * 4;
        if (s[0] == tx && s[1] == ty) { run_script(map_bank, M.script, s[2] | (s[3] << 8)); post_script(); return; }
    }
}

void field_loop(void) {
    uint8_t d, prevd = 0, hold = 0, k, nd;
    for (;;) {
        field_idle = 1;
        frame();
        field_idle = 0;
        if (warp_pending) { warp_pending = 0; do_warp(wp_map, wp_x, wp_y, wp_dir); continue; }
        MAPB();
        if (joy_new & J_START) {
            start_menu();
            if (scene != SCENE_FIELD) field_show(); else { ui_close(); npcs_draw(); player_draw(0); }
            continue;
        }
        if (joy_new & J_A) { interact(); continue; }
        d = joy & (J_UP | J_DOWN | J_LEFT | J_RIGHT);
        if (slide) { slide = 0; d = J_DOWN; prevd = J_DOWN; hold = 0; }      // 턱에서 계속 뛰어내림
        if (!d) { prevd = 0; hold = 0; continue; }
        nd = (d & J_DOWN) ? 0 : (d & J_UP) ? 1 : (d & J_LEFT) ? 2 : 3;
        if (!prevd && nd != G.dir) hold = 6;
        prevd = d; G.dir = nd;
        if (hold) { hold--; player_draw(0); continue; }
        {
            uint8_t tx = px + DX[nd], ty = py + DY[nd], hop = 0;
            if (tx < M.w && ty < M.h && (M.mt[mt_at(tx, ty) * 9 + 8] & MT_LEDGE)) {       // 턱: 아래로만
                if (nd != 0) { player_draw(0); continue; }
                hop = 1;
            }
            if (!walkable(tx, ty)) { player_draw(0); continue; }
            if (nd == 0) draw_row((int8_t)py + 6);
            else if (nd == 1) draw_row((int8_t)py - 6);
            else if (nd == 2) draw_col((int8_t)px - 6);
            else draw_col((int8_t)px + 7);
            step_foot ^= 1;
            for (k = 2; k <= 16; k += 2) {
                set_cam(DX[nd] * (int8_t)k, DY[nd] * (int8_t)k);
                if (hop) hopy = k <= 8 ? k : 16 - k;
                player_draw(k <= 8); npcs_draw();
                if (k < 16) frame();
            }
            hopy = 0; px = tx; py = ty; set_cam(0, 0); player_draw(0); npcs_draw();
            arrive();
            MAPB();
            if (px < M.w && py < M.h && (M.mt[mt_at(px, py) * 9 + 8] & MT_LEDGE)) slide = 1;
        }
    }
}
