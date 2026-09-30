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
