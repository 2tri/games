// 「디지몬 금」 필드 그림 — 인물 16×16, 지도 칸 16×16
(function (root) {
  'use strict';
  const { K, W, pic, px, E, R, P, L, part, fill, paint, dots, art, flip } = root.DigiPix;
  const SKIN = '#f8c898';

  // ── 필드 인물 (앞모습) ──
  const WALK = {
    // 신태일: 갈색 덥수룩한 머리 + 이마의 고글, 파란 셔츠
    taichi: art([
      '...k.kk.kk.k....',
      '..kHkHHkHHkHk...',
      '.kHHHHHHHHHHHk..',
      'kHHGGHHHHHGGHHk.',
      'kHkkkkkkkkkkkHk.',
      'kHSSSSSSSSSSSHk.',
      '.kSSkSSSSSkSSk..',
      '.kSSkSSSSSkSSk..',
      '..kSSSSSSSSSk...',
      '...kkkBBBkkk....',
      '..kBBBByBBBBk...',
      '.kSBBByyyBBBSk..',
      '.kkBBBByBBBBkk..',
      '..kPPPPkPPPPk...',
      '..kSSk...kSSk...',
      '..kkkk...kkkk...'], { H: '#8a4a20', G: '#c8e8f8', S: SKIN, B: '#3868d8', y: '#f8c830', P: '#b08850' }),
    // 매튜: 금발, 초록 셔츠 (라이벌)
    yamato: art([
      '....kkkkkk......',
      '...kHHHHHHkk....',
      '..kHHHHHHHHHk...',
      '..kHHHHHHHHHHk..',
      '..kHkHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '...kSSSSSSSSk...',
      '....kkkGGkkk....',
      '...kGGGGGGGGk...',
      '..kSGGGGGGGGSk..',
      '..kkGGGGGGGGkk..',
      '...kPPPkkPPPk...',
      '...kPPk..kPPk...',
      '...kkkk..kkkk...'], { H: '#f0d050', S: SKIN, G: '#58a848', P: '#5878b8' }),
    // 아구몬 (태일을 따라 걷는 작은 모습)
    agumon: art([
      '................',
      '....kkkkkkk.....',
      '...kAAAAAAAk....',
      '..kAwkAAAwkAk...',
      '..kAkkAAAkkAk...',
      '..kAAAAAAAAAk...',
      '.kAAAAAAAAAAAk..',
      '.kAkkkkkkkkkAk..',
      '..kAwDDDDDwAk...',
      '...kkAAAAAkk....',
      '..kwkAAAAADkwk..',
      '..kAkAAAAADkAk..',
      '...kAAAAAADDk...',
      '...kAADkkADDk...',
      '..kwAADk.kADwk..',
      '..kkkkkk.kkkkk..'], { A: '#f8b840', D: '#c06820', w: W })
  };

  // ── 지도 칸 16×16 ──
  const S1 = '#f8e8b0', S2 = '#e0c880', G1 = '#b8e088', G2 = '#80b858', G3 = '#407838', B1 = '#68a8f0', B2 = '#3870c8';
  const T = (rows, map) => art(rows, map);
  const TILE = {
    sand: T([
      '________________', '________________', '___s____________', '________________', '__________s_____', '________________',
      '______s_________', '________________', '________________', '_____________s__', '________________', '__s_____________',
      '________________', '_________s______', '________________', '________________'], { _: S1, s: S2 }),
    shore: T([   // 모래 위, 아래로 하얀 파도
      '________________', '___s________s___', '________________', '________________', '________________', 'w_____ww_____ww_',
      'wwwwwwwwwwwwwwww', 'BwwwBBwwwwBBwwwB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBbbBBBBBB', 'BBbbBBBBBBBBBBBB', 'BBBBBBBBBBBBBbbB',
      'BBBBBBbbBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BbbBBBBBBBBbbBBB', 'BBBBBBBBBBBBBBBB'], { _: S1, s: S2, w: W, B: B1, b: B2 }),
    sea: T([
      'BBBBBBBBBBBBBBBB', 'BBBbbbBBBBBBBBBB', 'BBBBBBbBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBbbbBB', 'BBBBBBBBBBBBBBbB',
      'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BbbbBBBBBBBBBBBB', 'BBBBbBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBbbbBBBBB',
      'BBBBBBBBBBBbBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB'], { B: B1, b: B2 }),
    grass: T([
      '________________', '..g.............', '.g.g.......g....', '..........g.g...', '................', '................',
      '.....g..........', '....g.g.........', '................', '...........g....', '..........g.g...', '................',
      '..g.............', '.g.g......g.....', '.........g.g....', '................'].map(r => r.replace(/[._]/g, '_')), { _: G1, g: G2 }),
    tall: T([   // 풀숲 (야생 디지몬이 나오는 곳)
      '_g___g___g___g__', 'gGg_gGg_gGg_gGg_', 'GGGgGGGgGGGgGGGg', 'kGGkkGGkkGGkkGGk', '_kk__kk__kk__kk_', '________________',
      '_g___g___g___g__', 'gGg_gGg_gGg_gGg_', 'GGGgGGGgGGGgGGGg', 'kGGkkGGkkGGkkGGk', '_kk__kk__kk__kk_', '________________',
      '__g___g___g___g_', '_gGg_gGg_gGg_gGg', 'gGGGgGGGgGGGgGGG', 'GkkGGkkGGkkGGkkG'], { _: G1, g: G2, G: '#58a048', k: G3 }),
    jungle: T([  // 정글 나무 (지나갈 수 없음)
      '__kkkk____kkkk__', '_kLLLLk__kLLLLk_', 'kLLLLDDkkLLLLDDk', 'kLLLDDDDkLLLDDDk', 'kLDDDDDkkLDDDDDk', '_kkDDkk_kkkDDkk_',
      '__kkkkkkkkkkkk__', '_kLLLLkkLLLLLk__', 'kLLLLDDkLLLDDDk_', 'kLLDDDDkLLDDDDk_', 'kDDDDDDkDDDDDkk_', '_kkkkkk_kkkkkk__',
      '___kTTk__kTTk___', '___kTTk__kTTk___', '__kkkkkk_kkkkk__', '________________'], { _: G1, L: G2, D: G3, T: '#8a5a30' }),
    path: T([
      'pppppppppppppppp', 'pppppppppppppppp', 'pppqpppppppppppp', 'pppppppppppppppp', 'ppppppppppqppppp', 'pppppppppppppppp',
      'pppppppppppppppp', 'ppppppqppppppppp', 'pppppppppppppppp', 'pppppppppppppppp', 'pppppppppppppqpp', 'pppppppppppppppp',
      'ppqppppppppppppp', 'pppppppppppppppp', 'ppppppppqppppppp', 'pppppppppppppppp'], { p: '#e8d098', q: '#c8a868' })
  };

  // 야자수 (16×32 = 칸 1×2, 모래 위)
  TILE.palm = (function () {
    const s = pic(16, 32);
    fill(s, R(0, 0, 16, 32), S1);
    for (const [x, y] of [[3, 20], [11, 26], [6, 30]]) px(s, x, y, S2);
    part(s, L(8, 30, 9, 12, 1.6, 1.3), '#a87038', { shade: [1, 0, '#704820'] });                  // 줄기
    for (let y = 15; y < 30; y += 3) { px(s, 8, y, '#704820'); px(s, 9, y, '#704820'); }
    for (const [x0, y0, x1, y1] of [[9, 10, 1, 14], [9, 10, 15, 14], [9, 10, 3, 4], [9, 10, 14, 5], [9, 10, 9, 2]]) part(s, L(x0, y0, x1, y1, 2.2, 1), G2, { shade: [1, 1, G3] }); // 잎
    part(s, E(9, 11, 2, 1.6), '#704820');                                                           // 열매
    for (let x = 4; x < 14; x++) px(s, x, 31, S2);
    return s;
  })();

  // 해변의 전화박스 (16×32 = 칸 1×2)
  TILE.booth = (function () {
    const s = pic(16, 32), F = '#f0f0e8', F2 = '#a8a8a0', GL = '#a8d8f0', PH = '#48a048';
    fill(s, R(0, 0, 16, 32), S1);
    part(s, R(2, 2, 12, 28), F, { shade: [1, 0, F2] });          // 틀
    fill(s, R(3, 1, 10, 3), '#e85040');                          // 빨간 지붕 띠
    for (let x = 2; x < 14; x++) px(s, x, 0, K);
    fill(s, R(4, 6, 8, 18), GL);                                 // 유리
    fill(s, R(4, 6, 8, 1), K); fill(s, R(4, 24, 8, 1), K); fill(s, R(3, 6, 1, 19), K); fill(s, R(12, 6, 1, 19), K);
    fill(s, R(5, 10, 4, 6), PH); fill(s, R(5, 10, 4, 1), K); fill(s, R(5, 16, 4, 1), K); fill(s, R(9, 10, 1, 7), K); // 초록 전화기
    px(s, 6, 8, W); px(s, 7, 8, W); px(s, 10, 18, W); px(s, 10, 19, W);     // 유리 반짝임
    fill(s, R(2, 30, 13, 2), S2);
    return s;
  })();

  root.DigiField = { WALK, TILE, SKIN };
})(typeof window !== 'undefined' ? window : globalThis);
