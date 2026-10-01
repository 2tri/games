"""GBC판 이야기·지도 (웹판 story.js 를 옮긴 것). 글은 {kid}·{baby} 같은 변수와 {이/가} 같은 조사를 쓴다."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from dsl import *

KEY = {'.': 'grass', ',': 'tall', 'T': 'tree', ':': 'path', '*': 'flower', 's': 'sand', '~': 'sea', 'w': 'shore',
       'D': 'dtree', 'd': 'dgrass', 'S': 'sign', 'F': 'fire', 'c': 'crib', 'e': 'egg'}
CRESTS = ['용기', '우정', '사랑', '지식', '순수', '성실', '희망', '빛']
KIDS = ['taichi', 'yamato', 'takeru', 'hikari']          # 고를 수 있는 주인공 4명 (2026-10-01 사용자 결정)
COMP = ('yamato', 'taichi')                                 # 동행: 매튜, 주인공이 매튜면 신태일
PARTNER = {'taichi': 'agumon', 'yamato': 'gabumon', 'takeru': 'patamon', 'hikari': 'salamon'}
BABY = {'taichi': 'koromon', 'yamato': 'tsunomon', 'takeru': 'tokomon', 'hikari': 'nyaromon'}
EGGS = ['koromon', 'tsunomon', 'pyocomon', 'mochimon', 'tanemon', 'bukamon', 'tokomon', 'nyaromon']
ITEMS = [('회복 디스크', 20, '디지몬의 체력을 20 회복한다'), ('고급 회복 디스크', 50, '디지몬의 체력을 50 회복한다')]
START = ('house2f', 3, 3, 'down')

MAPS = {}
# 지도마다 배경 음악 (tools/midi2gb.py 곡 이름)
MAP_SONG = {'house2f': 'town', 'house1f': 'town', 'town': 'town', 'camp': 'town', 'forest': 'field', 'route1': 'field',
            'village': 'village', 'beach': 'field'}

# ── 오프닝 (흰수염 도사) ──
OPENING = [
    Pic(SP_NONE), FadeIn(),
    Say('…들리느냐?'),
    Say('나는 디지털 월드에 사는\n흰수염 도사라고 한다.'),
    Say('디지털 월드는 컴퓨터 네트워크 속에 있는 또 하나의 세계.\f그곳에 사는 것이 바로 디지몬이다.'),
    Say('지금 디지털 월드는 어둠의 힘에 뒤덮이려 하고 있다…\f이 세계를 구할 수 있는 것은\n선택받은 아이들뿐.'),
    Say('자, 너는 누구지?'), Close(),
    PickKid(),
    Pic(SP_NONE),
    Say('그래, {kid}.\f너와 함께할 디지몬이 저 너머에서 기다리고 있다.'),
    Say('자, 가거라!\n디지털 월드가 너를 부르고 있다!'), Close(),
    FadeOut(white=True), PicOff(),
    Warp('house2f', 3, 3, 'down'),
]

# ── 이미지 AI 배경 조각으로 만든 지도 (tools/assets.py) ──
KEYH = {'W': 'h_wall', 'b': 'h_wallb', '.': 'h_floor'}
KEYT = {'F': 't_forest', '.': 't_grass', ':': 't_path', '*': 't_flowers', 'g': 't_garden'}
KEYC = {'F': 'c_forest', '.': 'c_grass', ':': 'c_path', 'd': 'c_dirt'}
KEYV = {'W': 'v_sea', '.': 'v_grass', ':': 'v_path', 'c': 'v_crib'}
KEYR = {'J': 'r_canopy', '.': 'r_grass', ':': 'r_path', ',': 'r_tall', '*': 'r_flowers'}                 # 파일섬 숲·길 (A6 타일)
KEYB = {'J': 'r_canopy', ',': 'r_tall2', 's': 'r_sand', '~': 'r_sea', 'w': 'r_shore', '.': 'r_grass'}  # 해변

# ── 주인공 집 2층 (내 방) ──
MAPS['house2f'] = Map('내 방', [
    'WWWWWWWW',
    'bbbbbbbb',
    '........',
    '........',
    '........',
    '........',
    '........'], KEYH, 'h_void',
    objs=[('h_desk', 1, 0), ('h_window', 4, 0), ('h_plant', 0, 1), ('h_bed', 6, 1), ('h_console', 0, 4), ('h_tv', 1, 4), ('h_stairs', 7, 6)],
    warps=[Warp_(7, 6, 'house1f', 9, 1, 'down')],
    signs=[Sign(x, 2, [Say('컴퓨터를 켰다.\f메일이 1통 와 있다.\n「캠프에서 만나자! —{comp}」')]) for x in (1, 2, 3)] +
          [Sign(x, 4, [Say('게임기다.\f…지금은 놀 때가 아니야!\n오늘은 캠프 가는 날이잖아.')]) for x in (0, 1, 2)] +
          [Sign(x, 1, [Say('창밖으로 우리 동네가 보인다.\f하늘이 이상하게 반짝이고 있다…')]) for x in (4, 5)],
    on_enter=[IfFlag('start', 'e'), SetFlag('start'),
              Say('여름 방학 첫날 아침.\f오늘은 기다리던 여름 캠프 날이다!'),
              Say('아래층으로 내려가 보자.\n(오른쪽 아래 계단)'), Label('e')])

# ── 주인공 집 1층 ──
MAPS['house1f'] = Map('우리 집', [
    'WWWWWWWWWW',
    'bbbbbbbbbb',
    '..........',
    '..........',
    '..........',
    '..........',
    '..........',
    '..........'], KEYH, 'h_void',
    objs=[('h_plant2', 0, 1), ('h_tv2', 2, 1), ('h_stairs', 9, 1), ('h_shelf', 7, 2), ('h_kitchen', 8, 2),
          ('h_table', 4, 4), ('h_stool', 3, 5), ('h_stool', 6, 5), ('h_mat', 4, 7)],
    warps=[Warp_(9, 1, 'house2f', 7, 6, 'left'), Warp_(4, 7, 'town', 3, 7, 'down'), Warp_(5, 7, 'town', 3, 7, 'down')],
    signs=[Sign(x, y, [Say('식탁 위에 엄마의 쪽지가 있다.\f「캠프 잘 다녀오렴!\n버스는 동네 위쪽 정류장에서 출발한대.」'), SetFlag('momnote')])
           for (x, y) in ((4, 4), (5, 4), (4, 5), (5, 5))] +
          [Sign(x, 2, [Say('텔레비전에서 뉴스가 나온다.\f「올여름, 세계 곳곳에서 이상한 날씨가 이어지고 있습니다…」')]) for x in (2, 3, 4)] +
          [Sign(7, y, [Say('책이 잔뜩 꽂혀 있다.')]) for y in (2, 3, 4)] +
          [Sign(8, y, [Say('부엌이다.\n맛있는 냄새가 난다.')]) for y in (2, 3, 4)])

# ── 우리 동네 ──
BUS = [Ask('캠프 버스를 타고 출발할까?'), IfNo('no'),
       Close(), FadeOut(), Say('버스를 타고 여름 캠프장으로 향했다…'), Close(), Wait(30),
       Warp('camp', 7, 12, 'up'), End(),
       Label('no'), Say('…조금 더 둘러보자.')]
MAPS['town'] = Map('우리 동네', [
    'FFFFFFF::FFFFFFF',
    'F......::......F',
    'F......::......F',
    'F......::......F',
    'F......::......F',
    'F*.....::......F',
    'F......::......F',
    'F..:::::::::...F',
    'F......::......F',
    'F......::......F',
    'F......::......F',
    'F.....::::::...F',
    'F*.*...::....*.F',
    'FFFFFFFFFFFFFFFF'], KEYT, 't_forest', open=[(7, -9, 8, -1, 't_path')],
    objs=[('t_house', 2, 2), ('t_house2', 10, 3), ('t_shop', 10, 8), ('t_sign', 6, 2), ('t_sign2', 9, 6),
          ('t_tree', 14, 1), ('t_tree', 1, 8), ('t_tree', 5, 9), ('t_flowerbed', 2, 11), ('t_tree', 14, 5)],
    warps=[Warp_(3, 6, 'house1f', 4, 7, 'up')],
    signs=[Sign(6, 2, [Say('↑ 캠프 버스 정류장')]), Sign(9, 6, [Say('여기는 우리 동네.\f← 우리 집   → 편의점')]),
           Sign(11, 4, [Say('이웃집이다.\f아무도 없는 것 같다.')]), Sign(11, 10, [Say('편의점이다.\f「오늘은 쉽니다」라고 쓰여 있다.')])],
    triggers=[Trigger(7, 0, 2, 1, BUS)])

# ── 여름 캠프장 ──
KID_LINE = {
    'taichi': '한여름에 눈이라니… 축구공이 다 젖겠는걸.',
    'yamato': '…리키는 어디 갔지? 너무 멀리 가지 말라고 했는데.',
    'takeru': '와, 눈이다! 여름인데 눈이 와!',
    'hikari': '여름인데 눈이 오다니… 무슨 일이 생기려나.',
}
KID_NAME = {'taichi': '신태일', 'yamato': '매튜', 'takeru': '리키', 'hikari': '신나리'}
CAMP_SPOTS = {'taichi': (7, 9, 'right'), 'yamato': (10, 9, 'left'), 'takeru': (9, 11, 'up'), 'hikari': (9, 8, 'down')}

AURORA = [
    Say('하늘에 오로라가 펼쳐졌다…!'), Close(), Flash(2),
    Say('하늘에서 빛나는 것들이 떨어졌다!'),
    Say('{kid}{은/는} 작은 기계를 주웠다.\f디지바이스를 손에 넣었다!'), SetFlag('digivice'),
    Say('디지바이스가 빛나기 시작했다…!\f몸이 어딘가로 빨려 들어간다!'), Close(),
    Flash(3), FadeOut(white=True), Wait(30),
    Warp('forest', 5, 10, 'up'),
]
MAPS['camp'] = Map('여름 캠프장', [
    'FFFFFFFFFFFFFFFF',
    'F..............F',
    'F..............F',
    'F..............F',
    'F..............F',
    'F..............F',
    'F............:.F',
    'F..:::::::::::.F',
    'F......:.......F',
    'F......:.......F',
    'F......:.......F',
    'F......:.......F',
    'F......:.......F',
    'FFFFFFFFFFFFFFFF'], KEYC, 'c_forest',
    objs=[('c_shrine', 12, 1), ('c_lodge', 2, 2), ('c_office', 7, 3), ('c_fire', 8, 9), ('c_table', 2, 9), ('c_table', 2, 11),
          ('c_tent1', 12, 9), ('c_tent2', 14, 9), ('c_tent3', 13, 11), ('c_tent4', 11, 12), ('c_tent5', 14, 12), ('c_stump', 11, 10),
          ('c_sign', 4, 12), ('c_tree', 1, 7), ('c_tree', 6, 1), ('c_tree', 11, 1)],
    npcs=[NPC(x, y, k, d, [Say(KID_NAME[k] + ': ' + KID_LINE[k])], hide_kid=k, hide_if='aurora') for k, (x, y, d) in CAMP_SPOTS.items()],
    signs=[Sign(3, 6, [Say('캠프 산장.\f지금은 모두 밖에 나와 있다.')]), Sign(8, 4, [Say('캠프 관리 사무소.\f「오늘의 일정: 캠프파이어」')]),
           Sign(4, 12, [Say('여름 캠프장\n― 버스 정류장 ―')]), Sign(5, 12, [Say('여름 캠프장\n― 버스 정류장 ―')])],
    triggers=[Trigger(13, 3, 1, 1, AURORA, once='aurora')],
    on_enter=[IfFlag('campIntro', 'e'), SetFlag('campIntro'),
              Say('여름 캠프장에 도착했다.\f그런데 한여름인데도 갑자기 눈이 내리기 시작했다…'),
              Say('모두 언덕 위 사당 쪽이 이상하다며 웅성거리고 있다.\n(오른쪽 위 사당으로 가 보자)'), Label('e')])

# ── 파일섬 숲 ──
KUWAGA = [
    Say('부우우웅…!\f거대한 날갯소리가 다가온다!'), Close(), Flash(1),
    Pic('kuwagamon'),
    Say('쿠가몬이 덮쳐 왔다!'),
    Say('{partner}: {kid}에게는 손대지 마!'), Close(), PicOff(),
    Evolve(SP_ROOKIE, 5),
    Pic('kuwagamon'),
    Say('{rookie}의 {f0}!'), Close(), Shake(8), Flash(1),
    Say('쿠가몬은 숲 너머로 날아가 버렸다…'), Close(), PicOff(),
    Say('{rookie}: 휴우… 다행이다.\f{rookie}: 이 섬 어딘가에 디지몬들이 사는 마을이 있어. 가 보자!'),
]
MAPS['forest'] = Map('파일섬 숲', [
    'JJJJJ:::JJJJ',
    'J....::....J',
    'J.,,.::.,,.J',
    'J.,,.::.,,.J',
    'J....::....J',
    'J....::....J',
    'J....::....J',
    'J,,..::..,,J',
    'J,,..::..,,J',
    'J....::....J',
    'J....::....J',
    'JJJJJJJJJJJJ'], KEYR, 'r_canopy', open=[(5, -9, 7, -1, 'r_path')],
    objs=[('r_jungle', 1, 4), ('r_bush', 9, 4), ('r_palm', 2, 9), ('r_bush2', 8, 9), ('r_jungle', 3, 0), ('r_tree', 8, 0), ('r_rock', 1, 1)],
    warps=edge([5, 6, 7], -1, 'route1', 5, 17),
    triggers=[Trigger(2, 3, 9, 1, KUWAGA, once='kuwaga', need='partner')],
    on_enter=[IfFlag('partner', 'e'), SetFlag('partner'), SetHeal('forest', 5, 9, 'up'),
              Say('…여기는 어디지?\f처음 보는 정글 한가운데에 떨어져 있었다.'), Close(),
              Pic(SP_BABY),
              Say('???: 어이~! 여기야, 여기!'),
              Say('{baby}: 기다리고 있었어, {kid}!\f나는 {baby}! 디지몬이야!'),
              Say('{baby}: 너를 줄곧 기다렸어.\n이제부터 내가 함께할게!'),
              GiveMon(SP_BABY, 3),
              Say('{baby}{이/가} 동료가 되었다!'), Close(), PicOff(),
              Say('START 버튼으로 메뉴를 열 수 있다.\f우선 숲을 빠져나가 보자. (위쪽)'), Label('e')])

# ── 1번 길 ──
MAPS['route1'] = Map('1번 길', [
    'JJJJ::JJJJJJ',
    'J...::.....J',
    'J.,,::..,,,J',
    'J.,,::..,,,J',
    'J...:::....J',
    'J....::....J',
    'J,,,.::.**.J',
    'J,,,.::....J',
    'J,,,.::,,,.J',
    'J....::,,,.J',
    'J....::,,,.J',
    'J....::....J',
    'J.**.::.,,,J',
    'J....::.,,,J',
    'J,,,.::.,,,J',
    'J,,,.::....J',
    'J....:::...J',
    'JJJJJ:::JJJJ'], KEYR, 'r_canopy', open=[(4, -9, 5, -1, 'r_path'), (5, 18, 7, 29, 'r_path')],
    objs=[('r_tree', 7, 0), ('r_tree', 9, 4), ('r_sign', 2, 10), ('r_tree', 1, 4), ('r_rock', 8, 10), ('r_tree2', 9, 15), ('r_bush', 1, 12)],
    signs=[Sign(2, 10, [Say('1번 길\n↑ 행복의 마을  ↓ 파일섬 숲')])],
    warps=edge([4, 5], -1, 'village', 7, 12) + edge([5, 6, 7], 18, 'forest', 5, 0),
    enc=(26, [('picodevimon', 2, 4, 20), ('tentomon', 2, 4, 15), ('palmon', 2, 4, 15), ('elecmon', 3, 4, 10), ('koromon', 2, 3, 25), ('tsunomon', 2, 3, 15)]),
    on_enter=[IfFlag('route1', 'e'), SetFlag('route1'),
              Say('풀숲에는 야생 디지몬이 숨어 있다.\f쓰러뜨린 디지몬이 동료가 되고 싶어 할 때도 있다!'), Label('e')])

# ── 행복의 마을 ──
ELECMON = [
    IfFlag('elecmon', 'heal'), SetFlag('elecmon'),
    Say('에렉몬: 여기는 행복의 마을. 디지몬이 디지타마에서 태어나는 곳이야.\f나는 이 마을을 지키는 에렉몬!'),
    Say('에렉몬: …뭐? 인간이 디지털 월드에 왔다고?\n게다가 디지몬과 함께?'),
    Say('에렉몬: 좋아, 믿어 줄게.\f지쳤으면 언제든 나한테 와. 디지몬들을 쉬게 해 줄게.'),
    GiveItem('회복 디스크', 3), Say('회복 디스크를 3개 받았다!'),
    Say('에렉몬: 그리고 이건 막 생겨난 디지타마야.\n데려가서 따뜻하게 해 줘.'),
    GiveEgg(), Say('디지타마를 받았다!'),
    Say('에렉몬: 디지몬에게는 속성이 있어.\f백신은 바이러스에 강하고,\n바이러스는 데이터에 강하고,\f데이터는 백신에 강해.\n잘 기억해 둬!'),
    Label('heal'),
    Ask('에렉몬: 디지몬들을 쉬게 해 줄까?'), IfNo('no'),
    Close(), FadeOut(), Heal(), SetHeal('village', 7, 7, 'up'), Wait(20), FadeIn(),
    Say('에렉몬: 다들 기운을 되찾았어!\n또 와!'), End(),
    Label('no'), Say('에렉몬: 조심해서 다녀!'),
]
MAPS['village'] = Map('행복의 마을', [
    'WWWWWWWWWWWWWWWW',
    'W..............W',
    'W..............W',
    'W..............W',
    'W..............W',
    'W..............W',
    'W.....::::::::::',
    'W.....::.......:',
    'W......:.......:',
    'W......:..c....W',
    'W.c....:.......W',
    'W......:.......W',
    'W.c....:....c..W',
    'WWWWWWW::WWWWWWW'], KEYV, 'v_sea', open=[(7, 14, 8, 29, 'v_path'), (16, 6, 29, 8, 'v_path')],
    objs=[('v_center', 5, 1), ('v_shop', 11, 2), ('v_egg1', 1, 2), ('v_tree', 3, 4), ('v_block2', 3, 8), ('v_egg2', 9, 10),
          ('v_pond', 12, 9), ('v_tree', 10, 7)],
    warps=edge([7, 8], 14, 'route1', 4, 0) + edgeV(16, [6, 7, 8], 'beach', 0, 6),
    npcs=[NPC(6, 6, 'elecmon', 'down', ELECMON),
          NPC(2, 6, 'blob:botamon', 'down', [Say('깜몬: 뽀글… 뽀글…')]),
          NPC(11, 11, 'blob:punimon', 'down', [Say('푸니몬: 푸니~ 푸니~')]),
          NPC(6, 10, 'blob:koromon', 'down', [Say('코로몬: 이 마을에서는 디지몬이 디지타마에서 태어나!\f다시 태어날 때도 여기로 돌아온대.')])],
    signs=[Sign(12, 4, [Say('디지몬 상점.\f「곧 문을 엽니다」라고 쓰여 있다.')]), Sign(7, 5, [Say('디지몬 회복 센터.\f에렉몬에게 말을 걸면 디지몬을 쉬게 해 준다.')])],
    on_enter=[IfFlag('village', 'e'), SetFlag('village'),
              Say('알록달록한 블록과 요람이 가득한 마을이다.\f아기 디지몬들이 잠들어 있다.'), Label('e')])

# ── 해변 ──
SHELLMON = [
    Say('바다 쪽에서 땅이 울린다…!'), Close(), Shake(10),
    Pic('shellmon'),
    Say('쉘몬: 여기는 내 바다다!\n인간 따위가 발을 들이다니!'), Close(), PicOff(),
    Battle('shellmon', 9, 'boss'),
    SetFlag('shellmon'),
    Say('쉘몬은 바닷속으로 도망쳐 버렸다!'),
    Say('???: 어이~! 괜찮아?'),
    Say('{comp}: 전화박스에 숨어 있었는데…\n대단하다, {kid}!'),
    Say('쉘몬이 사라진 물가에서 무언가가 빛나고 있다…'), Close(), Flash(1),
    Crest('성실'), Say('성실의 문장을 손에 넣었다!'),
    Say('{comp}: 문장…? 너희 디지몬을 더 강하게 해 주는 걸지도 몰라.\f{comp}: 다른 아이들도 이 섬 어딘가에 있을 거야. 같이 찾아보자!'),
    Say('(1부의 다음 이야기는 준비 중입니다)'),
]
MAPS['beach'] = Map('파일섬 해변', [
    'JJJJJJsssJJ~~~~',
    'J,,,ssssssw~~~~',
    'J,,,ssssssw~~~~',
    'J,,ssssssssw~~~',
    'Jssssssssssw~~~',
    'Jssssssssssw~~~',
    'ssssssssssssw~~',
    'ssssssssssssw~~',
    'ssssssssssssw~~',
    'J,,,ssssssssw~~',
    'J,,,,ssssssw~~~',
    'JJJJJJJJJJJw~~~'], KEYB, 'r_canopy', open=[(-9, 6, -1, 8, 'r_sand')], border_fn=lambda x, y: 'r_sea' if x >= 11 else 'r_canopy',
    objs=[('r_palm', 1, 4), ('r_palm2', 9, 8), ('r_booth', 4, 3), ('r_booth', 5, 3), ('r_booth', 6, 3)],
    warps=edgeV(-1, [6, 7, 8], 'village', 15, 6),
    enc=(26, [('gomamon', 5, 7, 25), ('piyomon', 5, 7, 20), ('bukamon', 4, 6, 20), ('pyocomon', 4, 6, 15), ('tanemon', 4, 6, 10)]),
    npcs=[NPC(7, 0, 'blob:shellmon', 'down', SHELLMON, hide_if='shellmon', fixed=True),
          NPC(7, 0, 'COMP', 'down', [Say('{comp}: 이 앞은 아직 길이 막혀 있어.\f(다음 이야기는 준비 중입니다)')], show_if='shellmon')],
    signs=[Sign(4, 4, [Say('전화기를 들어 보았다…\f「…오늘의 날씨는…」\n알 수 없는 안내 방송만 흘러나온다.')]),
           Sign(5, 4, [Say('전화기를 들어 보았다…\f「뚜― 뚜―」\n아무 데도 이어지지 않는다.')]),
           Sign(6, 4, [Say('해변 한가운데에 전화박스가 줄지어 서 있다.\f…왜 이런 곳에?')])],
    triggers=[Trigger(6, 1, 3, 1, SHELLMON, unless='shellmon')],
    on_enter=[IfFlag('beach', 'e'), SetFlag('beach'),
              Say('바닷바람이 분다.\f모래사장에 웬 전화박스가 늘어서 있다…'), Label('e')])
