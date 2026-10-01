#include <gb/gb.h>
#include <stdint.h>
enum { EV_NONE, EV_TRIG };
extern uint8_t ev_arg, warp_map, warp_x, warp_y;
void field_enter(void) BANKED;
uint8_t field_loop(void) BANKED;
void field_start_pos(void) BANKED;
void menu_open(void) BANKED;
