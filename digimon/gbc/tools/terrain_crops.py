import numpy as np
from PIL import Image, ImageDraw
A = np.asarray(Image.open('art/src/bg/terrain_ai.png').convert('RGB')).astype(np.int16)
def crop_native(box, tw, th, frac=0.4):
    x0, y0, x1, y1 = box; W, H = 16 * tw, 16 * th
    pw, ph = (x1 - x0) / W, (y1 - y0) / H
    out = np.zeros((H, W, 3), np.uint8)
    for j in range(H):
        for i in range(W):
            cx, cy = x0 + (i + .5) * pw, y0 + (j + .5) * ph
            rx, ry = max(1, int(pw * frac / 2)), max(1, int(ph * frac / 2))
            blk = A[int(cy) - ry:int(cy) + ry + 1, int(cx) - rx:int(cx) + rx + 1].reshape(-1, 3)
            out[j, i] = np.median(blk, 0)
    return out
C = {
 'ledge': ((2, 314, 86, 416), 1, 1), 'ledge2': ((283, 314, 360, 416), 1, 1), 'ledgeT': ((1254, 196, 1336, 236), 1, 1),
 'plankH': ((447, 0, 538, 82), 1, 1), 'plankV': ((869, 0, 950, 82), 1, 1),
 'rockA': ((362, 255, 538, 384), 2, 2), 'rockB': ((620, 200, 786, 384), 2, 2), 'cliffL': ((362, 384, 620, 492), 3, 1),
 'stairs': ((788, 240, 868, 384), 1, 2), 'stairs2': ((950, 220, 1021, 312), 1, 1), 'cave': ((950, 312, 1114, 492), 2, 2),
 'boulder': ((538, 522, 620, 604), 1, 1), 'crack': ((620, 522, 703, 604), 1, 1), 'pebble': ((450, 522, 538, 604), 1, 1),
 'gate': ((786, 520, 868, 606), 1, 1), 'fence': ((868, 520, 949, 606), 1, 1), 'tree': ((262, 600, 366, 740), 1, 2),
 'ball': ((462, 682, 524, 744), 1, 1), 'tall': ((538, 606, 620, 686), 1, 1), 'grass': ((703, 606, 786, 686), 1, 1), 'dirt': ((868, 606, 949, 686), 1, 1),
 'pond': ((0, 0, 362, 312), 5, 4),
}
tiles = {k: crop_native(*v) for k, v in C.items()}
if __name__ == '__main__':
    sc = 4; x = 4; H = max(t.shape[0] for t in tiles.values()) * sc + 20
    W = sum(t.shape[1] * sc + 8 for t in tiles.values()) + 8
    im = Image.new('RGB', (W, H), (60, 60, 70)); d = ImageDraw.Draw(im)
    for k, t in tiles.items():
        im.paste(Image.fromarray(t).resize((t.shape[1] * sc, t.shape[0] * sc), Image.NEAREST), (x, 16)); d.text((x, 2), k, fill=(255, 255, 0)); x += t.shape[1] * sc + 8
    im.save('/tmp/claude-0/-home-user-games/6383e336-0dcf-5b3b-862b-dcfdcb19a4bd/scratchpad/crops.png'); print(im.size)
