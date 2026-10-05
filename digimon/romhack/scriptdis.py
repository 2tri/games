"""맵 스크립트 해독기 (금 이벤트 스크립트 명령 → 읽을 수 있는 줄)
명령 표는 pokegold-kr macros/scripts/events.asm 에서 자동으로 만든다.
  python3 scriptdis.py ROM DUMP.json OUT.json     (DUMP = romdump 결과: 맵 이벤트·이름표)
맵마다 사람·표지판·발판·장면·콜백 스크립트를 따라가며 해독하고, 선물·전투·도구·진화 같은 중요한 명령을 모아 둔다."""
import os, re, sys, json, collections
import asmconst, krtext, texts, romanat

KR = asmconst.KR
END = {'end', 'endall', 'reloadend', 'endcallback', 'sjump', 'farsjump', 'memjump', 'jumptext', 'jumptextfaceplayer',
       'jumpstd', 'stopandsjump'}
BRANCH = {'scall', 'sjump', 'iffalse', 'iftrue', 'ifequal', 'ifnotequal', 'ifgreater', 'ifless', 'stopandsjump'}
TEXTS = {'writetext', 'jumptext', 'jumptextfaceplayer', 'farwritetext', 'repeattext'}
KEY = {'givepoke', 'giveegg', 'giveitem', 'verbosegiveitem', 'takeitem', 'checkitem', 'loadwildmon', 'loadtrainer',
       'startbattle', 'checkpoke', 'trade', 'pokemart', 'special', 'warp', 'warpfacing', 'setevent', 'checkevent',
       'clearevent', 'givemoney', 'givecoins', 'playmusic', 'pokepic', 'changeblock', 'changemapblocks', 'loadtemptrainer',
       'callasm', 'farscall', 'farsjump', 'setflag', 'checkflag', 'halloffame', 'credits', 'cry', 'appear', 'disappear'}


def load_cmds():
    src = open(os.path.join(KR, 'macros/scripts/events.asm')).read()
    C = {}
    op = 0
    for m in re.finditer(r'const (\w+)_command[^\n]*\nMACRO (\w+)\n(.*?)\nENDM', src, re.S):
        name, body = m.group(1), m.group(3)
        i = body.find('db %s_command' % name)
        params = []
        if i >= 0:
            depth = 0
            for ln in body[i:].split('\n')[1:]:
                s = ln.strip()
                if s.startswith('if '): depth += 1; continue
                if s.startswith('endc'):
                    depth = max(0, depth - 1); continue
                if depth: continue
                mm = re.match(r'(db|dw|dba|dn|bigdw|dwb|dbw)\b\s*([^;]*);?\s*(.*)', s)
                if mm: params.append((mm.group(1), mm.group(3).strip() or mm.group(2).strip()))
        C[op] = (name, params); op += 1
    return C


CMDS = load_cmds()
SIZE = {'db': 1, 'dn': 1, 'dw': 2, 'bigdw': 2, 'dba': 3, 'dwb': 3, 'dbw': 3}


class Dis:
    def __init__(self, d, names=None):
        self.d = d; self.n = names or {}

    def fmt(self, kind, val):
        n = self.n
        k = kind.lower()
        if 'pokemon' in k or 'species' in k: return '%s(%d)' % (n.get('mon', {}).get(val, '?'), val)
        if 'item' in k and 'ptr' not in k and 'pointer' not in k: return '%s(%d)' % (n.get('item', {}).get(val, '?'), val)
        if k.startswith('map') and isinstance(val, int): return str(val)
        return str(val) if not isinstance(val, int) else ('%d' % val if val < 256 else '$%04x' % val)

    def one(self, a):
        d = self.d; op = d[a]
        if op not in CMDS: return None
        name, params = CMDS[op]; p = a + 1; args = []
        for typ, cm in params:
            if typ in ('db', 'dn'): v = d[p]
            elif typ in ('dw', 'bigdw'): v = d[p] | d[p + 1] << 8 if typ == 'dw' else d[p] << 8 | d[p + 1]
            elif typ == 'dba': v = (d[p], d[p + 1] | d[p + 2] << 8)
            elif typ == 'dwb': v = (d[p] | d[p + 1] << 8, d[p + 2])
            elif typ == 'dbw': v = (d[p], d[p + 1] | d[p + 2] << 8)
            args.append((cm, v)); p += SIZE[typ]
        if name == 'givepoke' and len(args) >= 4 and args[3][1]:
            args.append(('nickname_pointer', d[p] | d[p + 1] << 8)); args.append(('ot_name_pointer', d[p + 2] | d[p + 3] << 8)); p += 4
        return name, args, p - a

    def script(self, start, limit=4000):
        """start 부터 흐름을 따라 해독 → {주소: (이름, 인자, 길이)}, 대사 [(주소, 글)]"""
        d = self.d; seen = {}; todo = [start]; txt = []; far = []
        while todo and len(seen) < limit:
            a = todo.pop()
            while a not in seen and a < len(d):
                r = self.one(a)
                if r is None: seen[a] = ('??', [('byte', d[a])], 1); break
                name, args, ln = r; seen[a] = r
                bank = a // 0x4000
                for cm, v in args:
                    if name in BRANCH and isinstance(v, int) and 0x4000 <= v < 0x8000 and 'pointer' in cm:
                        todo.append(romanat.off(bank, v))
                if name in ('farscall', 'farsjump') and isinstance(args[0][1], tuple):
                    b, p = args[0][1]; far.append(romanat.off(b, p))
                if name in TEXTS:
                    v = args[0][1]
                    ta = romanat.off(v[0], v[1]) if isinstance(v, tuple) else (romanat.off(bank, v) if 0x4000 <= v < 0x8000 else None)
                    if ta is not None and ta < len(d):
                        t = texts.read_text(d, ta)
                        if t: txt.append((ta, t[2]))
                if name in END: break
                a += ln
        return seen, txt, far

    def render(self, seen):
        out = []
        for a in sorted(seen):
            name, args, ln = seen[a]
            out.append('%06x %s %s' % (a, name, ', '.join(self.fmt(cm, v) if not isinstance(v, tuple) else '%02x:%04x' % v for cm, v in args)))
        return out


def map_scripts(d, m, dis):
    """맵 하나: 스크립트 머리(장면·콜백) + 이벤트(사람·표지판·발판)에서 시작점을 모아 해독"""
    bank = m['scripts_at'] // 0x4000; a = m['scripts_at']
    starts = []
    n = d[a]; a += 1
    for k in range(min(n, 16)): starts.append(('scene%d' % k, romanat.off(bank, d[a] | d[a + 1] << 8))); a += 4
    n = d[a]; a += 1
    for k in range(min(n, 16)): starts.append(('callback%d' % d[a], romanat.off(bank, d[a + 1] | d[a + 2] << 8))); a += 3
    ev = m['events']; extra = []
    for k, c in enumerate(ev['coords']): starts.append(('coord%d' % k, romanat.off(bank, c['script'])))
    for k, b in enumerate(ev['bgs']):
        p = romanat.off(bank, b['script'])
        if b['kind'] == 7: extra.append(('hiddenitem%d' % k, d[p + 2], d[p] | d[p + 1] << 8))
        elif b['kind'] in (5, 6): starts.append(('bg%d' % k, romanat.off(bank, d[p + 2] | d[p + 3] << 8)))
        else: starts.append(('bg%d' % k, p))
    for k, o in enumerate(ev['objects']):
        p = romanat.off(bank, o['script']); typ = o['pal_type'] & 15
        if typ == 1: extra.append(('itemball%d' % k, d[p], d[p + 1]))
        elif typ == 2:
            extra.append(('trainer%d' % k, d[p + 2], d[p + 3]))
            starts.append(('trainer%d_after' % k, romanat.off(bank, d[p + 10] | d[p + 11] << 8)))
        else: starts.append(('obj%d' % k, p))
    res = []
    for tag, s in starts:
        if not (0 <= s < len(d)): continue
        seen, txt, far = dis.script(s)
        res.append(dict(tag=tag, start=s, lines=dis.render(seen), texts=[t for _, t in txt],
                        key=[dis.render({a: v})[0] for a, v in seen.items() if v[0] in KEY]))
    return res, extra


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); D = json.load(open(sys.argv[2]))
    names = {'mon': {s['no']: s['name'] for s in D['species']}, 'item': {i['no']: i['name'] for i in D['items']}}
    dis = Dis(d, names); out = []
    for m in D['maps']:
        if 'error' in m: continue
        try: sc, extra = map_scripts(d, m, dis)
        except Exception as ex: sc, extra = [], [('error', repr(ex))]
        out.append(dict(group=m['group'], num=m['num'], label=m['label'], area=m['area'], scripts=sc, extra=extra))
    json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False)
    cnt = collections.Counter()
    for m in out:
        for s in m['scripts']:
            for k in s['key']: cnt[k.split()[1]] += 1
    print('맵 %d, 스크립트 %d, 중요 명령 %s' % (len(out), sum(len(m['scripts']) for m in out), dict(cnt.most_common(20))))
