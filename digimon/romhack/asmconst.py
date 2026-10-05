"""pokegold-kr 디스어셈블리 constants/*.asm 의 const_def / const / DEF EQU 를 읽어 이름 ↔ 값 표로
  C = asmconst.load(); C.val('EFFECT_BURN_HIT'); C.names('EFFECT_') → {값: 이름}"""
import os, re

KR = os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr')


class Consts:
    def __init__(self):
        self.v = {}
        self.order = []

    def val(self, n): return self.v[n]

    def names(self, prefix, first=True):
        out = {}
        for n in self.order:
            if n.startswith(prefix) and isinstance(self.v[n], int):
                if first: out.setdefault(self.v[n], n)
                else: out[self.v[n]] = n
        return out


def _num(s, C):
    s = s.strip().split(';')[0].strip()
    s = s.replace('$', '0x').replace('%', '0b')
    try:
        return int(eval(re.sub(r'[A-Za-z_]\w*', lambda m: str(C.v.get(m.group(0), m.group(0))) if m.group(0) not in ('0x', '0b') else m.group(0), s), {}))
    except Exception:
        return None


def load(files=None):
    C = Consts()
    d = os.path.join(KR, 'constants')
    files = files or sorted(f for f in os.listdir(d) if f.endswith('.asm'))
    for f in files:
        cv, step = 0, 1
        for ln in open(os.path.join(d, f), encoding='utf-8', errors='replace'):
            ln = ln.split(';')[0].rstrip()
            s = ln.strip()
            if not s: continue
            m = re.match(r'const_def\s*(.*)', s)
            if m:
                a = [x for x in m.group(1).split(',') if x.strip()]
                cv = _num(a[0], C) if a else 0; step = _num(a[1], C) if len(a) > 1 else 1
                continue
            m = re.match(r'const\s+(\w+)', s)
            if m:
                C.v[m.group(1)] = cv; C.order.append(m.group(1)); cv += step; continue
            m = re.match(r'const_skip\s*(.*)', s)
            if m: cv += step * (_num(m.group(1), C) if m.group(1).strip() else 1); continue
            m = re.match(r'const_next\s+(.*)', s)
            if m: cv = _num(m.group(1), C); continue
            m = re.match(r'DEF\s+(\w+)\s+EQU\s+(.*)', s) or re.match(r'DEF\s+(\w+)\s*=\s*(.*)', s)
            if m:
                x = _num(m.group(2).replace('const_value', str(cv)), C)
                if x is not None: C.v[m.group(1)] = x; C.order.append(m.group(1))
                continue
            m = re.match(r'(\w+)\s+EQU\s+(.*)', s)
            if m:
                x = _num(m.group(2), C)
                if x is not None: C.v[m.group(1)] = x; C.order.append(m.group(1))
    return C


if __name__ == '__main__':
    C = load()
    for p in ('EFFECT_', 'GROWTH_', 'EGG_', 'HELD_', 'MUSIC_', 'SPRITE_'):
        print(p, len(C.names(p)), list(C.names(p).items())[:5])
    print(C.v.get('NUM_ITEMS'), C.v.get('NUM_TMS'), C.v.get('NUM_HMS'), C.v.get('NUM_TYPES'), C.v.get('NUM_TRAINER_CLASSES'))
