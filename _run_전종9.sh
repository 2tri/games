export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
cd "C:/Users/skagn/OneDrive/Desktop/claude/수정판_시험/게임화면"
for b in "$@"; do
  python 전종_확인.py ../../_emu_rom9.nds ../../게임화면_오늘/d1015b/out5.dst $b ../../화면_전종_v11 2>&1 | tail -1
done
echo DONE
