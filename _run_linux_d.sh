set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; P=games/digimon/art/src/people; T=수정판_시험
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/d$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/d$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/d$n.txt | cut -c1-110)"; }
IN=hg4t_out/hg4t_test.nds
[ -f "$IN" ] || IN=hg4f_out/hg4f_test.nds
run t1 python3 $T/inject_front.py $IN _a1.nds
run t2 python3 $T/inject_back.py _a1.nds _a2.nds
run t3 python3 $T/inject_walk.py _a2.nds _a3.nds --sheet $P/taichi_walk_4x3.png --layout tile
run n1 python3 $T/inject_front.py _a3.nds _a4.nds --portrait $P/hikari_portrait_ai.png --members 17,18,19,20 --pal 21 --no-card
run n2 python3 $T/inject_back.py _a4.nds _a5.nds --back $P/hikari_back_ds_ai.png --groups 16,1
run n3 python3 $T/inject_walk.py _a5.nds _a6.nds --sheet $P/hikari_walk_4x3.png --layout tile --target 70
run it python3 $T/inject_items.py _a6.nds _a7.nds
run ti python3 $T/inject_title.py _a7.nds _a8.nds
run bd python3 $T/inject_badges.py _a8.nds _a9.nds
run ro python3 $T/inject_roamer.py _a9.nds _a10.nds
run an python3 $T/inject_animfix.py _a10.nds _a11.nds
run gr python3 $T/inject_ground.py _a11.nds _a11g.nds                      # 10/19 전투 그림 높이(바닥에서 뜨는 것)
run ty python3 $T/inject_typeicons.py _a11g.nds _a11t.nds                    # 10/20 타입 글자판 그림(불꽃→화염 등 11장)
run dc python3 $T/inject_dexchips.py _a11t.nds _a11d.nds                    # 10/20 도감 화면 타입 칩 그림(11장)
run at python3 hg_attr.py _a11d.nds _a12.nds --base "$ROM"      # 10/19 속성 상성(백신>바이러스>데이터>백신, ×1.2/×0.8)
run nm python3 $T/inject_names.py _a12.nds _a13.nds                         # 10/20 7글자 종 이름 2개를 6글자로(이름판에서 잘림)
run kl python3 $T/inject_kantolab_trigger.py _a13.nds _a14.nds              # 10/20 관동 연구소(2부 시작) 입장하면 장면 시작 + 스타팅 레벨 45 전부
run gt python3 $T/inject_gatomon_wild.py _a14.nds _a15.nds                    # 10/20 가트몬을 2부 시작 야생(관동 1·2·3번도로 10%)에
run eg python3 $T/inject_egg_species.py _a15.nds _a16.nds                       # 10/20 조수의 알이 포요몬이 아니라 토코몬으로 부화(오버레이 1 코드)
cp _a16.nds 최종_오늘.nds
run rc1 python3 rom_check.py 최종_오늘.nds --base "$ROM" --out 롬검사_오늘.txt
run 9b python3 hg_hard.py 최종_오늘.nds --out 최종_하드.nds
run 11d python3 hg_song.py 최종_오늘.nds --out 최종_노래.nds
cp 노래_배정결과.txt _로그/노래_배정결과_오늘.txt
run 11dh python3 hg_song.py 최종_하드.nds --out 최종_하드_노래.nds
run rc2 python3 rom_check.py 최종_하드.nds --base "$ROM" --out 롬검사_하드.txt
run rc3 python3 rom_check.py 최종_노래.nds --base "$ROM" --out 롬검사_노래.txt
run rc4 python3 rom_check.py 최종_하드_노래.nds --base "$ROM" --out 롬검사_하드_노래.txt
echo PART_B_DONE
