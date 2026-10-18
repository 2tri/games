// index.html 의 HEROES·MOVES·FOES·EFFECT 를 그대로 꺼내 JSON 으로 (밸런스를 웹판과 같게)
const s = require('fs').readFileSync(__dirname + '/../index.html', 'utf8');
const a = s.indexOf('const HEROES = {'), e = s.indexOf('\n', s.indexOf('const EFFECT ='));
const d = new Function(s.slice(a, e) + '\nreturn { HEROES, MOVES, FOES, EFFECT };')();
process.stdout.write(JSON.stringify(d));
