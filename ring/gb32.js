// 「반지 원정」 게임보이 4단계 도트 — 32×32, 2등신(큰 머리)
// 톤: 0=흰 1=밝은회 2=어두운회 3=검정, -1=투명
// 부위는 [밑색 + 오른쪽 아래 그늘 한 단계]로만 칠하고, 바깥선과 부위 사이 선은 검정.
(function (root) {
  'use strict';
  const GB = ['#f8f8f0', '#b0b0a8', '#606060', '#181818'];
  function mk(w, h) { return { w: w || 32, h: h || 32, p: new Int8Array((w || 32) * (h || 32)).fill(-1), id: new Int16Array((w || 32) * (h || 32)).fill(-1), n: 0 }; }
  const inb = (s, x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h;
  // 부위 칠하기: mask(x,y) 안쪽을 tone 으로, (cx,cy,rx,ry) 기준 오른쪽 아래를 shade 로
  function fill(s, mask, tone, o) {
    o = o || {}; const id = s.n++;
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) {
      const X = x + 0.5, Y = y + 0.5; if (!mask(X, Y)) continue;
      let t = tone;
      if (o.cx !== undefined) {
        const ax = Math.abs((X - (o.cx - o.rx * 0.4)) / o.rx), ay = Math.abs((Y - (o.cy - o.ry * 0.45)) / o.ry), d = (ax ** SQ + ay ** SQ) ** (1 / SQ);
        if (o.shade !== undefined && d > 0.95 + (o.at === undefined ? 0.42 : o.at) * 0.5) t = o.shade;
        else if (o.hi !== undefined && d < 0.5 + (o.hiAt === undefined ? -0.62 : o.hiAt) * 0.5) t = o.hi;
      }
      s.p[y * s.w + x] = t; s.id[y * s.w + x] = o.noLine ? -2 : id;
    }
    return id;
  }
  const SQ = 2.8; // 2=원, 클수록 네모 — 도트다운 각진 덩어리
  const E = (cx, cy, rx, ry) => (x, y) => Math.abs((x - cx) / rx) ** SQ + Math.abs((y - cy) / ry) ** SQ <= 1;
  const OR = (...m) => (x, y) => m.some(f => f(x, y));
  const AND = (...m) => (x, y) => m.every(f => f(x, y));
  const R = (x0, y0, x1, y1) => (x, y) => x >= x0 && x < x1 && y >= y0 && y < y1;
  function ell(s, cx, cy, rx, ry, tone, o) { o = Object.assign({ cx, cy, rx, ry }, o); return fill(s, E(cx, cy, rx, ry), tone, o); }
  function px(s, x, y, t) { if (inb(s, x, y)) s.p[y * s.w + x] = t; }
  // 글자 그림 찍기: '.' 건너뜀, 0~3 톤
  function stamp(s, x0, y0, rows, keepId) {
    rows.forEach((r, j) => [...r].forEach((ch, i) => { if (ch === '.') return; const x = x0 + i, y = y0 + j; if (!inb(s, x, y)) return; s.p[y * s.w + x] = +ch; if (!keepId) s.id[y * s.w + x] = -2; }));
  }
  const flip = rows => rows.map(r => [...r].reverse().join(''));
  // 바깥 외곽선 + 부위 사이 선
  function finish(s, minArea) {
    minArea = minArea || 10;
    const area = {}; for (const v of s.id) if (v >= 0) area[v] = (area[v] || 0) + 1;
    const o = s.p.slice(), W = s.w, g = (x, y) => inb(s, x, y) ? s.p[y * W + x] : -1;
    for (let y = 0; y < s.h; y++) for (let x = 0; x < W; x++) {
      const i = y * W + x;
      if (s.p[i] < 0) { if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([a, b]) => g(x + a, y + b) >= 0)) o[i] = 3; continue; }
      const b = s.id[i]; if (b < 0 || (area[b] || 0) < minArea) continue;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const X = x + dx, Y = y + dy; if (!inb(s, X, Y)) continue;
        const a = s.id[Y * W + X];
        if (a > b && (area[a] || 0) >= minArea && s.p[Y * W + X] >= 0) { o[i] = 3; break; }
      }
    }
    s.p = o; return s;
  }
  // 곱슬: 머리 덩어리 안에 작은 C자 (밝은 점 2 + 어두운 점 1)
  function curls(s, hid, lo, hi, y0, y1) {
    // 드문드문 밝은 ◠ 고리 (가운데 점은 어둡게) — 물방울 무늬가 되지 않게 듬성듬성, 엇갈리게
    const ok = (X, Y) => inb(s, X, Y) && s.id[Y * s.w + X] === hid;
    for (let r = 0, y = y0; y <= y1; y += 4, r++) for (let x = 4 + (r % 2) * 3; x < s.w - 4; x += 6) {
      if (![[0, 0], [2, 0], [1, -1], [1, 1]].every(([a, b]) => ok(x + a, y + b))) continue;
      px(s, x, y, hi); px(s, x + 1, y - 1, hi); px(s, x + 2, y, hi); px(s, x + 1, y, lo);
    }
  }
  // 곱슬머리 실루엣: 둥근 덩어리 + 가장자리에 1~2칸 혹
  function bumpy(cx, cy, rx, ry, a0, a1, n, br) {
    const b = []; for (let k = 0; k < n; k++) { const t = Math.PI * (a0 + k * (a1 - a0) / (n - 1)); b.push([cx + Math.cos(t) * rx, cy + Math.sin(t) * ry]); }
    return OR(E(cx, cy, rx, ry), (x, y) => b.some(([bx, by]) => (x - bx) ** 2 + (y - by) ** 2 <= br * br));
  }
  // 몸통(어깨 둥근 사다리꼴): 위 y0, 어깨 반폭 w0, 바닥 반폭 w1
  const body = (cx, y0, w0, w1) => (x, y) => {
    if (y < y0) return false;
    const k = Math.floor(y - y0), hw = k === 0 ? w0 - 3 : k === 1 ? w0 - 1 : w0 + (k - 2) * (w1 - w0) / 10;
    return Math.abs(x - cx) <= hw;
  };
  const EYE = ['3', '3'];
  // 칼: 세로로 세운 장검 (8칸 폭, 가운데 3|4)
  function sword(s, x0, y0, len) {
    const rows = ['...33...', '..3003..'];
    for (let i = 0; i < len; i++) rows.push('..3013..');
    rows.push('33333333', '31111113', '33333333', '..3223..', '..3223..', '..3223..', '..3113..', '...33...');
    stamp(s, x0, y0, rows);
  }
  // 비스듬히 든 장검: 손잡이 끝(hx,hy) → 칼끝(tx,ty). 머리보다 먼저 그려 머리 뒤로 지나가게.
  function swordDiag(s, hx, hy, tx, ty) {
    const L = Math.hypot(tx - hx, ty - hy), ux = (tx - hx) / L, uy = (ty - hy) / L;
    const seg = (a, b, w) => (x, y) => { const t = (x - hx) * ux + (y - hy) * uy, n = -(x - hx) * uy + (y - hy) * ux; return t >= a && t <= b && Math.abs(n) <= w; };
    fill(s, seg(4, 6, 1.1), 2, {});                                                             // 손잡이
    fill(s, (x, y) => { const t = (x - hx) * ux + (y - hy) * uy, n = -(x - hx) * uy + (y - hy) * ux; return t >= 6 && t <= L && Math.abs(n) <= 1.15 - Math.max(0, t - L + 2.5) * 0.45; }, 0, {}); // 칼날
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const X = x + 0.5, Y = y + 0.5, t = (X - hx) * ux + (Y - hy) * uy, n = -(X - hx) * uy + (Y - hy) * ux;
      if (t > 7 && t < L - 1 && n > 0.3 && n <= 1.15 && s.p[y * s.w + x] === 0) s.p[y * s.w + x] = 1; }              // 날 한쪽 그늘
    fill(s, seg(6, 7.4, 3.6), 1, {});                                                           // 코등이
    fill(s, seg(2, 4, 1.4), 1, {});                                                             // 칼자루 끝
  }
  // 활: 크게 휜 활대 (dir=+1 이면 오른쪽으로 불룩). 시위는 finish 뒤에 그린다.
  function bow(s, x0, dir, y0, y1) {
    const mid = (y0 + y1) / 2, half = (y1 - y0) / 2;
    fill(s, (x, y) => y >= y0 && y <= y1 && Math.abs(x - (x0 + dir * 4.2 * (1 - ((y - mid) / half) ** 2))) <= 1.05, 2, {});
  }
  const bowString = (s, x0, y0, y1) => { for (let y = y0 + 1; y < y1; y++) if (s.p[y * s.w + x0] !== 3) px(s, x0, y, 1); };
  // 양날 도끼: 자루 가운데 hx, 도끼머리 가운데 높이 hy
  const o_dir = hx => hx > 16 ? 1 : -1; // 날은 바깥쪽으로
  function axe(s, hx, hy, top, bottom) {
    fill(s, R(hx - 1, top, hx + 1, bottom), 2, { cx: hx, cy: 20, rx: 1, ry: 12, shade: 3, at: 0.6 });
    fill(s, R(hx - 2, hy - 4, hx + 2, hy + 4), 2, { cx: hx, cy: hy, rx: 2, ry: 4, shade: 3, at: 0.4 });         // 쇠 고리
    const dir = o_dir(hx), e0 = dir > 0 ? hx + 2 : hx - 2;
    const blade = (x, y) => { const k = dir > 0 ? x - e0 : e0 - x; return k >= 0 && k < 6 && Math.abs(y - hy) <= 1.6 + k * 0.85; };
    const id = fill(s, blade, 1, {});
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) if (s.id[y * s.w + x] === id && (dir > 0 ? x >= e0 + 4 : x <= e0 - 5)) s.p[y * s.w + x] = 0; // 날 끝 번쩍
    stamp(s, dir > 0 ? hx - 4 : hx + 2, hy - 1, ['33', '33']);                                                          // 뒤쪽 뿔
  }

  // ───────── 프로도 ─────────
  function frodoF() {
    const s = mk();
    fill(s, body(16, 20, 9.5, 11), 1, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 2 });                // 망토
    fill(s, (x, y) => y >= 21 && Math.abs(x - 16) <= 4 - (y > 27 ? 0 : 0), 2, { noLine: false });      // 조끼
    fill(s, (x, y) => y >= 20 && y < 25 && Math.abs(x - 16) <= 2.8 - (y - 20) * 0.6, 0);              // 셔츠 깃
    // 머리털(뒤) → 얼굴 → 앞머리
    const hair = bumpy(16, 10.5, 9.2, 8.4, 0.95, 2.05, 11, 1.8);
    const hid = fill(s, hair, 2, { cx: 16, cy: 10, rx: 9, ry: 9, hi: 1, hiAt: -0.35, shade: 3, at: 0.75 });
    fill(s, (x, y) => E(16, 13, 7.6, 7.2)(x, y) && y > 8.5 + ((Math.floor(x) % 3) === 0 ? 1 : 0) + Math.abs(x - 16) * 0.18, 0, { cx: 16, cy: 13, rx: 7.6, ry: 7.2, shade: 1, at: 0.62 });
    stamp(s, 6, 12, ['.0', '00', '.0']); stamp(s, 24, 12, ['0.', '00', '0.']);                       // 귀
    stamp(s, 12, 13, EYE.map(c => c)); stamp(s, 19, 13, EYE);                                          // 눈
    stamp(s, 15, 17, ['22']);                                                                          // 입
    // 지팡이 + 손
    fill(s, R(2, 6, 4, 32), 2, { cx: 3, cy: 18, rx: 2, ry: 14, shade: 3 }); fill(s, E(3, 6, 2, 2), 2);
    fill(s, E(4, 24, 2.2, 2), 0);
    return finish(s);
  }
  function frodoB() {
    const s = mk();
    fill(s, body(16, 20, 9.5, 11), 1, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 2 });
    fill(s, E(16, 21.5, 6.5, 2.4), 1, { cx: 16, cy: 21, rx: 6, ry: 2.4, shade: 2 });                 // 두건
    fill(s, R(28, 6, 30, 32), 2, { cx: 29, cy: 18, rx: 2, ry: 14, shade: 3 }); fill(s, E(29, 6, 2, 2), 2);
    fill(s, E(27.5, 24, 2.2, 2), 0);
    const hid = fill(s, bumpy(16, 11, 9.2, 8.8, 0.85, 2.15, 13, 1.8), 2, { cx: 16, cy: 11, rx: 9, ry: 9, hi: 1, hiAt: -0.35, shade: 3, at: 0.75 });
    stamp(s, 6, 12, ['.0', '00', '.0']); stamp(s, 24, 12, ['0.', '00', '0.']);
    return finish(s);
  }

  // ───────── 샘 ─────────
  function samF() {
    const s = mk();
    fill(s, body(16, 20, 10, 11.5), 2, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 3 });               // 갈색 윗옷
    fill(s, (x, y) => y >= 21 && Math.abs(x - 16) <= 4, 1);                                            // 조끼
    fill(s, (x, y) => y >= 20 && y < 25 && Math.abs(x - 16) <= 2.8 - (y - 20) * 0.6, 0);
    stamp(s, 9, 21, ['3', '3', '3', '3', '3', '3', '3', '3', '3', '3', '3']); stamp(s, 22, 21, ['3', '3', '3', '3', '3', '3', '3', '3', '3', '3', '3']); // 짐 멜빵
    const hid = fill(s, bumpy(16, 10.5, 9.6, 8.6, 0.95, 2.05, 11, 1.8), 1, { cx: 16, cy: 10, rx: 9, ry: 9, shade: 2, at: 0.6, hi: 0, hiAt: -0.45 });
    fill(s, (x, y) => E(16, 13.4, 8.2, 7.4)(x, y) && y > 8.5 + ((Math.floor(x) % 3) === 1 ? 1 : 0) + Math.abs(x - 16) * 0.16, 0, { cx: 16, cy: 13, rx: 8.2, ry: 7.4, shade: 1, at: 0.65 });
    stamp(s, 6, 12, ['.0', '00', '.0']); stamp(s, 24, 12, ['0.', '00', '0.']);
    stamp(s, 12, 13, EYE); stamp(s, 19, 13, EYE);
    stamp(s, 10, 16, ['1']); stamp(s, 21, 16, ['1']);                                                  // 볼
    stamp(s, 14, 17, ['2..2', '.22.']);                                                                // 웃는 입
    return finish(s);
  }
  function samB() {
    const s = mk();
    fill(s, body(16, 20, 10, 11.5), 2, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 3 });
    fill(s, R(7, 19, 25, 32), 1, { cx: 16, cy: 23, rx: 9, ry: 8, shade: 2 });                         // 등짐
    fill(s, R(8, 19, 24, 23), 1, { cx: 16, cy: 19, rx: 8, ry: 4, hi: 0, hiAt: -0.3 });                // 덮개
    fill(s, E(16, 18.5, 11, 2.2), 2, { cx: 16, cy: 18, rx: 11, ry: 2.2, shade: 3 });                  // 담요 말이
    fill(s, E(27, 26, 3, 3), 2, { cx: 27, cy: 26, rx: 3, ry: 3, shade: 3 });                           // 프라이팬
    stamp(s, 27, 21, ['3', '3']);
    const hid = fill(s, bumpy(16, 10, 9.6, 8.4, 0.85, 2.15, 13, 1.8), 1, { cx: 16, cy: 10, rx: 9, ry: 9, shade: 2, at: 0.6, hi: 0, hiAt: -0.45 });
    stamp(s, 6, 11, ['.0', '00', '.0']); stamp(s, 24, 11, ['0.', '00', '0.']);
    return finish(s);
  }

  // ───────── 아라곤 (검사) ─────────
  function aragornF() {
    const s = mk();
    fill(s, body(16, 19, 11, 13), 2, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 3 });                 // 망토
    fill(s, (x, y) => y >= 21 && Math.abs(x - 16) <= 4.5, 1, { cx: 16, cy: 25, rx: 4, ry: 6, shade: 2 }); // 가죽 웃옷
    fill(s, R(11, 27, 22, 29), 3, {});                                                                  // 칼띠
    stamp(s, 15, 27, ['00']);
    const hid = fill(s, OR(E(16, 10.5, 9, 8.6), AND(R(7, 10, 25, 19), (x, y) => (Math.abs(x - 16) > 5 || y < 12) && y < 18.5 - (Math.floor(x) % 2))), 2, { cx: 16, cy: 10, rx: 9, ry: 9, shade: 3, at: 0.2 });
    fill(s, (x, y) => E(16, 13, 6.4, 7.4)(x, y) && y > 7.6 + (x < 16 ? 1.4 : 0.4) + Math.abs(x - 16) * 0.2, 0, { cx: 16, cy: 13, rx: 6.4, ry: 7.4, shade: 1, at: 0.6 });
    stamp(s, 12, 13, EYE); stamp(s, 19, 13, EYE);
    stamp(s, 11, 11, ['333']); stamp(s, 18, 11, ['333']);                                              // 굵은 눈썹
    stamp(s, 13, 17, ['1.11.1', '.1111.']); stamp(s, 15, 17, ['22']);                                // 수염 그늘 + 입
    stamp(s, 10, 8, ['3', '3', '3']);
    swordDiag(s, 2, 31, 31.5, 15);                                                                      // 가슴 앞으로 비껴 든 장검
    fill(s, E(6.5, 28.5, 2.6, 2.2), 0, { cx: 6.5, cy: 28, rx: 2.6, ry: 2.2, shade: 1, at: 0.6 });
    return finish(s);
  }
  function aragornB() {
    const s = mk();
    fill(s, body(16, 19, 11, 13), 2, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 3 });
    fill(s, (x, y) => y >= 19 && y < 28 && Math.abs(x - 16) <= 8 - (y - 19) * 0.8, 1, { cx: 16, cy: 21, rx: 8, ry: 5, shade: 2 }); // 두건
    fill(s, OR(E(16, 11, 9, 9), AND(R(7, 11, 25, 21), (x, y) => Math.abs(x - 16) <= 9 - (y - 11) * 0.12 && y < 20.5 - (Math.floor(x) % 2))), 2, { cx: 16, cy: 11, rx: 9, ry: 9, shade: 3, at: 0.2 });
    stamp(s, 25, 12, ['0', '0']);
    swordDiag(s, 22, 33, 31, 3);                                                                        // 앞으로 치켜든 장검
    fill(s, E(24.5, 26.5, 2.6, 2.2), 0, { cx: 24.5, cy: 26, rx: 2.6, ry: 2.2, shade: 1, at: 0.6 });
    return finish(s);
  }

  // ───────── 레골라스 (활) ─────────
  function legolasF() {
    const s = mk();
    fill(s, body(16, 20, 9, 10.5), 2, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 3 });                // 초록 옷
    fill(s, (x, y) => y >= 20 && y < 25 && Math.abs(x - 16) <= 3.2 - (y - 20) * 0.6, 1);
    for (let i = 0; i < 11; i++) px(s, 22 - i, 21 + i, 3);                                             // 화살통 끈
    stamp(s, 5, 17, ['.0.0', '0000', '.33.', '.33.']);                                                 // 어깨 너머 화살깃
    fill(s, OR(E(16, 10.5, 8.8, 8.6), R(8, 10, 12, 26), R(20, 10, 24, 26)), 1, { cx: 16, cy: 12, rx: 9, ry: 12, shade: 2, at: 0.75, hi: 0, hiAt: -0.8 });
    fill(s, (x, y) => E(16, 13, 6.6, 7.2)(x, y) && y > 7.4 + Math.abs(x - 15) * 0.22, 0, { cx: 16, cy: 13, rx: 6.6, ry: 7.2, shade: 1, at: 0.7 });
    stamp(s, 4, 9, ['0...', '.0..', '.00.', '..00', '..00']); stamp(s, 24, 9, flip(['0...', '.0..', '.00.', '..00', '..00']));
    stamp(s, 12, 13, EYE); stamp(s, 19, 13, EYE);
    stamp(s, 15, 17, ['22']);
    // 왼손(화면 오른쪽)에 든 큰 활
    bow(s, 25, 1, 0, 31);
    fill(s, E(28.5, 16, 2.4, 2.4), 0, { cx: 28.5, cy: 16, rx: 2.4, ry: 2.4, shade: 1, at: 0.6 });
    finish(s); bowString(s, 25, 0, 31);
    return s;
  }
  function legolasB() {
    const s = mk();
    fill(s, body(16, 20, 9, 10.5), 2, { cx: 16, cy: 22, rx: 11, ry: 10, shade: 3 });
    // 화살통 (오른 어깨 → 왼 허리) + 깃
    fill(s, (x, y) => { const u = (x - 23) * 0.6 + (y - 12) * 0.8, v = (x - 23) * 0.8 - (y - 12) * 0.6; return u > 0 && u < 22 && Math.abs(v) < 2.2; }, 3, {});
    stamp(s, 21, 6, ['.0.0', '0000', '.00.']);
    fill(s, OR(E(16, 10.5, 8.8, 8.6), (x, y) => y > 10 && y < 27 - Math.abs(x - 16) * 0.8 && Math.abs(x - 16) < 7.5), 1, { cx: 16, cy: 12, rx: 9, ry: 12, shade: 2, at: 0.7, hi: 0, hiAt: -0.8 });
    for (let y = 14; y < 25; y++) px(s, 16, y, y % 2 ? 2 : 1);                                         // 땋은 가닥
    stamp(s, 4, 8, ['0...', '.0..', '.00.', '..00']); stamp(s, 24, 8, flip(['0...', '.0..', '.00.', '..00']));
    // 왼손(화면 왼쪽)에 든 큰 활
    bow(s, 6, -1, 0, 31);
    fill(s, E(3.5, 16, 2.4, 2.4), 0, { cx: 3.5, cy: 16, rx: 2.4, ry: 2.4, shade: 1, at: 0.6 });
    finish(s); bowString(s, 6, 0, 31);
    return s;
  }

  // ───────── 김리 (도끼, 볼가리개 투구) ─────────
  function dwarfHelm(s, back) {
    fill(s, (x, y) => E(16, 8, 8.6, 8)(x, y) && y < 7 && Math.abs(x - 16) < 9.5 - Math.max(0, 3 - y) * 1.3, 1, { cx: 16, cy: 6, rx: 9, ry: 6, shade: 2, hi: 0, hiAt: -0.2 }); // 둥근 투구
    fill(s, R(6, 6, 26, 8), 2, { cx: 16, cy: 7, rx: 10, ry: 2, shade: 3, at: 0.8 });                       // 테
    fill(s, (x, y) => y >= 8 && y < 15 && ((x >= 6.5 && x < 9 - (y > 12 ? 1 : 0)) || (x >= 23 + (y > 12 ? 1 : 0) && x < 25.5)), 2, { cx: 16, cy: 12, rx: 10, ry: 5, shade: 3, at: 0.8 }); // 볼가리개
    stamp(s, 15, 1, ['3', '3', '3', '3', '3']);                                                         // 가운데 솔기
    for (const y of [9, 12]) { px(s, 7, y, 1); px(s, 24, y, 1); }                                          // 징
    if (back) stamp(s, 10, 3, ['3......', '.3.....', '..3....']);
  }
  function gimliF() {
    const s = mk();
    fill(s, body(15, 19, 11, 13), 1, { cx: 15, cy: 22, rx: 12, ry: 10, shade: 2 });                // 사슬갑옷
    for (let y = 22; y < 32; y += 2) for (let x = 3 + (y % 4 ? 0 : 1); x < 29; x += 2) if (s.p[y * 32 + x] >= 0) px(s, x, y, 2);
    fill(s, E(16, 12, 7.4, 6.2), 0, { cx: 16, cy: 12, rx: 7.4, ry: 6.2, shade: 1, at: 0.6 });
    fill(s, (x, y) => y > 14.5 + Math.max(0, 3 - Math.abs(x - 16)) * 0.4 && y < 28 - Math.abs(x - 16) * 0.6 && Math.abs(x - 16) < 7.5 - Math.max(0, y - 21) * 0.5, 2, { cx: 16, cy: 21, rx: 8, ry: 7, shade: 3, at: 0.9, hi: 1, hiAt: -0.5 });
    stamp(s, 11, 15, ['2222222222']);                                                                  // 콧수염
    stamp(s, 15, 13, ['01', '11']);                                                                   // 큰 코
    stamp(s, 12, 11, EYE); stamp(s, 19, 11, EYE);
    stamp(s, 11, 10, ['333']); stamp(s, 18, 10, ['333']);
    dwarfHelm(s, false);
    axe(s, 25, 6, 1, 32);
    fill(s, E(25, 22, 2.4, 2.2), 0, { cx: 26, cy: 22, rx: 2.4, ry: 2.2, shade: 1, at: 0.6 });
    return finish(s);
  }
  function gimliB() {
    const s = mk();
    fill(s, body(17, 19, 11, 13), 1, { cx: 17, cy: 22, rx: 12, ry: 10, shade: 2 });
    for (let y = 22; y < 32; y += 2) for (let x = 5 + (y % 4 ? 0 : 1); x < 31; x += 2) if (s.p[y * 32 + x] >= 0) px(s, x, y, 2);
    stamp(s, 6, 15, ['22', '22', '22']); stamp(s, 24, 15, ['22', '22', '22']);                         // 수염 끝
    fill(s, OR(E(16, 12, 8.6, 8.4), (x, y) => y > 12 && y < 25 - Math.abs(x - 16) * 0.4 && Math.abs(x - 16) < 7.5), 2, { cx: 16, cy: 13, rx: 9, ry: 10, shade: 3, at: 0.6 });
    for (const x of [13, 18]) for (let y = 17; y < 26; y++) px(s, x, y, y % 2 ? 3 : 1);                 // 땋은 머리
    dwarfHelm(s, true);
    axe(s, 6, 6, 1, 32);
    fill(s, E(6, 22, 2.4, 2.2), 0, { cx: 6, cy: 22, rx: 2.4, ry: 2.2, shade: 1, at: 0.6 });
    return finish(s);
  }

  // ───────── 간달프 ─────────
  function gandalfF() {
    const s = mk();
    fill(s, body(16, 19, 10.5, 12), 1, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 2 });               // 회색 망토
    fill(s, E(16, 19.5, 8, 2), 0, { cx: 16, cy: 19.5, rx: 8, ry: 2, shade: 1 });                      // 은빛 목도리
    fill(s, OR(R(8, 10, 11, 20), R(21, 10, 24, 20)), 0, { cx: 16, cy: 14, rx: 8, ry: 6, shade: 1 }); // 옆 흰머리
    fill(s, E(16, 13.5, 6, 5.6), 0, { cx: 16, cy: 13, rx: 6, ry: 5.6, shade: 1, at: 0.55 });
    // 긴 수염
    fill(s, (x, y) => y > 15 && y < 31 && Math.abs(x - 16) < 6.5 - Math.max(0, y - 21) * 0.55, 0, { cx: 16, cy: 22, rx: 7, ry: 9, shade: 1, at: 0.45 });
    stamp(s, 12, 16, ['00000000']); stamp(s, 15, 17, ['22']);
    stamp(s, 12, 13, EYE.slice(0, 1)); stamp(s, 19, 13, EYE.slice(0, 1));
    stamp(s, 10, 11, ['0000']); stamp(s, 18, 11, ['0000']);                                          // 덥수룩한 눈썹
    // 뾰족 모자 (끝이 살짝 꺾임)
    fill(s, (x, y) => y < 10.5 && y > 0 && Math.abs(x - (16 + (10 - y) * (10 - y) * 0.05)) < y * 0.6 + 0.3, 2, { cx: 17, cy: 5, rx: 4, ry: 6, shade: 3, at: 0.3 });
    fill(s, E(16, 10, 12, 1.9), 2, { cx: 16, cy: 10, rx: 12, ry: 2, shade: 3, at: 0.5 });
    // 지팡이 + 손
    fill(s, R(2, 4, 4, 32), 2, { cx: 3, cy: 18, rx: 2, ry: 14, shade: 3 }); stamp(s, 1, 1, ['.33.', '3223', '3223', '.33.']);
    fill(s, E(4, 23, 2.2, 2), 0);
    return finish(s);
  }
  function gandalfB() {
    const s = mk();
    fill(s, body(16, 19, 10.5, 12), 1, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 2 });
    fill(s, R(28, 4, 30, 32), 2, { cx: 29, cy: 18, rx: 2, ry: 14, shade: 3 }); stamp(s, 27, 1, ['.33.', '3223', '3223', '.33.']);
    fill(s, E(27.5, 23, 2.2, 2), 0);
    fill(s, (x, y) => y > 9 && y < 26 - Math.abs(x - 16) * 0.5 && Math.abs(x - 16) < 7.5, 0, { cx: 16, cy: 15, rx: 8, ry: 9, shade: 1, at: 0.5 });
    fill(s, (x, y) => y < 10.5 && y > 0 && Math.abs(x - (16 + (10 - y) * (10 - y) * 0.05)) < y * 0.6 + 0.3, 2, { cx: 17, cy: 5, rx: 4, ry: 6, shade: 3, at: 0.3 });
    fill(s, E(16, 10, 12, 1.9), 2, { cx: 16, cy: 10, rx: 12, ry: 2, shade: 3, at: 0.5 });
    return finish(s);
  }

  // ───────── 농부 매곳네 개 '송곳니' (적, 40×40 앞 3/4) ─────────
  function dog() {
    const s = mk(40, 40);
    fill(s, (x, y) => { const t = (x - 30) / 6; return y > 10 && y < 22 && Math.abs(x - (31 + (22 - y) * 0.25)) < 1.6; }, 2, {});   // 꼬리
    fill(s, R(27, 28, 31, 38), 2, { cx: 29, cy: 33, rx: 2, ry: 5, shade: 3 });                       // 먼 뒷다리
    fill(s, E(24, 24, 9.5, 6.5), 1, { cx: 24, cy: 24, rx: 9.5, ry: 6.5, shade: 2, at: 0.35 });      // 몸통
    fill(s, R(31, 26, 35, 38), 1, { cx: 33, cy: 32, rx: 2, ry: 6, shade: 2 });                       // 가까운 뒷다리
    fill(s, E(14, 25, 6, 7), 1, { cx: 14, cy: 25, rx: 6, ry: 7, shade: 2, at: 0.5 });               // 가슴
    fill(s, R(9, 28, 13, 38), 1, { cx: 11, cy: 33, rx: 2, ry: 5, shade: 2 });                        // 앞다리
    fill(s, R(15, 29, 19, 38), 1, { cx: 17, cy: 33, rx: 2, ry: 5, shade: 2 });
    fill(s, E(13, 19.5, 6.5, 1.6), 3, {});                                                           // 목줄
    fill(s, E(12, 13, 6.6, 6), 1, { cx: 12, cy: 13, rx: 6.6, ry: 6, shade: 2, at: 0.5, hi: 0, hiAt: -0.7 }); // 머리
    stamp(s, 13, 4, ['..33', '.322', '3220', '322.']);                                                // 귀(뒤로 젖힘)
    stamp(s, 5, 5, ['3...', '23..', '223.', '.2..']);
    fill(s, E(6, 16, 4.6, 2.6), 0, { cx: 6, cy: 16, rx: 4.6, ry: 2.6, shade: 1, at: 0.4 });           // 주둥이
    stamp(s, 2, 17, ['30303', '33333', '.3030']);                                                     // 이빨 드러낸 입
    stamp(s, 1, 14, ['33', '33']);                                                                    // 코
    stamp(s, 10, 11, ['333', '.03']); stamp(s, 15, 11, ['333', '30.']);                               // 성난 눈
    stamp(s, 20, 20, ['0']);                                                                          // 목줄 고리
    return finish(s, 8);
  }

  function toCanvas(s, scale, pal) {
    pal = pal || GB; scale = scale || 1;
    const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const t = s.p[y * s.w + x]; if (t >= 0) { g.fillStyle = pal[t]; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }
  root.RingGB32 = {
    GB, toCanvas, dog,
    heroes: [
      { name: '프로도', front: frodoF, back: frodoB }, { name: '샘', front: samF, back: samB },
      { name: '아라곤', front: aragornF, back: aragornB }, { name: '레골라스', front: legolasF, back: legolasB },
      { name: '김리', front: gimliF, back: gimliB }, { name: '간달프', front: gandalfF, back: gandalfB },
    ],
  };
})(typeof window !== 'undefined' ? window : globalThis);
