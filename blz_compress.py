"""뒤에서부터 압축(BLZ, 오버레이용): hg_scan.blz_decompress 의 역. 압축 파일 = 압축 조각(뒤집힘) + 머리 8바이트(압축길이|머리길이<<24, 늘어난 길이)"""
import struct
def blz_compress(D):
    R = bytes(D[::-1]); n = len(R)
    out = bytearray(); i = 0
    head = {}                                  # 3바이트 → 최근 위치들
    flags_pos = None; bit = 0
    def add_pos(p):
        if p + 3 <= n: head.setdefault(R[p:p + 3], []).append(p)
    while i < n:
        if bit == 0: flags_pos = len(out); out.append(0); bit = 8
        best_len = 0; best_disp = 0
        if i + 3 <= n:
            cands = head.get(R[i:i + 3], [])
            for p in reversed(cands[-64:]):
                d = i - p
                if d < 3: continue
                if d > 4098: break
                l = 3
                while l < 18 and i + l < n and R[p + l] == R[i + l]: l += 1
                if l > best_len: best_len, best_disp = l, d
                if l == 18: break
        if best_len >= 3:
            out[flags_pos] |= 0x80 >> (8 - bit)
            v = ((best_len - 3) << 12) | (best_disp - 3); out += struct.pack('>H', v)
            for k in range(best_len): add_pos(i + k)
            i += best_len
        else:
            out.append(R[i]); add_pos(i); i += 1
        bit -= 1
    comp = bytes(out)[::-1]
    clen = len(comp) + 8
    return comp + struct.pack('<II', clen | (8 << 24), len(D) - clen)
if __name__ == '__main__':
    import sys, hg_scan, os
    data = os.urandom(0) + bytes(range(256)) * 40 + b'abcabcabc' * 100
    c = blz_compress(data); d = hg_scan.blz_decompress(c); print(len(data), len(c), d == data)
