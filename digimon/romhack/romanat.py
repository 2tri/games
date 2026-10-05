"""롬 해부 (2.0 같은 다른 사람 판을 통째로 뜯어보기)
기준 = 금 한글판 디스어셈블리(pokegold-kr)를 빌드해 얻은 심볼(라벨) 지도.
  · 디스어셈블리가 소스로 가진 바이트 = 원본 금 값을 앎 (빌드를 00/FF 덮개로 두 번 해서 같은 자리)
  · 소스가 없는 자리(덮개에서 옴) = 원본 값을 모름 → 비어 있던 곳이면 「새로 넣은 것」
준비 (한 번): rgbds 1.0.3 빌드 → pokegold-kr 를 baserom_g.bin = 00·FF 2MB 로 두 번 빌드 →
  work/anat/van_00.gbc · van_ff.gbc · pokegold.sym · pokegold.map
롬·뽑은 내용은 저장소에 올리지 않는다 (work/ 는 .gitignore).

  python3 romanat.py regions ROM [--out J]   원본 금 대비 바뀐 곳을 라벨 단위로
"""
import os, re, sys, json, bisect, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ANAT = os.path.join(HERE, 'work', 'anat')


def off(bank, a): return bank * 0x4000 + (a - 0x4000 if bank else a)


class Sym:
    def __init__(self, path=os.path.join(ANAT, 'pokegold.sym')):
        self.rows = []
        for ln in open(path):
            m = re.match(r'([0-9a-f]{2,3}):([0-9a-f]{4}) (\S+)', ln)
            if not m: continue
            b, a = int(m.group(1), 16), int(m.group(2), 16)
            if b >= 0x80 or (b and a < 0x4000) or a >= 0x8000: continue      # ROM 만
            self.rows.append((off(b, a), m.group(3)))
        self.rows.sort()
        self.offs = [r[0] for r in self.rows]
        self.by = {}
        for o, n in self.rows: self.by.setdefault(n, o)

    def at(self, o, top=False):
        """o 를 덮는 가장 가까운 라벨 (top=True 면 .local 을 떼고 윗 라벨)"""
        i = bisect.bisect_right(self.offs, o) - 1
        while i >= 0:
            n = self.rows[i][1]
            if not top or '.' not in n: return n, o - self.rows[i][0]
            i -= 1
        return '(없음)', o

    def __getitem__(self, n): return self.by[n]


class Vanilla:
    def __init__(self):
        self.a = open(os.path.join(ANAT, 'van_00.gbc'), 'rb').read()
        b = open(os.path.join(ANAT, 'van_ff.gbc'), 'rb').read()
        self.known = bytes(1 if x == y else 0 for x, y in zip(self.a, b))
        # 지도에서 비어 있던 자리(EMPTY) — 원본 금의 빈 공간
        self.empty = bytearray(len(self.a))
        m = open(os.path.join(ANAT, 'pokegold.map')).read()
        for blk in re.split(r'\n(?=[A-Z0-9]+ bank #)', m)[1:]:
            h = blk.split('\n', 1)[0]
            if not h.startswith('ROM'): continue
            bn = int(re.search(r'#(\d+)', h).group(1))
            if re.search(r'^\tEMPTY\s*$', blk, re.M):      # 뱅크 통째로 비었다고 표시
                for i in range(off(bn, 0x4000 if bn else 0), off(bn, 0x4000 if bn else 0) + 0x4000): self.empty[i] = 1
            for s, e in re.findall(r'EMPTY: \$(\w+)-\$(\w+)', blk):
                s, e = int(s, 16), int(e, 16)
                for i in range(off(bn, s), off(bn, e) + 1): self.empty[i] = 1


def runs(mask_fn, n, gap=4):
    """mask_fn(i) 가 참인 자리를 gap 이하로 떨어진 것끼리 묶어 [s,e) 목록"""
    out = []; s = None; last = None
    for i in range(n):
        if mask_fn(i):
            if s is None: s = i
            elif i - last > gap: out.append((s, last + 1)); s = i
            last = i
    if s is not None: out.append((s, last + 1))
    return out


def regions(path, sym=None, van=None):
    sym = sym or Sym(); van = van or Vanilla()
    d = open(path, 'rb').read(); a = van.a; kn = van.known; em = van.empty
    N = len(a)
    # 1) 원본 값을 아는 자리에서 바뀐 곳
    ch = runs(lambda i: kn[i] and d[i] != a[i], N)
    changed = []
    for s, e in ch:
        lab, rel = sym.at(s); top, trel = sym.at(s, top=True)
        changed.append(dict(off=s, end=e, n=sum(1 for i in range(s, e) if d[i] != a[i]), label=lab, rel=rel, top=top))
    # 2) 원본에서 비어 있던 곳에 들어간 내용 (00·FF 가 아닌 바이트)
    added = runs(lambda i: em[i] and d[i] not in (0, 0xff), N, gap=32)
    added = [dict(off=s, end=e, n=e - s, bank=s // 0x4000) for s, e in added]
    # 3) 원본 값을 모르는(소스 없는) 자리 — 다른 판끼리만 비교 가능
    unk = runs(lambda i: not kn[i] and not em[i], N, gap=64)
    unknown = [dict(off=s, end=e, n=e - s, top=sym.at(s, top=True)[0]) for s, e in unk]
    return dict(rom=os.path.basename(path), changed=changed, added=added, unknown=unknown)


def summarize(R):
    by = {}
    for c in R['changed']:
        k = c['top']; v = by.setdefault(k, [0, 0, c['off']]); v[0] += c['n']; v[1] += 1
    return sorted(by.items(), key=lambda kv: kv[1][2])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('rom'); ap.add_argument('--out')
    A = ap.parse_args()
    if A.cmd == 'regions':
        R = regions(A.rom)
        if A.out: json.dump(R, open(A.out, 'w'), ensure_ascii=False)
        S = summarize(R)
        print('바뀐 라벨 %d곳, 바뀐 바이트 %d / 빈 곳에 새로 넣은 바이트 %d (%d덩어리)' % (
            len(S), sum(v[0] for k, v in S), sum(x['n'] for x in R['added']), len(R['added'])))
        for k, (n, cnt, o) in S:
            print('%02x:%04x %6d %s' % (o // 0x4000, o % 0x4000 + (0x4000 if o >= 0x4000 else 0), n, k))
