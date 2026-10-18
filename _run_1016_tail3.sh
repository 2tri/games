set -e
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude"
ROM="포켓몬/1_폰에 넣을 파일/디지몬골드 v1.6 (이지).nds"; T=수정판_시험
run(){ n=$1; shift; s=$(date +%s); "$@" > _로그/m$n.txt 2>&1 || { echo "[$n] FAIL ($(( $(date +%s)-s ))s)"; tail -8 _로그/m$n.txt; exit 1; }; echo "[$n] ok $(( $(date +%s)-s ))s: $(tail -1 _로그/m$n.txt | cut -c1-110)"; }
run op python $T/inject_otherpoke.py 최종_오늘.nds _a13.nds --base "$ROM"
cp _a13.nds 최종_오늘.nds
run 9b python hg_hard.py 최종_오늘.nds --out 최종_하드.nds
run 11d python _hg3_작업/hg_song.py 최종_오늘.nds --out 최종_노래.nds
run 11dh python hg_hard.py 최종_노래.nds --out 최종_하드_노래.nds
echo TAILDONE
