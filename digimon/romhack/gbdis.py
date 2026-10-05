"""게임보이(LR35902) 역어셈블러 — 바뀐 코드 확인용 (작게, 표준 명령표)"""
R8 = ['b', 'c', 'd', 'e', 'h', 'l', '[hl]', 'a']
R16 = ['bc', 'de', 'hl', 'sp']
R16S = ['bc', 'de', 'hl', 'af']
CC = ['nz', 'z', 'nc', 'c']
ALU = ['add a,', 'adc a,', 'sub', 'sbc a,', 'and', 'xor', 'or', 'cp']
CB = ['rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'swap', 'srl']


def one(d, a, base=0):
    """→ (글, 길이, 대상주소 또는 None, 종류: call/jp/jr/ret/None)"""
    op = d[a]
    n8 = lambda: d[a + 1]
    n16 = lambda: d[a + 1] | d[a + 2] << 8
    rel = lambda: base + a + 2 + ((d[a + 1] ^ 0x80) - 0x80)
    if op == 0x00: return 'nop', 1, None, None
    if op == 0x76: return 'halt', 1, None, None
    if 0x40 <= op < 0x80: return 'ld %s, %s' % (R8[(op >> 3) & 7], R8[op & 7]), 1, None, None
    if 0x80 <= op < 0xc0: return '%s %s' % (ALU[(op >> 3) & 7], R8[op & 7]), 1, None, None
    T = {
        0x01: lambda: ('ld bc, $%04x' % n16(), 3), 0x11: lambda: ('ld de, $%04x' % n16(), 3), 0x21: lambda: ('ld hl, $%04x' % n16(), 3),
        0x31: lambda: ('ld sp, $%04x' % n16(), 3), 0x02: lambda: ('ld [bc], a', 1), 0x12: lambda: ('ld [de], a', 1),
        0x22: lambda: ('ld [hli], a', 1), 0x32: lambda: ('ld [hld], a', 1), 0x0a: lambda: ('ld a, [bc]', 1), 0x1a: lambda: ('ld a, [de]', 1),
        0x2a: lambda: ('ld a, [hli]', 1), 0x3a: lambda: ('ld a, [hld]', 1), 0x08: lambda: ('ld [$%04x], sp' % n16(), 3),
        0x07: lambda: ('rlca', 1), 0x0f: lambda: ('rrca', 1), 0x17: lambda: ('rla', 1), 0x1f: lambda: ('rra', 1),
        0x27: lambda: ('daa', 1), 0x2f: lambda: ('cpl', 1), 0x37: lambda: ('scf', 1), 0x3f: lambda: ('ccf', 1), 0x10: lambda: ('stop', 2),
        0xe0: lambda: ('ldh [$ff%02x], a' % n8(), 2), 0xf0: lambda: ('ldh a, [$ff%02x]' % n8(), 2),
        0xe2: lambda: ('ld [$ff00+c], a', 1), 0xf2: lambda: ('ld a, [$ff00+c]', 1),
        0xea: lambda: ('ld [$%04x], a' % n16(), 3), 0xfa: lambda: ('ld a, [$%04x]' % n16(), 3),
        0xe8: lambda: ('add sp, %d' % ((n8() ^ 0x80) - 0x80), 2), 0xf8: lambda: ('ld hl, sp%+d' % ((n8() ^ 0x80) - 0x80), 2),
        0xf9: lambda: ('ld sp, hl', 1), 0xe9: lambda: ('jp hl', 1), 0xf3: lambda: ('di', 1), 0xfb: lambda: ('ei', 1),
        0xc6: lambda: ('add a, $%02x' % n8(), 2), 0xce: lambda: ('adc a, $%02x' % n8(), 2), 0xd6: lambda: ('sub $%02x' % n8(), 2),
        0xde: lambda: ('sbc a, $%02x' % n8(), 2), 0xe6: lambda: ('and $%02x' % n8(), 2), 0xee: lambda: ('xor $%02x' % n8(), 2),
        0xf6: lambda: ('or $%02x' % n8(), 2), 0xfe: lambda: ('cp $%02x' % n8(), 2), 0xd9: lambda: ('reti', 1),
    }
    if op in T:
        s, l = T[op]()
        return s, l, (None if op != 0xe9 else None), ('ret' if op == 0xd9 else ('jp' if op == 0xe9 else None))
    lo = op & 7; r = (op >> 3) & 7
    if op & 0xc7 == 0x04: return 'inc %s' % R8[r], 1, None, None
    if op & 0xc7 == 0x05: return 'dec %s' % R8[r], 1, None, None
    if op & 0xc7 == 0x06: return 'ld %s, $%02x' % (R8[r], n8()), 2, None, None
    if op & 0xcf == 0x03: return 'inc %s' % R16[op >> 4], 1, None, None
    if op & 0xcf == 0x0b: return 'dec %s' % R16[op >> 4], 1, None, None
    if op & 0xcf == 0x09: return 'add hl, %s' % R16[op >> 4], 1, None, None
    if op == 0x18: t = rel(); return 'jr $%04x' % t, 2, t, 'jr'
    if op in (0x20, 0x28, 0x30, 0x38): t = rel(); return 'jr %s, $%04x' % (CC[(op >> 3) & 3], t), 2, t, 'jrc'
    if op == 0xc3: t = n16(); return 'jp $%04x' % t, 3, t, 'jp'
    if op in (0xc2, 0xca, 0xd2, 0xda): t = n16(); return 'jp %s, $%04x' % (CC[(op >> 3) & 3], t), 3, t, 'jpc'
    if op == 0xcd: t = n16(); return 'call $%04x' % t, 3, t, 'call'
    if op in (0xc4, 0xcc, 0xd4, 0xdc): t = n16(); return 'call %s, $%04x' % (CC[(op >> 3) & 3], t), 3, t, 'call'
    if op == 0xc9: return 'ret', 1, None, 'ret'
    if op in (0xc0, 0xc8, 0xd0, 0xd8): return 'ret %s' % CC[(op >> 3) & 3], 1, None, None
    if op & 0xcf == 0xc5: return 'push %s' % R16S[(op >> 4) & 3], 1, None, None
    if op & 0xcf == 0xc1: return 'pop %s' % R16S[(op >> 4) & 3], 1, None, None
    if op & 0xc7 == 0xc7: return 'rst $%02x' % (op & 0x38), 1, op & 0x38, 'rst'
    if op == 0xcb:
        c = d[a + 1]; reg = R8[c & 7]; k = c >> 6; b = (c >> 3) & 7
        if k == 0: return '%s %s' % (CB[b], reg), 2, None, None
        return '%s %d, %s' % (['', 'bit', 'res', 'set'][k], b, reg), 2, None, None
    return 'db $%02x' % op, 1, None, None


def block(d, start, end, label_fn=None, cpu_base=None):
    """[start, end) 를 줄 목록으로 (롬 위치, 바이트, 글)"""
    out = []; a = start
    bank = start // 0x4000
    base = (0x4000 - (bank * 0x4000) if bank else 0) if cpu_base is None else cpu_base
    while a < end:
        s, l, t, k = one(d, a, base)
        if t is not None and label_fn:
            nm = label_fn(t, bank)
            if nm: s += '  ; ' + nm
        out.append((a, d[a:a + l].hex(), s)); a += l
    return out
