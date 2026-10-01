// 디지몬 GBC — 제목 화면, 아이 고르기, START 메뉴, 디지몬 목록·능력, 가방, 도감, 주인공 정보, 저장
#pragma bank 2
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"

extern uint8_t print_max;

// ───────── 제목 ─────────
uint8_t title_screen(void) BANKED {
    static uint8_t tm[360], ta[360], alt[N_TITLE_ALT * 4 + 1], keep[N_TITLE_ALT * 2 + 1];
    uint16_t i; uint8_t sel, blink = 0;
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(0);
    music_play(SONG_TITLE);
    far_vram(0, 80, N_TITLE0, MISC_BANK, title_tiles);
    if (N_TITLE1) far_vram(1, 0, N_TITLE1, MISC_BANK, title_tiles1);
    far_copy(tm, MISC_BANK, title_map, 360); far_copy(ta, MISC_BANK, title_attr, 360);
    far_copy(alt, MISC_BANK, title_alt, N_TITLE_ALT * 4);
    for (i = 0; i < 18; i++) { VBK_REG = 1; set_bkg_tiles(0, i, 20, 1, ta + i * 20); VBK_REG = 0; set_bkg_tiles(0, i, 20, 1, tm + i * 20); }
    for (i = 0; i < N_TITLE_PAL * 4; i++) bgpal[4 + i] = TITLE_PAL[i];
    fade_lv = 0; pal_apply();
    DISPLAY_ON;
    for (;;) {
        frame();
        if (joy_new & (J_START | J_A)) break;
        if ((frames & 31) == 0) {          // START 글씨 깜빡임: 글씨 없는 칸과 바꿔 끼움
            blink ^= 1;
            for (i = 0; i < N_TITLE_ALT; i++) {
                uint16_t pos = alt[i * 4] | (alt[i * 4 + 1] << 8);
                if (blink) put_tile(TGT_BG, pos % 20, pos / 20, alt[i * 4 + 2], alt[i * 4 + 3]);
                else put_tile(TGT_BG, pos % 20, pos / 20, tm[pos], ta[pos]);
            }
        }
    }
    for (i = 0; i < N_TITLE_ALT; i++) { uint16_t pos = alt[i * 4] | (alt[i * 4 + 1] << 8); put_tile(TGT_BG, pos % 20, pos / 20, tm[pos], ta[pos]); }
    if (!save_exists()) return 0;
    {
        static const uint16_t items[2] = { S_T_CONT, S_T_NEW };
        ui_open(11);
        sel = choose(TGT_WIN, 5, 11, 11, items, 2, 0, 0);
        ui_close();
        if (sel == 0) return 1;
        if (!ask(S_T_OVER)) { tb_close(); return title_screen(); }
        tb_close();
    }
    return 0;
}

// ───────── 아이 고르기 ─────────
// ───────── 주인공 고르기: 4명이 나란히 서 있고, 고른 아이는 제자리 걸음 · 아래에 파트너 그림·문장·소개 ─────────
#define KP_X(i) (20 + (i) * 36)          // 화면 x (아이 왼쪽)
#define KP_Y 40                         // 머리 위 (16×32)
static void kp_sprite(uint8_t i, uint8_t fr) {
    uint8_t q, t0 = i * 16 + fr * 8;
    for (q = 0; q < 4; q++) {           // 0·1 아래 반, 2·3 위 반
        set_sprite_tile(i * 4 + q, t0 + ((q & 2) ? 0 : 4) + ((q & 1) ? 2 : 0));
        set_sprite_prop(i * 4 + q, 0x08 | i);
        move_sprite(i * 4 + q, KP_X(i) + 8 + (q & 1) * 8, KP_Y + 16 + ((q & 2) ? 0 : 16));
    }
}
static void kp_info(uint8_t k, uint8_t m) {
    pool_release(m);
    fill_tiles(TGT_BG, 0, 11, 20, 7, T_BLANK, 0);
    pic_load(SPECIES[KID_PARTNER[k]].front, 1, 128, 4); pic_place(0, 11, 7, 7, 128, 4 | 0x08);
    draw_frame(TGT_BG, 7, 11, 13, 7, 1);
    var_sp[0] = KID_PARTNER[k]; print_at(TGT_BG, 9, 12, S_NAME_S0);
    print_at(TGT_BG, 9, 14, KID_CRESTS[k]);
    print_at(TGT_BG, 9, 16, KID_DESC[k]);
    pal_apply();
}
uint8_t kid_pick(void) BANKED {
    uint8_t sel = G.kid, i, m, n, fr = 0;
    for (;;) {
        DISPLAY_OFF;
        screen_clear(); scene = SCENE_OTHER; pool_reset(1);
        draw_frame(TGT_BG, 0, 0, 20, 4, 0);
        print_at(TGT_BG, 2, 1, S_KP_Q);
        for (i = 0; i < N_KIDS; i++) {          // 아이 그림 (앞모습 두 장씩) · 팔레트 · 이름
            far_sprite(1, i * 16, 16, MISC_BANK, kid_spr + (uint16_t)i * 768);
            for (n = 0; n < 4; n++) obpal[i * 4 + n] = KID_PAL[i * 4 + n];
            kp_sprite(i, 0);
            print_at(TGT_BG, (KP_X(i) + 8) / 8 - 1, 9, KID_NAME[i]);
        }
        DISPLAY_ON;
        m = pool_mark();
        kp_info(sel, m);
        for (;;) {
            for (i = 0; i < N_KIDS; i++) draw_cursor(TGT_BG, (KP_X(i) + 8) / 8 - 2, 9, i == sel);
            for (;;) {
                frame();
                if ((frames & 15) == 0) { fr ^= 1; kp_sprite(sel, fr); }
                if (joy_new & (J_LEFT | J_RIGHT | J_A)) break;
            }
            if (joy_new & J_A) break;
            kp_sprite(sel, 0);
            if (joy_new & J_LEFT) sel = sel ? sel - 1 : N_KIDS - 1;
            else sel = (sel + 1 == N_KIDS) ? 0 : sel + 1;
            kp_info(sel, m);
        }
        G.kid = sel;
        if (ask(S_KP_OK)) { tb_close(); hide_sprites(); return sel; }
        tb_close();
    }
}

// ───────── 디지몬 목록 ─────────
static void party_draw(void) {
    uint8_t i, row;
    for (i = 0; i < G.nparty; i++) {
        mon_t *mm = &G.party[i]; row = i * 2;
        if (mm->egg) { print_at(TGT_BG, 2, row, S_EGG); continue; }
        var_sp[0] = mm->sp; print_at(TGT_BG, 2, row, S_NAME_S0);
        print_lv(TGT_BG, 14, row, mm->lv);
        hp_bar(TGT_BG, 10, row + 1, mm->hp, mon_maxhp(mm), hp_level(mm->hp, mon_maxhp(mm)) == 0 ? 1 : hp_level(mm->hp, mon_maxhp(mm)) == 1 ? 2 : 6);
    }
}
static void party_bg(void) {
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    set_hp_color(1, 0); set_hp_color(2, 1); set_hp_color(6, 2);
    party_draw();
    DISPLAY_ON; pal_apply();
}
static void status_screen(uint8_t slot);
uint8_t party_screen(uint8_t mode) BANKED {
    static const uint16_t sub[3] = { S_P_MENU1, S_P_MENU2, S_P_MENU3 };
    uint8_t sel = 0, i, r;
    uint16_t prompt = mode == 1 ? S_P_SEND : mode == 2 ? S_P_USE : mode == 3 ? S_BOX_PICK : S_P_PICK;
    if (!G.nparty) { say(S_NO_MON); tb_close(); return 0xFF; }
    party_bg();
    for (;;) {
        say_nowait(prompt);
        for (;;) {
            for (i = 0; i < G.nparty; i++) draw_cursor(TGT_BG, 1, i * 2, i == sel);
            frame();
            if (joy_new & J_UP) sel = sel ? sel - 1 : G.nparty - 1;
            if (joy_new & J_DOWN) sel = (sel + 1 == G.nparty) ? 0 : sel + 1;
            if (joy_new & (J_A | J_B)) break;
        }
        if (joy_new & J_B) { tb_close(); return 0xFF; }
        if (mode) { tb_close(); return sel; }
        if (G.party[sel].egg) { say(S_EGG_INFO); continue; }
        tb_close();
        ui_open(10);
        r = choose(TGT_WIN, 9, 10, 11, sub, 3, 0, 1);
        ui_close();
        if (r == 0) { status_screen(sel); party_bg(); }
        if (r == 1 && G.nparty > 1) {
            uint8_t t = sel;
            say_nowait(S_P_MOVE);
            for (;;) {
                for (i = 0; i < G.nparty; i++) draw_cursor(TGT_BG, 1, i * 2, i == t);
                frame();
                if (joy_new & J_UP) t = t ? t - 1 : G.nparty - 1;
                if (joy_new & J_DOWN) t = (t + 1 == G.nparty) ? 0 : t + 1;
                if (joy_new & (J_A | J_B)) break;
            }
            if ((joy_new & J_A) && t != sel) { mon_t tmp = G.party[sel]; G.party[sel] = G.party[t]; G.party[t] = tmp; sel = t; }
            tb_close(); party_bg();
        }
    }
}

// ───────── 능력 보기 ─────────
static void status_screen(uint8_t slot) {
    mon_t *m = &G.party[slot]; const species_t *s = &SPECIES[m->sp];
    uint8_t page = 0, i;
    for (;;) {
        DISPLAY_OFF;
        screen_clear(); scene = SCENE_OTHER; pool_reset(1);
        pic_load(s->front, 1, 128, 4); pic_place(0, 0, 7, 7, 128, 4 | 0x08);
        var_sp[0] = m->sp; print_at(TGT_BG, 1, 8, S_NAME_S0);
        print_lv(TGT_BG, 1, 10, m->lv);
        print_at(TGT_BG, 1, 12, s->grade);
        if (!page) {
            static const uint16_t BH[6] = { S_BOND0, S_BOND1, S_BOND2, S_BOND3, S_BOND4, S_BOND5 };
            print_at(TGT_BG, 1, 14, S_ST_BOND); print_at(TGT_BG, 1, 16, BH[m->bond >= 250 ? 5 : m->bond / 50]);
            set_hp_color(1, hp_level(m->hp, mon_maxhp(m)));
            hp_bar(TGT_BG, 10, 0, m->hp, mon_maxhp(m), 1);
            print_num(TGT_BG, 12, 1, m->hp, 3); put_tile(TGT_BG, 15, 1, T_SLASH, 0x80); print_num(TGT_BG, 16, 1, mon_maxhp(m), 3);
            print_at(TGT_BG, 9, 2, S_ST_ATTR); print_at(TGT_BG, 13, 2, ATTR_NAME[s->attr]);
            print_at(TGT_BG, 9, 4, S_ST_TYPE); print_at(TGT_BG, 13, 4, s->type);
            print_at(TGT_BG, 9, 6, S_ST_ATK); print_num(TGT_BG, 16, 7, mon_stat(m, 1), 3);
            print_at(TGT_BG, 9, 8, S_ST_DEF); print_num(TGT_BG, 16, 9, mon_stat(m, 2), 3);
            print_at(TGT_BG, 9, 10, S_ST_SPD); print_num(TGT_BG, 16, 11, mon_stat(m, 3), 3);
            print_at(TGT_BG, 9, 13, S_ST_NEXT);
            print_num(TGT_BG, 13, 15, m->lv >= 100 ? 0 : (uint16_t)(exp_at(m->lv + 1) - m->exp), 6);
        } else {
            print_at(TGT_BG, 9, 0, S_ST_MOVES);
            for (i = 0; i < 4; i++) {
                if (m->mv[i] == 0xFF) continue;
                var_mv = m->mv[i]; print_max = 10; print_at(TGT_BG, 9, 2 + i * 4, S_NAME_M0); print_max = 255;
                print_at(TGT_BG, 10, 4 + i * 4, MOVES[m->mv[i]].kind ? S_K_SIG : S_K_BASIC);
                print_num(TGT_BG, 14, 5 + i * 4, m->pp[i], 2); put_tile(TGT_BG, 16, 5 + i * 4, T_SLASH, 0x80); print_num(TGT_BG, 17, 5 + i * 4, MOVES[m->mv[i]].pp, 2);
            }
        }
        DISPLAY_ON; pal_apply();
        for (;;) { frame(); if (joy_new & (J_LEFT | J_RIGHT | J_A | J_B)) break; }
        if (joy_new & (J_LEFT | J_RIGHT)) { page ^= 1; continue; }
        return;
    }
}

// ───────── 기술 익히기 (포켓몬처럼: 4개가 꽉 차면 무엇을 잊을지 고름) ─────────
static uint8_t forget_pick(mon_t *m) {
    uint8_t i, sel = 0, mk = pool_mark();
    say_nowait(S_FORGET_WHICH);
    ui_open(1); tb_shown = 0; win_top = 1; tb_place();
    draw_frame(TGT_WIN, 4, 1, 16, 10, 0);
    for (i = 0; i < 4; i++) { var_mv = m->mv[i]; print_at(TGT_WIN, 6, 2 + i * 2, S_NAME_M0); }
    for (;;) {
        for (i = 0; i < 4; i++) draw_cursor(TGT_WIN, 5, 2 + i * 2, i == sel);
        frame();
        if (joy_new & J_UP) sel = sel ? sel - 1 : 3;
        if (joy_new & J_DOWN) sel = sel == 3 ? 0 : sel + 1;
        if (joy_new & J_A) { sfx_play(SFX_SELECT); break; }
        if (joy_new & J_B) { sel = 0xFF; break; }
    }
    pool_release(mk);
    win_top = 12; move_win(7, 96); tb_shown = 0; tb_open();
    return sel;
}
uint8_t learn_ui(mon_t *m, uint8_t mv) BANKED {
    uint8_t j;
    var_sp[0] = m->sp; var_mv = mv;
    for (j = 0; j < 4; j++) if (m->mv[j] == 0xFF) { m->mv[j] = mv; m->pp[j] = MOVES[mv].pp; say(S_LEARN); return 1; }
    for (;;) {
        var_sp[0] = m->sp; var_mv = mv; say(S_LEARN_FULL);
        if (ask(S_LEARN_Q)) {
            j = forget_pick(m);
            if (j != 0xFF) {
                var_sp[0] = m->sp; var_mv = m->mv[j]; say(S_FORGOT);
                m->mv[j] = mv; m->pp[j] = MOVES[mv].pp;
                var_mv = mv; say(S_LEARN);
                return 1;
            }
        }
        var_mv = mv;
        if (ask(S_GIVEUP_Q)) { var_sp[0] = m->sp; say(S_DIDNT); return 0; }
    }
}

// ───────── 가방 ─────────
// 물건 종류 (IT_KIND): 0 회복 1 디지바이스 2·3 그물 4 고기 5 검은 톱니 6 이블 스파이럴
#define BAG_VIS 4
static void bag_rows(const uint8_t *list, uint8_t n, uint8_t top) {
    uint8_t i, k;
    fill_tiles(TGT_BG, 1, 2, 18, 9, T_BLANK, 0);
    for (i = 0; i < BAG_VIS; i++) {
        k = top + i;
        if (k > n) break;
        if (k == n) { print_at(TGT_BG, 2, 2 + i * 2, S_BAG_QUIT); break; }
        var_item = list[k]; print_at(TGT_BG, 2, 2 + i * 2, S_NAME_I0);
        if (IT_KIND[list[k]] != 1) print_num(TGT_BG, 16, 3 + i * 2, G.bag[list[k]], 2);   // 디지바이스는 개수 없음
    }
    put_tile(TGT_BG, 18, 1, top ? T_F_BMORE : T_BLANK, 0x80 | 0x40);       // 위로 더 있음 (뒤집은 ▼)
    put_tile(TGT_BG, 18, 10, top + BAG_VIS <= n ? T_F_BMORE : T_BLANK, 0x80);
}
uint8_t bag_screen(uint8_t inbattle) BANKED {
    uint8_t list[N_ITEMS + 1], n, i, sel = 0, top = 0, t, k;
    for (;;) {
        n = 0;
        for (i = 0; i < N_ITEMS; i++) if (G.bag[i]) list[n++] = i;
        DISPLAY_OFF;
        screen_clear(); scene = SCENE_OTHER; pool_reset(1);
        draw_frame(TGT_BG, 0, 0, 20, 12, 0);
        print_at(TGT_BG, 2, 0, S_BAG);
        if (sel > n) sel = n;
        if (sel < top) top = sel;
        if (sel >= top + BAG_VIS) top = sel - BAG_VIS + 1;
        bag_rows(list, n, top);
        DISPLAY_ON; pal_apply();
        for (;;) {
            for (i = 0; i < BAG_VIS; i++) draw_cursor(TGT_BG, 1, 2 + i * 2, top + i == sel);
            say_nowait(sel < n ? IT_DESC[list[sel]] : S_BAG_QUIT);
            for (;;) { frame(); if (joy_new & (J_UP | J_DOWN | J_A | J_B)) break; }
            if (joy_new & J_UP) sel = sel ? sel - 1 : n;
            else if (joy_new & J_DOWN) sel = sel >= n ? 0 : sel + 1;
            else break;
            if (sel < top || sel >= top + BAG_VIS) {
                top = sel < top ? sel : sel - BAG_VIS + 1;
                bag_rows(list, n, top);
            }
        }
        tb_close();
        if ((joy_new & J_B) || sel == n) return 0;
        t = list[sel]; k = IT_KIND[t];
        if (k >= 1 && k <= 3) {                 // 디지바이스·그물: 전투에서 포획 (전투 쪽에서 처리)
            if (inbattle) return 0x10 | t;
            say(S_CANTUSE); tb_close(); continue;
        }
        if (k >= 5) {                           // 진화 물건: 필드에서만
            uint8_t who;
            if (inbattle) { say(S_CANTUSE); tb_close(); continue; }
            who = party_screen(2);
            if (who == 0xFF) continue;
            var_item = t;
            if (item_evolve(who, k)) G.bag[t]--;
            continue;
        }
        if (IT_HEAL[t]) {
            uint8_t who = party_screen(2);
            if (who == 0xFF) continue;
            {
                mon_t *m = &G.party[who]; uint16_t mx = mon_maxhp(m), before = m->hp;
                if (m->egg || !m->hp || (m->hp >= mx && k != 4)) { say(S_USELESS); tb_close(); continue; }
                m->hp += IT_HEAL[t]; if (m->hp > mx) m->hp = mx;
                G.bag[t]--;
                var_sp[0] = m->sp; var_num[0] = m->hp - before;
                if (k == 4) { m->bond = m->bond > 240 ? 250 : m->bond + 10; say(S_MEAT); }       // 고기: 유대↑
                else say(S_HEALED);
                tb_close();
                if (inbattle) return 1;
            }
            continue;
        }
        say(S_CANTUSE); tb_close();
    }
}

// ───────── 상점 (프렌들리숍 오마주) ─────────
void shop_screen(void) BANKED {
    uint8_t list[N_ITEMS], n = 0, i, sel = 0, t;
    for (i = 0; i < N_ITEMS; i++) if (IT_PRICE[i]) list[n++] = i;
    for (;;) {
        DISPLAY_OFF;
        screen_clear(); scene = SCENE_OTHER; pool_reset(1);
        draw_frame(TGT_BG, 0, 0, 20, 14, 0);
        print_at(TGT_BG, 2, 0, S_SHOP_TITLE);
        for (i = 0; i < n; i++) {
            var_item = list[i]; print_at(TGT_BG, 2, 2 + i * 2, S_NAME_I0);
            print_num(TGT_BG, 14, 3 + i * 2, IT_PRICE[list[i]], 4);
        }
        print_at(TGT_BG, 2, 2 + n * 2, S_SHOP_QUIT);
        draw_frame(TGT_BG, 0, 14, 20, 4, 1);
        print_at(TGT_BG, 2, 15, S_SHOP_BITS); print_num(TGT_BG, 13, 16, G.bits, 5);
        DISPLAY_ON; pal_apply();
        if (sel > n) sel = n;
        for (;;) {
            for (i = 0; i <= n; i++) draw_cursor(TGT_BG, 1, 2 + i * 2, i == sel);
            frame();
            if (joy_new & J_UP) sel = sel ? sel - 1 : n;
            else if (joy_new & J_DOWN) sel = sel >= n ? 0 : sel + 1;
            else if (joy_new & (J_A | J_B)) break;
        }
        if ((joy_new & J_B) || sel == n) return;
        t = list[sel]; var_item = t; var_num[0] = IT_PRICE[t];
        say_nowait(IT_DESC[t]); wait_frames(30);
        if (ask(S_SHOP_ASK)) {
            if (G.bits < IT_PRICE[t]) say(S_SHOP_POOR);
            else if (G.bag[t] >= 99) say(S_SHOP_FULL);
            else { G.bits -= IT_PRICE[t]; G.bag[t]++; var_item = t; say(S_SHOP_THX); }
        }
        tb_close();
    }
}

// ───────── 디지몬 보관함 (회복 센터 PC) ─────────
static void box_list(uint8_t top) {
    uint8_t i, n;
    fill_tiles(TGT_BG, 1, 2, 18, 14, T_BLANK, 0);
    for (i = 0; i < 7 && top + i < G.nbox; i++) {
        mon_t *mm = &G.box[top + i];
        n = top + i;
        if (mm->egg) print_at(TGT_BG, 3, 2 + i * 2, S_EGG);
        else { var_sp[0] = mm->sp; print_at(TGT_BG, 3, 2 + i * 2, S_NAME_S0); print_lv(TGT_BG, 14, 2 + i * 2, mm->lv); }
        (void)n;
    }
    if (top + 7 >= G.nbox) print_at(TGT_BG, 3, 2 + (G.nbox - top) * 2, S_SHOP_QUIT);
}
static uint8_t box_pick(void) {       // 보관함에서 하나 고르기 → 번호, FF 그만
    uint8_t sel = 0, top = 0, i, m;
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    draw_frame(TGT_BG, 0, 0, 20, 18, 0);
    print_at(TGT_BG, 2, 0, S_BOX_TITLE);
    print_num(TGT_BG, 14, 1, G.nbox, 2); print_at(TGT_BG, 16, 0, S_BOX_N);
    m = pool_mark();
    box_list(0);
    DISPLAY_ON; pal_apply();
    for (;;) {
        for (i = 0; i < 7; i++) draw_cursor(TGT_BG, 2, 2 + i * 2, top + i == sel);
        frame();
        if (joy_new & J_B) return 0xFF;
        if (joy_new & J_A) return sel < G.nbox ? sel : 0xFF;
        if ((joy_new & J_UP) && sel) sel--;
        else if ((joy_new & J_DOWN) && sel < G.nbox) sel++;
        else continue;
        if (sel < top || sel >= top + 7) {
            top = sel < top ? sel : sel - 6;
            pool_release(m); box_list(top);
        }
    }
}
void box_screen(void) BANKED {
    static const uint16_t items[3] = { S_BOX_DEP, S_BOX_WD, S_SHOP_QUIT };
    uint8_t r, s, i;
    for (;;) {
        say_nowait(S_BOX_Q);
        ui_open(10);
        r = choose(TGT_WIN, 11, 10, 9, items, 3, 0, 2);
        ui_close();
        tb_close();
        if (r == 0) {                              // 맡기기
            if (G.nbox >= MAX_BOX) { say(S_BOX_FULL); tb_close(); continue; }
            if (G.nparty <= 1) { say(S_BOX_ONE); tb_close(); continue; }
            s = party_screen(3);
            if (s != 0xFF) {
                mon_t tmp = G.party[s];
                if (!tmp.egg && alive_count() <= 1 && tmp.hp) { field_restore(); say(S_BOX_ONE); tb_close(); continue; }
                G.box[G.nbox++] = tmp;
                for (i = s; i + 1 < G.nparty; i++) G.party[i] = G.party[i + 1];
                G.nparty--;
                field_restore(); var_sp[0] = tmp.sp; say(tmp.egg ? S_BOX_DID_E : S_BOX_DID); tb_close();
            } else field_restore();
        } else if (r == 1) {                       // 데려오기
            if (!G.nbox) { say(S_BOX_EMPTY); tb_close(); continue; }
            if (G.nparty >= 6) { say(S_PARTY_FULL); tb_close(); continue; }
            s = box_pick();
            field_restore();
            if (s != 0xFF) {
                mon_t tmp = G.box[s];
                for (i = s; i + 1 < G.nbox; i++) G.box[i] = G.box[i + 1];
                G.nbox--;
                G.party[G.nparty++] = tmp;
                var_sp[0] = tmp.sp; say(tmp.egg ? S_BOX_GOT_E : S_BOX_GOT); tb_close();
            }
        } else return;
    }
}

// ───────── 도감 ─────────
static uint8_t seen(uint8_t sp) { return (G.seen[sp >> 3] >> (sp & 7)) & 1; }
static uint8_t own(uint8_t sp) { return (G.own[sp >> 3] >> (sp & 7)) & 1; }
static void dex_entry(uint8_t sp) {
    const species_t *s = &SPECIES[sp]; uint8_t i;
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    pic_load(s->front, 1, 128, 4); pic_place(0, 0, 7, 7, 128, 4 | 0x08);
    var_sp[0] = sp; print_at(TGT_BG, 8, 0, S_NAME_S0);
    print_at(TGT_BG, 8, 2, s->type);
    print_at(TGT_BG, 8, 4, s->grade);
    print_at(TGT_BG, 8, 6, ATTR_NAME[s->attr]);
    print_at(TGT_BG, 1, 8, S_K_SIG);
    for (i = 0; i < 3; i++) if (s->sig[i] != 0xFF) { var_mv = s->sig[i]; print_at(TGT_BG, 2, 10 + i * 2, S_NAME_M0); }
    DISPLAY_ON; pal_apply();
    wait_press();
}
static void dex_screen(void) {
    uint8_t list[N_SPECIES], n = 0, i, sel = 0, top = 0, m;
    for (i = 0; i < N_SPECIES; i++) if (seen(i)) list[n++] = i;
    if (!n) { say(S_DEX_NONE); tb_close(); return; }
    for (;;) {
        DISPLAY_OFF;
        screen_clear(); scene = SCENE_OTHER; pool_reset(1);
        print_at(TGT_BG, 1, 0, S_DEX);
        print_at(TGT_BG, 9, 0, S_DEX_SEEN); print_num(TGT_BG, 12, 1, n, 3);
        DISPLAY_ON; pal_apply();
        m = pool_mark();
        for (;;) {
            pool_release(m);
            fill_tiles(TGT_BG, 0, 2, 20, 16, T_BLANK, 0);
            for (i = 0; i < 8 && top + i < n; i++) {
                uint8_t sp = list[top + i];
                print_num(TGT_BG, 2, 3 + i * 2, sp + 1, 3);
                if (own(sp)) { var_sp[0] = sp; print_at(TGT_BG, 6, 2 + i * 2, S_NAME_S0); }
                else print_at(TGT_BG, 6, 2 + i * 2, S_DEX_Q);
                draw_cursor(TGT_BG, 1, 2 + i * 2, top + i == sel);
            }
            for (;;) { frame(); if (joy_new & (J_UP | J_DOWN | J_A | J_B)) break; }
            if (joy_new & J_UP) { if (sel) sel--; if (sel < top) top = sel; }
            else if (joy_new & J_DOWN) { if (sel + 1 < n) sel++; if (sel >= top + 8) top = sel - 7; }
            else break;
        }
        if (joy_new & J_B) return;
        if (own(list[sel])) dex_entry(list[sel]);
    }
}

// ───────── 주인공 정보 ─────────
static void card_screen(void) {
    uint8_t i, n = 0; uint16_t mins;
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    draw_frame(TGT_BG, 0, 0, 20, 18, 0);
    print_at(TGT_BG, 2, 1, S_CARD_TITLE);
    print_at(TGT_BG, 2, 3, KID_NAME[G.kid]);
    for (i = 0; i < N_SPECIES; i++) if (own(i)) n++;
    print_at(TGT_BG, 2, 5, S_M_DEX); print_num(TGT_BG, 7, 6, n, 3);
    print_at(TGT_BG, 11, 5, S_CARD_BITS); print_num(TGT_BG, 14, 6, G.bits, 5);
    mins = (uint16_t)(G.time / 3600);
    print_at(TGT_BG, 2, 7, S_CARD_TIME); print_num(TGT_BG, 11, 8, mins / 60, 3); print_num(TGT_BG, 15, 8, mins % 60, 2);
    print_at(TGT_BG, 2, 10, S_CARD_CREST);
    for (i = 0; i < N_CRESTS; i++) if ((G.crests >> i) & 1) print_at(TGT_BG, 2 + (i & 3) * 4, 12 + (i >> 2) * 2, CREST_NAME[i]);
    DISPLAY_ON; pal_apply();
    wait_press();
}

// ───────── START 메뉴 ─────────
void start_menu(void) BANKED {
    static uint8_t last;
    uint16_t items[6];
    uint8_t sel;
    items[0] = S_M_DEX; items[1] = S_M_MON; items[2] = S_M_BAG; items[3] = KID_NAME[G.kid]; items[4] = S_M_SAVE; items[5] = S_M_CLOSE;
    for (;;) {
        pool_reset(0);
        ui_open(0);
        sel = choose(TGT_WIN, 11, 0, 9, items, 6, last, 1);
        ui_close();
        if (sel == 0xFF || sel == 5) return;
        last = sel;
        if (sel == 0) dex_screen();
        else if (sel == 1) party_screen(0);
        else if (sel == 2) bag_screen(0);
        else if (sel == 3) card_screen();
        else {
            if (ask(S_SAVE_Q)) { save_game(); say(S_SAVED); }
            tb_close();
            return;
        }
        field_restore();
    }
}
