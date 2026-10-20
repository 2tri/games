#!/usr/bin/env python3
"""python 요약화면.py <롬(연구소 스크립트가 「요약 화면」으로 바뀐 사본)> <출력 폴더> <종 번호,...|all> [레벨=50] [--shard i/n] — 종마다 내 첫 마리로 넣고 요약 화면(메모·능력치·기술)을 찍음
        롬 만들기: python mkscript.py <롬> <출력> "6001 00 0000 0000"   (스크립트 명령 352 = 요약 화면, 연구소 진입점을 덮어씀 — 시험용 사본)
        이유: 연구소 저장 상태에서는 X 메뉴 아이콘 터치가 열리지 않아, 스크립트 명령으로 요약 화면을 직접 띄움(10/20)."""
import sys, os, json, struct
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.abspath(os.path.join(H, '..', '..')))
import pkm, hg1
from hg1 import NDS, NARC
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
rom_path, out, spec = sys.argv[1], sys.argv[2], sys.argv[3]
args = [a for a in sys.argv[4:] if not a.startswith('--')]; LV = int(args[0]) if args else 50
shard = [a for a in sys.argv if a.startswith('--shard')]
si, sn = (map(int, sys.argv[sys.argv.index('--shard') + 1].split('/')) if '--shard' in sys.argv else (0, 1))
os.makedirs(out, exist_ok=True)
data = json.load(open(os.path.join(H, '..', '..', '포켓몬', '디지몬_표_자료.json'), encoding='utf-8'))
S = {s['id']: s for s in data['species']}
ids = sorted(S) if spec == 'all' else [int(x) for x in spec.split(',')]
R = NDS(open(rom_path, 'rb').read()); personal = NARC(R.get(hg1.NARC_PATHS['personal'])).files
W = NARC(R.get('a/0/1/1')).files; PPD = {i: W[i][6] for i in range(len(W)) if len(W[i]) > 6}
emu = DeSmuME(); emu.open(rom_path); emu.volume_set(0)
DST = os.environ.get('AG4', os.path.join(H, 'ag4.dst'))
def run(n):
    for _ in range(n): emu.cycle(False)
def press(k, hold=4, gap=40):
    m = keymask(k); emu.input.keypad_add_key(m); run(hold); emu.input.keypad_rm_key(m); run(gap)
def walk(k, n):
    m = keymask(k); emu.input.keypad_add_key(m); run(16 * n); emu.input.keypad_rm_key(m); run(10)
ADDRS = (0x0227cce8, 0x022bc958)
for k, sp in enumerate(ids):
    if k % sn != si: continue
    emu.savestate.load_file(DST); run(5); walk(Keys.KEY_LEFT, 1); press(Keys.KEY_A); run(300)
    tmpl = bytes(emu.memory.unsigned[ADDRS[0]:ADDRS[0] + 236]); growth = personal[sp][19]
    mv = [m['id'] for m in S[sp]['moves'] if m['lv'] <= LV][-4:] or [33]
    new = pkm.make_mon(tmpl, sp, LV, mv, personal, 0, pp=PPD)
    for a in ADDRS:
        for i, b in enumerate(new): emu.memory.unsigned[a + i] = b
    walk(Keys.KEY_RIGHT, 1); walk(Keys.KEY_UP, 1); press(Keys.KEY_A); run(200)
    emu.screenshot().save('%s/s%03d_p1.png' % (out, sp))
    press(Keys.KEY_RIGHT, 4, 60); emu.screenshot().save('%s/s%03d_p2.png' % (out, sp))
    print('done', sp, S[sp]['name'], mv, flush=True)
