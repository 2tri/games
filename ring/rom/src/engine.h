// 화면·글자·입력 엔진: 화면 전체를 메모리(fb)에 그리고, 바뀐 타일만 VRAM 으로 보냄
#include <stdint.h>
#define K_A 1
#define K_B 2
#define K_UP 3
#define K_DOWN 4
#define K_LEFT 5
#define K_RIGHT 6
#define K_START 7
#define K_SELECT 8
#define NOCANCEL 255
void eng_init(void);
extern uint8_t field_mode;
void mode_fb(void);
void win_layout(uint8_t rows, uint8_t bx);
uint8_t key_held(void);
void flush(void);
void frame(void);                 // 바뀐 타일 보내고 한 프레임 기다림
void wait_frames(uint8_t n);
uint8_t key_wait(void);
uint8_t key_poll(void);           // 지금 새로 눌린 키(없으면 0)
void rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tone);
void box(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
extern uint8_t blit_ymax;
void blit(uint8_t id, uint8_t x, uint8_t y, uint8_t white);
uint8_t spr_w(uint8_t id);
uint8_t spr_h(uint8_t id);
uint8_t text(const char *s, uint8_t x, uint8_t y, uint8_t tone);
uint8_t text_w(const char *s);
// 글 조립
extern char SB[];
void sb_clear(void);
void sb_add(const char *s);
void sb_num(uint16_t n, uint8_t pad);
void sb_josa(const char *a, const char *b);   // 받침 있으면 a, 없으면 b
// 대사창·고르기
extern void (*scene)(void);       // 지금 장면 다시 그리기
void set_scene(void (*f)(void));
void redraw(void);
void say(const char *s);
uint8_t fget(uint8_t bank, const uint8_t *p);
void fcopy(void *d, uint8_t bank, const void *src, uint16_t n);
void say_far(uint8_t bank, const char *t);
uint8_t choose(const char *q, const char * const *opts, uint8_t n, uint8_t cancel);
uint8_t rnd(void);
uint8_t rnd100(void);
