"""onlinesequencer.net 곡 자료(get_proto) 읽기: 음표(높이·시작·길이·악기) 목록으로."""
import struct, urllib.request, os, json
def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7F) << s; s += 7
        if c < 0x80: return r, i
def fields(b):
    i = 0; out = []
    while i < len(b):
        k, i = varint(b, i); f, w = k >> 3, k & 7
        if w == 0: v, i = varint(b, i)
        elif w == 5: v = struct.unpack('<f', b[i:i + 4])[0]; i += 4
        elif w == 1: v = struct.unpack('<d', b[i:i + 8])[0]; i += 8
        elif w == 2: n, i = varint(b, i); v = b[i:i + n]; i += n
        else: raise ValueError(w)
        out.append((f, w, v))
    return out
def fetch(sid, cache=os.path.dirname(os.path.abspath(__file__)) + '/../../ref/midi'):
    p = '%s/os_%s.bin' % (cache, sid)
    if not os.path.exists(p):
        req = urllib.request.Request('https://onlinesequencer.net/app/api/get_proto.php?id=%s' % sid, headers={'User-Agent': 'Mozilla'})
        open(p, 'wb').write(urllib.request.urlopen(req, timeout=30).read())
    return open(p, 'rb').read()
def load(sid):
    b = fetch(sid); bpm = 110; notes = []
    for f, w, v in fields(b):
        if f == 1 and w == 2:
            for f2, w2, v2 in fields(v):
                if f2 == 1: bpm = v2
        if f == 2 and w == 2:
            d = {'type': 0, 'time': 0.0, 'len': 1.0, 'inst': 0, 'vol': 1.0}
            for f2, w2, v2 in fields(v):
                d[{1: 'type', 2: 'time', 3: 'len', 4: 'inst', 5: 'vol'}.get(f2, f2)] = v2
            notes.append(d)
    return bpm, notes
if __name__ == '__main__':
    import sys
    bpm, n = load(sys.argv[1])
    print('bpm', bpm, 'notes', len(n))
    from collections import Counter
    print('inst', Counter(x['inst'] for x in n)); print('type range', min(x['type'] for x in n), max(x['type'] for x in n))
    for x in sorted(n, key=lambda x: x['time'])[:30]: print(x)
