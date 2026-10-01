// 전투: 웹판 battle()/heroTurn()/foeTurn() 을 그대로 옮김 (2번 은행, 자료표와 같은 은행)
#pragma bank 2
#include <gb/gb.h>
#include <string.h>
#include "engine.h"
#include "data.h"
#include "game.h"

State S;
static const Foe *F; static uint8_t foeId;
static int16_t fhp, fmax, fShown, hShown;
static int8_t fAtkB, fDefB;
static uint8_t heroSleep, heroBind, hide, foeSleep, phialUsed, foeShow, heroShow;

uint16_t statOf(uint8_t id, uint8_t lv, uint8_t k) BANKED {
    const Hero *h = &HEROES[id]; uint16_t v;
    if (k == ST_HP) { v = h->hp + 4 * (lv - 5); if (id == HE_FRODOSAM && S.wound) v = (v * 7 + 5) / 10; return v; }
    if (k == ST_ATK) return h->atk + 2 * (lv - 5) + (id == HE_FRODOSAM && S.dagger ? 3 : 0);
    if (k == ST_DEF) return h->def + 2 * (lv - 5) + (id == HE_FRODOSAM && S.mithril ? 5 : 0) + (S.cloak ? 2 : 0);
    return h->spd + (lv - 5);
}
uint16_t stat(uint8_t k) BANKED { return statOf(S.hero, S.lv, k); }
uint8_t heroMove(uint8_t id, uint8_t i) { return (id == HE_FRODOSAM && S.sting && i == 0) ? MV_STINGM : HEROES[id].moves[i]; }
uint8_t has(uint8_t id) BANKED { uint8_t i; for (i = 0; i < S.np; i++) if (S.party[i] == id) return 1; return 0; }
static uint8_t memi(uint8_t id) { uint8_t i; for (i = 0; i < S.np; i++) if (S.party[i] == id) return i; return 0; }
void swapTo(uint8_t id) BANKED {
    uint8_t a = memi(S.hero), b = memi(id);
    S.mlv[a] = S.lv; S.mxp[a] = S.xp; S.mhp[a] = S.hp;
    S.hero = id; S.lv = S.mlv[b]; S.xp = S.mxp[b]; S.hp = S.mhp[b];
}
void addMember(uint8_t id, uint8_t lv) BANKED { uint8_t i; if (has(id)) return; i = S.np++; S.party[i] = id; S.mlv[i] = lv; S.mxp[i] = 0; S.mhp[i] = statOf(id, lv, ST_HP); }
void healAll(void) BANKED { uint8_t i; S.hp = stat(ST_HP); for (i = 0; i < S.np; i++) S.mhp[i] = statOf(S.party[i], S.mlv[i], ST_HP); }

// ── 화면 ──
static void bar(uint8_t x, uint8_t y, int16_t cur, int16_t max) {
    uint8_t w; if (cur < 0) cur = 0;
    rect(x, y, 50, 4, 3); rect(x + 1, y + 1, 48, 2, 0);
    w = (uint8_t)((cur * 48L + max / 2) / max); rect(x + 1, y + 1, w, 2, cur * 4 < max ? 3 : 2);
}
static void foeStatus(void) {
    rect(0, 0, 84, 25, 0);
    if (!foeShow) return;
    text(F->name, 4, 3, 3); sb_clear(); sb_add("Lv"); sb_num(F->lv, 0); if (text_w(F->name) < 46) text(SB, 54, 3, 3);
    text("HP", 6, 13, 3); bar(22, 17, fShown, fmax); rect(4, 23, 72, 1, 3); rect(75, 15, 1, 9, 3);
}
static void heroStatus(void) {
    uint8_t i;
    rect(86, 62, 74, 34, 0);
    text(HEROES[S.hero].name, 89, 62, 3); sb_clear(); sb_add("Lv"); sb_num(S.lv, 0); text(SB, 139, 62, 3);
    text("HP", 90, 72, 3); bar(106, 76, hShown, stat(ST_HP));
    sb_clear(); sb_num(hShown < 0 ? 0 : hShown, 3); sb_add("/"); sb_num(stat(ST_HP), 3); text(SB, 106, 82, 3);
    rect(86, 94, 72, 1, 3); rect(86, 72, 1, 23, 3);
    for (i = 0; i < S.shadow && i < 5; i++) rect(150 - i * 4, 90, 2, 2, 3);
}
static const uint8_t EW[6] = { 21, 31, 34, 34, 31, 21 };   // 적 발판 타원 (웹판과 같은 값)
static void ground(void) { uint8_t y; for (y = 0; y < 6; y++) rect(124 - EW[y], 58 + y, EW[y] * 2, 1, 1); }
static void foeSpr(uint8_t white) { uint8_t b = F->spr; blit(b, 152 - spr_w(b), 64 - spr_h(b), white); }
static void heroSpr(uint8_t white) { uint8_t b = HEROES[S.hero].back; blit_ymax = 96; blit(b, 0, 104 - spr_h(b), white); blit_ymax = 144; }
static void battleScene(void) {
    rect(0, 0, 160, 96, 0);
    ground();
    if (foeShow) foeSpr(0);
    if (heroShow) heroSpr(0);
    foeStatus(); heroStatus();
    box(0, 96, 160, 48);
}
static void foeGone(void) {   // 적 그림만 지움
    uint8_t b = F->spr, h = spr_h(b);
    foeShow = 0; rect(152 - spr_w(b), 64 - h, spr_w(b), h, 0); ground(); foeStatus(); heroStatus();
}
static void heroGone(void) {
    uint8_t b = HEROES[S.hero].back, h = spr_h(b);
    heroShow = 0; rect(0, 104 - h, spr_w(b), h - 8, 0);
}
static void hpAnim(void) {   // 체력 막대가 천천히 따라감
    int16_t d;
    for (;;) {
        uint8_t ch = 0;
        d = fhp - fShown; if (d) { fShown += d > 0 ? (d + 5) / 6 : (d - 5) / 6; ch = 1; foeStatus(); }
        d = S.hp - hShown; if (d) { hShown += d > 0 ? (d + 5) / 6 : (d - 5) / 6; ch = 1; heroStatus(); }
        if (!ch) return;
        frame();
    }
}
static void flash(uint8_t foe) {   // 맞으면 세 번 깜빡
    uint8_t i;
    for (i = 0; i < 3; i++) {
        if (foe) foeSpr(1); else heroSpr(1); wait_frames(4);
        if (foe) foeSpr(0); else heroSpr(0); wait_frames(4);
    }
}
// ── 계산 ──
typedef struct { uint16_t d; uint8_t m, crit; } Dmg;
static Dmg R;
static void dmgCalc(const Move *mv, uint16_t atk, int8_t ab, uint16_t def, int8_t db, uint8_t lv, uint8_t target) {
    uint32_t num, den;
    R.m = EFFECT[mv->elem][target]; R.crit = rnd100() < mv->crit;
    num = (uint32_t)mv->pow * atk * (4 + ab) * (36 + 5 * lv);
    num = num * (85 + rnd100() % 16) * R.m * (R.crit ? 3 : 2);
    den = (uint32_t)def * (4 + db) * 60 * 100 * 2;
    R.d = (uint16_t)((num + den / 2) / den); if (!R.d) R.d = 1;
}
static void sayName(const char *name, const char *a, const char *b, const char *rest) { sb_clear(); sb_add(name); sb_josa(a, b); sb_add(rest); say(SB); }
static void switchIn(uint8_t id, uint8_t forced) {
    if (!forced) { sb_clear(); sb_add(HEROES[S.hero].name); sb_add(", 물러서!"); say(SB); heroGone(); wait_frames(10); }
    swapTo(id); hShown = S.hp; S.buffAtk = S.buffDef = 0; heroSleep = heroBind = hide = 0;
    heroShow = 1; heroSpr(0); heroStatus(); sb_clear(); sb_add("가라, "); sb_add(HEROES[id].name); sb_add("!"); say(SB);
}
enum { A_NONE, A_MOVE, A_LEMBAS, A_HERB, A_PHIAL };
static uint8_t act, actMove;
static uint8_t heroTurn(void) {
    const Hero *H = &HEROES[S.hero]; const Move *mv; uint8_t i, before;
    if (heroSleep) { heroSleep--; if (heroSleep) { sayName(H->name, "은", "는", " 깊이 잠들어 있다..."); return 0; } sayName(H->name, "이", "가", " 퍼뜩 정신을 차렸다!"); }
    if (heroBind) { heroBind--; say("뿌리에 묶여 움직일 수 없다!"); return 0; }
    if (act == A_NONE) return 0;
    if (act == A_LEMBAS) { S.lembas--; before = S.hp; S.hp += 20; if (S.hp > stat(ST_HP)) S.hp = stat(ST_HP); hpAnim();
        sb_clear(); sb_add("렘바스를 한 입 먹었다. 체력이 "); sb_num(S.hp - before, 0); sb_add(" 회복됐다."); say(SB); return 0; }
    if (act == A_PHIAL) { phialUsed = 1; i = (F->type == TY_DARK || F->type == TY_BEAST || F->type == TY_WRAITH) ? 2 : 1; foeSleep = i;
        say("빛의 병을 높이 들었다! 별빛이 쏟아진다!"); sb_clear(); sb_add(F->name); sb_josa("이", "가"); sb_add(" 눈을 가리고 물러섰다! ("); sb_num(i, 0); sb_add("턴 움직이지 못함)"); say(SB); return 0; }
    if (act == A_HERB) { S.herb--; heroSleep = heroBind = 0; if (S.buffAtk < 0) S.buffAtk = 0; say("약초를 씹었다. 몸이 가뿐해졌다."); return 0; }
    mv = &MOVES[actMove];
    sb_clear(); sb_add(H->name); sb_add("의 "); sb_add(mv->name); sb_add("!"); say(SB);
    if (mv->line) say(mv->line);
    if (mv->kind == K_HIDE) {
        S.shadow++; hide = 1; heroStatus(); say("프로도가 반지를 끼자 모습이 사라졌다!");
        if (S.shadow >= 3) { S.hp -= 3 + S.shadow; if (S.hp < 1) S.hp = 1; hpAnim(); sb_clear(); sb_add("반지가 무겁게 짓누른다... (그림자 "); sb_num(S.shadow, 0); sb_add(")"); say(SB); }
        return 0;
    }
    if (mv->kind == K_BUFF) { if (mv->stat) { if (S.buffDef < 3) S.buffDef++; } else if (S.buffAtk < 3) S.buffAtk++; say(mv->stat ? "방어가 올라갔다!" : "공격이 올라갔다!"); return 0; }
    if (mv->kind == K_HEAL) { before = S.hp; S.hp += (stat(ST_HP) * mv->amt + 50) / 100; if (S.hp > stat(ST_HP)) S.hp = stat(ST_HP); if (mv->cure) heroSleep = heroBind = 0; hpAnim();
        sb_clear(); sb_add("체력이 "); sb_num(S.hp - before, 0); sb_add(" 회복됐다."); say(SB); return 0; }
    for (i = 0; i < mv->hits; i++) {
        if (rnd100() >= mv->acc) { say("빗나갔다!"); continue; }
        dmgCalc(mv, stat(ST_ATK), S.buffAtk, F->def, fDefB, S.lv, F->type);
        flash(1); fhp -= R.d; if (fhp < 0) fhp = 0; hpAnim();
        if (R.crit) say("급소에 맞았다!");
        if (R.m > 1) say("효과가 굉장했다!");
        if (fhp <= 0) break;
    }
    if (fhp <= 0) {
        foeGone();
        sayName(F->name, "을", "를", " 쓰러뜨렸다!");
        S.xp += F->lv * 12; sb_clear(); sb_add("경험치를 "); sb_num(F->lv * 12, 0); sb_add(" 얻었다."); say(SB);
        while (S.xp >= S.lv * 10) { uint16_t old = stat(ST_HP); S.xp -= S.lv * 10; S.lv++; S.hp += stat(ST_HP) - old; hShown = S.hp; heroStatus();
            sb_clear(); sb_add("레벨이 올랐다! 이제 Lv"); sb_num(S.lv, 0); sb_add("이다."); say(SB); }
        return R_WIN;
    }
    return 0;
}
static uint8_t foeTurn(void) {
    const Hero *H = &HEROES[S.hero]; const Move *mv; uint8_t i, n, alive[5];
    const char *names[5];
    if (foeSleep) { foeSleep--; sayName(F->name, "은", "는", " 움직이지 않는다."); return 0; }
    mv = &MOVES[F->moves[rnd() % 3]];
    sb_clear(); sb_add(F->name); sb_add("의 "); sb_add(mv->name); sb_add("!"); say(SB);
    if (mv->line) say(mv->line);
    if (hide && mv->kind != K_DEBUFF) { hide = 0; say("하지만 아무도 보이지 않는다! 공격이 빗나갔다."); return 0; }
    if (mv->kind == K_DEBUFF) { if (mv->stat) { if (S.buffDef > -2) S.buffDef--; } else if (S.buffAtk > -2) S.buffAtk--; say(mv->stat ? "방어가 떨어졌다!" : "공격이 떨어졌다!"); return 0; }
    if (mv->kind == K_SLEEP) { if (rnd100() < mv->acc) { heroSleep = 1 + (rnd100() < 40); sayName(H->name, "은", "는", " 스르르 잠이 들었다..."); } else say("하지만 정신을 붙잡았다!"); return 0; }
    if (rnd100() >= mv->acc) { say("빗나갔다!"); return 0; }
    dmgCalc(mv, F->atk, fAtkB, stat(ST_DEF), S.buffDef, F->lv, 0);
    flash(0); S.hp -= R.d; if (S.hp < 0) S.hp = 0; hpAnim();
    if (R.crit) say("급소에 맞았다!");
    if (mv->bind && rnd100() < mv->bind && S.hp > 0) { heroBind = 1; say("뿌리가 다리를 휘감았다!"); }
    if (mv->weaken && rnd100() < mv->weaken && S.hp > 0) { if (S.buffAtk > -2) S.buffAtk--; say("냉기에 힘이 빠졌다... 공격이 떨어졌다."); }
    if (S.hp <= 0) {
        heroGone(); sayName(H->name, "은", "는", " 쓰러지고 말았다...");
        n = 0; for (i = 0; i < S.np; i++) if (S.party[i] != S.hero && S.mhp[i] > 0) { alive[n] = S.party[i]; names[n] = HEROES[S.party[i]].name; n++; }
        if (!n) return R_LOSE;
        i = n > 1 ? choose("누가 나설까?", names, n, NOCANCEL) : 0;
        switchIn(alive[i], 1); return R_SWAPPED;
    }
    return 0;
}
static const char *MAIN_OPTS[4] = { "싸운다", "가방", "동료", "도망" };
uint8_t battle(uint8_t id, uint8_t noRun, uint8_t turns) BANKED {
    const Hero *H; const char *opts[5]; char ib[4][24]; uint8_t c, k, i, n, others[5], r, heroFirst, turn = 0;
    foeId = id; F = &FOES[id]; fhp = fmax = fShown = F->hp; fAtkB = fDefB = 0; hShown = S.hp;
    heroSleep = heroBind = hide = foeSleep = phialUsed = 0; foeShow = heroShow = 1;
    S.buffAtk = S.buffDef = 0;
    scene = battleScene; battleScene();
    sb_clear(); if (!F->boss) sb_add("야생의 "); sb_add(F->name); sb_josa("이", "가"); sb_add(F->boss ? " 앞을 가로막았다!" : " 덤벼들었다!"); say(SB);
    if (S.sting && F->type == TY_ORC) say("스팅의 칼날이 푸르게 빛난다! 오크가 가까이 있다.");
    for (;;) {
        if (turns && turn >= turns) return R_RESCUE;   // 구원: 이야기 쪽에서 대사 뒤 rescue_end()
        turn++;
        H = &HEROES[S.hero]; act = 0xFF;
        while (act == 0xFF) {
            sb_clear(); sb_add(H->name); sb_josa("은", "는"); sb_add(" 어떻게 할까?");
            c = choose(SB, MAIN_OPTS, 4, NOCANCEL);
            if (c == 0) {
                for (i = 0; i < 4; i++) opts[i] = MOVES[heroMove(S.hero, i)].name; opts[4] = "돌아가기";
                k = choose(0, opts, 5, 4); if (k < 4) { act = A_MOVE; actMove = heroMove(S.hero, k); }
            } else if (c == 1) {
                sb_clear(); sb_add("렘바스 ×"); sb_num(S.lembas, 0); strcpy(ib[0], SB);
                sb_clear(); sb_add("약초 ×"); sb_num(S.herb, 0); strcpy(ib[1], SB);
                opts[0] = ib[0]; opts[1] = ib[1]; n = 2;
                if (S.phial) opts[n++] = phialUsed ? "빛의 병 (약해짐)" : "빛의 병";
                opts[n] = "돌아가기";
                k = choose(0, opts, n + 1, n);
                if (k == 0 && S.lembas) act = A_LEMBAS;
                else if (k == 1 && S.herb) act = A_HERB;
                else if (k == 2 && S.phial && !phialUsed) act = A_PHIAL;
                else if (k == 2 && S.phial) say("빛의 병은 한 싸움에 한 번만 밝게 빛난다.");
                else if (k < n) say("가방에 남아 있지 않다.");
            } else if (c == 2) {
                n = 0; for (i = 0; i < S.np; i++) if (S.party[i] != S.hero) others[n++] = S.party[i];
                if (!n) { say(S.hero == HE_FRODOSAM ? "프로도와 샘은 서로를 바라보았다. 지금은 둘뿐이다." : "지금은 함께할 동료가 없다."); continue; }
                for (i = 0; i < n; i++) { uint8_t m = memi(others[i]); sb_clear(); sb_add(HEROES[others[i]].name); sb_add(" "); sb_num(S.mhp[m], 0); sb_add("/"); sb_num(statOf(others[i], S.mlv[m], ST_HP), 0); strcpy(ib[i], SB); opts[i] = ib[i]; }
                opts[n] = "돌아가기";
                k = choose("누구와 교대할까?", opts, n + 1, n);
                if (k < n) { if (S.mhp[memi(others[k])] <= 0) say("쓰러져 있어서 나설 수 없다."); else { switchIn(others[k], 0); act = A_NONE; } }
            } else {
                if (F->boss || noRun) say("도망칠 수 없다!");
                else if (rnd100() < 75) { say("무사히 도망쳤다!"); return R_RUN; }
                else { say("도망치지 못했다!"); act = A_NONE; }
            }
        }
        heroFirst = stat(ST_SPD) >= F->spd || act == A_LEMBAS || act == A_HERB || act == A_PHIAL;
        for (i = 0; i < 2; i++) {
            if ((i == 0) == heroFirst) { r = heroTurn(); if (r) return r; }
            else { r = foeTurn(); if (r == R_SWAPPED) break; if (r) return r; }
        }
    }
}

// 구원 전투 마무리: 적이 사라지고 경험치 (웹판: lv × 8)
void rescue_end(void) BANKED {
    foeGone();
    S.xp += F->lv * 8; sb_clear(); sb_add("경험치를 "); sb_num(F->lv * 8, 0); sb_add(" 얻었다."); say(SB);
    while (S.xp >= S.lv * 10) { uint16_t old = stat(ST_HP); S.xp -= S.lv * 10; S.lv++; S.hp += stat(ST_HP) - old;
        sb_clear(); sb_add("레벨이 올랐다! 이제 Lv"); sb_num(S.lv, 0); sb_add("이다."); say(SB); }
}
// 동료 빼기 (웹판 removeMember)
void removeMember(uint8_t id) BANKED {
    uint8_t i, j;
    if (!has(id)) return;
    if (S.hero == id) { for (i = 0; i < S.np; i++) if (S.party[i] != id) { swapTo(S.party[i]); break; } }
    for (i = 0, j = 0; i < S.np; i++) if (S.party[i] != id) { S.party[j] = S.party[i]; S.mlv[j] = S.mlv[i]; S.mxp[j] = S.mxp[i]; S.mhp[j] = S.mhp[i]; j++; }
    S.np = j;
}
// 웹판의 S.mem 반복문들
void party_hurt(uint8_t d) BANKED { uint8_t i; for (i = 0; i < S.np; i++) if (S.party[i] != S.hero) { S.mhp[i] -= d; if (S.mhp[i] < 1) S.mhp[i] = 1; } }
void party_floor_third(void) BANKED { uint8_t i; int16_t m; for (i = 0; i < S.np; i++) if (S.party[i] != S.hero) { m = (statOf(S.party[i], S.mlv[i], ST_HP) + 1) / 3; if (S.mhp[i] < m) S.mhp[i] = m; } }
void frodo_cap_hp(void) BANKED { uint8_t i = memi(HE_FRODOSAM); int16_t m;
    if (S.hero == HE_FRODOSAM) { m = stat(ST_HP); if (S.hp > m) S.hp = m; }
    else if (has(HE_FRODOSAM)) { m = statOf(HE_FRODOSAM, S.mlv[i], ST_HP); if (S.mhp[i] > m) S.mhp[i] = m; } }
void frodo_full_hp(void) BANKED { uint8_t i = memi(HE_FRODOSAM);
    if (S.hero == HE_FRODOSAM) S.hp = stat(ST_HP); else if (has(HE_FRODOSAM)) S.mhp[i] = statOf(HE_FRODOSAM, S.mlv[i], ST_HP); }
// 사우론의 입 막간: 일행을 잠시 맡겨 두고 아라곤 혼자
static State keep;
void keep_party(void) BANKED { keep = S; }
void solo_party(uint8_t id) BANKED { S.np = 1; S.party[0] = id; S.mlv[0] = S.lv; S.mxp[0] = 0; S.mhp[0] = 0; }
void restore_party(void) BANKED { uint8_t st = S.step; S = keep; S.step = st; }
