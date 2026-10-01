// 「반지 원정」 시험 롬 — GBC 전투 화면 2장 (A: 다음 화면)
#include <gb/gb.h>
#include <gb/cgb.h>
#include <stdint.h>
extern const uint16_t NT0, NT1;
extern const uint8_t TILES0[], TILES1[];
extern const uint8_t MAP0[], MAP1[], ATTR0[], ATTR1[];
void show(uint8_t k) {
    VBK_REG = 1; set_bkg_tiles(0, 0, 20, 18, k ? ATTR1 : ATTR0);   // 타일 속성(어느 칸의 타일인지)
    VBK_REG = 0; set_bkg_tiles(0, 0, 20, 18, k ? MAP1 : MAP0);
}
// 게임보이 4단계 회색 (흰, 밝은회, 어두운회, 검정) — RGB 0~31
const palette_color_t PAL[4] = { RGB(30, 30, 29), RGB(21, 21, 20), RGB(11, 11, 11), RGB(2, 2, 2) };
void main(void) {
    DISPLAY_OFF;
    if (_cpu == CGB_TYPE) set_bkg_palette(0, 1, PAL);
    BGP_REG = 0xE4;                       // 흑백 기계에서도 같은 순서
    VBK_REG = 0; set_bkg_data(0, 0, TILES0);            // 0 = 256개
    if (NT0 < 256) set_bkg_data(0, (uint8_t)NT0, TILES0);
    if (NT1) { VBK_REG = 1; set_bkg_data(0, (uint8_t)NT1, TILES1); VBK_REG = 0; }
    show(0);
    SHOW_BKG; DISPLAY_ON;
    uint8_t k = 0;
    while (1) {
        waitpad(J_A | J_START); waitpadup();
        k ^= 1; show(k);
    }
}
