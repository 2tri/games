// 웹판 자료(글꼴·디지몬·필드 그림)를 JSON으로 내보냄 → build.py 가 GBC 데이터로 바꿈
const vm = require('vm'), fs = require('fs'), path = require('path');
const W = path.join(__dirname, '..', '..');
const ctx = { console }; ctx.window = ctx; ctx.globalThis = ctx; vm.createContext(ctx);
for (const f of ['font.js', 'pix.js', 'mons.js', 'field.js', 'species.js']) vm.runInContext(fs.readFileSync(path.join(W, f), 'utf8'), ctx, { filename: f });
const F = ctx.DigiField, pic = (s) => ({ w: s.w, h: s.h, p: s.p.map((c) => c || 0) });
const out = {
  font: ctx.DigiFontData,
  species: ctx.DigiSpecies, power: ctx.DigiPower,
  kids: Object.fromEntries(Object.entries(F.KIDS).map(([k, v]) => [k, { name: v.name, map: v.map }])),
  tiles: Object.fromEntries(Object.entries(F.TILE).map(([k, v]) => [k, pic(v)])),
  walks: Object.fromEntries(Object.entries(F.WALKS).map(([k, v]) => [k, Object.fromEntries(Object.entries(v).map(([d, fr]) => [d, fr.map(pic)]))])),
  walk1: { agumon: pic(F.WALK.agumon), elecmon: pic(F.WALK.elecmon) },
  blob: pic(F.blob('#c0c0c0', '#606060'))
};
fs.writeFileSync(process.argv[2], JSON.stringify(out));
console.log('exported', Object.keys(out.tiles).length, 'tiles', Object.keys(out.walks).length, 'kids', Object.keys(out.species).length, 'species');
