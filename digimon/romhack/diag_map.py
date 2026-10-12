"""맵 하나 불러오기 진단 (10판): python3 diag_map.py 25 4 8 17
단계마다 화면을 work/shots/diag_NN.png 로 남기고 맵·좌표·PC 를 찍음. 멈추는 맵(노랑 수련장)이 어디서 멈추는지 보려는 것.
timeout 과 같이 쓴다: timeout 300 python3 diag_map.py 25 4 8 17"""
import sys, os
import dmrom, romtest
from romtest import new, put_party, MAP_GROUP, MAP_NUM, XC, YC

g, n, x, y = map(int, sys.argv[1:5])
r = dmrom.Rom(romtest.ROM)
names = {k: bytes(r.d[r.names + 10 * (k - 1):r.names + 10 * k]) for k in range(1, dmrom.NUM + 1)}
N = {r.name(k): k for k in range(1, dmrom.NUM + 1)}


def pc(p):
    try: return '%04X' % p.pb.register_file.PC
    except Exception: return '?'


def st(p, tag):
    m = p.pb.memory
    p.shot('diag_%s' % tag)
    print('  %s: 맵 %d-%d (%d,%d) PC %s' % (tag, m[MAP_GROUP], m[MAP_NUM], m[XC], m[YC], pc(p)), flush=True)


p = new('intro.state')
m = p.pb.memory
put_party(p, [(N.get('코로몬') or 1, 5, 70)], names)
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
