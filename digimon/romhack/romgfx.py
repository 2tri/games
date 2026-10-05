"""롬의 그림을 종류별로 전부 뽑기 (디지몬 앞·뒤, 트레이너, 필드 인물, 메뉴 아이콘, 타일셋, 제목 화면)
  python3 romgfx.py ROM OUT.json [--png]     (--png: 그림 data URI 까지, 없으면 비교용 해시만)
표 위치는 금 한글판 심볼 지도(romanat) 기준, 표가 가리키는 곳을 따라가므로 그림을 다른 뱅크로 옮겨도 읽힌다.
뽑은 그림은 원작 것이므로 work/ 와 비공개 페이지에만."""
import io, sys, json, base64, hashlib, struct
import numpy as np
from PIL import Image
import romanat, gblz

S = romanat.Sym()
GRAY = [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)]
FIX = None


def rgb15(v): return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)


def tiles(data, tw, th, colmajor=False):
    """2bpp 타일 → (th*8, tw*8) 색번호 배열"""
    a = np.zeros((th * 8, tw * 8), np.uint8)
    for t in range(tw * th):
        if colmajor: tx, ty = t // th, t % th
        else: tx, ty = t % tw, t // tw
        blk = data[t * 16:t * 16 + 16]
        if len(blk) < 16: break
        for r in range(8):
            lo, hi = blk[2 * r], blk[2 * r + 1]
            for c in range(8):
                a[ty * 8 + r, tx * 8 + c] = ((lo >> (7 - c)) & 1) | (((hi >> (7 - c)) & 1) << 1)
    return a


def png(idx, pal=GRAY, scale=1):
    cols = np.array(pal, np.uint8)
    im = Image.fromarray(cols[idx])
    if scale != 1: im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    b = io.BytesIO(); im.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def h(b): return hashlib.md5(bytes(b)).hexdigest()[:12]


class Gfx:
    def __init__(self, path, with_png=False):
        self.d = open(path, 'rb').read(); self.png = with_png
        d = self.d
        # FixPicBank: 롬에서 13 xx 14 xx 1f xx ff 표
        import re
        m = re.search(rb'\x13(.)\x14(.)\x1f(.)\xff', d, re.S)
        self.fix = {0x13: m.group(1)[0], 0x14: m.group(2)[0], 0x1f: m.group(3)[0]} if m else {}

    def w(self, a): return self.d[a] | self.d[a + 1] << 8

    def item(self, key, raw, idx=None, pal=GRAY, **kw):
        e = dict(key=key, hash=h(raw), size=len(raw), **kw)
        if self.png and idx is not None: e['png'] = png(idx, pal)
        return e

    def mons(self):
        d = self.d; pp = S['PokemonPicPointers']; bs = S['BaseData']; pal = S['PokemonPalettes']
        out = []
        for sp in range(1, 252):
            if sp == 201: continue
            c = [struct.unpack('<H', d[pal + 8 * sp + 2 * i:pal + 8 * sp + 2 * i + 2])[0] for i in range(2)]
            P = [(255, 255, 255), rgb15(c[0]), rgb15(c[1]), (0, 0, 0)]
            for back in (0, 1):
                e = d[pp + 6 * (sp - 1) + 3 * back:pp + 6 * (sp - 1) + 3 * back + 3]
                bank = self.fix.get(e[0], e[0]); a = romanat.off(bank, e[1] | e[2] << 8)
                try:
                    data, end = gblz.decompress(d, a)
                    if back: tw = th = 6
                    else: s = d[bs + 32 * (sp - 1) + 17]; tw, th = s & 15, s >> 4
                    idx = tiles(data, tw, th, colmajor=True)
                    out.append(self.item('%03d%s' % (sp, 'b' if back else 'f'), d[a:end], idx, P, at=a, dims=[tw, th]))
                except Exception as ex:
                    out.append(dict(key='%03d%s' % (sp, 'b' if back else 'f'), error=repr(ex)[:60], at=a))
        return out

    def trainers(self, n=66):
        d = self.d; tp = S['TrainerPicPointers']; pal = S['TrainerPalettes']; out = []
        for c in range(n):
            e = d[tp + 3 * c:tp + 3 * c + 3]; bank = self.fix.get(e[0], e[0]); a = romanat.off(bank, e[1] | e[2] << 8)
            cs = [struct.unpack('<H', d[pal + 4 * (c + 1) + 2 * i:pal + 4 * (c + 1) + 2 * i + 2])[0] for i in range(2)]
            P = [(255, 255, 255), rgb15(cs[0]), rgb15(cs[1]), (0, 0, 0)]
            try:
                data, end = gblz.decompress(d, a)
                out.append(self.item('cls%02d' % (c + 1), d[a:end], tiles(data, 7, 7, colmajor=True), P, at=a))
            except Exception as ex:
                out.append(dict(key='cls%02d' % (c + 1), error=repr(ex)[:60], at=a))
        return out

    def sprites(self, n=95):
        d = self.d; a0 = S['OverworldSprites']; out = []
        for k in range(n):
            e = d[a0 + 6 * k:a0 + 6 * k + 6]
            ptr, nt, bank = e[0] | e[1] << 8, e[2] // 16, e[3]          # e[2] = 바이트 수 (12 tiles = 192)
            a = romanat.off(bank, ptr)
            raw = d[a:a + nt * 16]
            frames = max(1, nt // 4)
            idx = np.vstack([tiles(raw[f * 64:f * 64 + 64], 2, 2) for f in range(frames)]) if nt >= 4 else None
            if idx is not None: idx = np.hstack([idx[i * 16:(i + 1) * 16] for i in range(frames)])
            out.append(self.item('spr%02d' % (k + 1), raw, idx, at=a, tiles=nt, type=e[4], opal=e[5]))
        return out

    def icons(self):
        d = self.d; ip = S['IconPointers']; bank = S['PoliwagIcon'] // 0x4000; out = []
        for k in range(1, 60):
            p = self.w(ip + 2 * k)
            if not (0x4000 <= p < 0x8000): break
            a = romanat.off(bank, p); raw = d[a:a + 8 * 16]
            idx = np.hstack([tiles(raw[:64], 2, 2), tiles(raw[64:], 2, 2)])
            out.append(self.item('icon%02d' % k, raw, idx, at=a))
        return out

    def tilesets(self, n=29):
        d = self.d; t0 = S['Tilesets']; out = []
        for k in range(n):
            e = d[t0 + 15 * k:t0 + 15 * k + 15]
            gb, gp = e[0], e[1] | e[2] << 8; mb, mp = e[3], e[4] | e[5] << 8; cb, cp = e[6], e[7] | e[8] << 8
            a = romanat.off(gb, gp)
            try:
                data, end = gblz.decompress(d, a, limit=0x1000)
                nt = len(data) // 16; tw = 16; th = (nt + tw - 1) // tw
                idx = tiles(data + bytes(tw * th * 16 - len(data)), tw, th)
                meta = d[romanat.off(mb, mp):romanat.off(mb, mp) + 0x400]; coll = d[romanat.off(cb, cp):romanat.off(cb, cp) + 0x100]
                out.append(self.item('ts%02d' % k, d[a:end], idx, at=a, tiles=nt, meta=h(meta), coll=h(coll)))
            except Exception as ex:
                out.append(dict(key='ts%02d' % k, error=repr(ex)[:60], at=a))
        return out

    def misc(self):
        d = self.d; out = []
        for lab, kind, tw in (('TitleScreenGFX1', 'lz', 16), ('TitleScreenGFX3', 'lz', 16), ('TitleScreenGFX2', 'raw:0x80', 16),
                              ('CopyrightGFX', 'raw:0x1e0', 16), ('ChrisPicAndTrainerCardGFX', 'raw:0x310', 7)):
            a = S[lab]
            try:
                if kind == 'lz': data, end = gblz.decompress(d, a, limit=0x2000); raw = d[a:end]
                else: n = int(kind.split(':')[1], 16); data = raw = d[a:a + n]
                nt = len(data) // 16
                if lab == 'ChrisPicAndTrainerCardGFX':
                    idx = tiles(data[:49 * 16], 7, 7, colmajor=True)
                else:
                    th = (nt + tw - 1) // tw; idx = tiles(data + bytes(tw * th * 16 - len(data)), tw, th)
                out.append(self.item(lab, raw, idx, at=a))
            except Exception as ex:
                out.append(dict(key=lab, error=repr(ex)[:60], at=a))
        return out

    def all(self):
        return dict(mons=self.mons(), trainers=self.trainers(), sprites=self.sprites(), icons=self.icons(),
                    tilesets=self.tilesets(), misc=self.misc())


if __name__ == '__main__':
    G = Gfx(sys.argv[1], '--png' in sys.argv).all()
    json.dump(G, open(sys.argv[2], 'w'))
    for k, v in G.items(): print(k, len(v), sum(1 for x in v if 'error' in x), '오류')
