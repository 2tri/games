// 「반지 원정」 도트 — 포켓몬 금·은 방식 규칙
//  · 필드 인물 16×16(2등신), 전투 그림 32×32, 타일 16×16
//  · 그림 하나에 색 4개(외곽선 + 진한색 + 밝은색 + 피부/흰색)
//  · 눈은 세로 2점, 입은 생략, 인물마다 특징 하나를 크게
(function (root) {
  'use strict';
  const K = '#181018';

  // 글자 그림을 점 배열로: 한 글자 = 한 점, '.' = 비움
  function art(rows, pal) {
    const h = rows.length, w = rows[0].length, p = new Array(w * h).fill(0);
    rows.forEach((r, y) => { for (let x = 0; x < w; x++) { const c = r[x]; if (c !== '.') p[y * w + x] = c === 'k' ? K : pal[c]; } });
    return { w, h, p };
  }
  // 도형 그리기 (32×32 전투 그림용)
  function mk(w, h) { return { w, h, p: new Array(w * h).fill(0) }; }
  function px(s, x, y, c) { if (x >= 0 && y >= 0 && x < s.w && y < s.h) s.p[y * s.w + x] = c; }
  function rect(s, x, y, w, h, c) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) px(s, x + i, y + j, c); }
  function ell(s, cx, cy, rx, ry, c) {
    for (let y = Math.floor(cy - ry); y <= Math.ceil(cy + ry); y++) for (let x = Math.floor(cx - rx); x <= Math.ceil(cx + rx); x++) {
      const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry; if (dx * dx + dy * dy <= 1) px(s, x, y, c);
    }
  }
  function line(s, x0, y0, x1, y1, c, w) {
    w = w || 1; const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1;
    for (let i = 0; i <= n; i++) { const x = Math.round(x0 + (x1 - x0) * i / n), y = Math.round(y0 + (y1 - y0) * i / n); rect(s, x - (w >> 1), y - (w >> 1), w, w, c); }
  }
  function get(s, x, y) { return (x < 0 || y < 0 || x >= s.w || y >= s.h) ? 0 : s.p[y * s.w + x]; }
  function outline(s) {
    const o = s.p.slice();
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) {
      if (get(s, x, y)) continue;
      if (get(s, x + 1, y) || get(s, x - 1, y) || get(s, x, y + 1) || get(s, x, y - 1)) o[y * s.w + x] = K;
    }
    s.p = o; return s;
  }

  const SKIN = '#f8c8a0';

  // ── 필드 인물 16×16 (앞모습) ─────────────────────
  const WALK = {
    frodo: art([
      '................',
      '...kk.kkk.kk....',
      '..kHHkHHHkHHk...',
      '..kHHHHHHHHHHk..',
      '..kHHHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kSSkSSSSkSSk..',
      '..kSSkSSSSkSSk..',
      '...kSSSSSSSSk...',
      '....kkkCCkkk....',
      '...kCCCyyCCCk...',
      '..kSCCCCCCCCSk..',
      '..kkCCCCCCCCkk..',
      '...kCCCCCCCCk...',
      '..kSSSk..kSSSk..',
      '..kkkk....kkkk..'], { H: '#4a3020', S: SKIN, C: '#6a8a5a', y: '#f0c040' }),
    sam: art([
      '................',
      '....kkkkkkk.....',
      '...kHHHkHHHk....',
      '..kHHHHHHHHHk...',
      '..kHHHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kSSkSSSSkSSk..',
      '..kSSkSSSSkSSk..',
      '...kSSSSSSSSk...',
      '....kkkkkkkk....',
      '...kHLLLLLLHkk..',
      '..kSHLLLLLLHkHk.',
      '..kkHLLLLLLHkHk.',
      '...kHHHHHHHHkk..',
      '..kSSSk..kSSSk..',
      '..kkkk....kkkk..'], { H: '#8a5a30', S: SKIN, L: '#e8d8b0' }),
    aragorn: art([
      '....kkkkkkkk....',
      '...kHHHHHHHHk...',
      '..kHHHHHHHHHHk..',
      '..kHHHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSHHHHHHSHk..',
      '...kkSSSSSSkk...',
      '...kCkkkkkkCk.k.',
      '..kCCCCCCCCCCkwk',
      '..kSCCCCCCCCSkwk',
      '..kkCCCCCCCCkkwk',
      '...kCCCkkCCCk.k.',
      '...kHHk..kHHk...',
      '....kk....kk....'], { H: '#3a2a20', S: SKIN, C: '#3e6a48', w: '#e8f0f8' }),
    legolas: art([
      '....kkkkkkkk....',
      '...kHHHHHHHHk...',
      '..kHHHHHHHHHHk..',
      '.kkHHHHHHHHHHkk.',
      '.kSkHSSSSSSHkSk.',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSSSSSSSSHk..',
      '..kHkSSSSSSkHk..',
      '.k.kkkkkkkkkk...',
      'kbkkCCCCCCCCk...',
      'kbkSCCCCCCCCSk..',
      'kbkkCCCCCCCCkk..',
      '.k.kCCCkkCCCk...',
      '...kbbk..kbbk...',
      '....kk....kk....'], { H: '#f0d878', S: SKIN, C: '#5a9a48', b: '#a06a30' }),
    gimli: art([
      '................',
      '.....kkkkkk.....',
      '....kMMMMMMk....',
      '...kMMMMMMMMk...',
      '..kyyyyyyyyyyk..',
      '..kSSSSSSSSSSk..',
      '..kSSkSSSSkSSk..',
      '..kSSkSSSSkSSk..',
      '..kBBSSSSSSBBk.k',
      '.kBBBBBBBBBBBkMk',
      'kMkBBBBBBBBBkMMk',
      'kSkMBBBBBBBMkok.',
      'kkkMMBBBBBMMkok.',
      '..kMMMkBkMMMkok.',
      '..kHHHk..kHHHkk.',
      '..kkkk....kkkk..'], { M: '#8890a0', S: SKIN, y: '#e0b040', B: '#c04a20', H: '#5a3a24', o: '#6a4020' }),
    gandalf: art([
      '......kk........',
      '.....kHHk.......',
      '....kHHHk.......',
      '...kHHHHHk......',
      '.kkHHHHHHHkk....',
      'kHHHHHHHHHHHHk..',
      '.kkSSkSSkSSkk...',
      '..kSSkSSkSSk....',
      '..kWWWWWWWWk....',
      '.kkWWWWWWWWkk...',
      'kHkHWWWWWWHkHk..',
      'kSkHHWWWWHHkSk..',
      'kokHHHWWHHHkok..',
      'kok.kHHHHHk.kok.',
      'kok.kHHHHHk.....',
      'kk...kkkkk......'], { H: '#9090a0', S: SKIN, W: '#f0f0f0', o: '#7a5030' })
  };

  // ── 전투 그림 32×32 ─────────────────────────
  const BATTLE = {};
  BATTLE.wolf = function () {
    const s = mk(32, 32), F = '#8a8078', F2 = '#5e5650', L = '#c8bcb0';
    line(s, 24, 17, 29, 9, F2, 3);                         // 꼬리
    rect(s, 12, 22, 3, 7, F2); rect(s, 22, 22, 3, 7, F2);  // 먼 다리
    ell(s, 18, 19, 9, 5, F); ell(s, 18, 22, 7, 2, L);      // 몸
    rect(s, 9, 22, 3, 7, F); rect(s, 25, 22, 3, 7, F);     // 앞다리
    ell(s, 9, 16, 5, 5, F);                                // 목·머리
    rect(s, 2, 14, 6, 3, F); rect(s, 2, 17, 5, 1, L);      // 주둥이
    px(s, 2, 14, K); px(s, 1, 15, K);                      // 코
    rect(s, 7, 8, 2, 3, F); rect(s, 11, 8, 2, 3, F);       // 귀
    px(s, 7, 13, '#f0c030'); px(s, 8, 13, K);              // 눈
    return outline(s);
  };
  BATTLE.orc = function () {
    const s = mk(32, 32), SK = '#78904c', A = '#4e4238', M = '#6a6a74';
    rect(s, 10, 25, 4, 5, A); rect(s, 18, 25, 4, 5, A);
    ell(s, 16, 20, 9, 6, A); rect(s, 9, 17, 14, 2, M);     // 몸·어깨
    ell(s, 6, 20, 2.5, 5, SK); ell(s, 26, 17, 2.5, 4, SK); // 팔
    rect(s, 25, 3, 5, 9, M); rect(s, 27, 11, 1, 4, A);     // 칼
    ell(s, 16, 11, 7, 6, SK);                              // 머리
    rect(s, 10, 4, 12, 4, M); px(s, 16, 3, M);             // 투구
    rect(s, 12, 10, 3, 1, '#e83c28'); rect(s, 17, 10, 3, 1, '#e83c28');
    rect(s, 13, 14, 6, 1, K); px(s, 13, 13, '#f0ecd8'); px(s, 18, 13, '#f0ecd8'); // 입·엄니
    return outline(s);
  };
  BATTLE.rider = function () {
    const s = mk(32, 32), C = '#2c2838', C2 = '#1a1822';
    for (let y = 9; y < 31; y++) { const w = Math.min(12, 4 + (y - 9) * 0.45); rect(s, Math.round(16 - w), y, Math.round(w * 2), 1, C); }
    rect(s, 16, 12, 1, 18, C2); rect(s, 10, 22, 1, 8, C2); rect(s, 22, 20, 1, 10, C2);
    ell(s, 16, 9, 6, 6, C); ell(s, 16, 11, 4, 4, '#08060c');
    px(s, 14, 11, '#f4ec9c'); px(s, 18, 11, '#f4ec9c');
    line(s, 24, 16, 29, 3, '#c8ccd8', 1); rect(s, 22, 15, 4, 1, '#6a6a74');
    return outline(s);
  };
  BATTLE.frodoBack = function () { // 전투 때 내 쪽 인물 (뒷모습)
    const s = mk(32, 32), H = '#4a3020', C = '#6a8a5a', C2 = '#4e6a44';
    for (let y = 16; y < 32; y++) { const w = Math.min(13, 8 + (y - 16) * 0.5); rect(s, Math.round(15 - w), y, Math.round(w * 2) + 1, 1, C); } // 망토
    rect(s, 15, 18, 1, 14, C2); rect(s, 8, 24, 1, 8, C2); rect(s, 22, 24, 1, 8, C2);
    ell(s, 15, 10, 9, 8, H);                                // 뒷머리
    for (const [x, y] of [[9, 4], [13, 2], [18, 3], [22, 6], [8, 9], [23, 11]]) ell(s, x, y, 2, 2, H); // 곱슬
    for (const [x, y] of [[11, 7], [16, 6], [19, 9], [13, 12]]) px(s, x, y, '#2e1c12');
    ell(s, 5, 12, 1.5, 2, SKIN); ell(s, 25, 12, 1.5, 2, SKIN); // 귀
    rect(s, 26, 20, 2, 6, SKIN);                            // 손 + 짧은 칼
    line(s, 27, 19, 30, 10, '#dce8f4', 1); px(s, 27, 20, '#b0903c'); px(s, 28, 19, '#b0903c');
    return outline(s);
  };

  // ── 지도 타일 16×16 ──────────────────────────
  const G1 = '#c8e8a0', G2 = '#90c070', G3 = '#4a7a40', P1 = '#f0dfb0', P2 = '#d4b880';
  const TILE = {
    grass: art([
      '................', '..g.............', '.g.g.......g....', '..........g.g...', '................', '................',
      '.....g..........', '....g.g.........', '................', '...........g....', '..........g.g...', '................',
      '..g.............', '.g.g......g.....', '.........g.g....', '................'].map(r => r.replace(/\./g, '_')), { _: G1, g: G2 }),
    tall: art([
      '_g__g__g__g__g__', 'gGggGggGggGggGg_', 'GGgGGgGGgGGgGGg_', 'dGGdGGdGGdGGdGG_', '_d__d__d__d__d__', '________________',
      '_g__g__g__g__g__', 'gGggGggGggGggGg_', 'GGgGGgGGgGGgGGg_', 'dGGdGGdGGdGGdGG_', '_d__d__d__d__d__', '________________',
      '_g__g__g__g__g__', 'gGggGggGggGggGg_', 'GGgGGgGGgGGgGGg_', 'dGGdGGdGGdGGdGG_'], { _: G1, g: G2, G: '#70a858', d: G3 }),
    path: art([
      '________________', '________________', '___p____________', '________________', '__________p_____', '________________',
      '________________', '______p_________', '________________', '________________', '_____________p__', '________________',
      '__p_____________', '________________', '________p_______', '________________'], { _: P1, p: P2 }),
    tree: art([
      '.....kkkkkk.....', '...kkLLLLLLkk...', '..kLLLLLLLLLLk..', '.kLLLLLLLLLLDDk.', '.kLLLLLLLLLDDDk.', 'kLLLLLLLLLLDDDDk',
      'kLLLLLLLLLDDDDDk', 'kLLLLLLLLDDDDDDk', '.kLLLLLDDDDDDDk.', '.kDLDDDDDDDDDDk.', '..kDDDDDDDDDDk..', '...kkkktttkkk...',
      '......ktttk.....', '......ktttk.....', '.....kkttkkk....', '................'].map(r => r.replace(/\./g, '_')), { _: G1, L: G2, D: G3, t: '#8a5a30' }),
    flower: art([
      '________________', '__r_____________', '_rwr________y___', '__r________ywy__', '__g_________y___', '____________g___',
      '________________', '______w_________', '_____wyw________', '______w_________', '______g_______r_', '_____________rwr',
      '__y___________r_', '_ywy__________g_', '__y_____________', '__g_____________'], { _: G1, r: '#e85848', w: '#ffffff', y: '#f8d048', g: G2 }),
    fence: art([
      '________________', '________________', '________________', '_k____k____k____', 'kok__kok__kok___', 'kokkkkokkkkokkkk',
      'kooooooooooooooo', 'kokkkkokkkkokkkk', 'kokkkkokkkkokkkk', 'kooooooooooooooo', 'kokkkkokkkkokkkk', 'kok__kok__kok___',
      'kok__kok__kok___', '_k____k____k____', '________________', '________________'], { _: G1, o: '#c89a60' })
  };
  // 언덕 속 둥근 문 집 (32×32 = 타일 2×2)
  TILE.hobbitHole = (function () {
    const s = mk(32, 32);
    rect(s, 0, 0, 32, 32, G1);
    ell(s, 16, 20, 17, 14, G2); ell(s, 16, 22, 15, 11, '#7ab060');
    for (const [x, y] of [[6, 12], [24, 11], [10, 9], [21, 8]]) px(s, x, y, G3);
    ell(s, 16, 22, 7, 7, K); ell(s, 16, 22, 6, 6, '#3a8a50'); rect(s, 9, 22, 14, 10, '#7ab060');
    rect(s, 10, 22, 12, 7, '#3a8a50'); rect(s, 9, 22, 1, 7, K); rect(s, 22, 22, 1, 7, K);
    px(s, 16, 23, '#f0c040'); px(s, 16, 24, '#f0c040');           // 한가운데 둥근 손잡이
    for (let x = 11; x < 22; x += 3) rect(s, x, 17, 1, 11, '#2e7040');
    ell(s, 5, 23, 2.5, 2.5, K); ell(s, 5, 23, 1.5, 1.5, '#f0e8a0'); ell(s, 27, 23, 2.5, 2.5, K); ell(s, 27, 23, 1.5, 1.5, '#f0e8a0');
    rect(s, 8, 29, 16, 3, P1); rect(s, 0, 30, 32, 2, G1);
    return s;
  })();

  function toCanvas(s, scale) {
    scale = scale || 1;
    const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const v = s.p[y * s.w + x]; if (v) { g.fillStyle = v; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }
  root.RingPix = { WALK, BATTLE: { wolf: BATTLE.wolf(), orc: BATTLE.orc(), rider: BATTLE.rider(), frodoBack: BATTLE.frodoBack() }, TILE, toCanvas, K };
})(typeof window !== 'undefined' ? window : globalThis);
