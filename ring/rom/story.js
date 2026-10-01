// 웹판 index.html 의 이야기(CH1 배열)를 C 로 옮김 → src/story_N.c (은행마다 나눔) + src/steps.c
// 대사 문장은 그대로 옮기므로 웹판을 고치면 롬도 다시 빌드만 하면 된다.
const fs = require('fs'), path = require('path');
const ts = require(require('child_process').execSync('npm root -g').toString().trim() + '/typescript');
const html = fs.readFileSync(__dirname + '/../index.html', 'utf8');
const a = html.indexOf('const CH1 = ['), b = html.indexOf('\n];', a) + 3;
const src = ts.createSourceFile('ch1.js', html.slice(a, b), ts.ScriptTarget.ES2020, true);
const SRC = __dirname + '/src';
const FIRST_BANK = +process.argv[2] || 8, BANK_SIZE = 15500;

const up = s => s.toUpperCase();
const cstr = s => JSON.stringify(s);
const txt = n => n.getText(src);
// 특별한 문장(웹판의 자바스크립트 기능을 쓰는 것)은 그대로 대응되는 C 로
const SPECIAL = {
  "for (const id in S.mem) S.mem[id].hp = Math.max(1, S.mem[id].hp - 8);": 'party_hurt(8);',
  "for (const id in S.mem) S.mem[id].hp = Math.max(S.mem[id].hp, Math.round(statOf(id, S.mem[id].lv, 'hp') / 3));": 'party_floor_third();',
  "if (S.hero === 'frodosam') S.hp = Math.min(S.hp, stat('hp')); else if (S.mem.frodosam) S.mem.frodosam.hp = Math.min(S.mem.frodosam.hp, statOf('frodosam', S.mem.frodosam.lv, 'hp'));": 'frodo_cap_hp();',
  "if (S.hero === 'frodosam') S.hp = stat('hp'); else if (S.mem.frodosam) S.mem.frodosam.hp = statOf('frodosam', S.mem.frodosam.lv, 'hp');": 'frodo_full_hp();',
  "for (const id of ['aragorn', 'legolas', 'gimli']) removeMember(id);": 'removeMember(HE_ARAGORN); removeMember(HE_LEGOLAS); removeMember(HE_GIMLI);',
  "const keep = { hero: S.hero, lv: S.lv, xp: S.xp, hp: S.hp, party: S.party.slice(), mem: JSON.parse(JSON.stringify(S.mem)) };": 'keep_party();',
  "S.party = ['aragorn'];": 'solo_party(HE_ARAGORN);',
  "S.mem = {};": '',
  "Object.assign(S, keep);": 'restore_party();',
};
const FIELD = { 'S.items.lembas': 'S.lembas', 'S.items.herb': 'S.herb' };
const R = { win: 'R_WIN', lose: 'R_LOSE', run: 'R_RUN' };
let vars, pre;   // 함수 안 변수, 문장 앞에 먼저 넣을 C (글 조립)
let lit = 0;

function strArg(n) {   // 문자열 인자: 그냥 글이면 그대로, 템플릿이면 SB 로 조립
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return cstr(n.text);
  if (ts.isTemplateExpression(n)) {
    let c = 'sb_clear(); sb_add(' + cstr(n.head.text) + '); ';
    for (const sp of n.templateSpans) c += 'sb_num(' + expr(sp.expression) + ', 0); sb_add(' + cstr(sp.literal.text) + '); ';
    pre.push(c); return 'SB';
  }
  if (ts.isConditionalExpression(n)) return '(' + expr(n.condition) + ' ? ' + strArg(n.whenTrue) + ' : ' + strArg(n.whenFalse) + ')';
  throw new Error('글 인자 모름: ' + txt(n));
}
function idConst(n, kind) { if (!ts.isStringLiteral(n)) throw new Error('이름 아님: ' + txt(n)); return kind + up(n.text); }
function expr(n) {
  const t = txt(n);
  if (FIELD[t]) return FIELD[t];
  if (ts.isParenthesizedExpression(n)) return '(' + expr(n.expression) + ')';
  if (ts.isNumericLiteral(n)) return n.text;
  if (n.kind === ts.SyntaxKind.TrueKeyword) return '1';
  if (n.kind === ts.SyntaxKind.FalseKeyword) return '0';
  if (ts.isIdentifier(n)) return n.text;
  if (ts.isPropertyAccessExpression(n)) { if (t.startsWith('S.')) return t; throw new Error('속성 모름: ' + t); }
  if (ts.isPrefixUnaryExpression(n)) return ts.tokenToString(n.operator) + expr(n.operand);
  if (ts.isPostfixUnaryExpression(n)) return expr(n.operand) + ts.tokenToString(n.operator);
  if (ts.isConditionalExpression(n)) return '(' + expr(n.condition) + ' ? ' + expr(n.whenTrue) + ' : ' + expr(n.whenFalse) + ')';
  if (ts.isBinaryExpression(n)) {
    let op = n.operatorToken.getText(src); if (op === '===') op = '=='; if (op === '!==') op = '!=';
    const L = n.left, Rt = n.right;
    if (ts.isStringLiteral(Rt)) {
      const lt = txt(L);
      if (lt === 'S.hero' || lt === 'S.lead') return expr(L) + ' ' + op + ' HE_' + up(Rt.text);
      if (R[Rt.text]) return expr(L) + ' ' + op + ' ' + R[Rt.text];
      throw new Error('비교 모름: ' + t);
    }
    if (op === '=' && txt(L) === 'S.hero' && ts.isStringLiteral(Rt)) return 'S.hero = HE_' + up(Rt.text);
    return expr(L) + ' ' + op + ' ' + expr(Rt);
  }
  if (ts.isCallExpression(n)) {
    const f = txt(n.expression), A = n.arguments;
    if (f === 'stat') return 'stat(ST_' + up(A[0].text) + ')';
    if (f === 'Math.max' || f === 'Math.min') return (f === 'Math.max' ? 'MAX(' : 'MIN(') + expr(A[0]) + ', ' + expr(A[1]) + ')';
    if (f === 'Math.round') { const d = A[0]; if (ts.isBinaryExpression(d) && d.operatorToken.getText(src) === '/') return '(((' + expr(d.left) + ') + ' + expr(d.right) + ' / 2) / ' + expr(d.right) + ')'; return expr(d); }
    if (f === 'save' || f === 'healAll') return f + '()';
    if (f === 'swapTo' || f === 'removeMember') return f + '(' + idConst(A[0], 'HE_') + ')';
    if (f === 'addMember') return 'addMember(' + idConst(A[0], 'HE_') + ', ' + expr(A[1]) + ')';
    if (f === 'S.party.includes') return 'has(' + idConst(A[0], 'HE_') + ')';
    if (f === 'lose') return 'lose()';
    throw new Error('함수 모름: ' + t);
  }
  throw new Error('식 모름: ' + t);
}
function arr(n) { if (!ts.isArrayLiteralExpression(n)) throw new Error('배열 아님: ' + txt(n)); return n.elements; }
function linesArr(els) {   // 글 배열 → C 배열 이름
  const name = 'L' + (lit++);
  const items = els.map(strArg);
  if (items.some(x => !x.startsWith('"'))) { return { decl: 'const char *' + name + '[' + items.length + ']; ' + items.map((x, i) => name + '[' + i + '] = ' + x + ';').join(' '), name, n: items.length, dyn: true }; }
  return { decl: 'static const char * const ' + name + '[] = { ' + items.join(', ') + ' };', name, n: items.length };
}
function awaitCall(n, assign) {   // await f(...) → C
  const c = n.expression, f = txt(c.expression), A = c.arguments;
  const as = assign ? assign + ' = ' : '';
  if (f === 'chapterTitle') { const x = strArg(A[0]), y = strArg(A[1]); return 'chapterTitle(' + x + ', ' + y + ');'; }
  if (f === 'say') return 'say(' + strArg(A[0]) + ');';
  if (f === 'story') {
    const place = ts.isStringLiteral(A[0]) ? cstr(A[0].text) : '0';
    const spr = A[1].kind === ts.SyntaxKind.NullKeyword ? '255' : 'SP_' + up(A[1].text);
    const L = linesArr(arr(A[2]));
    return '{ ' + L.decl + ' story(' + place + ', ' + spr + ', ' + L.name + ', ' + L.n + '); }';
  }
  if (f === 'choose') {
    const q = A[0].kind === ts.SyntaxKind.NullKeyword ? '0' : strArg(A[0]);
    const L = linesArr(arr(A[1]));
    return '{ ' + L.decl + ' ' + as + 'choose(' + q + ', ' + L.name + ', ' + L.n + ', NOCANCEL); }';
  }
  if (f === 'battle') {
    let noRun = 0, turns = 0, hint = null, rl = null;
    if (A[1]) for (const p of A[1].properties) {
      const k = p.name.text;
      if (k === 'noRun') noRun = 1;
      else if (k === 'rescue') for (const q of p.initializer.properties) {
        if (q.name.text === 'turns') turns = +q.initializer.text;
        if (q.name.text === 'hint') hint = strArg(q.initializer);
        if (q.name.text === 'lines') rl = arr(q.initializer).map(strArg);
      } else throw new Error('전투 설정 모름: ' + k);
    }
    const v = assign || '_r';
    let out = (hint ? 'say(' + hint + '); ' : '') + v + ' = battle(FO_' + up(A[0].text) + ', ' + noRun + ', ' + turns + ');';
    if (turns) out += ' if (' + v + ' == R_RESCUE) { ' + rl.map(x => 'say(' + x + ');').join(' ') + ' rescue_end(); ' + v + ' = R_WIN; }';
    return out;
  }
  throw new Error('await 모름: ' + txt(n));
}
function stmt(n, ind) {
  const t = txt(n);
  if (SPECIAL[t] !== undefined) return ind + SPECIAL[t];
  pre = [];
  let body;
  if (ts.isBlock(n)) return ind + '{\n' + n.statements.map(s => stmt(s, ind + '  ')).join('\n') + '\n' + ind + '}';
  if (ts.isIfStatement(n)) {
    const c = expr(n.expression); const p0 = pre.join('');
    return ind + p0 + 'if (' + c + ') ' + stmt(n.thenStatement, '').trim() + (n.elseStatement ? ' else ' + stmt(n.elseStatement, '').trim() : '');
  }
  if (ts.isForStatement(n) && !n.initializer && !n.condition) return ind + 'for (;;) ' + stmt(n.statement, ind).trim();
  if (ts.isBreakStatement(n)) return ind + 'break;';
  if (ts.isReturnStatement(n)) { if (txt(n.expression) === 'lose()') return ind + '{ lose(); return; }'; throw new Error('return 모름: ' + t); }
  if (ts.isVariableStatement(n)) {
    const d = n.declarationList.declarations[0], name = d.name.text; vars.add(name);
    const init = d.initializer;
    if (ts.isAwaitExpression(init)) body = awaitCall(init, name); else body = name + ' = ' + expr(init) + ';';
  } else if (ts.isExpressionStatement(n)) {
    const e = n.expression;
    if (ts.isAwaitExpression(e)) body = awaitCall(e, null);
    else if (ts.isBinaryExpression(e) && e.operatorToken.getText(src) === '=' && ts.isAwaitExpression(e.right)) body = awaitCall(e.right, txt(e.left));
    else if (ts.isBinaryExpression(e) && e.operatorToken.getText(src) === '=' && txt(e.left) === 'S.hero') body = 'S.hero = HE_' + up(e.right.text) + ';';
    else body = expr(e) + ';';
  } else throw new Error('문장 모름: ' + t);
  const p = pre.join('');
  return ind + p + body;
}
const steps = src.statements[0].declarationList.declarations[0].initializer.elements;
const funcs = steps.map((f, i) => {
  vars = new Set(['_r']); lit = 0;
  const body = f.body.statements.map(s => stmt(s, '  ')).join('\n');
  if (!body.includes('_r')) vars.delete('_r');
  return 'void step_' + i + '(void) BANKED {\n' + (vars.size ? '  uint8_t ' + [...vars].join(', ') + ';\n' : '') + body + '\n}\n';
});
// 은행마다 나눔 (글자가 대부분이라 크기 ≈ C 소스 바이트)
for (const f of fs.readdirSync(SRC)) if (/^story_\d+\.c$/.test(f)) fs.unlinkSync(SRC + '/' + f);
let bank = FIRST_BANK, size = 0, files = {}, bankOf = [];
funcs.forEach((c, i) => {
  const sz = Buffer.byteLength(c) * 0.8;
  if (size + sz > BANK_SIZE) { bank++; size = 0; }
  size += sz; (files[bank] = files[bank] || []).push(c); bankOf.push(bank);
});
const HDR = '#include <gb/gb.h>\n#include "data.h"\n#include "engine.h"\n#include "game.h"\n#include "story.h"\n';
for (const [bk, cs] of Object.entries(files)) fs.writeFileSync(SRC + '/story_' + bk + '.c', '#pragma bank ' + bk + '\n' + HDR + cs.join('\n'));
fs.writeFileSync(SRC + '/steps.h', '#include <gb/gb.h>\n#define N_STEPS ' + funcs.length + '\n' + funcs.map((_, i) => 'void step_' + i + '(void) BANKED;').join('\n') + '\nvoid run_step(uint8_t s);\n');
fs.writeFileSync(SRC + '/steps.c', '#include "steps.h"\nvoid run_step(uint8_t s) {\n  switch (s) {\n' + funcs.map((_, i) => '    case ' + i + ': step_' + i + '(); break;').join('\n') + '\n  }\n}\n');
console.log('이야기', funcs.length, '단계, 은행', Object.keys(files).join(','));
