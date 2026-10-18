#include <stdint.h>
#define MUSIC_BANK 12
enum { MUS_TITLE, MUS_SHIRE, MUS_BATTLE, MUS_BOSS, MUS_STORY1, MUS_STORY2, MUS_STORY3, MUS_END, MUS_NONE = 255 };
void music_play(uint8_t id);
void music_stop(void);
uint8_t music_cur(void);
