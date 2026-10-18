#!/usr/bin/env python3
"""하트골드 스크립트(a/0/1/2) 간이 역어셈블러 — pret/pokeheartgold 의 script.inc 매크로 표로 명령 길이를 읽어 진입점부터 따라가 「진짜 명령 자리」를 모은다. (Claude 작성, 2026-10-15)
사용:   python script_disasm.py <롬.nds> --check "<파일>@<16진 위치>,…"     → 그 자리가 명령 시작 자리인지(진짜) / 아닌지(자료 속 우연)
        python script_disasm.py <롬.nds> --stat                              → 파일마다 끝까지 읽혔는지 통계
표:     script.inc 는 처음 한 번 인터넷에서 받아 같은 폴더의 script_inc.txt 로 저장한다(받을 수 없으면 직접 넣을 것).
한계:   움직임 자료(ApplyMovement 가 가리키는 덩어리)는 따라가지 않음 — 거기 든 우연한 바이트는 「자료」로 판정됨(원하는 것)."""
import sys, os, re, struct, argparse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, PROJ)
INC = os.path.join(HERE, 'script_inc.txt')
URL = 'https://raw.githubusercontent.com/pret/pokeheartgold/master/asm/macros/script.inc'
SIZES = {'.byte': 1, '.short': 2, '.2byte': 2, '.hword': 2, '.word': 4, '.4byte': 4}

def load_table():
    if not os.path.exists(INC):
        open(INC, 'wb').write(urllib.request.urlopen(URL, timeout=60).read())
    txt = open(INC, encoding='utf-8', errors='replace').read()
    macros = {}
    for m in re.finditer(r'\.macro\s+(\w+)([^\n]*)\n(.*?)\.endm', txt, re.S):
        name, params, body = m.group(1), m.group(2), m.group(3)
        macros[name] = [l.strip() for l in body.split('\n') if l.strip() and not l.strip().startswith('//')]
    ops = {}
    for name, lines in macros.items():
        size = 0; opcode = None; jumps = []; ok = True
        for l in lines:
            l = l.split('//')[0].strip()
            if not l or l.startswith('.if') or l.startswith('.else') or l.startswith('.endif') or l.startswith('.set'): continue
            tok = l.split()
            d = tok[0]
            if d in SIZES:
                if opcode is None and d == '.short':
                    v = ' '.join(tok[1:])
                    try: opcode = int(v.split(',')[0], 0)
                    except ValueError: opcode = v.split(',')[0]      # 기호 상수
                    size += 2; continue
                if d == '.word' and '- . - 4' in l: jumps.append(size)
                n = SIZES[d]
                size += n * max(1, len([x for x in l[len(d):].split(',') if x.strip()]))
            else:
                ok = False                                              # 다른 매크로 호출·알 수 없는 줄 → 길이 불명
        if opcode is not None and ok: ops[name] = (opcode, size, jumps)
    return ops, macros

def build(ops):
    """기호 상수(opcode 가 이름)는 scrcmd.h 가 없으면 못 풂 → 숫자 opcode 만 사용"""
    by = {}
    for n, (op, size, jumps) in ops.items():
        if isinstance(op, int): by[op] = (n, size, jumps)
    return by

TERM = ('End', 'Return', 'GoTo', 'EndStd', 'Kill', 'ScrDefEnd')

def disasm_file(f, by):
    """진입점마다 따라가며 명령 시작 위치 집합을 돌려줌. (시작 집합, 알 수 없는 명령 번호 목록)"""
    starts = set(); unknown = []
    ents = []; p = 0
    while p + 2 <= len(f):
        if struct.unpack_from('<H', f, p)[0] == 0xFD13: p += 2; break
        if p + 4 > len(f): return starts, ['머리말']
        v = struct.unpack_from('<i', f, p)[0]; ents.append(p + 4 + v); p += 4
    work = [e for e in ents if 0 <= e < len(f)]; seen = set()
    while work:
        q = work.pop()
        while 0 <= q + 2 <= len(f) and q not in seen:
            seen.add(q); op = struct.unpack_from('<H', f, q)[0]
            if op not in by: unknown.append((q, op)); break
            name, size, jumps = by[op]; starts.add(q)
            for j in jumps:
                if q + j + 4 <= len(f):
                    t = q + j + 4 + struct.unpack_from('<i', f, q + j)[0]
                    if 0 <= t < len(f) and not name.startswith(('Move', 'Apply')): work.append(t)
            if name in TERM or name == 'GoTo': break
            q += size
    return starts, unknown

def forward_ok(f, off, by, n=6):
    """그 자리에서 앞으로 n 개 명령을 읽어 모두 알려진 명령이고 파일 안이면 True(진짜 코드일 가능성). → (True/False, 읽은 명령 이름들)"""
    q = off; names = []
    for _ in range(n):
        if q + 2 > len(f): return False, names
        op = struct.unpack_from('<H', f, q)[0]
        if op not in by: return False, names + ['?%04X' % op]
        nm, size, _j = by[op]; names.append(nm)
        if q + size > len(f): return False, names
        q += size
        if nm in TERM: break
    return True, names

def main():
    import hg1
    from hg1 import NDS, NARC
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--check', default=None); ap.add_argument('--stat', action='store_true')
    A = ap.parse_args()
    ops, macros = load_table(); by = build(ops)
    print('명령 %d개(숫자 번호 %d개)' % (len(ops), len(by)))
    rom = NDS(open(A.rom, 'rb').read()); S = NARC(rom.get('a/0/1/2')).files
    cache = {}
    def get(fi):
        if fi not in cache: cache[fi] = disasm_file(S[fi], by)
        return cache[fi]
    if A.stat:
        bad = 0
        for fi in range(len(S)):
            st, un = get(fi)
            if un: bad += 1
        print('알 수 없는 명령을 만난 파일 %d / %d' % (bad, len(S)))
    if A.check:
        for it in A.check.split(','):
            fi, off = it.split('@'); fi = int(fi); off = int(off, 16)
            st, un = get(fi)
            if off + 2 > len(S[fi]): print('파일 %d @%X: 파일 길이(%d) 밖' % (fi, off, len(S[fi]))); continue
            op = struct.unpack_from('<H', S[fi], off)[0]
            ok, names = forward_ok(S[fi], off, by)
            print('파일 %d @%X 명령 %04X: %s | 앞으로 읽기 %s %s' % (fi, off, op, '따라가기에서 명령 시작 자리' if off in st else '따라가기에서 못 만남', '성공' if ok else '실패', ' '.join(names)))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
