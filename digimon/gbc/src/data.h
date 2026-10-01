// 디지몬 GBC — 자료 구조 (tools/build.py 가 이 모양으로 데이터를 만든다)
#ifndef DATA_H
#define DATA_H
#include <stdint.h>

typedef struct { uint8_t bank; const uint8_t *ptr; } farptr_t;

typedef struct {
    uint8_t w, h;                 // 지도 크기 (16×16 칸)
    uint8_t border, split, border2;   // 바깥 칸: x >= split 이면 border2
    uint8_t n_open; const uint8_t *opens;   // 바깥에 보이는 길: x0,y0,x1,y1(부호 있음), 칸
    const uint8_t *cells;
    uint8_t n_mt; const uint8_t *mt;        // 칸마다 타일4·속성4·성질1 (9바이트)
    uint8_t n_t0; const uint8_t *t0;        // VRAM 0번 칸 152~ 타일
    uint8_t n_t1; const uint8_t *t1;        // VRAM 1번 칸 64~ 타일
    const uint16_t *pal;                    // 배경 팔레트 1~7 (28색)
    uint8_t n_npc; const uint8_t *npcs;     // 15바이트씩
    uint8_t n_sign; const uint8_t *signs;   // x,y,스크립트(2)
    uint8_t n_warp; const uint8_t *warps;   // x,y,지도,tx,ty,방향
    uint8_t n_trig; const uint8_t *trigs;   // x,y,w,h,한번(2),필요(2),아니면(2),스크립트(2)
    uint8_t enc_rate, n_enc; const uint8_t *enc;  // 디지몬,최소,최대,무게
    const uint8_t *script;
    uint16_t on_enter;
    uint8_t n_objpal; const uint16_t *objpal;
    uint8_t n_spr; const uint8_t *spr;      // OBJ 타일 (1번 칸 24~)
    uint16_t name;
    uint8_t t1_base;                        // 1번 VRAM 지도 타일 시작 (그 앞은 OBJ)
    uint8_t song;                           // 배경 음악 (SONG_*)
} map_t;

typedef struct { uint8_t bank; const map_t *map; } farmap_t;

typedef struct {
    uint8_t tier, attr;
    uint8_t base[4];              // 체력 공격 방어 스피드
    uint8_t exp;
    uint8_t evo_to, evo_lv, evo_need;   // need: FF 없음, FE 사건, 그 밖 문장 번호
    uint8_t sig[3];
    uint16_t name, grade, type;
    uint8_t front, back;
    uint8_t dark_to, dark;        // 자기 문장 없이 진화하면 이것으로 (FF 없음) · 1 = 암흑 진화체 (폭주)
} species_t;

typedef struct { uint16_t name; uint8_t power, acc, pp, eff, kind; } move_t;   // eff 0 피해 1 상대방어↓ 2 내방어↑, kind 0 기본기 1 필살기

// 지도 칸 성질
#define MT_SOLID 1
#define MT_GRASS 2
#define MT_LEDGE 4      // 한쪽 턱: 아래로만 뛰어내림

// NPC 바이트 위치
#define NPC_X 0
#define NPC_Y 1
#define NPC_BASE 2
#define NPC_NFR 3
#define NPC_PAL 4
#define NPC_BASE2 5
#define NPC_NFR2 6
#define NPC_PAL2 7
#define NPC_ALTKID 8
#define NPC_DIR 9
#define NPC_FLAGS 10
#define NPC_COND 11
#define NPC_HIDEKID 13
#define NPC_SCRIPT 14
#define NPC_SIZE 16

extern const farptr_t FONTS[], STRTAB[], PICTAB[];
extern const farmap_t MAPTAB[];
extern const uint8_t MISC_BANK;
extern const uint8_t CHARFLAG[];
extern const species_t SPECIES[];
extern const move_t MOVES[];
extern const uint8_t TIER_BASIC[];
extern const uint16_t KID_CRESTS[], KID_DESC[];
extern const uint16_t ATTR_NAME[], KID_NAME[], KID_PAL[], IT_NAME[], IT_DESC[], CREST_NAME[], TITLE_PAL[], DIGCH[], JOSACH[];
extern const uint8_t KID_PARTNER[], KID_BABY[], EGGS[], IT_HEAL[], IT_KIND[], BMAP[];
extern const uint16_t IT_PRICE[];
extern const uint8_t ui_tiles[], title_tiles[], title_tiles1[], title_map[], title_attr[], title_alt[], kid_spr[], opening[];
#endif
