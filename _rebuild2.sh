set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; P=games/digimon/art/src/people; T=수정판_시험
run(){ n=$1; shift; "$@" > _로그/q$n.txt 2>&1 || { echo "[$n] FAIL"; tail -5 _로그/q$n.txt; exit 1; }; echo "[$n] ok: $(tail -1 _로그/q$n.txt | cut -c1-100)"; }
run 4 python art_nds.py dsw_ow 그림_보충 "games/images/digimon" "games/digimon/art/src" --out nds_art
run fb python $T/fix_black.py
run 8 python hg4.py hg3_out/hg3_test.nds nds_art --base "$ROM"
run 8b python hg4_icons.py hg4_out/hg4_test.nds nds_art --base "$ROM" --paltab arm9:0x10023B --dex-order NDS_도감순서.tsv
run 8b2 python hg_event.py hg4i_out/hg4i_test.nds --base "$ROM" --apply
run 8c python hg4_follow.py hg_ev_out/hg_ev_test.nds nds_art --base "$ROM"
run 9a python hg4_trainer.py hg4f_out/hg4f_test.nds "games/digimon/art/src/people" --base "$ROM"
run t1 python $T/inject_front.py hg4t_out/hg4t_test.nds _a1.nds
run t2 python $T/inject_back.py _a1.nds _a2.nds
run t3 python $T/inject_walk.py _a2.nds _a3.nds
run n1 python $T/inject_front.py _a3.nds _a4.nds --portrait $P/hikari_portrait_ai.png --members 17,18,19,20 --pal 21 --no-card
run n2 python $T/inject_back.py _a4.nds _a5.nds --back $P/hikari_back_ds_ai.png --groups 16,1
run n3 python $T/inject_walk.py _a5.nds _a6.nds --sheet $P/hikari_walk_ds_ai.png --target 70
run it python $T/inject_items.py _a6.nds _a7.nds
run ti python $T/inject_title.py _a7.nds _a8.nds
run wr python $T/fix_wild_rare.py _a8.nds 최종_오늘.nds --report 야생_귀한종_고침.txt
run hd python hg_hard.py 최종_오늘.nds --out 최종_하드.nds
run sg python hg_song.py 최종_오늘.nds --out 최종_노래.nds
run sh python hg_hard.py 최종_노래.nds --out 최종_하드_노래.nds
echo ALLDONE
