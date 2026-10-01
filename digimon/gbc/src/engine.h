// 디지몬 GBC — 엔진 공통 선언
#ifndef ENGINE_H
#define ENGINE_H
#include <gbdk/platform.h>
#include <stdint.h>
#include "data.h"
#include "gen.h"

// ── 게임 상태 (저장되는 것) ──
typedef struct {
    uint8_t sp, lv, egg, hpad;
    uint16_t hp;
    uint32_t exp;
    uint8_t mv[4], pp[4];
    uint16_t steps;
} mon_t;

#define MAX_BOX 20
#define N_FLAGBYTES 32
typedef struct {
    uint8_t magic[4];
    uint8_t kid, map, x, y, dir;
    uint8_t heal_map, heal_x, heal_y, heal_dir;
    uint8_t nparty, nbox;
    mon_t party[6];
    mon_t box[MAX_BOX];
    uint8_t bag[8];
    uint8_t flags[N_FLAGBYTES];
    uint8_t crests;
    uint8_t seen[12], own[12];
    uint32_t time;
    uint16_t bits;                 // 돈 (비트)
    uint16_t sum;
} game_t;
extern game_t G;

// ── 입력·시간 ──
extern uint8_t joy, joy_new;
extern uint16_t frames;
void frame(void);
void wait_frames(uint8_t n);
uint8_t wait_press(void);          // A 또는 B (돌려줌)
uint16_t rnd(void);
uint8_t rnd8(uint8_t n);           // 0..n-1

// ── 뱅크 ──
uint8_t far_u8(uint8_t bank, const uint8_t *p);
uint16_t far_u16(uint8_t bank, const uint8_t *p);
void far_copy(void *dst, uint8_t bank, const void *src, uint16_t n);
void far_vram(uint8_t vbank, uint8_t first, uint8_t n, uint8_t bank, const uint8_t *src);
void far_sprite(uint8_t vbank, uint8_t first, uint8_t n, uint8_t bank, const uint8_t *src);   // 다른 뱅크 코드는 SWITCH_ROM 금지 → 이것을 씀   // 배경·OBJ 타일 올리기

// ── 팔레트 ──
extern uint16_t bgpal[32], obpal[32];
extern uint8_t fade_lv, fade_white;
void pal_apply(void);
void fade_out(uint8_t white);
void fade_in(void);
void flash(uint8_t n);
void shake(uint8_t n);
void set_hp_color(uint8_t palno, uint8_t lvl);   // 0 초록 1 노랑 2 빨강

// ── 글 ──
#define TGT_WIN 0
#define TGT_BG 1
extern uint8_t win_top;
extern uint8_t var_sp[2];
extern uint16_t var_num[2];
extern uint8_t var_mv, var_item;
void put_tile(uint8_t tgt, uint8_t x, uint8_t y, uint8_t tile, uint8_t attr);
void fill_tiles(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tile, uint8_t attr) BANKED;
void draw_frame(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t style) BANKED;   // style 0 이중선 1 굵은선
void ui_open(uint8_t top);         // 창을 top 줄부터 (위쪽은 배경 복사)
void ui_close(void);
void tb_open(void);                // 아래 글상자
void tb_close(void);
void tb_place(void);
extern uint8_t tb_shown;
void say(uint16_t sid);            // 글을 다 보이고 A를 기다림
void say_nowait(uint16_t sid);     // 글만 보이고 바로 돌아옴
uint8_t ask(uint16_t sid) BANKED;         // 예/아니오 → 1 예
void pool_reset(uint8_t full);
uint8_t pool_mark(void);
void pool_release(uint8_t m);
uint8_t print_at(uint8_t tgt, uint8_t x, uint8_t y, uint16_t sid);    // 8×16 글자칸으로, 돌려줌: 글자 수
uint8_t print_right(uint8_t tgt, uint8_t xr, uint8_t y, uint16_t sid);  // xr 칸 앞에서 끝나게
void print_num(uint8_t tgt, uint8_t x, uint8_t y, uint16_t v, uint8_t w) BANKED;   // 굵은 숫자, 오른쪽 맞춤
void print_lv(uint8_t tgt, uint8_t x, uint8_t y, uint8_t lv) BANKED;
uint8_t choose(uint8_t tgt, uint8_t x, uint8_t y, uint8_t w, const uint16_t *items, uint8_t n, uint8_t start, uint8_t cancel) BANKED;
void draw_cursor(uint8_t tgt, uint8_t x, uint8_t y, uint8_t on) BANKED;
void hp_bar(uint8_t tgt, uint8_t x, uint8_t y, uint16_t hp, uint16_t mx, uint8_t pal) BANKED;
uint8_t hp_level(uint16_t hp, uint16_t mx) BANKED;

// ── 그림 ──
void screen_clear(void);           // 배경을 흰색으로, 스크롤 0, OBJ 숨김
void load_ui(void);
uint8_t pic_load(uint8_t pic, uint8_t vbank, uint8_t tile0, uint8_t palno);   // 돌려줌: 폭(타일)
void pic_place(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tile0, uint8_t attr);
void pic_screen(uint8_t sp);       // 흰 화면 가운데 그림 (SP_NONE이면 빈 화면)
void hide_sprites(void);

// ── 디지몬 ──
uint16_t mon_stat(const mon_t *m, uint8_t i) BANKED;
#define mon_maxhp(m) mon_stat(m, 0)
void mon_make(mon_t *m, uint8_t sp, uint8_t lv) BANKED;
uint32_t exp_at(uint8_t lv) BANKED;
uint8_t add_mon(mon_t *m) BANKED;         // 0 함께 1 보관함 2 꽉 참
void heal_all(void) BANKED;
uint8_t alive_count(void) BANKED;
uint8_t first_alive(void) BANKED;
void set_seen(uint8_t sp) BANKED;
void set_own(uint8_t sp) BANKED;
uint8_t learn_sig(mon_t *m, uint8_t sp, uint8_t *got) BANKED;   // 진화 뒤 필살기 익히기, 익힌 기술 수

// ── 깃발 ──
uint8_t flag_get(uint16_t f);
void flag_set(uint16_t f);
void flag_clr(uint16_t f);

// ── 필드 ──
#define SCENE_NONE 0
#define SCENE_FIELD 1
#define SCENE_OTHER 2
extern uint8_t scene;
extern uint8_t cur_map;
void field_enter(uint8_t map, uint8_t x, uint8_t y, uint8_t dir, uint8_t run_enter);
void field_restore(void);
void field_loop(void);
void do_warp(uint8_t map, uint8_t x, uint8_t y, uint8_t dir);
extern uint8_t warp_pending, wp_map, wp_x, wp_y, wp_dir;

// ── 스크립트 ──
extern uint8_t vm_result, vm_abort;
void run_script(uint8_t bank, const uint8_t *base, uint16_t off) BANKED;

// ── 저장 ──
uint8_t save_game(void);
uint8_t load_game(void);
uint8_t save_exists(void);

// ── 다른 뱅크 ──
uint8_t battle(uint8_t sp, uint8_t lv, uint8_t kind) BANKED;     // 1 이김 0 짐 2 도망
void evolve_scene(uint8_t slot, uint8_t to) BANKED;
void hatch_scene(uint8_t slot) BANKED;
void evolve_check(void) BANKED;
void start_menu(void) BANKED;
uint8_t party_screen(uint8_t mode) BANKED;   // 0 보기 1 고르기(싸움) 2 도구 쓰기 대상 → 칸 번호, FF 취소
// 음악 (music_drv.inc, 음악 뱅크)
void music_update(void) BANKED;
void music_play(uint8_t s) BANKED;          // 같은 곡이면 그대로
void music_stop(void) BANKED;
void sfx_play(uint8_t id) BANKED;          // SFX_*
void jingle(uint8_t s) BANKED;             // 짧은 곡 한 번 → 원래 곡
#define SFX_SELECT 0
#define SFX_BUMP 1
#define SFX_DOOR 2
#define SFX_HIT 3
#define SFX_HIT2 4
#define SFX_THROW 5
#define SFX_RUN 6
extern uint8_t music_done, cur_song;
uint8_t title_screen(void) BANKED;
void shop_screen(void) BANKED;
void box_screen(void) BANKED;            // 0 새로 1 이어서
uint8_t kid_pick(void) BANKED;
#endif
