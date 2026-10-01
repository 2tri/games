// 「반지 원정」 전투 그림 48×48 — 덩어리 명암 방식
// 부위(머리, 몸, 다리…)를 하나씩 올리고, 각 부위는 빛(왼쪽 위)을 받는 입체로 4단계 명암을 넣는다.
// 앞에 올린 부위와 맞닿는 뒤쪽 부위 가장자리는 한 단계 어둡게 눌러 깊이를 만든다.
(function (root) {
  'use strict';
  const K = '#1c1418';
  const L = (() => { const v = [-0.55, -0.65, 0.52]; const n = Math.hypot(...v); return v.map(a => a / n); })(); // 빛: 왼쪽 위 앞

  function mk(w, h) { return { w, h, p: new Array(w * h).fill(0), id: new Int32Array(w * h).fill(-1), n: 0 }; }
  function inb(s, x, y) { return x >= 0 && y >= 0 && x < s.w && y < s.h; }

  // 부위 하나 칠하기: inside(x,y) 판정 + 입체 기준 타원(cx,cy,rx,ry)으로 명암
  function part(s, inside, cx, cy, rx, ry, ramp, o) {
    o = o || {};
    const id = s.n++, bias = o.bias || 0, flat = o.flat || 0;
    const xs = o.box || [0, 0, s.w - 1, s.h - 1];
    const prev = s.id.slice();
    for (let y = xs[1]; y <= xs[3]; y++) for (let x = xs[0]; x <= xs[2]; x++) {
      if (!inb(s, x, y) || !inside(x + 0.5, y + 0.5)) continue;
      let nx = (x + 0.5 - cx) / rx, ny = (y + 0.5 - cy) / ry;
      const r2 = Math.min(1, nx * nx + ny * ny), nz = Math.sqrt(1 - r2);
      let d = nx * L[0] + ny * L[1] + nz * L[2];
      d = d * (1 - flat) + flat * 0.5 + bias;
      const lv = d > 0.78 ? 3 : d > 0.5 ? 2 : d > 0.18 ? 1 : 0;
      s.p[y * s.w + x] = ramp[Math.min(ramp.length - 1, lv)];
      s.id[y * s.w + x] = id;
    }
    // 새 부위 뒤에 깔린 옛 부위의 맞닿은 가장자리를 어둡게 (그림자 선)
    if (!o.noShadow) {
      for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) {
        if (s.id[y * s.w + x] !== id) continue;
        for (const [dx, dy] of [[1, 0], [0, 1], [1, 1]]) {
          const X = x + dx, Y = y + dy; if (!inb(s, X, Y)) continue;
          const j = Y * s.w + X; const pid = prev[j];
          if (pid >= 0 && s.id[j] !== id && s.shadeOf && s.shadeOf[pid]) s.p[j] = s.shadeOf[pid];
        }
      }
    }
    (s.shadeOf = s.shadeOf || {})[id] = ramp[0];
    return id;
  }
  const E = (cx, cy, rx, ry) => (x, y) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
  function P(pts) { // 다각형 안쪽 판정
    return (x, y) => { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, yi] = pts[i], [xj, yj] = pts[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
  }
  function ell(s, cx, cy, rx, ry, ramp, o) { return part(s, E(cx, cy, rx, ry), cx, cy, rx, ry, ramp, o); }
  function poly(s, pts, ramp, o) {
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    const rx = (Math.max(...xs) - Math.min(...xs)) / 2 + 0.5, ry = (Math.max(...ys) - Math.min(...ys)) / 2 + 0.5;
    return part(s, P(pts), (o && o.cx) || cx, (o && o.cy) || cy, (o && o.rx) || rx, (o && o.ry) || ry, ramp, o);
  }
  function px(s, x, y, c) { if (inb(s, x, y)) s.p[y * s.w + x] = c; }
  function line(s, x0, y0, x1, y1, c) { const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1; for (let i = 0; i <= n; i++) px(s, Math.round(x0 + (x1 - x0) * i / n), Math.round(y0 + (y1 - y0) * i / n), c); }
  function outline(s) {
    const o = s.p.slice(), g = (x, y) => inb(s, x, y) ? s.p[y * s.w + x] : 0;
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (!g(x, y) && (g(x + 1, y) || g(x - 1, y) || g(x, y + 1) || g(x, y - 1))) o[y * s.w + x] = K;
    s.p = o;
    // 외곽선의 계단 모서리 다듬기: 대각선으로만 이어진 외톨이 외곽점 제거
    const g2 = (x, y) => inb(s, x, y) ? s.p[y * s.w + x] : 0;
    for (let y = 1; y < s.h - 1; y++) for (let x = 1; x < s.w - 1; x++) {
      if (g2(x, y) !== K) continue;
      const solid = [[1, 0], [-1, 0], [0, 1], [0, -1]].filter(([a, b]) => g2(x + a, y + b) && g2(x + a, y + b) !== K).length;
      const kn = [[1, 0], [-1, 0], [0, 1], [0, -1]].filter(([a, b]) => g2(x + a, y + b) === K).length;
      if (solid === 0 && kn >= 2) { /* 모서리를 잇는 점은 둔다 */ }
    }
    return s;
  }

  // ── 색 사다리 (어두움 → 밝음) ──
  const HAIR = ['#24160e', '#43291a', '#6a4227', '#94633a'];
  const SKIN = ['#a8684c', '#d4946c', '#f0bc94', '#fcd9b6'];
  const CLOAK = ['#2e3a2c', '#4a5a40', '#6a7c56', '#8c9c70'];
  const WOOD = ['#3a2414', '#5e3c20', '#86582e', '#a8794a'];

  // 프로도 뒷모습 (여행 망토, 곱슬머리, 지팡이)
  function frodoBack() {
    const s = mk(48, 48);
    // 망토 몸통 — 둥근 어깨, 아래로 퍼짐
    poly(s, [[3, 48], [5, 37], [9, 31], [16, 28], [30, 28], [37, 31], [41, 37], [44, 48]], CLOAK, { cx: 22, cy: 38, rx: 22, ry: 13 });
    // 망토 주름
    for (const [x, y0] of [[13, 36], [21, 33], [29, 35], [35, 39]]) for (let y = y0; y < 48; y++) px(s, x + ((y - y0) % 7 === 6 ? 1 : 0), y, CLOAK[0]);
    for (const [x, y0] of [[14, 37], [22, 34]]) for (let y = y0; y < 48; y += 2) px(s, x, y, CLOAK[2]);
    // 오른팔(소매) + 손 + 지팡이
    ell(s, 40, 35, 5, 7, CLOAK);
    for (let y = 9; y < 48; y++) { px(s, 42, y, y < 12 ? WOOD[3] : WOOD[2]); px(s, 43, y, WOOD[1]); }
    ell(s, 42.5, 9, 2.2, 2.4, WOOD, { noShadow: true });
    ell(s, 41, 39, 2.8, 2.6, SKIN);
    // 등에 늘어진 두건
    ell(s, 22, 29, 10, 4.2, CLOAK);
    for (let x = 15; x < 30; x += 3) px(s, x, 30, CLOAK[0]);
    // 목덜미·셔츠 깃
    ell(s, 22, 26, 5, 2.5, SKIN, { flat: 0.3 });
    // 머리 — 바탕 덩어리(조금 작게) + 곱슬 무늬: 빛 쪽으로 열린 작은 호(밝은 3점) + 아래 그늘 2점
    const HX = 22, HY = 15.5, HR = 9.6;
    const inHead = (x, y) => ((x + 0.5 - HX) / HR) ** 2 + ((y + 0.5 - HY) / (HR + 0.6)) ** 2 <= 1;
    // 실루엣 가장자리를 곱슬곱슬하게: 테두리에 작은 혹을 붙인다
    const bumps = [];
    for (let k = 0; k < 15; k++) { const t = Math.PI * (0.95 + k * 1.15 / 14) ; bumps.push([HX + Math.cos(t) * (HR + 0.3), HY + Math.sin(t) * (HR + 0.9)]); }
    for (let k = 0; k < 4; k++) { const t = Math.PI * (0.55 + k * 0.13); bumps.push([HX + Math.cos(t) * (HR + 0.3), HY + Math.sin(t) * (HR + 0.6)]); }
    const inHair = (x, y) => inHead(x - 0.5, y - 0.5) || bumps.some(([bx, by]) => (x - bx) ** 2 + (y - by) ** 2 <= 3.2);
    part(s, inHair, HX - 1, HY - 1, HR + 1.5, HR + 2, HAIR, { bias: -0.08 });
    const hid = s.n - 1;
    const tone = (x, y) => { const d = (-(x - HX) * 0.6 - (y - HY) * 0.8) / HR; return d > 0.35 ? 3 : d > -0.35 ? 2 : 1; };
    for (let row = 0, y = 7; y <= 25; y += 3, row++) for (let x = 11 + (row % 2) * 2; x <= 34; x += 4) {
      const cx = x + ((x * 7 + y * 3) % 3 === 0 ? 1 : 0), cy = y;
      if (!inb(s, cx, cy) || s.id[cy * s.w + cx] !== hid) continue;
      const t = tone(cx, cy), hi = HAIR[t], lo = HAIR[Math.max(0, t - 2)];
      const set = (X, Y, c) => { if (inb(s, X, Y) && s.id[Y * s.w + X] === hid) s.p[Y * s.w + X] = c; };
      set(cx - 1, cy, hi); set(cx, cy - 1, hi); set(cx + 1, cy - 1, t === 3 ? '#b88454' : hi);
      set(cx + 1, cy + 1, lo); set(cx, cy + 1, lo); set(cx + 2, cy, lo);
    }
    // 머리 아래쪽(목덜미)으로 드리운 그늘
    for (let x = 14; x <= 30; x++) for (let y = 23; y <= 26; y++) if (s.id[y * s.w + x] === hid && !inHead(x, y - 2)) s.p[y * s.w + x] = HAIR[0];
    // 왼쪽 귀(살짝 뾰족한 호빗 귀)
    poly(s, [[13, 21], [11, 19], [10, 15], [12, 16], [14, 18]], SKIN, { cx: 13, cy: 18, rx: 3, ry: 4 });
    return outline(s);
  }

  // 농부 매곳의 개 '송곳니' — 정면 3/4, 이빨 드러내고 낮게 웅크림
  const FUR = ['#3a2416', '#6e4a2c', '#a07448', '#cfa274'];
  const FUR_D = ['#24160e', '#43291a', '#5e3c24', '#7a5232'];
  function maggotDog() {
    const s = mk(48, 48);
    // 꼬리 (치켜든)
    for (let i = 0; i <= 12; i++) { const t = i / 12; ell(s, 41 + 4 * Math.sin(t * 1.7), 27 - 14 * t, 2.4 - t * 1.1, 2.2, FUR_D, { noShadow: true }); }
    // 뒷다리(먼 쪽)
    poly(s, [[32, 36], [37, 36], [38, 44], [35, 46], [32, 46]], FUR_D);
    // 몸통
    ell(s, 29, 28.5, 13.5, 7.8, FUR);
    poly(s, [[20, 30], [38, 30], [34, 36], [22, 37]], FUR, { cx: 29, cy: 28.5, rx: 13.5, ry: 7.8, bias: -0.1 });
    for (const [x, y] of [[24, 22], [28, 21], [33, 22], [38, 24]]) { px(s, x, y, FUR_D[1]); px(s, x + 1, y + 1, FUR_D[1]); } // 등 줄무늬
    // 뒷다리(가까운 쪽) 허벅지 + 발
    ell(s, 37.5, 31.5, 5.5, 6.5, FUR);
    poly(s, [[35, 35], [41, 35], [41, 41], [42, 47], [36, 47], [37, 41]], FUR);
    // 가슴
    ell(s, 17, 31, 9, 9.5, FUR, { bias: 0.08 });
    // 앞다리 두 개
    poly(s, [[11, 33], [16, 33], [16, 45], [17, 47], [10, 47], [11, 44]], FUR);
    poly(s, [[18, 34], [23, 34], [23, 45], [24, 47], [17, 47], [18, 44]], FUR, { bias: -0.1 });
    for (const x of [11, 13, 18, 20]) px(s, x, 46, FUR[0]); // 발가락
    // 가죽 목줄
    ell(s, 16, 24, 8, 2.6, ['#4a2412', '#7a3a1a', '#a4522a', '#c8703e'], { flat: 0.4 });
    px(s, 16, 26, '#d8c060'); px(s, 16, 27, '#a88a30');                           // 쇠고리
    // 머리
    ell(s, 13, 17, 8.5, 7.5, FUR);
    // 귀 (뒤로 젖힌 성난 귀)
    poly(s, [[14, 11], [20, 7], [22, 9], [19, 13]], FUR_D);
    poly(s, [[6, 12], [7, 6], [11, 10]], FUR_D);
    // 주둥이 + 벌린 입
    ell(s, 6, 20, 6, 3.6, FUR, { bias: 0.15 });
    poly(s, [[1, 22], [11, 21], [10, 26], [3, 25]], ['#3a0e10', '#5a1818', '#7a2424', '#9a3030'], { flat: 0.8 });
    ell(s, 6, 24.5, 2.5, 1.2, ['#a8303a', '#c8484a', '#e06a66', '#f08a80'], { noShadow: true }); // 혀
    for (const [x, y] of [[2, 22], [4, 22], [7, 22], [9, 21], [3, 25], [8, 25]]) px(s, x, y, '#f4efe2'); // 이빨
    px(s, 2, 23, '#f4efe2'); px(s, 9, 22, '#f4efe2');
    // 코·눈
    ell(s, 1.6, 18.6, 1.6, 1.3, ['#100808', '#201414', '#3a2a2a', '#5a4848'], { noShadow: true });
    px(s, 11, 15, '#f0c030'); px(s, 12, 15, '#f0c030'); px(s, 12, 16, K); px(s, 11, 16, '#c08a20');
    line(s, 9, 13, 13, 14, K); // 찌푸린 눈썹
    for (const [x, y] of [[18, 20], [20, 23], [12, 21]]) px(s, x, y, FUR[0]); // 콧잔등 주름
    return outline(s);
  }

  function toCanvas(s, scale) {
    scale = scale || 1; const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const v = s.p[y * s.w + x]; if (v) { g.fillStyle = v; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }
  root.RingArt = { frodoBack, maggotDog, toCanvas };
})(typeof window !== 'undefined' ? window : globalThis);
