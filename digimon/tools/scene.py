"""이미지 AI 배경 그림 → 진짜 도트(원래 칸) → 16×16 지도 칸으로 자르기 위한 도구"""
import numpy as np
from PIL import Image, ImageDraw
import snapc

def native(path, cell=None, off=None):
    """도트 칸마다 가운데 색(중앙값) → (h,w,3). 칸 가운데 40% 정사각 영역의 중앙값 (빠르게)"""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    if cell is None:
        (pw, ox), (ph, oy) = snapc.grid(snapc.lum(a.astype(float)))
    else:
        pw = ph = cell; ox, oy = off if off else (0, 0)
    nx, ny = int((a.shape[1] - ox) / pw), int((a.shape[0] - oy) / ph)
    r = max(1, int(min(pw, ph) * 0.2))
    cx = (ox + (np.arange(nx) + .5) * pw).astype(int); cy = (oy + (np.arange(ny) + .5) * ph).astype(int)
    offs = np.arange(-r, r + 1)
    YY = np.clip(cy[:, None] + offs[None], 0, a.shape[0] - 1); XX = np.clip(cx[:, None] + offs[None], 0, a.shape[1] - 1)
    blk = a[YY[:, None, :, None], XX[None, :, None, :]]          # ny,nx,k,k,3
    out = np.median(blk.reshape(ny, nx, -1, 3), axis=2).astype(np.uint8)
    return out, (pw, ph, ox, oy)

def grid_preview(img, path, step=16, scale=4, x0=0, y0=0):
    im = Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for x in range(x0, img.shape[1], step): d.line([(x * scale, 0), (x * scale, im.size[1])], fill=(255, 0, 0), width=1)
    for y in range(y0, img.shape[0], step): d.line([(0, y * scale), (im.size[0], y * scale)], fill=(255, 0, 0), width=1)
    for ty, y in enumerate(range(y0, img.shape[0], step)):
        for tx, x in enumerate(range(x0, img.shape[1], step)):
            d.text((x * scale + 2, y * scale + 1), '%d,%d' % (tx, ty), fill=(255, 255, 0))
    im.save(path)
