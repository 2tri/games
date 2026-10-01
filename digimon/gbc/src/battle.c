// 디지몬 GBC — 전투 (금판 화면 배치), 진화, 디지타마 부화
#pragma bank 1
#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"

uint8_t bag_screen(uint8_t inbattle) BANKED;
extern uint8_t print_max;

mon_t foe;                       // 시험 도구가 읽음 (_foe)
static uint8_t me, kind, runs, lvup;
static int8_t sme, sfoe;          // 방어 단계
static uint8_t used;              // 싸운 디지몬 (비트)
static uint16_t dme, dfoe;        // 화면에 보이는 HP

#define FOE_T 128                 // 1번 VRAM: 상대 그림 128~176
#define ME_T 177                  // 내 그림 177~212

static void exp_bar(void) {
    mon_t *m = &G.party[me];
    uint32_t lo = exp_at(m->lv), hi = exp_at(m->lv + 1), cur = m->exp;
    uint8_t px = 0, j; int16_t k;
    if (m->lv < 100 && hi > lo) px = (uint8_t)(((cur - lo) * 48) / (hi - lo));
    if (px > 48) px = 48;
    for (j = 0; j < 6; j++) {
        k = (int16_t)(j * 8 + 8) - (48 - px);
        if (k < 0) k = 0; if (k > 8) k = 8;
        put_tile(TGT_BG, 12 + j, 11, T_EXP0 + k, 0x80 | 3);
    }
}
static void hud_foe(void) {
    hp_bar(TGT_BG, 2, 2, dfoe, mon_maxhp(&foe), 1);
    set_hp_color(1, hp_level(dfoe, mon_maxhp(&foe)));
}
static void hud_me(void) {
    mon_t *m = &G.party[me]; uint16_t mx = mon_maxhp(m);
    hp_bar(TGT_BG, 10, 9, dme, mx, 2);
    set_hp_color(2, hp_level(dme, mx));
    print_num(TGT_BG, 11, 10, dme, 3); put_tile(TGT_BG, 14, 10, T_SLASH, 0x80); print_num(TGT_BG, 15, 10, mx, 3);
}
static void show_foe(void) {
    uint8_t i;
    pic_load(SPECIES[foe.sp].front, 1, FOE_T, 4);
    pic_place(12, 0, 7, 7, FOE_T, 4 | 0x08);
    var_sp[0] = foe.sp; print_right(TGT_BG, 7, 0, S_NAME_S0);
    for (i = 0; i < 3; i++) put_tile(TGT_BG, 8 + i, 1, T_PAPER, 0x80);
    print_lv(TGT_BG, 8, 1, foe.lv);
    hud_foe();
    pal_apply();
}
static void clear_me(void) {
    fill_tiles(TGT_BG, 1, 6, 6, 6, T_BLANK, 0);
    fill_tiles(TGT_BG, 8, 7, 7, 2, T_BLANK, 0);
}
static void show_me(void) {
    mon_t *m = &G.party[me]; uint8_t i;
    clear_me();
    pic_load(SPECIES[m->sp].back, 1, ME_T, 5);
    pic_place(1, 6, 6, 6, ME_T, 5 | 0x08);
    var_sp[0] = m->sp; print_right(TGT_BG, 15, 7, S_NAME_S0);
    for (i = 0; i < 4; i++) put_tile(TGT_BG, 15 + i, 8, T_PAPER, 0x80);
    print_lv(TGT_BG, 15, 8, m->lv);
    dme = m->hp; hud_me(); exp_bar();
    pal_apply();
}
static void draw_static(void) {
    uint8_t i;
    for (i = 0; i < N_BMAP; i++) put_tile(TGT_BG, BMAP[i * 3], BMAP[i * 3 + 1], BMAP[i * 3 + 2], 0x80);
}
// 전투 시작: 상대가 왼쪽에서 미끄러져 들어온 뒤 상자들이 나타남 (포켓몬 금 오마주)
static void intro_slide(void) {
    uint8_t x;
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    pic_load(SPECIES[foe.sp].front, 1, FOE_T, 4);
    pic_place(12, 0, 7, 7, FOE_T, 4 | 0x08);
    move_bkg(152, 0); pal_apply();
    DISPLAY_ON;
    for (x = 152; x; x -= 4) { move_bkg(x, 0); frame(); }
    move_bkg(0, 0);
    draw_static(); show_foe();
}
static void screen_full(uint8_t with_me) {
    DISPLAY_OFF;
    screen_clear(); scene = SCENE_OTHER; pool_reset(1);
    draw_static(); show_foe();
    if (with_me) show_me();
    DISPLAY_ON;
}

// HP 줄어드는 모습
static void anim_hp(void) {
    mon_t *m = &G.party[me]; uint16_t t;
    for (;;) {
        uint8_t ch = 0;
        t = foe.hp; if (dfoe != t) { if (dfoe > t) { dfoe -= (dfoe - t > 2) ? 2 : 1; } else dfoe++; ch = 1; hud_foe(); }
        t = m->hp; if (dme != t) { if (dme > t) { dme -= (dme - t > 2) ? 2 : 1; } else dme++; ch = 1; hud_me(); }
        if (!ch) break;
        frame();
    }
}
static void blink_pic(uint8_t foe_side) {
    uint8_t i;
    for (i = 0; i < 6; i++) {
        if (foe_side) { if (i & 1) pic_place(12, 0, 7, 7, FOE_T, 4 | 0x08); else fill_tiles(TGT_BG, 12, 0, 7, 7, T_BLANK, 0); }
        else { if (i & 1) pic_place(1, 6, 6, 6, ME_T, 5 | 0x08); else fill_tiles(TGT_BG, 1, 6, 6, 6, T_BLANK, 0); }
        wait_frames(4);
    }
}

static uint16_t stat_of(mon_t *m, uint8_t i, int8_t stage) {
    uint16_t v = mon_stat(m, i);
    if (stage > 0) v = v * (2 + stage) / 2;
    else if (stage < 0) v = v * 2 / (2 - stage);
    return v ? v : 1;
}
static uint8_t beats(uint8_t a, uint8_t d) {     // 0 백신 1 데이터 2 바이러스: 백신>바이러스>데이터>백신
    return (a == 0 && d == 2) || (a == 2 && d == 1) || (a == 1 && d == 0);
}

// who: 0 나, 1 상대
static void use_move(uint8_t who, uint8_t slot) {
    mon_t *att = who ? &foe : &G.party[me], *def = who ? &G.party[me] : &foe;
    uint8_t mv = slot == 4 ? MV_STRUGGLE : att->mv[slot], aa, da, crit, mult;     // 4 = 발버둥
    const move_t *M_ = &MOVES[mv];
    uint32_t dmg;
    if (slot < 4 && att->pp[slot]) att->pp[slot]--;
    var_sp[0] = att->sp; var_mv = mv;
    say((who && kind == 0) ? S_USE_W : S_USE);
    if (rnd8(100) >= M_->acc) { say(S_MISS); return; }
    if (!M_->power) {
        if (M_->eff == 1) {
            int8_t *s = who ? &sme : &sfoe;
            if (*s <= -6) { say(S_NOEFF); return; }
            (*s)--; var_sp[0] = def->sp; say((!who && kind == 0) ? S_DEFDN_W : S_DEFDN);
        } else {
            int8_t *s = who ? &sfoe : &sme;
            if (*s >= 6) { say(S_NOEFF); return; }
            (*s)++; var_sp[0] = att->sp; say((who && kind == 0) ? S_DEFUP_W : S_DEFUP);
        }
        return;
    }
    {
        uint16_t A = mon_stat(att, 1), D = stat_of(def, 2, who ? sme : sfoe), lvf = att->lv * 2 / 5 + 2;
        uint16_t pw = M_->power, cap = 20 + 3 * (uint16_t)att->lv;      // 레벨이 낮으면 큰 기술도 힘을 다 못 냄
        if (pw > cap) pw = cap;
        dmg = ((uint32_t)lvf * pw * A / D) / 50 + 2;
    }
    if (M_->kind) dmg = dmg * 3 / 2;              // 필살기: 포켓몬 자속 보정처럼 1.5배
    crit = rnd8(16) == 0; if (crit) dmg *= 2;
    aa = SPECIES[att->sp].attr; da = SPECIES[def->sp].attr;
    mult = beats(aa, da) ? 2 : beats(da, aa) ? 0 : 1;
    if (mult == 2) dmg = dmg * 5 / 4; else if (mult == 0) dmg = dmg * 4 / 5;      // 상성 1.25배 / 0.8배 (속성이 하나뿐이라 포켓몬보다 약하게)
    dmg = dmg * (217 + rnd8(39)) / 255; if (!dmg) dmg = 1;
    tb_close();
    blink_pic(!who);
    sfx_play(mult == 2 ? SFX_HIT2 : SFX_HIT);
    if (dmg >= def->hp) def->hp = 0; else def->hp -= (uint16_t)dmg;
    anim_hp();
    if (crit) say(S_CRIT);
    if (mult == 2) say(S_SUPER); else if (mult == 0) say(S_WEAK);
    if (M_->eff == 3 && att->hp) {                // 반동
        dmg = dmg / 4; if (!dmg) dmg = 1;
        if (dmg >= att->hp) att->hp = 0; else att->hp -= (uint16_t)dmg;
        anim_hp(); var_sp[0] = att->sp; say(S_RECOIL);
    }
}

static void give_exp(void) {
    uint8_t i, cnt = 0;
    uint16_t gain;
    for (i = 0; i < G.nparty; i++) if ((used >> i) & 1 && G.party[i].hp && !G.party[i].egg) cnt++;
    if (!cnt) return;
    gain = (uint16_t)SPECIES[foe.sp].exp * foe.lv / 5;
    if (kind) gain = gain * 3 / 2;
    gain /= cnt; if (!gain) gain = 1;
    for (i = 0; i < G.nparty; i++) {
        mon_t *m = &G.party[i];
        if (!((used >> i) & 1) || !m->hp || m->egg) continue;
        var_sp[0] = m->sp; var_num[0] = gain; say(S_EXP);
        m->bond = m->bond > 246 ? 250 : m->bond + (kind ? 4 : 2);
        m->exp += gain;
        while (m->lv < 100 && m->exp >= exp_at(m->lv + 1)) {
            uint16_t old = mon_maxhp(m);
            m->lv++; m->hp += mon_maxhp(m) - old; lvup |= 1 << i;
            if (i == me) { dme = m->hp; show_me(); }
            var_sp[0] = m->sp; var_num[0] = m->lv; jingle(SONG_LEVELUP); say(S_LVUP);
        }
        if (i == me) exp_bar();
    }
}

static uint8_t battle_menu(void) {
    static const uint8_t cx[4] = { 10, 14, 10, 14 }, cy[4] = { 13, 13, 15, 15 };
    uint8_t sel = 0, i, m;
    tb_close(); win_top = 12; move_win(7, 96); SHOW_WIN;
    m = pool_mark();
    draw_frame(TGT_WIN, 0, 12, 9, 6, 1); draw_frame(TGT_WIN, 9, 12, 11, 6, 1);
    var_sp[0] = G.party[me].sp;
    print_at(TGT_WIN, 1, 13, S_B_WHAT1); print_at(TGT_WIN, 1, 15, S_B_WHAT2);
    print_at(TGT_WIN, 11, 13, S_B_FIGHT); print_at(TGT_WIN, 15, 13, S_B_BAG); print_at(TGT_WIN, 11, 15, S_B_MON); print_at(TGT_WIN, 15, 15, S_B_RUN);
    for (;;) {
        for (i = 0; i < 4; i++) draw_cursor(TGT_WIN, cx[i], cy[i], i == sel);
        frame();
        if (joy_new & (J_UP | J_DOWN)) sel ^= 2;
        if (joy_new & (J_LEFT | J_RIGHT)) sel ^= 1;
        if (joy_new & J_A) { sfx_play(SFX_SELECT); break; }
    }
    pool_release(m); ui_close();
    return sel;
}
static uint8_t move_menu(void) {
    mon_t *mm = &G.party[me];
    uint8_t sel = 0, i, n = 0, m = pool_mark();
    for (i = 0; i < 4; i++) if (mm->mv[i] != 0xFF) n = i + 1;
    ui_open(8);
    draw_frame(TGT_WIN, 0, 8, 11, 10, 1); draw_frame(TGT_WIN, 11, 12, 9, 6, 1);
    print_max = 8;
    for (i = 0; i < n; i++) { var_mv = mm->mv[i]; print_at(TGT_WIN, 2, 9 + i * 2, S_NAME_M0); }
    print_max = 255;
    for (;;) {
        uint8_t mv = mm->mv[sel], mk = pool_mark();
        for (i = 0; i < n; i++) draw_cursor(TGT_WIN, 1, 9 + i * 2, i == sel);
        fill_tiles(TGT_WIN, 12, 13, 7, 4, T_PAPER, 0x80);
        print_at(TGT_WIN, 12, 13, MOVES[mv].kind ? S_K_SIG : S_K_BASIC);
        print_num(TGT_WIN, 12, 16, mm->pp[sel], 2); put_tile(TGT_WIN, 14, 16, T_SLASH, 0x80); print_num(TGT_WIN, 15, 16, MOVES[mv].pp, 2);
        for (;;) {
            frame();
            if (joy_new & (J_UP | J_DOWN | J_A | J_B)) break;
        }
        pool_release(mk);
        if (joy_new & J_UP) sel = sel ? sel - 1 : n - 1;
        else if (joy_new & J_DOWN) sel = (sel + 1 >= n) ? 0 : sel + 1;
        else if (joy_new & J_A) { pool_release(m); ui_close(); return sel; }
        else { pool_release(m); ui_close(); return 0xFF; }
    }
}

static uint8_t foe_pick(void) {
    uint8_t ok[4], n = 0, i;
    for (i = 0; i < 4; i++) if (foe.mv[i] != 0xFF && foe.pp[i]) ok[n++] = i;
    return n ? ok[rnd8(n)] : 4;
}
// 쓰러짐 확인: 0 계속, 1 이김, 2 짐
static uint8_t check_faint(void) {
    if (!foe.hp) {
        var_sp[0] = foe.sp; say(kind ? S_FAINT : S_FAINT_W);
        fill_tiles(TGT_BG, 12, 0, 7, 7, T_BLANK, 0);
        give_exp();
        return 1;
    }
    if (!G.party[me].hp) {
        var_sp[0] = G.party[me].sp; say(S_FAINT);
        G.party[me].bond = G.party[me].bond > 10 ? G.party[me].bond - 10 : 0;     // 돌봄 실수
        clear_me();
        if (!alive_count()) return 2;
        for (;;) {
            uint8_t s = party_screen(1);
            screen_full(0);
            if (s == 0xFF || G.party[s].egg || !G.party[s].hp) continue;
            me = s; sme = 0; used |= 1 << me;
            var_sp[0] = G.party[me].sp; say(S_GO); show_me();
            break;
        }
    }
    return 0;
}
static uint8_t turn(uint8_t myslot) {   // myslot FF = 내 차례 없음
    uint8_t r, me0 = me;
    uint16_t s1 = stat_of(&G.party[me], 3, 0), s2 = stat_of(&foe, 3, 0);
    uint8_t first = (myslot != 0xFF) && (s1 > s2 || (s1 == s2 && rnd8(2)));
    if (myslot != 0xFF && first) { use_move(0, myslot); if ((r = check_faint())) return r; }
    if (foe.hp) { use_move(1, foe_pick()); if ((r = check_faint())) return r; }
    if (myslot != 0xFF && !first && me == me0 && G.party[me].hp) { use_move(0, myslot); if ((r = check_faint())) return r; }
    return 0;
}

// ───────── 포획 (디지몬 RPG 오마주: 디지바이스는 한 번 싸움에 3번, 그물은 확률↑·성장기까지) ─────────
static uint8_t cap_tries;
static uint8_t capture(uint8_t it) {      // 4 = 잡음(전투 끝), 0 = 계속
    uint8_t tier = SPECIES[foe.sp].tier, k = IT_KIND[it], ch, lost, i;
    uint16_t mx = mon_maxhp(&foe);
    if (kind) { say(S_CAP_BOSS); return 0; }
    if (k == 1) { if (!cap_tries) { say(S_CAP_NOMORE); return 0; } cap_tries--; say(S_CAP_DV); }
    else { G.bag[it]--; var_item = it; say(S_CAP_NET); }
    var_sp[0] = foe.sp;
    if (tier >= 3 || (tier == 2 && k != 3)) { flash(1); say(S_CAP_STRONG); return turn(0xFF); }   // 유년기(0·1)만, 성장기(2)는 성장기 그물
    lost = (uint8_t)((uint32_t)(mx - foe.hp) * 100 / mx);
    ch = k == 1 ? 6 + lost / 3 : k == 2 ? 45 + lost / 2 : (tier == 2 ? 25 + lost / 2 : 70 + lost / 4);
    sfx_play(SFX_THROW);
    for (i = 0; i < 3; i++) { flash(1); blink_pic(1); }
    if (rnd8(100) < ch) {
        uint8_t r;
        tb_close(); jingle(SONG_CAPTURE); say(S_CAP_OK);
        for (i = 0; i < 4; i++) if (foe.mv[i] != 0xFF) foe.pp[i] = MOVES[foe.mv[i]].pp;
        r = add_mon(&foe); set_own(foe.sp);
        say(r == 0 ? S_JOINED : S_JOINED_BOX);
        return 4;
    }
    say(S_CAP_NG);
    return turn(0xFF);
}

uint8_t battle(uint8_t sp, uint8_t lv, uint8_t k) BANKED {
    uint8_t res = 0, act, s;
    kind = k; runs = 0; sme = sfoe = 0; lvup = 0; cap_tries = 3;
    mon_make(&foe, sp, lv); set_seen(sp);
    me = first_alive(); used = 1 << me;
    tb_close(); music_play(kind ? SONG_BOSS : SONG_BATTLE); flash(2);
    dfoe = foe.hp;
    intro_slide();
    var_sp[0] = sp; say(kind ? S_BOSS_APPEAR : S_WILD_APPEAR);
    var_sp[0] = G.party[me].sp; say_nowait(S_GO); show_me(); wait_frames(20);
    while (!res) {
        act = battle_menu();
        if (act == 0) {
            for (s = 0; s < 4; s++) if (G.party[me].mv[s] != 0xFF && G.party[me].pp[s]) break;
            if (s == 4) { var_sp[0] = G.party[me].sp; say(S_STRUGGLE); res = turn(4); continue; }
            s = move_menu();
            if (s == 0xFF) continue;
            if (!G.party[me].pp[s]) { say(S_NO_PP); continue; }
            if (SPECIES[G.party[me].sp].dark && rnd8(100) < 30) {      // 암흑 진화체 폭주
                uint8_t t, n = 0;
                for (t = 0; t < 4; t++) if (G.party[me].mv[t] != 0xFF) n = t + 1;
                var_sp[0] = G.party[me].sp; say(S_RAMPAGE);
                s = rnd8(n); if (!G.party[me].pp[s]) s = 0;
            }
            res = turn(s);
        } else if (act == 1) {
            uint8_t used_item = bag_screen(1);
            screen_full(1);
            if (!used_item) continue;
            if (used_item >= 0x10) { res = capture(used_item & 0x0F); continue; }
            dme = G.party[me].hp; hud_me();
            res = turn(0xFF);
        } else if (act == 2) {
            s = party_screen(1);
            screen_full(1);
            if (s == 0xFF) continue;
            if (G.party[s].egg) { say(S_EGG_CANT); continue; }
            var_sp[0] = G.party[s].sp;
            if (!G.party[s].hp) { say(S_CANT); continue; }
            if (s == me) { say(S_ALREADY); continue; }
            var_sp[0] = G.party[me].sp; say_nowait(S_BACK); wait_frames(20); clear_me();
            me = s; sme = 0; used |= 1 << me;
            var_sp[0] = G.party[me].sp; say_nowait(S_GO); show_me(); wait_frames(20);
            res = turn(0xFF);
        } else {
            if (kind) { say(S_NO_RUN); continue; }
            runs++;
            {
                uint16_t ch = stat_of(&G.party[me], 3, 0) * 32 / stat_of(&foe, 3, 0) + 30 * runs;
                if (rnd8(255) < ch) { sfx_play(SFX_RUN); say(S_RUN_OK); res = 3; }
                else { say(S_RUN_NG); res = turn(0xFF); }
            }
        }
    }
    tb_close();
    if (res == 2) return 0;
    if (res == 1) {          // 이기면 비트
        uint16_t b = kind ? (uint16_t)foe.lv * 40 : (uint16_t)foe.lv * 8 + 10;
        if (G.bits > 60000 - b) G.bits = 60000; else G.bits += b;
        var_num[0] = b; say(S_GOT_BITS); tb_close();
    }
    evolve_check();
    return res == 3 ? 2 : 1;
}

// ───────── 진화 ─────────
#include "evox.h"       // EVO_ALT · EVO_FAIL · EVO_SPIRAL · EVO_UNDARK (build.py)
// 성장기→성숙기: 유대로 갈래 (본래 / 다른 / 실패)
// 성숙기→완전체: 문장이 하나 이상 필요. 자기 문장 → 문장 진화, 없으면 암흑 진화 위험 (유대가 낮으면 억지로)
void evolve_check(void) BANKED {
    uint8_t i, to, own;
    for (i = 0; i < G.nparty; i++) {
        mon_t *m = &G.party[i]; const species_t *s;
        if (m->egg || !((lvup >> i) & 1)) continue;
        s = &SPECIES[m->sp];
        if (s->evo_to == 0xFF || m->lv < s->evo_lv) continue;
        if (s->evo_need == 0xFE) continue;
        to = s->evo_to; var_sp[0] = m->sp;
        if (s->evo_need != 0xFF) {
            if (!G.crests) continue;                // 문장이 하나도 없으면 아직
            own = s->evo_need < 8 && ((G.crests >> s->evo_need) & 1);
            if (!own && s->dark_to != 0xFF) {
                if (m->bond < BOND_LOW) { say(S_DARK_FORCE); }
                else if (!ask(S_DARK_Q)) { tb_close(); continue; }
                tb_close(); flash(2); say(S_DARK_EVO); tb_close();
                evolve_scene(i, s->dark_to, 0);
                continue;
            }
            if (own) { flash(1); say(S_CREST_SHINE); tb_close(); }
        } else if (EVO_FAIL[m->sp] != 0xFF && m->bond < BOND_LOW) to = EVO_FAIL[m->sp];
        else if (EVO_ALT[m->sp] != 0xFF && m->bond < BOND_HI) to = EVO_ALT[m->sp];
        evolve_scene(i, to, 1);
    }
    lvup = 0;
}
uint8_t item_evolve(uint8_t slot, uint8_t kind) BANKED {
    mon_t *m = &G.party[slot]; uint8_t to;
    to = kind == 5 ? SPECIES[m->sp].dark_to : EVO_SPIRAL[m->sp];
    var_sp[0] = m->sp;
    if (m->egg || to == 0xFF) { say(S_NOTHING); tb_close(); return 0; }
    flash(2); say(S_DARK_EVO); tb_close();
    evolve_scene(slot, to, 0);
    return 1;
}
void purify(void) BANKED {
    uint8_t i, to; uint16_t old;
    for (i = 0; i < G.nparty; i++) {
        mon_t *m = &G.party[i];
        if (m->egg || !SPECIES[m->sp].dark || (to = EVO_UNDARK[m->sp]) == 0xFF) continue;
        var_sp[0] = m->sp;
        if (!ask(S_PURIFY_Q)) { tb_close(); continue; }
        tb_close(); flash(1);
        old = mon_maxhp(m); m->sp = to; m->hp = m->hp + mon_maxhp(m) > old ? m->hp + mon_maxhp(m) - old : 1;
        if (m->hp > mon_maxhp(m)) m->hp = mon_maxhp(m);
        var_sp[1] = to; say(S_PURIFIED); tb_close();
    }
}
static void sil(uint8_t palno, uint8_t on, uint8_t pic) {
    if (on) { bgpal[palno * 4 + 1] = bgpal[palno * 4 + 2] = bgpal[palno * 4 + 3] = RGB(7, 7, 9); pal_apply(); }
    else { pic_load(pic, 1, palno == 4 ? 128 : 192, palno); pal_apply(); }
}
uint8_t evolve_scene(uint8_t slot, uint8_t to, uint8_t can_cancel) BANKED {
    mon_t *m = &G.party[slot];
    uint8_t from = m->sp, i, per, t, got[3], n, cur = 0;
    uint16_t old; uint8_t ps = cur_song;
    music_play(SONG_EVOLVE);
    DISPLAY_OFF; screen_clear(); scene = SCENE_OTHER;
    pic_load(SPECIES[from].front, 1, 128, 4); pic_load(SPECIES[to].front, 1, 192, 5);
    pic_place(6, 2, 7, 7, 128, 4 | 0x08);
    DISPLAY_ON; pal_apply();
    var_sp[0] = from; say_nowait(S_EVO1); wait_frames(50);
    sil(4, 1, 0); sil(5, 1, 0);
    for (per = 24; per >= 4; per -= 4) {
        for (t = 0; t < 2; t++) {
            cur ^= 1;
            pic_place(6, 2, 7, 7, cur ? 192 : 128, (cur ? 5 : 4) | 0x08);
            for (i = 0; i < per; i++) {
                frame();
                if (can_cancel && (joy_new & J_B)) {      // 포켓몬처럼 B로 멈춤 (다음 레벨업에 다시)
                    pic_place(6, 2, 7, 7, 128, 4 | 0x08); sil(4, 0, SPECIES[from].front);
                    var_sp[0] = from; say(S_EVO_STOP); tb_close();
                    music_play(ps);
                    return 0;
                }
            }
        }
    }
    pic_place(6, 2, 7, 7, 192, 5 | 0x08);
    flash(1);
    pic_load(SPECIES[to].front, 1, 192, 5); pal_apply();
    old = mon_maxhp(m); m->sp = to; m->hp += mon_maxhp(m) - old; set_own(to);
    var_sp[0] = from; var_sp[1] = to; say(S_EVO2);
    n = learn_sig(m, to, got);
    for (i = 0; i < n; i++) learn_ui(m, got[i]);
    tb_close();
    music_play(ps);
    return 1;
}

void hatch_scene(uint8_t slot) BANKED {
    mon_t *m = &G.party[slot]; uint8_t sp = m->sp, i;
    DISPLAY_OFF; screen_clear(); scene = SCENE_OTHER;
    pic_load(PIC_EGG, 1, 128, 4); pic_place(6, 2, 7, 7, 128, 4 | 0x08);
    DISPLAY_ON; pal_apply();
    say_nowait(S_HATCH1); wait_frames(40);
    for (i = 0; i < 8; i++) { move_bkg((i & 1) ? 2 : 254, 0); wait_frames(6); }
    move_bkg(0, 0);
    flash(2);
    mon_make(m, sp, 3); m->bond = 50; set_own(sp);
    pic_load(SPECIES[sp].front, 1, 128, 4); pal_apply();
    var_sp[0] = sp; say(S_HATCH2);
    tb_close();
}
