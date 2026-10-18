set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude"
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/r$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/r$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/r$n.txt | cut -c1-120)"; }
bash _run_1015c.sh > _로그/run_c.txt 2>&1
tail -2 _로그/run_c.txt
run 9b python hg_hard.py 최종_오늘.nds --out 최종_하드.nds
run 11d python _hg3_작업/hg_song.py 최종_오늘.nds --out 최종_노래.nds
run 11dh python hg_hard.py 최종_노래.nds --out 최종_하드_노래.nds
echo PART4DONE
