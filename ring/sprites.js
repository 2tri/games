// 「반지 원정」 도트 그림 — 전부 코드로 한 점씩 찍는다.
// 인물 앞모습 24×24, 적 40×40. 외곽선은 마지막에 자동으로 두른다.
(function (root) {
  'use strict';
  const K = '#1a1420'; // 외곽선

  function mk(w, h) { return { w, h, p: new Array(w * h).fill(0) }; }
  function px(s, x, y, c) { if (x >= 0 && y >= 0 && x < s.w && y < s.h) s.p[y * s.w + x] = c; }
  function rect(s, x, y, w, h, c) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) px(s, x + i, y + j, c); }
  function ell(s, cx, cy, rx, ry, c) {
    for (let y = Math.floor(cy - ry); y <= Math.ceil(cy + ry); y++)
      for (let x = Math.floor(cx - rx); x <= Math.ceil(cx + rx); x++) {
        const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry;
        if (dx * dx + dy * dy <= 1) px(s, x, y, c);
      }
  }
  // 글자 그림: 한 글자 = 한 점. 범례에 없는 글자는 건너뜀
  function pat(s, x, y, rows, map) {
    rows.forEach((r, j) => { for (let i = 0; i < r.length; i++) { const c = map[r[i]]; if (c) px(s, x + i, y + j, c); } });
  }
  function line(s, x0, y0, x1, y1, c, w) {
    w = w || 1; const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1;
    for (let i = 0; i <= n; i++) { const x = Math.round(x0 + (x1 - x0) * i / n), y = Math.round(y0 + (y1 - y0) * i / n); rect(s, x - (w >> 1), y - (w >> 1), w, w, c); }
  }
  function tri(s, x0, y0, x1, y1, x2, y2, c) {
    const minX = Math.min(x0, x1, x2), maxX = Math.max(x0, x1, x2), minY = Math.min(y0, y1, y2), maxY = Math.max(y0, y1, y2);
    const d = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0); if (!d) return;
    for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
      const px_ = x + 0.5, py = y + 0.5;
      const a = ((x1 - px_) * (y2 - py) - (x2 - px_) * (y1 - py)) / d, b = ((x2 - px_) * (y0 - py) - (x0 - px_) * (y2 - py)) / d;
      if (a >= 0 && b >= 0 && a + b <= 1) px(s, x, y, c);
    }
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

  const SKIN = '#F2C49C', SKIN2 = '#D69A74', EYE = '#241c2c', WHITE = '#F4F0E4';

  // ── 공통 몸 (사람 크기) ─────────────────────────
  function body(s, o) {
    const top = o.top || 0;                     // 호빗·드워프는 아래로 내려 키를 줄인다
    const leg = o.legs == null ? 3 : o.legs;
    if (o.cloak) { rect(s, 7, 11 + top, 10, 7 + leg - 1, o.cloak); rect(s, 6, 13 + top, 1, 5, o.cloak); rect(s, 17, 13 + top, 1, 5, o.cloak); }
    rect(s, 8, 11 + top, 8, 5, o.tunic);         // 몸통
    rect(s, 8, 11 + top, 1, 5, o.tunic2 || o.tunic); rect(s, 15, 11 + top, 1, 5, o.tunic2 || o.tunic);
    rect(s, 6, 11 + top, 2, 3, o.sleeve || o.tunic); rect(s, 16, 11 + top, 2, 3, o.sleeve || o.tunic); // 팔
    rect(s, 6, 14 + top, 2, 1, SKIN); rect(s, 16, 14 + top, 2, 1, SKIN); // 손
    if (o.belt) rect(s, 8, 15 + top, 8, 1, o.belt);
    rect(s, 9, 16 + top, 2, leg, o.pants); rect(s, 13, 16 + top, 2, leg, o.pants);
    const fy = 16 + top + leg;
    if (o.feet === 'hobbit') { // 큰 맨발, 발등에 털
      rect(s, 7, fy, 4, 2, SKIN); rect(s, 13, fy, 4, 2, SKIN);
      px(s, 8, fy, o.hair2); px(s, 9, fy, o.hair2); px(s, 14, fy, o.hair2); px(s, 15, fy, o.hair2);
      rect(s, 7, fy + 1, 4, 1, SKIN2); rect(s, 13, fy + 1, 4, 1, SKIN2);
    } else { rect(s, 8, fy, 3, 2, o.boots); rect(s, 13, fy, 3, 2, o.boots); }
  }
  function face(s, top, o) {
    rect(s, 8, 3 + top, 8, 8, SKIN);
    px(s, 8, 3 + top, 0); px(s, 15, 3 + top, 0); px(s, 8, 10 + top, 0); px(s, 15, 10 + top, 0);
    rect(s, 8, 8 + top, 1, 2, SKIN2); rect(s, 15, 8 + top, 1, 2, SKIN2);     // 볼 그늘
    rect(s, 10, 6 + top, 1, 2, EYE); rect(s, 13, 6 + top, 1, 2, EYE);         // 눈
    if (o && o.blue) { px(s, 10, 7 + top, '#3a5ea8'); px(s, 13, 7 + top, '#3a5ea8'); }
    px(s, 11, 9 + top, SKIN2); px(s, 12, 9 + top, SKIN2);                     // 입
  }

  // ── 원정대 ───────────────────────────────────
  const HERO = {};

  HERO.frodo = function () {
    const s = mk(24, 24), t = 2, H = '#3c2618', H2 = '#24160e';
    body(s, { top: t, legs: 2, cloak: '#61785a', tunic: '#e6e0c8', tunic2: '#c9c2a6', sleeve: '#61785a', belt: '#7a5634', pants: '#7a5a3a', feet: 'hobbit', hair2: H2 });
    face(s, t, { blue: true });
    pat(s, 7, 1 + t, [
      '.HH.HH.HH.',
      'HHHHHHHHHH',
      'HHhHHHHhHH',
      'H.HH..HH.H',
      'H........H',
      'h........h'], { H, h: H2 });
    px(s, 11, 11 + t, '#d8b040'); px(s, 12, 11 + t, '#d8b040'); px(s, 12, 12 + t, '#f0d060'); // 목걸이의 반지
    // 짧은 칼 (칼날이 푸르게 빛남)
    pat(s, 4, 8 + t, ['.m', '.M', '.M', '.M', 'GGG', '.o'], { M: '#d6e6f6', m: '#9ec4ec', G: '#9a7a40', o: '#5a3a20' });
    return outline(s);
  };

  HERO.sam = function () {
    const s = mk(24, 24), t = 2, H = '#9a6434', H2 = '#6e4420';
    body(s, { top: t, legs: 2, tunic: '#dccca4', tunic2: '#bba882', sleeve: '#dccca4', belt: '#6e4a2a', pants: '#566a3e', feet: 'hobbit', hair2: H2 });
    rect(s, 8, 11 + t, 2, 5, '#8a5a30'); rect(s, 14, 11 + t, 2, 5, '#8a5a30'); // 조끼
    face(s, t);
    rect(s, 8, 8 + t, 1, 1, '#e8a888'); rect(s, 15, 8 + t, 1, 1, '#e8a888');   // 발그레한 볼
    pat(s, 7, 1 + t, [
      '..HHHHHH..',
      '.HHHhHHHH.',
      'HHHHHHHhHH',
      'HH......HH',
      'H........H'], { H, h: H2 });
    // 배낭 끈 + 등 뒤 배낭
    rect(s, 17, 9 + t, 3, 6, '#7a5230'); rect(s, 17, 9 + t, 3, 1, '#5a3a20');
    // 프라이팬
    pat(s, 1, 10 + t, ['.ppp.', 'ppppp', 'ppppp', '.ppp.', '..o..', '..o..'], { p: '#3a3a44', o: '#5a3a20' });
    px(s, 2, 11 + t, '#5a5a66');
    return outline(s);
  };

  HERO.aragorn = function () {
    const s = mk(24, 24), H = '#2e2218', H2 = '#1c140e';
    body(s, { top: 0, legs: 4, cloak: '#34503a', tunic: '#4a4a3e', tunic2: '#383830', sleeve: '#4a4a3e', belt: '#6a4a2a', pants: '#3e3a32', boots: '#4a3222' });
    face(s, 0);
    rect(s, 9, 9, 6, 2, '#7a5a44'); px(s, 11, 9, SKIN2); px(s, 12, 9, SKIN2); // 수염 자국
    pat(s, 6, 1, [
      '..HHHHHHHH..',
      '.HHHHHHHHHH.',
      '.HHhHHHHhHH.',
      'HHH.HHHH..HH',
      'HH........HH',
      'HH........HH',
      'H..........H',
      'H..........H',
      'h..........h'], { H, h: H2 });
    // 장검 (오른손)
    pat(s, 18, 1, ['.M.', '.M.', '.M.', '.M.', '.M.', '.M.', '.M.', '.M.', '.M.', 'GGG', '.o.', '.o.', '.G.'], { M: '#dfe6ee', G: '#b89448', o: '#4a3020' });
    px(s, 18, 3, '#aab4c2');
    return outline(s);
  };

  HERO.legolas = function () {
    const s = mk(24, 24), H = '#f0dc96', H2 = '#c8b060';
    // 등 뒤 화살통
    rect(s, 16, 7, 3, 7, '#7a5230'); pat(s, 16, 4, ['w.w', 'www', '.w.'], { w: '#e8e0d0' });
    body(s, { top: 0, legs: 4, cloak: '#8a9a5a', tunic: '#5e8a42', tunic2: '#4a6e34', sleeve: '#5e8a42', belt: '#8a6a3a', pants: '#6a5a3e', boots: '#5a4028' });
    face(s, 0);
    px(s, 7, 6, SKIN); px(s, 6, 5, SKIN); px(s, 16, 6, SKIN); px(s, 17, 5, SKIN); // 뾰족한 귀
    pat(s, 7, 1, [
      '.HHHHHHHH.',
      'HHHHHHHHHH',
      'HHHHhHHHHH',
      'H.......HH',
      'H........H',
      '..........',
      '.........H',
      '.........H',
      '.........h',
      '.........h'], { H, h: H2 });
    // 활 (왼손)
    pat(s, 2, 6, ['..b', '.b.', 'b..', 'b..', 'b..', 'b..', 'b..', '.b.', '..b'], { b: '#a06a30' });
    for (let y = 6; y <= 14; y++) px(s, 5, y, '#e8e0d0'); // 활시위
    return outline(s);
  };

  HERO.gimli = function () {
    const s = mk(24, 24), t = 2, B = '#b44a22', B2 = '#86341a';
    // 넓고 낮은 몸
    rect(s, 6, 11 + t, 12, 6, '#727a86'); rect(s, 6, 11 + t, 1, 6, '#585e68'); rect(s, 17, 11 + t, 1, 6, '#585e68'); // 사슬갑옷
    for (let y = 12 + t; y < 17 + t; y += 2) for (let x = 7; x < 17; x += 2) px(s, x, y, '#8c94a0');
    rect(s, 4, 11 + t, 2, 4, '#727a86'); rect(s, 18, 11 + t, 2, 4, '#727a86');
    rect(s, 4, 15 + t, 2, 1, SKIN); rect(s, 18, 15 + t, 2, 1, SKIN);
    rect(s, 6, 16 + t, 12, 1, '#6a4424');
    rect(s, 8, 17 + t, 3, 2, '#5a3e2a'); rect(s, 13, 17 + t, 3, 2, '#5a3e2a');
    rect(s, 7, 19 + t, 4, 2, '#3e2a1a'); rect(s, 13, 19 + t, 4, 2, '#3e2a1a');
    face(s, t);
    // 투구
    pat(s, 7, 0 + t, [
      '...MMMM...',
      '.MMMMMMMM.',
      'MMMMMMMMMM',
      'GGGGGGGGGG',
      '....mm....'], { M: '#9aa2ae', m: '#7a828e', G: '#d0a840' });
    // 큰 붉은 수염 (가슴까지)
    pat(s, 7, 7 + t, [
      'B........B',
      'BB.BBBB.BB',
      'BBBBBBBBBB',
      'BBBbBBbBBB',
      '.BBBBBBBB.',
      '.BBbBBbBB.',
      '..BBBBBB..',
      '...BBBB...'], { B, b: B2 });
    // 도끼 (오른손)
    pat(s, 18, 3 + t, ['.MMM', 'MMMM', 'MMMo', '.MMo', '...o', '...o', '...o', '...o', '...o', '...o', '...o'], { M: '#c6ced8', o: '#6a4020' });
    return outline(s);
  };

  HERO.gandalf = function () {
    const s = mk(24, 24), R = '#8e8e98', R2 = '#6e6e78', W = '#ecece8', W2 = '#c8c8c4';
    // 긴 로브
    rect(s, 8, 11, 8, 11, R); rect(s, 7, 14, 10, 8, R); rect(s, 7, 14, 1, 8, R2); rect(s, 15, 11, 1, 11, R2);
    rect(s, 5, 11, 3, 4, R); rect(s, 16, 11, 3, 4, R);
    rect(s, 5, 15, 2, 1, SKIN); rect(s, 17, 15, 2, 1, SKIN);
    face(s, 1);
    // 뾰족 모자 (챙 넓게)
    pat(s, 5, 0, [
      '.......HH.....',
      '......HHH.....',
      '.....HHHH.....',
      '....HHHHHH....',
      '.hHHHHHHHHHHh.',
      'hhhhhhhhhhhhhh'], { H: '#8a8a94', h: '#6a6a74' });
    // 흰 수염 (허리까지)
    pat(s, 8, 8, [
      'W......W',
      'WW.WW.WW',
      'WWWWWWWW',
      'WWwWWwWW',
      'WWWWWWWW',
      '.WWwWWW.',
      '.WWWWWW.',
      '..WWWW..',
      '..WwWW..',
      '...WW...'], { W, w: W2 });
    // 지팡이 (왼손)
    pat(s, 2, 2, ['.oo.', 'o..o', '.oo.', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..', '.o..'], { o: '#7a5030' });
    return outline(s);
  };

  // ── 적 ─────────────────────────────────────
  const FOE = {};
  FOE.orc = function () {
    const s = mk(40, 40), SK = '#6e7c4a', SK2 = '#55613a';
    // 다리
    rect(s, 12, 31, 5, 6, '#3c3228'); rect(s, 23, 31, 5, 6, '#3c3228');
    rect(s, 11, 36, 6, 2, '#2a221c'); rect(s, 23, 36, 6, 2, '#2a221c');
    // 몸 (구부정)
    ell(s, 20, 25, 11, 8, '#5c4432'); ell(s, 20, 24, 9, 6, '#6c5240');
    rect(s, 14, 21, 12, 2, '#4e4e56'); rect(s, 13, 29, 14, 2, '#3e2e22'); // 어깨 쇠붙이, 허리띠
    // 왼팔 (늘어뜨림)
    ell(s, 8, 25, 3, 6, SK); ell(s, 8, 31, 3, 2, SK2);
    // 오른팔 + 큰 식칼
    ell(s, 32, 21, 3, 5, SK); ell(s, 33, 17, 2.5, 2.5, SK2);
    pat(s, 31, 2, [
      '.MMMM.',
      'MMMMMM',
      'MMMMMm',
      'MMMMMm',
      'MMMMm.',
      'MMMm..',
      'MMm...',
      '.Mm...',
      '.MM...',
      '..MM..',
      '..mM..',
      '..oo..',
      '..oo..',
      '..oo..'], { M: '#b4b6be', m: '#7e8088', o: '#4a3020' });
    // 머리
    ell(s, 20, 13, 8, 7, SK); ell(s, 20, 16, 7, 4, SK2);
    rect(s, 13, 16, 14, 2, SK);
    // 투구
    pat(s, 12, 4, [
      '.......m.......',
      '......mmm......',
      '....MMMMMMM....',
      '..MMMMMMMMMMM..',
      '.MMMMMMMMMMMMM.',
      'MmmmmmmmmmmmmmM'], { M: '#5a5a64', m: '#40404a' });
    // 눈·눈썹
    rect(s, 15, 12, 3, 1, '#2a2418'); rect(s, 22, 12, 3, 1, '#2a2418');
    rect(s, 16, 13, 2, 1, '#e8402a'); rect(s, 22, 13, 2, 1, '#e8402a');
    // 입과 엄니
    rect(s, 16, 17, 8, 1, '#2a1c14');
    px(s, 16, 16, '#ece4c8'); px(s, 23, 16, '#ece4c8'); px(s, 16, 15, '#ece4c8'); px(s, 23, 15, '#ece4c8');
    px(s, 20, 11, SK2); px(s, 20, 14, SK2); // 코
    return outline(s);
  };

  FOE.rider = function () { // 검은 기사 (두건 쓴 악령, 걸어서)
    const s = mk(40, 40), C = '#26222e', C2 = '#16141c', C3 = '#34303e';
    // 망토 (아래로 퍼짐)
    for (let y = 10; y < 38; y++) { const w = Math.min(15, 5 + (y - 10) * 0.45); rect(s, Math.round(20 - w), y, Math.round(w * 2), 1, y % 5 === 0 ? C3 : C); }
    rect(s, 20, 14, 1, 24, C2); rect(s, 12, 26, 1, 12, C2); rect(s, 28, 24, 1, 14, C2);
    // 두건
    ell(s, 20, 11, 8, 8, C); ell(s, 20, 13, 5, 5, '#07060a');
    rect(s, 17, 13, 2, 1, '#f0e8a0'); rect(s, 22, 13, 2, 1, '#f0e8a0'); // 빛나는 눈
    px(s, 20, 3, C3); px(s, 19, 4, C3);
    // 뻗은 손 + 칼
    ell(s, 8, 22, 3, 2, C); rect(s, 4, 21, 3, 2, '#b0b0bc');
    pat(s, 30, 6, ['...M', '..M.', '..M.', '.M..', '.M..', 'M...', 'GGG.', '.o..'], { M: '#d0d4e0', G: '#6a6a74', o: '#26222e' });
    ell(s, 31, 15, 3, 2, C);
    return outline(s);
  };


  // ── 1~2장 ──
  FOE.wolf = function () { // 들늑대
    const s = mk(40, 40), F = '#7c7066', F2 = '#5a5048', L = '#aa9c8e';
    line(s, 30, 22, 36, 12, F, 3); line(s, 36, 12, 37, 9, F2, 2);          // 꼬리
    rect(s, 27, 27, 3, 9, F2); rect(s, 16, 27, 3, 9, F2);                   // 뒷다리(먼 쪽)
    ell(s, 22, 23, 11, 6, F); ell(s, 22, 26, 9, 3, L);                      // 몸통
    for (let x = 14; x < 32; x += 3) px(s, x, 17, F2);                      // 등털
    rect(s, 31, 28, 3, 8, F); rect(s, 12, 28, 3, 8, F);                     // 앞다리
    rect(s, 11, 35, 4, 1, F2); rect(s, 30, 35, 4, 1, F2);
    ell(s, 11, 21, 6, 6, F); ell(s, 11, 24, 4, 3, L);                       // 가슴·목
    ell(s, 9, 16, 5, 4, F);                                                 // 머리
    rect(s, 2, 16, 6, 3, F); rect(s, 2, 19, 6, 1, L);                       // 주둥이
    px(s, 2, 16, '#1a1420'); px(s, 1, 17, '#1a1420');                       // 코
    pat(s, 6, 9, ['F...F', 'FF.FF', 'FFFFF'], { F });                        // 귀
    px(s, 7, 10, '#c89a8a'); px(s, 11, 10, '#c89a8a');
    px(s, 8, 15, '#f0c030'); px(s, 9, 15, '#1a1420');                       // 노란 눈
    pat(s, 3, 19, ['w.w.w'], { w: '#f4f0e0' });                             // 이빨
    return outline(s);
  };

  FOE.willow = function () { // 묵은숲 버드나무
    const s = mk(40, 40), B = '#6c4c32', B2 = '#4a3222', M = '#6a8a3a', LV = '#86ae4e';
    line(s, 15, 17, 5, 7, B, 3); line(s, 25, 15, 35, 5, B, 3); line(s, 16, 23, 6, 27, B2, 2); // 가지 팔
    for (const [x, y] of [[4, 7], [3, 9], [6, 5], [34, 5], [36, 7], [32, 4]])
      for (let k = 0; k < 7; k++) px(s, x + (k % 2), y + k, k % 3 ? LV : M);               // 늘어진 잎
    rect(s, 14, 6, 12, 29, B); rect(s, 13, 10, 1, 25, B2); rect(s, 26, 10, 1, 25, B2);        // 줄기
    ell(s, 20, 7, 7, 4, B);
    for (let y = 9; y < 34; y += 4) px(s, 16 + (y % 3), y, B2);
    rect(s, 22, 12, 1, 6, B2); rect(s, 18, 27, 1, 5, B2);
    line(s, 13, 33, 6, 37, B, 2); line(s, 26, 33, 34, 37, B, 2); line(s, 18, 35, 16, 38, B2, 2); line(s, 22, 35, 25, 38, B2, 2); // 뿌리
    ell(s, 17, 17, 2.2, 1.6, '#150e08'); ell(s, 23, 17, 2.2, 1.6, '#150e08');                 // 옹이 눈
    px(s, 17, 17, '#e8d060'); px(s, 23, 17, '#e8d060');
    pat(s, 15, 22, ['kkkkkkkkk', 'k.k.k.k.k', '.........'], { k: '#150e08' });               // 갈라진 입
    for (const [x, y] of [[15, 9], [24, 26], [14, 30]]) px(s, x, y, M);                      // 이끼
    return outline(s);
  };

  FOE.spider = function () { // 숲 거미
    const s = mk(40, 40), D = '#2e2638', D2 = '#453a52', R = '#b8402c';
    const legs = [[14, 22, 6, 14, 2, 24], [14, 24, 5, 20, 1, 31], [16, 26, 8, 28, 5, 36], [18, 27, 12, 32, 10, 38],
                  [24, 22, 32, 12, 37, 18], [25, 24, 34, 20, 38, 28], [23, 26, 31, 28, 35, 36], [21, 27, 27, 32, 29, 38]];
    for (const [a, b, c, d, e, f] of legs) { line(s, a, b, c, d, D2, 2); line(s, c, d, e, f, D, 1); }
    ell(s, 26, 17, 10, 8, D); ell(s, 26, 15, 7, 4, D2);                     // 배
    pat(s, 22, 13, ['R.....R', '.R...R.', '..RRR..', '...R...'], { R });    // 붉은 무늬
    ell(s, 15, 24, 6, 5, D2);                                               // 머리가슴
    pat(s, 11, 21, ['r.r.r', '.r.r.'], { r: '#f04030' });                   // 눈 여럿
    pat(s, 11, 27, ['w...w', '.w.w.'], { w: '#e8e0d0' });                   // 집게
    return outline(s);
  };

  FOE.midges = function () { // 늪 모기 떼
    const s = mk(40, 40), M = '#4a4038', W = '#cfe4ee';
    ell(s, 13, 15, 6, 3, W); ell(s, 26, 15, 6, 3, W);                       // 큰 모기 날개
    ell(s, 20, 20, 3, 6, '#6a5a48'); ell(s, 20, 26, 2, 4, '#8a5a3a');      // 몸
    ell(s, 20, 13, 3, 3, M); line(s, 20, 15, 20, 7, '#2a2018', 1);         // 머리·침
    px(s, 19, 12, '#e84030'); px(s, 21, 12, '#e84030');
    for (const [a, b, c, d] of [[18, 19, 11, 27], [22, 19, 29, 27], [18, 22, 13, 32], [22, 22, 27, 32]]) line(s, a, b, c, d, M, 1);
    const pts = [[5, 6], [33, 5], [6, 29], [34, 30], [9, 36], [30, 37], [3, 18], [37, 20], [14, 34], [27, 3], [11, 2], [36, 12]];
    for (const [x, y] of pts) { rect(s, x, y, 2, 1, M); px(s, x, y - 1, W); }  // 작은 모기들
    return outline(s);
  };

  FOE.ruffian = function () { // 브리 불량배
    const s = mk(40, 40), SK = '#e0b08a', SK2 = '#c08a66', C = '#7a4a3a', C2 = '#5a3428';
    rect(s, 13, 31, 5, 6, '#3e3a34'); rect(s, 22, 31, 5, 6, '#3e3a34'); rect(s, 12, 36, 6, 2, '#2a221a'); rect(s, 22, 36, 6, 2, '#2a221a');
    rect(s, 11, 19, 18, 13, C); rect(s, 11, 19, 2, 13, C2); rect(s, 27, 19, 2, 13, C2); rect(s, 11, 28, 18, 2, '#3a2a1a');
    rect(s, 7, 20, 4, 8, C); rect(s, 29, 20, 4, 8, C); rect(s, 7, 28, 4, 2, SK); rect(s, 29, 28, 4, 2, SK);
    line(s, 31, 29, 36, 12, '#6a4424', 3); ell(s, 36, 10, 3, 4, '#7a5030'); px(s, 35, 8, '#9a9aa4'); px(s, 37, 11, '#9a9aa4'); // 몽둥이
    ell(s, 20, 12, 7, 8, SK); rect(s, 13, 14, 1, 4, SK2); rect(s, 26, 14, 1, 4, SK2);
    pat(s, 12, 3, ['..HHHHHHHHHHH..', '.HHHHHHHHHHHHHH', 'HHHHHHHHHHHHHHH', 'hhhhhhhhhhhhhhh'], { H: '#4a4a3e', h: '#34342c' }); // 모자
    rect(s, 16, 10, 3, 1, '#2a2018'); rect(s, 22, 10, 3, 1, '#2a2018');    // 찡그린 눈
    px(s, 17, 11, '#2a2018'); px(s, 23, 11, '#2a2018');
    rect(s, 15, 16, 10, 3, '#8a6a52'); rect(s, 18, 17, 4, 1, '#5a2a22');   // 수염 자국·입
    px(s, 26, 11, '#c86a5a'); px(s, 25, 12, '#c86a5a');                    // 흉터
    return outline(s);
  };

  FOE.wight = function () { // 무덤 악령 (1장 우두머리) 56×56
    const s = mk(56, 56), G = '#c6ceda', G2 = '#8e98ac', D = '#1e1e2a', AU = '#d8b040';
    for (let y = 18; y < 52; y++) { const w = Math.min(19, 7 + (y - 18) * 0.42); rect(s, Math.round(28 - w), y, Math.round(w * 2), 1, y % 6 < 2 ? G2 : G); }
    for (let x = 10; x < 47; x += 4) rect(s, x, 50 + (x % 3), 2, 3, G);    // 누더기 끝단
    rect(s, 27, 22, 2, 28, G2);
    line(s, 18, 24, 5, 34, G, 3); line(s, 5, 34, 2, 40, G2, 2);             // 뻗은 팔
    line(s, 38, 24, 51, 32, G, 3); line(s, 51, 32, 54, 38, G2, 2);
    for (const [x, y] of [[1, 40], [3, 41], [53, 38], [55, 39]]) px(s, x, y, '#e8ecf4');   // 손톱
    ell(s, 28, 14, 8, 9, G); ell(s, 28, 16, 6, 6, G2);                     // 머리
    ell(s, 24, 14, 2.5, 3, D); ell(s, 32, 14, 2.5, 3, D);                   // 퀭한 눈
    px(s, 24, 14, '#9fe8ff'); px(s, 32, 14, '#9fe8ff');
    rect(s, 25, 20, 6, 1, D); px(s, 26, 21, D); px(s, 28, 21, D); px(s, 30, 21, D);
    pat(s, 20, 5, ['A.A..A..A.A', 'AAAAAAAAAAA', '.r...b...r.'], { A: AU, r: '#c83030', b: '#3a70d0' }); // 금관
    for (let y = 26; y < 44; y += 3) px(s, 28, y, AU);                      // 금 장신구
    return outline(s);
  };

  // ── 4장 이후 ──
  FOE.watcher = function () { // 물속의 감시자 56×56
    const s = mk(56, 56), T = '#4c6e4a', T2 = '#30503a', SU = '#c8d8b0', WA = '#2a4a6a', WA2 = '#3e6e92';
    const arms = [[10, 50, 6, 30, 12, 12], [20, 50, 22, 32, 18, 18], [34, 50, 32, 28, 38, 8], [46, 50, 50, 34, 46, 20]];
    for (const [a, b, c, d, e, f] of arms) { line(s, a, b, c, d, T, 4); line(s, c, d, e, f, T, 3); line(s, e, f, e + 3, f - 4, T2, 2); }
    for (const [a, b, c, d] of [[10, 46, 7, 34], [34, 46, 33, 30], [46, 46, 49, 36]]) for (let k = 0; k < 4; k++) px(s, Math.round(a + (c - a) * k / 4), Math.round(b + (d - b) * k / 4), SU);
    rect(s, 0, 46, 56, 10, WA); for (let x = 0; x < 56; x += 6) { rect(s, x, 46, 3, 1, WA2); rect(s, x + 3, 49, 2, 1, WA2); }
    ell(s, 28, 45, 10, 3, '#0e1a26'); ell(s, 24, 45, 2, 1, '#f0e060'); ell(s, 32, 45, 2, 1, '#f0e060'); // 물속의 눈
    return outline(s);
  };

  FOE.troll = function () { // 동굴 트롤 56×56
    const s = mk(56, 56), SK = '#7e8c78', SK2 = '#5c6a58', H = '#6a5040';
    rect(s, 16, 42, 9, 10, SK2); rect(s, 32, 42, 9, 10, SK2); rect(s, 14, 50, 12, 3, SK); rect(s, 31, 50, 12, 3, SK);
    ell(s, 28, 30, 17, 14, SK); ell(s, 30, 33, 12, 9, '#8e9c88');         // 큰 몸
    rect(s, 14, 38, 28, 6, H); for (let x = 15; x < 41; x += 4) px(s, x, 43, '#4a3428');
    ell(s, 9, 30, 5, 9, SK); ell(s, 8, 40, 5, 4, SK2);                      // 왼팔
    ell(s, 47, 26, 5, 8, SK); ell(s, 48, 17, 4, 4, SK2);                    // 들어 올린 오른팔
    rect(s, 45, 2, 7, 13, '#6a4a2c'); rect(s, 44, 1, 9, 6, '#5a5a62');      // 망치
    for (const [x, y] of [[44, 2], [52, 3], [48, 0]]) px(s, x, y, '#8a8a94');
    rect(s, 5, 36, 7, 2, '#8a8a94'); px(s, 12, 37, '#8a8a94'); px(s, 13, 38, '#8a8a94'); // 팔목 쇠사슬
    ell(s, 26, 14, 8, 7, SK); ell(s, 26, 18, 7, 4, SK2);                    // 작은 머리, 큰 턱
    px(s, 23, 12, '#f0c040'); px(s, 29, 12, '#f0c040'); rect(s, 22, 11, 3, 1, SK2); rect(s, 28, 11, 3, 1, SK2);
    rect(s, 21, 19, 10, 1, '#2a2418'); px(s, 22, 18, '#e8e0c0'); px(s, 29, 18, '#e8e0c0');
    return outline(s);
  };

  FOE.uruk = function () { // 우루크하이
    const s = mk(40, 40), SK = '#4a403a', SK2 = '#342c28', A = '#3c3c46', A2 = '#2a2a32';
    rect(s, 12, 30, 6, 7, A2); rect(s, 22, 30, 6, 7, A2); rect(s, 11, 36, 7, 2, '#1e1a18'); rect(s, 22, 36, 7, 2, '#1e1a18');
    rect(s, 10, 17, 20, 14, A); rect(s, 10, 17, 20, 2, A2); rect(s, 10, 28, 20, 2, '#5a3a22');
    rect(s, 5, 18, 5, 10, SK); rect(s, 30, 18, 5, 10, SK);
    ell(s, 7, 24, 5, 7, '#4a4a54'); ell(s, 7, 24, 3, 5, '#5a5a66'); px(s, 7, 24, '#e8e8e0'); px(s, 6, 23, '#e8e8e0'); px(s, 8, 23, '#e8e8e0'); // 방패
    line(s, 33, 27, 37, 4, '#9a9ca6', 3); rect(s, 31, 26, 6, 2, '#5a4a3a'); // 넓은 칼
    ell(s, 20, 11, 7, 7, SK); ell(s, 20, 14, 7, 4, SK2); rect(s, 14, 3, 12, 3, A2); rect(s, 13, 5, 14, 2, A); px(s, 20, 2, A2);   // 머리·투구
    rect(s, 15, 9, 3, 1, '#e8402a'); rect(s, 22, 9, 3, 1, '#e8402a');
    pat(s, 17, 11, ['w.w.w', 'wwwww', '.www.'], { w: '#e8e8e0' });         // 얼굴의 흰 손자국
    rect(s, 16, 14, 8, 1, '#1a1410'); px(s, 16, 13, '#ece4c8'); px(s, 23, 13, '#ece4c8');
    return outline(s);
  };

  FOE.crebain = function () { // 까마귀 떼
    const s = mk(40, 40), B = '#24222c', B2 = '#3c3a4c', B3 = '#52506a';
    function crow(ox, oy, k) {
      const r = v => Math.round(v);
      tri(s, r(ox - 1 * k), r(oy - 1 * k), r(ox - 9 * k), r(oy - 11 * k), r(ox + 3 * k), r(oy - 2 * k), B2);   // 뒤 날개
      tri(s, r(ox + 1 * k), r(oy - 1 * k), r(ox + 12 * k), r(oy - 10 * k), r(ox + 5 * k), r(oy + 1 * k), B2);  // 앞 날개
      for (let i = 1; i <= 3; i++) px(s, r(ox + (4 + i * 2) * k), r(oy - (3 + i * 2) * k), B3);             // 깃털 결
      ell(s, ox, oy, 5 * k, 3 * k, B);                                                                     // 몸
      tri(s, r(ox + 4 * k), r(oy), r(ox + 9 * k), r(oy - 1 * k), r(ox + 9 * k), r(oy + 3 * k), B);            // 꼬리
      ell(s, ox - 5 * k, oy - 2 * k, 2.6 * k, 2.4 * k, B);                                                   // 머리
      tri(s, r(ox - 7 * k), r(oy - 3 * k), r(ox - 11 * k), r(oy - 1 * k), r(ox - 7 * k), r(oy - 1 * k), '#6a6a74'); // 부리
      px(s, r(ox - 6 * k), r(oy - 3 * k), '#e03020');                                                       // 붉은 눈
    }
    crow(20, 26, 1.5); crow(9, 11, 0.75); crow(32, 9, 0.7);
    return outline(s);
  };

  FOE.gollum = function () { // 골룸
    const s = mk(40, 40), SK = '#b8baa0', SK2 = '#8e9078', E = '#dff4f0';
    line(s, 14, 28, 8, 36, SK, 3); line(s, 26, 28, 32, 36, SK, 3);          // 쪼그린 다리
    rect(s, 5, 36, 6, 2, SK2); rect(s, 30, 36, 6, 2, SK2);
    ell(s, 20, 26, 7, 6, SK); rect(s, 15, 29, 10, 3, '#6a5a44');             // 앙상한 몸·허리천
    for (let y = 22; y < 29; y += 2) { px(s, 16, y, SK2); px(s, 24, y, SK2); }
    line(s, 14, 22, 8, 30, SK, 2); line(s, 26, 22, 31, 29, SK, 2);          // 팔
    ell(s, 34, 30, 4, 2, '#8aa0b0'); px(s, 37, 29, '#8aa0b0'); px(s, 38, 31, '#8aa0b0'); px(s, 32, 29, '#1a1420'); // 손에 든 물고기
    ell(s, 20, 13, 9, 8, SK); ell(s, 20, 17, 6, 3, SK2);                    // 큰 머리
    ell(s, 16, 12, 3, 3.5, E); ell(s, 24, 12, 3, 3.5, E);                   // 커다란 눈
    px(s, 16, 12, '#2a3a4a'); px(s, 24, 12, '#2a3a4a'); px(s, 17, 13, '#2a3a4a'); px(s, 25, 13, '#2a3a4a');
    rect(s, 17, 18, 6, 1, '#4a4038'); px(s, 18, 19, '#f0ece0'); px(s, 21, 19, '#f0ece0');
    for (const [x, y] of [[18, 5], [21, 4], [23, 5]]) line(s, x, y, x + 1, y - 2, '#5a5448', 1); // 머리카락 몇 가닥
    ell(s, 10, 13, 2, 3, SK); ell(s, 30, 13, 2, 3, SK);                     // 귀
    return outline(s);
  };

  FOE.shelob = function () { // 쉴로브 56×56
    const s = mk(56, 56), D = '#1e1a24', D2 = '#342c40', P = '#6a5a7a';
    const legs = [[22, 30, 10, 12, 2, 20], [22, 33, 6, 26, 1, 40], [24, 36, 10, 42, 6, 54], [27, 38, 18, 46, 16, 55],
                  [34, 30, 46, 10, 54, 16], [34, 33, 50, 24, 55, 38], [32, 36, 46, 42, 50, 54], [29, 38, 38, 46, 40, 55]];
    for (const [a, b, c, d, e, f] of legs) { line(s, a, b, c, d, D2, 3); line(s, c, d, e, f, D, 2); }
    ell(s, 34, 22, 16, 13, D); ell(s, 34, 19, 12, 8, D2);                   // 부푼 배
    pat(s, 26, 14, ['P.......P.......P', '.P.....P.P.....P.', '..PPPPP...PPPPP..'], { P });
    ell(s, 24, 34, 8, 7, D2);                                               // 머리
    pat(s, 18, 30, ['g.g.g.g', '.g.g.g.', 'g.g.g.g'], { g: '#9aff6a' });     // 여러 눈
    pat(s, 18, 38, ['w.....w', '.w...w.', '..w.w..'], { w: '#e8e0d0' });   // 독니
    return outline(s);
  };

  // 캔버스로 바꾸기
  function toCanvas(s, scale) {
    scale = scale || 1;
    const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const v = s.p[y * s.w + x]; if (v) { g.fillStyle = v; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }

  root.RingSprites = { HERO, FOE, toCanvas };
})(typeof window !== 'undefined' ? window : globalThis);
