"""롬 자료 만들기: index.html 의 자료(기술·적·인물) + ai/sprites.js 그림 + 쓰인 글자만 담은 갈무리9 글꼴 → src/*.c
사용: python3 gen.py 갈무리9.ttf"""
import json, re, subprocess, sys, glob, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = HERE + '/src'
D = json.loads(subprocess.check_output(['node', HERE + '/extract.js']))
s = open(HERE + '/../ai/sprites.js').read(); SPR = json.loads(s[s.index('{'):s.rindex('}') + 1])
H, M, F = D['HEROES'], D['MOVES'], D['FOES']

def cstr(t): return '"' + t.replace('\\', '\\\\').replace('"', '\\"') + '"'
TYPES = ['', '짐승', '나무', '망령', '어둠', '오크', '마법사']
ELEMS = ['', '불', '빛', '요정']
KINDS = ['hit', 'heal', 'buff', 'hide', 'debuff', 'sleep']
mids = list(M); hids = list(H); fids = list(F)
# 쓰는 그림: 인물 뒷모습·앞모습, 적
sprs = []
def sid(n):
    if n not in SPR: return 255
    if n not in sprs: sprs.append(n)
    return sprs.index(n)
for h in hids: sid(h + '_back'); sid(h + '_front')
for f in fids: sid(F[f]['spr'])
for n in SPR: sid(n)

h_out = ['#include <stdint.h>', '#define FONT_BANK 1', '#define DATA_BANK 2', '#define N_MOVES %d' % len(mids), '#define N_FOES %d' % len(fids), '#define N_HEROES %d' % len(hids), '#define N_SPR %d' % len(sprs)]
h_out += ['#define MV_%s %d' % (m.upper(), i) for i, m in enumerate(mids)]
h_out += ['#define FO_%s %d' % (f.upper(), i) for i, f in enumerate(fids)]
h_out += ['#define HE_%s %d' % (h.upper(), i) for i, h in enumerate(hids)]
h_out += ['#define SP_%s %d' % (n.upper(), i) for i, n in enumerate(sprs)]
h_out += ['#define T_%d %d' % (i, i) for i in range(len(TYPES))]
h_out += ['enum { K_HIT, K_HEAL, K_BUFF, K_HIDE, K_DEBUFF, K_SLEEP };', 'enum { TY_NONE, TY_BEAST, TY_TREE, TY_WRAITH, TY_DARK, TY_ORC, TY_WIZARD };',
          'enum { EL_NONE, EL_FIRE, EL_LIGHT, EL_ELF };',
          'typedef struct { const char *name, *line; uint8_t pow, acc, kind, stat, elem, hits, crit, bind, weaken, amt, cure; } Move;',
          'typedef struct { const char *name; uint8_t spr, lv; uint16_t hp; uint8_t atk, def, spd, type, boss, moves[3]; } Foe;',
          'typedef struct { const char *name; uint8_t hp, atk, def, spd, moves[4], back, front; } Hero;',
          'typedef struct { uint8_t bank, w, h; const uint8_t *data; } Spr;',
          'extern const Move MOVES[]; extern const Foe FOES[]; extern const Hero HEROES[]; extern const Spr SPRS[]; extern const uint8_t EFFECT[4][7];',
          'extern const uint16_t FONT_CP[]; extern const uint8_t FONT_GL[], FONT_GL2[]; extern const uint16_t FONT_N, FONT_SPLIT;', '#define FONT_BANK2 15']
open(SRC + '/data.h', 'w').write('\n'.join(h_out) + '\n')

c = ['#pragma bank 2', '#include "data.h"', 'const Move MOVES[] = {']
for m in mids:
    v = M[m]
    c.append('  { %s, %s, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d },' % (cstr(v['name']), cstr(v['line']) if 'line' in v else '0', v.get('pow', 0), v.get('acc', 100),
             KINDS.index(v.get('kind', 'hit')), 1 if v.get('stat') == 'def' else 0, ELEMS.index(v.get('elem', '')), v.get('hits', 1), v.get('crit', 6),
             v.get('bind', 0), v.get('weaken', 0), round(v.get('amt', 0) * 100), 1 if v.get('cure') else 0))
c += ['};', 'const Foe FOES[] = {']
for f in fids:
    v = F[f]
    c.append('  { %s, %d, %d, %d, %d, %d, %d, %d, %d, { %s } },' % (cstr(v['name']), sid(v['spr']), v['lv'], v['hp'], v['atk'], v['def'], v['spd'], TYPES.index(v['type']),
             1 if v.get('boss') else 0, ', '.join(str(mids.index(x)) for x in v['moves'])))
c += ['};', 'const Hero HEROES[] = {']
for h in hids:
    v = H[h]
    c.append('  { %s, %d, %d, %d, %d, { %s }, %d, %d },' % (cstr(v['name']), v['hp'], v['atk'], v['def'], v['spd'], ', '.join(str(mids.index(x)) for x in v['moves']), sid(h + '_back'), sid(h + '_front')))
c.append('};')
eff = [[D['EFFECT'].get(e, {}).get(t, 1) for t in TYPES] for e in ELEMS]
c.append('const uint8_t EFFECT[4][7] = {' + ','.join('{' + ','.join(map(str, r)) + '}' for r in eff) + '};')

# ── 그림: 8×8 타일마다 [2bpp 16바이트 + 불투명 마스크 8바이트], 은행(16KB)마다 나눠 담음 ──
def enc_sprite(t):
    t = np.array(t); h, w = t.shape; out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            b = t[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]; data = []; mask = []
            for row in b:
                lo = hi = mk = 0
                for x, v in enumerate(row):
                    if v >= 0: mk |= 1 << (7 - x); lo |= (v & 1) << (7 - x); hi |= ((v >> 1) & 1) << (7 - x)
                data += [lo, hi]; mask.append(mk)
            out += data + mask
    return out, w // 8, h // 8
bank, used, files = 3, 0, {}   # 0 코드, 1 글꼴, 2 전투·자료, 3~7 그림, 8~ 이야기
entries = []
for n in sprs:
    data, w, h = enc_sprite(SPR[n])
    if used + len(data) > 16000: bank += 1; used = 0
    used += len(data); files.setdefault(bank, []).append((n, data)); entries.append((bank, w, h, n))
assert bank <= 7, '그림이 3~7번 은행을 넘음'
for old in glob.glob(SRC + '/spr*.c'): os.remove(old)
for b, items in files.items():
    with open(SRC + '/spr%d.c' % b, 'w') as f:
        f.write('#pragma bank %d\n#include <stdint.h>\n' % b)
        for n, data in items: f.write('const uint8_t S_%s[] = {%s};\n' % (n, ','.join(map(str, data))))
c += ['extern const uint8_t ' + ', '.join('S_%s[]' % n for n in sprs) + ';', 'const Spr SPRS[] = {']
c += ['  { %d, %d, %d, S_%s },' % e for e in entries] + ['};']
open(SRC + '/data.c', 'w').write('\n'.join(c) + '\n')

# ── 글꼴: 롬에 쓰인 글자만. 글자마다 [너비 1바이트 + 10줄 × 2바이트] (그림 위 2줄 띄움) ──
chars = set(chr(i) for i in range(32, 127))
for fn in glob.glob(SRC + '/*.c') + glob.glob(SRC + '/*.h'):
    for lit in re.findall(r'"((?:[^"\\]|\\.)*)"', open(fn).read()): chars |= set(lit)
chars = sorted(ch for ch in chars if ord(ch) >= 32 and ord(ch) < 0x10000)
font = ImageFont.truetype(sys.argv[1], 10); gl = []
for ch in chars:
    im = Image.new('L', (16, 14)); ImageDraw.Draw(im).text((0, 1), ch, font=font, fill=255); a = np.asarray(im) > 110
    w = round(font.getlength(ch)); gl.append(w)
    for y in range(2, 12):
        bits = 0
        for x in range(16):
            if a[y, x]: bits |= 1 << (15 - x)
        gl += [bits >> 8, bits & 255]
SPLIT = 16380 // 21          # 글자 780개씩: 앞쪽은 1번 은행, 나머지는 15번 은행
assert len(chars) <= SPLIT * 2, '글꼴이 두 은행을 넘음'
for fn, bk, part in (('font.c', 1, gl[:SPLIT * 21]), ('font2.c', 15, gl[SPLIT * 21:] or [0])):
    with open(SRC + '/' + fn, 'w') as f:
        f.write('#pragma bank %d\n#include <stdint.h>\n' % bk)
        f.write('const uint8_t %s[] = {%s};\n' % ('FONT_GL' if bk == 1 else 'FONT_GL2', ','.join(map(str, part))))
with open(SRC + '/fontcp.c', 'w') as f:   # 글자 번호 찾기 표는 0번 은행 (어느 은행에서도 읽힘)
    f.write('#include <stdint.h>\nconst uint16_t FONT_N = %d, FONT_SPLIT = %d;\nconst uint16_t FONT_CP[] = {%s};\n' % (len(chars), SPLIT, ','.join(str(ord(ch)) for ch in chars)))
print('글자', len(chars), '글꼴', len(gl), 'B · 그림', len(sprs), '개, 은행', sorted(files), '· 기술', len(mids), '적', len(fids))
