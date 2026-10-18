#pragma bank 10
#include <gb/gb.h>
#include "data.h"
#include "engine.h"
#include "game.h"
#include "story.h"
void step_33(void) BANKED {
  uint8_t _r, r, c;
  { static const char * const L0[] = { "끝없이 가파른 계단. 밤에 샘은 골룸이 혼잣말하는 것을 들었다. 「그녀가 해치우게 하자... 그리고 보물은 우리 거야.」", "아침이 되자 렘바스가 사라져 있었다. 골룸은 샘의 옷에 묻은 부스러기를 가리키며 샘이 먹었다고 우겼다.", "샘이 골룸에게 덤벼들자 지친 프로도가 소리쳤다. 「샘, 집으로 돌아가.」", "샘은 울면서 계단을 내려갔다. 프로도는 골룸을 따라 어둠 속 굴로 들어갔다." }; story("키리스 웅골의 계단", SP_GOLLUM, L0, 4); }
  { static const char * const L1[] = { "썩은 냄새가 코를 찌르는 터널. 골룸은 어느새 사라졌다. 끈적한 줄이 얼굴에 감긴다.", "어둠 속에서 수많은 눈이 하나씩 켜졌다..." }; story("쉴로브의 굴", SP_SHELOB, L1, 2); }
  say("(빛의 병을 들어 버텨라! 가방에서 쓸 수 있다)"); _r = battle(FO_SHELOB, 1, 2); if (_r == R_RESCUE) { say("프로도가 굴 밖으로 달아났다. 그러나 등 뒤에서 거대한 독침이..."); say("프로도가 쓰러졌다."); rescue_end(); _r = R_WIN; }
  { static const char * const L2[] = { "계단을 내려가던 샘은 굴러떨어진 렘바스 부스러기를 보고 모든 걸 깨달았다. 샘은 다시 뛰어 올라왔다.", "거미줄에 꽁꽁 감긴 프로도 앞에서, 샘이 스팅과 빛의 병을 들고 거대한 거미 앞을 막아섰다!" }; story("쉴로브의 굴 · 출구", SP_FRODOSAM_FRONT, L2, 2); }
  healAll();
  r = battle(FO_SHELOB, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L3[] = { "쉴로브는 비틀거리며 어둠 속으로 기어 들어갔다.", "샘이 프로도를 흔들었지만 대답이 없었다. 차갑게 식은 얼굴... 샘은 프로도가 죽었다고 생각했다.", "샘: 끝내야 해요. 나리가 못 한 일을 제가 해야 해요. 샘은 반지를 자기 목에 걸었다." }; story("쉴로브의 굴 · 출구", SP_FRODOSAM_FRONT, L3, 3); }
  say("반지가 속삭인다. 이 산맥의 주인이 되어 모르도르를 거대한 정원으로 바꿀 수 있다고. 샘이 다스리는 끝없는 꽃밭...");
  { static const char * const L4[] = { "환상을 비웃는다", "잠깐 그 꿈을 떠올린다" }; c = choose("샘은...", L4, 2, NOCANCEL); }
  if (c == 0) say("샘: 나한테 필요한 건 작은 정원 하나면 돼요. 남의 손을 빌린 큰 정원 따윈 필요 없어요."); else {
  S.shadow++;
  say("달콤한 꿈이 스쳤다. 하지만 샘은 고개를 저었다. 정원사의 손은 자기 손으로 흙을 만지는 손이다. (그림자 +1)");
}
  say("그때 오크들이 몰려와 프로도를 메고 갔다. 「아직 살아 있어! 독에 마비된 것뿐이야!」 샘은 주먹을 쥐었다. 나리는 살아 있다!");
  S.step = 34;
  save();
}

void step_34(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "탑 안에서 오크들끼리 미스릴 갑옷을 두고 다투다 서로를 베고 있었다. 샘은 칼을 들고 계단을 뛰어올랐다." }; story("키리스 웅골의 탑", SP_ORC, L0, 1); }
  r = battle(FO_ORCT, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  say("위층에서 또 다른 오크가 채찍을 들고 내려온다!");
  r = battle(FO_ORCT, 0, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L1[] = { "꼭대기 방에 프로도가 묶여 있었다. 샘을 보자 프로도가 울음을 터뜨렸다. 「반지를 빼앗겼어, 샘! 다 끝났어!」", "샘: 아니에요. 제가 가지고 있어요. 죄송해요, 나리." }; story("키리스 웅골의 탑 · 꼭대기", SP_FRODOSAM_FRONT, L1, 2); }
  say("프로도가 반지를 낚아채듯 받아 들었다. 「도둑!」 ... 그러고는 곧 자기 말에 소스라쳤다. 「미안해, 샘. 이게 나를 이렇게 만들어.」");
  say("둘은 죽은 오크들의 갑옷을 걸치고 탑을 빠져나왔다. 프로도가 반지를 다시 지녔다.");
  S.shadow++;
  healAll();
  S.step = 35;
  save();
}

void step_35(void) BANKED {
  uint8_t r;
  { static const char * const L0[] = { "흰 옷을 입고 돌아온 간달프가 무너져 가는 하얀 도시를 지키고 있었다. 하늘에는 날짐승을 탄 나즈굴들이 맴돈다.", "펠렌노르 들판에서는 로한의 기병들이 함성과 함께 달려들었고, 아라곤은 망자의 길을 지나 검은 배를 이끌고 나타났다." }; story("그 시각 · 미나스 티리스", SP_GANDALFW_FRONT, L0, 2); }
  { static const char * const L1[] = { "쓰러진 세오덴 왕 앞에 마술사왕이 내려앉았다. 「어떤 사내도 나를 죽일 수 없다.」", "방패를 든 로한의 아가씨가 투구를 벗었다. 에오윈이었다. 「나는 사내가 아니다!」 그녀의 칼이 왕관 아래를 꿰뚫었다." }; story("펠렌노르 들판", SP_EOWYN_FRONT, L1, 2); }
  { static const char * const L2[] = { "서부의 군대가 검은 문 앞에 섰다. 모르도르의 눈을 프로도에게서 돌리기 위해서였다.", "문이 열리고 투구에 입만 드러낸 사자가 다가왔다. 그가 프로도의 미스릴 갑옷을 흔들어 보였다.", "아라곤: 거짓말이다. 나는 믿지 않는다." }; story("그 시각 · 검은 문 앞", SP_MOUTH, L2, 3); }
  keep_party();
  S.hero = HE_ARAGORN;
  S.lv = 30;
  S.xp = 0;
  solo_party(HE_ARAGORN);
  
  S.hp = stat(ST_HP);
  r = battle(FO_MOUTH, 1, 0);
  if (r != R_WIN) say("아라곤이 쓰러지는 척하다 단숨에 칼을 휘둘렀다. 사자가 말에서 떨어졌다.");
  restore_party();
  say("아라곤: 서부의 사람들이여, 오늘 우리는 반지 지기를 위해 싸운다! 검은 문이 열리고, 군대가 쏟아져 나왔다.");
  S.step = 36;
  save();
}

void step_36(void) BANKED {
  uint8_t r;
  chapterTitle("제8장", "운명의 산");
  { static const char * const L0[] = { "불타는 산까지 끝없이 이어진 재의 평원. 물도 렘바스도 거의 바닥났다.", "샘은 가방의 냄비를 내려놓았다. 한참을 바라보다가 조용히 돌무더기 위에 두고 왔다.", "프로도는 이제 물 한 모금 넘기기도 힘들어했다. 반지가 맷돌처럼 목을 짓누른다." }; story("고르고로스 평원", SP_FRODOSAM_FRONT, L0, 3); }
  S.lembas = MIN(S.lembas, 2);
  { static const char * const L1[] = { "마지막 비탈에서 프로도가 쓰러졌다. 「반지 무게가... 더는 못 가겠어, 샘.」", "샘: 반지는 대신 들어 드릴 수 없지만, 나리는 업어 드릴 수 있어요!" }; story("운명의 산 · 비탈", SP_FRODOSAM_FRONT, L1, 2); }
  { static const char * const L2[] = { "샘이 프로도를 등에 업고 한 걸음씩 산을 올랐다.", "발밑에서 뜨거운 재가 부서졌다. 샘은 이를 악물었다." }; story("운명의 산 · 비탈", SP_SAMFRODO_FRONT, L2, 2); }
  { static const char * const L3[] = { "그때 바위 뒤에서 골룸이 덮쳐 왔다! 「보물! 우리 보물!」" }; story("운명의 산 · 비탈", SP_GOLLUM, L3, 1); }
  r = battle(FO_GOLLUMF, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  S.step = 37;
  save();
}

void step_37(void) BANKED {
  uint8_t c;
  { static const char * const L0[] = { "산 안쪽, 끓어오르는 불의 틈 앞. 반지가 만들어진 곳이다.", "샘: 던져요, 나리! 불 속으로!" }; story("운명의 틈", SP_FRODOSAM_FRONT, L0, 2); }
  say("프로도가 반지를 들어 올렸다. 그리고 천천히 돌아섰다.");
  { static const char * const L1[] = { "반지를 던진다", "반지는 내 것이다" }; c = choose("프로도는...", L1, 2, NOCANCEL); }
  if (c == 0) say("프로도는 팔을 뻗었다... 하지만 손가락이 펴지지 않았다. 「못 하겠어... 이건 내 거야.」");
  { static const char * const L2[] = { "프로도가 반지를 꼈다. 모르도르 전체가 그를 향해 눈을 돌렸다." }; story("운명의 틈", SP_EYE, L2, 1); }
  { static const char * const L3[] = { "보이지 않는 프로도에게 골룸이 달려들어 손가락을 물어뜯었다! 반지를 되찾은 골룸이 기뻐 날뛰다... 발을 헛디뎠다." }; story("운명의 틈", SP_GOLLUM, L3, 1); }
  { static const char * const L4[] = { "골룸과 반지가 함께 불 속으로 떨어졌다. 반지가 녹아내리며 마지막으로 빛났다." }; story("운명의 틈", SP_RING_ITEM, L4, 1); }
  { static const char * const L5[] = { "땅이 흔들리고 바랏두르의 탑이 무너져 내렸다. 거대한 눈이 꺼졌다." }; story("운명의 산", SP_EYE, L5, 1); }
  { static const char * const L6[] = { "용암이 흐르는 바위 위에서 프로도와 샘은 서로 손을 잡았다.", "프로도: 함께 있어서 다행이야, 샘. 모든 게 끝나는 곳에서." }; story("운명의 산", SP_FRODOSAM_FRONT, L6, 2); }
  { static const char * const L7[] = { "그때 하늘에서 큰독수리들이 내려왔다. 그 등에는 흰 옷의 간달프가 타고 있었다." }; story("운명의 산", SP_GANDALFW_FRONT, L7, 1); }
  S.step = 38;
  save();
}

void step_38(void) BANKED {
  { static const char * const L0[] = { "눈을 뜨자 간달프가 웃고 있었다. 프로도도 따라 웃었다." }; story("미나스 티리스", SP_GANDALFW_FRONT, L0, 1); }
  { static const char * const L1[] = { "이어 메리, 피핀, 레골라스, 김리가 문을 열고 뛰어들었다.", "아라곤이 곤도르의 왕관을 썼다. 그리고 네 호빗 앞에서 무릎을 꿇었다. 「그대들은 누구에게도 고개 숙일 필요가 없소.」", "온 도시가 따라 무릎을 꿇었다." }; story("미나스 티리스", SP_ARAGORN_FRONT, L1, 3); }
  chapterTitle("제3부 「왕의 귀환」 끝", "반지는 사라졌다");
  S.step = 39;
  save();
}

void step_39(void) BANKED {
  uint8_t r;
  chapterTitle("덧붙이는 장", "샤이어 소탕");
  { static const char * const L0[] = { "네 호빗이 고향으로 돌아왔다. 그런데 다리에 낯선 문이 세워져 있고, 「샤키 두목의 명령」이라는 팻말이 붙어 있었다.", "나무는 베이고, 굴뚝마다 시커먼 연기. 거울에서 본 그대로였다.", "메리: 원정에서 배운 게 하나 있다면, 이런 건 그냥 두면 안 된다는 거지.", "메리가 로한의 뿔나팔을 불었다. 샤이어 곳곳의 호빗들이 쇠스랑과 몽둥이를 들고 모여들었다." }; story("브랜디와인 다리", SP_MERRYPIPPIN_FRONT, L0, 4); }
  { static const char * const L1[] = { "골목쟁이집 앞에 지저분한 옷을 입은 노인이 서 있었다. 몰락한 사루만, 「샤키」였다.", "샤키: 어서 오게, 반지 지기. 자네 고향을 내 마음대로 바꿔 보았지." }; story("골목쟁이집 앞", SP_SHARKEY, L1, 2); }
  r = battle(FO_SHARKEY, 1, 0);
  if (r == R_LOSE) { lose(); return; }
  { static const char * const L2[] = { "호빗들이 사루만을 둘러쌌다. 프로도가 손을 들어 막았다. 「죽이지 마. 그는 한때 위대했어. 이제는 그저 가엾을 뿐이야.」", "사루만은 아무 말 없이 떠났고, 그날로 샤이어에서 사라졌다.", "샘은 갈라드리엘에게 받은 흙 상자를 열어 베어진 나무 자리마다 한 줌씩 뿌렸다. 이듬해 봄, 샤이어는 그 어느 때보다 푸르렀다." }; story("골목쟁이집 앞", SP_FRODOSAM_FRONT, L2, 3); }
  S.step = 40;
  save();
}

void step_40(void) BANKED {
  { static const char * const L0[] = { "몇 해 뒤. 바람마루의 상처는 해마다 같은 날이면 다시 아려 왔다.", "프로도는 빌보, 간달프, 요정들과 함께 바다 건너 서쪽으로 떠나기로 했다.", "프로도: 샤이어를 지켜 냈어, 샘. 하지만 나를 위해서는 아니었나 봐.", "프로도는 샘에게 붉은 책을 건넸다. 「남은 쪽은 네가 채워 줘.」", "배가 수평선 너머로 사라졌다. 샘은 집으로 돌아가 문을 열었다. 「다녀왔어.」" }; story("회색 항구", SP_GALADRIEL_FRONT, L0, 5); }
  sb_clear(); sb_add("여정의 그림자 "); sb_num(S.shadow, 0); sb_add(" · 레벨 "); sb_num(S.lv, 0); sb_add(""); chapterTitle("반지 원정 · 끝", SB);
  say("끝까지 함께해 주셔서 고맙습니다. 저장되었습니다.");
  S.step = 41;
  S.done = 1;
  save();
}
