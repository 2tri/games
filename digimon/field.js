// 필드 그림 — 인물 16×16, 지도 칸 16×16
// 선택받은 아이들 이름: 한국 방영판 (루리위키 「디지몬 어드벤처」 등장인물 표기)
(function (root) {
  'use strict';
  const { K, W, pic, px, E, R, P, L, part, fill, dots, art } = root.DigiPix;
  const S = '#f8c898';           // 피부
  const body = (C, P2, legs) => [ // 몸통 아래 7줄 (옷 색 C, 바지 색 P2)
    '...kkkCCCCkkk...',
    '..kCCCCCCCCCCk..',
    '.kSCCCCCCCCCCSk.',
    '.kkCCCCCCCCCCkk.',
    '...kPPPPkPPPPk..',
    legs || '...kSSk..kSSk...',
    '...kkkk..kkkk...'];

  const KIDS = {
    // 신태일 — 덥수룩한 갈색 머리 + 이마의 고글, 파란 셔츠
    taichi: { name: '신태일', partner: '아구몬', rows: [
      '..k.kk.kk.kk....',
      '.kHkHHkHHkHHk...',
      'kHHHHHHHHHHHHk..',
      'kHGGkHHHHkGGHk..',
      'kHkkkkkkkkkkHk..',
      'kHSSSSSSSSSSHk..',
      '.kSSkSSSSkSSk...',
      '.kSSkSSSSkSSk...',
      '..kSSSSSSSSk....'], map: { H: '#8a4a20', G: '#a8d8f8', C: '#3868d8', P: '#c8a060' } },
    // 매튜 — 금발, 초록 셔츠, 청바지
    yamato: { name: '매튜', partner: '파피몬', rows: [
      '....kkkkkk......',
      '...kHHHHHHkk....',
      '..kHHHHHHHHHk...',
      '..kHHHHHHHHHHk..',
      '..kHkHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '...kSSSSSSSSk...'], map: { H: '#f0d050', C: '#58a848', P: '#4868b0' }, legs: '...kPPk..kPPk...' },
    // 한소라 — 하늘색 모자, 주황 머리, 노란 윗옷
    sora: { name: '한소라', partner: '피요몬', rows: [
      '....kkkkkk......',
      '...kTTTTTTk.....',
      '..kTTTTTTTTk....',
      '..kTTTTTTTTTk...',
      '.kkkkkkkkkkkkk..',
      '..kHSSSSSSSSHk..',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '..kHHSSSSSSHHk..'], map: { T: '#38a8e0', H: '#e86830', C: '#f8d048', P: '#4868b0' }, legs: '...kPPk..kPPk...' },
    // 장한솔 — 붉은 머리, 주황 셔츠, 초록 반바지
    koushiro: { name: '장한솔', partner: '텐타몬', rows: [
      '...k.kk.kk.k....',
      '..kHkHHkHHkHk...',
      '..kHHHHHHHHHHk..',
      '..kHHHHHHHHHHk..',
      '..kHSSSSSSSSHk..',
      '..kSSSSSSSSSSk..',
      '..kSSkSSSSkSSk..',
      '..kSSkSSSSkSSk..',
      '...kSSSSSSSSk...'], map: { H: '#d84820', C: '#f89838', P: '#5a9848' } },
    // 이미나 — 분홍 카우보이모자, 분홍 옷
    mimi: { name: '이미나', partner: '팔몬', rows: [
      '.....kkkkk......',
      '....kTTTTTk.....',
      '...kTTwTTTTk....',
      'kkkkTTTTTTTkkkk.',
      'kTTTTTTTTTTTTTk.',
      '.kkHSSSSSSSHkk..',
      '..kHSkSSSSkSHk..',
      '..kHSkSSSSkSHk..',
      '..kHHSSSSSSHHk..'], map: { T: '#f080b0', H: '#c08040', C: '#f8a0c8', P: '#f8a0c8' } },
    // 정석 — 남색 머리, 안경, 흰 셔츠, 회색 바지
    jou: { name: '정석', partner: '쉬라몬', rows: [
      '....kkkkkk......',
      '...kHHHHHHk.....',
      '..kHHHHHHHHk....',
      '..kHHHHHHHHHk...',
      '..kHSSSSSSSHk...',
      '..kkkkSSkkkkk...',
      '..kkwkSSkwkSk...',
      '..kSkkSSSkkSk...',
      '...kSSSSSSSk....'], map: { H: '#304890', C: '#e8e8e0', P: '#888898' }, legs: '...kPPk..kPPk...' },
    // 리키 — 초록 벙거지모자, 금발, 초록 옷
    takeru: { name: '리키', partner: '파닥몬', rows: [
      '.....kkkkk......',
      '....kTTTTTk.....',
      '...kTTTTTTTk....',
      '..kkTTTTTTTkk...',
      '.kTTTTTTTTTTTk..',
      '..kkHSSSSSHkk...',
      '..kHSkSSSkSHk...',
      '..kHSkSSSkSHk...',
      '...kSSSSSSSk....'], map: { T: '#68b048', H: '#f0d050', C: '#a8d878', P: '#c8a060' } },
    // 신나리 — 짧은 갈색 머리, 분홍 윗옷, 목에 건 호루라기
    hikari: { name: '신나리', partner: '가트몬', rows: [
      '....kkkkkk......',
      '...kHHHHHHk.....',
      '..kHHHHHHHHk....',
      '..kHHHHHHHHHk...',
      '..kHHSSSSHHHk...',
      '..kHSSSSSSSHk...',
      '..kHSkSSSkSHk...',
      '..kHSkSSSkSHk...',
      '...kSSSSSSSk....'], map: { H: '#7a4a28', C: '#f088a8', P: '#f8f0e0' } }
  };
  const WALK = {};
  for (const k in KIDS) {
    const d = KIDS[k];
    WALK[k] = art(d.rows.concat(body(null, null, d.legs)), Object.assign({ S, k: K }, d.map));
  }
  // 나리의 호루라기
  px(WALK.hikari, 7, 10, '#f8d048');

  // 아구몬 (주인공을 따라 걷는 작은 모습)
  WALK.agumon = art([
    '................',
    '....kkkkkkk.....',
    '...kAAAAAAAk....',
    '..kAggAAAggAk...',
    '..kAgkAAAkgAk...',
    '..kAAAAAAAAAk...',
    '.kAAAAAAAAAAAk..',
    '.kAkkkkkkkkkAk..',
    '..kAwAAAAAwAk...',
    '...kkAAAAAkk....',
    '..kwkAAAAAAkwk..',
    '..kAkAAAAAAkAk..',
    '...kAAAAAAAAk...',
    '...kAAkkkAAk....',
    '..kwAAk.kAAwk...',
    '..kkkkk.kkkkk...'], { A: '#f89830', g: '#58b840' });
  // 에렉몬 (행복의 마을 관리인) — 빨간 몸, 파란 줄무늬, 꼬리 여러 개
  WALK.elecmon = art([
    '................',
    '..k........k....',
    '.kRk......kRk...',
    '.kRRk....kRRk...',
    '..kRRkkkkRRk....',
    '..kRRRBBRRRk....',
    '.kRRwkRRwkRRk...',
    '.kRRkkRRkkRRk...',
    '.kRRRRRRRRRRk.k.',
    '..kRRRkkRRRk.kRk',
    '...kkRRRRkk.kRk.',
    '..kRRBRBRRk.kRk.',
    '..kRRRRRRRRkRk..',
    '..kRkkRRkkRRk...',
    '..kwk.kk.kwk....',
    '..kk......kk....'], { R: '#e04838', B: '#4878d8' });

  // ── 지도 칸 16×16: 행복의 마을 (파일섬) ──
  const G1 = '#c8e8a0', G2 = '#90c870', G3 = '#4a8848', PT = '#f0e0b0', PT2 = '#d8c088';
  const TILE = {
    grass: art([
      '________________', '__g_____________', '_g_g_______g____', '__________g_g___', '________________', '______g_________',
      '_____g_g________', '________________', '___________g____', '__________g_g___', '________________', '__g_____________',
      '_g_g______g_____', '_________g_g____', '________________', '________________'], { _: G1, g: G2 }),
    path: art([
      'pppppppppppppppp', 'pppppppppppppppp', 'pppqpppppppppppp', 'pppppppppppppppp', 'ppppppppppqppppp', 'pppppppppppppppp',
      'pppppppppppppppp', 'ppppppqppppppppp', 'pppppppppppppppp', 'pppppppppppppppp', 'pppppppppppppqpp', 'pppppppppppppppp',
      'ppqppppppppppppp', 'pppppppppppppppp', 'ppppppppqppppppp', 'pppppppppppppppp'], { p: PT, q: PT2 }),
    tree: art([
      '____kkkkkkkk____', '__kkLLLLLLLLkk__', '_kLLLLLLLLLLLDk_', '_kLLLLLLLLLLDDk_', 'kLLLLLLLLLLLDDDk', 'kLLLLLLLLLLDDDDk',
      'kLLLLLLLLLDDDDDk', 'kDLLLLLLLDDDDDDk', '_kDDLLLDDDDDDDk_', '_kDDDDDDDDDDDDk_', '__kkDDDDDDDDkk__', '____kkkTTkkk____',
      '______kTTk______', '______kTTk______', '_____kkkkkk_____', '________________'], { _: G1, L: G2, D: G3, T: '#8a5a30' }),
    flower: art([
      '________________', '__r_____________', '_rwr________y___', '__r________ywy__', '__g_________y___', '____________g___',
      '________________', '______b_________', '_____bwb________', '______b_________', '______g_______r_', '_____________rwr',
      '__y___________r_', '_ywy__________g_', '__y_____________', '__g_____________'], { _: G1, r: '#f06878', w: W, y: '#f8d048', b: '#68a8f0', g: G2 })
  };
  // 장난감 블록 하나 (16×16): 앞면 색 + 무늬
  function block(face, top, mark) {
    const s = pic(16, 16);
    fill(s, R(0, 0, 16, 16), G1);
    fill(s, R(1, 3, 14, 12), K);
    fill(s, R(2, 1, 13, 2), K); fill(s, R(3, 2, 11, 2), top);             // 윗면
    fill(s, R(2, 4, 12, 10), face);                                       // 앞면
    fill(s, R(2, 4, 12, 1), W);
    dots(s, 5, 6, mark, { m: K });
    return s;
  }
  TILE.blockR = block('#e85848', '#f8a090', ['..mm..', '.m..m.', 'm....m', 'm....m', '.m..m.', '..mm..']);     // 동그라미
  TILE.blockB = block('#4878e0', '#98b8f8', ['..mm..', '..mm..', '.m..m.', '.m..m.', 'm....m', 'mmmmmm']);     // 세모
  TILE.blockY = block('#f8c830', '#fce898', ['m....m', '.m..m.', '..mm..', '..mm..', '.m..m.', 'm....m']);     // 엑스
  // 블록을 쌓은 집 (32×32 = 칸 2×2)
  TILE.blockHouse = (function () {
    const s = pic(32, 32);
    fill(s, R(0, 0, 32, 32), G1);
    const put = (t, x, y) => { for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) { const v = t.p[j * 16 + i]; if (v && v !== G1) px(s, x + i, y + j, v); } };
    put(TILE.blockB, 0, 16); put(TILE.blockY, 16, 16); put(TILE.blockR, 8, 2);
    fill(s, R(12, 24, 8, 8), K); fill(s, R(13, 25, 6, 7), '#6a4a30');      // 문
    px(s, 17, 28, '#f8d048');
    return s;
  })();
  // 요람 속 아기 디지몬 (16×16) — 깜몬
  TILE.crib = (function () {
    const s = pic(16, 16);
    fill(s, R(0, 0, 16, 16), G1);
    part(s, R(2, 6, 12, 7), '#f8f0e0');                                   // 이불
    part(s, E(8, 7, 3.6, 3), '#383840');                                  // 깜몬 (검은 아기)
    px(s, 7, 6, W); px(s, 9, 6, W);
    for (let x = 1; x < 15; x += 3) fill(s, R(x, 4, 1, 10), '#a06830');  // 난간
    fill(s, R(1, 4, 14, 1), '#a06830'); fill(s, R(1, 13, 14, 2), '#a06830'); fill(s, R(1, 15, 14, 1), K);
    return s;
  })();
  // 풀밭의 디지타마 (16×16)
  TILE.egg = (function () {
    const s = pic(16, 16);
    for (let i = 0; i < 256; i++) s.p[i] = TILE.grass.p[i];
    part(s, U2(E(8, 9, 4.5, 5.6)), '#f8f0d0');
    for (const [x, y] of [[6, 7], [9, 10], [10, 6], [7, 12]]) { px(s, x, y, '#f89830'); px(s, x + 1, y, '#f89830'); }
    fill(s, R(4, 15, 9, 1), G2);
    return s;
  })();
  function U2(f) { return f; }

  root.DigiField = { KIDS, WALK, TILE, SKIN: S };
})(typeof window !== 'undefined' ? window : globalThis);
