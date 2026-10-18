// 이야기 장면 (웹판 story/chapterTitle/lose/save 와 같은 동작)
#include <stdint.h>
void story(const char *place, uint8_t spr, const char * const *lines, uint8_t n);
void chapterTitle(const char *a, const char *b);
void lose(void);
void save(void);
uint8_t load(void);
