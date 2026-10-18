// 「반지 원정」 적·주요 인물 시안 — 게임보이 4단계 도트 (gb32.js 도구 사용)
// 적은 앞모습 1배: 일반 40×40, 우두머리 56×56. 인물은 32×32.
(function (root) {
  'use strict';
  const { mk, fill, E, OR, R, P, px, stamp, flip, finish, body, swordDiag, EYE } = root.RingGB32.lib;
  const mirror = (pts, W) => pts.map(([x, y]) => [W - x, y]);
  function line(s, x0, y0, x1, y1, t, w) {
    const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1;
    for (let i = 0; i <= n; i++) { const x = Math.round(x0 + (x1 - x0) * i / n), y = Math.round(y0 + (y1 - y0) * i / n); px(s, x, y, t); if (w) px(s, x + 1, y, t); }
  }
  // 불꽃 혀: 바닥 가운데(bx,by), 너비 w, 끝(tx,ty) — 밝은회 바깥 + 흰 속
  function flame(s, bx, by, w, tx, ty) {
    fill(s, P([[bx - w, by], [bx + w, by], [tx, ty]]), 1, {});
    fill(s, P([[bx - w * 0.4, by], [bx + w * 0.4, by], [bx + (tx - bx) * 0.55, by + (ty - by) * 0.55]]), 0, { noLine: true });
  }

  // ───────── 발로그 (우두머리 56×56) ─────────
  function balrog() {
    const s = mk(56, 56), W = 56;
    // 그림자 날개
    const wingL = [[22, 22], [15, 11], [5, 2], [0, 9], [0, 22], [2, 33], [7, 29], [10, 37], [15, 31], [18, 37], [22, 30]];
    fill(s, OR(P(wingL), P(mirror(wingL, W))), 3, {});
    for (const [a, b] of [[[21, 22], [5, 3]], [[21, 23], [1, 22]], [[21, 25], [9, 35]], [[21, 26], [17, 35]]]) {
      line(s, a[0], a[1], b[0], b[1], 2); line(s, W - 1 - a[0], a[1], W - 1 - b[0], b[1], 2);           // 날개뼈
    }
    // 머리·어깨 뒤 불꽃
    [[20, 13, 3, 16, 1], [24, 11, 3, 23, 0], [28, 10, 3, 29, 0], [32, 11, 3, 34, 1], [36, 13, 3, 41, 3], [15, 22, 3, 11, 11], [41, 22, 3, 46, 10]]
      .forEach(([bx, by, w, tx, ty]) => flame(s, bx, by, w, tx, ty));
    // 다리
    fill(s, OR(R(19, 43, 26, 54), R(30, 43, 37, 54)), 2, { cx: 28, cy: 48, rx: 10, ry: 6, shade: 3, at: 0.5 });
    stamp(s, 17, 53, ['3.3.3.3.3']); stamp(s, 30, 53, ['3.3.3.3.3'].map(r => r.slice(0, 8)));            // 발톱
    // 몸통 + 용암 금
    fill(s, P([[17, 21], [39, 21], [43, 29], [38, 46], [18, 46], [13, 29]]), 2, { cx: 28, cy: 32, rx: 14, ry: 13, shade: 3, at: 0.35 });
    for (const pts of [[[23, 26], [25, 30], [23, 34], [25, 38]], [[33, 26], [31, 31], [34, 35], [31, 40]], [[28, 36], [27, 41], [29, 44]]])
      for (let i = 0; i < pts.length - 1; i++) line(s, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 1);
    // 왼팔(화면 왼쪽) + 불채찍
    fill(s, P([[14, 23], [19, 26], [13, 40], [7, 41], [7, 37]]), 2, { cx: 12, cy: 32, rx: 6, ry: 9, shade: 3, at: 0.4 });
    fill(s, E(8.5, 41.5, 3.4, 3), 2, { cx: 8, cy: 41, rx: 3, ry: 3, shade: 3, at: 0.5 });
    for (let y = 44; y < 56; y++) { const x = Math.round(7 + Math.sin((y - 44) / 2.2) * 3 - (y - 44) * 0.3); px(s, x, y, 1); px(s, x + 1, y, 0); }
    // 오른팔 + 불칼
    fill(s, P(mirror([[14, 23], [19, 26], [13, 40], [7, 41], [7, 37]], W)), 2, { cx: 44, cy: 32, rx: 6, ry: 9, shade: 3, at: 0.4 });
    fill(s, P([[46, 6], [50, 2], [51, 38], [46, 38]]), 0, { cx: 48, cy: 20, rx: 2.5, ry: 18, shade: 1, at: 0.2 });
    for (let y = 6; y < 37; y += 4) { px(s, 45, y, 1); px(s, 52, y + 2, 1); }                              // 칼날 불꽃
    fill(s, R(43, 38, 54, 40), 1, {});                                                                       // 코등이
    fill(s, E(47.5, 41.5, 3.4, 3), 2, { cx: 47, cy: 41, rx: 3, ry: 3, shade: 3, at: 0.5 });
    // 머리 + 뿔
    fill(s, E(28, 16.5, 7, 6.2), 2, { cx: 28, cy: 16, rx: 7, ry: 6, shade: 3, at: 0.3 });
    const horn = [[23, 13], [17, 11], [11, 12], [6, 9], [4, 3], [7, 0], [8, 5], [12, 7], [18, 7], [25, 10]];
    fill(s, OR(P(horn), P(mirror(horn, W))), 1, { cx: 28, cy: 7, rx: 18, ry: 5, shade: 2, at: 0.6 });
    stamp(s, 23, 15, ['000.', '.000']); stamp(s, 29, 15, ['.000', '000.']);                                 // 불타는 눈
    stamp(s, 24, 19, ['30303030', '.3.3.3.']);                                                              // 송곳니 입
    return finish(s, 14);
  }

  // ───────── 동굴 트롤 (우두머리 56×56) ─────────
  function caveTroll() {
    const s = mk(56, 56);
    fill(s, OR(R(17, 44, 25, 55), R(31, 44, 39, 55)), 1, { cx: 28, cy: 48, rx: 12, ry: 7, shade: 2, at: 0.4 });     // 다리
    fill(s, E(28, 34, 16, 14), 1, { cx: 28, cy: 34, rx: 16, ry: 14, shade: 2, at: 0.35 });                         // 몸
    fill(s, E(28, 39, 10, 8), 1, { cx: 28, cy: 39, rx: 10, ry: 8, shade: 2, hi: 0, hiAt: -0.4, at: 0.7 });        // 배
    fill(s, R(19, 42, 37, 47), 2, { cx: 28, cy: 44, rx: 9, ry: 3, shade: 3, at: 0.6 });                            // 허리 가죽
    // 팔: 왼쪽은 늘어뜨린 주먹, 오른쪽은 망치
    fill(s, P([[14, 24], [20, 27], [12, 44], [5, 44], [6, 36]]), 1, { cx: 12, cy: 34, rx: 7, ry: 10, shade: 2, at: 0.4 });
    fill(s, E(7.5, 46, 5, 4.5), 1, { cx: 7, cy: 46, rx: 5, ry: 4.5, shade: 2, at: 0.4 });
    fill(s, R(44, 6, 47, 44), 2, { cx: 45, cy: 25, rx: 2, ry: 19, shade: 3, at: 0.5 });                             // 망치 자루
    fill(s, R(38, 2, 54, 11), 2, { cx: 46, cy: 6, rx: 8, ry: 5, shade: 3, hi: 1, hiAt: -0.2, at: 0.6 });           // 망치 머리
    fill(s, P([[42, 24], [36, 27], [43, 42], [50, 42], [50, 34]]), 1, { cx: 44, cy: 34, rx: 7, ry: 10, shade: 2, at: 0.4 });
    fill(s, E(46, 42, 4.6, 4), 1, { cx: 46, cy: 42, rx: 4.6, ry: 4, shade: 2, at: 0.4 });
    // 작은 머리 (어깨 사이에 파묻힘)
    fill(s, E(28, 17, 7.5, 6.5), 1, { cx: 28, cy: 17, rx: 7.5, ry: 6.5, shade: 2, at: 0.35 });
    stamp(s, 24, 15, ['3', '3']); stamp(s, 31, 15, ['3', '3']);
    stamp(s, 26, 17, ['.22.', '2112']);                                                                            // 뭉툭한 코
    stamp(s, 23, 20, ['3333333333', '3.0.0.0.03'].map(r => r.slice(0, 10)));                                       // 벌린 입
    for (let x = 20; x <= 36; x += 2) px(s, x, 25, x % 4 ? 3 : 0);                                                 // 목사슬
    return finish(s, 14);
  }

  // ───────── 검은 기사 (40×40) ─────────
  function blackRider() {
    const s = mk(40, 40);
    // 너덜너덜한 망토
    const hem = []; for (let x = 36; x >= 4; x -= 2) hem.push([x, x % 4 ? 39 : 36]);
    fill(s, P([[20, 3], [27, 8], [31, 18], [36, 36], ...hem, [4, 36], [9, 18], [13, 8]]), 2, { cx: 20, cy: 22, rx: 15, ry: 18, shade: 3, at: 0.3 });
    for (const x of [13, 19, 25, 30]) line(s, x, 22, x + (x > 20 ? 2 : -2), 36, 3);                              // 주름
    // 두건 + 텅 빈 얼굴
    fill(s, E(20, 11, 7.5, 8), 2, { cx: 20, cy: 11, rx: 7.5, ry: 8, shade: 3, at: 0.35, hi: 1, hiAt: -0.1 });
    fill(s, P([[16, 9], [24, 9], [25, 17], [20, 19], [15, 17]]), 3, {});
    // 쇠장갑 손 + 모르굴 칼
    swordDiag(s, 26, 31, 38, 6);
    fill(s, E(28.5, 27.5, 2.6, 2.4), 1, { cx: 28, cy: 27, rx: 2.6, ry: 2.4, shade: 2, at: 0.5 });
    fill(s, E(10, 26, 2.6, 2.4), 1, { cx: 10, cy: 26, rx: 2.6, ry: 2.4, shade: 2, at: 0.5 });
    stamp(s, 7, 28, ['3.3.3']);                                                                                     // 갈퀴 손끝
    return finish(s, 10);
  }

  // ───────── 골룸 (40×40) ─────────
  function gollum() {
    const s = mk(40, 40);
    // 개구리처럼 접은 다리
    fill(s, OR(E(10, 31, 4.6, 5.5), E(30, 31, 4.6, 5.5)), 1, { cx: 20, cy: 30, rx: 14, ry: 6, shade: 2, at: 0.5 });
    fill(s, OR(E(8, 37, 4.5, 1.8), E(32, 37, 4.5, 1.8)), 1, { cx: 20, cy: 37, rx: 14, ry: 2, shade: 2, at: 0.6 });
    // 앙상한 몸 + 갈비뼈
    fill(s, E(20, 27, 6.5, 6), 1, { cx: 20, cy: 27, rx: 6.5, ry: 6, shade: 2, at: 0.4 });
    for (const y of [24, 26, 28]) { px(s, 17, y, 2); px(s, 18, y, 2); px(s, 22, y, 2); px(s, 23, y, 2); }
    fill(s, R(16, 31, 25, 35), 2, { cx: 20, cy: 33, rx: 4, ry: 2, shade: 3, at: 0.6 });                            // 허리 천
    // 땅을 짚은 가는 팔
    for (const [a, b] of [[[15, 24], [12, 36]], [[25, 24], [28, 36]]]) fill(s, (x, y) => { const t = (y - a[1]) / (b[1] - a[1]); return t >= 0 && t <= 1 && Math.abs(x - (a[0] + (b[0] - a[0]) * t)) < 1.1; }, 1, {});
    fill(s, OR(E(12, 37, 2.6, 1.4), E(28, 37, 2.6, 1.4)), 1, {});
    // 큰 머리, 뾰족 귀
    fill(s, OR(P([[11, 13], [5, 9], [8, 15], [12, 17]]), P([[29, 13], [35, 9], [32, 15], [28, 17]])), 1, { cx: 20, cy: 13, rx: 14, ry: 4, shade: 2, at: 0.6 });
    fill(s, E(20, 13.5, 9, 8), 1, { cx: 20, cy: 13, rx: 9, ry: 8, shade: 2, at: 0.45, hi: 0, hiAt: -0.5 });
    // 왕방울 눈
    for (const cx of [16, 24]) { fill(s, E(cx, 13, 3, 3.2), 0, { noLine: false }); }
    stamp(s, 15, 13, ['33', '33']); stamp(s, 24, 13, ['33', '33']); px(s, 15, 13, 0); px(s, 24, 13, 0);
    stamp(s, 16, 18, ['3.3.3.3', '.30303.'].map(r => r.slice(0, 7)));                                             // 이 몇 개
    // 몇 가닥 남은 머리털
    line(s, 18, 6, 15, 2, 3); line(s, 23, 6, 25, 3, 3);
    return finish(s, 8);
  }

  // ───────── 사루만 (40×40) ─────────
  function saruman() {
    const s = mk(40, 40);
    fill(s, body(19, 20, 10, 13), 0, { cx: 19, cy: 24, rx: 13, ry: 12, shade: 1, at: 0.3 });                      // 흰 옷
    for (const x of [12, 26]) line(s, x, 26, x + (x > 19 ? 2 : -2), 39, 1);
    // 곧게 내린 흰 머리
    fill(s, OR(R(10, 9, 14, 30), R(24, 9, 28, 30), E(19, 10, 9, 7.5)), 1, { cx: 19, cy: 14, rx: 9, ry: 14, shade: 2, hi: 0, hiAt: -0.3, at: 0.8 });
    fill(s, (x, y) => E(19, 14, 5.8, 6.4)(x, y) && y > 8.5, 0, { cx: 19, cy: 14, rx: 6, ry: 6.4, shade: 1, at: 0.6 });
    stamp(s, 15, 12, ['22.', '.22']); stamp(s, 21, 12, ['.22', '22.']);                                           // 성난 눈썹
    stamp(s, 16, 14, EYE); stamp(s, 22, 14, EYE);
    // 길고 끝이 갈라진 수염
    fill(s, (x, y) => y > 17 && y < 37 && Math.abs(x - 19) < 5 - Math.max(0, y - 25) * 0.35 && !(y > 31 && Math.abs(x - 19) < 0.8), 1, { cx: 19, cy: 26, rx: 5, ry: 10, shade: 2, hi: 0, hiAt: -0.3, at: 0.7 });
    stamp(s, 16, 18, ['1111111']);
    // 검은 지팡이 + 갈퀴 머리에 박힌 흰 돌
    fill(s, R(33, 7, 35, 40), 3, {});
    stamp(s, 30, 0, ['3.....3', '3..3..3', '.3.0.3.', '.30003.', '..303..', '...3...', '...3...']);
    fill(s, E(32.5, 24, 2.6, 2.4), 0, { cx: 32, cy: 24, rx: 2.6, ry: 2.4, shade: 1, at: 0.5 });
    return finish(s, 10);
  }

  // ───────── 우루크하이 (40×40) ─────────
  const HAND = ['0.0.0.', '0.0.0.', '000000', '00000.', '.000..'];   // 흰 손 표식
  function urukHai() {
    const s = mk(40, 40);
    fill(s, body(21, 20, 12, 15), 2, { cx: 21, cy: 26, rx: 14, ry: 12, shade: 3, at: 0.3 });                     // 검은 갑옷
    fill(s, R(15, 23, 28, 33), 1, { cx: 21, cy: 28, rx: 7, ry: 6, shade: 2, at: 0.5 });                           // 가슴판
    // 긴 검은 머리
    fill(s, OR(R(12, 12, 16, 26), R(26, 12, 30, 26)), 3, {});
    fill(s, E(21, 15, 7.4, 7), 2, { cx: 21, cy: 15, rx: 7.4, ry: 7, shade: 3, at: 0.5 });                        // 어두운 얼굴
    stamp(s, 16, 14, ['00', '03']); stamp(s, 24, 14, ['00', '30']);                                               // 노려보는 눈
    stamp(s, 17, 19, ['3030303', '.3.3.3.'].map(r => r.slice(0, 7)));                                             // 이
    // 투구 + 흰 손 표식
    fill(s, (x, y) => E(21, 12, 8.6, 8)(x, y) && y < 12.5, 1, { cx: 21, cy: 9, rx: 8.6, ry: 5, shade: 2, hi: 0, hiAt: -0.3, at: 0.6 });
    fill(s, R(20, 0, 23, 6), 2, {});                                                                               // 볏
    stamp(s, 19, 6, HAND.slice(1, 5).map(r => r.slice(0, 5)));
    // 둥근 방패 (흰 손)
    fill(s, E(8, 28, 7, 8.5), 1, { cx: 8, cy: 28, rx: 7, ry: 8.5, shade: 2, at: 0.4 });
    stamp(s, 6, 25, HAND);
    // 넓적한 언월도
    fill(s, P([[31, 30], [33, 30], [37, 8], [39, 2], [39, 12], [35, 31]]), 1, { cx: 36, cy: 16, rx: 3, ry: 14, shade: 2, at: 0.3 });
    fill(s, R(29, 30, 38, 32), 3, {});
    fill(s, E(33, 33.5, 2.6, 2.2), 2, { cx: 33, cy: 33, rx: 2.6, ry: 2.2, shade: 3, at: 0.5 });
    return finish(s, 10);
  }

  // ───────── 보로미르 (32×32) ─────────
  function boromir() {
    const s = mk();
    fill(s, body(16, 20, 10, 12), 2, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 3 });                               // 곤도르 망토
    fill(s, (x, y) => y >= 21 && Math.abs(x - 16) <= 4.5, 1, { cx: 16, cy: 25, rx: 4, ry: 6, shade: 2 });        // 웃옷
    fill(s, OR(E(9, 20.5, 4, 2.6), E(23, 20.5, 4, 2.6)), 1, { cx: 16, cy: 20, rx: 10, ry: 3, shade: 2, hi: 0, hiAt: -0.2, at: 0.6 }); // 털깃
    // 어깨까지 오는 갈색 머리
    fill(s, OR(E(16, 10.5, 8.8, 8.4), R(7, 10, 11, 20), R(21, 10, 25, 20)), 2, { cx: 16, cy: 10, rx: 9, ry: 9, shade: 3, at: 0.6, hi: 1, hiAt: -0.4 });
    fill(s, (x, y) => E(16, 13, 6.4, 7.2)(x, y) && y > 7.8 + Math.abs(x - 17) * 0.2, 0, { cx: 16, cy: 13, rx: 6.4, ry: 7.2, shade: 1, at: 0.6 });
    stamp(s, 12, 13, EYE); stamp(s, 19, 13, EYE);
    stamp(s, 11, 11, ['333']); stamp(s, 18, 11, ['333']);
    stamp(s, 12, 16, ['1......1', '11.22.11', '.111111.']);                                                       // 짧은 수염
    // 곤도르의 뿔나팔 (허리)
    stamp(s, 2, 24, ['.0000.', '3000003', '.3..000', '.....03']);
    // 둥근 방패
    fill(s, E(27, 26, 5, 5.5), 1, { cx: 27, cy: 26, rx: 5, ry: 5.5, shade: 2, hi: 0, hiAt: -0.3, at: 0.6 });
    stamp(s, 26, 25, ['00', '00']);
    return finish(s);
  }

  // ───────── 갈라드리엘 (32×32) ─────────
  function galadriel() {
    const s = mk();
    fill(s, body(16, 20, 8.5, 12), 0, { cx: 16, cy: 22, rx: 12, ry: 10, shade: 1, at: 0.6 });                     // 흰 옷
    // 물결치는 긴 금발
    fill(s, OR(E(16, 10.5, 8.8, 8.6), (x, y) => y > 10 && y < 31 && (Math.abs(x - 16) > 5.2 && Math.abs(x - 16) < 9.3 + Math.sin(y / 2) * 0.8)), 1, { cx: 16, cy: 12, rx: 9, ry: 14, shade: 2, at: 0.85, hi: 0, hiAt: -0.3 });
    for (let y = 14; y < 30; y += 3) { px(s, 8 + (y % 2), y, 2); px(s, 23 - (y % 2), y, 2); }                     // 물결
    fill(s, (x, y) => E(16, 13, 6.4, 7.2)(x, y) && y > 8.5 + Math.abs(x - 16) * 0.25, 0, { cx: 16, cy: 13, rx: 6.4, ry: 7.2, shade: 1, at: 0.7 });
    stamp(s, 10, 8, ['2222222222222'].map(r => r.slice(0, 12)));                                                  // 머리띠
    stamp(s, 15, 8, ['00']);
    stamp(s, 12, 13, EYE); stamp(s, 19, 13, EYE);
    stamp(s, 15, 17, ['11']);
    // 빛의 병 (가슴 앞에서 빛남)
    stamp(s, 14, 22, ['..2..', '.202.', '20002', '.202.', '..2..']);
    return finish(s);
  }

  root.RingGB32Foes = {
    bosses: [{ name: '발로그', make: balrog }, { name: '동굴 트롤', make: caveTroll }],
    foes: [{ name: '검은 기사', make: blackRider }, { name: '골룸', make: gollum }, { name: '사루만', make: saruman }, { name: '우루크하이', make: urukHai }],
    people: [{ name: '보로미르', make: boromir }, { name: '갈라드리엘', make: galadriel }],
  };
})(typeof window !== 'undefined' ? window : globalThis);
