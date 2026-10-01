#!/bin/sh
# 롬 만들기: sh build.sh <gbdk 폴더> <Galmuri9.ttf>  →  ring.gbc
# 은행: 0 코드 · 1 글꼴 · 2 전투·자료표 · 3~7 그림 · 8~ 이야기
set -e
cd "$(dirname "$0")"
G=$1; FONT=$2
node story.js 8          # index.html 의 이야기 → src/story_*.c
python3 gen.py "$FONT"   # 자료·그림·글꼴(쓰인 글자만) → src/data.c, spr*.c, font.c
rm -rf obj; mkdir -p obj
for f in src/*.c; do
  b=$(basename "$f" .c)
  $G/bin/lcc -Wm-yC -c -o obj/$b.o "$f"
done
$G/bin/lcc -Wm-yC -Wm-yt0x1B -Wm-ya1 -Wm-yo16 -Wm-yn"RING QUEST" -Wl-m -o ring.gbc obj/*.o
grep -E "^_CODE |^_HOME |^_DATA " ring.map
ls -l ring.gbc
