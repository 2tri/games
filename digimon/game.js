// 디지몬 팬 게임 — 엔진 (조작·장면·글상자·메뉴·필드·전투·진화·알·저장)
// 화면 160×144 금판 규격. 이야기·지도는 story.js, 디지몬 자료는 species.js
(function () {
  'use strict';
  const U = DigiUI, PX = DigiPix, SP = DigiSpecies, POW = DigiPower, FLD = DigiField, ST = DigiStory;
  const K = U.K, PAPER = U.PAPER;
  const cv = document.getElementById('scr'), g = cv.getContext('2d');
  g.imageSmoothingEnabled = false;

  // ───────── 입력 ─────────
  const KEYMAP = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', KeyW: 'up', KeyS: 'down', KeyA: 'left', KeyD: 'right',
    KeyZ: 'a', Space: 'a', KeyX: 'b', Escape: 'b', Backspace: 'b', Enter: 'start', ShiftLeft: 'select', ShiftRight: 'select' };
  const held = {}, hit = {};
  let lastDir = null;
  const down = (k) => { if (!held[k]) { hit[k] = true; if (['up', 'down', 'left', 'right'].includes(k)) lastDir = k; } held[k] = true; };
  const up = (k) => { held[k] = false; };
  addEventListener('keydown', (e) => { const k = KEYMAP[e.code]; if (!k) return; e.preventDefault(); if (!e.repeat) down(k); });
  addEventListener('keyup', (e) => { const k = KEYMAP[e.code]; if (k) up(k); });
  document.querySelectorAll('[data-k]').forEach((el) => {
    const k = el.dataset.k;
    el.addEventListener('pointerdown', (e) => { e.preventDefault(); el.setPointerCapture && el.setPointerCapture(e.pointerId); down(k); el.classList.add('on'); });
    for (const t of ['pointerup', 'pointercancel', 'lostpointercapture']) el.addEventListener(t, () => { up(k); el.classList.remove('on'); });
  });
  addEventListener('blur', () => { for (const k in held) held[k] = false; });
  const press = (k) => { if (hit[k]) { hit[k] = false; return true; } return false; };
  const heldDir = () => { if (lastDir && held[lastDir]) return lastDir; for (const d of ['up', 'down', 'left', 'right']) if (held[d]) return d; return null; };

  // ───────── 장면 쌓기 · 기다리기 ─────────
  const stack = [], waiters = [];
  function open(sc) { stack.push(sc); return new Promise((r) => { sc._done = r; }); }
  function close(sc, v) { const i = stack.indexOf(sc); if (i >= 0) stack.splice(i, 1); if (sc._done) sc._done(v); }
  const wait = (n) => new Promise((r) => waiters.push({ n, r }));
  const until = (pred) => new Promise((r) => waiters.push({ pred, r }));

  // ───────── 그림 ─────────
  const cache = new Map();
  function cvs(pic) { let c = cache.get(pic); if (!c) { c = PX.toCanvas(pic, 1); cache.set(pic, c); } return c; }
  const put = (pic, x, y) => g.drawImage(cvs(pic), x, y);
  const ATTRCOL = { '백신': ['#a8c8f8', '#3868c0'], '데이터': ['#a8e0a0', '#3c9048'], '바이러스': ['#d8a8e8', '#7840a0'], '프리': ['#f8e0a0', '#b88830'], '없음': ['#e0e0e0', '#888888'], '불명': ['#c8c8c8', '#585858'] };
  const DRAWN_F = { agumon: 'agumon', greymon: 'greymon', kuwagamon: 'kuwagamon', koromon: 'koromon' };
  const DRAWN_B = { agumon: 'agumonBack' };
  const artImg = {};
  for (const id in (window.DigiArt || {})) for (const side of ['front', 'back']) if (DigiArt[id][side]) { const im = new Image(); im.src = DigiArt[id][side]; artImg[id + ':' + side] = im; }
  const sprCache = {};
  function card(id, back) {                      // 그림이 없는 디지몬의 임시 카드
    const s = SP[id], [c1, c2] = ATTRCOL[s.attr] || ATTRCOL['없음'], w = back ? 48 : 48, h = back ? 48 : 48;
    const c = document.createElement('canvas'); c.width = w; c.height = h; const q = c.getContext('2d');
    q.fillStyle = K; q.beginPath(); q.ellipse(24, 28, 19, 19, 0, 0, 7); q.fill();
    q.fillStyle = c1; q.beginPath(); q.ellipse(24, 28, 17, 17, 0, 0, 7); q.fill();
    q.fillStyle = c2; q.beginPath(); q.ellipse(28, 32, 13, 13, 0, 0, 7); q.fill();
    q.fillStyle = c1; q.beginPath(); q.ellipse(23, 27, 13, 13, 0, 0, 7); q.fill();
    q.fillStyle = PAPER; q.fillRect(14, 16, 3, 2);
    if (!back) { q.fillStyle = K; q.fillRect(17, 25, 3, 4); q.fillRect(28, 25, 3, 4); }
    const ch = [...s.name][0]; U.text(q, ch, 24 - U.textWidth(ch) / 2, back ? 23 : 31, K);
    return c;
  }
  function sprite(id, back) {
    const key = id + (back ? ':back' : ':front');
    const im = artImg[key];
    if (im && im.complete && im.naturalWidth) return im;
    if (sprCache[key]) return sprCache[key];
    let c;
    const fn = back ? DRAWN_B[id] : DRAWN_F[id];
    if (fn && DigiMons.MON[fn]) c = PX.toCanvas(DigiMons.MON[fn](), 1); else c = card(id, back);
    return (sprCache[key] = c);
  }
  const icon = (id) => (id === 'agumon' ? FLD.WALK.agumon : null);

  // ───────── 글자 도우미 ─────────
  function josa(w, pair) {
    const [a, b] = pair.split('/'); const c = w.charCodeAt(w.length - 1);
    if (c < 0xac00 || c > 0xd7a3) return a;
    const j = (c - 0xac00) % 28;
    if (pair === '으로/로') return j === 0 || j === 8 ? '로' : '으로';
    return j ? a : b;
  }
  const numJosa = (n) => { const d = n % 10; if (n % 10 === 0) return '이'; return [2, 4, 5, 9].includes(d) ? '가' : '이'; };
  const nm = (id) => SP[id].name;

  // ───────── 디지몬 ─────────
  const BASIC = {
    '부딪치기': { pow: 40, acc: 100, pp: 35 }, '할퀴기': { pow: 40, acc: 100, pp: 35 }, '물기': { pow: 60, acc: 100, pp: 25 },
    '노려보기': { pow: 0, acc: 100, pp: 30, eff: 'foeDef' }, '웅크리기': { pow: 0, acc: 100, pp: 30, eff: 'selfDef' }
  };
  const TIERS = ['baby', 'baby2', 'rookie', 'champion', 'ultimate', 'mega'];
  const SIGTIER = {};
  for (const id in SP) for (const n of SP[id].sig) { const t = SP[id].tier; if (!SIGTIER[n] || TIERS.indexOf(t) < TIERS.indexOf(SIGTIER[n])) SIGTIER[n] = t; }
  function moveInfo(n) {
    if (BASIC[n]) return Object.assign({ kind: '기본기' }, BASIC[n]);
    const t = SIGTIER[n] || 'rookie';
    return { pow: POW[t], acc: 95, pp: t === 'mega' ? 5 : t === 'ultimate' ? 8 : 12, kind: '필살기' };
  }
  const BASICS_BY_TIER = { baby: ['부딪치기'], baby2: ['부딪치기', '노려보기'], rookie: ['할퀴기', '노려보기'], champion: ['물기', '웅크리기'], ultimate: ['물기', '웅크리기'], mega: ['물기', '웅크리기'] };
  function startMoves(id) { const s = SP[id]; return BASICS_BY_TIER[s.tier].concat(s.sig).slice(-4).map((n) => ({ n, pp: moveInfo(n).pp })); }
  const stat = (m, i) => { const b = SP[m.sp].base[i]; return i === 0 ? Math.floor(b * 2 * m.lv / 100) + m.lv + 10 : Math.floor(b * 2 * m.lv / 100) + 5; };
  const maxHp = (m) => stat(m, 0);
  const expAt = (lv) => (lv <= 1 ? 0 : lv * lv * lv);
  function makeMon(sp, lv) { const m = { sp, lv, exp: expAt(lv), moves: startMoves(sp) }; m.hp = maxHp(m); return m; }
  function learn(m, id) {                               // 진화하면 새 필살기를 익힘 (4개 넘으면 오래된 기본기부터 잊음)
    const got = [];
    for (const n of SP[id].sig) if (!m.moves.some((x) => x.n === n)) { m.moves.push({ n, pp: moveInfo(n).pp }); got.push(n); }
    while (m.moves.length > 4) { const i = m.moves.findIndex((x) => BASIC[x.n]); m.moves.splice(i >= 0 ? i : 0, 1); }
    return got;
  }
  const BEATS = { '백신': '바이러스', '바이러스': '데이터', '데이터': '백신' };
  const attrMult = (a, d) => (BEATS[a] === d ? 1.5 : BEATS[d] === a ? 0.75 : 1);
  const stageMul = (s) => (s >= 0 ? (2 + s) / 2 : 2 / (2 - s));

  // ───────── 게임 상태 ─────────
  const SAVE_KEY = 'digimon-fan-save-1';
  let G = null;
  function newState(kid) {
    return { v: 1, kid, map: ST.START.map, x: ST.START.x, y: ST.START.y, dir: ST.START.dir, party: [], box: [], bag: {}, flags: {}, crests: [], seen: {}, owned: {}, steps: 0, heal: Object.assign({}, ST.START), time: 0 };
  }
  const saveGame = () => { try { localStorage.setItem(SAVE_KEY, JSON.stringify(G)); return true; } catch (e) { return false; } };
  const loadGame = () => { try { const s = localStorage.getItem(SAVE_KEY); return s ? JSON.parse(s) : null; } catch (e) { return null; } };
  const kidName = () => FLD.KIDS[G.kid].name;
  const alive = () => G.party.filter((m) => !m.egg && m.hp > 0);
  function addMon(m) { G.seen[m.sp] = 1; G.owned[m.sp] = 1; if (G.party.length < 6) { G.party.push(m); return 'party'; } G.box.push(m); return 'box'; }
  function healAll() { for (const m of G.party) if (!m.egg) { m.hp = maxHp(m); for (const mv of m.moves) mv.pp = moveInfo(mv.n).pp; } }

  // ───────── 글상자 ─────────
  function wrap(line) {
    const out = []; let cur = '';
    for (const word of line.split(' ')) {
      const t = cur ? cur + ' ' + word : word;
      if (U.textWidth(t) <= 144) { cur = t; continue; }
      if (cur) out.push(cur);
      cur = word;
      while (U.textWidth(cur) > 144) { let i = cur.length; while (U.textWidth(cur.slice(0, i)) > 144) i--; out.push(cur.slice(0, i)); cur = cur.slice(i); }
    }
    out.push(cur);
    return out;
  }
  function paginate(text) {
    const pages = [];
    for (const block of String(text).split('\f')) {
      const lines = [];
      for (const l of block.split('\n')) lines.push(...wrap(l));
      for (let i = 0; i < lines.length; i += 2) pages.push(lines.slice(i, i + 2));
    }
    return pages;
  }
  class TextBox {
    constructor(text, o) { this.overlay = true; this.pages = paginate(text); this.p = 0; this.n = 0; this.t = 0; this.o = o || {}; }
    get len() { return this.pages[this.p].reduce((s, l) => s + [...l].length, 0); }
    update() {
      if (this.n < this.len) {
        this.n += held.a || held.b ? 3 : 1;
        if (press('a') || press('b')) this.n = this.len;
        if (this.n >= this.len) { this.n = this.len; if (this.last && this.shown) { this.shown(); this.shown = null; } }
        return;
      }
      if (this.last && this.o.hold) return;
      if (this.o.auto) { if (++this.t >= this.o.auto) this.next(); return; }
      if (press('a') || press('b')) this.next();
    }
    get last() { return this.p === this.pages.length - 1; }
    next() { if (!this.last) { this.p++; this.n = 0; this.t = 0; } else close(this); }
    draw(q) {
      U.frame(q, 0, 96, 160, 48);
      let rem = this.n;
      this.pages[this.p].forEach((l, i) => { const ch = [...l]; U.text(q, ch.slice(0, Math.max(0, rem)).join(''), 8, 104 + i * 16); rem -= ch.length; });
      if (this.n >= this.len && !this.o.hold && !this.o.auto && (frameNo >> 4) % 2 === 0) U.more(q, 145, 136);
    }
  }
  const say = (text, o) => open(new TextBox(text, o));
  function sayHold(text) { const b = new TextBox(text, { hold: true }); const shown = new Promise((r) => { b.shown = r; }); open(b); if (b.len === 0) b.shown(); return shown.then(() => b); }

  // ───────── 메뉴 ─────────
  class Menu {
    constructor(items, o) {
      this.overlay = true; this.items = items; this.o = o || {}; this.i = this.o.start || 0;
      const w = this.o.w || Math.max(...items.map((t) => U.textWidth(t))) + 24, h = items.length * 16 + 10;
      this.w = w; this.h = h; this.x = this.o.x != null ? this.o.x : 160 - w; this.y = this.o.y != null ? this.o.y : 0;
    }
    update() {
      const n = this.items.length;
      if (press('up')) this.i = (this.i + n - 1) % n;
      if (press('down')) this.i = (this.i + 1) % n;
      if (press('a')) close(this, this.i);
      else if ((press('b') || (this.o.startCloses && press('start'))) && this.o.cancel !== false) close(this, -1);
    }
    draw(q) {
      U.frame(q, this.x, this.y, this.w, this.h);
      this.items.forEach((t, j) => U.text(q, t, this.x + 14, this.y + 6 + j * 16));
      U.cursor(q, this.x + 7, this.y + 8 + this.i * 16);
    }
  }
  const choose = (items, o) => open(new Menu(items, o));
  async function ask(text) { const b = await sayHold(text); const r = await choose(['예', '아니오'], { x: 104, y: 52, w: 56 }); close(b); return r === 0; }

  // ───────── 화면 전환 ─────────
  class Fade {
    constructor(dir, col) { this.overlay = true; this.dir = dir; this.t = 0; this.col = col || '#000'; this.keep = false; }
    tick() { if (this.t < 12) this.t++; }
    update() {}
    draw(q) { const a = this.dir > 0 ? this.t / 12 : 1 - this.t / 12; q.globalAlpha = Math.max(0, Math.min(1, a)); q.fillStyle = this.col; q.fillRect(0, 0, 160, 144); q.globalAlpha = 1; }
  }
  let blackout = null;
  async function fadeOut(col) { const f = new Fade(1, col); open(f); await until(() => f.t >= 12); blackout = f; }
  async function fadeIn() { if (!blackout) return; const f = blackout; f.dir = -1; f.t = 0; await until(() => f.t >= 12); close(f); blackout = null; }
  async function flash(n) { for (let i = 0; i < (n || 3); i++) { await fadeOut('#f8f8f8'); await wait(2); await fadeIn(); } }

  // 흰 바탕 그림 보여 주기 (오프닝·문장·합류 등)
  class PicScene {
    constructor(items) { this.overlay = false; this.items = items || []; this.bg = PAPER; }
    update() {}
    draw(q) { q.fillStyle = this.bg; q.fillRect(0, 0, 160, 144); for (const it of this.items) { if (it.draw) it.draw(q); else q.drawImage(it.img, it.x, it.y); } }
  }
  function showPics(items) { const s = new PicScene(items); open(s); return s; }

  // ───────── 필드 ─────────
  const TPROP = { tree: { solid: 1 }, dtree: { solid: 1 }, sea: { solid: 1 }, shore: { solid: 1 }, crib: { solid: 1 }, egg: { solid: 1 }, sign: { solid: 1 }, blockR: { solid: 1 }, blockB: { solid: 1 }, blockY: { solid: 1 }, fire: { solid: 1 }, tall: { grass: 1 } };
  const DIRV = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
  const OPP = { up: 'down', down: 'up', left: 'right', right: 'left' };
  const mapOf = () => ST.maps[G.map];
  function tileAt(map, x, y) {
    if (x < 0 || y < 0 || y >= map.rows.length || x >= map.rows[0].length) {
      for (const o of map.open || []) if (x >= o[0] && x <= o[2] && y >= o[1] && y <= o[3]) return o[4];
      return typeof map.border === 'function' ? map.border(x, y) : map.border;
    }
    return map.key[map.rows[y][x]] || 'grass';
  }
  function objAt(map, x, y) { return (map.objs || []).find((o) => x >= o.x && x < o.x + o.w && y >= o.y && y < o.y + o.h); }
  const npcsOf = (map) => (map.npcs || []).filter((n) => !n.cond || n.cond(G));
  function npcAt(map, x, y) { return npcsOf(map).find((n) => n.x === x && n.y === y); }
  function walkable(map, x, y) {
    if (x < 0 || y < 0 || y >= map.rows.length || x >= map.rows[0].length) return false;
    const t = tileAt(map, x, y);
    if (TPROP[t] && TPROP[t].solid) return false;
    if (objAt(map, x, y)) return false;
    if (npcAt(map, x, y)) return false;
    return true;
  }
  class Field {
    constructor() { this.mv = null; this.busy = false; this.prevD = null; this.turnHold = 0; }
    update() {
      if (this.busy) return;
      if (this.mv) return;
      if (press('start')) return this.run(startMenu);
      if (press('a')) return this.run(interact);
      const d = heldDir(), fresh = d && !this.prevD; this.prevD = d;
      if (!d) { this.turnHold = 0; return; }
      if (fresh && G.dir !== d) this.turnHold = 6;          // 살짝 누르면 방향만 바꿈
      G.dir = d;
      if (this.turnHold > 0) { this.turnHold--; return; }
      const [dx, dy] = DIRV[d], map = mapOf();
      if (walkable(map, G.x + dx, G.y + dy)) this.mv = { dx, dy, t: 0 };
      else { const w = (map.warps || []).find((w) => w.edge && w.x === G.x + dx && w.y === G.y + dy); if (w) { this.mv = { dx, dy, t: 0, edgeWarp: w }; } }
    }
    tick() {
      if (!this.mv) return;
      this.mv.t += 2;
      if (this.mv.t >= 16) {
        const m = this.mv; this.mv = null; G.x += m.dx; G.y += m.dy; G.steps++;
        this.run(() => arrive(m.edgeWarp));
      }
    }
    async run(fn) { this.busy = true; try { await fn(); } catch (e) { console.error(e); } this.busy = false; }
    draw(q) {
      const map = mapOf();
      const ox = this.mv ? this.mv.dx * this.mv.t : 0, oy = this.mv ? this.mv.dy * this.mv.t : 0;
      const camX = G.x * 16 + ox - 64, camY = G.y * 16 + oy - 64;
      const tx0 = Math.floor(camX / 16), ty0 = Math.floor(camY / 16);
      for (let ty = ty0; ty < ty0 + 11; ty++) for (let tx = tx0; tx < tx0 + 11; tx++) {
        const t = tileAt(map, tx, ty); const pic = FLD.TILE[t] || FLD.TILE.grass;
        q.drawImage(cvs(pic), 0, 0, 16, 16, tx * 16 - camX, ty * 16 - camY, 16, 16);
      }
      for (const o of map.objs || []) q.drawImage(cvs(FLD.TILE[o.t]), o.x * 16 - camX, o.y * 16 - camY);
      const list = npcsOf(map).map((n) => ({ y: n.y, d: () => q.drawImage(cvs(npcPic(n)), n.x * 16 - camX, n.y * 16 - camY - 4) }));
      const frames = FLD.WALKS[G.kid][G.dir];
      const fi = this.mv && this.mv.t <= 8 ? (G.steps % 2 ? 1 : 3) : 0;
      list.push({ y: G.y + (this.mv ? 0.5 : 0), d: () => q.drawImage(cvs(frames[fi]), 64, 60) });
      list.sort((a, b) => a.y - b.y).forEach((it) => it.d());
    }
  }
  function npcPic(n) {
    const spr = typeof n.spr === 'function' ? n.spr(G) : n.spr;
    if (FLD.WALKS[spr]) return FLD.WALKS[spr][n.dir || 'down'][0];
    if (FLD.WALK[spr]) return FLD.WALK[spr];
    if (spr && spr.startsWith('blob:')) { const id = spr.slice(5); if (!n._blob) { const [c1, c2] = ATTRCOL[SP[id].attr] || ATTRCOL['없음']; n._blob = FLD.blob(c1, c2); } return n._blob; }
    return FLD.WALK.agumon;
  }
  let field = null;
  async function arrive(edgeWarp) {
    const map = mapOf();
    if (edgeWarp) return warp(edgeWarp.to, edgeWarp.tx, edgeWarp.ty, G.dir);
    await eggStep();
    const w = (map.warps || []).find((w) => !w.edge && w.x === G.x && w.y === G.y);
    if (w) return warp(w.to, w.tx, w.ty, w.dir || G.dir);
    for (const tr of map.triggers || []) {
      if (tr.once && G.flags[tr.once]) continue;
      if (tr.cond && !tr.cond(G)) continue;
      if (G.x >= tr.x && G.x < tr.x + (tr.w || 1) && G.y >= tr.y && G.y < tr.y + (tr.h || 1)) { if (tr.once) G.flags[tr.once] = 1; await tr.run(API); return; }
    }
    if (TPROP[tileAt(map, G.x, G.y)] && TPROP[tileAt(map, G.x, G.y)].grass && map.enc && alive().length && Math.random() < map.enc.rate) await wildEncounter(map.enc);
  }
  async function warp(to, x, y, dir) {
    await fadeOut();
    G.map = to; G.x = x; G.y = y; if (dir) G.dir = dir;
    await wait(4);
    await fadeIn();
    const map = mapOf();
    if (map.onEnter) await map.onEnter(API);
  }
  async function interact() {
    const map = mapOf(), [dx, dy] = DIRV[G.dir], x = G.x + dx, y = G.y + dy;
    const n = npcAt(map, x, y);
    if (n) { const keep = n.dir; if (n.turn !== false) n.dir = OPP[G.dir]; if (n.talk) await n.talk(API, n); else if (n.text) await say(typeof n.text === 'function' ? n.text(G) : n.text); n.dir = n.fixed ? keep : n.dir; return; }
    const sg = (map.signs || []).find((s) => s.x === x && s.y === y);
    if (sg) { await say(typeof sg.text === 'function' ? sg.text(G) : sg.text); return; }
  }
  async function eggStep() {
    for (const m of G.party) if (m.egg && --m.steps <= 0) { await hatch(m); }
  }

  // ───────── START 메뉴 ─────────
  async function startMenu() {
    let i = 0;
    for (;;) {
      const items = ['도감', '디지몬', '가방', kidName(), '저장', '닫기'];
      i = await choose(items, { x: 88, y: 0, w: 72, start: i, startCloses: true });
      if (i < 0 || i === 5) return;
      if (i === 0) await dexScreen();
      if (i === 1) await partyScreen({ field: true });
      if (i === 2) await bagScreen({ field: true });
      if (i === 3) await kidCard();
      if (i === 4) { if (await ask('지금까지의 모험을 기록할까?')) { const ok = saveGame(); await say(ok ? kidName() + josa(kidName(), '은/는') + ' 모험을 기록했다!' : '기록하지 못했다… (브라우저 저장소를 쓸 수 없음)'); } return; }
    }
  }

  // ───────── 디지몬 목록 (파티) ─────────
  class PartyScene {
    constructor(o) { this.overlay = false; this.o = o || {}; this.i = 0; this.msg = this.o.msg || '디지몬을 고르세요'; }
    update() {
      const n = G.party.length;
      if (press('up')) this.i = (this.i + n - 1) % n;
      if (press('down')) this.i = (this.i + 1) % n;
      if (press('a')) close(this, this.i);
      else if (press('b') && !this.o.must) close(this, -1);
    }
    draw(q) {
      q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
      G.party.forEach((m, j) => {
        const y = j * 16;
        if (j === this.i) U.cursor(q, 2, y + 4);
        if (m.egg) { put(FLD.TILE.egg, 8, y); U.text(q, '디지타마', 28, y + 2); return; }
        const ic = icon(m.sp); if (ic) put(ic, 8, y); else { const [c1, c2] = ATTRCOL[SP[m.sp].attr] || ATTRCOL['없음']; q.fillStyle = K; q.fillRect(10, y + 3, 12, 11); q.fillStyle = c1; q.fillRect(11, y + 4, 10, 9); q.fillStyle = c2; q.fillRect(11, y + 10, 10, 3); }
        U.text(q, nm(m.sp), 28, y + 2);
        U.level(q, m.lv, 128, y + 2);
        const r = m.hp / maxHp(m); q.fillStyle = K; q.fillRect(90, y + 12, 50, 3);
        q.fillStyle = r > .5 ? U.PAL.hpG : r > .2 ? U.PAL.hpY : U.PAL.hpR; q.fillRect(91, y + 13, Math.round(48 * r), 1);
      });
      U.frame(q, 0, 96, 160, 48); U.text(q, this.msg, 8, 106);
    }
  }
  async function partyScreen(o) {
    o = o || {};
    for (;;) {
      if (!G.party.length) { await say('함께하는 디지몬이 없다.'); return -1; }
      const sc = new PartyScene(o); const i = await open(sc);
      if (i < 0) return -1;
      if (o.pick) return i;
      const m = G.party[i];
      if (m.egg) { await say(`디지타마다. 걷다 보면 깨어날 것 같다… (앞으로 약 ${Math.max(1, Math.ceil(m.steps / 10) * 10)}걸음)`); continue; }
      const j = await choose(['능력 보기', '순서 바꾸기', '닫기'], { x: 72, y: 56, w: 88 });
      if (j === 0) await statusScreen(m);
      if (j === 1 && G.party.length > 1) {
        const t = await open(new PartyScene({ msg: '어느 자리로 옮길까?' }));
        if (t >= 0 && t !== i) { const a = G.party[i]; G.party[i] = G.party[t]; G.party[t] = a; }
      }
    }
  }

  // ───────── 능력 보기 ─────────
  class StatusScene {
    constructor(m) { this.overlay = false; this.m = m; this.page = 0; }
    update() { if (press('left') || press('right')) this.page ^= 1; if (press('a') || press('b')) close(this); }
    draw(q) {
      const m = this.m, s = SP[m.sp];
      q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
      q.fillStyle = this.page ? '#a8e0a0' : '#f8b8d8'; q.fillRect(60, 0, 100, 144); q.fillStyle = K; q.fillRect(58, 0, 2, 144);
      const sp = sprite(m.sp); const sc = Math.min(1, 48 / Math.max(sp.width, sp.height));
      q.drawImage(sp, 6 + (48 - sp.width * sc) / 2, 12 + (48 - sp.height * sc), sp.width * sc, sp.height * sc);
      U.num(q, 'No.' + String(dexNo(m.sp)).padStart(3, '0'), 2, 2); U.level(q, m.lv, 4, 64);
      U.text(q, nm(m.sp), 4, 74); U.text(q, s.grade, 4, 90);
      if (!this.page) {
        U.hpBar(q, 72, 6, m.hp / maxHp(m)); U.num(q, String(m.hp).padStart(3, ' ') + '/' + String(maxHp(m)).padStart(3, ' '), 88, 14);
        U.text(q, '속성/', 64, 26); U.text(q, s.attr, 104, 26); U.text(q, '유형/', 64, 42); U.text(q, s.type, 104, 42);
        U.text(q, '공격', 64, 62); U.num(q, String(stat(m, 1)).padStart(3, ' '), 128, 64);
        U.text(q, '방어', 64, 78); U.num(q, String(stat(m, 2)).padStart(3, ' '), 128, 80);
        U.text(q, '스피드', 64, 94); U.num(q, String(stat(m, 3)).padStart(3, ' '), 128, 96);
        U.text(q, '다음 레벨까지', 64, 112); U.num(q, String(Math.max(0, expAt(m.lv + 1) - m.exp)), 104, 128);
      } else {
        U.text(q, '기술', 64, 4);
        m.moves.forEach((mv, j) => { const mi = moveInfo(mv.n); U.text(q, mv.n, 66, 20 + j * 28); U.text(q, mi.kind, 70, 34 + j * 28, '#406040'); U.num(q, mv.pp + '/' + mi.pp, 118, 36 + j * 28); });
      }
      U.text(q, '◀ ▶', 12, 128);
    }
  }
  const statusScreen = (m) => open(new StatusScene(m));

  // ───────── 가방 ─────────
  const ITEMS = ST.items;
  class BagScene {
    constructor(o) { this.overlay = false; this.o = o || {}; this.i = 0; }
    get list() { return Object.keys(G.bag).filter((k) => G.bag[k] > 0); }
    update() { const n = this.list.length + 1; if (press('up')) this.i = (this.i + n - 1) % n; if (press('down')) this.i = (this.i + 1) % n; if (press('a')) close(this, this.i < this.list.length ? this.list[this.i] : null); else if (press('b')) close(this, null); }
    draw(q) {
      q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
      U.frame(q, 0, 0, 160, 96); U.text(q, '가방', 8, 4);
      const L = this.list.concat(['그만두다']);
      L.forEach((k, j) => { U.text(q, k, 18, 20 + j * 14); if (G.bag[k]) { U.text(q, '×', 122, 20 + j * 14); U.num(q, String(G.bag[k]).padStart(2, ' '), 132, 22 + j * 14); } });
      U.cursor(q, 9, 22 + this.i * 14);
      U.frame(q, 0, 96, 160, 48); const it = ITEMS[L[this.i]]; U.text(q, it ? it.desc : '가방을 닫는다', 8, 106);
    }
  }
  async function bagScreen(o) {
    o = o || {};
    for (;;) {
      const k = await open(new BagScene(o));
      if (!k) return null;
      const it = ITEMS[k];
      if (it.heal) {
        const i = await partyScreen({ pick: true, msg: '누구에게 쓸까?' });
        if (i < 0) continue;
        const m = G.party[i];
        if (m.egg || m.hp <= 0 || m.hp >= maxHp(m)) { await say('써도 효과가 없다.'); continue; }
        const before = m.hp; m.hp = Math.min(maxHp(m), m.hp + it.heal); G.bag[k]--;
        await say(`${nm(m.sp)}의 체력이 ${m.hp - before} 회복되었다!`);
        if (o.battle) return { used: k, mon: m };
        continue;
      }
      await say('지금은 쓸 수 없다.');
    }
  }

  // ───────── 도감 ─────────
  const DEX_ORDER = ST.dexOrder;
  const dexNo = (id) => DEX_ORDER.indexOf(id) + 1;
  class DexScene {
    constructor() { this.overlay = false; this.i = 0; this.top = 0; this.entry = false; }
    get list() { return DEX_ORDER.filter((id) => G.seen[id]); }
    update() {
      const L = this.list; if (!L.length) { if (press('a') || press('b')) close(this); return; }
      if (this.entry) { if (press('a') || press('b')) this.entry = false; return; }
      if (press('up')) this.i = Math.max(0, this.i - 1); if (press('down')) this.i = Math.min(L.length - 1, this.i + 1);
      if (this.i < this.top) this.top = this.i; if (this.i > this.top + 6) this.top = this.i - 6;
      if (press('a') && G.owned[L[this.i]]) this.entry = true; else if (press('b')) close(this);
    }
    draw(q) {
      const L = this.list;
      q.fillStyle = '#d84828'; q.fillRect(0, 0, 160, 144); q.fillStyle = '#101010'; q.fillRect(3, 3, 154, 138);
      if (!L.length) { U.text(q, '아직 만난 디지몬이 없다', 16, 64, PAPER); return; }
      if (this.entry) {
        const id = L[this.i], s = SP[id], sp = sprite(id);
        q.fillStyle = PAPER; q.fillRect(8, 6, 56, 56); const sc = Math.min(1, 56 / Math.max(sp.width, sp.height));
        q.drawImage(sp, 8 + (56 - sp.width * sc) / 2, 6 + (56 - sp.height * sc), sp.width * sc, sp.height * sc);
        U.num(q, 'No.' + String(dexNo(id)).padStart(3, '0'), 10, 66, PAPER);
        U.text(q, s.name, 70, 6, PAPER); U.text(q, s.type + ' 디지몬', 70, 22, PAPER);
        U.text(q, '등급', 70, 38, PAPER); U.text(q, s.grade, 104, 38, PAPER); U.text(q, '속성', 70, 54, PAPER); U.text(q, s.attr, 104, 54, PAPER);
        q.fillStyle = '#d84828'; q.fillRect(6, 78, 148, 2);
        U.text(q, '필살기', 8, 84, '#f8b048'); s.sig.forEach((n, j) => U.text(q, n, 16, 100 + j * 14, PAPER));
        return;
      }
      U.text(q, '디지몬 도감', 8, 4, '#f8b048');
      U.text(q, '만남 ' + L.length + ' · 함께 ' + Object.keys(G.owned).length, 76, 4, PAPER);
      for (let j = 0; j < 7 && this.top + j < L.length; j++) {
        const id = L[this.top + j], y = 22 + j * 16;
        U.num(q, String(dexNo(id)).padStart(3, '0'), 18, y + 2, PAPER); U.text(q, G.owned[id] ? SP[id].name : '?????', 50, y, PAPER);
        if (G.owned[id]) { q.fillStyle = '#f8b048'; q.fillRect(140, y + 4, 4, 4); }
      }
      q.fillStyle = PAPER; for (let i = 0; i < 4; i++) q.fillRect(8 + i, 24 + (this.i - this.top) * 16 + i, 1, 7 - i * 2);
    }
  }
  const dexScreen = () => open(new DexScene());

  // ───────── 주인공 정보 ─────────
  class KidCard {
    constructor() { this.overlay = false; }
    update() { if (press('a') || press('b')) close(this); }
    draw(q) {
      q.fillStyle = '#88b0f0'; q.fillRect(0, 0, 160, 144); U.frame(q, 4, 4, 152, 136);
      U.text(q, '선택받은 아이', 12, 10); U.text(q, kidName(), 12, 28);
      q.drawImage(cvs(FLD.WALKS[G.kid].down[0]), 120, 18);
      U.text(q, '도감', 12, 48); U.num(q, String(Object.keys(G.owned).length), 80, 50);
      const t = Math.floor(G.time / 3600); U.text(q, '모험 시간', 12, 64); U.num(q, Math.floor(t / 60) + ':' + String(t % 60).padStart(2, '0'), 80, 66);
      U.text(q, '문장', 12, 84);
      ST.CRESTS.forEach((c, j) => { const x = 14 + (j % 4) * 36, y = 100 + Math.floor(j / 4) * 18; const got = G.crests.includes(c); U.text(q, got ? c : '··', x, y, got ? K : '#909090'); });
    }
  }
  const kidCard = () => open(new KidCard());

  // ───────── 전투 ─────────
  class BattleScene {
    constructor(B) { this.overlay = false; this.B = B; this.foeX = 160; this.meX = -48; this.blinkF = 0; this.blinkM = 0; }
    tick() {
      const B = this.B;
      if (B.showFoe && this.foeX > 96) this.foeX -= 4;
      if (B.showMe && this.meX < 16) this.meX += 4;
      for (const k of ['foe', 'me']) { const m = B[k]; if (!m) continue; const t = m.hp, d = B['d' + k]; if (d !== t) B['d' + k] = d > t ? Math.max(t, d - Math.max(1, Math.ceil(maxHp(m) / 48))) : Math.min(t, d + Math.max(1, Math.ceil(maxHp(m) / 48))); }
      if (this.blinkF) this.blinkF--; if (this.blinkM) this.blinkM--;
    }
    update() {}
    draw(q) {
      const B = this.B;
      q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
      if (B.showFoe && B.foe && !(this.blinkF && (this.blinkF >> 2) % 2) && !B.foeGone) {
        const s = sprite(B.foe.sp); q.drawImage(s, this.foeX + (56 - s.width) / 2, 56 - s.height);
      }
      if (B.showMe && B.me && !(this.blinkM && (this.blinkM >> 2) % 2) && !B.meGone) {
        const s = sprite(B.me.sp, true);
        if (s.width <= 48 && s.height <= 48) q.drawImage(s, this.meX + (48 - s.width) / 2, 96 - s.height); else q.drawImage(s, this.meX, 48, 48, 48);
      }
      if (B.showFoe && B.foe && this.foeX <= 96 && !B.foeGone) {
        const n = nm(B.foe.sp); U.text(q, n, 56 - U.textWidth(n), 4); U.level(q, B.foe.lv, 64, 8);
        U.hpBar(q, 16, 16, B.dfoe / maxHp(B.foe)); U.bracketFoe(q, 10, 15);
      }
      if (B.showMe && B.me && this.meX >= 16 && !B.meGone) {
        const n = nm(B.me.sp); U.text(q, n, 112 - U.textWidth(n), 61); U.level(q, B.me.lv, 120, 65);
        U.hpBar(q, 80, 73, B.dme / maxHp(B.me)); U.bracketMe(q, 145, 73);
        U.num(q, String(B.dme).padStart(3, ' ') + '/' + String(maxHp(B.me)).padStart(3, ' '), 88, 81);
        const lo = expAt(B.me.lv), hi = expAt(B.me.lv + 1); U.expBar(q, 96, 91, Math.max(0, Math.min(1, (B.me.exp - lo) / (hi - lo))));
      }
    }
  }
  class BattleMenu {
    constructor(B) { this.overlay = true; this.B = B; this.i = 0; }
    update() {
      if (press('up') || press('down')) this.i ^= 2;
      if (press('left') || press('right')) this.i ^= 1;
      if (press('a')) close(this, this.i);
    }
    draw(q) {
      U.frame2(q, 0, 98, 68, 46); const n = nm(this.B.me.sp); U.text(q, n + josa(n, '은/는'), 6, 106); U.text(q, '무엇을 할까?', 5, 122);
      U.frame2(q, 66, 98, 94, 46);
      U.text(q, '싸우다', 80, 109); U.text(q, '가방', 120, 109); U.text(q, '디지몬', 80, 125); U.text(q, '도망치다', 120, 125);
      U.cursor(q, [74, 114][this.i & 1], [111, 127][this.i >> 1]);
    }
  }
  class MoveMenu {
    constructor(m) { this.overlay = true; this.m = m; this.i = 0; }
    update() {
      const n = this.m.moves.length;
      if (press('up')) this.i = (this.i + n - 1) % n; if (press('down')) this.i = (this.i + 1) % n;
      if (press('a')) close(this, this.i); else if (press('b')) close(this, -1);
    }
    draw(q) {
      U.frame2(q, 0, 64, 92, 80);
      for (let j = 0; j < 4; j++) { const mv = this.m.moves[j]; U.text(q, mv ? mv.n : '-', 14, 72 + j * 16); }
      U.cursor(q, 6, 74 + this.i * 16);
      const mv = this.m.moves[this.i], mi = moveInfo(mv.n);
      U.frame2(q, 94, 96, 66, 48); U.num(q, String(mv.pp).padStart(2, ' ') + '/' + String(mi.pp).padStart(2, ' '), 112, 104);
      U.text(q, mi.kind, 102, 114); U.text(q, mi.pow ? '위력 ' + mi.pow : '변화', 102, 128);
    }
  }
  function foeLabel(B) { const n = nm(B.foe.sp); return B.kind === 'wild' ? '야생 ' + n : n; }
  async function battle(o) {
    const B = { kind: o.kind || 'wild', foe: o.foe, me: alive()[0], sMe: { def: 0, atk: 0 }, sFoe: { def: 0, atk: 0 }, showFoe: false, showMe: false, used: new Set(), runs: 0 };
    B.dfoe = B.foe.hp; B.dme = B.me.hp;
    G.seen[B.foe.sp] = 1;
    await flash(2);
    const sc = new BattleScene(B); open(sc);
    B.showFoe = true; await until(() => sc.foeX <= 96);
    const fn = nm(B.foe.sp);
    await say(o.intro || (B.kind === 'wild' ? `앗! 야생 ${fn}${josa(fn, '이/가')} 나타났다!` : `${fn}${josa(fn, '이/가')} 덤벼들었다!`));
    B.showMe = true; B.used.add(B.me); await say(`가랏! ${nm(B.me.sp)}!`, { auto: 20 }); await until(() => sc.meX >= 16);
    let result = null;
    while (!result) {
      const act = await open(new BattleMenu(B));
      if (act === 0) {
        const mi = await open(new MoveMenu(B.me));
        if (mi < 0) continue;
        if (B.me.moves[mi].pp <= 0) { await say('기술을 쓸 힘이 남아 있지 않다!'); continue; }
        result = await turn(B, sc, B.me.moves[mi]);
      } else if (act === 1) {
        const r = await bagScreen({ battle: true }); if (!r) continue;
        if (r.mon === B.me) B.dme = B.me.hp;
        result = await turn(B, sc, null);
      } else if (act === 2) {
        const i = await partyScreen({ pick: true, msg: '누구를 내보낼까?' });
        if (i < 0) continue; const m = G.party[i];
        if (m.egg) { await say('디지타마는 싸울 수 없다!'); continue; }
        if (m.hp <= 0) { await say(`${nm(m.sp)}${josa(nm(m.sp), '은/는')} 싸울 힘이 없다!`); continue; }
        if (m === B.me) { await say(`${nm(m.sp)}${josa(nm(m.sp), '은/는')} 이미 싸우고 있다!`); continue; }
        await say(`돌아와, ${nm(B.me.sp)}!`, { auto: 20 }); B.meGone = true; await wait(10);
        B.me = m; B.dme = m.hp; B.sMe = { def: 0, atk: 0 }; B.used.add(m); B.meGone = false; sc.meX = -48;
        await say(`가랏! ${nm(m.sp)}!`, { auto: 20 }); await until(() => sc.meX >= 16);
        result = await turn(B, sc, null);
      } else {
        if (B.kind !== 'wild') { await say('도망칠 수 없다!'); continue; }
        B.runs++;
        const chance = (stat(B.me, 3) * 32 / Math.max(1, stat(B.foe, 3)) + 30 * B.runs) / 256;
        if (Math.random() < chance) { await say('무사히 도망쳤다!'); result = 'run'; }
        else { await say('도망칠 수 없었다!'); result = await turn(B, sc, null); }
      }
    }
    if (result === 'win' && B.kind === 'wild') await joinOffer(B.foe);
    close(sc);
    if (result === 'lose') await whiteout(); else { await evolveCheck(); }
    return result;
  }
  async function turn(B, sc, myMove) {
    const foeMoves = B.foe.moves.filter((m) => m.pp > 0);
    const fm = foeMoves.length ? foeMoves[Math.floor(Math.random() * foeMoves.length)] : { n: '부딪치기', pp: 1 };
    const meFirst = myMove && (stat(B.me, 3) > stat(B.foe, 3) || (stat(B.me, 3) === stat(B.foe, 3) && Math.random() < .5));
    const me = B.me, foe = B.foe;
    const order = myMove ? (meFirst ? [['me', myMove], ['foe', fm]] : [['foe', fm], ['me', myMove]]) : [['foe', fm]];
    for (const [who, mv] of order) {
      const att = who === 'me' ? me : foe, def = who === 'me' ? B.foe : B.me;
      if (att.hp <= 0 || (who === 'me' && B.me !== me)) continue;   // 쓰러져 교체됐으면 그 기술은 취소
      await useMove(B, sc, who, att, def, mv);
      const r = await checkFaint(B, sc); if (r) return r;
    }
    return null;
  }
  async function useMove(B, sc, who, att, def, mv) {
    mv.pp = Math.max(0, mv.pp - 1);
    const mi = moveInfo(mv.n), an = who === 'me' ? nm(att.sp) : foeLabel(B), dn = who === 'me' ? foeLabel(B) : nm(def.sp);
    await say(`${an}의 ${mv.n}!`, { auto: 24 });
    if (Math.random() * 100 >= mi.acc) { await say('그러나 빗나갔다!'); return; }
    const sA = who === 'me' ? B.sMe : B.sFoe, sD = who === 'me' ? B.sFoe : B.sMe;
    if (!mi.pow) {
      if (mi.eff === 'foeDef') { if (sD.def <= -6) { await say('효과가 없었다!'); return; } sD.def--; await say(`${dn}의 방어가 떨어졌다!`); }
      if (mi.eff === 'selfDef') { if (sA.def >= 6) { await say('효과가 없었다!'); return; } sA.def++; await say(`${an}의 방어가 올라갔다!`); }
      return;
    }
    const A = stat(att, 1) * stageMul(sA.atk), Dd = stat(def, 2) * stageMul(sD.def);
    let dmg = Math.floor(Math.floor((Math.floor(2 * att.lv / 5) + 2) * mi.pow * A / Dd) / 50) + 2;
    const crit = Math.random() < 1 / 16; if (crit) dmg *= 2;
    const mult = attrMult(SP[att.sp].attr, SP[def.sp].attr);
    dmg = Math.max(1, Math.floor(dmg * mult * (217 + Math.floor(Math.random() * 39)) / 255));
    if (who === 'me') sc.blinkF = 24; else sc.blinkM = 24;
    await wait(24);
    def.hp = Math.max(0, def.hp - dmg);
    await until(() => B.dfoe === B.foe.hp && B.dme === B.me.hp);
    if (crit) await say('급소에 맞았다!');
    if (mult > 1) await say('효과가 굉장했다!'); else if (mult < 1) await say('효과가 별로인 듯하다…');
  }
  async function checkFaint(B, sc) {
    if (B.foe.hp <= 0) {
      B.foeGone = true; await say(`${foeLabel(B)}${josa(nm(B.foe.sp), '은/는')} 쓰러졌다!`);
      const parts = [...B.used].filter((m) => m.hp > 0);
      const gain = Math.max(1, Math.floor(SP[B.foe.sp].exp * B.foe.lv / 5 * (B.kind === 'wild' ? 1 : 1.5) / Math.max(1, parts.length)));
      for (const m of parts) await giveExp(B, m, gain);
      return 'win';
    }
    if (B.me.hp <= 0) {
      const n = nm(B.me.sp); B.meGone = true; await say(`${n}${josa(n, '은/는')} 쓰러졌다!`);
      if (!alive().length) return 'lose';
      for (;;) {
        const i = await partyScreen({ pick: true, must: true, msg: '누구를 내보낼까?' });
        const m = G.party[i]; if (!m || m.egg || m.hp <= 0) { await say('그 디지몬은 싸울 수 없다!'); continue; }
        B.me = m; B.dme = m.hp; B.sMe = { def: 0, atk: 0 }; B.used.add(m); B.meGone = false; sc.meX = -48;
        await say(`가랏! ${nm(m.sp)}!`, { auto: 20 }); await until(() => sc.meX >= 16); break;
      }
    }
    return null;
  }
  async function giveExp(B, m, gain) {
    const n = nm(m.sp);
    await say(`${n}${josa(n, '은/는')} 경험치 ${gain}${numJosa(gain) === '이' ? '을' : '를'} 얻었다!`);
    m.exp += gain;
    while (m.lv < 100 && m.exp >= expAt(m.lv + 1)) {
      const oldMax = maxHp(m); m.lv++; m.hp += maxHp(m) - oldMax; m.lvUp = true; if (m === B.me) B.dme = m.hp;
      await say(`${n}의 레벨이 ${m.lv}${numJosa(m.lv)} 되었다!`);
    }
  }
  async function joinOffer(foe) {
    const tier = SP[foe.sp].tier, p = { baby: .4, baby2: .4, rookie: .3, champion: .2 }[tier] || 0;
    if (Math.random() >= p) return;
    const s = sprite(foe.sp); const pic = showPics([{ img: s, x: 80 - s.width / 2, y: 64 - s.height }]);
    const n = nm(foe.sp);
    const yes = await ask(`${n}${josa(n, '이/가')} 일어나 동료가 되고 싶은 듯 이쪽을 보고 있다!\f${n}${josa(n, '을/를')} 데려갈까?`);
    if (yes) {
      foe.hp = Math.max(1, Math.floor(maxHp(foe) / 2)); for (const mv of foe.moves) mv.pp = moveInfo(mv.n).pp;
      const where = addMon(foe);
      await say(where === 'party' ? `${n}${josa(n, '이/가')} 동료가 되었다!` : `${n}${josa(n, '이/가')} 동료가 되었다!\n(가득 차서 디지몬 보관함으로 보냈다)`);
    } else await say(`${n}${josa(n, '은/는')} 숲으로 돌아갔다…`);
    close(pic);
  }
  async function evolveCheck() {
    for (const m of G.party) {
      if (m.egg || !m.lvUp) continue; m.lvUp = false;
      const e = (SP[m.sp].evo || []).find((e) => m.lv >= e.lv && (!e.need || (e.need !== 'event' && G.crests.includes(e.need))));
      if (e) await evolve(m, e.to);
    }
  }
  class EvoScene {
    constructor(a, b) { this.overlay = false; this.a = a; this.b = b; this.t = 0; this.done = false; }
    tick() { this.t++; }
    update() {}
    draw(q) {
      q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
      const sa = sprite(this.a), sb = sprite(this.b);
      let show = sa, sil = false;
      if (this.done) show = sb;
      else if (this.t > 30) { const per = Math.max(4, 24 - Math.floor((this.t - 30) / 12)); show = Math.floor(this.t / per) % 2 ? sb : sa; sil = true; }
      const c = sil ? silhouetteOf(show) : show;
      q.drawImage(c, 80 - c.width / 2, 84 - c.height);
    }
  }
  const silCache = new Map();
  function silhouetteOf(c) {
    let s = silCache.get(c); if (s) return s;
    s = document.createElement('canvas'); s.width = c.width; s.height = c.height; const q = s.getContext('2d');
    q.drawImage(c, 0, 0); q.globalCompositeOperation = 'source-in'; q.fillStyle = '#383848'; q.fillRect(0, 0, s.width, s.height);
    silCache.set(c, s); return s;
  }
  async function evolve(m, to) {
    const from = m.sp, sc = new EvoScene(from, to); open(sc);
    const n = nm(from);
    await say(`어라…!? ${n}의 모습이…!`, { auto: 40 });
    await until(() => sc.t > 200);
    sc.done = true; await flash(1);
    m.sp = to; const oldMax = maxHp(m); m.hp += Math.max(0, maxHp(m) - oldMax);
    G.seen[to] = 1; G.owned[to] = 1;
    await say(`축하합니다! ${n}${josa(n, '은/는')}\n${nm(to)}${josa(nm(to), '으로/로')} 진화했다!`);
    for (const mv of learn(m, to)) await say(`${nm(to)}${josa(nm(to), '은/는')} ${mv}${josa(mv, '을/를')} 익혔다!`);
    close(sc);
  }
  async function hatch(egg) {
    const sc = showPics([]);
    const eggPic = PX.toCanvas(DigiMons.MON.digitama(), 1);
    sc.items = [{ img: eggPic, x: 68, y: 40 }];
    await say('어라…?', { auto: 40 });
    for (let i = 0; i < 6; i++) { sc.items[0].x = 68 + (i % 2 ? 2 : -2); await wait(8); }
    await flash(2);
    const baby = makeMon(egg.sp, 3); Object.assign(egg, baby); delete egg.egg; delete egg.steps;
    G.seen[baby.sp] = 1; G.owned[baby.sp] = 1;
    const s = sprite(baby.sp); sc.items = [{ img: s, x: 80 - s.width / 2, y: 84 - s.height }];
    const n = nm(baby.sp);
    await say(`디지타마가 부화해서\n${n}${josa(n, '이/가')} 태어났다!`);
    close(sc);
  }
  async function whiteout() {
    await say(`${kidName()}에게는 싸울 수 있는 디지몬이 없다!`);
    await say('눈앞이 캄캄해졌다…');
    await fadeOut();
    G.map = G.heal.map; G.x = G.heal.x; G.y = G.heal.y; G.dir = 'up'; healAll();
    await wait(20); await fadeIn();
    await say('…정신을 차려 보니 쉴 곳으로 돌아와 있었다.\f디지몬들이 모두 기운을 되찾았다.');
  }
  async function wildEncounter(enc) {
    const total = enc.list.reduce((s, e) => s + e[3], 0); let r = Math.random() * total, pick = enc.list[0];
    for (const e of enc.list) { if ((r -= e[3]) < 0) { pick = e; break; } }
    const lv = pick[1] + Math.floor(Math.random() * (pick[2] - pick[1] + 1));
    await battle({ kind: 'wild', foe: makeMon(pick[0], lv) });
  }

  // ───────── 타이틀 · 오프닝 ─────────
  class Title {
    constructor() { this.overlay = false; this.t = 0; }
    tick() { this.t++; }
    update() {}
    draw(q) {
      for (let y = 0; y < 144; y++) { q.fillStyle = y < 56 ? '#6890f0' : y < 84 ? '#88b0f8' : '#a8c8f8'; q.fillRect(0, y, 160, 1); }
      const sh = (this.t >> 2) % 12;
      q.fillStyle = '#f8f8f8'; for (let x = -12; x < 176; x += 12) { q.beginPath(); q.arc(x - sh, 104 + (((x + 12) / 12) | 0) % 2 * 3, 9, 0, 7); q.fill(); } q.fillRect(0, 104, 160, 40);
      logo(q, '디지몬', 20, 4, 3, '#f89830'); U.text(q, '팬 게임 (가제)', 50, 50, '#f8f8f8');
      q.drawImage(sprite('agumon'), 56, 64);
      if ((this.t >> 5) % 2 === 0 && !this.menu) U.text(q, 'START를 누르세요', 40, 124, '#5878c8');
    }
  }
  function logo(q, str, x, y, sc, col) {
    const w = U.textWidth(str) + 4, h = 16, a = document.createElement('canvas'); a.width = w; a.height = h; U.text(a.getContext('2d'), str, 2, 2, col);
    const o = document.createElement('canvas'); o.width = w; o.height = h; U.text(o.getContext('2d'), str, 2, 2, K);
    q.imageSmoothingEnabled = false;
    for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, 1], [-1, 1], [1, -1], [1, 2], [0, 2], [2, 2]]) q.drawImage(o, x + dx, y + dy, w * sc, h * sc);
    q.drawImage(a, x, y, w * sc, h * sc);
  }
  async function titleFlow() {
    const t = new Title(); open(t);
    await until(() => press('start') || press('a'));
    const saved = loadGame();
    t.menu = true;
    const items = saved ? ['이어서 하기', '새로 시작'] : ['새로 시작'];
    let i = await choose(items, { x: 40, y: 92, w: 80, cancel: false });
    if (saved && i === 0) { G = saved; close(t); startField(); await say(`${mapOf().name || ''}에서 이어서 한다.`); return; }
    if (saved && !(await ask('새로 시작하면 지금의 기록은 덮어쓰게 된다. 괜찮을까?'))) { close(t); return titleFlow(); }
    close(t);
    await ST.opening(API);
    startField();
    await fadeIn();
    const map = mapOf(); if (map.onEnter) await field.run(() => map.onEnter(API));
  }
  function startField() { field = new Field(); stack.length = 0; open(field); if (blackout) stack.push(blackout); }

  // ───────── 이야기 쪽에서 쓰는 도구 ─────────
  const API = {
    say, ask, choose, wait, until, evolve, partyScreen, fadeOut, fadeIn, flash, showPics, close, open, sprite, josa, nm, makeMon, addMon, healAll, maxHp, battle, saveGame,
    get G() { return G; }, set G(v) { G = v; }, newState, kidName, warp, PX, U, FLD, SP, cvs,
    give(item, n) { G.bag[item] = (G.bag[item] || 0) + (n || 1); },
    flag(f) { return !!G.flags[f]; }, setFlag(f) { G.flags[f] = 1; },
    crest(c) { if (!G.crests.includes(c)) G.crests.push(c); },
    partner() { return G.party.find((m) => !m.egg); },
    pickKid: async (order, confirm) => {               // 아이 고르기 — confirm(kid)이 참이면 끝
      const names = order.map((k) => FLD.KIDS[k].name);
      class KidPick {
        constructor() { this.overlay = false; this.i = 0; this.locked = false; }
        update() {
          if (this.locked) return;
          const n = order.length; if (press('up')) this.i = (this.i + n - 1) % n; if (press('down')) this.i = (this.i + 1) % n;
          if (press('a')) { this.locked = true; Promise.resolve(confirm ? confirm(order[this.i]) : true).then((ok) => { this.locked = false; if (ok) close(this, this.i); }); }
        }
        draw(q) {
          q.fillStyle = PAPER; q.fillRect(0, 0, 160, 144);
          U.text(q, '선택받은 아이', 8, 2);
          U.frame(q, 0, 16, 80, 128);
          names.forEach((n, j) => U.text(q, n, 18, 21 + j * 15)); if (!this.locked || (frameNo >> 3) % 2) U.cursor(q, 9, 23 + this.i * 15);
          const k = order[this.i];
          if (k === 'taichi') q.drawImage(sprite_people('taichi'), 104, 20);
          else { q.imageSmoothingEnabled = false; q.drawImage(cvs(FLD.WALKS[k].down[0]), 96, 28, 48, 48); }
          if (!this.locked) { const ps = DigiStory.PARTNER[k]; U.text(q, '파트너', 88, 84); U.text(q, nm(ps), 92, 100); }
        }
      }
      return order[await open(new KidPick())];
    }
  };
  const peopleCache = {};
  function sprite_people(k) { return peopleCache[k] || (peopleCache[k] = PX.toCanvas(DigiPeople.PEOPLE[k](), 1)); }
  API.peopleSprite = sprite_people;

  // ───────── 돌리기 ─────────
  let frameNo = 0, acc = 0, last = performance.now();
  function step() {
    frameNo++;
    if (G && field && stack.includes(field)) G.time++;
    for (const sc of stack.slice()) if (sc.tick) sc.tick();
    const top = stack[stack.length - 1]; if (top && top.update) top.update();
    for (let i = waiters.length - 1; i >= 0; i--) { const w = waiters[i]; if (w.pred ? w.pred() : --w.n <= 0) { waiters.splice(i, 1); w.r(); } }
    for (const k in hit) hit[k] = false;
  }
  function render() {
    let s = stack.length - 1; while (s > 0 && stack[s].overlay) s--;
    g.fillStyle = '#000'; g.fillRect(0, 0, 160, 144);
    for (let i = Math.max(0, s); i < stack.length; i++) stack[i].draw(g);
  }
  function loop(now) {
    acc += Math.min(100, now - last); last = now;
    while (acc >= 1000 / 60) { step(); acc -= 1000 / 60; }
    render(); requestAnimationFrame(loop);
  }
  window.DigiGame = { API, get G() { return G; }, stack, press, held, hit, step, render };
  requestAnimationFrame(loop);
  titleFlow();
})();
