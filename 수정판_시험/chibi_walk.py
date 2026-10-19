"""나리 걷기 시트(96x128, 32x32칸)를 태일처럼 2등신으로: 머리 키우고 몸·다리 줄이고 테두리 진하게."""
import sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
HEAD_ROWS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
HS = float(sys.argv[4]) if len(sys.argv) > 4 else 1.4     # 머리 배율
BW = float(sys.argv[5]) if len(sys.argv) > 5 else 1.2     # 몸 가로 배율
FOOT = 30                                                  # 발 밑 줄 (원본과 같게)

def scale2x(im):
    w, h = im.size; p = im.load(); o = Image.new('RGBA', (w*2, h*2)); q = o.load()
    g = lambda x, y: p[min(max(x,0),w-1), min(max(y,0),h-1)]
    for y in range(h):
        for x in range(w):
            P = g(x,y); A = g(x,y-1); B = g(x+1,y); C = g(x-1,y); D = g(x,y+1)
            e0 = A if (C == A and C != D and A != B) else P
            e1 = B if (A == B and A != C and B != D) else P
            e2 = C if (D == C and D != B and C != A) else P
            e3 = D if (B == D and B != A and D != C) else P
            q[2*x,2*y], q[2*x+1,2*y], q[2*x,2*y+1], q[2*x+1,2*y+1] = e0, e1, e2, e3
    return o

def rs(im, w, h):
    big = scale2x(scale2x(im))                    # 4배로 부드럽게 키운 뒤
    return big.resize((max(1,w), max(1,h)), Image.NEAREST)   # 원하는 크기로 (색은 원래 팔레트 그대로)

def clean_alpha(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x,y][3] < 128: px[x,y] = (0,0,0,0)
            else: px[x,y] = px[x,y][:3] + (255,)
    return im

def outline(im, col):
    w, h = im.size; p = im.load(); add = []
    for y in range(h):
        for x in range(w):
            if p[x,y][3]: continue
            if any(0 <= x+dx < w and 0 <= y+dy < h and p[x+dx,y+dy][3] and p[x+dx,y+dy][:3] != col for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                add.append((x,y))
    for x,y in add: p[x,y] = col + (255,)
    return im

def strip_outline(im, col):
    # 바깥 테두리(투명과 닿은 어두운 점)를 걷어 내고 키운 뒤 새로 두른다
    w, h = im.size; p = im.load(); rm = []
    for y in range(h):
        for x in range(w):
            c = p[x,y]
            if c[3] and max(c[:3]) < 90 and any(not(0<=x+dx<w and 0<=y+dy<h) or p[x+dx,y+dy][3]==0 for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                rm.append((x,y))
    for x,y in rm: p[x,y] = (0,0,0,0)
    return im

def frame(f):
    f = clean_alpha(f.copy())
    bb = f.getchannel('A').getbbox(); top, bot = bb[1], bb[3]
    col = (40, 32, 40)
    body_src = strip_outline(f.crop((0, top+HEAD_ROWS, 32, bot)), col)
    head_src = strip_outline(f.crop((0, top, 32, top+HEAD_ROWS)), col)
    hb = head_src.getchannel('A').getbbox(); head_src = head_src.crop(hb)
    bb2 = body_src.getchannel('A').getbbox(); body_src = body_src.crop(bb2)
    hw, hh = round(head_src.width*HS), round(head_src.height*HS)
    body_h = FOOT - 1 - (1 + hh) + 2                    # 머리와 몸이 2줄 겹침(목)
    bw = round(body_src.width*BW)
    head = rs(head_src, hw, hh); body = rs(body_src, bw, body_h)
    cx = (hb[0]+hb[2])/2
    out = Image.new('RGBA', (32,32), (0,0,0,0))
    out.alpha_composite(body, (round((bb2[0]+bb2[2])/2 - bw/2), FOOT - body_h))
    out.alpha_composite(head, (round(cx - hw/2), 1))
    return outline(out, col)

sh = Image.open(src).convert('RGBA'); out = Image.new('RGBA', sh.size, (0,0,0,0))
for r in range(4):
    for c in range(3):
        out.alpha_composite(frame(sh.crop((c*32, r*32, c*32+32, r*32+32))), (c*32, r*32))
out.save(dst)
