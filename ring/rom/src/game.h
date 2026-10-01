#include <stdint.h>
enum { ST_HP, ST_ATK, ST_DEF, ST_SPD };
enum { R_NONE, R_WIN, R_LOSE, R_RUN, R_SWAPPED };
typedef struct {
    uint8_t hero, lv; uint16_t xp; int16_t hp;
    uint8_t np, party[4], mlv[4]; uint16_t mxp[4]; int16_t mhp[4];
    uint8_t lembas, herb, shadow, sting, dagger, mithril, cloak, phial, wound;
    int8_t buffAtk, buffDef;
    uint8_t step;
} State;
extern State S;
uint16_t statOf(uint8_t id, uint8_t lv, uint8_t k);
uint16_t stat(uint8_t k);
void swapTo(uint8_t id);
void addMember(uint8_t id, uint8_t lv);
void healAll(void);
uint8_t battle(uint8_t id, uint8_t noRun);
