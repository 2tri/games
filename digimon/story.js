// 디지몬 팬 게임 — 이야기·지도·사건 (프롤로그 ~ 1부 첫 문장)
// 지도 글자:  . 풀  , 풀숲(야생)  T 나무  : 길  * 꽃  s 모래  ~ 바다  w 물가  D 짙은 나무  d 짙은 풀  S 표지판  F 모닥불  c 요람  e 디지타마
// 큰 물건(집·텐트·야자수·전화박스)은 objs 에 따로 적는다 (칸을 차지하고 지나갈 수 없음).
(function (root) {
  'use strict';
  const SP = root.DigiSpecies;

  const KEY = { '.': 'grass', ',': 'tall', T: 'tree', ':': 'path', '*': 'flower', s: 'sand', '~': 'sea', w: 'shore', D: 'dtree', d: 'dgrass', S: 'sign', F: 'fire', c: 'crib', e: 'egg' };
  const CRESTS = ['용기', '우정', '사랑', '지식', '순수', '성실', '희망', '빛'];
  const ORDER = ['taichi', 'yamato', 'sora', 'koushiro', 'mimi', 'jou', 'takeru', 'hikari'];
  const PARTNER = { taichi: 'agumon', yamato: 'gabumon', sora: 'piyomon', koushiro: 'tentomon', mimi: 'palmon', jou: 'gomamon', takeru: 'patamon', hikari: 'salamon' };
  const BABY = { taichi: 'koromon', yamato: 'tsunomon', sora: 'pyocomon', koushiro: 'mochimon', mimi: 'tanemon', jou: 'bukamon', takeru: 'tokomon', hikari: 'nyaromon' };
  const BABY2 = ['koromon', 'tsunomon', 'pyocomon', 'mochimon', 'tanemon', 'bukamon', 'tokomon', 'nyaromon'];

  // 도감 순서: 주인공 파트너 줄기 → 나머지 (등급 순)
  const TIERS = ['baby', 'baby2', 'rookie', 'champion', 'ultimate', 'mega'];
  const dexOrder = [];
  const addLine = (id) => { while (id && !dexOrder.includes(id)) { dexOrder.push(id); const e = (SP[id].evo || [])[0]; id = e && e.to; } };
  addLine('botamon'); addLine('punimon');
  for (const k of ORDER) addLine(BABY[k]);
  for (const t of TIERS) for (const id in SP) if (SP[id].tier === t && !dexOrder.includes(id)) dexOrder.push(id);

  const items = {
    '회복 디스크': { heal: 20, desc: '디지몬의 체력을 20 회복한다' },
    '고급 회복 디스크': { heal: 50, desc: '디지몬의 체력을 50 회복한다' }
  };

  // 지도 가장자리로 나가는 길: xs 칸들을 to 지도의 (tx0 + 오프셋, ty)로 잇는다
  const edge = (xs, y, to, tx0, ty) => xs.map((x, i) => ({ edge: true, x, y, to, tx: tx0 + i, ty }));
  const edgeV = (x, ys, to, tx, ty0) => ys.map((y, i) => ({ edge: true, x, y, to, tx, ty: ty0 + i }));
  const KID_LINE = {
    taichi: '한여름에 눈이라니… 축구공이 다 젖겠는걸.',
    yamato: '…리키는 어디 갔지? 너무 멀리 가지 말라고 했는데.',
    sora: '모자 챙겨 오길 잘했다. 눈이 그칠 생각을 안 하네.',
    koushiro: '노트북에 전파가 안 잡혀요. 이상한데요…',
    mimi: '추워~! 그러니까 캠프 같은 거 오기 싫었단 말이야!',
    jou: '다들 선생님 말씀 잘 들어! 함부로 돌아다니면 안 돼!',
    takeru: '와, 눈이다! 여름인데 눈이 와!',
    hikari: '…감기 기운이 있어서 오늘은 쉬고 싶었는데.'
  };

  // ───── 지도 ─────
  const maps = {};

  // 여름 캠프 (현실 세계)
  maps.camp = {
    name: '여름 캠프', border: 'tree', key: KEY,
    rows: [
      'TTTTT::TTTTT',
      'T....::....T',
      'T.*..::..*.T',
      'T..........T',
      'T..........T',
      'T....F.....T',
      'T..........T',
      'T.*......*.T',
      'T..........T',
      'TTTTTTTTTTTT'],
    objs: [{ t: 'tent', x: 1, y: 3, w: 2, h: 2 }, { t: 'tent', x: 8, y: 3, w: 2, h: 2 }, { t: 'tent', x: 8, y: 7, w: 2, h: 2 }],
    npcs: [],
    triggers: [{ x: 5, y: 1, w: 2, h: 1, once: 'aurora', run: aurora }],
    onEnter: async (A) => {
      if (A.flag('campIntro')) return;
      A.setFlag('campIntro');
      await A.say('여름 방학, 캠프 날.\f그런데 한여름인데도 갑자기 눈이 내리기 시작했다…');
      await A.say('모두 언덕 위 사당 쪽이 이상하다며 웅성거리고 있다.\n(위쪽 길로 가 보자)');
    }
  };
  // 캠프장의 다른 아이들 (주인공으로 고른 아이와 나리는 빠짐)
  const CAMP_SPOTS = { taichi: [4, 4, 'right'], yamato: [7, 5, 'left'], sora: [4, 6, 'up'], koushiro: [2, 7, 'up'], mimi: [3, 2, 'down'], jou: [5, 8, 'up'], takeru: [7, 4, 'down'] };
  for (const k in CAMP_SPOTS) {
    const [x, y, dir] = CAMP_SPOTS[k];
    maps.camp.npcs.push({ x, y, spr: k, dir, cond: (G) => G.kid !== k && !G.flags.aurora, text: () => root.DigiField.KIDS[k].name + ': ' + KID_LINE[k] });
  }
  async function aurora(A) {
    await A.say('하늘에 오로라가 펼쳐졌다…!');
    await A.flash(2);
    await A.say('하늘에서 빛나는 것들이 떨어졌다!');
    await A.say(A.kidName() + josaOf(A, A.kidName(), '은/는') + ' 작은 기계를 주웠다.\f디지바이스를 손에 넣었다!');
    A.setFlag('digivice');
    await A.say('디지바이스가 빛나기 시작했다…!\f몸이 어딘가로 빨려 들어간다!');
    await A.flash(3);
    await A.fadeOut('#f8f8f8');
    const G = A.G; G.map = 'forest'; G.x = 5; G.y = 10; G.dir = 'up';
    await A.wait(30);
    await A.fadeIn();
    await maps.forest.onEnter(A);
  }
  const josaOf = (A, w, p) => A.josa(w, p);

  // 파일섬 숲 (디지털 월드에 떨어진 곳)
  maps.forest = {
    name: '파일섬 숲', border: 'dtree', key: KEY, open: [[5, -9, 7, -1, 'dgrass']],
    rows: [
      'DDDDDdddDDDD',
      'DDddddddddDD',
      'DddDDddDDddD',
      'DddDdddddddD',
      'DdddddDDdddD',
      'DDddddDDdddD',
      'DdddddddddDD',
      'DddDDdddddDD',
      'DddDDddddddD',
      'DddddddDDddD',
      'DDddddddddDD',
      'DDDDDDDDDDDD'],
    warps: edge([5, 6, 7], -1, 'route1', 5, 17),
    triggers: [{ x: 2, y: 3, w: 9, h: 1, once: 'kuwaga', cond: (G) => G.flags.partner, run: kuwagaEvent }],
    npcs: [],
    onEnter: async (A) => {
      if (A.flag('partner')) return;
      A.setFlag('partner');
      const G = A.G; G.heal = { map: 'forest', x: 5, y: 9, dir: 'up' };
      await A.say('…여기는 어디지?\f처음 보는 정글 한가운데에 떨어져 있었다.');
      const id = BABY[G.kid], n = A.nm(id), s = A.sprite(id);
      const pic = A.showPics([{ img: s, x: 80 - s.width / 2, y: 70 - s.height }]);
      await A.say('???: 어이~! 여기야, 여기!');
      await A.say(`${n}: 기다리고 있었어, ${A.kidName()}!\f나는 ${n}! 디지몬이야!`);
      await A.say(`${n}: 너를 줄곧 기다렸어.\n이제부터 내가 함께할게!`);
      A.addMon(A.makeMon(id, 3));
      await A.say(`${n}${A.josa(n, '이/가')} 동료가 되었다!`);
      A.close(pic);
      await A.say('START 버튼으로 메뉴를 열 수 있다.\f우선 숲을 빠져나가 보자. (위쪽)');
    }
  };
  async function kuwagaEvent(A) {
    const G = A.G, m = A.partner(), kn = A.nm('kuwagamon');
    await A.say('부우우웅…!\f거대한 날갯소리가 다가온다!');
    await A.flash(1);
    const s = A.sprite('kuwagamon');
    const pic = A.showPics([{ img: s, x: 80 - s.width / 2, y: 70 - s.height }]);
    await A.say(`${kn}${A.josa(kn, '이/가')} 덮쳐 왔다!`);
    const bn = A.nm(m.sp);
    await A.say(`${bn}: ${A.kidName()}에게는 손대지 마!`);
    A.close(pic);
    const to = PARTNER[G.kid];
    m.lv = 5; m.exp = 125;
    await A.evolve(m, to);
    m.hp = A.maxHp(m);
    const rn = A.nm(to), sig = SP[to].sig[0];
    const pic2 = A.showPics([{ img: s, x: 80 - s.width / 2, y: 70 - s.height }]);
    await A.say(`${rn}의 ${sig}!`);
    await A.flash(1);
    await A.say(`${kn}${A.josa(kn, '은/는')} 숲 너머로 날아가 버렸다…`);
    A.close(pic2);
    await A.say(`${rn}: 휴우… 다행이다.\f${rn}: 이 섬 어딘가에 디지몬들이 사는 마을이 있어. 가 보자!`);
  }

  // 1번 길 (숲 → 행복의 마을)
  maps.route1 = {
    name: '1번 길', border: 'tree', key: KEY, open: [[4, -9, 5, -1, 'path'], [5, 18, 7, 29, 'path']],
    rows: [
      'TTTT::TTTTTT',
      'T...::.....T',
      'T.,,::..,,,T',
      'T.,,::..,,,T',
      'T...:::....T',
      'T....::....T',
      'T,,,.::.**.T',
      'T,,,.::....T',
      'T,,,.::,,,.T',
      'T....::,,,.T',
      'T.S..::,,,.T',
      'T....::....T',
      'T.**.::.,,,T',
      'T....::.,,,T',
      'T,,,.::.,,,T',
      'T,,,.::....T',
      'T....:::...T',
      'TTTTT:::TTTT'],
    signs: [{ x: 2, y: 10, text: '1번 길\n↑ 행복의 마을   ↓ 파일섬 숲' }],
    warps: edge([4, 5], -1, 'village', 5, 11).concat(edge([5, 6, 7], 18, 'forest', 5, 0)),
    enc: { rate: 0.1, list: [['picodevimon', 2, 4, 20], ['tentomon', 2, 4, 15], ['palmon', 2, 4, 15], ['elecmon', 3, 4, 10], ['koromon', 2, 3, 25], ['tsunomon', 2, 3, 15]] },
    onEnter: async (A) => {
      if (A.flag('route1')) return;
      A.setFlag('route1');
      await A.say('풀숲에는 야생 디지몬이 숨어 있다.\f쓰러뜨린 디지몬이 동료가 되고 싶어 할 때도 있다!');
    }
  };

  // 행복의 마을 (디지몬이 태어나는 마을, 관리인 에렉몬)
  maps.village = {
    name: '행복의 마을', border: 'tree', key: KEY, open: [[5, 12, 6, 29, 'path'], [12, 4, 29, 6, 'path']],
    rows: [
      'TTTTTTTTTTTT',
      'T..........T',
      'T.c.e..c.e.T',
      'T..........T',
      'T....::....:',
      'T.e..::..c.:',
      'T....::....:',
      'T*...::...*T',
      'T....::....T',
      'T..........T',
      'T.*..::..*.T',
      'TTTTT::TTTTT'],
    objs: [{ t: 'blockHouse', x: 1, y: 7, w: 2, h: 2 }, { t: 'blockHouse', x: 8, y: 7, w: 2, h: 2 }, { t: 'blockR', x: 4, y: 1, w: 1, h: 1 }, { t: 'blockB', x: 7, y: 1, w: 1, h: 1 }],
    warps: edge([5, 6], 12, 'route1', 4, 0).concat(edgeV(12, [4, 5, 6], 'beach', 0, 6)),
    npcs: [
      { x: 6, y: 3, spr: 'elecmon', talk: elecmonTalk },
      { x: 3, y: 4, spr: 'blob:botamon', text: '깜몬: 뽀글… 뽀글…' },
      { x: 9, y: 9, spr: 'blob:punimon', text: '푸니몬: 푸니~ 푸니~' },
      { x: 4, y: 9, spr: 'blob:koromon', text: '코로몬: 이 마을에서는 디지몬이 디지타마에서 태어나!\f다시 태어날 때도 여기로 돌아온대.' }
    ],
    onEnter: async (A) => {
      if (A.flag('village')) return;
      A.setFlag('village');
      await A.say('알록달록한 블록과 요람이 가득한 마을이다.\f아기 디지몬들이 잠들어 있다.');
    }
  };
  async function elecmonTalk(A) {
    const G = A.G, n = '에렉몬';
    if (!A.flag('elecmon')) {
      A.setFlag('elecmon');
      await A.say(`${n}: 여기는 행복의 마을. 디지몬이 디지타마에서 태어나는 곳이야.\f나는 이 마을을 지키는 ${n}!`);
      await A.say(`${n}: …뭐? 인간이 디지털 월드에 왔다고?\n게다가 디지몬과 함께?`);
      await A.say(`${n}: 좋아, 믿어 줄게.\f지쳤으면 언제든 나한테 와. 디지몬들을 쉬게 해 줄게.`);
      A.give('회복 디스크', 3);
      await A.say('회복 디스크를 3개 받았다!');
      const egg = { egg: true, sp: BABY2[Math.floor(Math.random() * BABY2.length)], steps: 200, lv: 1, hp: 0, exp: 0, moves: [] };
      const where = A.G.party.length < 6 ? (A.G.party.push(egg), 'party') : (A.G.box.push(egg), 'box');
      await A.say(`${n}: 그리고 이건 막 생겨난 디지타마야.\n데려가서 따뜻하게 해 줘.`);
      await A.say('디지타마를 받았다!' + (where === 'box' ? '\n(보관함으로 보냈다)' : ''));
      await A.say(`${n}: 디지몬에게는 속성이 있어.\f백신은 바이러스에 강하고,\n바이러스는 데이터에 강하고,\f데이터는 백신에 강해.\n잘 기억해 둬!`);
    }
    if (await A.ask(`${n}: 디지몬들을 쉬게 해 줄까?`)) {
      await A.fadeOut();
      A.healAll();
      G.heal = { map: 'village', x: 6, y: 4, dir: 'up' };
      await A.wait(20);
      await A.fadeIn();
      await A.say(`${n}: 다들 기운을 되찾았어!\n또 와!`);
    } else await A.say(`${n}: 조심해서 다녀!`);
  }

  // 해변 (전화박스가 늘어선 바닷가, 쉘몬)
  maps.beach = {
    name: '파일섬 해변', key: KEY, open: [[-9, 6, -1, 8, 'sand']], border: (x, y) => (x >= 11 ? 'sea' : 'tree'),
    rows: [
      'TTTTTTsssTT~~~~',
      'T,,,ssssssw~~~~',
      'T,,,ssssssw~~~~',
      'T,,ssssssssw~~~',
      'Tssssssssssw~~~',
      'Tssssssssssw~~~',
      'ssssssssssssw~~',
      'ssssssssssssw~~',
      'ssssssssssssw~~',
      'T,,,ssssssssw~~',
      'T,,,,ssssssw~~~',
      'TTTTTTTTTTTw~~~'],
    objs: [{ t: 'palm', x: 1, y: 4, w: 1, h: 2 }, { t: 'palm', x: 9, y: 8, w: 1, h: 2 }, { t: 'booth', x: 4, y: 3, w: 1, h: 2 }, { t: 'booth', x: 5, y: 3, w: 1, h: 2 }, { t: 'booth', x: 6, y: 3, w: 1, h: 2 }],
    warps: edgeV(-1, [6, 7, 8], 'village', 11, 4),
    enc: { rate: 0.1, list: [['gomamon', 5, 7, 25], ['piyomon', 5, 7, 20], ['bukamon', 4, 6, 20], ['pyocomon', 4, 6, 15], ['tanemon', 4, 6, 10]] },
    npcs: [
      { x: 7, y: 0, spr: 'blob:shellmon', fixed: true, cond: (G) => !G.flags.shellmon, talk: shellmonTalk },
      { x: 7, y: 0, spr: (G) => companion(G), cond: (G) => !!G.flags.shellmon, talk: companionTalk }
    ],
    signs: [
      { x: 4, y: 4, text: '전화기를 들어 보았다…\f「…오늘의 날씨는…」\n알 수 없는 안내 방송만 흘러나온다.' },
      { x: 5, y: 4, text: '전화기를 들어 보았다…\f「뚜― 뚜―」\n아무 데도 이어지지 않는다.' },
      { x: 6, y: 4, text: '해변 한가운데에 전화박스가 줄지어 서 있다.\f…왜 이런 곳에?' }
    ],
    triggers: [{ x: 6, y: 1, w: 3, h: 1, cond: (G) => !G.flags.shellmon, run: (A) => shellmonTalk(A) }],
    onEnter: async (A) => {
      if (A.flag('beach')) return;
      A.setFlag('beach');
      await A.say('바닷바람이 분다.\f모래사장에 웬 전화박스가 늘어서 있다…');
    }
  };
  const companion = (G) => (G.kid === 'jou' ? 'taichi' : 'jou');
  async function shellmonTalk(A) {
    const G = A.G, n = A.nm('shellmon');
    await A.say('바다 쪽에서 땅이 울린다…!');
    const s = A.sprite('shellmon');
    const pic = A.showPics([{ img: s, x: 80 - s.width / 2, y: 70 - s.height }]);
    await A.say(`${n}: 여기는 내 바다다!\n인간 따위가 발을 들이다니!`);
    A.close(pic);
    const foe = A.makeMon('shellmon', 9);
    const r = await A.battle({ kind: 'boss', foe, intro: `${n}${A.josa(n, '이/가')} 덤벼들었다!` });
    if (r !== 'win') return;
    A.setFlag('shellmon');
    await A.say(`${n}${A.josa(n, '은/는')} 바닷속으로 도망쳐 버렸다!`);
    const cn = root.DigiField.KIDS[companion(G)].name;
    await A.say(`???: 어이~! 괜찮아?`);
    await A.say(`${cn}: 전화박스에 숨어 있었는데…\n대단하다, ${A.kidName()}!`);
    await A.say(`${n}${A.josa(n, '이/가')} 사라진 물가에서 무언가가 빛나고 있다…`);
    await A.flash(1);
    A.crest('성실');
    await A.say(`성실의 문장을 손에 넣었다!`);
    await A.say(`${cn}: 문장…? 너희 디지몬을 더 강하게 해 주는 걸지도 몰라.\f${cn}: 다른 아이들도 이 섬 어딘가에 있을 거야. 같이 찾아보자!`);
    await A.say('(1부의 다음 이야기는 준비 중입니다)');
  }
  async function companionTalk(A) {
    const cn = root.DigiField.KIDS[companion(A.G)].name;
    await A.say(`${cn}: 이 앞은 아직 길이 막혀 있어.\f(다음 이야기는 준비 중입니다)`);
  }

  const START = { map: 'camp', x: 6, y: 7, dir: 'up' };

  async function opening(A) {
    const gen = A.peopleSprite('gennai');
    const pic = A.showPics([{ img: gen, x: 80 - gen.width / 2, y: 84 - gen.height }]);
    await A.fadeIn();
    await A.say('…들리느냐?');
    await A.say('나는 디지털 월드에 사는\n흰수염 도사라고 한다.');
    await A.say('디지털 월드는 컴퓨터 네트워크 속에 있는 또 하나의 세계.\f그곳에 사는 것이 바로 디지몬이다.');
    await A.say('지금 디지털 월드는 어둠의 힘에 뒤덮이려 하고 있다…\f이 세계를 구할 수 있는 것은\n선택받은 아이들뿐.');
    await A.say('자, 너는 누구지?');
    A.close(pic);
    const kid = await A.pickKid(ORDER, (k) => { const name = root.DigiField.KIDS[k].name; return A.ask(`${name}${A.josa(name, '이/가')} 맞느냐?`); });
    A.G = A.newState(kid);
    const name = A.kidName();
    const pic2 = A.showPics([{ img: gen, x: 80 - gen.width / 2, y: 84 - gen.height }]);
    await A.say(`그래, ${name}.\f너와 함께할 디지몬이 저 너머에서 기다리고 있다.`);
    await A.say('자, 가거라!\n디지털 월드가 너를 부르고 있다!');
    A.close(pic2);
    await A.fadeOut('#f8f8f8');
  }

  root.DigiStory = { START, maps, items, dexOrder, CRESTS, ORDER, PARTNER, BABY, opening };
})(typeof window !== 'undefined' ? window : globalThis);
