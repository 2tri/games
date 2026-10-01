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

  // ── 해변·바다·풀숲 (파일섬) ──
  const S1 = '#f8e8b0', S2 = '#e0c880', B1 = '#68a8f0', B2 = '#3870c8';
  TILE.sand = art([
    '________________', '________________', '___s____________', '________________', '__________s_____', '________________',
    '______s_________', '________________', '________________', '_____________s__', '________________', '__s_____________',
    '________________', '_________s______', '________________', '________________'], { _: S1, s: S2 });
  TILE.shore = art([   // 위는 모래, 아래로 하얀 파도
    '________________', '___s________s___', '________________', '________________', '________________', 'w_____ww_____ww_',
    'wwwwwwwwwwwwwwww', 'BwwwBBwwwwBBwwwB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBbbBBBBBB', 'BBbbBBBBBBBBBBBB', 'BBBBBBBBBBBBBbbB',
    'BBBBBBbbBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BbbBBBBBBBBbbBBB', 'BBBBBBBBBBBBBBBB'], { _: S1, s: S2, w: W, B: B1, b: B2 });
  TILE.sea = art([
    'BBBBBBBBBBBBBBBB', 'BBBbbbBBBBBBBBBB', 'BBBBBBbBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBbbbBB', 'BBBBBBBBBBBBBBbB',
    'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BbbbBBBBBBBBBBBB', 'BBBBbBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBbbbBBBBB',
    'BBBBBBBBBBBbBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB', 'BBBBBBBBBBBBBBBB'], { B: B1, b: B2 });
  TILE.tall = art([   // 풀숲 (야생 디지몬이 나오는 곳)
    '_g___g___g___g__', 'gGg_gGg_gGg_gGg_', 'GGGgGGGgGGGgGGGg', 'kGGkkGGkkGGkkGGk', '_kk__kk__kk__kk_', '________________',
    '_g___g___g___g__', 'gGg_gGg_gGg_gGg_', 'GGGgGGGgGGGgGGGg', 'kGGkkGGkkGGkkGGk', '_kk__kk__kk__kk_', '________________',
    '__g___g___g___g_', '_gGg_gGg_gGg_gGg', 'gGGGgGGGgGGGgGGG', 'GkkGGkkGGkkGGkkG'], { _: G1, g: G2, G: '#60a850', k: G3 });
  TILE.dtree = art([  // 짙은 숲 나무
    '____kkkkkkkk____', '__kkLLLLLLLLkk__', '_kLLLLLLLLLLLDk_', '_kLLLLLLLLLLDDk_', 'kLLLLLLLLLLLDDDk', 'kLLLLLLLLLLDDDDk',
    'kLLLLLLLLLDDDDDk', 'kDLLLLLLLDDDDDDk', '_kDDLLLDDDDDDDk_', '_kDDDDDDDDDDDDk_', '__kkDDDDDDDDkk__', '____kkkTTkkk____',
    '______kTTk______', '______kTTk______', '_____kkkkkk_____', '________________'], { _: '#88c070', L: '#4a9848', D: '#286830', T: '#6a4020' });
  TILE.dgrass = art([
    '________________', '__g_____________', '_g_g_______g____', '__________g_g___', '________________', '______g_________',
    '_____g_g________', '________________', '___________g____', '__________g_g___', '________________', '__g_____________',
    '_g_g______g_____', '_________g_g____', '________________', '________________'], { _: '#88c070', g: '#4a9848' });
  // 표지판
  TILE.sign = (function () {
    const s = pic(16, 16); for (let i = 0; i < 256; i++) s.p[i] = TILE.grass.p[i];
    part(s, R(7, 9, 2, 6), '#8a5a30');
    part(s, R(2, 2, 12, 8), '#c89050');
    fill(s, R(4, 4, 8, 1), '#8a5a30'); fill(s, R(4, 6, 6, 1), '#8a5a30');
    return s;
  })();
  // 야자수 (16×32 = 칸 1×2, 모래 위)
  TILE.palm = (function () {
    const s = pic(16, 32);
    fill(s, R(0, 0, 16, 32), S1);
    for (const [x, y] of [[3, 20], [11, 26], [6, 30]]) px(s, x, y, S2);
    part(s, L(8, 30, 9, 12, 1.6, 1.3), '#a87038');
    for (let y = 15; y < 30; y += 3) { px(s, 8, y, '#704820'); px(s, 9, y, '#704820'); }
    for (const [x0, y0, x1, y1] of [[9, 10, 1, 14], [9, 10, 15, 14], [9, 10, 3, 4], [9, 10, 14, 5], [9, 10, 9, 2]]) part(s, L(x0, y0, x1, y1, 2.2, 1), G2);
    part(s, E(9, 11, 2, 1.6), '#704820');
    return s;
  })();
  // 해변의 전화박스 (16×32 = 칸 1×2)
  TILE.booth = (function () {
    const s = pic(16, 32), F = '#f0f0e8', GL = '#a8d8f0', PH = '#48a048';
    fill(s, R(0, 0, 16, 32), S1);
    part(s, R(2, 2, 12, 28), F);
    fill(s, R(3, 1, 10, 3), '#e85040'); for (let x = 2; x < 14; x++) px(s, x, 0, K);
    fill(s, R(4, 6, 8, 18), GL);
    fill(s, R(4, 6, 8, 1), K); fill(s, R(4, 24, 8, 1), K); fill(s, R(3, 6, 1, 19), K); fill(s, R(12, 6, 1, 19), K);
    fill(s, R(5, 10, 4, 6), PH); fill(s, R(5, 10, 4, 1), K); fill(s, R(5, 16, 4, 1), K); fill(s, R(9, 10, 1, 7), K);
    px(s, 6, 8, W); px(s, 7, 8, W); px(s, 10, 18, W); px(s, 10, 19, W);
    return s;
  })();
  // 캠프 텐트 (32×32 = 칸 2×2)
  TILE.tent = (function () {
    const s = pic(32, 32); for (let j = 0; j < 32; j++) for (let i = 0; i < 32; i++) s.p[j * 32 + i] = TILE.grass.p[(j % 16) * 16 + (i % 16)];
    part(s, P([[16, 2], [31, 29], [1, 29]]), '#e8783c');
    part(s, P([[16, 2], [31, 29], [22, 29]]), '#b84c20');
    part(s, P([[16, 12], [21, 29], [11, 29]]), '#382818');
    fill(s, R(0, 30, 32, 1), G3);
    return s;
  })();
  // 모닥불 (16×16)
  TILE.fire = (function () {
    const s = pic(16, 16); for (let i = 0; i < 256; i++) s.p[i] = TILE.grass.p[i];
    part(s, U2(L(3, 13, 13, 11, 1.2)), '#8a5a30'); part(s, L(3, 11, 13, 13, 1.2), '#8a5a30');
    part(s, P([[8, 2], [12, 11], [4, 11]]), '#f87830'); fill(s, P([[8, 6], [10, 11], [6, 11]]), '#f8d848');
    return s;
  })();

  // ── 걷는 그림: 아이마다 아래·위·왼쪽·오른쪽 × 2동작 ──
  function rowsOf(k) { const d = KIDS[k]; return d.rows.concat(body(null, null, d.legs)); }
  function mapOf(k) { return Object.assign({ S, k: K }, KIDS[k].map); }
  const legsStep = (rows, side) => {               // 한쪽 다리를 든 동작
    const r = rows.slice();
    r[14] = side < 0 ? '....kk...kSSk...' : '...kSSk...kk....';
    r[15] = side < 0 ? '.........kkkk...' : '...kkkk.........';
    return r;
  };
  function backRows(k) {                          // 뒷모습: 얼굴 자리를 머리(또는 모자)로 덮음
    const d = KIDS[k], hc = d.map.H ? 'H' : 'T', r = d.rows.slice();
    for (let y = 4; y < 9; y++) {
      const row = r[y].split(''), a = row.indexOf('k'), b = row.lastIndexOf('k');
      for (let x = a + 1; x < b; x++) if (row[x] === 'S' || row[x] === 'k') row[x] = hc;
      r[y] = row.join('');
    }
    return r.concat(body(null, null, d.legs));
  }
  function sideRows(k) {                          // 옆모습(왼쪽): 오른쪽 눈을 지우고 얼굴을 한쪽으로
    const r = rowsOf(k).slice();
    for (let y = 5; y < 8; y++) { const row = r[y].split(''); for (let x = 8; x < 13; x++) if (row[x] === 'k' && row[x - 1] === 'S' && row[x + 1] === 'S') row[x] = 'S'; r[y] = row.join(''); }
    return r;
  }
  const mirror = (rows) => rows.map(r => r.split('').reverse().join(''));
  const WALKS = {};
  for (const k in KIDS) {
    const m = mapOf(k), dn = rowsOf(k), up = backRows(k), lf = sideRows(k), rt = mirror(lf);
    WALKS[k] = {
      down: [art(dn, m), art(legsStep(dn, -1), m), art(dn, m), art(legsStep(dn, 1), m)],
      up: [art(up, m), art(legsStep(up, -1), m), art(up, m), art(legsStep(up, 1), m)],
      left: [art(lf, m), art(legsStep(lf, -1), m), art(lf, m), art(legsStep(lf, 1), m)],
      right: [art(rt, m), art(legsStep(rt, 1), m), art(rt, m), art(legsStep(rt, -1), m)]
    };
  }
  if (WALKS.hikari) for (const f of WALKS.hikari.down) px(f, 7, 10, '#f8d048');

  // 필드의 디지몬 임시 그림 (그림이 들어오기 전까지): 색 덩어리 + 눈
  function blob(col, dark) {
    return art([
      '................', '................', '.....kkkkkk.....', '...kkCCCCCCkk...', '..kCCwCCCCCCCk..', '..kCwCCCCCCCCk..',
      '.kCCCkCCCCkCCCk.', '.kCCCkCCCCkCCCk.', '.kCCCCCCCCCCCDk.', '.kCCCCCkkCCCCDk.', '.kDCCCCCCCCCDDk.', '..kDDCCCCCCDDk..',
      '..kDDDDDDDDDDk..', '...kkDDDDDDkk...', '.....kkkkkk.....', '................'], { C: col, D: dark });
  }

  root.DigiField = { KIDS, WALK, WALKS, TILE, SKIN: S, blob };
})(typeof window !== 'undefined' ? window : globalThis);
