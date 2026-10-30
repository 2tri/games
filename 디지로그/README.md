# 디지로그 (포케로그 × 디지골드)

포케로그(오픈소스 포켓몬 로그라이트, AGPL)를 바탕으로 포켓몬 자리에 디지몬골드의 디지몬 188종을 넣은 개인용 팬 게임.

## 구성
- `data/digimon.json`, `data/sprites/` : 디지골드 롬에서 뽑은 디지몬 자료(칸 번호·능력치·타입·특성·기술·진화)와 전투 그림
- `tools/gen_digimon.py` : 자료 → 포케로그 소스(종 데이터 TS, 이름·기술·타입·진화 도구 번역, 그림·아이콘)
- `tools/gen_ui.py` : 타입 표시 그림, 사탕 색, 화면 문구(포켓몬→디지몬)
- `tools/prune_dist.py` : 배포판에서 안 쓰는 포켓몬 그림 지우기 + 배경음악 64kbps
- `digilog-src.patch` : 포케로그 코드 변경분(`POKEROGUE_BASE.txt` 커밋 기준)

## 다시 만들기
```
git clone https://github.com/pagefaultgames/pokerogue.git src && cd src
git checkout $(cat ../POKEROGUE_BASE.txt) && git submodule update --init --depth 1
git apply ../digilog-src.patch
npx pnpm@10.34.5 install --frozen-lockfile
cd .. && python tools/gen_digimon.py && python tools/gen_ui.py
cd src && npx pnpm@10.34.5 build && cd .. && python tools/prune_dist.py   # → src/dist
```
개발 중 확인: `cd src && npx pnpm@10.34.5 start:dev --port 8000`

## 바꾼 규칙
- 디지골드에서 디지몬이 들어간 하트골드 칸(1~493번)에 같은 번호로 덮어씀. 기술·특성 번호는 포켓몬 것 그대로(이름만 디지골드 한글)
- 디지몬이 아닌 포켓몬은 시작·알 목록에서 빠지고, 적으로 나오면 같은 무게(단계·종족값)의 디지몬으로 바뀜(`digimonize`)
- 진화: 기본 갈래 하나는 레벨 진화, 나머지 갈래는 속성별 진화칩(백신·데이터·바이러스·프리), 궁극의 문장·디지멘탈·어둠의 돌 등은 이름 그대로 진화 도구
- 타입: 디지골드 이름(빛=페어리 자리, 화염·식물·번개·바람·대지·암석·곤충·기계·용·암흑)
