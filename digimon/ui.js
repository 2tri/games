// 금판식 화면 부품 — 디지몬스터(포켓몬 금 한글판 기반) 화면을 재서 같은 자리·크기로 새로 그린 것
//  · 한글: 갈무리11 Condensed 비트맵 (글자 폭 8, 높이 11) — font.js
//  · 숫자·:L·HP: 표시는 금판 모양을 보고 새로 찍은 7×7 굵은 글씨
(function (root) {
  'use strict';
  const K = '#181818', PAPER = '#f8f8f8';
  const PAL = { hpG: '#18a830', hpG2: '#a8e0a0', hpY: '#f8b800', hpY2: '#f8e098', hpR: '#e83818', hpR2: '#f8a890', tag: '#f8d070', exp: '#4890f0' };

  // ── 한글·영문 글자 (갈무리11 Condensed) ──
  const F = root.DigiFontData;
  const cache = {};
  function glyph(ch) {
    if (cache[ch]) return cache[ch];
    const d = F[ch] || F['?'];
    const [dw, w, h, xo, yo, hex, hl] = d, rows = [];
    for (let i = 0; i < h; i++) { const v = parseInt(hex.substr(i * hl, hl), 16), bits = hl * 4; const r = []; for (let x = 0; x < w; x++) r.push((v >> (bits - 1 - x)) & 1); rows.push(r); }
    return (cache[ch] = { dw, w, h, xo, yo, rows });
  }
  // y = 글줄 맨 위. 한글 높이 11, 기준선은 y+11
  function text(g, str, x, y, col) {
    g.fillStyle = col || K; let cx = x;
    for (const ch of str) {
      if (ch === ' ') { cx += 4; continue; }
      const gl = glyph(ch), top = y + 11 - gl.h - gl.yo;
      for (let j = 0; j < gl.h; j++) for (let i = 0; i < gl.w; i++) if (gl.rows[j][i]) g.fillRect(cx + gl.xo + i, top + j, 1, 1);
      cx += gl.dw;
    }
    return cx;
  }
  const textWidth = (str) => { let w = 0; for (const ch of str) w += ch === ' ' ? 4 : glyph(ch).dw; return w; };

  // ── 굵은 숫자 7×7 (HP 숫자·레벨) ──
  const DIG = {
    '0': ['.#####.', '##...##', '##..###', '##.#.##', '###..##', '##...##', '.#####.'],
    '1': ['..##...', '.###...', '..##...', '..##...', '..##...', '..##...', '.####..'],
    '2': ['.#####.', '##...##', '.....##', '..####.', '.##....', '##.....', '#######'],
    '3': ['######.', '.....##', '....##.', '..####.', '.....##', '##...##', '.#####.'],
    '4': ['...###.', '..####.', '.##.##.', '##..##.', '#######', '....##.', '....##.'],
    '5': ['######.', '##.....', '######.', '.....##', '.....##', '##...##', '.#####.'],
    '6': ['.#####.', '##.....', '######.', '##...##', '##...##', '##...##', '.#####.'],
    '7': ['#######', '##...##', '....##.', '...##..', '..##...', '..##...', '..##...'],
    '8': ['.#####.', '##...##', '##...##', '.#####.', '##...##', '##...##', '.#####.'],
    '9': ['.#####.', '##...##', '##...##', '.######', '.....##', '.....##', '.#####.'],
    '/': ['......#', '.....#.', '....#..', '...#...', '..#....', '.#.....', '#......'],
    'L': ['##.....', '##.....', '##.....', '##.....', '##.....', '##.....', '#####..'],
    ':': ['.', '.', '#', '.', '.', '#', '.'],
    'N': ['##...##', '###..##', '####.##', '##.####', '##..###', '##...##', '##...##'],
    'o': ['.......', '.......', '.#####.', '##...##', '##...##', '##...##', '.#####.'],
    '.': ['..', '..', '..', '..', '..', '##', '##'],
    'P': ['######.', '##...##', '##...##', '######.', '##.....', '##.....', '##.....']
  };
  function num(g, str, x, y, col) {
    g.fillStyle = col || K; let cx = x;
    for (const ch of String(str)) {
      if (ch === ' ') { cx += 8; continue; }
      const d = DIG[ch]; if (!d) { cx += 8; continue; }
      d.forEach((r, j) => { for (let i = 0; i < r.length; i++) if (r[i] === '#') g.fillRect(cx + i, y + j, 1, 1); });
      cx += ch === ':' ? 2 : ch === 'L' ? 6 : ch === '.' ? 3 : 8;
    }
    return cx;
  }
  // 레벨: 「:L5」
  function level(g, lv, x, y) { let cx = num(g, ':', x, y); cx = num(g, 'L', cx, y); num(g, String(lv), cx, y); }
  // 성별 기호 (7×8)
  const SEX = { m: ['..####', '....##', '...#.#', '.###..', '#...#.', '#...#.', '.###..'], f: ['.###.', '#...#', '#...#', '.###.', '..#..', '#####', '..#..'] };
  function sex(g, s, x, y) { g.fillStyle = K; SEX[s].forEach((r, j) => { for (let i = 0; i < r.length; i++) if (r[i] === '#') g.fillRect(x + i, y + j, 1, 1); }); }

  // ── HP 막대: 「HP:」 표시 16×6 + 막대 48×4 + 오른쪽 끝 마개 ──
  function hpBar(g, x, y, ratio) {
    g.fillStyle = K; g.fillRect(x, y, 16, 6); g.fillRect(x + 1, y - 1, 15, 1); g.fillRect(x + 1, y + 6, 15, 0);
    g.fillStyle = PAL.tag;                                        // H P :
    [[2, 1], [2, 2], [2, 3], [2, 4], [3, 2], [4, 1], [4, 2], [4, 3], [4, 4], [6, 1], [6, 2], [6, 3], [6, 4], [7, 1], [8, 1], [8, 2], [7, 3], [11, 1], [11, 4]].forEach(([i, j]) => g.fillRect(x + i, y + j, 1, 1));
    g.fillStyle = K; g.fillRect(x + 16, y + 5, 48, 1); g.fillRect(x + 64, y, 3, 6); g.fillRect(x + 64, y - 1, 2, 1);   // 아래 선 + 끝 마개
    const w = Math.max(0, Math.round(48 * ratio));
    const [c1, c2] = ratio > .5 ? [PAL.hpG, PAL.hpG2] : ratio > .2 ? [PAL.hpY, PAL.hpY2] : [PAL.hpR, PAL.hpR2];
    g.fillStyle = PAPER; g.fillRect(x + 16, y + 1, 48, 4);
    g.fillStyle = c2; g.fillRect(x + 16, y + 1, w, 4);
    g.fillStyle = c1; g.fillRect(x + 16, y + 2, w, 2);
  }
  // 상대 쪽 꺾쇠: 왼쪽 굵은 세로줄 → 아래 가로줄 → 오른쪽 끝 삼각
  function bracketFoe(g, x, y) { // x,y = 세로줄 왼쪽 위 (디지몬스터: 10,15)
    g.fillStyle = K;
    g.fillRect(x, y, 4, 12); g.fillRect(x + 1, y + 12, 4, 1); g.fillRect(x + 2, y + 13, 4, 1);
    g.fillRect(x + 3, y + 14, 74, 1); g.fillRect(x + 4, y + 15, 72, 0);
    for (let i = 0; i < 4; i++) g.fillRect(x + 70 + i, y + 11 + i, 6 - i, 1);  // 끝 삼각
    g.fillRect(x + 70, y + 14, 8, 1);
  }
  // 내 쪽 꺾쇠: 오른쪽 굵은 세로줄 → 아래 가로줄 → 왼쪽 끝 삼각
  function bracketMe(g, x, y) { // x,y = 세로줄 왼쪽 위 (디지몬스터: 145,73)
    g.fillStyle = K;
    g.fillRect(x, y + 1, 4, 19); g.fillRect(x - 1, y, 3, 1);
    g.fillRect(x - 1, y + 20, 4, 1); g.fillRect(x - 2, y + 21, 4, 0);
    g.fillRect(x - 73, y + 20, 72, 1);
    for (let i = 0; i < 4; i++) g.fillRect(x - 73 - (3 - i) + (3 - i), y + 17 + i, 0, 1);
    for (let i = 0; i < 4; i++) g.fillRect(x - 73 + 3 - i, y + 17 + i, 4 + i, 1);  // 끝 삼각
  }
  function expBar(g, x, y, ratio) { g.fillStyle = PAL.exp; const w = Math.round(48 * ratio); g.fillRect(x + 48 - w, y, w, 2); }

  // ── 테두리 ──
  // 글상자: 바깥 가는 선 + 1칸 틈 + 안쪽 두꺼운 선, 모서리 둥글게
  function frame(g, x, y, w, h) {
    g.fillStyle = PAPER; g.fillRect(x, y, w, h);
    g.fillStyle = K;
    g.fillRect(x + 2, y, w - 4, 1); g.fillRect(x + 2, y + h - 1, w - 4, 1); g.fillRect(x, y + 2, 1, h - 4); g.fillRect(x + w - 1, y + 2, 1, h - 4);
    g.fillRect(x + 1, y + 1, 1, 1); g.fillRect(x + w - 2, y + 1, 1, 1); g.fillRect(x + 1, y + h - 2, 1, 1); g.fillRect(x + w - 2, y + h - 2, 1, 1);
    g.fillRect(x + 3, y + 2, w - 6, 2); g.fillRect(x + 3, y + h - 4, w - 6, 2); g.fillRect(x + 2, y + 3, 2, h - 6); g.fillRect(x + w - 4, y + 3, 2, h - 6);
  }
  // 전투 메뉴 칸: 2칸 굵기 한 줄, 모서리 둥글게
  function frame2(g, x, y, w, h) {
    g.fillStyle = PAPER; g.fillRect(x, y, w, h);
    g.fillStyle = K;
    g.fillRect(x + 2, y, w - 4, 2); g.fillRect(x + 2, y + h - 2, w - 4, 2); g.fillRect(x, y + 2, 2, h - 4); g.fillRect(x + w - 2, y + 2, 2, h - 4);
    g.fillRect(x + 1, y + 1, 2, 2); g.fillRect(x + w - 3, y + 1, 2, 2); g.fillRect(x + 1, y + h - 3, 2, 2); g.fillRect(x + w - 3, y + h - 3, 2, 2);
  }
  // 커서 ▶ (4×7) 과 다음 ▼ (7×4)
  function cursor(g, x, y) { g.fillStyle = K; for (let i = 0; i < 4; i++) g.fillRect(x + i, y + i, 1, 7 - i * 2); }
  function more(g, x, y) { g.fillStyle = K; for (let j = 0; j < 4; j++) g.fillRect(x + j, y + j, 7 - j * 2, 1); }
  // 아래 대사창 (두 줄): 디지몬스터 위치 그대로 — 글줄 y 104, 120
  function say(g, a, b, arrow) { frame(g, 0, 96, 160, 48); text(g, a, 8, 104); if (b) text(g, b, 8, 120); if (arrow !== false) more(g, 145, 136); }

  root.DigiUI = { K, PAPER, PAL, text, textWidth, num, level, sex, hpBar, bracketFoe, bracketMe, expBar, frame, frame2, cursor, more, say };
})(typeof window !== 'undefined' ? window : globalThis);
