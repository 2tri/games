# games

폰 홈 화면에 추가해서 인터넷 없이 하는 웹 게임 모음. 설치할 것 없이 파일만으로 동작한다.

| 폴더 | 게임 | 내용 |
|---|---|---|
| `2048/` | 쑥쑥 2048 | 같은 과일을 합쳐 👶를 만드는 2048 퍼즐 |

## 폴더 하나의 구성

- `index.html` — 게임 전체 (CSS·JS 포함)
- `manifest.json` — 홈 화면 이름·아이콘
- `sw.js` — 오프라인 캐시. **`index.html`을 고치면 `VERSION` 값도 바꿔야** 폰이 새 파일을 받는다
- `icon-180/192/512.png`

## 저장

진행·별점·도감·최고 점수는 그 폰의 브라우저 저장소(localStorage)에만 남는다. 홈 화면 앱을 지우면 같이 지워질 수 있다.

## 앱 주소 켜기 (처음 한 번)

저장소 Settings → Pages → Source 「Deploy from a branch」 → Branch `main` / `(root)` → Save.
1~2분 뒤 `https://2tri.github.io/games/` 에서 열린다.
