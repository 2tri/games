import struct
ORD = ['ABCD','ABDC','ACBD','ACDB','ADBC','ADCB','BACD','BADC','BCAD','BCDA','BDAC','BDCA','CABD','CADB','CBAD','CBDA','CDAB','CDBA','DABC','DACB','DBAC','DBCA','DCAB','DCBA']
def lcg(seed):
    while True:
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        yield seed >> 16
def xor_words(words, seed):
    g = lcg(seed); return [w ^ next(g) for w in words]
def decode(raw):
    """236바이트(파티) → dict(blocks={'A':bytes32,...}, party=bytes100, pid, ck)"""
    pid, _, ck = struct.unpack_from('<IHH', raw, 0)
    d = xor_words(struct.unpack_from('<64H', raw, 8), ck)
    b = struct.pack('<64H', *d); order = ORD[((pid >> 13) & 31) % 24]
    blocks = {order[i]: b[i * 32:(i + 1) * 32] for i in range(4)}
    party = struct.pack('<50H', *xor_words(struct.unpack_from('<50H', raw, 136), pid)) if len(raw) >= 236 else b''
    return dict(pid=pid, ck=ck, order=order, blocks=blocks, party=party)
def encode(pk):
    pid = pk['pid']; order = pk['order']
    b = b''.join(pk['blocks'][c] for c in order)
    ck = sum(struct.unpack('<64H', b)) & 0xFFFF
    enc = struct.pack('<64H', *xor_words(struct.unpack('<64H', b), ck))
    party = struct.pack('<50H', *xor_words(struct.unpack('<50H', pk['party']), pid))
    return struct.pack('<IHH', pid, 0, ck) + enc + party
def species(pk): return struct.unpack_from('<H', pk['blocks']['A'], 0)[0]
def moves(pk): return list(struct.unpack_from('<4H', pk['blocks']['B'], 0))
def pps(pk): return list(pk['blocks']['B'][8:12])
def level(pk): return pk['party'][4]

import sys, os
sys.path.insert(0, '/home/user/games')
GROWTH_EXP = {
    0: lambda n: n ** 3,
    4: lambda n: 4 * n ** 3 // 5,
    5: lambda n: 5 * n ** 3 // 4,
    3: lambda n: max(0, 6 * n ** 3 // 5 - 15 * n ** 2 + 100 * n - 140),
}
def exp_for(growth, n):
    if growth in GROWTH_EXP: return GROWTH_EXP[growth](n)
    if growth == 1:   # 변동(Erratic)
        if n <= 50: return n ** 3 * (100 - n) // 50
        if n <= 68: return n ** 3 * (150 - n) // 100
        if n <= 98: return n ** 3 * ((1911 - 10 * n) // 3) // 500
        return n ** 3 * (160 - n) // 100
    if growth == 2:   # 요동(Fluctuating)
        if n <= 15: return n ** 3 * ((n + 1) // 3 + 24) // 50
        if n <= 35: return n ** 3 * (n + 14) // 50
        return n ** 3 * (n // 2 + 32) // 50
    return n ** 3
def calc_stats(base, lv, iv=31):
    hp = (2 * base[0] + iv) * lv // 100 + lv + 10
    f = lambda b: (2 * b + iv) * lv // 100 + 5
    return [hp] + [f(b) for b in base[1:]]     # base = [hp, at, df, sp, sa, sd]; 반환 순서 hp, at, df, sp, sa, sd
def make_mon(template_raw, species, lv, moves, personal, item=0, exp=None, pp=None):
    """template 236바이트(기존 아구몬)를 바탕으로 종·레벨·기술·능력치를 새로 씀 → 236바이트"""
    pk = decode(template_raw)
    A = bytearray(pk['blocks']['A']); B = bytearray(pk['blocks']['B']); P = bytearray(pk['party'])
    struct.pack_into('<H', A, 0, species); struct.pack_into('<H', A, 2, item)
    growth = personal[species][19]
    struct.pack_into('<I', A, 8, exp_for(growth, lv) if exp is None else exp)
    for k in range(4):
        struct.pack_into('<H', B, 2 * k, moves[k] if k < len(moves) else 0)
        B[8 + k] = (pp.get(moves[k], 10) if pp else 10) if k < len(moves) and moves[k] else 0
        B[12 + k] = 0
    base = list(personal[species][:6])
    st = calc_stats(base, lv)
    P[4] = lv
    struct.pack_into('<HH', P, 6, st[0], st[0])
    struct.pack_into('<5H', P, 10, st[1], st[2], st[3], st[4], st[5])   # 파티 칸 순서: 공 방 스피드 특공 특방 (personal 도 같은 순서)
    pk['blocks']['A'] = bytes(A); pk['blocks']['B'] = bytes(B); pk['party'] = bytes(P)
    return encode(pk)
