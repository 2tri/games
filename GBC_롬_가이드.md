# 게임보이 컬러(GBC) 롬 만들기 안내 — 디지몬·반지 원정 공통

**목표**: 아이폰 **Delta 에뮬레이터**에서 여는 `.gbc` 롬. 십자키·A·B·START·SELECT·저장·화면 크기는 Delta가 다 해 주므로, 만들 것은 **160×144 게임 화면 안의 내용뿐**이다. 웹판은 이야기·전투·밸런스를 빠르게 확인하는 시험판으로만 쓴다.

## 이미 확인된 것 (반지 원정 세션, 2026-10-01)
- 컴파일러: **GBDK-2020 4.4.0** — `https://github.com/gbdk-2020/gbdk-2020/releases/download/4.4.0/gbdk-linux64.tar.gz` (허용 도메인에 `github.com`, `*.githubusercontent.com` 필요 — 이미 추가됨)
- 시험 롬: `ring/rom/ring_test.gbc` (전투 화면 2장, A로 넘김). 빌드: `ring/rom/build_test.py` + `ring/rom/main.c`
  - `lcc -Wm-yC -Wm-yn"이름" -o 롬.gbc main.c tiles.c` (`-Wm-yC` = GBC 전용)
- 실행 확인: `pip install pyboy` → `PyBoy('롬.gbc', window='null', cgb=True)` 로 화면 캡처 (Delta 없이 검증)
- 한글: 갈무리9 글꼴을 TTF로 바꿔(`fontTools`로 woff2→ttf) 파이썬에서 화면 그림에 직접 찍은 뒤 8×8 타일로 변환. 실제 게임은 **대사에 쓰인 글자만** 8×16 타일로 뽑아 넣는 방식이 필요.

## 규칙 (그림·화면을 만들 때 지킬 것)
1. 그림은 **8의 배수 크기** (8×8 타일 단위). 적 앞모습 최대 64×64, 내 쪽 뒷모습 최대 80×80.
2. 한 화면에 쓰는 **서로 다른 타일 수**: VRAM 1칸에 256개(배경). GBC는 2칸이라 넘치는 타일은 **VRAM bank 1** 에 두고, 타일 속성(attribute) 3번 비트(값 8)를 켜면 된다 (`VBK_REG = 1; set_bkg_tiles(...)`). 반지 원정 시험 롬이 260타일로 이 방식을 씀.
3. 색: GBC는 배경 팔레트 8개 × 4색. 반지 원정은 회색 4단계(흰·밝은회·어두운회·검정)로 통일 중. 디지몬처럼 대표색이 있으면 그림마다 팔레트를 따로 주면 된다.
4. 저장: 배터리 저장(SRAM, MBC5 등)으로 하면 Delta에서도 유지됨 (`-Wl-yt0x1B -Wl-ya1` 등 — 실제 적용 시 확인 필요, **불확실함**).

## 그림 만드는 방식 (반지 원정에서 정착)
- 사용자가 이미지 AI(ChatGPT·제미나이)로 "Pokemon Gold and Silver Game Boy battle sprite, pixel art, 4 shades of gray, white background" 류의 도트풍 그림을 만들어 줌
- `ring/tools/snap.py`(칸 주기 자동 검출 → 진짜 도트 칸 → 4단계) + `ring/tools/ingest.py`(잡티 제거·크기 맞춤·게임 데이터 갱신)로 정리
