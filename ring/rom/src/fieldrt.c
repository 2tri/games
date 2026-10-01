// 걷는 화면: 지도·스크롤·걷기, 말 걸기·표지판·물건, 여관·상점, 길 막는 적(눈 마주치면 전투), 풀숲 야생, START 메뉴
// 지도 자료와 같은 11번 은행에 있음 (0번 은행이 꽉 차서). 다른 은행 자료는 BANKED 함수로만 다룬다.
#pragma bank 11
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"
#include "story.h"
#include "field.h"
#include "fieldrt.h"
#include "music.h"

static MapDef MD;
// 지금 지도의 작은 표들은 RAM 으로 (지도 자료는 13번 은행부터)
static Npc NPCS[8]; static Sign SIGNS[5]; static Item ITEMS[8]; static Trig TRIGS[6]; static Exit EXITS[8]; static uint8_t WILDS[24];
static int16_t camx, camy;
static uint8_t npx[10], npy[10];          // 사람 지금 자리 (길 막는 적은 걸어옴)
static const int8_t DX[4] = { 0, 0, -1, 1 }, DY[4] = { 1, -1, 0, 0 };   // 아래·위·왼쪽·오른쪽
static const palette_color_t OBJPAL[4] = { RGB(31, 31, 31), RGB(31, 31, 30), RGB(11, 11, 11), RGB(2, 2, 2) };
static const palette_color_t BGPAL[4] = { RGB(30, 30, 29), RGB(21, 21, 20), RGB(11, 11, 11), RGB(2, 2, 2) };
static const palette_color_t FLASHPAL[4] = { RGB(2, 2, 2), RGB(11, 11, 11), RGB(21, 21, 20), RGB(30, 30, 29) };
uint8_t ev_arg, warp_map = 255, warp_x, warp_y;

static uint8_t flag_get(uint8_t f) { return S.flags[f >> 3] & (1 << (f & 7)); }
static void flag_set(uint8_t f) { S.flags[f >> 3] |= 1 << (f & 7); }
#define ITEM_FLAG(m, i) ((m) * 16 + (i))

static uint8_t raw_at(int8_t x, int8_t y) {
    if (x < 0 || y < 0 || x >= (int8_t)MD.w || y >= (int8_t)MD.h) return MT_TREE0 + (x & 1) + 2 * (y & 1);
    return fget(MD.bank, MD.cells + (uint16_t)y * MD.w + x);
}
static uint8_t item_idx(int8_t x, int8_t y) { uint8_t i; for (i = 0; i < MD.ni; i++) if (MD.item[i].x == (uint8_t)x && MD.item[i].y == (uint8_t)y) return i; return 255; }
static uint8_t cell_at(int8_t x, int8_t y) {
    uint8_t c = raw_at(x, y), i;
    if (MTDEF[c][4] == MK_ITEM) { i = item_idx(x, y); if (i == 255 || flag_get(ITEM_FLAG(S.map, i))) c = MD.grass; }
    return c;
}
static uint8_t npc_at(int8_t x, int8_t y) { uint8_t i; for (i = 0; i < MD.nn; i++) if (npx[i] == (uint8_t)x && npy[i] == (uint8_t)y) return i; return 255; }
static uint8_t open_at(int8_t x, int8_t y) { uint8_t k = MTDEF[cell_at(x, y)][4]; return k == MK_WALK || k == MK_GRASS || k == MK_ITEM; }
static uint8_t passable(int8_t x, int8_t y) { return open_at(x, y) && npc_at(x, y) == 255; }
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

#define PLAYER_TILE 220   // VRAM 1번 칸 220~251 (0~219 는 창 레이어 글상자)
#define NPC_TILE 200      // VRAM 0번 칸 200~ (필드 타일은 0~)
#define EXCL_TILE 204
#define SAM_TILE 208       // VRAM 0번 칸 208~239: 뒤따라 걷는 샘
// ── 그림(OBJ): 8×16 두 장이 16×16 한 명. 주인공 0·1번, 사람 2번부터, 느낌표 38·39번 ──
static void spr16(uint8_t k, uint8_t tile, int16_t sx, int16_t sy) {
    uint8_t prop = tile >= PLAYER_TILE ? 0x08 : 0x00;               // 주인공은 VRAM 1번 칸, 사람·느낌표는 0번 칸
    if (sx < -16 || sx > 168 || sy < -16 || sy > 160) { move_sprite(k, 0, 0); move_sprite(k + 1, 0, 0); return; }
    set_sprite_tile(k, tile); set_sprite_tile(k + 1, tile + 2);
    set_sprite_prop(k, prop); set_sprite_prop(k + 1, prop);
    move_sprite(k, (uint8_t)(sx + 8), (uint8_t)(sy + 16)); move_sprite(k + 1, (uint8_t)(sx + 16), (uint8_t)(sy + 16));
}

static int8_t nofs_i = -1, nofs_x, nofs_y;   // 걸어오는 사람의 칸 사이 위치
static void draw_player(uint8_t step) { spr16(0, PLAYER_TILE + (S.dir * 2 + step) * 4, 64, 60); }
// 샘: 프로도가 있던 칸을 따라 걷는다 (포켓몬 금은 리메이크의 따라오는 포켓몬처럼)
static int8_t fx, fy; static uint8_t fdir;
static void draw_sam(uint8_t step, int8_t ox, int8_t oy) {
    if (fx == (int8_t)S.x && fy == (int8_t)S.y) { move_sprite(36, 0, 0); move_sprite(37, 0, 0); return; }
    spr16(36, SAM_TILE + (fdir * 2 + step) * 4, (int16_t)fx * 16 - camx + ox, (int16_t)fy * 16 - camy - 4 + oy);
}
static void draw_npcs(void) {
    uint8_t i; int16_t ox, oy;
    for (i = 0; i < MD.nn && i < 8; i++) {
        ox = (int8_t)i == nofs_i ? nofs_x : 0; oy = (int8_t)i == nofs_i ? nofs_y : 0;
        spr16(2 + i * 2, NPC_TILE, (int16_t)npx[i] * 16 - camx + ox, (int16_t)npy[i] * 16 - camy - 4 + oy);
    }
}
static void set_cam(int8_t ox, int8_t oy) {
    camx = (int16_t)S.x * 16 - 64 + ox; camy = (int16_t)S.y * 16 - 64 + oy;
    move_bkg((uint8_t)camx, (uint8_t)camy);
}

void field_enter(void) BANKED {
    uint8_t r;
    DISPLAY_OFF;
    field_mode = 1;
    memcpy(&MD, &MAPS[S.map], sizeof MD);
    if (MD.nn > 8) MD.nn = 8; if (MD.ns > 5) MD.ns = 5; if (MD.ni > 8) MD.ni = 8; if (MD.nt > 6) MD.nt = 6; if (MD.ne > 8) MD.ne = 8; if (MD.nw > 8) MD.nw = 8;
    fcopy(NPCS, MD.bank, MD.npc, MD.nn * sizeof(Npc)); MD.npc = NPCS;
    fcopy(SIGNS, MD.bank, MD.sign, MD.ns * sizeof(Sign)); MD.sign = SIGNS;
    fcopy(ITEMS, MD.bank, MD.item, MD.ni * sizeof(Item)); MD.item = ITEMS;
    fcopy(TRIGS, MD.bank, MD.trig, MD.nt * sizeof(Trig)); MD.trig = TRIGS;
    fcopy(EXITS, MD.bank, MD.exit, MD.ne * sizeof(Exit)); MD.exit = EXITS;
    fcopy(WILDS, MD.bank, MD.wild, MD.nw * 3); MD.wild = WILDS;
    for (r = 0; r < MD.nn; r++) { npx[r] = MD.npc[r].x; npy[r] = MD.npc[r].y; }
    nofs_i = -1;
    VBK_REG = 0; set_bkg_data(0, FT_N, FT_TILES);
    VBK_REG = 1; set_sprite_data(PLAYER_TILE, 32, PLAYER_SPR); VBK_REG = 0; set_sprite_data(NPC_TILE, 4, NPC_SPR); set_sprite_data(EXCL_TILE, 4, EXCL_SPR); set_sprite_data(SAM_TILE, 32, SAM_SPR);
    if (_cpu == CGB_TYPE) { set_bkg_palette(0, 1, BGPAL); set_sprite_palette(0, 1, OBJPAL); }
    OBP0_REG = 0xE4;
    win_layout(0, 0);
    HIDE_WIN;
    SPRITES_8x16; SHOW_SPRITES;
    for (r = 0; r < 40; r++) move_sprite(r, 0, 0);
    fx = (int8_t)S.x - DX[S.dir]; fy = (int8_t)S.y - DY[S.dir]; fdir = S.dir;
    if (!open_at(fx, fy) || npc_at(fx, fy) != 255) { fx = S.x; fy = S.y; }
    render_all(); set_cam(0, 0); draw_npcs(); draw_sam(0, 0, 0); draw_player(0);
    DISPLAY_ON;
    {   // 지역 곡: 샤이어 · 묵은숲 · 브리 · 황야 · 깊은골 · 홀린 · 모리아
        static const uint8_t MAPMUS[] = { MUS_SHIRE, MUS_STORY1, MUS_TITLE, MUS_STORY1, MUS_END, MUS_STORY2, MUS_BOSS };
        music_play(S.map < sizeof MAPMUS ? MAPMUS[S.map] : MUS_STORY1);
    }
}
static void hide_below(uint8_t top) {   // 글상자·고르기 상자에 겹치는 사람 그림은 잠시 숨김
    uint8_t i;
    for (i = 2; i < 18; i += 2) if (shadow_OAM[i].y >= top + 16 - 8) { shadow_OAM[i].y = 0; shadow_OAM[i + 1].y = 0; }
    if (shadow_OAM[36].y >= top + 16 - 8) { shadow_OAM[36].y = 0; shadow_OAM[37].y = 0; }
}
static void ftalk(const char *t);
static void talk(const char *t) {
    hide_below(96);
    SHOW_WIN; say(t); HIDE_WIN; draw_npcs(); draw_sam(0, 0, 0);
}
static void ftalk(const char *t) { hide_below(96); SHOW_WIN; say_far(MD.bank, t); HIDE_WIN; draw_npcs(); draw_sam(0, 0, 0); }
static void beep(uint8_t hi) { NR52_REG = 0x80; NR10_REG = 0; NR11_REG = 0x80; NR12_REG = 0xA2; NR13_REG = hi; NR14_REG = 0x87; }
static void encounter_fx(void) {   // 띠리링: 화면 세 번 번쩍 + 소리
    uint8_t i;
    NR52_REG = 0x80; NR10_REG = 0x16; NR11_REG = 0x80; NR12_REG = 0xF3; NR13_REG = 0x00; NR14_REG = 0x87;
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
    {   // 샘은 프로도가 있던 칸으로
        int8_t dx = (int8_t)S.x - fx, dy = (int8_t)S.y - fy;
        uint8_t moving = (dx || dy);
        if (moving) fdir = dy > 0 ? 0 : dy < 0 ? 1 : dx < 0 ? 2 : 3;
        for (i = 1; i <= 8; i++) {
            set_cam(DX[d] * i * 2, DY[d] * i * 2);
            draw_npcs(); draw_player(i >= 2 && i <= 6);
            if (moving) draw_sam(i >= 2 && i <= 6, DX[fdir] * i * 2, DY[fdir] * i * 2); else draw_sam(0, 0, 0);
            wait_vbl_done();
        }
    }
    fx = S.x; fy = S.y;
    S.x = nx; S.y = ny; set_cam(0, 0); draw_npcs(); draw_sam(0, 0, 0); draw_player(0);
}

// ── 전투 (야생·길 막는 적) 뒤 처리: 지면 마지막 쉼터 → 지도 처음 자리 ──
static uint8_t fight(uint8_t foe, uint8_t noRun) {
    uint8_t r = battle(foe, noRun, 0);
    if (r == R_WIN) { S.money += foe_lv(foe) * 4; }
    if (r == R_LOSE) { lose(); S.x = MD.sx; S.y = MD.sy; S.dir = MD.sdir; }
    field_enter();
    return r;
}
// ── 여관: 쉬어 가면 모두 회복 + 기록 ──
static const char * const YESNO[] = { "쉬어 간다", "그냥 간다" };
static void inn(const char *t) {
    uint8_t c;
    ftalk(t);
    hide_below(48); move_sprite(0, 0, 0); move_sprite(1, 0, 0); SHOW_WIN; c = choose(0, YESNO, 2, 1); draw_npcs(); draw_player(0);
    if (c == 0) { healAll(); save(); beep(0xE0); talk("푹 쉬었다! 일행 모두 기운을 되찾았다. (기록했다)"); }
}
// ── 상점: 은화로 렘바스·약초 ──
static const char * const SHOP[] = { "렘바스 40은화", "약초 20은화" };
static void shop(const char *t) {
    uint8_t c;
    ftalk(t);
    for (;;) {
        sb_clear(); sb_add("가진 은화 "); sb_num(S.money, 0); sb_add(". 무엇을 살까? B는 그만");
        hide_below(48); move_sprite(0, 0, 0); move_sprite(1, 0, 0); SHOW_WIN; c = choose(SB, SHOP, 2, 2); draw_npcs(); draw_player(0);
        if (c == 2) break;
        if (S.money < (c ? 20 : 40)) { talk("은화가 모자라다."); continue; }
        S.money -= c ? 20 : 40;
        if (c) { S.herb++; talk("약초를 샀다!"); } else { S.lembas++; talk("렘바스를 샀다!"); }
    }
}
// ── 길 막는 적: 바라보는 방향 4칸 안에 주인공이 보이면 걸어와서 싸움 ──
static uint8_t trainer_check(void) {
    uint8_t i, k, d; int8_t x, y;
    for (i = 0; i < MD.nn; i++) {
        const Npc *n = &MD.npc[i];
        if (n->kind != NK_TRAINER || flag_get(n->flag)) continue;
        d = n->dir; x = npx[i]; y = npy[i];
        for (k = 1; k <= 4; k++) {
            x += DX[d]; y += DY[d];
            if (x == (int8_t)S.x && y == (int8_t)S.y) break;
            if (!open_at(x, y) || npc_at(x, y) != 255) { k = 9; break; }
        }
        if (k > 4) continue;
        // 알아챘다! 느낌표 → 걸어와서 → 대사 → 전투
        beep(0xC0);
        spr16(38, EXCL_TILE, (int16_t)npx[i] * 16 - camx, (int16_t)npy[i] * 16 - camy - 20);
        wait_frames(30); move_sprite(38, 0, 0); move_sprite(39, 0, 0);
        while (!((int8_t)npx[i] + DX[d] == (int8_t)S.x && (int8_t)npy[i] + DY[d] == (int8_t)S.y)) {
            uint8_t f;
            nofs_i = i;
            for (f = 1; f <= 8; f++) { nofs_x = DX[d] * f * 2; nofs_y = DY[d] * f * 2; draw_npcs(); wait_vbl_done(); }
            npx[i] += DX[d]; npy[i] += DY[d]; nofs_i = -1; draw_npcs();
        }
        S.dir = d ^ 1; draw_player(0);           // 주인공이 그쪽을 봄
        ftalk(n->text);
        if (fight(n->arg, 1) == R_WIN) {
            flag_set(n->flag); S.money += n->arg2;
            sb_clear(); sb_add("은화를 "); sb_num(n->arg2, 0); sb_add(" 받았다!"); talk(SB);
            if (n->text2) ftalk(n->text2);
        }
        return 1;
    }
    return 0;
}
// 한 걸음 뒤: 물건·사건·길 막는 적·풀숲. EV_TRIG 이면 이야기 단계로
static uint8_t after_step(void) {
    uint8_t i, c = raw_at(S.x, S.y);
    if (MTDEF[c][4] == MK_ITEM && (i = item_idx(S.x, S.y)) != 255 && !flag_get(ITEM_FLAG(S.map, i))) {
        flag_set(ITEM_FLAG(S.map, i)); draw_mt(S.x, S.y);
        if (MD.item[i].kind == 0) { S.herb++; talk("약초를 주웠다! 가방에 넣었다."); } else { S.lembas++; talk("렘바스를 주웠다! 가방에 넣었다."); }
    }
    for (i = 0; i < MD.ne; i++) {   // 출구: 다른 지역으로 (아직 이야기가 거기까지 안 갔으면 막힘)
        const Exit *e = &MD.exit[i];
        if (S.x != e->x || S.y != e->y) continue;
        if (S.step < e->need) {
            talk("아직 이쪽으로 갈 때가 아니다.");
            S.x -= DX[S.dir]; S.y -= DY[S.dir]; render_all(); set_cam(0, 0); draw_npcs(); draw_player(0);
            return EV_NONE;
        }
        S.map = e->map; S.x = e->tx; S.y = e->ty; field_enter();
        return EV_NONE;
    }
    for (i = 0; i < MD.nt; i++) {
        const Trig *t = &MD.trig[i];
        if (S.x >= t->x && S.x < t->x + t->w && S.y >= t->y && S.y < t->y + t->h && S.step <= t->step) {
            ev_arg = t->step;
            if (t->wmap != 255) { warp_map = t->wmap; warp_x = t->wx; warp_y = t->wy; } else warp_map = 255;
            return EV_TRIG;
        }
    }
    if (trainer_check()) return EV_NONE;
    if (MTDEF[cell_at(S.x, S.y)][4] == MK_GRASS && rnd100() < MD.rate) {
        const uint8_t *w = MD.wild + (rnd() % MD.nw) * 3;   // 적, 최저·최고 레벨
        wild_lv = w[1] + rnd() % (w[2] - w[1] + 1);
        encounter_fx(); fight(w[0], 0); wild_lv = 0;
    }
    return EV_NONE;
}
static const char * const SAMLINE[] = {
    "샘: 한 발짝만 더 가면 제가 가 본 가장 먼 곳이에요, 나리.",
    "샘: 이 숲은 기분이 나빠요. 나무들이 우릴 쳐다보는 것 같아요.",
    "샘: 여관 맥주가 꽤 괜찮대요. 한잔만 하고 가요, 나리.",
    "샘: 저 기사들… 우릴 쫓아오는 걸까요? 제가 꼭 붙어 있을게요.",
    "샘: 요정들을 실컷 봤어요! 이제 죽어도 여한이 없어요. 아, 아니 죽으면 안 되죠.",
    "샘: 눈이 이렇게 많이 오다니. 샤이어에선 상상도 못 했어요.",
    "샘: 여긴 너무 어두워요… 나리 곁에서 떨어지지 않을게요.",
};
static void interact(void) {
    int8_t fx2 = (int8_t)S.x + DX[S.dir], fy2 = (int8_t)S.y + DY[S.dir];
    uint8_t i = npc_at(fx2, fy2);
    if (fx2 == fx && fy2 == fy) { talk(SAMLINE[S.map < 7 ? S.map : 6]); return; }
    if (i != 255) {
        const Npc *n = &MD.npc[i];
        if (n->kind == NK_INN) inn(n->text);
        else if (n->kind == NK_SHOP) shop(n->text);
        else if (n->kind == NK_TRAINER) ftalk(flag_get(n->flag) && n->text2 ? n->text2 : n->text);
        else ftalk(n->text);
        return;
    }
    if (MTDEF[cell_at(fx2, fy2)][4] == MK_SIGN) for (i = 0; i < MD.ns; i++) if (MD.sign[i].x == (uint8_t)fx2 && MD.sign[i].y == (uint8_t)fy2) { ftalk(MD.sign[i].text); return; }
}
uint8_t field_loop(void) BANKED {
    uint8_t k, h, d, ev;
    for (;;) {
        frame();
        k = key_poll(); h = key_held();
        if (k == K_A) { interact(); continue; }
        if (k == K_START) { menu_open(); field_enter(); continue; }
        d = (h & J_DOWN) ? 0 : (h & J_UP) ? 1 : (h & J_LEFT) ? 2 : (h & J_RIGHT) ? 3 : 255;
        if (d == 255) continue;
        if (S.dir != d) {
            S.dir = d; draw_player(0);
            if ((int8_t)S.x + DX[d] == fx && (int8_t)S.y + DY[d] == fy) { wait_frames(6); continue; }   // 샘 쪽은 먼저 돌아보기만
        }
        if (!passable((int8_t)S.x + DX[d], (int8_t)S.y + DY[d])) continue;
        walk(d);
        ev = after_step();
        if (ev) return ev;
    }
}
void field_start_pos(void) BANKED { S.x = MAPS[S.map].sx; S.y = MAPS[S.map].sy; S.dir = MAPS[S.map].sdir; }

// ── START 메뉴 (그림 화면): 동료 · 가방 · 기록 ──
static const char * const MENU[] = { "동료", "가방", "기록", "닫기" };
static char lines[5][28];
static uint8_t nl;
static void menuScene(void) {
    uint8_t i;
    rect(0, 0, 160, 144, 0); box(0, 0, 160, 96);
    text("일행", 10, 6, 3);
    for (i = 0; i < nl; i++) text(lines[i], 10, 20 + i * 14, 3);
    box(0, 96, 160, 48);
}
static void load_lines(void) { uint8_t i; nl = S.np; for (i = 0; i < nl; i++) { party_line(i); strncpy(lines[i], SB, 27); lines[i][27] = 0; } }
void menu_open(void) BANKED {
    uint8_t c, i, k; const char *opts[6];
    for (;;) {
        load_lines(); set_scene(menuScene); menuScene();
        sb_clear(); sb_add("은화 "); sb_num(S.money, 0); sb_add(" · 그림자 "); sb_num(S.shadow, 0);
        c = choose(SB, MENU, 4, 3);
        if (c == 3) return;
        if (c == 2) { save(); say("여기까지 기록했다."); continue; }
        if (c == 0) {   // 동료: 고른 사람을 앞장 세우기 / 능력 보기
            for (i = 0; i < nl; i++) opts[i] = lines[i]; opts[nl] = "돌아가기";
            k = choose("누구를?", opts, nl + 1, nl);
            if (k >= nl) continue;
            party_info(k); say(SB);
            if (S.party[k] != S.hero) {
                static const char * const LEAD[] = { "앞장 세운다", "그대로" };
                if (choose("앞장 세울까?", LEAD, 2, 1) == 0) {
                    if (party_hp(k) <= 0) say("쓰러져 있어서 앞장설 수 없다.");
                    else { swapTo(S.party[k]); say("앞장을 바꿨다."); }
                }
            }
            continue;
        }
        // 가방: 렘바스·약초를 앞장선 사람에게
        {
            static char b0[24], b1[24];
            sb_clear(); sb_add("렘바스 ×"); sb_num(S.lembas, 0); strcpy(b0, SB);
            sb_clear(); sb_add("약초 ×"); sb_num(S.herb, 0); strcpy(b1, SB);
            opts[0] = b0; opts[1] = b1; opts[2] = "돌아가기";
            k = choose("무엇을 쓸까?", opts, 3, 2);
            if (k == 0) { if (!S.lembas) say("렘바스가 없다."); else { S.lembas--; heal_lead(20); say("렘바스를 먹었다. 체력이 회복됐다."); } }
            if (k == 1) { if (!S.herb) say("약초가 없다."); else { S.herb--; heal_lead(10); say("약초를 씹었다. 몸이 조금 가뿐하다."); } }
        }
    }
}
