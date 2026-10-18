import sys, colorsys
sys.argv=['x','../../_emu_test.nds','../../게임화면_오늘/d1015b/out5.dst','../../게임화면_오늘/d1015b/ft2','126']
exec(open('emu_party.py').read().split("for a in acts:")[0])
touch(50, 76); run(60)
for _ in range(7): press(Keys.KEY_B, 4, 45)
run(90)
NAMES = {'빨강1': (255,0,0), '초록2': (0,200,0), '파랑3': (0,0,255), '노랑4': (255,255,0), '보라5': (255,0,255), '흰6': (255,255,255), '주황7': (255,128,0), '자주8': (128,0,255)}
def classify(im):
    px = im.convert('RGB').load()
    cnt = {}
    for y in range(40, 150):
        for x in range(60, 200):
            c = px[x, y]
            if all(px[x+dx, y+dy] == c for dx in (-2, 0, 2) for dy in (-2, 0, 2)):
                hh, s, v = colorsys.rgb_to_hsv(c[0]/255, c[1]/255, c[2]/255)
                if (s > 0.5 and v > 0.3): cnt[c] = cnt.get(c, 0) + 1
    if not cnt: return None, None
    c, n = max(cnt.items(), key=lambda kv: kv[1])
    if n < 40: return None, None
    best = min(NAMES.items(), key=lambda kv: sum((c[i]-kv[1][i]*(0.55,0.6,0.85)[i])**2 for i in range(3)))
    # 밤 색조가 없는 밝은 구간도 허용: 색조 없이도 비교
    best2 = min(NAMES.items(), key=lambda kv: sum((c[i]-kv[1][i])**2 for i in range(3)))
    return (best[0] if sum((c[i]-best[1][i]*(0.55,0.6,0.85)[i])**2 for i in range(3)) <= sum((c[i]-best2[1][i])**2 for i in range(3)) else best2[0]), c
def dirtest(nm, key, pre_key):
    # 먼저 반대쪽 한 칸 걸어 방향을 바꾼 뒤 시험 방향으로 두 칸
    mm = keymask(pre_key); emu.input.keypad_add_key(mm); run(20); emu.input.keypad_rm_key(mm); run(50)
    m = keymask(key); emu.input.keypad_add_key(m)
    out = []
    for f in range(40):
        run(1)
        if f % 5 == 4: out.append(classify(emu.screenshot())[0])
    emu.input.keypad_rm_key(m); run(10)
    out2 = []
    for f in range(45):
        run(1)
        if f % 5 == 4: out2.append(classify(emu.screenshot())[0])
    print(nm, '걷는 중:', out, '멈춘 뒤:', out2)
dirtest('위', Keys.KEY_UP, Keys.KEY_LEFT)
dirtest('아래', Keys.KEY_DOWN, Keys.KEY_RIGHT)
dirtest('왼쪽', Keys.KEY_LEFT, Keys.KEY_UP)
dirtest('오른쪽', Keys.KEY_RIGHT, Keys.KEY_DOWN)
dirtest('위2', Keys.KEY_UP, Keys.KEY_RIGHT)
dirtest('아래2', Keys.KEY_DOWN, Keys.KEY_LEFT)
