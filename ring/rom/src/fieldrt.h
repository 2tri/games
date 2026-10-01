#include <stdint.h>
enum { EV_NONE, EV_TRIG, EV_WILD };
extern uint8_t ev_arg;
void field_enter(void);
uint8_t field_loop(void);
void field_start_pos(void);
