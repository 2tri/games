#!/bin/sh
# 롬 만들기: sh build.sh <gbdk 폴더> <Galmuri9.ttf>  →  ring.gbc
set -e
cd "$(dirname "$0")"
G=$1; FONT=$2
python3 gen.py "$FONT"
mkdir -p obj
for f in src/*.c; do
  b=$(basename "$f" .c)
  $G/bin/lcc -Wm-yC -c -o obj/$b.o "$f"
done
$G/bin/lcc -Wm-yC -Wl-yt0x19 -Wl-yo8 -Wm-yn"RING QUEST" -o ring.gbc obj/*.o
ls -l ring.gbc
