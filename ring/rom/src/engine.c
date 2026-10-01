#include <gb/gb.h>
#include <gb/cgb.h>
#include <string.h>
#include "engine.h"
#include "data.h"

// 화면 160×144 = 타일 20×18 = 360장. 타일 n 은 화면의 n 번째 칸 (0~255: VRAM 0번 칸, 256~359: 1번 칸)
static uint8_t fb[360 * 16];
static uint8_t dirty[360];
static uint8_t *ROWB[18];          // 타일 줄마다 fb 시작 (곱셈 없이)
static uint16_t DROW[18];          // 타일 줄마다 dirty 시작
const palette_color_t PAL[4] = { RGB(30, 30, 29), RGB(21, 21, 20), RGB(11, 11, 11), RGB(2, 2, 2) };

// ── 입력: 화면 갱신 인터럽트(VBL)마다 읽어서 새로 눌린 키를 쌓아 둠 → 그리는 중에 누른 키도 놓치지 않음 ──
static volatile uint8_t latch, cur;
static uint16_t rs = 0xACE1;
// 고속 모드에서는 기본 joypad() 가 덜 안정된 값을 읽을 수 있음 → 여러 번 읽어 안정된 값 사용
static uint8_t pad_read(void) {
    uint8_t a = 0, b = 0, i;
    P1_REG = 0x20; for (i = 0; i < 8; i++) a = P1_REG;     // 방향키
    P1_REG = 0x10; for (i = 0; i < 12; i++) b = P1_REG;    // 버튼
    P1_REG = 0x30;
    return (uint8_t)(((~b & 0x0F) << 4) | (~a & 0x0F));
}
static void vbl_isr(void) { uint8_t j = pad_read(); latch |= j & ~cur; cur = j; rs += DIV_REG; }
static const uint8_t KBIT[8] = { J_A, J_B, J_UP, J_DOWN, J_LEFT, J_RIGHT, J_START, J_SELECT };
uint8_t key_poll(void) {
    uint8_t i, n;
    disable_interrupts(); n = latch;
    for (i = 0; i < 8; i++) if (n & KBIT[i]) { latch = n & ~KBIT[i]; enable_interrupts(); return i + 1; }
    enable_interrupts(); return 0;
}

void eng_init(void) {
    uint8_t i, j, row[20];
    DISPLAY_OFF;
    if (_cpu == CGB_TYPE) { cpu_fast(); set_bkg_palette(0, 1, PAL); }
    BGP_REG = 0xE4;
    for (i = 0; i < 18; i++) { ROWB[i] = fb + (uint16_t)i * 320; DROW[i] = (uint16_t)i * 20; }
    for (i = 0; i < 18; i++) {
        for (j = 0; j < 20; j++) row[j] = i * 20 + j >= 256 ? 8 : 0;
        VBK_REG = 1; set_bkg_tiles(0, i, 20, 1, row);
        for (j = 0; j < 20; j++) row[j] = (uint8_t)(i * 20 + j);
        VBK_REG = 0; set_bkg_tiles(0, i, 20, 1, row);
    }
    memset(fb, 0, sizeof fb); memset(dirty, 1, sizeof dirty);
    flush();
    SWITCH_ROM(1);
    add_VBL(vbl_isr);
    SHOW_BKG; DISPLAY_ON;
}
void flush(void) {
    uint16_t t = 0, s, lim;
    while (t < 360) {
        if (!dirty[t]) { t++; continue; }
        s = t; lim = s < 256 ? 256 : 360; if (lim > s + 255) lim = s + 255;
        while (t < lim && dirty[t]) { dirty[t] = 0; t++; }
        if (s < 256) { VBK_REG = 0; set_bkg_data((uint8_t)s, (uint8_t)(t - s), fb + (s << 4)); }
        else { VBK_REG = 1; set_bkg_data((uint8_t)(s - 256), (uint8_t)(t - s), fb + (s << 4)); VBK_REG = 0; }
    }
}
uint8_t rnd(void) { rs ^= rs << 7; rs ^= rs >> 9; rs ^= rs << 8; return (uint8_t)rs; }
uint8_t rnd100(void) { uint8_t r; do r = rnd() & 127; while (r >= 100); return r; }
void frame(void) { flush(); wait_vbl_done(); }
void wait_frames(uint8_t n) { while (n--) frame(); }
uint8_t key_wait(void) { uint8_t k; for (;;) { frame(); k = key_poll(); if (k) return k; } }

// ── 그리기 ──
#define APPLY(p, m, nm, tone) do { if ((tone) & 1) (p)[0] |= (m); else (p)[0] &= (nm); if ((tone) & 2) (p)[1] |= (m); else (p)[1] &= (nm); } while (0)
// 사각형: 타일 한 칸 폭씩, 위에서 아래로 포인터만 옮기며 칠함
void rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h, uint8_t tone) {
    uint8_t x2, y2, xx, yy, o, n, m, nm, col, ty, r, lo, hi; uint8_t *p;
    if (!w || !h || x >= 160 || y >= 144) return;
    x2 = (x + w > 160 || (uint8_t)(x + w) < x) ? 160 : x + w;
    y2 = (y + h > 144 || (uint8_t)(y + h) < y) ? 144 : y + h;
    lo = tone & 1 ? 0xFF : 0; hi = tone & 2 ? 0xFF : 0;
    for (xx = x; xx < x2; xx += n) {
        o = xx & 7; n = 8 - o; if (xx + n > x2) n = x2 - xx;
        m = (uint8_t)(0xFF >> o) & (uint8_t)(0xFF << (8 - o - n)); nm = ~m; col = xx >> 3;
        for (yy = y; yy < y2; yy += r) {
            ty = yy >> 3; r = 8 - (yy & 7); if (yy + r > y2) r = y2 - yy;
            dirty[DROW[ty] + col] = 1;
            p = ROWB[ty] + ((uint16_t)col << 4) + ((yy & 7) << 1);
            if (m == 0xFF) { uint8_t k = r; while (k--) { p[0] = lo; p[1] = hi; p += 2; } }
            else { uint8_t k = r, ml = m & lo, mh = m & hi; while (k--) { p[0] = (p[0] & nm) | ml; p[1] = (p[1] & nm) | mh; p += 2; } }
        }
    }
}
void box(uint8_t x, uint8_t y, uint8_t w, uint8_t h) {
    rect(x, y, w, h, 3); rect(x + 1, y + 1, w - 2, h - 2, 0);
    rect(x + 3, y + 3, w - 6, 1, 3); rect(x + 3, y + h - 4, w - 6, 1, 3); rect(x + 3, y + 3, 1, h - 6, 3); rect(x + w - 4, y + 3, 1, h - 6, 3);
}
uint8_t spr_w(uint8_t id) { return SPRS[id].w * 8; }
uint8_t spr_h(uint8_t id) { return SPRS[id].h * 8; }
// 그림 붙이기 (x, y 는 8의 배수). white=1 이면 하얀 실루엣(맞았을 때 깜빡임)
uint8_t blit_ymax = 144;   // 이 줄부터 아래는 그리지 않음 (대사창 가림)
void blit(uint8_t id, uint8_t x, uint8_t y, uint8_t white) {
    uint8_t w = SPRS[id].w, h = SPRS[id].h, tx, ty, r, m, col, row;
    const uint8_t *d = SPRS[id].data; uint8_t *p;
    SWITCH_ROM(SPRS[id].bank);
    for (ty = 0; ty < h; ty++) {
        row = (y >> 3) + ty;
        for (tx = 0; tx < w; tx++, d += 24) {
            col = (x >> 3) + tx;
            if (col >= 20 || row >= 18 || row >= (blit_ymax >> 3)) continue;
            dirty[DROW[row] + col] = 1;
            p = ROWB[row] + ((uint16_t)col << 4);
            for (r = 0; r < 8; r++, p += 2) {
                m = d[16 + r]; if (!m) continue;
                if (white) { p[0] &= ~m; p[1] &= ~m; }
                else { p[0] = (p[0] & ~m) | d[r * 2]; p[1] = (p[1] & ~m) | d[r * 2 + 1]; }
            }
        }
    }
    SWITCH_ROM(1);
}
// ── 글자 (갈무리9, 롬에 쓰인 글자만) ──
static uint16_t utf8(const char **ps) {
    const uint8_t *s = (const uint8_t *)*ps; uint16_t c = s[0];
    if (c < 0x80) { *ps += 1; return c; }
    if ((c & 0xE0) == 0xC0) { *ps += 2; return ((c & 0x1F) << 6) | (s[1] & 0x3F); }
    *ps += 3; return ((c & 0x0F) << 12) | ((uint16_t)(s[1] & 0x3F) << 6) | (s[2] & 0x3F);
}
static const uint8_t *glyph(uint16_t cp) {
    uint16_t lo = 0, hi = FONT_N, mid;
    if (cp < 127) return FONT_GL + (cp - 32) * 21;
    while (lo < hi) { mid = (lo + hi) >> 1; if (FONT_CP[mid] < cp) lo = mid + 1; else hi = mid; }
    if (lo >= FONT_N || FONT_CP[lo] != cp) lo = '?' - 32;
    return FONT_GL + lo * 21;
}
static uint8_t cw(uint16_t cp) { return glyph(cp)[0]; }
static uint8_t draw_char(uint16_t cp, uint8_t x, uint8_t y, uint8_t tone) {
    const uint8_t *g = glyph(cp); uint8_t w = g[0], r, b0, b1, o, yy, col, ty, c0, c1, c2; uint8_t *p;
    o = x & 7; col = x >> 3;
    for (r = 0; r < 10; r++) {
        b0 = g[1 + r * 2]; b1 = g[2 + r * 2];
        if (!(b0 | b1)) continue;
        yy = y + 2 + r; if (yy >= 144) break;
        ty = yy >> 3;
        c0 = b0 >> o; c1 = (uint8_t)(o ? (b0 << (8 - o)) : 0) | (b1 >> o); c2 = o ? (uint8_t)(b1 << (8 - o)) : 0;
        p = ROWB[ty] + ((uint16_t)col << 4) + ((yy & 7) << 1);
        if (c0) { APPLY(p, c0, ~c0, tone); dirty[DROW[ty] + col] = 1; }
        if (c1 && col < 19) { APPLY(p + 16, c1, ~c1, tone); dirty[DROW[ty] + col + 1] = 1; }
        if (c2 && col < 18) { APPLY(p + 32, c2, ~c2, tone); dirty[DROW[ty] + col + 2] = 1; }
    }
    return w;
}
uint8_t text(const char *s, uint8_t x, uint8_t y, uint8_t tone) { while (*s) x += draw_char(utf8(&s), x, y, tone); return x; }
uint8_t text_w(const char *s) { uint8_t w = 0; while (*s) w += cw(utf8(&s)); return w; }

// ── 글 조립 ──
char SB[200]; static uint8_t sbn;
void sb_clear(void) { sbn = 0; SB[0] = 0; }
void sb_add(const char *s) { while (*s && sbn < 198) SB[sbn++] = *s++; SB[sbn] = 0; }
void sb_num(uint16_t n, uint8_t pad) {
    char t[6]; uint8_t k = 0;
    do { t[k++] = '0' + n % 10; n /= 10; } while (n);
    while (pad > k) { SB[sbn++] = ' '; pad--; }
    while (k) SB[sbn++] = t[--k]; SB[sbn] = 0;
}
void sb_josa(const char *a, const char *b) {
    uint8_t i = sbn; const char *p; uint16_t c;
    while (i && ((uint8_t)SB[i - 1] & 0xC0) == 0x80) i--;
    if (i) i--;
    p = SB + i; c = utf8(&p);
    sb_add(c >= 0xAC00 && c <= 0xD7A3 && (c - 0xAC00) % 28 ? a : b);
}

// ── 대사창: 두 줄씩, 한 글자씩 ──
void (*scene)(void);
void redraw(void) { if (scene) scene(); }
static uint8_t LS[10], LE[10], NL;
static void push_line(uint8_t s, uint8_t e) { if (NL < 10) { LS[NL] = s; LE[NL] = e; NL++; } }
static void wrap(const char *s, uint8_t maxw) {
    uint8_t ls = 0, le = 0, lw = 0, i = 0, ws, ww, nw; const char *p; uint16_t cp;
    NL = 0;
    for (;;) {
        ws = i; ww = 0;
        while (s[i] && s[i] != ' ' && s[i] != '\n') { p = s + i; cp = utf8(&p); ww += cw(cp); i = (uint8_t)(p - s); }
        nw = (le == ls) ? ww : lw + cw(' ') + ww;
        if (le != ls && nw > maxw) { push_line(ls, le); ls = ws; lw = ww; } else lw = nw;
        le = i;
        if (!s[i]) { push_line(ls, le); return; }
        if (s[i] == '\n') { push_line(ls, le); i++; ls = le = i; lw = 0; continue; }
        i++;
    }
}
static void more_mark(uint8_t on) {
    if (on) { rect(148, 133, 5, 2, 3); rect(149, 135, 3, 1, 3); rect(150, 136, 1, 1, 3); } else rect(148, 133, 5, 4, 0);
}
static uint8_t type_line(const char *s, uint8_t a, uint8_t b, uint8_t y, uint8_t fast) {
    uint8_t x = 8; const char *p = s + a, *e = s + b;
    while (p < e) {
        x += draw_char(utf8(&p), x, y, 3);
        if (!fast) { frame(); if (key_poll() == K_A) fast = 1; }
    }
    return fast;
}
static char SAYBUF[200];
void say(const char *s0) {
    uint8_t i, fast, k, t;
    strcpy(SAYBUF, s0);     // SB 로 만든 글을 넘겨도 안전하게
    wrap(SAYBUF, 144);
    for (i = 0; i < NL; i += 2) {
        box(0, 96, 160, 48);
        fast = type_line(SAYBUF, LS[i], LE[i], 105, 0);
        if (i + 1 < NL) type_line(SAYBUF, LS[i + 1], LE[i + 1], 121, fast);
        for (t = 0;; t++) {
            if ((t & 15) == 0) more_mark(t & 16);
            frame(); k = key_poll();
            if (k == K_A || k == K_B) break;
        }
    }
}
uint8_t choose(const char *q, const char **opts, uint8_t n, uint8_t cancel) {
    uint8_t w = 0, h, x, y, i = 0, k, tw;
    for (k = 0; k < n; k++) { tw = text_w(opts[k]); if (tw > w) w = tw; }
    w += 22; h = n * 14 + 10; x = 160 - w; y = 96 - h;
    box(0, 96, 160, 48);
    if (q) { strcpy(SAYBUF, q); wrap(SAYBUF, 144); type_line(SAYBUF, LS[0], LE[0], 105, 1); if (NL > 1) type_line(SAYBUF, LS[1], LE[1], 121, 1); }
    box(x, y, w, h);
    for (k = 0; k < n; k++) text(opts[k], x + 14, y + 6 + k * 14, 3);
    for (;;) {
        text("▶", x + 5, y + 6 + i * 14, 3);
        k = key_wait();
        if (k == K_UP || k == K_DOWN) { rect(x + 5, y + 6 + i * 14, 9, 13, 0); i = k == K_UP ? (i + n - 1) % n : (i + 1) % n; }
        else if (k == K_A || k == K_START) break;
        else if (k == K_B && cancel != NOCANCEL) { i = cancel; break; }
    }
    redraw();
    return i;
}
