#include <stdint.h>
enum { ST_HP, ST_ATK, ST_DEF, ST_SPD };
enum { R_NONE, R_WIN, R_LOSE, R_RUN, R_SWAPPED, R_RESCUE };
#include <gb/gb.h>
#define MAX(a, b) ((int16_t)(a) > (int16_t)(b) ? (int16_t)(a) : (int16_t)(b))
#define MIN(a, b) ((int16_t)(a) < (int16_t)(b) ? (int16_t)(a) : (int16_t)(b))
typedef struct {
    uint8_t hero, lv; uint16_t xp; int16_t hp;
    uint8_t np, party[5], mlv[5]; uint16_t mxp[5]; int16_t mhp[5];
    uint8_t lembas, herb, shadow, sting, dagger, mithril, cloak, phial, wound;
    int8_t buffAtk, buffDef;
    uint8_t step, gollum, done;
    uint8_t map, x, y, dir, flags[16];
    uint16_t money;
} State;
extern State S;
uint16_t statOf(uint8_t id, uint8_t lv, uint8_t k) BANKED;
uint16_t stat(uint8_t k) BANKED;
void swapTo(uint8_t id) BANKED;
void addMember(uint8_t id, uint8_t lv) BANKED;
void removeMember(uint8_t id) BANKED;
uint8_t has(uint8_t id) BANKED;
void healAll(void) BANKED;
uint8_t battle(uint8_t id, uint8_t noRun, uint8_t turns) BANKED;
void rescue_end(void) BANKED;
void party_hurt(uint8_t d) BANKED;
void party_floor_third(void) BANKED;
void frodo_cap_hp(void) BANKED;
void frodo_full_hp(void) BANKED;
void keep_party(void) BANKED;
void solo_party(uint8_t id) BANKED;
void restore_party(void) BANKED;
uint8_t foe_lv(uint8_t id) BANKED;
int16_t party_hp(uint8_t i) BANKED;
void party_line(uint8_t i) BANKED;
void party_info(uint8_t i) BANKED;
void heal_lead(uint8_t n) BANKED;
