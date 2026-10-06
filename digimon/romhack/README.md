# 디지몬스터 「내 버전」 개조 도구

엘클 님의 「디지몬스터」(포켓몬스터 금 한글판 개조)를 허락받고 한 번 더 고치기 위한 도구 모음.
**롬·패치 결과·롬에서 뽑은 그림은 저장소에 올리지 않는다.** 모두 `work/`에만 둔다(`.gitignore`로 막혀 있음).
배포 범위는 엘클 님께 확인한 뒤에 정한다.

## 이어받기 (다른 세션·계정에서 이어서 할 때)

- 브랜치: `claude/kind-newton-dl61e0` (저장소 2tri/games, 폴더 `digimon/`)
- 롬 파일 (저장소에 없음 — 사용자에게 받아 `digimon/romhack/work/` 에 둠, work/ 는 gitignore):
  - `work/base.gbc` — 디지몬스터 1.4 (모든 빌드의 바탕, `DMROM=경로` 로도 지정 가능)
  - `work/v20.gbc` — 디지몬스터 2.0 (2.0 그림·기술 복사에 씀, rules.V20)
- 빌드: `cd digimon/romhack && python3 -c "import patch,dmrom; patch.build(dmrom.default_rom(),'work/myver.gbc','work/myver.ips')"`
- 검사: `python3 check.py work/myver.gbc` (규칙 R1~R23) · `python3 romtest.py` (PyBoy 시험, 처음엔 인트로 상태를 만듦)
- 금 한글판 디스어셈블리(pokegold-kr, rgbds 1.0.3 빌드)를 `/tmp/pgkr` 에 두어야 encounters·traces·romtest 가 동작
- **새 세션 준비 순서 (없으면 빌드가 아래 오류로 멈춤 — 2026-10-06 실제로 막혔던 순서)**
  1. `pip install pyboy numpy pillow scipy` (scipy 없으면 patch.py 의 `tools/enlarge14.py` 에서 ModuleNotFoundError)
  2. `git clone --depth 1 https://github.com/Narishma-gb/pokegold-kr /tmp/pgkr` 후 `export POKEGOLD_KR=/tmp/pgkr` (없으면 `FileNotFoundError: .../data/trainers/parties.asm`. 기본값은 `/home/user/narishma-gb/pokegold-kr` 라서 환경변수 필수)
  3. rgbds 1.0.3: `git clone --depth 1 --branch v1.0.3 https://github.com/gbdev/rgbds /tmp/rgbds && cd /tmp/rgbds && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j8 && cmake --install build` (cmake·gcc·bison·libpng 필요)
  4. `work/anat/` 만들기 (없으면 `FileNotFoundError: work/anat/pokegold.sym`, moves7.py 가 읽음). `/tmp/pgkr` 에서 `baserom_g.bin` 을 00 으로 채운 2MB 로 두고 `make clean; make -j8 pokegold.gbc` → `pokegold.gbc` 를 `work/anat/van_00.gbc`, `pokegold.sym`·`pokegold.map` 을 `work/anat/` 로 복사. 다시 FF 로 채운 2MB 로 `make clean; make -j8 pokegold.gbc` → `work/anat/van_ff.gbc`
  5. 롬 두 개를 `work/base.gbc`(1.4, CRC32 AEB9BACB)·`work/v20.gbc`(2.0, CRC32 A70CEC43) 로 두고 빌드·검사·시험
  - 확인값 (2026-10-06, f0a7b7f): check.py 22 [OK] / 0 [X] / 0 [?] (3초) · romtest.py 116 OK / 실패 1 (기술 224 송곳 돌진 스팅몬 「독 안 걸림」, 약 2분)
- 읽을 문서 순서:
  1. `digimon/작업팩_1006_목요일까지.md` — 지금 진행 중인 단계(S1~S11)와 보고 양식
  2. `digimon/판정/` — 설계자 판정 (날짜_단계 순서로)
  3. `digimon/보고/` — 단계마다 보고서 (짧은 보고 + 롬 확인값)
  4. `digimon/decisions.md` — 결정 로그 (한 줄씩)
  5. `digimon/기획.md` — 전체 기획
  6. 이 README 의 아래 절들 (도구·표 위치)
- 단계별 코드: `patch.py`(빌드 전체) · `rules.py`(값) · `moves7.py`(S7 기술) · `evo8.py`(S8 진화 장면) · `check.py`(R1~R23) · `romtest.py`(PyBoy 시험)
- 알려진 문제: `rules.RECLAIM_EMPTY_EVOS = True` 로 켜면 학습표가 깨짐 (꺼 둠, 원인 미확인)
- 지키는 것: 롬·IPS·롬에서 뽑은 그림·대사는 공개 저장소에 올리지 않음 (work/ 에만). 1.4 그림 공개 커밋 금지. 단계마다 롬 파일은 보내지 않고 S11 에서 IPS 두 개.

## 쓰는 법

```sh
pip install pyboy numpy pillow
cp <디지몬스터 롬> work/base.gbc                # 또는 DMROM=<경로>
python3 audit.py      # 종마다 이름·능력치·진화·그림 → work/audit.json, work/sheet0~3.png
python3 patch.py      # work/base.gbc → work/myver.gbc + work/myver.ips
python3 romtest.py    # 고친 롬 자동 시험 (PyBoy, 약 30초)
python3 check.py      # 검수 보고서 (자문자에게 그대로 붙임). --full evo 로 진화 표
python3 wild.py       # 야생 출현표 → work/wild.json, 아직 포켓몬인데 야생에 나오는 칸 목록
python3 grades.py     # 롬이 바뀌었을 때(2.0판) grades.json 다시 만들기
python3 trainers.py   # 트레이너가 데리고 있는 종 → work/trainers.json, 아직 포켓몬을 쓰는 트레이너
```
`audit.py`·`wild.py`·`trainers.py`·`grades.py`·`mkcharmap.py`는 pokegold-kr 디스어셈블리(github.com/Narishma-gb/pokegold-kr)를 읽는다. 받은 곳을 `POKEGOLD_KR=<경로>`로 알려 준다.

`romtest.py`는 처음 실행할 때 인트로를 지나가서 `work/intro.state`를 만든다. 롬이 바뀌면 `--intro`를 붙여 다시 만든다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `dmrom.py` | 롬 읽기. 표 위치를 **코드 모양(서명)으로 찾으므로** 2014판·2.0판 어느 쪽이든 그대로 쓸 수 있다 |
| `patch.py` | 「내 버전」 패치 만들기. 작은 SM83 어셈블러, 빈 곳 나눠 쓰기, 그림 넣기, 진화·포획 엔진 |
| `romtest.py` | 진화 7가지와 포획 막기를 실제 게임 화면 조작(가방 → 이상한사탕, 풀숲 → 몬스터볼)으로 시험 |
| `gblz.py` | 금·은 그림 압축 풀기 / 압축 |
| `krtext.py`, `charmap.json`, `mkcharmap.py` | 한글판 금 글자 부호 (pokegold-kr 디스어셈블리에서 만듦) |
| `grades.json`, `grades.py` | 롬의 디지몬 칸마다 공식 세대(유년기~궁극체), 포획 규칙에 씀. 이름으로 기억하므로 2.0판에서도 손으로 채운 값이 이어짐 |
| `wild.py` | 야생 출현표(풀숲 2개·물 1개)를 모양으로 찾아 읽음, 지명은 한글 |
| `trainers.py` | 트레이너 496명의 데리고 있는 종과 레벨 |
| `audit.py` | 롬 조사표 |
| `encounters.py` | 롬에서 종을 가리키는 곳 전부 (풀숲·물·대량발생·낚시·박치기 나무·벌레잡기 대회·트레이너·선물·고정 만남·경품·교환·떠돌이) 3,492곳 |
| `check.py` | 검수 보고서: 요약 + 규칙 R1~R12 ([X]/[OK]/[?]), `--full evo|party|wild` 로 표 |
| `parties.json` | 상대 파티 (C단계). 그림 대기 종은 그림이 올 때까지 다른 종 |
| `remap.py`, `mapping.csv` | A단계: 포켓몬·뺄 종 → 남길 디지몬. 계획종이 설치된 칸은 그대로, 야생은 레벨로 단계 낮춤 |
| `play.py` | PyBoy 실행·화면 찍기 |

## 찾은 표 (2014-11-13판 기준 파일 주소)

| 표 | 주소 |
|---|---|
| 능력치 (종마다 0x20바이트) | 0x51BDF |
| 그림 포인터 (종마다 6바이트) | 0x48000, 뱅크 바꿈 표 0x5194C {13→1F, 14→20, 1F→2E} |
| 팔레트 (종마다 8바이트) | 0xAD0D |
| 이름 (10바이트 = 한글 5자) | 0x1B0C4A |
| 진화·기술 포인터 | 0x423ED (뱅크 10) |
| 진화 엔진 EVOLVE_STAT 갈래 | 0x41E8A (뱅크 10:5E8A) |
| 포획 판정 `call Random` | 0xEA0C (뱅크 3) |
| 메뉴 아이콘 / 울음소리 / 도감 포인터 | 0x8E96D / 0xF2747 / 0x442FF (뱅크 68·69) |
| 야생 풀숲 (성도·관동) / 물 | 0x2AC1A ×61, 0x2B8A5 ×30 / 0x2BE28 ×24 |
| 완전히 빈 뱅크 | 75, 76, 77, 7C, 7D |

## 내 버전 v0.1에 들어간 것

1. 새 진화 종류 6~10: 유대 높음 / 유대 낮음 / 자기 문장 / 암흑(문장은 있지만 자기 것이 아님) / 아무 문장
2. 문장 = 배지 8개: 사랑(비상) 지식(호일) 순수(꼭두) 빛(유빈) 우정(규리) 용기(사도) 성실(류옹) 희망(이향)
3. 포획: 성숙기 이상(95종)은 몬스터볼로 못 잡음
4. 코로몬 추가(꼬리선 자리, 29번 도로 야생) → Lv11 아구몬. 메뉴 아이콘·울음소리(아구몬 울음을 높게)·도감(공식 설명 바탕, 렛서형)까지
5. 디지몬스터 버그 고침: 메탈가루몬 진화 목록 끝 표시가 없어 엉뚱한 진화가 섞이던 것, 원뿔몬 통신 진화(혼자 못 함) → 문장 진화

시험 결과(`romtest.py`): 진화 7/7, 포획률 0 → 10번 던져 0번, 포획률 255 → 10번 중 2~3번 잡힘.
