// 「반지 원정」 원정대 6명 — 48×48 앞모습(동료 화면·대화용) / 뒷모습(전투용)
// art48.js 의 덩어리 명암 도구(part/ell/poly)를 그대로 쓴다. 빛은 왼쪽 위.
(function (root) {
  'use strict';
  const { K, mk, inb, part, ell, poly, px, line, outline, E } = root.RingArt.lib;

  // ── 색 사다리 (어두움 → 밝음) ──
  const C = {
    skin:   ['#a8684c', '#d4946c', '#f0bc94', '#fcd9b6'],
    skinE:  ['#a87868', '#d8a890', '#f2d0b6', '#fde8d6'],   // 요정: 희고 맑은 살빛
    skinD:  ['#8e4c36', '#bc7454', '#dc9a74', '#f0be98'],   // 난쟁이: 붉은 기
    skinO:  ['#946858', '#c4947c', '#e2b8a0', '#f4d6c2'],   // 노인
    hairF:  ['#24160e', '#43291a', '#6a4227', '#94633a'],   // 프로도: 짙은 갈색
    hairS:  ['#5a3818', '#8a5c2a', '#b8884a', '#dcb470'],   // 샘: 모랫빛
    hairA:  ['#141012', '#2a2022', '#433436', '#5e4a48'],   // 아라곤: 거의 검은
    hairL:  ['#8a6420', '#c0963a', '#e6c464', '#fbe8a0'],   // 레골라스: 금발
    beardG: ['#4a1c0e', '#7a3216', '#a85228', '#d07a42'],   // 김리: 적갈색
    white:  ['#76788a', '#a6a8b6', '#d2d4dc', '#f4f4f8'],   // 간달프 수염·머리
    cloakF: ['#2e3a2c', '#4a5a40', '#6a7c56', '#8c9c70'],
    vestF:  ['#4a1e1a', '#74302a', '#9a4a3a', '#bc6c54'],
    shirt:  ['#8a8478', '#b8b2a2', '#e0dac8', '#f6f2e4'],
    jacketS:['#3e2814', '#644022', '#8c5e34', '#b0804c'],
    vestS:  ['#6a4a14', '#9a7024', '#c49a3a', '#e2c264'],
    pack:   ['#3e3424', '#62543a', '#8a7a56', '#b0a27a'],
    roll:   ['#5a2418', '#843828', '#a85438', '#c8784e'],
    ranger: ['#1e221c', '#33382e', '#4c5444', '#68705a'],
    leather:['#2e1c12', '#4e3220', '#704a30', '#946a4a'],
    elf:    ['#1c2e20', '#2c4a2e', '#44683e', '#608650'],
    elfC:   ['#3a3a2a', '#5a5a40', '#7e7c5a', '#a4a07c'],   // 요정 겉옷(회갈색)
    bow:    ['#4a2a12', '#7a4a22', '#a87238', '#d4a060'],
    iron:   ['#262a32', '#464c58', '#788090', '#b6bec8'],
    mail:   ['#2a2e36', '#4c525c', '#7a828c', '#a8b0b8'],
    grey:   ['#363844', '#555a68', '#7e8292', '#a8aebc'],
    hat:    ['#1c2448', '#2c3c70', '#4460a0', '#6a88c4'],
    scarf:  ['#5e6474', '#8c92a2', '#bcc2ce', '#e8ecf2'],
    wood:   ['#3a2414', '#5e3c20', '#86582e', '#a8794a'],
    gold:   ['#6a4a10', '#a07a20', '#d4aa3a', '#f4dc78'],
  };
  const I = (s, x, y) => inb(s, x, y) ? s.id[y * s.w + x] : -9;
  const clamp = k => Math.max(0, Math.min(3, k));
  function each(s, pid, fn) { for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (s.id[y * s.w + x] === pid) fn(x, y); }
  function shift(s, x, y, ramp, d) { const i = y * s.w + x, k = ramp.indexOf(s.p[i]); if (k >= 0) s.p[i] = ramp[clamp(k + d)]; }
  const last = s => s.n - 1;
  // 단순판(lite): 잔무늬·소품 생략 — window.RingHeroOpts = { lite: true }
  const lite = () => !!(root.RingHeroOpts && root.RingHeroOpts.lite);

  // 곱슬 무늬: 빛 쪽으로 열린 작은 호(밝게) + 아래 그늘
  function curls(s, pid, HX, HY, R, ramp, y0, y1) {
    const tone = (x, y) => { const d = (-(x - HX) * 0.6 - (y - HY) * 0.8) / R; return d > 0.35 ? 3 : d > -0.35 ? 2 : 1; };
    const sy = lite() ? 4 : 3, sx = lite() ? 5 : 4;
    for (let row = 0, y = y0; y <= y1; y += sy, row++) for (let x = HX - R - 2 + (row % 2) * 2; x <= HX + R + 2; x += sx) {
      const cx = Math.round(x + ((x * 7 + y * 3) % 3 === 0 ? 1 : 0)), cy = y;
      if (I(s, cx, cy) !== pid) continue;
      const t = tone(cx, cy), hi = ramp[t], lo = ramp[Math.max(0, t - 2)];
      const set = (X, Y, c) => { if (I(s, X, Y) === pid) s.p[Y * s.w + X] = c; };
      set(cx - 1, cy, hi); set(cx, cy - 1, hi); set(cx + 1, cy - 1, hi);
      set(cx + 1, cy + 1, lo); set(cx, cy + 1, lo); set(cx + 2, cy, lo);
    }
  }
  // 곧은 머리결: 세로 결을 따라 밝고 어두운 줄
  function strands(s, pid, ramp, period) {
    period = period || 3;
    // 결마다 길이가 다른 가닥: 열마다 엇갈린 구간으로 끊는다
    const hsh = (x, y) => ((x * 73856093) ^ (Math.floor((y + x * 5) / 4) * 19349663)) >>> 0;
    each(s, pid, (x, y) => {
      const m = x % period, h = hsh(x, y) % 7;
      if (lite()) { if (x % 4 === 0 && h < 3) shift(s, x, y, ramp, -1); return; }
      if (m === 0 && h < 5) shift(s, x, y, ramp, -1);
      else if (m === 1 && h < 3) shift(s, x, y, ramp, 1);
    });
  }
  // 사슬갑옷: 작은 고리 줄
  function mailTex(s, pid, ramp) {
    each(s, pid, (x, y) => { if (lite() && y % 3) return; const m = (x + (y % 2) * 2) % 4; if (m === 0) shift(s, x, y, ramp, -1); else if (m === 1 && y % 2 === 0) shift(s, x, y, ramp, 1); });
  }
  // 곱슬머리 실루엣 (둥근 머리 + 가장자리 혹)
  function curlyMask(HX, HY, R, from, to) {
    const bumps = [];
    for (let k = 0; k < 16; k++) { const t = Math.PI * (from + k * (to - from) / 15); bumps.push([HX + Math.cos(t) * (R + 0.3), HY + Math.sin(t) * (R + 0.9)]); }
    return (x, y) => ((x - HX) / R) ** 2 + ((y - HY) / (R + 0.6)) ** 2 <= 1 || bumps.some(([bx, by]) => (x - bx) ** 2 + (y - by) ** 2 <= 3.2);
  }
  // 앞모습 얼굴: 눈(세로 2점 + 홍채), 눈썹, 코 그늘, 입
  function face(s, HX, ey, o) {
    const g = o.gap || 4, iris = o.iris || '#3a2a20', brow = o.brow || K, skin = o.skin;
    for (const side of [-1, 1]) {
      const a = side < 0 ? HX - g - 1 : HX + g - 1, b = a + 1;          // 눈 두 칸
      const outer = side < 0 ? a : b, inner = side < 0 ? b : a;
      px(s, a, ey, K); px(s, b, ey, K); px(s, outer, ey + 1, K); px(s, inner, ey + 1, iris);
      if (o.lid) { px(s, a, ey - 1, skin[1]); px(s, b, ey - 1, skin[1]); }
      const bw = o.browW || 3;
      for (let i = 0; i < bw; i++) px(s, side < 0 ? b - i : a + i, ey - 2 - (o.browTilt && i === bw - 1 ? 1 : 0), brow);
      if (o.blush) { px(s, outer - side, ey + 3, o.blush); px(s, outer, ey + 3, o.blush); }
    }
    // 코 (빛이 왼쪽이라 오른쪽에 그늘)
    px(s, HX, ey + 2, skin[1]); px(s, HX, ey + 3, skin[0]); px(s, HX - 1, ey + 3, skin[1]); px(s, HX - 1, ey + 2, skin[3]);
    // 입
    const my = ey + 5;
    if (o.mouth !== false) {
      if (o.smile) { px(s, HX - 2, my - 1, '#7a3428'); px(s, HX - 1, my, '#7a3428'); px(s, HX, my, '#7a3428'); px(s, HX + 1, my - 1, '#7a3428'); }
      else { px(s, HX - 1, my, '#8a4434'); px(s, HX, my, '#8a4434'); px(s, HX + 1, my, skin[1]); }
    }
  }
  // 지팡이 (세로)
  function staff(s, x, top, ramp, knob) {
    for (let y = top; y < 48; y++) { px(s, x, y, ramp[2]); px(s, x + 1, y, ramp[1]); if (y % 7 === 3) px(s, x, y, ramp[1]); }
    if (knob) ell(s, x + 0.9, top, 2.2, 2.4, ramp, { noShadow: true });
  }

  // ════════════════════ 호빗 공통 ════════════════════
  function hobbitFront(o) {
    const s = mk(48, 48), HX = 24, HY = 15.5, R = o.R || 9.6;
    // 등에 진 짐(샘): 머리 뒤로 비죽 보이는 침낭 말이
    // 몸(망토/윗옷)
    poly(s, [[3, 48], [5, 37], [9, 31], [16, 28], [32, 28], [39, 31], [43, 37], [45, 48]], o.coat, { cx: 22, cy: 38, rx: 22, ry: 13 });
    // 앞섶: 조끼 + 셔츠 깃
    poly(s, [[17, 28], [31, 28], [30, 48], [18, 48]], o.vest, { cx: 22, cy: 38, rx: 8, ry: 12 });
    poly(s, [[19, 27], [29, 27], [24, 35]], C.shirt, { flat: 0.2 });
    if (!lite()) { for (const y of [37, 41, 45]) { px(s, 24, y, C.gold[3]); px(s, 24, y + 1, C.gold[1]); } }         // 놋쇠 단추
    if (o.straps) for (const x of [14, 33]) for (let y = 28; y < 48; y++) { px(s, x, y, C.leather[1]); px(s, x + 1, y, y % 6 === 0 ? C.leather[3] : C.leather[2]); }
    if (!lite()) { if (o.chain) for (const [x, y] of [[21, 28], [22, 30], [23, 32], [27, 28], [26, 30], [25, 32]]) px(s, x, y, C.gold[3]); } // 목에 건 사슬(반지)
    // 목
    ell(s, 24, 26, 4, 2.6, o.skin, { flat: 0.4 });
    // 머리털 덩어리
    part(s, curlyMask(HX, HY, R, 0.9, 2.1), HX - 1, HY - 1, R + 1.5, R + 2, o.hair, { bias: -0.08 });
    const hid = last(s);
    // 귀 (끝이 살짝 뾰족한 호빗 귀)
    poly(s, [[16, 21], [14, 19], [13.6, 15.5], [16, 17.5]], o.skin, { cx: 16, cy: 19, rx: 3, ry: 4 });
    poly(s, [[32, 21], [34, 19], [34.4, 15.5], [32, 17.5]], o.skin, { cx: 32, cy: 19, rx: 3, ry: 4 });
    // 얼굴: 이마는 곱슬 앞머리가 덮는다
    const fr = o.faceR || 7.6;
    part(s, (x, y) => E(HX, 17.4, fr, 8.2)(x, y) && y > 11.2 + 0.05 * (x - HX) ** 2 + ((Math.floor(x) % 4) < 2 ? 1 : 0) && !(Math.abs(x - HX) > fr - 1.4 && y < 16),
      HX, 17.4, fr, 8.2, o.skin, { bias: 0.05 });
    curls(s, hid, HX, HY, R, o.hair, 4, 27);
    face(s, HX, 17, { iris: o.iris, brow: o.hair[0], skin: o.skin, blush: o.blush, smile: o.smile, gap: 4 });
    if (o.staff) { staff(s, 4, 9, C.wood, true); ell(s, 5.5, 38, 2.8, 2.6, o.skin); }
    return outline(s);
  }
  function hobbitBack(o) {
    const s = mk(48, 48), HX = 22, HY = 15.5, R = 9.6;
    poly(s, [[3, 48], [5, 37], [9, 31], [16, 28], [30, 28], [37, 31], [41, 37], [44, 48]], o.coat, { cx: 22, cy: 38, rx: 22, ry: 13 });
    if (!lite()) { for (const [x, y0] of [[13, 36], [21, 33], [29, 35], [35, 39]]) for (let y = y0; y < 48; y++) px(s, x + ((y - y0) % 7 === 6 ? 1 : 0), y, o.coat[0]); }
    if (o.staff) {
      ell(s, 40, 35, 5, 7, o.coat);
      for (let y = 9; y < 48; y++) { px(s, 42, y, C.wood[2]); px(s, 43, y, C.wood[1]); }
      ell(s, 42.5, 9, 2.2, 2.4, C.wood, { noShadow: true });
      ell(s, 41, 39, 2.8, 2.6, o.skin);
    }
    if (o.pack) {
      // 큰 등짐 + 위에 얹은 담요 말이 + 옆에 매단 프라이팬
      poly(s, [[9, 30], [35, 30], [37, 48], [7, 48]], C.pack, { cx: 20, cy: 36, rx: 16, ry: 12 });
      poly(s, [[10, 30], [34, 30], [33, 37], [11, 37]], C.pack, { bias: 0.1 });                    // 덮개
      for (let x = 11; x <= 33; x++) px(s, x, 37, C.pack[0]);
      for (const x of [16, 28]) for (let y = 31; y < 48; y++) { px(s, x, y, C.leather[1]); px(s, x + 1, y, C.leather[2]); }
      if (!lite()) { px(s, 16, 40, C.gold[3]); px(s, 28, 40, C.gold[3]); }
      ell(s, 22, 28.5, 15, 3.4, C.roll);
      for (const x of [13, 31]) for (let y = 25; y <= 32; y++) px(s, x, y, C.leather[0]);
      line(s, 40, 26, 40, 33, C.iron[1]); ell(s, 40.5, 38, 5, 4.6, C.iron, { bias: -0.05 });   // 프라이팬
      ell(s, 40.5, 38, 3, 2.6, C.iron, { noShadow: true, bias: -0.35 });
    } else {
      ell(s, 22, 29, 10, 4.2, o.coat);                                                          // 등에 늘어진 두건
      for (let x = 15; x < 30; x += 3) px(s, x, 30, o.coat[0]);
    }
    ell(s, 22, 26, 5, 2.5, o.skin, { flat: 0.3 });
    part(s, curlyMask(HX, HY, R, 0.95, 2.1), HX - 1, HY - 1, R + 1.5, R + 2, o.hair, { bias: -0.08 });
    const hid = last(s);
    curls(s, hid, HX, HY, R, o.hair, 7, 25);
    const inHead = (x, y) => ((x + 0.5 - HX) / R) ** 2 + ((y + 0.5 - HY) / (R + 0.6)) ** 2 <= 1;
    for (let x = 14; x <= 30; x++) for (let y = 23; y <= 26; y++) if (I(s, x, y) === hid && !inHead(x, y - 2)) s.p[y * s.w + x] = o.hair[0];
    poly(s, [[13, 21], [11, 19], [10, 15], [12, 16], [14, 18]], o.skin, { cx: 13, cy: 18, rx: 3, ry: 4 });
    return outline(s);
  }
  const FRODO = { coat: C.cloakF, vest: C.vestF, hair: C.hairF, skin: C.skin, iris: '#4a7ccc', chain: true, staff: true };
  const SAM = { coat: C.jacketS, vest: C.vestS, hair: C.hairS, skin: C.skin, iris: '#5a7a3a', straps: true, pack: true, blush: '#ec9c80', smile: true, R: 10, faceR: 8.2 };
  const frodoFront = () => hobbitFront(FRODO), frodoBack = () => hobbitBack(FRODO);
  const samFront = () => hobbitFront(SAM), samBack = () => hobbitBack(SAM);

  // ════════════════════ 아라곤 (성큼걸이) ════════════════════
  function aragornFront() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[0, 48], [1, 36], [6, 29], [15, 25], [33, 25], [42, 29], [47, 36], [47, 48]], C.ranger, { cx: 22, cy: 36, rx: 25, ry: 13 });
    if (!lite()) { for (const x of [7, 41]) for (let y = 34; y < 48; y++) px(s, x, y, C.ranger[0]); }                  // 망토 주름
    poly(s, [[17, 28], [31, 28], [30, 48], [18, 48]], C.leather, { cx: 22, cy: 38, rx: 8, ry: 12 });   // 가죽 웃옷
    if (!lite()) { for (let y = 31; y < 46; y += 3) { px(s, 23, y, C.leather[3]); px(s, 25, y, C.leather[3]); px(s, 24, y + 1, C.leather[0]); } } // 끈
    ell(s, 24, 26.5, 12, 3.4, C.ranger, { bias: 0.05 });                                                // 목에 감긴 두건
    ell(s, 24, 24, 3.6, 3, C.skin, { flat: 0.4 });
    // 어깨까지 오는 덥수룩한 머리
    const hairM = (x, y) => E(HX, 14, 9.6, 10.5)(x, y) || (y > 14 && y < 27 - ((Math.floor(x) * 5) % 3) && (Math.abs(x - HX) > 5.5) && Math.abs(x - HX) < 10.5 - (y - 14) * 0.12);
    part(s, hairM, HX - 1, 15, 11, 13, C.hairA, { bias: 0.05 });
    const hid = last(s);
    strands(s, hid, C.hairA, 3);
    // 얼굴 (길쭉하고 각진 턱)
    part(s, (x, y) => E(HX, 16, 6.8, 8.6)(x, y) && y > 9.6 + 0.12 * (x - HX - 1.5) ** 2 * 0.5 + (x < HX ? 0.8 : 0) && y < 24.2 - Math.abs(x - HX) * 0.2,
      HX, 16, 6.8, 8.6, C.skin, { bias: 0.02 });
    const fid = last(s);
    face(s, HX, 16, { iris: '#6a7c8a', brow: C.hairA[0], skin: C.skin, gap: 4, browW: 3, mouth: true });
    // 수염 그늘(덥수룩한 턱)
    each(s, fid, (x, y) => { if (lite()) { if (y >= 22) s.p[y * s.w + x] = '#a07a66'; return; } if (y >= 20 && (x + y) % 2 === 0 && !(y === 21 && Math.abs(x - 24) < 2)) s.p[y * s.w + x] = '#8a6a5a'; else if (y >= 22) s.p[y * s.w + x] = '#a07a66'; });
    px(s, 23, 21, '#6a3a2e'); px(s, 24, 21, '#6a3a2e');
    // 앞으로 흘러내린 머리칼 몇 가닥
    for (const [x, y0, y1] of [[17, 10, 18], [30, 10, 17], [21, 9, 11]]) for (let y = y0; y <= y1; y++) px(s, x, y, C.hairA[1]);
    // 칼자루(허리춤, 오른쪽 아래)
    poly(s, [[37, 40], [44, 40], [44, 42], [37, 42]], C.iron);
    for (let y = 42; y < 48; y++) { px(s, 40, y, C.leather[1]); px(s, 41, y, C.leather[2]); }
    for (let y = 36; y < 40; y++) { px(s, 40, y, C.leather[2]); px(s, 41, y, C.leather[1]); }
    ell(s, 40.5, 35, 1.8, 1.6, C.iron, { noShadow: true });
    return outline(s);
  }
  function aragornBack() {
    const s = mk(48, 48), HX = 23;
    poly(s, [[0, 48], [1, 36], [6, 29], [14, 25], [32, 25], [40, 29], [46, 36], [47, 48]], C.ranger, { cx: 22, cy: 36, rx: 25, ry: 13 });
    if (!lite()) { for (const [x, y0] of [[10, 34], [18, 38], [28, 37], [37, 33]]) for (let y = y0; y < 48; y++) px(s, x + ((y - y0) % 8 === 7 ? 1 : 0), y, C.ranger[0]); }
    // 등에 늘어진 두건 (주름진 고깔)
    poly(s, [[11, 27], [35, 27], [30, 37], [23, 41], [16, 37]], C.ranger, { bias: 0.08 });
    for (const [a, b] of [[[18, 29], [21, 37]], [[27, 29], [25, 37]]]) line(s, a[0], a[1], b[0], b[1], C.ranger[0]);
    // 칼자루가 망토 아래로
    poly(s, [[38, 41], [46, 39], [46.5, 41], [38.5, 43]], C.iron);
    line(s, 42, 43, 44, 47, C.leather[1]); line(s, 43, 43, 45, 47, C.leather[2]);
    // 머리
    const hairM = (x, y) => E(HX, 14, 9.6, 10.5)(x, y) || (y > 14 && y < 28 - ((Math.floor(x) * 5) % 3) && Math.abs(x - HX) < 9.8 - (y - 14) * 0.1);
    part(s, hairM, HX - 2, 13, 11, 13, C.hairA, { bias: 0.05 });
    strands(s, last(s), C.hairA, 3);
    poly(s, [[13, 19], [11.5, 16], [13, 14], [14.5, 17]], C.skin);                                     // 귀 끝
    return outline(s);
  }

  // ════════════════════ 레골라스 ════════════════════
  function bowArc(s, x0, side) { // 세로로 세운 활
    for (let y = 2; y < 48; y++) {
      const t = (y - 25) / 23, x = Math.round(x0 + side * 4.5 * (1 - t * t));
      px(s, x, y, C.bow[2]); px(s, x + side, y, C.bow[1]);
      if (Math.abs(t) > 0.9) px(s, x - side, y, C.bow[3]);
    }
    for (let y = 3; y < 47; y++) px(s, x0 - side, y, '#e8e4d4');                                         // 시위
    for (let y = 22; y < 29; y++) { px(s, x0 + side * 4, y, C.leather[2]); px(s, x0 + side * 5, y, C.leather[1]); } // 손잡이
  }
  function legolasFront() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[3, 48], [4, 36], [9, 30], [17, 26], [31, 26], [39, 30], [44, 36], [45, 48]], C.elf, { cx: 22, cy: 36, rx: 22, ry: 13 });
    poly(s, [[18, 27], [30, 27], [24, 34]], C.elfC, { flat: 0.3 });                                       // 깃
    for (let i = 0; i < 26; i++) { const x = 37 - i, y = 27 + Math.round(i * 0.85); px(s, x, y, C.leather[1]); px(s, x, y + 1, C.leather[2]); } // 화살통 끈
    for (let x = 6; x < 43; x++) { px(s, x, 44, C.leather[1]); px(s, x, 45, C.leather[2]); }                    // 허리띠
    if (!lite()) { px(s, 24, 44, C.gold[3]); px(s, 25, 44, C.gold[2]); px(s, 24, 45, C.gold[2]); }
    ell(s, 24, 24.5, 3.4, 2.8, C.skinE, { flat: 0.4 });
    // 긴 금발: 머리 + 어깨 앞으로 흘러내린 두 갈래
    const hairM = (x, y) => E(HX, 13.5, 9, 10)(x, y) || ((y > 13 && y < 38) && ((x > 14 && x < 18.5 - (y > 30 ? 1 : 0)) || (x > 29.5 + (y > 30 ? 1 : 0) && x < 34)));
    part(s, hairM, HX - 1, 18, 11, 18, C.hairL, { bias: 0.1 });
    const hid = last(s);
    strands(s, hid, C.hairL, 3);
    // 뾰족한 요정 귀
    poly(s, [[16.5, 19], [11, 10], [13, 10.5], [17, 15]], C.skinE, { cx: 15, cy: 15, rx: 4, ry: 5 });
    poly(s, [[31.5, 19], [37, 10], [35, 10.5], [31, 15]], C.skinE, { cx: 33, cy: 15, rx: 4, ry: 5 });
    // 얼굴 (가름하고 갸름한 턱)
    part(s, (x, y) => E(HX, 15.6, 6.6, 8.4)(x, y) && y > 9.2 + 0.07 * (x - HX + 2) ** 2 && y < 23.6 - Math.abs(x - HX) * 0.35,
      HX, 15.6, 6.6, 8.4, C.skinE, { bias: 0.05 });
    face(s, HX, 16, { iris: '#3a6aa8', brow: C.hairL[1], skin: C.skinE, gap: 4, browTilt: true, lid: true });
    for (const [x, y0, y1] of [[18, 9, 14], [29, 9, 13]]) for (let y = y0; y <= y1; y++) px(s, x, y, C.hairL[2]); // 옆머리
    bowArc(s, 41, 1);
    ell(s, 44, 25, 2.4, 2.6, C.skinE, { noShadow: true });                                                         // 활 쥔 손
    return outline(s);
  }
  function legolasBack() {
    const s = mk(48, 48), HX = 24;
    bowArc(s, 7, -1);
    poly(s, [[3, 48], [4, 36], [9, 30], [17, 26], [31, 26], [39, 30], [44, 36], [45, 48]], C.elf, { cx: 22, cy: 36, rx: 22, ry: 13 });
    for (let x = 6; x < 43; x++) { px(s, x, 44, C.leather[1]); px(s, x, 45, C.leather[2]); }
    // 화살통 (오른 어깨에서 왼 허리로 비스듬히) + 깃털
    const q = [[33, 15], [39, 18], [19, 47], [13, 44]];
    poly(s, q, C.leather, { cx: 26, cy: 31, rx: 12, ry: 16 });
    if (!lite()) { for (const t of [0.25, 0.75]) { const x = 36 - 20 * t, y = 16.5 + 29 * t; line(s, x - 3, y - 1.5, x + 3, y + 2, C.gold[2]); } }
    const fl = [[32, 9], [35, 8], [38, 10], [34, 11], [37, 12]];
    fl.forEach(([x, y], i) => { line(s, x, y + 2, x + 1, y + 7, C.wood[1]); poly(s, [[x - 1, y], [x + 1, y - 2], [x + 2, y + 3], [x, y + 3]], i % 2 ? ['#6a2a24', '#a03c30', '#c86048', '#e88a6a'] : C.shirt, { noShadow: true }); });
    // 긴 금발 (등 가운데로)
    const hairM = (x, y) => E(HX, 13.5, 9.2, 10)(x, y) || (y > 13 && y < 37 - Math.abs(x - HX) * 0.5 && Math.abs(x - HX) < 8.6 - (y - 13) * 0.12);
    part(s, hairM, HX - 2, 15, 10, 16, C.hairL, { bias: 0.1 });
    strands(s, last(s), C.hairL, 3);
    // 머리 뒤에서 땋아 묶은 가닥
    for (let y = 18; y < 34; y++) { px(s, 24, y, y % 3 ? C.hairL[1] : C.hairL[3]); px(s, 23, y, y % 3 === 1 ? C.hairL[0] : C.hairL[2]); }
    poly(s, [[15.5, 18], [10, 9], [12, 9.5], [16.5, 14]], C.skinE, { cx: 14, cy: 14, rx: 4, ry: 5 });
    poly(s, [[32.5, 18], [38, 9], [36, 9.5], [31.5, 14]], C.skinE, { cx: 34, cy: 14, rx: 4, ry: 5 });
    return outline(s);
  }

  // ════════════════════ 김리 ════════════════════
  function axe(s, hx, top, bottom, blade) { // 세운 도끼: 자루 + 한쪽 날
    for (let y = top; y < bottom; y++) { px(s, hx, y, C.wood[2]); px(s, hx + 1, y, C.wood[1]); if (y % 5 === 0) px(s, hx, y, C.leather[1]); }
    poly(s, blade, C.iron, { bias: 0.05 });
    const xs = blade.map(p => p[0]); const edge = blade[0][0] < hx ? Math.min(...xs) : Math.max(...xs);
    for (let y = Math.min(...blade.map(p => p[1])) + 1; y < Math.max(...blade.map(p => p[1])); y++) for (let x = Math.min(edge, hx); x <= Math.max(edge, hx); x++) if (Math.abs(x - edge) <= 1 && I(s, x, y) === last(s)) px(s, x, y, C.iron[3]);
  }
  function gimliFront() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[0, 48], [0, 34], [5, 28], [13, 25], [35, 25], [43, 28], [47, 34], [47, 48]], C.mail, { cx: 22, cy: 36, rx: 25, ry: 13 });
    mailTex(s, last(s), C.mail);
    poly(s, [[0, 30], [6, 26], [12, 25], [10, 31], [2, 34]], C.leather);                                  // 어깨 가죽
    poly(s, [[47, 30], [41, 26], [36, 25], [38, 31], [46, 34]], C.leather);
    // 커다란 수염 (가슴까지)
    const beardM = (x, y) => y > 17 && y < 46 - Math.abs(x - HX) * 0.25 && Math.abs(x - HX) < 10.5 - Math.max(0, y - 34) * 0.55;
    part(s, beardM, HX - 2, 26, 12, 16, C.beardG, { bias: 0.08 });
    const bid = last(s);
    strands(s, bid, C.beardG, 3);
    for (let y = 30; y < 44; y++) px(s, 24, y, C.beardG[0]);                                               // 가운데 가르마
    // 얼굴 위쪽 (투구 아래 눈·코)
    part(s, (x, y) => E(HX, 16, 7.6, 6.4)(x, y) && y < 21, HX, 16, 7.6, 6.4, C.skinD);
    face(s, HX, 15, { iris: '#4a3020', brow: C.beardG[1], skin: C.skinD, gap: 4, browW: 4, mouth: false });
    ell(s, 23.6, 18, 2, 2.2, C.skinD, { bias: 0.1 });                                                      // 큰 코
    // 콧수염
    poly(s, [[16, 22], [22, 19.5], [26, 19.5], [32, 22], [30, 23.5], [24, 21.5], [18, 23.5]], C.beardG, { bias: 0.1 });
    // 옆머리
    for (const x0 of [13, 31]) part(s, (x, y) => x > x0 && x < x0 + 4 && y > 11 && y < 24, x0 + 2, 17, 3, 7, C.beardG);
    // 쇠 투구
    part(s, (x, y) => E(HX, 13, 10, 9)(x, y) && y < 12.6, HX - 1, 9, 10, 7, C.iron, { bias: 0.05 });
    poly(s, [[13, 11], [35, 11], [35, 13.5], [13, 13.5]], C.iron, { cx: 24, cy: 9, rx: 12, ry: 6 });      // 테
    if (!lite()) { for (const x of [16, 20, 28, 32]) px(s, x, 12, C.iron[3]); }                                               // 징
    if (!lite()) { for (let y = 4; y < 11; y++) px(s, 24, y, C.gold[2]); }                                                    // 가운데 금줄
    axe(s, 41, 6, 48, [[42, 6], [47, 3], [47, 17], [42, 14]]);
    ell(s, 41.5, 32, 2.8, 2.8, C.skinD);
    return outline(s);
  }
  function gimliBack() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[0, 48], [0, 34], [5, 28], [13, 25], [35, 25], [43, 28], [47, 34], [47, 48]], C.mail, { cx: 22, cy: 36, rx: 25, ry: 13 });
    mailTex(s, last(s), C.mail);
    for (let x = 0; x < 48; x++) { px(s, x, 44, C.leather[1]); px(s, x, 45, C.leather[2]); }
    // 등에 비스듬히 멘 도끼
    for (let i = 0; i < 40; i++) { const x = Math.round(6 + i * 0.85), y = Math.round(46 - i * 0.95); px(s, x, y, C.wood[2]); px(s, x + 1, y, C.wood[1]); }
    poly(s, [[36, 9], [44, 2], [47, 10], [42, 16]], C.iron, { bias: 0.05 });
    line(s, 44, 2, 47, 10, C.iron[3]);
    // 수염 끝이 양옆으로 보임
    for (const x0 of [12, 33]) part(s, (x, y) => x > x0 && x < x0 + 3.5 && y > 17 && y < 26, x0 + 1.5, 22, 2, 5, C.beardG);
    // 투구 아래 머리 (등까지 길게)
    const hairM = (x, y) => E(HX, 14, 10, 10)(x, y) || (y > 14 && y < 32 - Math.abs(x - HX) * 0.4 && Math.abs(x - HX) < 9.5);
    part(s, hairM, HX - 2, 17, 11, 14, C.beardG, { bias: 0.05 });
    strands(s, last(s), C.beardG, 3);
    part(s, (x, y) => E(HX, 13, 10.5, 9.4)(x, y) && y < 13, HX - 2, 8, 10, 7, C.iron, { bias: 0.05 });
    poly(s, [[13, 11], [35, 11], [35, 13.5], [13, 13.5]], C.iron, { cx: 24, cy: 9, rx: 12, ry: 6 });
    for (const x of [16, 20, 24, 28, 32]) px(s, x, 12, C.iron[3]);
    return outline(s);
  }

  // ════════════════════ 간달프 ════════════════════
  function hat(s, back) {
    poly(s, [[15, 13], [33, 13], [28, 6], [31, 0], [26, 2], [21, 7]], C.hat, { cx: 22, cy: 6, rx: 10, ry: 8 });
    ell(s, 24, 13.5, 17, 3, C.hat, { bias: back ? -0.05 : 0.1 });
    for (let x = 14; x < 34; x++) px(s, x, 12, C.hat[0]);                                             // 띠
  }
  function gandalfFront() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[1, 48], [2, 36], [7, 29], [15, 25], [33, 25], [41, 29], [46, 36], [47, 48]], C.grey, { cx: 22, cy: 36, rx: 25, ry: 13 });
    if (!lite()) { for (const x of [11, 37]) for (let y = 33; y < 48; y++) px(s, x, y, C.grey[0]); }
    ell(s, 24, 27, 13, 3.4, C.scarf, { bias: 0.05 });                                                    // 은빛 목도리
    // 어깨까지 흘러내린 흰머리
    for (const x0 of [12.5, 30.5]) part(s, (x, y) => x > x0 && x < x0 + 5 && y > 13 && y < 30 - (x0 < 20 ? x0 + 5 - x : x - x0) * 0.6, x0 + 2.5, 20, 3, 9, C.white, { bias: 0.05 });
    // 얼굴
    part(s, (x, y) => E(HX, 19, 6.8, 7)(x, y) && y > 13, HX, 19, 6.8, 7, C.skinO);
    const fid = last(s);
    each(s, fid, (x, y) => { if (y <= 15) shift(s, x, y, C.skinO, -1); });                               // 모자 그늘
    face(s, HX, 18, { iris: '#5a6c88', brow: C.white[2], skin: C.skinO, gap: 4, mouth: false });
    // 덥수룩한 흰 눈썹
    for (const [a, b] of [[16, 22], [26, 32]]) for (let x = a; x <= b; x++) { px(s, x, 16, C.white[x < 24 ? 3 : 2]); if (x !== a && x !== b) px(s, x, 15, C.white[3]); }
    // 긴 수염
    const beardM = (x, y) => y > 20 && y < 48 && Math.abs(x - HX) < 8 - Math.max(0, y - 30) * 0.32 + (y < 26 ? (y - 20) * 0.3 : 1.8);
    part(s, beardM, HX - 2, 30, 10, 16, C.white, { bias: 0.1 });
    strands(s, last(s), C.white, 3);
    poly(s, [[17, 23.5], [22, 21.5], [26, 21.5], [31, 23.5], [29, 25], [24, 23.4], [19, 25]], C.white, { bias: 0.15 }); // 콧수염
    hat(s, false);
    // 지팡이 (오른손 = 화면 왼쪽)
    for (let y = 4; y < 48; y++) { const x = 4 + (y % 11 < 2 ? 1 : 0); px(s, x, y, C.wood[2]); px(s, x + 1, y, C.wood[1]); }
    poly(s, [[2, 2], [5, 0], [8, 3], [7, 7], [4, 7]], C.wood, { bias: 0.05 });
    ell(s, 5.5, 34, 3, 2.8, C.skinO);
    return outline(s);
  }
  function gandalfBack() {
    const s = mk(48, 48), HX = 24;
    poly(s, [[1, 48], [2, 36], [7, 29], [15, 25], [33, 25], [41, 29], [46, 36], [47, 48]], C.grey, { cx: 22, cy: 36, rx: 25, ry: 13 });
    if (!lite()) { for (const [x, y0] of [[10, 33], [19, 36], [29, 35], [38, 32]]) for (let y = y0; y < 48; y++) px(s, x + ((y - y0) % 8 === 7 ? 1 : 0), y, C.grey[0]); }
    ell(s, 24, 27, 13, 3.4, C.scarf, { bias: 0.05 });
    // 목도리 끝자락이 등으로
    poly(s, [[27, 28], [31, 28], [33, 40], [29, 41]], C.scarf);
    // 흰머리 (모자 아래로 등까지)
    const hairM = (x, y) => y > 12 && y < 34 - Math.abs(x - HX) * 0.5 && Math.abs(x - HX) < 9.2;
    part(s, hairM, HX - 2, 20, 10, 12, C.white, { bias: 0.05 });
    strands(s, last(s), C.white, 3);
    hat(s, true);
    for (let y = 4; y < 48; y++) { const x = 42 + (y % 11 < 2 ? 1 : 0); px(s, x, y, C.wood[2]); px(s, x + 1, y, C.wood[1]); }
    poly(s, [[40, 2], [43, 0], [46, 3], [45, 7], [42, 7]], C.wood, { bias: 0.05 });
    ell(s, 41.5, 34, 3, 2.8, C.skinO);
    return outline(s);
  }

  // 게임보이식 4단계 무채색. 실제 GB 그림처럼 재질마다 쓸 단계를 정해 둔다
  // (밝기만으로 자르면 얼굴·머리·옷이 한 덩어리로 뭉개진다). 0=흰 1=밝은회 2=어두운회 3=검정
  const GB = ['#f8f8f0', '#b0b0a8', '#606060', '#181818'];
  const GBMAP = {
    skin: [1, 0, 0, 0], skinE: [1, 0, 0, 0], skinO: [1, 1, 0, 0], skinD: [1, 1, 0, 0],
    hairF: [3, 2, 2, 1], hairA: [3, 3, 2, 2], hairS: [2, 1, 1, 0], hairL: [2, 1, 1, 1],
    beardG: [2, 2, 1, 1], white: [1, 0, 0, 0],
    cloakF: [2, 1, 1, 1], vestF: [3, 2, 2, 2], shirt: [1, 0, 0, 0], jacketS: [2, 2, 1, 1], vestS: [1, 1, 0, 0],
    pack: [2, 1, 1, 1], roll: [3, 2, 2, 2], ranger: [2, 2, 1, 1], leather: [3, 2, 2, 2],
    elf: [2, 1, 1, 1], elfC: [1, 0, 0, 0], bow: [3, 2, 2, 2], iron: [2, 1, 1, 0], mail: [2, 1, 1, 0],
    grey: [2, 1, 1, 1], hat: [3, 2, 2, 2], scarf: [1, 0, 0, 0], wood: [3, 2, 2, 2], gold: [1, 0, 0, 0],
  };
  const EXTRA = { // art48.js 쪽 색 (송곳니 등)
    '#3a2416': 2, '#6e4a2c': 1, '#a07448': 1, '#cfa274': 0, '#24160e': 3, '#43291a': 2, '#5e3c24': 2, '#7a5232': 2,
    '#8a6a5a': 1, '#a07a66': 1, '#ec9c80': 1,
  };
  // 부위와 부위 사이에 검은 안쪽 선을 긋는다 (GB 그림의 굵은 선맛). 뒤에 깔린 부위 쪽에 긋는다.
  function innerLines(sp, black, minArea) {
    const area = {}; for (const v of sp.id) if (v >= 0) area[v] = (area[v] || 0) + 1;
    const o = sp.p.slice(), W = sp.w;
    for (let y = 0; y < sp.h; y++) for (let x = 0; x < W; x++) {
      const b = sp.id[y * W + x]; if (b < 0 || !sp.p[y * W + x] || (area[b] || 0) < minArea) continue;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const X = x + dx, Y = y + dy; if (X < 0 || Y < 0 || X >= W || Y >= sp.h) continue;
        const a = sp.id[Y * W + X];
        if (a > b && (area[a] || 0) >= minArea && sp.p[Y * W + X]) { o[y * W + x] = black; break; }
      }
    }
    sp.p = o;
  }
  function toGB(sp, pal, o) {
    pal = pal || GB; o = o || {};
    const m = new Map(Object.entries(EXTRA));
    for (const k in GBMAP) C[k].forEach((c, i) => { if (!m.has(c)) m.set(c, GBMAP[k][i]); });
    sp.p = sp.p.map(c => {
      if (!c) return 0; if (c === K) return pal[3];
      if (m.has(c)) return pal[m.get(c)];
      const n = parseInt(c.slice(1), 16), L = 0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255);
      return pal[L > 190 ? 0 : L > 120 ? 1 : L > 58 ? 2 : 3];
    });
    if (o.lines !== false) innerLines(sp, pal[3], 24);
    return sp;
  }
  root.RingGB = { toGB, GB };

  root.RingHeroes = [
    { name: '프로도', front: frodoFront, back: frodoBack },
    { name: '샘', front: samFront, back: samBack },
    { name: '아라곤', front: aragornFront, back: aragornBack },
    { name: '레골라스', front: legolasFront, back: legolasBack },
    { name: '김리', front: gimliFront, back: gimliBack },
    { name: '간달프', front: gandalfFront, back: gandalfBack },
  ];
})(typeof window !== 'undefined' ? window : globalThis);
