"""LZ10(0x10) 압축·풀기 — DS BIOS 형식. (Claude 작성, 2026-10-13)
  decompress(b) -> bytes | None        compress(data) -> bytes (간단한 탐욕 방식, 풀면 항상 원본과 같음)"""

def decompress(d):
    if len(d) < 5 or d[0] != 0x10: return None
    n = d[1] | d[2] << 8 | d[3] << 16; out = bytearray(); i = 4
    try:
        while len(out) < n:
            flags = d[i]; i += 1
            for b in range(8):
                if len(out) >= n: break
                if flags & (0x80 >> b):
                    ln = (d[i] >> 4) + 3; disp = ((d[i] & 0xF) << 8 | d[i + 1]) + 1; i += 2
                    if disp > len(out): return None
                    for _ in range(ln): out.append(out[-disp])
                else:
                    out.append(d[i]); i += 1
    except IndexError:
        return None
    return bytes(out[:n])

def compress(data):
    n = len(data); out = bytearray([0x10, n & 255, (n >> 8) & 255, (n >> 16) & 255])
    i = 0
    head = {}                                     # 3바이트 → 최근 위치 목록
    def add(pos):
        if pos + 2 < n: head.setdefault(data[pos:pos + 3], []).append(pos)
    while i < n:
        flags = 0; chunk = bytearray()
        for b in range(8):
            if i >= n: break
            best_len = 0; best_disp = 0
            if i + 2 < n:
                for p in reversed(head.get(data[i:i + 3], [])[-32:]):
                    disp = i - p
                    if disp > 4096: break
                    ln = 3
                    while ln < 18 and i + ln < n and data[p + ln] == data[i + ln]: ln += 1
                    if ln > best_len: best_len, best_disp = ln, disp
                    if ln == 18: break
            if best_len >= 3:
                flags |= 0x80 >> b
                v = best_disp - 1
                chunk.append(((best_len - 3) << 4) | (v >> 8)); chunk.append(v & 255)
                for k in range(best_len): add(i + k)
                i += best_len
            else:
                chunk.append(data[i]); add(i); i += 1
        out.append(flags); out += chunk
    return bytes(out)

if __name__ == '__main__':
    import os
    t = bytes(range(256)) * 4 + b'\x00' * 500 + os.urandom(300)
    assert decompress(compress(t)) == t
    print('LZ10 왕복 OK', len(t), '->', len(compress(t)))
