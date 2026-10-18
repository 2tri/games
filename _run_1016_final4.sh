set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude"
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; T=수정판_시험
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/k$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/k$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/k$n.txt | cut -c1-110)"; }
cp NDS_*.tsv _hg3_작업/
python _scratch/patch_item.py > /dev/null
run 4 python art_nds.py dsw_ow 그림_보충 "games/images/digimon" "games/digimon/art/src" --out nds_art
run fb python $T/fix_black.py
run sh python $T/art_sharpen.py --src 머미몬=games/images/digimon/mummymon-ds-f.png --src 아마게몬=games/images/digimon/armagemon-wk-f.png
run 5 python hg2.py "$ROM"
run 6 python _hg3_작업/hg3.py hg2_out/hg2_test.nds --base "$ROM"
run 8 python _hg3_작업/hg4.py hg3_out/hg3_test.nds nds_art --base "$ROM"
run 8b python hg4_icons.py hg4_out/hg4_test.nds nds_art --base "$ROM" --paltab arm9:0x10023B --dex-order NDS_도감순서.tsv
run 8b2 python hg_event.py hg4i_out/hg4i_test.nds --base "$ROM" --apply
run 8c python _hg3_작업/hg4_follow.py hg_ev_out/hg_ev_test.nds nds_art --base "$ROM"
run 9a python hg4_trainer.py hg4f_out/hg4f_test.nds "games/digimon/art/src/people" --base "$ROM"
bash _run_1015c.sh > _로그/k_c.txt 2>&1; tail -1 _로그/k_c.txt
run 9b python hg_hard.py 최종_오늘.nds --out 최종_하드.nds
run 11d python _hg3_작업/hg_song.py 최종_오늘.nds --out 최종_노래.nds
run 11dh python hg_hard.py 최종_노래.nds --out 최종_하드_노래.nds
echo FINAL4DONE
