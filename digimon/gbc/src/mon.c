// 디지몬 GBC — 디지몬 계산 (뱅크 1)
#pragma bank 1
#include <gb/gb.h>
#include <string.h>
#include "engine.h"

// ───────── 디지몬 계산 ─────────
uint16_t mon_stat(const mon_t *m, uint8_t i) BANKED {
    uint16_t b = SPECIES[m->sp].base[i];
    uint16_t v = (b * 2 * m->lv) / 100;
    return i == 0 ? v + m->lv + 10 : v + 5;
}
uint32_t exp_at(uint8_t lv) BANKED { return lv <= 1 ? 0 : (uint32_t)lv * lv * lv; }
void mon_make(mon_t *m, uint8_t sp, uint8_t lv) BANKED {
    uint8_t mv[6], n = 0, i, t = SPECIES[sp].tier;
    memset(m, 0, sizeof(mon_t));
    m->sp = sp; m->lv = lv; m->exp = exp_at(lv);
    for (i = 0; i < 2; i++) if (TIER_BASIC[t * 2 + i] != 0xFF) mv[n++] = TIER_BASIC[t * 2 + i];
    for (i = 0; i < 3; i++) if (SPECIES[sp].sig[i] != 0xFF) mv[n++] = SPECIES[sp].sig[i];
    i = n > 4 ? n - 4 : 0;
    for (t = 0; t < 4; t++) {
        if (i < n) { m->mv[t] = mv[i]; m->pp[t] = MOVES[mv[i]].pp; i++; }
        else m->mv[t] = 0xFF;
    }
    m->hp = mon_maxhp(m);
}
uint8_t learn_sig(mon_t *m, uint8_t sp, uint8_t *got) BANKED {
    uint8_t i, j, k, n = 0, mv;
    for (i = 0; i < 3; i++) {
        mv = SPECIES[sp].sig[i]; if (mv == 0xFF) continue;
        for (j = 0; j < 4; j++) if (m->mv[j] == mv) break;
        if (j < 4) continue;
        got[n++] = mv;
        for (j = 0; j < 4; j++) if (m->mv[j] == 0xFF) break;
        if (j == 4) {   // 가장 앞의 기본기를 잊음
            for (j = 0; j < 4; j++) if (MOVES[m->mv[j]].kind == 0) break;
            if (j == 4) j = 0;
            for (k = j; k < 3; k++) { m->mv[k] = m->mv[k + 1]; m->pp[k] = m->pp[k + 1]; }
            j = 3;
        }
        m->mv[j] = mv; m->pp[j] = MOVES[mv].pp;
    }
    return n;
}
void set_seen(uint8_t sp) BANKED { G.seen[sp >> 3] |= 1 << (sp & 7); }
void set_own(uint8_t sp) BANKED { set_seen(sp); G.own[sp >> 3] |= 1 << (sp & 7); }
uint8_t add_mon(mon_t *m) BANKED {
    if (!m->egg) set_own(m->sp);
    if (G.nparty < 6) { G.party[G.nparty++] = *m; return 0; }
    if (G.nbox < MAX_BOX) { G.box[G.nbox++] = *m; return 1; }
    return 2;
}
void heal_all(void) BANKED {
    uint8_t i, j;
    for (i = 0; i < G.nparty; i++) {
        mon_t *m = &G.party[i]; if (m->egg) continue;
        m->hp = mon_maxhp(m);
        for (j = 0; j < 4; j++) if (m->mv[j] != 0xFF) m->pp[j] = MOVES[m->mv[j]].pp;
    }
}
uint8_t alive_count(void) BANKED {
    uint8_t i, n = 0;
    for (i = 0; i < G.nparty; i++) if (!G.party[i].egg && G.party[i].hp) n++;
    return n;
}
uint8_t first_alive(void) BANKED {
    uint8_t i;
    for (i = 0; i < G.nparty; i++) if (!G.party[i].egg && G.party[i].hp) return i;
    return 0;
}

