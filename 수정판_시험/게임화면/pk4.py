#!/usr/bin/env python3
"""4세대 포켓몬 자료(PK4) 읽기·바꾸기 — 파티용 236바이트 (Claude 작성, 2026-10-15)
문서: Project Pokémon 「Pokémon NDS structure」. 앞 8바이트 = PID(4)·잘못된 알 표시(2)·검산(2), 128바이트 = 블록 A~D(32바이트씩, PID 로 순서 섞임, 검산을 씨앗으로 u16 단위 암호),
      뒤 100바이트 = 파티 자료(레벨·체력·능력치, PID 를 씨앗으로 암호).
암호:  seed = seed * 0x41C64E6D + 0x6073 (32비트), 각 u16 에 seed>>16 을 XOR."""
import struct
ORDERS = ['ABCD', 'ABDC', 'ACBD', 'ACDB', 'ADBC', 'ADCB', 'BACD', 'BADC', 'BCAD', 'BCDA', 'BDAC', 'BDCA',
          'CABD', 'CADB', 'CBAD', 'CBDA', 'CDAB', 'CDBA', 'DABC', 'DACB', 'DBAC', 'DBCA', 'DCAB', 'DCBA']

def _crypt(buf, seed):
    out = bytearray(buf)
    for i in range(0, len(out), 2):
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        v = struct.unpack_from('<H', out, i)[0] ^ (seed >> 16)
        struct.pack_into('<H', out, i, v)
    return out

def decode(raw):
    """→ dict(pid, blocks{'A':32바이트,...}, party=100바이트 풀린 것)"""
    pid = struct.unpack_from('<I', raw, 0)[0]; chk = struct.unpack_from('<H', raw, 6)[0]
    dec = _crypt(raw[8:136], chk)
    order = ORDERS[((pid >> 13) & 31) % 24]
    blocks = {}
    for pos, ch in enumerate(order): blocks[ch] = bytes(dec[pos * 32:pos * 32 + 32])
    party = bytes(_crypt(raw[136:236], pid)) if len(raw) >= 236 else b''
    return {'pid': pid, 'blocks': blocks, 'party': party, 'order': order}

def encode(d):
    pid = d['pid']; order = ORDERS[((pid >> 13) & 31) % 24]
    body = b''.join(d['blocks'][ch] for ch in order)
    chk = sum(struct.unpack('<64H', body)) & 0xFFFF
    head = struct.pack('<IHH', pid, 0, chk)
    enc = bytes(_crypt(body, chk))
    party = bytes(_crypt(d['party'], pid)) if d['party'] else b''
    return head + enc + party

def species(raw): return struct.unpack_from('<H', decode(raw)['blocks']['A'], 0)[0]

def with_species(raw, sp, level=None):
    d = decode(raw)
    a = bytearray(d['blocks']['A']); struct.pack_into('<H', a, 0, sp); d['blocks']['A'] = bytes(a)
    if level is not None and d['party']:
        p = bytearray(d['party']); p[4] = level; d['party'] = bytes(p)       # 파티 자료 0x04 = 레벨
    return encode(d)
