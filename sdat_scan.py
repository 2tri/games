#!/usr/bin/env python3
"""음악 구조 조사 (롬은 읽기만) — 노래를 디지몬 노래로 바꾸기 위한 첫 조사 (2026-10-14)
사용:   python sdat_scan.py "<롬.nds>"    → sdat_목록.txt
하는 일: 롬 안 SDAT(사운드 묶음)를 찾아 곡(SEQ)·곡 묶음·악기 뱅크·파형 묶음·스트림 목록을 이름·크기와 함께 적는다.
        곡마다 쓰는 뱅크 번호·볼륨·플레이어도 적는다(같은 뱅크를 쓰는 곡끼리 악기가 같다).
        맵·장면 이름이 붙은 곡(SEQ_GS_…)을 「어느 장면 노래인지」 바꿀 목록의 바탕으로 쓴다."""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS

KINDS = ('SEQ', 'SEQARC', 'BANK', 'WAVEARC', 'PLAYER', 'GROUP', 'PLAYER2', 'STRM')

def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def u32(d, o): return struct.unpack_from('<I', d, o)[0]

def cstr(d, o):
    e = d.find(b'\0', o)
    return d[o:e].decode('latin1') if e >= 0 else ''

def parse_sdat(d):
    if d[:4] != b'SDAT': return None
    symb_o, symb_s, info_o, info_s, fat_o, fat_s = struct.unpack_from('<6I', d, 0x10)
    names = {k: [] for k in KINDS}
    if symb_o and d[symb_o:symb_o + 4] == b'SYMB':
        for ki, k in enumerate(KINDS):
            ro = u32(d, symb_o + 8 + 4 * ki)
            if not ro: continue
            base = symb_o + ro; n = u32(d, base)
            for i in range(n):
                if k == 'SEQARC':
                    no = u32(d, base + 4 + 8 * i); names[k].append(cstr(d, symb_o + no) if no else '')
                else:
                    no = u32(d, base + 4 + 4 * i); names[k].append(cstr(d, symb_o + no) if no else '')
    info = {k: [] for k in KINDS}
    for ki, k in enumerate(KINDS):
        ro = u32(d, info_o + 8 + 4 * ki)
        if not ro: continue
        base = info_o + ro; n = u32(d, base)
        for i in range(n):
            eo = u32(d, base + 4 + 4 * i)
            info[k].append(d[info_o + eo:info_o + eo + 16] if eo else None)
    fat = []
    n = u32(d, fat_o + 8)
    for i in range(n):
        off, size = struct.unpack_from('<II', d, fat_o + 12 + 16 * i); fat.append((off, size))
    return names, info, fat

def main():
    rom = NDS(open(sys.argv[1], 'rb').read())
    L = ['== 음악 구조 — 롬 %s' % rom.code]
    sdats = [p for p in rom.paths if p.lower().endswith('.sdat')]
    if not sdats:
        for p in rom.paths:
            try:
                if rom.get(p)[:4] == b'SDAT': sdats.append(p)
            except Exception: pass
    L.append('SDAT 파일: %s' % sdats)
    for p in sdats:
        d = rom.get(p); r = parse_sdat(d)
        if not r: L.append('%s: SDAT 를 못 읽음' % p); continue
        names, info, fat = r
        L.append('\n## %s (%d바이트, 파일 %d개)' % (p, len(d), len(fat)))
        for k in KINDS: L.append('  %-8s %d개' % (k, len(info[k])))
        L.append('\n-- 곡(SEQ): 번호 | 이름 | 파일 | 크기 | 뱅크 | 볼륨 | 플레이어')
        bank_use = collections.Counter()
        for i, e in enumerate(info['SEQ']):
            nm = names['SEQ'][i] if i < len(names['SEQ']) else ''
            if not e: L.append('%4d | %s | (빈 칸)' % (i, nm)); continue
            fid, _u, bank, vol, cpr, ppr, ply = struct.unpack_from('<HHHBBBB', e, 0)
            size = fat[fid][1] if fid < len(fat) else -1
            bank_use[bank] += 1
            L.append('%4d | %s | %d | %d | %d | %d | %d' % (i, nm, fid, size, bank, vol, ply))
        L.append('\n-- 악기 뱅크(BANK): 번호 | 이름 | 파일 | 크기 | 파형 묶음 4개 | 쓰는 곡 수')
        for i, e in enumerate(info['BANK']):
            nm = names['BANK'][i] if i < len(names['BANK']) else ''
            if not e: continue
            fid = u16(e, 0); wa = struct.unpack_from('<4H', e, 4)
            L.append('%4d | %s | %d | %d | %s | %d' % (i, nm, fid, fat[fid][1] if fid < len(fat) else -1, [x if x != 0xFFFF else '-' for x in wa], bank_use[i]))
        L.append('\n-- 파형 묶음(WAVEARC): 번호 | 이름 | 크기')
        for i, e in enumerate(info['WAVEARC']):
            if not e: continue
            fid = u16(e, 0)
            L.append('%4d | %s | %d' % (i, names['WAVEARC'][i] if i < len(names['WAVEARC']) else '', fat[fid][1] if fid < len(fat) else -1))
        L.append('\n-- 스트림(STRM, 녹음된 소리): 번호 | 이름 | 크기')
        for i, e in enumerate(info['STRM']):
            if not e: continue
            fid = u16(e, 0)
            L.append('%4d | %s | %d' % (i, names['STRM'][i] if i < len(names['STRM']) else '', fat[fid][1] if fid < len(fat) else -1))
        L.append('\n-- 곡 묶음(SEQARC, 효과음): %d개 — 이름 앞 20: %s' % (len(info['SEQARC']), names['SEQARC'][:20]))
    open('sdat_목록.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:20])); print('… 전체는 sdat_목록.txt — 설계자에게')

if __name__ == '__main__':
    main()
