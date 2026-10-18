#pragma bank 8
#include <gb/gb.h>
#include "data.h"
#include "engine.h"
#include "game.h"
#include "story.h"
void step_0(void) BANKED {
  chapterTitle("제1장", "샤이어를 떠나다");
  { static const char * const L0[] = { "빌보가 생일잔치에서 감쪽같이 사라진 뒤, 그의 반지는 프로도의 손에 남았다.", "오랜만에 찾아온 간달프가 난롯불에 반지를 던져 넣었다. 식은 반지 표면에 불꽃 같은 글자가 떠올랐다.", "간달프: 이건 보통 반지가 아닐세. 어둠의 군주가 온 힘을 다해 찾고 있는 바로 그 반지야.", "간달프: 샤이어에 오래 둘 수 없네. 브리의 「달리는 조랑말」로 가게. 거기서 나를 기다리게.", "창밖에서 엿듣던 샘이 붙잡혔다. 벌로 샘도 길동무가 되었다." }; story("호빗골 · 골목쟁이집", SP_GANDALF_FRONT, L0, 5); }
  S.step = 1;
  save();
}

void step_1(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "샘: 프로도 나리, 농부 매곳네 밭을 가로지르면 훨씬 빨라요.", "프로도: 그 집 개들은 어릴 때 나를 쫓아다니던 녀석들인데...", "울타리 너머에서 사나운 짖는 소리가 들려왔다!" }; story("매곳 농장 지름길", SP_FRODOSAM_FRONT, L0, 3); }
  r = battle(FO_DOG, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "농부 매곳의 고함 소리가 들리기 전에 서둘러 밭을 빠져나왔다.", "밭고랑에서 튀어나온 메리와 피핀이 합류했다. 넷은 나루터를 향해 달렸다." }; story("매곳 농장 지름길", SP_FRODOSAM_FRONT, L1, 2); }
  S.step = 2;
  save();
}

void step_2(void) BANKED {
  uint8_t c, c2, r;
  { static const char * const L0[] = { "길 저편에서 말발굽 소리가 다가온다. 검은 옷의 기사가 킁킁 냄새를 맡고 있다.", "샘: 나리, 길에서 벗어나요! 어서요!" }; story("숲길", SP_RIDER, L0, 2); }
  { static const char * const L1[] = { "나무뿌리 밑에 숨는다", "맞선다" }; c = choose("어떻게 할까?", L1, 2, NOCANCEL); }
  if (c == 0) {
  say("모두 길가 나무뿌리 아래로 몸을 숨겼다. 기사가 바로 위에서 멈춰 섰다.");
  say("주머니 속 반지가 손가락을 부르는 것만 같다...");
  { static const char * const L2[] = { "낀다", "참는다" }; c2 = choose("반지를...", L2, 2, NOCANCEL); }
  if (c2 == 0) {
  S.shadow++;
  say("반지를 끼려는 순간 기사가 고개를 돌렸다. 겨우 지나갔지만 마음 한구석이 서늘하다. (그림자 +1)");
} else say("샘이 프로도의 손을 꼭 붙잡았다. 기사는 아무것도 찾지 못하고 떠났다.");
} else {
  r = battle(FO_RIDER, 1, 0);
  if (r == R_LOSE) {
  { static const char * const L3[] = { "정신을 차려 보니 샘이 프로도를 끌고 나무뿌리 밑에 숨어 있었다.", "샘: 저런 걸 이길 순 없어요, 나리. 지금은 피하는 게 상책이에요." }; story("숲길", 255, L3, 2); }
  S.hp = MAX(1, (((stat(ST_HP)) + 2 / 2) / 2));
} else say("기사가 비명을 지르며 물러났다! 하지만 다시 올 것이다.");
}
  { static const char * const L4[] = { "간신히 나룻배에 올라 강을 건넜다. 건너편 둑에서 검은 기사가 멈춰 섰다.", "프로도: 큰길은 위험해. 묵은숲을 지나가자." }; story("노루말 나루", SP_FRODOSAM_FRONT, L4, 2); }
  S.step = 3;
  save();
}

void step_3(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "묵은숲은 나무들이 서로 수군대는 것 같은 곳이었다. 길은 자꾸만 강가로 이어졌다.", "늙은 버드나무 아래에서 졸음이 쏟아진다. 줄기 틈이 입처럼 벌어졌다!" }; story("묵은숲", SP_WILLOW, L0, 2); }
  say("(누군가 올 때까지 버텨야 한다!)"); r = battle(FO_WILLOW, 0, 4); if (r == R_RESCUE) { say("어디선가 흥겨운 노랫소리가 들려온다..."); say("파란 웃옷에 노란 장화를 신은 사람이 버드나무를 꾸짖었다!"); rescue_end(); r = R_WIN; }
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "그는 톰 봄바딜. 숲의 가장 오래된 주인이었다.", "톰이 노래 몇 소절을 부르자 버드나무가 스르르 뿌리를 거두었다.", "그날 밤 톰과 골드베리의 집에서 푹 쉬었다. 체력이 모두 회복됐다!" }; story("톰 봄바딜의 집", SP_TOM_FRONT, L1, 3); }
  S.hp = stat(ST_HP);
  S.lembas = MAX(S.lembas, 3);
  S.step = 4;
  save();
}

void step_4(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "짙은 안개 속에 고대 왕들의 무덤이 늘어서 있다. 길을 잃고 말았다.", "차가운 손이 어깨를 붙잡았다. 금관을 쓴 해골이 속삭이는 노래를 부른다!" }; story("무덤 언덕", SP_WIGHT, L0, 2); }
  r = battle(FO_WIGHT, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "아침 햇살이 무덤 안으로 쏟아지자 악령은 비명을 지르며 흩어졌다.", "무덤 속에서 오래된 서쪽나라의 단검을 찾았다. 공격이 3 올랐다!", "이제 브리로 간다. 거기서 간달프를... 아니면 다른 누군가를 만나게 될 것이다." }; story("무덤 언덕", 255, L1, 3); }
  S.dagger = 1;
  S.step = 5;
  save();
}

void step_5(void) BANKED {
  uint8_t c;
  chapterTitle("제2장", "브리와 바람마루");
  { static const char * const L0[] = { "사람들로 북적이는 여관. 간달프는 오지 않았다. 여관 주인 버터버는 간달프가 맡긴 편지를 깜빡 잊고 있었다며 뒤늦게 내밀었다.", "피핀이 떠들다 「골목쟁이」라는 이름을 꺼냈다. 말리려고 일어서던 프로도가 넘어지며... 반지가 손가락에 끼워졌다!", "프로도의 모습이 사라졌다. 어딘가에서 불타는 눈이 이쪽을 보는 것 같다. (그림자 +1)" }; story("브리 · 「달리는 조랑말」", SP_FRODOSAM_FRONT, L0, 3); }
  S.shadow++;
  { static const char * const L1[] = { "반지를 빼자마자 누군가 프로도의 팔을 낚아챘다. 두건을 쓴 순찰자, 사람들은 그를 「성큼걸이」라 불렀다.", "성큼걸이: 조심성이 없군. 그 물건은 장난감이 아니오. 놈들이 이미 브리에 와 있소." }; story("브리 · 구석 자리", SP_ARAGORN_FRONT, L1, 2); }
  { static const char * const L2[] = { "믿는다", "의심한다" }; c = choose("성큼걸이를...", L2, 2, NOCANCEL); }
  if (c == 1) say("샘이 의자를 들고 막아섰다. 성큼걸이가 조용히 부러진 칼자루를 보여 주었다. 간달프의 편지에 적힌 그 증표였다."); else say("프로도는 그의 눈을 오래 바라보았다. 거칠어 보여도 나쁜 사람의 눈은 아니었다.");
  { static const char * const L3[] = { "밤이 깊자 검은 기사들이 여관 방에 들이닥쳐 빈 침대를 마구 내리쳤다. 호빗들은 성큼걸이가 마련한 다른 방에 숨어 있었다.", "성큼걸이: 날이 밝으면 큰길을 버리고 들판을 가로지른다. 나를 따르시오.", "아라곤(성큼걸이)이 동료가 되었다! 전투 중 「동료」로 교대할 수 있다." }; story("브리 · 한밤중", SP_RIDER, L3, 3); }
  addMember(HE_ARAGORN, 7);
  S.step = 6;
  save();
}

void step_6(void) BANKED {
  { static const char * const L0[] = { "모기가 구름처럼 들끓는 늪을 며칠이나 헤맸다. 샘은 투덜대며 쉴 새 없이 목덜미를 때렸다.", "피핀: 저 녀석들은 호빗이 없을 땐 뭘 먹고 사는 걸까요?", "모두 지치고 가려워 체력이 조금 줄었다." }; story("미지워터 늪", SP_FRODOSAM_FRONT, L0, 3); }
  S.hp = MAX(1, S.hp - 4);
  S.step = 7;
  save();
}

void step_7(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "옛 봉화대가 무너진 언덕 꼭대기. 아라곤이 정찰을 나간 사이 호빗들이 불을 피웠다.", "아래쪽 어둠 속에서 검은 형체 다섯이 천천히 올라온다!", "샘: 나리 뒤에 붙으세요! 횃불, 횃불을 들어요!" }; story("바람마루", SP_ARAGORN_FRONT, L0, 3); }
  if (S.hero != HE_FRODOSAM && has(HE_FRODOSAM)) swapTo(HE_FRODOSAM);
  r = battle(FO_RIDERS5, 0, 0);
  { const char *L1[4]; L1[0] = "우두머리 기사가 칼을 높이 들었다. 겁에 질린 프로도의 손이 저도 모르게 반지를 향했다."; L1[1] = "반지를 낀 순간 세상이 잿빛으로 바뀌고, 왕관을 쓴 창백한 형상이 프로도의 어깨에 칼을 꽂았다!"; L1[2] = (r == R_WIN ? "불길 속에서 기사들이 물러났다. 하지만 상처는 얼음처럼 차갑게 번져 간다." : "아라곤이 양손에 횃불을 들고 뛰어들어 기사들을 쫓아냈다."); L1[3] = "프로도가 모르굴 칼에 다쳤다. 깊은골에 닿기 전까지 최대 체력이 줄어든다. (그림자 +1)"; story("바람마루", SP_RIDER, L1, 4); }
  S.shadow++;
  S.wound = 1;
  if (r == R_LOSE) {
  S.hp = MAX(S.hp, (((stat(ST_HP)) + 3 / 2) / 3));
  party_floor_third();
}
  frodo_cap_hp();
  S.step = 8;
  save();
}

void step_8(void) BANKED {
  { static const char * const L0[] = { "숲속 빈터에 거대한 트롤 셋이 돌이 된 채 서 있었다.", "샘: 이거 빌보 나리 이야기에 나오는 그 트롤들이잖아요! 정말 있었네!", "아라곤이 「아셀라스」 풀을 찾아와 프로도의 상처를 달랬다. 열이 조금 내렸다." }; story("트롤숲", 255, L0, 3); }
  frodo_full_hp();
  S.step = 9;
  save();
}

void step_9(void) BANKED {
  uint8_t c;
  { static const char * const L0[] = { "빛나는 요정 아르웬이 말을 타고 나타나 프로도를 안장에 태웠다.", "검은 기사 아홉이 바짝 뒤쫓는다. 여울 건너편에 닿자 그녀가 몸을 돌렸다." }; story("브루이넨 여울", SP_ARWEN_FRONT, L0, 2); }
  { static const char * const L1[] = { "칼을 뽑아 든다", "반지를 움켜쥔다" }; c = choose("프로도는...", L1, 2, NOCANCEL); }
  if (c == 1) {
  S.shadow++;
  say("반지가 속삭인다... 하지만 끝내 끼지 않았다. (그림자 +1)");
} else say("떨리는 손으로 작은 칼을 뽑았다. 「돌아가라! 반지는 너희 것이 아니다!」");
  { static const char * const L2[] = { "강물이 굉음과 함께 솟구쳤다. 흰 말 떼 같은 물결이 기사들을 집어삼키고 휩쓸어 갔다.", "프로도는 정신을 잃었다..." }; story("브루이넨 여울", 255, L2, 2); }
  S.step = 10;
  save();
}

void step_10(void) BANKED {
  { static const char * const L0[] = { "눈을 떠 보니 부드러운 침대 위였다. 곁에 간달프가 앉아 있었다.", "간달프: 엘론드가 자네 어깨에서 칼끝 조각을 빼냈다네. 조금만 늦었어도 위험했어.", "상처가 나았다! 모두의 체력이 회복됐다." }; story("깊은골", SP_GANDALF_FRONT, L0, 3); }
  S.wound = 0;
  healAll();
  S.step = 11;
  save();
}

void step_11(void) BANKED {
  chapterTitle("제3장", "깊은골의 회의");
  { static const char * const L0[] = { "폭포 소리가 들리는 요정들의 골짜기. 늙은 빌보가 반갑게 프로도를 맞았다.", "빌보: 이걸 가져가거라. 내 작은 칼 「스팅」이란다. 오크가 다가오면 푸르게 빛나지.", "빌보는 은빛 쇠사슬 갑옷도 꺼냈다. 깃털처럼 가볍지만 어떤 칼도 뚫지 못하는 미스릴이었다.", "스팅과 미스릴 갑옷을 얻었다! 프로도·샘의 「지팡이 휘두르기」가 「스팅」으로 바뀌고 방어가 5 올랐다." }; story("깊은골", SP_BILBO_FRONT, L0, 4); }
  S.sting = 1;
  S.mithril = 1;
  S.step = 12;
  save();
}

void step_12(void) BANKED {
  { static const char * const L0[] = { "요정, 난쟁이, 사람이 한자리에 모였다. 엘론드가 말했다. 반지는 오직 그것이 만들어진 운명의 산의 불 속에서만 녹일 수 있다고.", "곤도르의 보로미르는 반지를 무기로 쓰자고 했고, 김리와 레골라스는 서로를 노려보며 언성을 높였다.", "다툼 속에서 프로도가 일어섰다. 「제가 가져가겠습니다. 길은 모르지만요.」", "샘이 뛰어나왔다. 「나리는 저 없이는 아무 데도 못 가요!」 메리와 피핀도 뒤따랐다.", "그렇게 아홉 명의 원정대가 꾸려졌다." }; story("깊은골 · 엘론드의 회의", SP_ELROND_FRONT, L0, 5); }
  addMember(HE_LEGOLAS, 10);
  addMember(HE_GIMLI, 10);
  addMember(HE_GANDALF, 13);
  say("레골라스, 김리, 간달프가 동료가 되었다! (보로미르·메리·피핀도 함께한다)");
  { static const char * const L1[] = { "길을 떠나기 전 두 달 동안 정찰대가 사방을 살피고 돌아왔다. 검은 기사들의 말은 강에서 모두 떠내려갔다고 한다.", "원정대가 길을 나서는 날, 요정들이 문 앞에 나와 조용히 배웅했다.", "가방을 다시 채웠다. 렘바스 5개, 약초 3개." }; story("깊은골", 255, L1, 3); }
  S.lembas = MAX(S.lembas, 5);
  S.herb = MAX(S.herb, 3);
  healAll();
  S.step = 13;
  save();
}

void step_13(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "남쪽으로 내려가던 길. 하늘 저편에서 검은 구름 같은 것이 빠르게 다가온다.", "아라곤: 크레바인이다! 던랜드의 까마귀 떼야. 사루만의 눈이 되어 우리를 찾고 있다!" }; story("홀린의 바위 언덕", SP_CREBAIN, L0, 2); }
  r = battle(FO_CREBAIN, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "간달프: 남쪽 길도 감시당하고 있군. 카라드라스를 넘어야겠네." }; story("홀린의 바위 언덕", SP_GANDALF_FRONT, L1, 1); }
  S.step = 14;
  save();
}

void step_14(void) BANKED {
  uint8_t c;
  { static const char * const L0[] = { "눈보라가 몰아치는 산길. 바람 속에서 누군가 주문을 외는 목소리가 들린다.", "레골라스: 저건 바람 소리가 아니오. 산 위에서 누군가 우리를 막고 있소!", "눈사태가 쏟아져 길이 막혔다. 모두 지쳐 체력이 줄었다.", "김리: 산 밑으로 가면 되지 않소! 내 사촌 발린이 다스리는 모리아로!", "간달프는 모리아라는 말에 얼굴이 어두워졌다. 「반지 지기가 정하게.」" }; story("카라드라스", SP_GANDALF_FRONT, L0, 5); }
  S.hp = MAX(1, S.hp - 8);
  party_hurt(8);
  { static const char * const L1[] = { "모리아로 간다", "로한 협곡으로 돌아간다" }; c = choose("프로도는...", L1, 2, NOCANCEL); }
  if (c == 1) say("간달프: 그 길은 사루만의 땅에 너무 가깝네... 그래도 결국 모리아밖에 없겠군.");
  say("원정대는 안개산맥 아래, 모리아로 향했다.");
  S.step = 15;
  save();
}

void step_15(void) BANKED {
  uint8_t c, r;
  chapterTitle("제4장", "모리아의 어둠");
  { static const char * const L0[] = { "절벽에 달빛이 비치자 은빛 선으로 된 문이 떠올랐다. 문 위에 요정 글자가 새겨져 있다.", "간달프가 온갖 주문을 외워 봤지만 문은 열리지 않았다. 한참 뒤 프로도가 말했다.", "프로도: 혹시 수수께끼 아닐까요? 「친구」를 요정 말로 하면 뭐예요?" }; story("모리아 서문 · 거울 호수", SP_GANDALF_FRONT, L0, 3); }
  for (;;) {
    { static const char * const L1[] = { "열려라", "두린", "멜론" }; c = choose("요정 말로 「친구」는?", L1, 3, NOCANCEL); }
    if (c == 2) {
  say("「멜론!」 문이 소리 없이 열렸다.");
  break;
}
    say("아무 일도 일어나지 않았다...");
  }
  { static const char * const L2[] = { "그 순간 호수가 끓어오르더니 긴 촉수가 프로도의 발목을 낚아챘다!", "샘: 나리를 놔! 이 괴물아!" }; story("모리아 서문 · 거울 호수", SP_WATCHER, L2, 2); }
  r = battle(FO_WATCHER, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  say("촉수가 물러난 틈에 모두 문 안으로 뛰어들었다. 등 뒤에서 문이 무너져 내렸다. 이제 돌아갈 길은 없다.");
  S.step = 16;
  save();
}

void step_16(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "간달프의 지팡이 끝 희미한 빛만이 길을 비춘다. 난쟁이들의 거대한 기둥이 어둠 속으로 끝없이 이어진다.", "어둠 속에서 무언가 졸졸 따라오는 기척이 있다. 그리고 벽 틈에서 노란 눈들이 번뜩였다!" }; story("모리아 · 어둠 속 광산", SP_GOBLIN, L0, 2); }
  r = battle(FO_GOBLIN, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  say("한 마리가 아니었다. 또 다른 고블린이 기둥을 타고 내려온다!");
  r = battle(FO_GOBLIN, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "세 갈래 길 앞에서 간달프가 한참 생각에 잠겼다.", "간달프: 의심스러울 땐 코를 따르라 했지. 이쪽 공기가 덜 퀴퀴하군." }; story("모리아 · 갈림길", SP_GANDALF_FRONT, L1, 2); }
  S.step = 17;
  save();
}

void step_17(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "먼지 쌓인 방 한가운데 돌무덤이 있었다. 「발린, 모리아의 주인」.", "김리가 무릎을 꿇고 오래도록 울었다.", "그때 피핀이 우물가 해골을 건드렸다. 와르르 떨어지는 소리가 광산 깊숙이 울려 퍼졌다.", "둥... 둥... 땅속 깊은 곳에서 북소리가 대답했다. 문을 막아라!" }; story("마자르불의 방", SP_GIMLI_FRONT, L0, 4); }
  r = battle(FO_GOBLIN, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "문짝이 부서지며 거대한 동굴 트롤이 사슬을 끌고 들어왔다!" }; story("마자르불의 방", SP_TROLL, L1, 1); }
  r = battle(FO_TROLL, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L2[] = { "트롤이 쓰러졌다. 창에 찔린 줄 알았던 프로도가 숨을 몰아쉬며 일어났다. 미스릴 갑옷이 막아 준 것이다!", "모두가 빠져나가자 간달프가 문에 봉인 주문을 걸었다. 문 너머에서 무시무시한 힘이 주문을 맞받아쳤다.", "간달프: 내 평생 이런 맞수는 처음이군... 서두르게! 다리로!" }; story("마자르불의 방", SP_GANDALF_FRONT, L2, 3); }
  healAll();
  S.step = 18;
  save();
}

void step_18(void) BANKED {
  uint8_t _r;
  { static const char * const L0[] = { "고블린들이 갑자기 비명을 지르며 흩어졌다. 붉은 불빛이 벽을 타고 번져 온다.", "간달프: 발로그... 옛 세상의 악마일세. 자네들 칼로는 상대가 안 돼. 달려라!", "좁은 돌다리 위. 간달프가 홀로 돌아서서 지팡이를 들었다." }; story("크하자드둠의 다리", SP_BALROG, L0, 3); }
  if (has(HE_GANDALF) && S.hero != HE_GANDALF) swapTo(HE_GANDALF);
  say("(간달프가 원정대가 건널 시간을 벌어야 한다!)"); _r = battle(FO_BALROG, 1, 3); if (_r == R_RESCUE) { say("간달프가 지팡이로 다리를 내리찍었다!"); say("「이곳은 지나갈 수 없다!」 다리가 무너지며 발로그가 불길 속으로 떨어졌다..."); rescue_end(); _r = R_WIN; }
  { static const char * const L1[] = { "그러나 떨어지던 발로그의 채찍 끝이 간달프의 발목을 휘감았다.", "간달프: 달아나라, 이 바보들아!", "간달프는 어둠 속으로 사라졌다..." }; story("크하자드둠의 다리", 255, L1, 3); }
  removeMember(HE_GANDALF);
  healAll();
  S.step = 19;
  save();
}
