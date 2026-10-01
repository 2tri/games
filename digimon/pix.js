// 디지몬 팬 게임 도트 도구 — 게임보이 컬러 「금」판 규칙
//  · 화면 160×144, 지도 칸 16×16
//  · 전투 앞모습은 56×56 칸 안(작은 디지몬은 40·48 크기로 그려 바닥에 맞춤), 뒷모습 48×48
//  · 전투 그림 한 장에 색 4개: 흰색 + 밝은색 + 진한색 + 검정
//  · 필드 인물 16×16, 외곽선 + 4~5색 (머리·피부·옷)
//  · 대표 무늬가 있는 디지몬(그레이몬의 파란 줄무늬 등)만 전투 그림에 색 1개 더
//  · 그림은 모양(타원·다각형·굵은 선)을 겹쳐 그리고, 겹친 경계마다 검은 선을 자동으로 넣는다
(function (root) {
  'use strict';
  const K = '#181818', W = '#f8f8f8';

  function pic(w, h) { return { w, h, p: new Array(w * h).fill(0) }; }
  function at(s, x, y) { return (x < 0 || y < 0 || x >= s.w || y >= s.h) ? 0 : s.p[y * s.w + x]; }
  function px(s, x, y, c) { if (x >= 0 && y >= 0 && x < s.w && y < s.h) s.p[y * s.w + x] = c; }

  // ── 모양: 점(칸의 가운데)이 안에 있는지 묻는 함수 ──
  const E = (cx, cy, rx, ry) => (x, y) => { const dx = (x + .5 - cx) / rx, dy = (y + .5 - cy) / ry; return dx * dx + dy * dy <= 1; };
  const R = (x0, y0, w, h) => (x, y) => x >= x0 && x < x0 + w && y >= y0 && y < y0 + h;
  const P = (pts) => (x, y) => {
    const X = x + .5, Y = y + .5; let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, yi] = pts[i], [xj, yj] = pts[j];
      if ((yi > Y) !== (yj > Y) && X < (xj - xi) * (Y - yi) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  };
  // 굵기가 r0 → r1 로 변하는 선분 (꼬리·팔·뿔)
  const L = (x0, y0, x1, y1, r0, r1) => {
    if (r1 === undefined) r1 = r0;
    const vx = x1 - x0, vy = y1 - y0, l2 = vx * vx + vy * vy || 1;
    return (x, y) => {
      const X = x + .5, Y = y + .5; let t = ((X - x0) * vx + (Y - y0) * vy) / l2; t = Math.max(0, Math.min(1, t));
      const dx = X - (x0 + t * vx), dy = Y - (y0 + t * vy), r = r0 + (r1 - r0) * t; return dx * dx + dy * dy <= r * r;
    };
  };
  // 여러 점을 잇는 굵은 곡선 (점마다 굵기)
  const C = (pts) => { const segs = []; for (let i = 1; i < pts.length; i++) segs.push(L(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], pts[i - 1][2], pts[i][2])); return (x, y) => segs.some(f => f(x, y)); };
  const U = (...fs) => (x, y) => fs.some(f => f(x, y));
  const D = (a, ...bs) => (x, y) => a(x, y) && !bs.some(b => b(x, y));
  const N = (a, b) => (x, y) => a(x, y) && b(x, y);

  function mask(s, f) { const m = new Uint8Array(s.w * s.h); for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (f(x, y)) m[y * s.w + x] = 1; return m; }
  const inM = (s, m, x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h && m[y * s.w + x] === 1;

  // 한 덩어리 그리기: 바깥 검은 선 → 채우기 → 그늘(오른쪽 아래) → 빛(왼쪽 위)
  //   o.shade = [dx, dy, 색]   그 방향으로 dx,dy 만큼 옮기면 밖이 되는 칸을 칠함
  //   o.hi    = [dx, dy, 색]   반대쪽(왼쪽 위) 테두리 안쪽
  //   o.line  = false          검은 선 없이
  function part(s, f, col, o) {
    o = o || {};
    const m = mask(s, f);
    if (o.line !== false) {
      for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) {
        if (m[y * s.w + x]) continue;
        if (inM(s, m, x + 1, y) || inM(s, m, x - 1, y) || inM(s, m, x, y + 1) || inM(s, m, x, y - 1)) s.p[y * s.w + x] = K;
      }
    }
    for (let i = 0; i < m.length; i++) if (m[i]) s.p[i] = col;
    if (o.shade) { const [dx, dy, c] = o.shade; for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (m[y * s.w + x] && !inM(s, m, x + dx, y + dy)) s.p[y * s.w + x] = c; }
    if (o.hi) { const [dx, dy, c] = o.hi; for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (m[y * s.w + x] && !inM(s, m, x - dx, y - dy)) s.p[y * s.w + x] = c; }
    return m;
  }
  // 빗금 그늘: 덩어리(마스크) 안에서 (dx,dy)만큼 옮기면 밖이 되는 칸 중, 빗금 줄에 걸리는 칸을 검게
  //   period = 줄 간격, dir = 1 이면 ／, -1 이면 ＼ 방향
  function hatch(s, m, dx, dy, period, dir, c) {
    const inM2 = (x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h && m[y * s.w + x] === 1;
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) {
      if (!m[y * s.w + x] || inM2(x + dx, y + dy)) continue;
      const k = ((dir === -1 ? x - y : x + y) % period + period) % period;
      if (k === 0) s.p[y * s.w + x] = c || K;
    }
  }
  // 모양 안을 색 하나로 (선 없이)
  function fill(s, f, c) { for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (f(x, y)) s.p[y * s.w + x] = c; }
  // 이미 칠해진 칸 중 모양 안만 색을 바꿈 (무늬·줄무늬)
  function paint(s, f, c) { for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (s.p[y * s.w + x] && s.p[y * s.w + x] !== K && f(x, y)) s.p[y * s.w + x] = c; }
  // 글자 그림을 그대로 찍기: 한 글자 = 한 점. 'k' 는 검정, 'w' 는 흰색(범례에 따로 없으면), 범례에 없는 글자는 건너뜀
  function dots(s, x, y, rows, map) {
    rows.forEach((r, j) => { for (let i = 0; i < r.length; i++) { const ch = r[i], c = map[ch] || (ch === 'k' ? K : ch === 'w' ? W : 0); if (c) px(s, x + i, y + j, c); } });
  }
  // 글자 그림으로 그림 한 장 만들기 ('.' = 비움)
  function art(rows, map) {
    const s = pic(rows[0].length, rows.length); dots(s, 0, 0, rows, map); return s;
  }
  // 좌우 뒤집기
  function flip(s) { const o = pic(s.w, s.h); for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) o.p[y * s.w + x] = s.p[y * s.w + (s.w - 1 - x)]; return o; }
  // 큰 칸에 바닥·가운데 맞춰 앉히기
  function seat(s, w, h) { const o = pic(w, h), ox = Math.floor((w - s.w) / 2), oy = h - s.h; for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (s.p[y * s.w + x]) px(o, x + ox, y + oy, s.p[y * s.w + x]); return o; }
  // 한 색으로 칠한 실루엣 (진화 장면의 깜빡임)
  function silhouette(s, c) { return { w: s.w, h: s.h, p: s.p.map(v => v ? c : 0) }; }

  function toCanvas(s, scale) {
    scale = scale || 1;
    const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const v = s.p[y * s.w + x]; if (v) { g.fillStyle = v; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }

  root.DigiPix = { K, W, pic, at, px, E, R, P, L, C, U, D, N, part, hatch, mask, fill, paint, dots, art, flip, seat, silhouette, toCanvas };
})(typeof window !== 'undefined' ? window : globalThis);
