"""한글판 금 글자 부호 ↔ 문자열"""
import json, os
_M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charmap.json')))
ENC = {k: bytes.fromhex(v) for k, v in _M['kr'].items()}
for k, v in _M['single'].items():
    if len(k) == 1 and k not in ENC: ENC[k] = bytes.fromhex(v)
DEC2 = {v: k for k, v in ENC.items() if len(v) == 2}
DEC1 = {}
for k, v in _M['single'].items():          # 한 바이트: 처음 정의된 것 (제어 문자는 <..>)
    b = int(v, 16)
    if b not in DEC1: DEC1[b] = k

def decode(d, i=0, end=None, stop=0x50):
    out = []; n = end if end is not None else len(d)
    while i < n:
        b = d[i]
        if b == stop: break
        if 1 <= b <= 0x0b and i + 1 < n and bytes(d[i:i + 2]) in DEC2:
            out.append(DEC2[bytes(d[i:i + 2])]); i += 2; continue
        out.append(DEC1.get(b, '{%02x}' % b)); i += 1
    return ''.join(out)

def encode(s):
    out = bytearray()
    for ch in s:
        if ch not in ENC: raise KeyError('부호 없는 글자: %r' % ch)
        out += ENC[ch]
    return bytes(out)
