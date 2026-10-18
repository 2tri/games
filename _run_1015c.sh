set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude"
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; P=games/digimon/art/src/people; T=수정판_시험
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/r$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/r$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/r$n.txt | cut -c1-120)"; }
IN=hg4t_out/hg4t_test.nds
[ -f "$IN" ] || IN=hg4f_out/hg4f_test.nds
run t1 python $T/inject_front.py $IN _a1.nds
run t2 python $T/inject_back.py _a1.nds _a2.nds
run t3 python $T/inject_walk.py _a2.nds _a3.nds --sheet $P/taichi_walk_4x3.png --layout tile
run n1 python $T/inject_front.py _a3.nds _a4.nds --portrait $P/hikari_portrait_ai.png --members 17,18,19,20 --pal 21 --no-card
run n2 python $T/inject_back.py _a4.nds _a5.nds --back $P/hikari_back_ds_ai.png --groups 16,1
run n3 python $T/inject_walk.py _a5.nds _a6.nds --sheet $P/hikari_walk_4x3.png --layout tile --target 70
run it python $T/inject_items.py _a6.nds _a7.nds
run ti python $T/inject_title.py _a7.nds _a8.nds
run bd python $T/inject_badges.py _a8.nds _a9.nds
run ro python $T/inject_roamer.py _a9.nds _a10.nds
run op python $T/inject_otherpoke.py _a10.nds _a11.nds --base "$ROM"
run bw python $T/inject_bwg_fix.py _a11.nds _a12.nds
cp _a12.nds 최종_오늘.nds
echo PART3DONE
