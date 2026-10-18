set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude"
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; P=games/digimon/art/src/people; T=수정판_시험
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/c$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/c$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/c$n.txt | cut -c1-110)"; }
run 5 python hg2.py "$ROM"
run 6 python hg3.py hg2_out/hg2_test.nds --base "$ROM"
run 8 python hg4.py hg3_out/hg3_test.nds nds_art --base "$ROM"
run 8b python hg4_icons.py hg4_out/hg4_test.nds nds_art --base "$ROM" --paltab arm9:0x10023B --dex-order NDS_도감순서.tsv
run 8b2 python hg_event.py hg4i_out/hg4i_test.nds --base "$ROM" --apply
run 8c python hg4_follow.py hg_ev_out/hg_ev_test.nds nds_art --base "$ROM"
run 9a python hg4_trainer.py hg4f_out/hg4f_test.nds "games/digimon/art/src/people" --base "$ROM"
echo PART_A2_DONE
