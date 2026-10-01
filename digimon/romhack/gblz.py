# 금판(2세대) 그림 압축 풀기
def decompress(d, off, limit=0x4000):
    out=bytearray(); i=off
    while True:
        b=d[i]; i+=1
        if b==0xFF: break
        cmd=b>>5
        if cmd==7:
            cmd=(b>>2)&7; n=(((b&3)<<8)|d[i])+1; i+=1
        else: n=(b&0x1f)+1
        if cmd==0: out+=d[i:i+n]; i+=n
        elif cmd==1: out+=bytes([d[i]])*n; i+=1
        elif cmd==2:
            a,c=d[i],d[i+1]; i+=2
            for k in range(n): out.append(a if k%2==0 else c)
        elif cmd==3: out+=bytes(n)
        else:
            o=d[i]; i+=1
            if o&0x80: src=len(out)-(o&0x7f)-1
            else: src=(o<<8)|d[i]; i+=1
            if cmd==4:
                for k in range(n): out.append(out[src+k])
            elif cmd==5:
                for k in range(n): x=out[src+k]; out.append(int('{:08b}'.format(x)[::-1],2))
            elif cmd==6:
                for k in range(n): out.append(out[src-k])
        if len(out)>limit: raise ValueError('too long')
    return bytes(out), i

# ── 압축 (욕심쟁이 방식: 같은 바이트 반복 · 0 반복 · 앞 내용 베끼기 · 그대로) ──
def _cmd(out, cmd, n):
    n -= 1
    if n < 32 and cmd != 7: out.append((cmd << 5) | n)
    else: out += bytes([0xE0 | (cmd << 2) | (n >> 8), n & 0xFF])

def compress(src):
    src = bytes(src); out = bytearray(); lit = bytearray(); i = 0; n = len(src)
    def flush():
        j = 0
        while j < len(lit):
            k = min(1024, len(lit) - j); _cmd(out, 0, k); out.extend(lit[j:j + k]); j += k
        lit.clear()
    while i < n:
        # 같은 바이트 반복
        r = 1
        while i + r < n and src[i + r] == src[i] and r < 1024: r += 1
        # 앞 내용 베끼기 (가장 긴 것)
        best_len, best_src = 0, 0
        lo = max(0, i - 0x7FFF)
        for s in range(lo, i):
            L = 0
            while i + L < n and src[s + L] == src[i + L] and L < 1024: L += 1
            if L > best_len: best_len, best_src = L, s
        if r >= 3 and r >= best_len:
            flush(); _cmd(out, 3 if src[i] == 0 else 1, r)
            if src[i] != 0: out.append(src[i])
            i += r
        elif best_len >= 4:
            flush(); _cmd(out, 4, best_len)
            back = i - best_src - 1
            if back < 0x80: out.append(0x80 | back)
            else: out += bytes([best_src >> 8, best_src & 0xFF])
            i += best_len
        else:
            lit.append(src[i]); i += 1
    flush(); out.append(0xFF)
    return bytes(out)
