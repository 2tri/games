// 디지몬 GBC — 이야기 스크립트 실행기
#pragma bank 2
#include <gb/gb.h>
#include <string.h>
#include "engine.h"

uint8_t vm_result, vm_abort;
uint8_t field_battle(uint8_t sp, uint8_t lv, uint8_t kind);

static uint8_t sp_resolve(uint8_t s) {
    if (s == 0xFF) return KID_BABY[G.kid];
    if (s == 0xFE) return KID_PARTNER[G.kid];
    if (s == 0xFD) return G.party[0].sp;
    return s;
}

void run_script(uint8_t bank, const uint8_t *base, uint16_t off) BANKED {
    const uint8_t *pc = base + off;
    uint8_t op, a, b, c, d;
    uint16_t w;
    vm_abort = 0;
#define RB() far_u8(bank, pc++)
#define RW() (w = far_u16(bank, pc), pc += 2, w)
    for (;;) {
        op = RB();
        switch (op) {
        case OP_END: return;
        case OP_SAY: say(RW()); break;
        case OP_ASK: vm_result = ask(RW()); break;
        case OP_JMP: pc = base + RW(); break;
        case OP_JF: w = RW(); a = flag_get(w); w = RW(); if (a) pc = base + w; break;
        case OP_JNF: w = RW(); a = flag_get(w); w = RW(); if (!a) pc = base + w; break;
        case OP_JNO: w = RW(); if (!vm_result) pc = base + w; break;
        case OP_SETF: flag_set(RW()); break;
        case OP_CLRF: flag_clr(RW()); break;
        case OP_CLOSE: tb_close(); break;
        case OP_FLASH: flash(RB()); break;
        case OP_FADEOUT: tb_close(); fade_out(RB()); break;
        case OP_FADEIN:
            if (scene == SCENE_FIELD || cur_map == 0xFF || scene == SCENE_OTHER) fade_in();
            break;
        case OP_WARP:
            a = RB(); b = RB(); c = RB(); d = RB();
            tb_close();
            do_warp(a, b, c, d);
            vm_abort = 1; return;
        case OP_GIVEMON: {
            mon_t m;
            a = sp_resolve(RB()); b = RB();
            mon_make(&m, a, b); m.bond = 50; add_mon(&m);     // 이야기로 만난 파트너
            break;
        }
        case OP_GIVEITEM: a = RB(); b = RB(); G.bag[a] += b; tb_close(); jingle(SONG_ITEM); break;
        case OP_GIVEEGG: {
            mon_t m;
            memset(&m, 0, sizeof(m)); m.egg = 1; m.sp = EGGS[rnd8(N_EGGS)]; m.steps = 200; m.lv = 1;
            add_mon(&m);
            break;
        }
        case OP_HEAL: {
            uint8_t ps = cur_song, w = 0;
            heal_all(); music_play(SONG_HEAL);
            while (!music_done && ++w < 240) frame();
            music_play(ps);
            break;
        }
        case OP_SETHEAL: G.heal_map = RB(); G.heal_x = RB(); G.heal_y = RB(); G.heal_dir = RB(); break;
        case OP_PIC: a = RB(); tb_close(); if (a != 0xF0) { a = sp_resolve(a); set_seen(a); } pic_screen(a); break;
        case OP_PICOFF: tb_close(); if (cur_map != 0xFF) field_restore(); break;
        case OP_EVOLVE: {
            mon_t *m = &G.party[0];
            a = sp_resolve(RB()); b = RB();
            tb_close();
            m->lv = b; m->exp = exp_at(b);
            evolve_scene(0, a, 0);
            m->hp = mon_maxhp(m);
            break;
        }
        case OP_BATTLE:
            a = RB(); b = RB(); c = RB();
            tb_close();
            vm_result = field_battle(a, b, c);
            if (!vm_result) { vm_abort = 1; return; }
            break;
        case OP_CREST: G.crests |= 1 << RB(); break;
        case OP_WAIT: wait_frames(RB()); break;
        case OP_SHOP: tb_close(); shop_screen(); break;
        case OP_BOX: tb_close(); box_screen(); break;
        case OP_PURIFY: tb_close(); purify(); break;
        case OP_JKID: a = RB(); w = RW(); if (G.kid == a) pc = base + w; break;
        case OP_PICKKID: tb_close(); kid_pick(); break;
        case OP_SHAKE: shake(RB()); break;
        default: return;
        }
    }
}
