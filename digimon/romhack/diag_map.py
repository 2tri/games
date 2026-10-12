"""맵 하나 불러오기 진단 (10판, 12판: DIAG_ROM 으로 다른 롬도):
  python3 diag_map.py 25 4 8 17
  DIAG_ROM=work/base.gbc python3 diag_map.py 25 4 8 17      → 원본 롬으로 같은 시험 (work/intro_base.state 를 처음 한 번 만듦)
단계마다 화면을 work/shots/diag_<롬>_NN.png 로 남기고 맵·좌표·PC 를 찍음. timeout 과 같이: timeout 300 python3 diag_map.py 25 4 8 17"""
import sys, os
import dmrom, romtest
from romtest import put_party, MAP_GROUP, MAP_NUM, XC, YC

g, n, x, y = map(int, sys.argv[1:5])
state = 'intro.state'
if os.environ.get('DIAG_ROM'):
    romtest.ROM = os.path.abspath(os.environ['DIAG_ROM'])
    state = 'intro_%s.state' % os.path.splitext(os.path.basename(romtest.ROM))[0]
    if not os.path.exists(os.path.join(romtest.W, state)):
        _save = romtest.save
        romtest.save = lambda p, name: _save(p, state)
        print('인트로 지나가는 중 (%s)…' % romtest.ROM, flush=True)
        romtest.intro()
        romtest.save = _save
for ext in ('.ram', '.rtc'):
    if os.path.exists(romtest.ROM + ext): os.remove(romtest.ROM + ext)
new = romtest.new
r = dmrom.Rom(romtest.ROM)
names = {k: bytes(r.d[r.names + 10 * (k - 1):r.names + 10 * k]) for k in range(1, dmrom.NUM + 1)}
N = {r.name(k): k for k in range(1, dmrom.NUM + 1)}
tag0 = os.path.splitext(os.path.basename(romtest.ROM))[0]


def pc(p):
    try: return '%04X' % p.pb.register_file.PC
    except Exception: return '?'


def st(p, tag):
    m = p.pb.memory
    p.shot('diag_%s_%s' % (tag0, tag))
    print('  %s: 맵 %d-%d (%d,%d) PC %s' % (tag, m[MAP_GROUP], m[MAP_NUM], m[XC], m[YC], pc(p)), flush=True)


p = new(state)
m = p.pb.memory
put_party(p, [(N.get('코로몬') or N.get('아구몬') or 1, 5, 70)], names)
m[MAP_GROUP], m[MAP_NUM], m[XC], m[YC] = g, n, x, y
p.tick(5)
st(p, '00_set')
p.press('start', 6, 80)
for _ in range(3): p.press('down', 6, 20)
p.press('a', 6, 100); p.press('a', 6, 150); p.press('a', 6, 150)
p.tick(500)
st(p, '01_saved')
p.pb.stop(save=True)
p = new()
m = p.pb.memory
p.tick(300)
st(p, '02_boot')
for i in range(24):
    p.press('a', 6, 60)
    if (m[MAP_GROUP], m[MAP_NUM]) == (g, n): break
st(p, '03_cont')
for k in range(8):
    p.press('a', 6, 90)
    p.tick(180)
    st(p, '%02d_a%d' % (4 + k, k))
p.press('start', 6, 90)
st(p, '12_start')
p.stop()
print('끝')
