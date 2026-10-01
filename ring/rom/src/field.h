#include <stdint.h>
#define FIELD_BANK 11
#define N_MAPS 1
#define MT_TREE0 16
enum { MK_WALK, MK_SOLID, MK_GRASS, MK_WATER, MK_SIGN, MK_ITEM };
typedef struct { uint8_t x, y; const char *text; } Npc;
typedef struct { uint8_t x, y; const char *text; } Sign;
typedef struct { uint8_t x, y, kind, flag; } Item;
typedef struct { uint8_t x, y, w, h, step; } Trig;
typedef struct { uint8_t w, h; const uint8_t *cells; uint8_t nn; const Npc *npc; uint8_t ns; const Sign *sign; uint8_t ni; const Item *item;
                 uint8_t nt; const Trig *trig; uint8_t nw; const uint8_t *wild; uint8_t rate, sx, sy, sdir, grass; } MapDef;
extern const uint8_t FT_TILES[], FT_N, MTDEF[][5], PLAYER_SPR[], NPC_SPR[];
extern const MapDef MAPS[];
