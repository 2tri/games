// 「반지 원정」 선화 방식 도트 — 게임보이 원작 작법 분석 반영
// 1) 부위마다 자기 테두리를 1픽셀 검은 선으로 (덩어리 테두리 X)
// 2) 흰 바탕을 넓게, 어두운 곳은 검정/어두운회, 중간 톤은 바둑판 점묘
// 3) 3/4 각도·동작 자세
// 톤: 0=흰 1=밝은회 2=어두운회 3=검정
(function (root) {
  'use strict';
  const GB = ['#f8f8f0', '#b0b0a8', '#606060', '#181818'];
  const mk = (w, h) => ({ w, h, p: new Int8Array(w * h).fill(-1) });
  const inb = (s, x, y) => x >= 0 && y >= 0 && x < s.w && y < s.h;
  const px = (s, x, y, t) => { if (inb(s, x, y)) s.p[y * s.w + x] = t; };
  const D = (a, b) => (x, y) => ((x + y) & 1) ? a : b;                 // 바둑판 점묘
  const P = pts => (x, y) => { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
  const E = (cx, cy, rx, ry) => (x, y) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
  const OR = (...m) => (x, y) => m.some(f => f(x, y));
  // 굵기가 변하는 관(팔·다리·뿔·채찍): 꺾은선 pts, 반지름 r0→r1
  function tube(pts, r0, r1) {
    const seg = []; let L = 0;
    for (let i = 0; i < pts.length - 1; i++) { const [a, b] = [pts[i], pts[i + 1]], l = Math.hypot(b[0] - a[0], b[1] - a[1]); seg.push([a, b, l, L]); L += l; }
    return (x, y) => seg.some(([a, b, l, L0]) => {
      const t = Math.max(0, Math.min(1, ((x - a[0]) * (b[0] - a[0]) + (y - a[1]) * (b[1] - a[1])) / (l * l || 1)));
      const qx = a[0] + (b[0] - a[0]) * t, qy = a[1] + (b[1] - a[1]) * t, r = r0 + (r1 - r0) * (L0 + l * t) / L;
      return (x - qx) ** 2 + (y - qy) ** 2 <= r * r;
    });
  }
  // 부위 그리기: 안쪽은 tone(x,y), 자기 테두리는 검정 선. rim=왼쪽 위 안쪽 테두리 빛, dark=오른쪽 아래 그늘 영역
  function shape(s, mask, tone, o) {
    o = o || {};
    const W = s.w, H = s.h, m = new Uint8Array(W * H), tf = typeof tone === 'function' ? tone : () => tone;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (mask(x + 0.5, y + 0.5)) m[y * W + x] = 1;
    const at = (x, y) => inb(s, x, y) && m[y * W + x];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (!m[y * W + x]) continue;
      const edge = !(at(x + 1, y) && at(x - 1, y) && at(x, y + 1) && at(x, y - 1));
      let t = tf(x, y);
      if (o.dark && o.dark(x + 0.5, y + 0.5)) t = typeof o.darkTone === 'function' ? o.darkTone(x, y) : (o.darkTone ?? 2);
      if (o.rim !== undefined && !edge && (!at(x - 1, y) || !at(x, y - 1) || !at(x - 1, y - 1)) ) t = o.rim;
      if (edge && o.line !== false) t = o.lineTone ?? 3;
      s.p[y * W + x] = t;
    }
  }
  function stroke(s, pts, t) {
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[i + 1], n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1;
      for (let k = 0; k <= n; k++) px(s, Math.round(x0 + (x1 - x0) * k / n), Math.round(y0 + (y1 - y0) * k / n), t);
    }
  }
  function stamp(s, x0, y0, rows) { rows.forEach((r, j) => [...r].forEach((c, i) => { if (c !== '.') px(s, x0 + i, y0 + j, +c); })); }
  // 불꽃 혀 (흰 속 + 검은 선): 바닥 가운데, 반폭, 끝점
  function flame(s, bx, by, w, tx, ty) {
    const mx = (bx + tx) / 2, my = (by + ty) / 2, nx = -(ty - by), ny = tx - bx, k = 0.18;
    shape(s, P([[bx - w, by], [mx - w * 0.6 + nx * k, my + ny * k], [tx, ty], [mx + w * 0.5 - nx * k * 0.5, my - ny * k * 0.5], [bx + w, by]]), 0);
  }

  // ═════════ 발로그 56×56 — 3/4 왼쪽으로 내딛는 자세, 채찍을 휘두르고 칼은 낮게 ═════════
  function balrog() {
    const s = mk(56, 56);
    // 날개 (뒤): 어두운회 막 + 아래쪽 점묘, 검은 뼈
    const wl = [[22, 21], [17, 14], [10, 7], [2, 1], [2, 8], [4, 13], [1, 19], [5, 24], [3, 31], [8, 28], [11, 33], [15, 28], [19, 31], [22, 26]];
    const wr = [[33, 19], [39, 11], [47, 4], [55, 0], [54, 8], [52, 13], [55, 20], [51, 25], [53, 32], [48, 28], [45, 33], [41, 27], [37, 30], [34, 24]];
    for (const w of [wl, wr]) shape(s, P(w), (x, y) => y > 18 ? D(3, 2)(x, y) : 2);
    for (const [a, b] of [[[21, 21], [3, 2]], [[21, 22], [2, 19]], [[21, 23], [8, 29]], [[21, 24], [15, 29]]]) stroke(s, [a, b], 3);
    for (const [a, b] of [[[34, 19], [54, 1]], [[34, 20], [54, 20]], [[34, 22], [48, 29]], [[34, 23], [41, 28]]]) stroke(s, [a, b], 3);
    // 등 뒤로 날리는 불꽃 갈기
    [[24, 12, 3, 18, 1], [28, 11, 3, 27, 0], [31, 13, 3, 36, 2], [35, 17, 3, 43, 8], [37, 21, 3, 47, 16], [21, 15, 2, 14, 6]]
      .forEach(a => flame(s, ...a));
    // 뒷다리(오른쪽, 뒤로 뻗음)
    shape(s, tube([[34, 38], [40, 45], [41, 53]], 4.2, 2.6), D(3, 2), { rim: 2 });
    stamp(s, 38, 53, ['30303', '33333']);
    // 몸통: 검정, 왼쪽 위 테두리 빛 + 용암 금(흰)
    shape(s, P([[17, 22], [33, 19], [40, 25], [39, 35], [31, 42], [20, 41], [14, 32]]), 3, { rim: 2 });
    stroke(s, [[23, 25], [25, 29], [23, 33], [26, 37]], 0); stroke(s, [[31, 24], [29, 29], [32, 33]], 0); stroke(s, [[27, 33], [29, 39]], 1);
    // 앞다리(왼쪽, 앞으로 내딛음)
    shape(s, tube([[22, 38], [17, 45], [15, 53]], 4.6, 2.8), 3, { rim: 2 });
    stamp(s, 11, 53, ['303030', '333333']);
    // 오른팔 + 낮게 든 불칼
    shape(s, tube([[36, 24], [43, 29], [46, 35]], 3.6, 2.6), 3, { rim: 2 });
    shape(s, P([[46, 37], [49, 37], [55, 54], [52, 55]]), 0);                                        // 칼날
    for (const [x, y] of [[50, 41], [52, 46], [54, 51]]) stamp(s, x + 1, y - 1, ['0', '30']);       // 칼날 불꽃
    shape(s, P([[42, 35], [51, 35], [51, 38], [42, 38]]), 1);                                         // 코등이
    shape(s, E(46.5, 35, 3, 2.8), 3, { rim: 2 });
    // 왼팔을 앞으로 휘두르며 채찍
    shape(s, tube([[19, 25], [11, 29], [6, 36]], 3.6, 2.8), 3, { rim: 2 });
    shape(s, E(6, 37.5, 3, 2.8), 3, { rim: 2 });
    shape(s, tube([[5, 40], [3, 45], [6, 49], [12, 50], [17, 47], [21, 49], [20, 54]], 1.6, 0.9), 0);
    for (const [x, y] of [[2, 47], [13, 52], [22, 46]]) stamp(s, x, y, ['.0.', '000', '.0.']);      // 불똥
    // 머리 (3/4, 왼쪽을 노려봄) + 뿔
    shape(s, tube([[19, 12], [14, 9], [10, 8], [7, 4], [7, 1]], 2.4, 0.8), D(1, 0), { rim: 0 });      // 앞쪽 뿔
    shape(s, tube([[29, 11], [33, 8], [35, 4], [35, 1]], 2, 0.7), 1);                                  // 뒤쪽 뿔
    shape(s, P([[18, 11], [27, 9], [31, 13], [30, 19], [26, 23], [20, 22], [16, 17]]), 3, { rim: 2 });
    stroke(s, [[18, 14], [23, 13], [26, 12]], 2);                                                       // 이마 주름
    stamp(s, 19, 15, ['000', '..00']); stamp(s, 26, 14, ['00', '.0']);                                  // 이글거리는 눈
    stamp(s, 19, 19, ['01010', '.000.']);                                                               // 불을 머금은 입
    return s;
  }

  // ═════════ 골룸 40×40 — 3/4 왼쪽, 네 발로 웅크려 다가옴 ═════════
  function gollum() {
    const s = mk(40, 40);
    const skin = D(0, 1), skinD = D(1, 2);
    // 먼 쪽 팔·다리
    shape(s, tube([[27, 26], [31, 31], [33, 37]], 2, 1.4), skinD);
    shape(s, tube([[33, 37], [38, 38]], 1.3, 1), skinD);
    shape(s, tube([[22, 23], [24, 30], [23, 36]], 1.6, 1.2), skinD);
    stamp(s, 21, 36, ['3.3.3']);
    // 굽은 등 몸통
    shape(s, P([[15, 20], [22, 16], [29, 18], [33, 24], [30, 30], [21, 31], [15, 27]]), 0,
      { dark: (x, y) => x + y * 0.8 > 50, darkTone: skin });
    stamp(s, 21, 16, ['3.3.3']); stamp(s, 22, 15, ['.0.0']);                                           // 등뼈 마디
    stroke(s, [[20, 22], [22, 25]], 1); stroke(s, [[23, 21], [25, 25]], 1);                            // 갈비뼈
    shape(s, P([[20, 28], [29, 27], [28, 32], [21, 32]]), D(2, 3));                                    // 허리 천
    // 가까운 다리: 무릎을 어깨까지 접음
    shape(s, tube([[22, 30], [16, 27], [12, 32], [11, 37]], 2.6, 1.6), 0, { dark: (x, y) => y > 33, darkTone: skin });
    shape(s, tube([[11, 37], [5, 38]], 1.5, 1.1), 0);
    stamp(s, 3, 37, ['3.3', '...']);
    // 가까운 팔: 땅을 짚은 앙상한 팔과 긴 손가락
    shape(s, tube([[16, 21], [11, 27], [8, 34]], 1.8, 1.2), 0);
    stamp(s, 5, 34, ['3.3.3', '.3.3.']);
    // 큰 머리 (앞으로 쭉 내민)
    shape(s, tube([[20, 11], [26, 6], [29, 5]], 2.2, 0.6), skin);                                       // 뒤로 젖힌 귀
    shape(s, E(13, 14, 8, 7), 0, { dark: (x, y) => x > 16 && y > 14, darkTone: skin });
    // 왕방울 눈: 가까운 눈 크게, 먼 눈 작게
    shape(s, E(9.5, 13, 3.2, 3.6), 0);
    stamp(s, 9, 12, ['33', '33', '.3']); px(s, 9, 12, 0);
    shape(s, E(16, 12, 2.4, 2.8), 0);
    stamp(s, 16, 11, ['3', '3']);
    stroke(s, [[6, 9], [9, 9], [12, 10]], 3); stroke(s, [[14, 9], [17, 9]], 3);                         // 눈두덩
    stroke(s, [[6, 18], [9, 19], [13, 19], [16, 18]], 3); stamp(s, 9, 20, ['0.0']);                    // 히죽 웃는 입, 이 두 개
    stroke(s, [[12, 7], [11, 3], [9, 1]], 3); stroke(s, [[15, 7], [16, 3]], 3);                         // 몇 가닥 머리털
    return s;
  }

  function toCanvas(s, scale) {
    scale = scale || 1; const c = document.createElement('canvas'); c.width = s.w * scale; c.height = s.h * scale;
    const g = c.getContext('2d');
    for (let y = 0; y < s.h; y++) for (let x = 0; x < s.w; x++) { const t = s.p[y * s.w + x]; if (t >= 0) { g.fillStyle = GB[t]; g.fillRect(x * scale, y * scale, scale, scale); } }
    return c;
  }
  root.RingLine = { GB, toCanvas, balrog, gollum, lib: { mk, px, D, P, E, OR, tube, shape, stroke, stamp, flame } };
})(typeof window !== 'undefined' ? window : globalThis);
