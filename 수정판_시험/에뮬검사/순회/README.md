# 스토리 순회 도구 (2026-10-20)
지도 이동(스크립트 Warp)으로 NPC 앞·칸 이벤트 자리에 바로 도착해 대화·전투를 끝까지 자동 진행하고 화면을 찍는다(걷지 않음).
- `mkstages.py` → stages.json (NPC·표지판 스크립트에서 선물 종/도구·고정 전투·트레이너 찾기, 169곳)
- `mkstages2.py` → stages2.json (레벨 스크립트 장면 109 + 칸 이벤트 197, 변수 미리 세팅)
- `stage_play.py` 한 장면 실행(Lv100 파티로 전투 자동, 대화 쪽마다 화면) · `stage_driver.py`/`stage_driver2.py` 4개 병렬 순회 · `sheet.py` 확인용 시트 · `rep.py` 요약
- 경로는 시험 때 작업 폴더(rom.nds=최종 롬, start.dst=연구소 저장 상태, ../hdr.json=지도 머리말 표) 기준 — 쓰려면 맞춰서 바꿀 것
- 결과: `결과_이벤트169.jsonl`, `결과_장면306.jsonl`
