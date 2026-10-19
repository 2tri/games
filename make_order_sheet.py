"""개인 계정 Claude 에게 붙일 「NDS 그림 주문서」 아티팩트 만들기 글 → ../넘길것_NDS주문서.md
기준: DG_받을목록_표.md(136종, 디지골드에 없는 종만) + DG_대조표.md(이미 있는 66종) + 10/8 주문문(고침 1~5 반영판)."""
import os, re
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
# 10/12 고침1(디지골드 화풍): 앞모습 키를 키우고, 걷기도 큰 종은 조금 크게
PX = {'유년기Ⅱ': 40, '유년기': 40, '성장기': 52, '성숙기': 64, '아머체': 64, '완전체': 72, '궁극체': 76}
SIZE = {'유년기Ⅱ': 20, '유년기': 20, '성장기': 20, '성숙기': 24, '아머체': 24, '완전체': 26, '궁극체': 28}   # 디지골드 걷기 그림 크기(32칸)
rows = []; group = ''
for line in open(os.path.join(P, 'DG_받을목록_표.md'), encoding='utf-8'):
    m = re.match(r'^## (\S+)', line)
    if m: group = m.group(1); continue
    c = [x.strip() for x in line.strip().strip('|').split('|')]
    if len(c) == 7 and c[0].isdigit():
        n, ko, en, fid, gr, need, memo = c
        baby = '걷기=알' in need
        rows.append('|'.join([n, group, ko, en, fid, gr.replace('Ⅱ', ''), str(PX.get(gr, 64)), '-' if baby else str(SIZE.get(gr, 40)),
                              '앞·뒤' if baby else '앞·뒤·걷기', memo]))
assert len(rows) == 123, len(rows)   # 10/12: 유년기 13종 뺌
dg = open(os.path.join(P, 'DG_대조표.md'), encoding='utf-8').read()
have = dg.split('## 디지골드에 있음', 1)[1].split('\n')[1].strip()
same = dg.split('이름이 내 설계와 다른 것:', 1)[1].split('\n')[0].strip()

doc = '''# NDS 그림 주문서 — 개인 계정 Claude 에게 붙이는 글 (2026-10-12)

아래대로 **새 아티팩트 「NDS 그림 주문서」를 하나 만들어 줘.** 예전 「NDS 그림 정리」(205종)와 「디지몬 그림 정리」는 건드리지 마.
설명은 짧게, 만드는 데만 집중하고 다 만들면 「만들었어」 한 마디만 답해. 그림 파일을 열어 보거나 깃허브를 읽지 마(지금은 만들기만).

## 왜 새로 만드나
예전 「NDS 그림 정리」는 디지골드 목록을 알기 전에 만들어서, 디지골드에 이미 있는 종이 섞여 있었다.
이번 목록은 디지골드 제작자 엑셀과 대조해 **디지골드에 없는 123종만(10/12: 유년기는 뺌, 성장기부터)** 담았다. 이 136종만 그림을 받는다.

## 화면 (휴대폰에서 쓰기 좋게, 한국어)
1. 맨 위
   - 진행: 「받은 그림 n / 전체」(종마다 받을 그림 수만큼 셈: 앞·뒤·걷기면 3, 앞·뒤면 2).
   - 받는 순서 안내 한 줄: 「제미나이 새 채팅 하나에서: ① 공식 그림 첨부 + 앞 주문 → ② 뒤 주문(첨부 없음) → ③ 걷기 주문(첨부 없음)」
   - 우선순위 한 줄: 「① → ② 먼저. ⚑ 표시는 1부에서 일찍 쓰이니 ③·④보다 먼저. 못 받은 종은 GBC 그림이 대신 들어가니 다 못 받아도 게임은 돌아감」
2. 거르기: 묶음(①~⑤), 「⚑ 먼저만」, 「아직 안 받은 것만」, 이름 검색.
3. 종마다 카드 한 장 (번호 순서 그대로)
   - 위: 번호, 한글 이름, 영어 이름, 단계, 메모. 메모에 「⚑」가 있으면 눈에 띄게.
   - 그림마다 한 줄씩(유년기는 앞·뒤 두 줄만, 「걷기 = 공용 알 그림이라 안 받음」 한 줄 표시):
     | 줄 | 그림 | 버튼 ① | 버튼 ② | 체크 |
     |---|---|---|---|---|
     | 1 | 앞 (DS 배틀) | 「주문문 복사」(주문문 A) | 「이름 복사: <id>-ds-f.png」 | 받음 |
     | 2 | 뒤 (DS 배틀) | 「주문문 복사」(주문문 B) | 「이름 복사: <id>-ds-b.png」 | 받음 |
     | 3 | 걷기 (맵) | 「주문문 복사」(주문문 C) | 「이름 복사: <id>-ow.png」 | 받음 |
   - 이름 복사 버튼에는 복사될 파일 이름을 글자 그대로 보여 준다.
   - 복사가 막히면 글 상자를 띄워 길게 눌러 복사하게.
   - 「받음」 체크는 아티팩트 저장소에 저장(다시 열어도 유지). 카드 위에 「n / 3장」.
4. 맨 아래 접는 칸 세 개
   - 「디지골드에 이미 있음 — 받지 말 것」: 아래 목록 그대로.
   - 「꼭 볼 것 / 무시할 것」: 아래 검사 기준 그대로.
   - 「집에서 올리는 순서」: 아래 그대로.

## 주문문 ({EN_NAME}, {PX}, {SIZE} 만 그 종의 값으로 바꿈)

### 주문문 A — 앞 (공식 그림을 첨부해서)
```
Attached: a picture of {EN_NAME}, a Digimon. Keep this exact character: same design, same parts, its official colors.

Draw it as a FRONT battle sprite for a Nintendo DS-era monster RPG.
- ONE square image, pure white background, nothing else.
- The character faces slightly to the left (3/4 view), whole body visible, standing near the bottom, filling about 85% of the image height.
- Pixel art: the character is only about {PX} pixels tall. Every pixel is a crisp square of the same size. Dark outline, simple cel shading with 2-3 shades per color, at most 15 colors in total. No anti-aliasing, no blur, no gradients, no dithering, no ground shadow.
- Only the body parts this character really has.
- Leave an empty white margin of at least 12% on all four edges.
- No text, no frame, no grid lines.
```

### 주문문 B — 뒤 (앞을 받은 같은 채팅에서, 첨부 없이)
```
Good. Now draw the BACK battle sprite of the same character, in exactly the same pixel style, size and colors as the front sprite above.
Three-quarter rear view: we see its back and the back of its head, it faces away toward the upper-right. No face visible. Not a mirror of the front. No marks or patterns on the back unless the character really has them.
One image, pure white background, empty white margin of at least 12% on all edges. No text.
```

### 주문문 C — 걷기 (같은 채팅에서, 첨부 없이)
```
Good. Now make a small OVERWORLD sprite set of the same character, same colors, in the same pixel style but much smaller and cuter, like a character that follows the player on a town map.
Keep the face exactly like the battle sprite above: same eye color, same eye shape. Make the eyes and other key features big and bright so they stay visible at a very small size. No extra details such as a mouth or pupils unless the battle sprite has them.
4 poses in 2 columns x 2 rows: top-left facing DOWN (face visible), top-right facing UP (back only, no face), bottom-left facing LEFT, bottom-right facing RIGHT (side views show only ONE eye).
Each pose about {SIZE} pixels tall, all the same size. Only the body parts it really has. Pure white background, wide gaps between poses, empty white margin of at least 15% on all edges. No text, no grid lines, no shadow.
```

### 잘 안 나올 때 덧붙일 문장 (카드 맨 아래 접는 칸, 각각 복사 버튼)
1. `Use its official colors, not gray.`
2. `There must be exactly 4 separate poses in 2 columns and 2 rows.`
3. `The bottom-right pose is the mirror image of the bottom-left pose.`
4. `It is {EN_NAME} from Digimon Adventure, not any other creature.`
5. `Make it much lower resolution, like a tiny 1990s sprite.`
※ 「Pokemon」이라는 말은 어디에도 넣지 않는다(디자인이 포켓몬 쪽으로 바뀜).

## 검사 기준
- 꼭 볼 것: 다른 몬스터로 바뀜 · 회색 · 뒷모습에 얼굴이 보임 · 걷기 방향이 틀림(옆모습에 눈 둘) · 없는 발·꼬리가 붙음 · 몸에 이상한 얼룩·무늬 · 오른쪽 아래 반짝이가 몸에 겹침 → 같은 채팅에서 다시 요청.
- 무시할 것: 크기·해상도 차이(스크립트가 맞춤) · 앞모습이 정면을 봄(덩어리형은 자연스러움) · jpg 로 받은 것(이름만 .png 로 바꾸면 됨).

## 집에서 올리는 순서
1. 받은 그림 이름을 카드의 「이름 복사」 그대로 바꾼다(윈도우가 확장자를 숨기면 `.png.png` 가 되지 않게).
2. github.com/2tri/games → 브랜치 main → `images/digimon` → Add file → Upload files → Commit directly to main.
3. 크기·색 줄이기, 걷기 칸 자르기는 NDS 스크립트가 하니 손대지 않는다.

## 디지골드에 이미 있음 — 받지 말 것 (66종)
''' + have + '''
이름이 내 설계와 다른 것(같은 디지몬): ''' + same + '''
포요몬은 디지골드에 있지만 게임에서 뺐다.

## 받을 종 123 (번호|묶음|한글|영어 EN_NAME|id|단계|PX|SIZE|받을 그림|메모) — 이 순서 그대로 카드로
- 번호는 사용자가 이미 쓰고 있는 번호라 바꾸지 않는다.
- 묶음: ① 먼저(주요 인물·맵 등장) ② 다음(스타팅·파트너 줄) ③ 1부 야생·트레이너·보스 ④ 2부 ⑤ 추가(파트너 줄 궁극체 등)
''' + '\n'.join(rows) + '\n'
# 주문문 A·B·C 와 「잘 안 나올 때」는 고침1 글에서 가져옴(두 글이 어긋나지 않게)
fix = open(os.path.join(P, '넘길것_NDS주문서_고침1.md'), encoding='utf-8').read()
new_prompts = fix.split('## 2. 주문문 A·B·C 를 아래로 통째로 바꾸기', 1)[1].split('## 3.', 1)[0].strip('\n')
a = doc.index('### 주문문 A'); b = doc.index('### 잘 안 나올 때')
doc = doc[:a] + new_prompts + '\n\n' + doc[b:]
doc = doc.replace('5. `Make it much lower resolution, like a tiny 1990s sprite.`',
                  '5. (걷기 그림이 너무 복잡할 때만) `Make the walking sprites simpler, with fewer details.`\n'
                  '6. `Use smaller pixels and more detail, like a polished Nintendo DS sprite, not a chunky retro sprite.`\n'
                  '7. `The back sprite must be bigger than the front sprite and cut off at the bottom.`')
assert 'chunky retro' in doc and '96 x 96' in doc
out = os.path.join(P, '넘길것_NDS주문서.md')
open(out, 'w', encoding='utf-8', newline='\n').write(doc)
print(len(doc.encode('utf-8')), '바이트', len(rows), '종')
