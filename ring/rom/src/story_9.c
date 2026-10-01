#pragma bank 9
#include <gb/gb.h>
#include "data.h"
#include "engine.h"
#include "game.h"
#include "story.h"
void step_19(void) BANKED {
  { static const char * const L0[] = { "햇빛 아래로 빠져나온 원정대는 아무 말도 하지 못했다. 샘이 소리 없이 울었다.", "아라곤: 슬퍼할 시간이 없소. 해가 지면 이 언덕은 오크로 뒤덮일 거요. 로스로리엔으로 가야 하오." }; story("어둔내 골짜기", SP_FRODOSAM_FRONT, L0, 2); }
  S.step = 20;
  save();
}

void step_20(void) BANKED {
  uint8_t c;
  chapterTitle("제5장", "황금 숲과 대강");
  { static const char * const L0[] = { "황금빛 잎이 지지 않는 숲. 나무 위에서 요정 경비대장 할디르가 화살을 겨눈 채 내려왔다.", "할디르: 난쟁이는 눈을 가리고 들어가야 하오.", "김리가 버럭 화를 냈다. 결국 아라곤이 「그럼 모두 눈을 가리겠소」 하고 나서자, 레골라스도 함께 눈을 가렸다.", "눈을 가린 채 손을 잡고 걷는 사이, 레골라스와 김리 사이의 날 선 기운이 조금 누그러졌다." }; story("로스로리엔 · 숲 경계", SP_LEGOLAS_FRONT, L0, 4); }
  { static const char * const L1[] = { "거대한 나무 위 도시. 빛나는 갈라드리엘이 원정대를 내려다보았다. 누구도 그녀의 눈을 오래 마주하지 못했다.", "그날 밤 그녀는 프로도를 은빛 물그릇 앞으로 데려갔다. 「들여다보겠느냐?」" }; story("카라스 갈라돈", SP_GALADRIEL_FRONT, L1, 2); }
  { static const char * const L2[] = { "들여다본다", "들여다보지 않는다" }; c = choose("거울을...", L2, 2, NOCANCEL); }
  if (c == 0) say("물 위에 불타는 샤이어가 비쳤다. 쓰러진 굴뚝, 끌려가는 호빗들... 그리고 불꽃에 휩싸인 거대한 눈. 프로도는 비틀거리며 물러났다.");
  say("프로도가 반지를 꺼냈다. 「이걸... 당신이 가져 주시겠어요?」");
  { static const char * const L3[] = { "갈라드리엘에게 내민다", "다시 넣는다" }; c = choose("반지를...", L3, 2, NOCANCEL); }
  if (c == 0) {
  say("한순간 그녀가 무섭도록 크고 아름다워졌다. 그러나 곧 원래 모습으로 돌아와 고개를 저었다. 「시험을 이겨 냈구나. 나는 작아져 서쪽으로 가겠다.」");
  S.shadow = MAX(0, S.shadow - 1);
  say("마음이 조금 가벼워졌다. (그림자 −1)");
} else say("갈라드리엘이 희미하게 웃었다. 「그것은 너에게 맡겨진 짐이다.」");
  { static const char * const L4[] = { "갈라드리엘이 선물을 나눠 주었다. 모두에게 잎사귀 브로치가 달린 요정 망토(방어 +2), 넉넉한 렘바스.", "프로도에게는 에아렌딜의 별빛을 담은 「빛의 병」. 「다른 모든 빛이 꺼진 어둠 속에서 너를 비춰 줄 것이다.」", "김리는 머리카락 한 올을 청했다가 세 올을 받고는 감격해서 말을 잇지 못했다.", "빛의 병을 얻었다! 전투 중 가방에서 쓰면 적이 눈부셔 움직이지 못한다. (한 싸움에 한 번)" }; story("로스로리엔 · 떠나는 날", SP_GALADRIEL_FRONT, L4, 4); }
  S.cloak = 1;
  S.phial = 1;
  S.lembas = MAX(S.lembas, 6);
  S.herb = MAX(S.herb, 3);
  healAll();
  S.step = 21;
  save();
}

void step_21(void) BANKED {
  { static const char * const L0[] = { "요정 배 세 척에 나눠 타고 대강을 따라 내려갔다. 밤마다 무언가 뒤를 쫓는 기척이 있었다. 통나무에 매달려 헤엄치는 골룸이었다.", "어느 밤, 남쪽 하늘에서 거대한 날개 달린 그림자가 다가왔다. 차가운 공포가 배 위를 덮쳤다.", "레골라스가 갈라드리엘에게 받은 활을 당겼다. 화살 한 대에 그림자가 비명을 지르며 강 건너로 떨어졌다.", "김리: 훌륭하오, 요정 친구! 이번만큼은 인정하지." }; story("대강", SP_FELLBEAST, L0, 4); }
  { static const char * const L1[] = { "강 양쪽에 손을 치켜든 거대한 왕들의 석상이 서 있었다. 곤도르의 옛 국경이다.", "아라곤이 고개를 들고 조용히 석상을 바라보았다. 그는 이실두르의 후손이었다." }; story("아르고나스", SP_ARAGORN_FRONT, L1, 2); }
  S.step = 22;
  save();
}

void step_22(void) BANKED {
  uint8_t c, r;
  { static const char * const L0[] = { "원정대는 강가 언덕에서 길을 정해야 했다. 동쪽 모르도르로, 아니면 보로미르가 바라는 곤도르로.", "홀로 생각에 잠긴 프로도를 보로미르가 따라왔다. 「반지를 나에게 빌려주게. 곤도르를 지킬 수 있는 힘이야!」", "그의 눈빛이 이상하게 번들거렸다." }; story("아몬 헨", SP_BOROMIR_FRONT, L0, 3); }
  { static const char * const L1[] = { "반지를 끼고 달아난다", "말로 설득한다" }; c = choose("프로도는...", L1, 2, NOCANCEL); }
  if (c == 0) {
  S.shadow++;
  say("반지를 끼자 세상이 잿빛으로 변했다. 언덕 꼭대기에서 불타는 눈이 이쪽을 꿰뚫어 보았다! (그림자 +1)");
} else say("「보로미르, 당신은 지금 당신이 아니에요!」 보로미르가 덤벼들었고, 프로도는 몸을 비틀어 겨우 빠져나왔다.");
  say("정신을 차린 보로미르가 무릎을 꿇었다. 「내가 무슨 짓을...」 그러나 프로도는 이미 사라진 뒤였다.");
  { static const char * const L2[] = { "그때 숲 사이로 흰 손 표식을 단 거대한 오크들이 쏟아져 나왔다. 사루만의 우루크하이다!" }; story("아몬 헨 · 숲속", SP_URUK, L2, 1); }
  r = battle(FO_URUKS, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L3[] = { "숲 저편에서 곤도르의 뿔나팔 소리가 길게 울렸다. 보로미르가 메리와 피핀을 지키며 홀로 싸우고 있었다!", "검은 화살이 한 대, 또 한 대 그의 몸에 꽂혔다. 그래도 보로미르는 쓰러지지 않았다." }; story("아몬 헨 · 숲속", SP_BOROMIR_FRONT, L3, 2); }
  { static const char * const L4[] = { "우루크하이 대장이 마지막 화살을 메기며 돌아섰다!" }; story("아몬 헨 · 숲속", SP_URUK, L4, 1); }
  r = battle(FO_URUK, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L5[] = { "그러나 메리와 피핀은 이미 우루크하이에게 끌려간 뒤였다.", "보로미르가 아라곤의 팔에 기대어 말했다. 「반지를 빼앗으려 했소... 미안하오. 내 백성을... 지켜 주시오.」", "아라곤: 그대의 도시는 무너지지 않을 거요. 약속하겠소, 형제여.", "곤도르의 용사는 그렇게 눈을 감았다. 원정대는 그를 요정 배에 눕혀 라우로스 폭포로 떠나보냈다." }; story("아몬 헨 · 숲속", SP_BOROMIR_FRONT, L5, 4); }
  S.step = 23;
  save();
}

void step_23(void) BANKED {
  { static const char * const L0[] = { "프로도는 혼자 배를 밀어냈다. 반지는 결국 모두를 망가뜨릴 것이다. 혼자 가야 한다.", "샘: 나리! 기다려요! 저 헤엄 못 쳐요!", "첨벙거리며 물에 빠진 샘을 프로도가 손을 뻗어 건져 올렸다.", "샘: 약속했잖아요. 끝까지 함께한다고. 감지 할아버지한테도 그렇게 말하고 왔다고요.", "프로도는 웃으며 울었다. 둘은 함께 동쪽 강둑으로 노를 저었다." }; story("파르스 갈렌 · 강가", SP_FRODOSAM_FRONT, L0, 5); }
  { static const char * const L1[] = { "언덕 위에서 아라곤은 멀어지는 배를 바라보았다. 그리고 쫓아가지 않았다.", "아라곤: 프로도의 운명은 이제 우리 손을 떠났네. 하지만 메리와 피핀이 끌려가 고문당하게 둘 수는 없지.", "레골라스·김리: 그럼 오크를 쫓아야겠군!" }; story("아몬 헨", SP_ARAGORN_FRONT, L1, 3); }
  removeMember(HE_ARAGORN); removeMember(HE_LEGOLAS); removeMember(HE_GIMLI);
  if (S.hero != HE_FRODOSAM) swapTo(HE_FRODOSAM);
  healAll();
  S.step = 24;
  save();
}

void step_24(void) BANKED {
  chapterTitle("제1부 「반지 원정대」 끝", "이어서 제2부 「두 개의 탑」");
  S.step = 25;
  save();
}

void step_25(void) BANKED {
  uint8_t r, c;
  chapterTitle("제6장", "두 개의 탑 · 반지의 길");
  { static const char * const L0[] = { "날카로운 바위산이 미로처럼 얽힌 에민 무일. 며칠째 같은 자리를 맴도는 것 같다.", "절벽을 내려가다 샘이 로리엔에서 받은 밧줄을 묶었다. 다 내려와서 아쉬워하자, 매듭이 저절로 풀려 밧줄이 툭 떨어졌다.", "샘: 제가 묶은 매듭이 풀릴 리가 없는데... 요정 밧줄이 돌아오고 싶었나 봐요.", "그날 밤. 절벽을 거꾸로 기어 내려오는 그림자가 있었다. 「도둑놈들... 우리 보물을 훔쳐 간 도둑놈들!」" }; story("에민 무일", SP_FRODOSAM_FRONT, L0, 4); }
  r = battle(FO_GOLLUMB, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "샘이 요정 밧줄로 골룸을 꽁꽁 묶었다. 밧줄이 닿은 곳마다 골룸은 데인 듯 비명을 질렀다.", "골룸: 아파! 차가워! 풀어 줘, 착한 호빗... 길을 안내할게. 모르도르로 가는 비밀 길을 알아!", "프로도는 빌보가 했던 말을 떠올렸다. 그때 골룸을 죽이지 않은 건 연민 때문이었다고." }; story("에민 무일", SP_GOLLUM, L1, 3); }
  { static const char * const L2[] = { "밧줄을 풀어 준다", "묶은 채 끌고 간다" }; c = choose("골룸을...", L2, 2, NOCANCEL); }
  if (c == 0) say("프로도: 반지에 걸고 맹세해. 우리를 해치지 않겠다고. 골룸은 엎드려 「보물에 걸고」 맹세했다."); else {
  say("묶인 골룸이 울며 버둥댔다. 결국 프로도가 마음이 약해져 밧줄을 풀었다. 골룸은 「보물에 걸고」 맹세했다.");
}
  say("골룸(스메아골)이 길잡이가 되었다. 싸우지는 않지만 길을 안내한다.");
  S.gollum = 1;
  S.step = 26;
  save();
}

void step_26(void) BANKED {
  uint8_t c;
  { static const char * const L0[] = { "물 위에 희미한 불빛들이 떠 있다. 물속을 들여다보니 오래전 전쟁에서 죽은 이들의 얼굴이 잠겨 있다.", "골룸: 불빛을 보지 마. 따라가면 그들과 함께 잠들게 돼." }; story("죽음늪", SP_GOLLUM, L0, 2); }
  { static const char * const L1[] = { "눈을 돌린다", "들여다본다" }; c = choose("물속 얼굴이 부른다...", L1, 2, NOCANCEL); }
  if (c == 1) {
  say("프로도가 홀린 듯 물속으로 빠졌다! 창백한 손들이 뻗어 온다... 골룸이 뛰어들어 프로도를 끌어냈다.");
  S.shadow++;
  say("(그림자 +1)");
} else say("샘이 프로도의 손을 꼭 잡고 앞만 보고 걸었다.");
  { static const char * const L2[] = { "하늘에서 끔찍한 비명. 날개 달린 짐승을 탄 나즈굴이 머리 위를 지나간다.", "셋은 진흙 속에 납작 엎드렸다. 다행히 그림자는 서쪽으로 사라졌다." }; story("죽음늪", SP_FELLBEAST, L2, 2); }
  S.step = 27;
  save();
}

void step_27(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "거대한 쇠문 앞. 남쪽에서 온 군대가 줄지어 문 안으로 들어간다. 경비병 하나가 바위 쪽으로 다가온다!" }; story("검은 문 · 모란논", SP_ORC, L0, 1); }
  r = battle(FO_ORC, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "이 문으로는 절대 들어갈 수 없다.", "골룸: 다른 길이 있어. 남쪽, 무서운 도시 옆으로... 계단을 오르고, 터널을 지나... 아무도 지키지 않는 길.", "샘은 골룸의 눈빛이 영 마음에 들지 않았다." }; story("검은 문 · 모란논", SP_GOLLUM, L1, 3); }
  S.step = 28;
  save();
}

void step_28(void) BANKED {
  uint8_t _r;
  { static const char * const L0[] = { "모르도르 가장자리인데도 아직 꽃과 허브가 자라는 숲. 샘이 오랜만에 신이 났다.", "골룸이 잡아 온 토끼 두 마리로 샘이 스튜를 끓였다. 「감자만 있었으면!」 골룸은 날것이 최고라며 혀를 찼다.", "그때 숲속에서 함성과 함께 땅이 울렸다. 남쪽 하라드림 군대와 곤도르 순찰대가 맞붙었다!", "나무를 부러뜨리며 거대한 짐승이 돌진해 온다!" }; story("이실리엔", SP_FRODOSAM_FRONT, L0, 4); }
  say("(순찰대가 쓰러뜨릴 때까지 버텨야 한다!)"); _r = battle(FO_MUMAK, 1, 3); if (_r == R_RESCUE) { say("곤도르 순찰대의 화살이 비처럼 쏟아졌다!"); say("거대한 짐승이 비틀거리다 숲 저편으로 쓰러졌다."); rescue_end(); _r = R_WIN; }
  { static const char * const L1[] = { "샘: 올리펀트다! 진짜 올리펀트를 봤어! 아무도 안 믿을 거야!", "녹색 두건을 쓴 순찰대가 둘을 둘러쌌다. 대장은 보로미르의 동생, 파라미르였다." }; story("이실리엔", SP_FARAMIR_FRONT, L1, 2); }
  S.step = 29;
  save();
}

void step_29(void) BANKED {
  uint8_t c;
  { static const char * const L0[] = { "폭포 뒤에 숨은 동굴. 파라미르가 곤도르의 오래된 이야기를 들려주었다. 바다 건너 사라진 왕들의 나라, 흰 나무, 그리고 보로미르.", "파라미르: 형의 뿔나팔이 두 동강 난 채 강물에 떠내려왔소. 형에게 무슨 일이 있었던 거요?", "프로도는 반지에 대해서는 끝내 말하지 않았다.", "밤에 순찰대가 금지된 못에서 물고기를 잡는 골룸을 발견했다. 들어온 자는 죽음뿐인 곳이다." }; story("헨네스 안눈 · 해 지는 창", SP_FARAMIR_FRONT, L0, 4); }
  { static const char * const L1[] = { "직접 불러 데려온다", "순찰대에 맡긴다" }; c = choose("골룸을...", L1, 2, NOCANCEL); }
  if (c == 0) say("프로도가 부르자 골룸은 순순히 다가왔다가 그대로 붙잡혔다. 골룸의 눈에 배신감이 번졌다. 「주인님이... 우리를 속였어...」"); else {
  say("순찰대가 골룸을 쏘려 하자 프로도가 끝내 앞을 막았다. 골룸은 붙잡혔지만 살았다.");
}
  say("샘이 그만 입을 잘못 놀렸다. 「나리는 그 반지를...!」 파라미르의 눈빛이 변했다.");
  say("파라미르: 곤도르를 구할 기회로군. 반지를 미나스 티리스로 가져가겠소.");
  S.step = 30;
  save();
}

void step_30(void) BANKED {
  uint8_t _r, c;
  { static const char * const L0[] = { "불타는 폐허 도시. 오크들이 강을 건너 몰려오고 있다.", "하늘에서 비명과 함께 날짐승을 탄 나즈굴이 내려앉았다. 프로도가 홀린 듯 걸어 나가 반지를 들어 올린다!" }; story("오스길리아스", SP_FELLBEAST, L0, 2); }
  say("(프로도가 정신을 차릴 때까지 버텨야 한다!)"); _r = battle(FO_FELLBEAST, 1, 3); if (_r == R_RESCUE) { say("샘이 몸을 날려 프로도를 덮쳤다!"); say("둘이 계단 아래로 굴렀다. 파라미르의 화살에 날짐승이 놀라 날아올랐다."); rescue_end(); _r = R_WIN; }
  say("정신이 나간 프로도가 샘의 목에 스팅을 겨누었다... 그리고 손을 떨구었다. 「난 못 하겠어, 샘.」");
  { static const char * const L1[] = { "이야기를 꺼낸다", "말없이 곁에 앉는다" }; c = choose("샘은...", L1, 2, NOCANCEL); }
  if (c == 0) say("샘: 옛날이야기 속 영웅들도 돌아갈 기회가 많았대요. 그래도 계속 갔대요. 세상에 아직 지킬 만한 좋은 게 있다고 믿어서요."); else say("샘은 아무 말 없이 프로도의 어깨에 손을 얹었다. 그 손이 무엇보다 따뜻했다.");
  { static const char * const L2[] = { "그 모습을 지켜보던 파라미르가 마침내 칼을 거두었다.", "파라미르: 가시오. 곤도르의 장수가 어떤 사람인지 보여 줄 때요. 그 대가는 내가 치르겠소.", "프로도와 샘, 골룸은 다시 동쪽으로, 그림자의 산맥으로 향했다." }; story("오스길리아스", SP_FARAMIR_FRONT, L2, 3); }
  S.shadow = MAX(0, S.shadow - 1);
  healAll();
  S.step = 31;
  save();
}

void step_31(void) BANKED {
  chapterTitle("제2부 「두 개의 탑」 끝", "이어서 제3부 「왕의 귀환」");
  S.step = 32;
  save();
}

void step_32(void) BANKED {
  uint8_t c;
  chapterTitle("제7장", "키리스 웅골");
  { static const char * const L0[] = { "네 갈래 길이 만나는 곳에 머리가 깨진 옛 왕의 석상이 서 있었다. 오크들이 낙서를 해 놓았다.", "그때 구름 사이로 저녁 햇살이 비쳤다. 바닥에 굴러떨어진 석상의 머리 위에 하얀 꽃덩굴이 왕관처럼 감겨 있었다.", "프로도: 봐, 샘. 저들이 영원히 이기지는 못해." }; story("쓰러진 왕의 갈림길", SP_FRODOSAM_FRONT, L0, 3); }
  { static const char * const L1[] = { "골짜기 건너편에 푸르스름한 빛을 내뿜는 죽음의 도시가 있다. 쳐다보기만 해도 반지가 무거워진다.", "땅이 울리며 성문이 열리고, 끝없는 군대가 쏟아져 나왔다. 맨 앞에 왕관을 쓴 기사, 마술사왕이다.", "그가 문득 이쪽을 돌아보았다. 숨이 멎을 것 같다..." }; story("미나스 모르굴", SP_WITCHKING, L1, 3); }
  { static const char * const L2[] = { "반지를 움켜쥔다", "빛의 병을 쥔다" }; c = choose("프로도는...", L2, 2, NOCANCEL); }
  if (c == 0) {
  S.shadow++;
  say("반지를 끼고 싶은 마음을 간신히 눌렀다. 마술사왕은 고개를 돌려 미나스 티리스 쪽으로 떠났다. (그림자 +1)");
} else say("주머니 속 빛의 병이 손바닥을 따뜻하게 했다. 마술사왕은 고개를 돌려 미나스 티리스 쪽으로 떠났다.");
  S.step = 33;
  save();
}
