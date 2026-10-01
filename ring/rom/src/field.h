#include <stdint.h>
#define FIELD_BANK 11
#define N_MAPS 4
#define MT_TREE0 16
#define FIELD_END 10
extern const uint8_t EXCL_SPR[];
enum { MK_WALK, MK_SOLID, MK_GRASS, MK_WATER, MK_SIGN, MK_ITEM };
enum { NK_TALK, NK_INN, NK_SHOP, NK_TRAINER };
typedef struct { uint8_t x, y, kind, dir, arg, arg2, flag; const char *text, *text2; } Npc;
typedef struct { uint8_t x, y; const char *text; } Sign;
typedef struct { uint8_t x, y, kind, flag; } Item;
typedef struct { uint8_t x, y, w, h, step, wmap, wx, wy; } Trig;   // wmap != 255 이면 사건 뒤 그 지도로
typedef struct { uint8_t x, y, map, tx, ty, need; } Exit;   // 밟으면 다른 지도로 (need 단계부터)
typedef struct { uint8_t w, h; const uint8_t *cells; uint8_t nn; const Npc *npc; uint8_t ns; const Sign *sign; uint8_t ni; const Item *item;
                 uint8_t nt; const Trig *trig; uint8_t nw; const uint8_t *wild; uint8_t ne; const Exit *exit; uint8_t rate, sx, sy, sdir, grass; } MapDef;
extern const uint8_t FT_TILES[], FT_N, MTDEF[][5], PLAYER_SPR[], NPC_SPR[];
extern const MapDef MAPS[];
