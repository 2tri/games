"""20판: 검수 페이지 결과(picks.json) 를 art/ 에 반영.
python3 apply_picks.py            # 고른 대로 art/<id>-f.png·-b.png 바꾸기 + 앞뒤 출처가 다른 종은 뒷모습 색을 앞모습 팔레트에 맞춤
python3 apply_picks.py --sheet 이전롬 새롬 [출력.png]   # 앞뒤 조합 종의 전·후를 롬 화면 그대로 한 장에
picks.json = {칸 키: {name, id, f, b}}, f·b = cur(그대로) / bak(art_bak 의 이전 그림) / ds(위키몬 DS 변환) / alt(다른 id 의 새 그림) / none(새 그림 필요)
롬은 앞·뒤가 팔레트 하나(앞 그림에서 정함) → 뒷모습의 밝은 몸색·어두운 몸색을 앞의 두 색에 넓은 몸색끼리·나머지끼리 맞춤(앞뒤가 다른 그림일 때만)."""
import os, sys, json, shutil
import numpy as np
from PIL import Image, ImageDraw
import dmrom, patch, ingest, ds_convert, rules

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE)
ART, BAK = os.path.join(WEB, 'art'), os.path.join(WEB, 'art_bak'); IMG = os.path.join(os.path.dirname(WEB), 'images', 'digimon')
ALT_ID = {'thunderballmon': 'thunderballmon-back'}      # alt 로 쓰는 그림을 따로 둔 id (patch BACK_ONLY 는 앞 파일이 없어야 함)


def lum(c): return c[0] * .299 + c[1] * .587 + c[2] * .114


def front_pal(did, rom_no=None, rom=None, use_rom=False):
    """앞모습의 두 몸색과 그 중 넓은 쪽(dom). 롬 팔레트 순서 = png_to_idx 와 같게 [밝은 색, 어두운 색]"""
    f = os.path.join(ART, '%s-f.png' % did)
    if not use_rom and os.path.exists(f):
        idx, pal = patch.png_to_idx(f, 56, 56)
        cnt = [int((idx == 1).sum()), int((idx == 2).sum())]
        return [tuple(int(x) for x in c) for c in pal], (0 if cnt[0] >= cnt[1] else 1)
    if rom is not None and rom_no:
        a = rom.pic(rom_no); pal = sorted([tuple(int(x) for x in c) for c in rom.palette(rom_no)], key=lambda c: -lum(c))
        cnt = [int((a == 1).sum()), int((a == 2).sum())]
        return pal, (0 if cnt[0] >= cnt[1] else 1)
    return None, 0


def recolor_back(src, dst, pal, dom):
    """뒷모습의 몸색(흰·검정 빼고)을 밝기 2군집으로 나눠, 넓은 군집 → 앞모습의 넓은 몸색(pal[dom]), 나머지 → 다른 색.
    (밝기 순으로만 맞추면 앞은 어두운 색이 몸통인데 뒤는 밝은 색이 몸통으로 칠해지는 종이 있었음)"""
    a = np.asarray(Image.open(src).convert('RGBA')).astype(int).copy()
    op = a[..., 3] > 128; rgb = a[..., :3]
    white = op & (rgb.min(2) > 230); black = op & (rgb.max(2) < 60); mid = op & ~white & ~black
    big, small = pal[dom], pal[1 - dom]
    L = rgb @ np.array([.299, .587, .114])
    if mid.any():
        lm = L[mid]; lo, hi = lm.min(), lm.max()
        if hi - lo < 25:
            a[mid, :3] = big
        else:
            t = (lo + hi) / 2
            for _ in range(12):
                up, dn = lm[lm >= t], lm[lm < t]
                if len(up) == 0 or len(dn) == 0: break
                t = (up.mean() + dn.mean()) / 2
            light = mid & (L >= t); dark = mid & (L < t)
            if light.sum() >= dark.sum(): a[light, :3] = big; a[dark, :3] = small
            else: a[dark, :3] = big; a[light, :3] = small
    Image.fromarray(a.astype(np.uint8), 'RGBA').save(dst)


def apply():
    picks = json.load(open(os.path.join(HERE, 'picks.json'), encoding='utf-8'))
    rom = dmrom.Rom(os.path.join(dmrom.WORK, 'myver.gbc')); N = {rom.name(n): n for n in range(1, dmrom.NUM + 1)}
    changed, miss, mixed, recol, nothing = [], [], [], [], []
    for key, v in picks.items():
        did = v['id']
        dspal = None
        for side in ('f', 'b'):
            k = v[side]; dst = os.path.join(ART, '%s-%s.png' % (did, side))
            if k == 'bak':
                src = os.path.join(BAK, '%s-%s.png' % (did, side))
                if not os.path.exists(src): miss.append('%s %s: art_bak 에 그림 없음' % (v['name'], side)); continue
                if not os.path.exists(dst) or open(src, 'rb').read() != open(dst, 'rb').read():
                    shutil.copy(src, dst); changed.append((v['name'], side, '이전 그림'))
            elif k == 'ds':
                src = os.path.join(IMG, '%s-ds-%s.png' % (did, side))
                g = ingest.grade_of(did); fmax = ingest.FRONT.get(g, 56) if g else 56
                size, pal_ = ds_convert.convert(src, dst, fmax if side == 'f' else 48, dspal)      # 뒤는 앞 몸색 그대로 (ds_all 과 같게)
                if side == 'f': dspal = pal_
                changed.append((v['name'], side, 'DS 변환 %dx%d' % size))
        if v['f'] != v['b'] and 'none' not in (v['f'], v['b']):
            mixed.append(v['name'])
            n = N.get(v['name'])
            pal, dom = front_pal(did, n, rom, use_rom=(v['b'] == 'alt'))      # alt(번개콩알몬)는 앞이 1.4 그림 → 롬 팔레트·롬 그림
            if v['b'] == 'alt':      # 다른 id 의 새 그림을 뒷모습으로 → 이 종 전용 파일로 복사하며 색 맞춤
                src = os.path.join(ART, '%s-b.png' % did); dst = os.path.join(ART, '%s-b.png' % ALT_ID.get(did, did + '-alt'))
            else:
                src = dst = os.path.join(ART, '%s-b.png' % did)
            if pal and os.path.exists(src):
                recolor_back(src, dst, pal, dom); recol.append('%s(앞 %s·뒤 %s)' % (v['name'], v['f'], v['b']))
            else: nothing.append(v['name'])
    print('바꾼 면 %d: %s' % (len(changed), ', '.join('%s %s' % (a, b) for a, b, _ in changed)))
    if miss: print('못 바꿈 %d: %s' % (len(miss), '; '.join(miss)))
    print('앞뒤 다른 조합 %d종, 뒷모습 색 맞춤 %d: %s' % (len(mixed), len(recol), ', '.join(recol)))
    if nothing: print('색 못 맞춤: ' + ', '.join(nothing))


def sheet(old, new, out):
    picks = json.load(open(os.path.join(HERE, 'picks.json'), encoding='utf-8'))
    ro, rn = dmrom.Rom(old), dmrom.Rom(new)
    No = {ro.name(n): n for n in range(1, dmrom.NUM + 1)}; Nn = {rn.name(n): n for n in range(1, dmrom.NUM + 1)}
    mix = [v for v in picks.values() if v['f'] != v['b'] and 'none' not in (v['f'], v['b'])]
    SC, CW, CH = 2, 56 * 2 * 4 + 12, 56 * 2 + 16
    cols = 2; rows = (len(mix) + cols - 1) // cols
    sh = Image.new('RGB', (cols * CW, rows * CH), (255, 255, 255)); dr = ImageDraw.Draw(sh)
    fnt = None
    try:
        from PIL import ImageFont; fnt = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 13)
    except Exception: pass
    for k, v in enumerate(mix):
        x0, y0 = (k % cols) * CW, (k // cols) * CH
        for j, (rom, no, back) in enumerate(((ro, No.get(v['name']), False), (rn, Nn.get(v['name']), False), (ro, No.get(v['name']), True), (rn, Nn.get(v['name']), True))):
            if not no: continue
            a = rom.pic(no, back=back); c1, c2 = rom.palette(no)
            pal = np.array([(255, 255, 255), c1, c2, (0, 0, 0)], np.uint8)
            im = Image.fromarray(pal[a]).resize((a.shape[1] * SC, a.shape[0] * SC), Image.NEAREST)
            sh.paste(im, (x0 + j * 56 * SC + (56 * SC - im.width) // 2, y0 + 56 * SC - im.height))
            dr.line([x0 + j * 56 * SC, y0, x0 + j * 56 * SC, y0 + CH], fill=(220, 220, 220))
        dr.rectangle([x0, y0, x0 + CW - 1, y0 + CH - 1], outline=(180, 180, 180))
        dr.text((x0 + 3, y0 + 56 * SC + 1), '%s  앞 %s · 뒤 %s   (전앞|후앞|전뒤|후뒤)' % (v['name'], v['f'], v['b']), fill=(0, 0, 0), font=fnt)
    sh.save(out); print('%s (%d종)' % (out, len(mix)))


if __name__ == '__main__':
    if '--sheet' in sys.argv:
        i = sys.argv.index('--sheet'); sheet(sys.argv[i + 1], sys.argv[i + 2], sys.argv[i + 3] if len(sys.argv) > i + 3 else os.path.join(dmrom.WORK, 'mixed_sheet.png'))
    else:
        apply()
