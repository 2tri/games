#!/usr/bin/env python3
"""롬 검사기 (2026-10-15) — 멈춤·튕김을 일으킬 깨진 자료를 롬을 켜기 전에 잡는다. 롬은 읽기만.
사용:   python rom_check.py "<만든 롬.nds>" --base "<원본 롬.nds>"        → 롬검사.txt, 끝줄 「검사 통과」 또는 「검사 실패 n건」(실패면 종료 코드 1)
        python rom_check.py "<롬>" --base "<원본>" --quiet                    → 실패만 출력
보는 것 (원본과 비교해 「달라진 곳」 위주)
 1) 머리말 CRC · 파일 위치표(FAT): 파일끼리 겹침, 롬 밖, arm9·오버레이 자리
 2) NARC 멤버 수가 원본과 같은지(바뀌면 게임이 엉뚱한 번호를 읽음)
 3) 종 자료·기술 배우기·진화·트레이너 파티·야생: 번호가 범위 안인지(종 1~493, 기술 1~467, 도구 0~536, 레벨 1~100)
 4) 스크립트: 파일 머리 표(u32 상대 위치 … 0xFD13)가 파일 안을 가리키는지, 원본보다 짧아지지 않았는지
 5) 글 묶음: 모든 글 파일이 풀리는지, 글 수가 원본과 같은지
 6) 소리(SDAT): 곡 정보가 가리키는 파일·뱅크가 있는지, 바뀐 곡이 SSEQ 검사(hg_song.check_sseq)를 통과하는지
 7) 포켓몬 흔적(10/15 사용자 「배틀에 강철톤 같은 게 없어야」): hg2_out/칸표.tsv 가 있으면
    - 야생(라디오·대량 발생 칸 포함)·트레이너 파티에 나오는 종이 전부 우리 종 칸인지
    - 새 그림이 들어가야 하는 칸의 전투 앞모습이 원본과 달라졌는지(같으면 원래 포켓몬 그림이 남은 것)
 이 검사를 통과해도 게임 진행 확인(에뮬레이터)은 따로 해야 한다 — 여기서는 「자료가 깨졌는지」만 본다."""
import os, sys, struct, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1
from hg1 import NDS, NARC

P = hg1.NARC_PATHS
FAIL = []; NOTE = []; TRACE = []
def trace(*a): TRACE.append(' '.join(str(x) for x in a))
def fail(*a): FAIL.append(' '.join(str(x) for x in a))
def note(*a): NOTE.append(' '.join(str(x) for x in a))

def narc(rom, path):
    try: return NARC(rom.get(path)).files
    except Exception as ex: fail('NARC 못 읽음', path, ex); return None

def check_fs(rom):
    d = rom.d
    if struct.unpack_from('<H', d, 0x15E)[0] != hg1.crc16(bytes(d[0:0x15E])): fail('머리말 CRC 틀림')
    spans = []
    for name, oo, so in (('arm9', 0x20, 0x2C), ('arm7', 0x30, 0x3C)):
        o, s = struct.unpack_from('<I', d, oo)[0], struct.unpack_from('<I', d, so)[0]; spans.append((o, o + s, name))
    for name, oo, so in (('FNT', 0x40, 0x44), ('FAT', 0x48, 0x4C), ('arm9 오버레이표', 0x50, 0x54), ('arm7 오버레이표', 0x58, 0x5C)):
        o, s = struct.unpack_from('<II', d, oo); spans.append((o, o + s, name))
    for i in range(rom.nfiles):
        s, e = rom.fat(i)
        if e < s: fail('FAT 파일 %d 끝이 시작보다 앞' % i); continue
        if e > len(d): fail('FAT 파일 %d 가 롬 밖(%d > %d)' % (i, e, len(d)))
        if e > s: spans.append((s, e, 'file%d' % i))
    spans.sort()
    for (a0, a1, an), (b0, b1, bn) in zip(spans, spans[1:]):
        if b0 < a1: fail('겹침: %s(%X~%X) 와 %s(%X~%X)' % (an, a0, a1, bn, b0, b1))
    y9o, y9s = struct.unpack_from('<II', d, 0x50)
    for k in range(y9s // 32):
        e = struct.unpack_from('<8I', d, y9o + 32 * k)
        if e[6] >= rom.nfiles: fail('오버레이 %d 의 파일 번호 %d 가 FAT 밖' % (e[0], e[6]))
    note('파일 %d개, 롬 %d바이트' % (rom.nfiles, len(d)))

def check_counts(rom, base):
    bad = 0
    for p in sorted(rom.paths):
        if not p.startswith('a/'): continue
        try: a = NARC(rom.get(p)).files
        except Exception: continue
        try: b = NARC(base.get(p)).files
        except Exception: continue
        if len(a) != len(b): fail('NARC 멤버 수가 바뀜: %s %d → %d' % (p, len(b), len(a))); bad += 1
    note('NARC 멤버 수 비교: 다른 곳 %d' % bad)

def check_data(rom, base):
    pers = narc(rom, P['personal']); learn = narc(rom, P['learn']); evo = narc(rom, P['evo'])
    trd = narc(rom, P['trdata']); trp = narc(rom, P['trpoke']); enc = narc(rom, P['enc'])
    if pers:
        for i, f in enumerate(pers[:494]):
            if len(f) < 28: continue
            if f[6] > 17 or f[7] > 17: fail('종 %d 타입 번호 범위 밖 %d/%d' % (i, f[6], f[7]))
    if learn:
        for i, f in enumerate(learn[:494]):
            if b'\xff\xff' not in f[:len(f) - len(f) % 2] and len(f) > 1: fail('종 %d 기술 배우기 끝 표시(FFFF) 없음' % i)
            for lv, mv in hg1.learnset(f):
                if not (1 <= lv <= 100) or not (1 <= mv <= 467): fail('종 %d 기술 배우기 Lv%d 기술 %d 범위 밖' % (i, lv, mv)); break
    if evo:
        for i, f in enumerate(evo[:494]):
            for m, prm, t in hg1.evos(f):
                if not (1 <= m <= 26): fail('종 %d 진화 방법 %d 범위 밖' % (i, m))
                if not (1 <= t <= 493): fail('종 %d 진화 대상 %d 범위 밖' % (i, t))
                if m in (6, 7, 17, 18, 19) and not (1 <= prm <= 536): fail('종 %d 진화 도구 %d 범위 밖' % (i, prm))
    if trd and trp:
        nb = 0
        for i, d_ in enumerate(trd):
            t = hg1.trdata(d_)
            if not t or i >= len(trp): continue
            pt, _ = hg1.trpoke(trp[i], t['flags'], t['n'])
            if t['n'] and pt is None: fail('트레이너 %d 파티를 못 읽음(크기 %d, 마리 %d, 깃발 %d)' % (i, len(trp[i]), t['n'], t['flags'])); nb += 1; continue
            for m in pt or []:
                if not (1 <= m['sp'] <= 493) or not (1 <= m['lv'] <= 100): fail('트레이너 %d 종 %d Lv%d 범위 밖' % (i, m['sp'], m['lv'])); nb += 1; break
                if m['item'] is not None and m['item'] > 536: fail('트레이너 %d 도구 %d 범위 밖' % (i, m['item']))
                if m['moves'] and any(x > 467 for x in m['moves']): fail('트레이너 %d 기술 %s 범위 밖' % (i, m['moves']))
        note('트레이너 %d명 검사' % len(trd))
    if enc:
        for i, f in enumerate(enc):
            if len(f) != 0xC4: continue
            for off in getattr(__import__('hg3'), 'ENC_SPECIES', []):
                x = struct.unpack_from('<H', f, off)[0]
                if x > 493: fail('야생 파일 %d 칸 @%X 종 %d 범위 밖' % (i, off, x)); break
            if any(not (0 <= v <= 100) for v in f[8:20]): fail('야생 파일 %d 걷기 레벨 범위 밖 %s' % (i, list(f[8:20])))

def check_scripts(rom, base):
    a = narc(rom, P['script']); b = narc(base, P['script']) if base else None
    if not a: return
    changed = [i for i in range(len(a)) if b is None or i >= len(b) or a[i] != b[i]]
    for i in changed:
        f = a[i]; k = 0
        while k + 4 <= len(f):
            if struct.unpack_from('<H', f, k)[0] == 0xFD13: break
            off = struct.unpack_from('<I', f, k)[0]
            if k + 4 + off >= len(f): fail('스크립트 파일 %d 머리 표 %d번이 파일 밖을 가리킴' % (i, k // 4))
            k += 4
            if k > 400: fail('스크립트 파일 %d 머리 표 끝(FD13)을 못 찾음' % i); break
        if b and i < len(b) and len(f) < len(b[i]): fail('스크립트 파일 %d 이 원본보다 짧아짐(%d → %d)' % (i, len(b[i]), len(f)))
    note('스크립트 바뀐 파일 %d개 검사: %s' % (len(changed), changed[:20]))

def check_msgs(rom, base):
    a = narc(rom, P['msg']); b = narc(base, P['msg']) if base else None
    if not a: return
    nb = 0
    for i, f in enumerate(a):
        if b and i < len(b) and f == b[i]: continue
        try: _, ent = hg1.msg_decode(f)
        except Exception as ex: fail('글 파일 %d 못 풂: %s' % (i, ex)); nb += 1; continue
        if b and i < len(b):
            try:
                _, e0 = hg1.msg_decode(b[i])
                if len(e0) != len(ent): fail('글 파일 %d 글 수가 바뀜 %d → %d' % (i, len(e0), len(ent)))
            except Exception: pass
        for j, e in enumerate(ent):
            if e and e[-1] != 0xFFFF: fail('글 파일 %d #%d 끝 표시(FFFF) 없음' % (i, j)); break
    note('글 파일 검사(바뀐 것만)')

def check_sound(rom, base):
    try:
        import sdat_scan, hg_song
    except Exception as ex: note('소리 검사 건너뜀', ex); return
    sp = next((p for p in rom.paths if p.endswith('gs_sound_data.sdat')), None)
    if not sp: note('SDAT 없음'); return
    d = rom.get(sp); r = sdat_scan.parse_sdat(d)
    if not r: fail('SDAT 못 읽음'); return
    names, info, fat = r
    b = None
    if base and sp in base.paths:
        bd = base.get(sp); rb = sdat_scan.parse_sdat(bd)
        if rb: b = (bd, rb)
    nch = 0
    for i, e in enumerate(info['SEQ']):
        if not e: continue
        fid, _u, bank = struct.unpack_from('<HHH', e, 0)
        if fid >= len(fat): fail('곡 %d %s 파일 번호 %d 가 FAT 밖' % (i, names['SEQ'][i] if i < len(names['SEQ']) else '', fid)); continue
        if bank >= len(info['BANK']) or not info['BANK'][bank]: fail('곡 %d 뱅크 %d 없음' % (i, bank)); continue
        f = d[fat[fid][0]:fat[fid][0] + fat[fid][1]]
        if b:
            bd, (bn, bi, bf) = b
            if fid < len(bf) and bd[bf[fid][0]:bf[fid][0] + bf[fid][1]] == f: continue
        nch += 1
        bad = hg_song.check_sseq(f, hg_song.bank_types(d, info, fat, bank))
        if bad: fail('곡 %d %s: %s' % (i, names['SEQ'][i] if i < len(names['SEQ']) else '', '; '.join(bad[:3])))
    note('바뀐 곡 %d개 SSEQ 검사' % nch)

def load_slots(path):
    if not path or not os.path.exists(path): return None
    rows = [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8') if l.strip()][1:]
    return {r[0]: (int(r[1]), r[2], r[3] == '예') for r in rows if len(r) >= 4 and r[1].isdigit()}

def check_traces(rom, base, slots):
    if not slots: note('포켓몬 흔적 검사 건너뜀(칸표.tsv 없음 — hg2 를 먼저 돌린 폴더에서 실행)'); return
    ours = {v[0] for v in slots.values()}; name_of = {v[0]: k for k, v in slots.items()}
    enc = narc(rom, P['enc']); trd = narc(rom, P['trdata']); trp = narc(rom, P['trpoke'])
    import hg3
    enc0 = narc(base, P['enc']) if base else None
    if enc0 is not None and enc == enc0: note('포켓몬 흔적: 야생 표가 원본 그대로(hg3 전 단계) — 흔적 검사는 hg3 뒤부터'); return
    leftover = collections.Counter(); where = collections.defaultdict(list)
    for i, f in enumerate(enc or []):
        if len(f) != 0xC4: continue
        for off in hg3.ENC_SPECIES:
            x = struct.unpack_from('<H', f, off)[0]
            if x and x not in ours: leftover[x] += 1; where[x].append('야생%d@%X' % (i, off))
    for i, d_ in enumerate(trd or []):
        t = hg1.trdata(d_)
        if not t or i >= len(trp): continue
        pt, _ = hg1.trpoke(trp[i], t['flags'], t['n'])
        for m in pt or []:
            if m['sp'] not in ours: leftover[m['sp']] += 1; where[m['sp']].append('트레이너%d' % i)
    # 10/15 야생 표 밖(박치기·사파리·벌레잡기·교환) — hg3 를 거친 롬에서만
    def xf(path):
        try: return narc(rom, path)
        except Exception: return None
    hb = xf('a/2/5/2') if 'a/2/5/2' in rom.paths else None
    for i, d in enumerate(hb or []):
        for bs in (0x04, 0x1C, 0x34):                   # (base 는 원본 롬 변수라 다른 이름)
            for k in range(6):
                o = bs + 4 * k
                if o + 2 > len(d): break
                x = struct.unpack_from('<H', d, o)[0]
                if x and x not in ours: leftover[x] += 1; where[x].append('박치기%d@%X' % (i, o))
    sf = xf('a/2/3/0') if 'a/2/3/0' in rom.paths else None
    for i, d in enumerate(sf or []):
        if len(d) < 8: continue
        nb = list(d[:5]); o = 8
        for t in range(5):
            for _ in range(30 + 3 * nb[t]):
                if o + 4 > len(d): break
                x = struct.unpack_from('<H', d, o)[0]
                if x and x not in ours: leftover[x] += 1; where[x].append('사파리%d@%X' % (i, o))
                o += 4
            o += 4 * nb[t]
    mp = next((q for q in rom.paths if q.endswith('mushi_encount.bin')), None)
    if mp:
        d = rom.get(mp)
        for o in range(0, len(d) - 7, 8):
            x = struct.unpack_from('<H', d, o)[0]
            if x and x not in ours: leftover[x] += 1; where[x].append('벌레잡기@%X' % o)
    tr_ = xf('a/1/1/2') if 'a/1/1/2' in rom.paths else None
    for i, d in enumerate(tr_ or []):
        for o in (0x00, 0x4C):
            if o + 4 > len(d): break
            x = struct.unpack_from('<I', d, o)[0]
            if 1 <= x <= 493 and x not in ours: leftover[x] += 1; where[x].append('교환%d@%X' % (i, o))
    # 10/15: 스크립트의 고정 전투·선물(GiveMon·LegendaryBattle·WildBattle2) — hg_event 를 거친 롬(스크립트가 원본과 다름)에서만
    sc = narc(rom, P['script']); sc0 = narc(base, P['script']) if base else None
    if sc and sc0 is not None and sc != sc0:
        import hg_event
        exc = set()
        ep = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_흔적_예외.tsv')
        if os.path.exists(ep):
            for l in open(ep, encoding='utf-8').read().split(chr(10))[1:]:
                r = l.split(chr(9))
                if len(r) >= 2 and r[0].strip().isdigit(): exc.add((int(r[0]), int(r[1], 16)))
        for fi, f in enumerate(sc):
            for o in range(0, len(f) - 5):
                cmd = f[o] | (f[o + 1] << 8)
                if cmd not in hg_event.CMDS: continue
                nm, si, li = hg_event.CMDS[cmd]
                if o + 2 + 2 * (max(si, li) + 1) > len(f): continue
                x = struct.unpack_from('<H', f, o + 2 + 2 * si)[0]; lv = struct.unpack_from('<H', f, o + 2 + 2 * li)[0]
                if 1 <= x <= 493 and 1 <= lv <= 100 and x not in ours and (fi, o) not in exc:
                    leftover[x] += 1; where[x].append('스크립트%d@%X %s Lv%d' % (fi, o, nm, lv))
    for x, n in leftover.most_common():
        trace('포켓몬 흔적: 우리 종이 아닌 칸 %d 가 %d곳에 나옴 (%s) — 스크립트 줄이 가짜(명령이 아닌 자료)면 NDS_흔적_예외.tsv 에 「파일·오프셋(16진)·이유」로 적음' % (x, n, ', '.join(where[x][:6])))
    note('포켓몬 흔적(야생·트레이너): 우리 종 아닌 칸 %d종' % len(leftover))
    g = narc(rom, P['pokegra']); g0 = narc(base, P['pokegra']) if base else None
    if g and g0:
        changed_any = any(g[i] != g0[i] for i in range(min(len(g), len(g0))))
        if not changed_any: note('전투 그림이 원본 그대로(hg4 전 단계) — 그림 검사는 hg4 뒤부터'); return
        same = []
        for nm, (s_, src, need) in sorted(slots.items(), key=lambda kv: kv[1][0]):
            if not need or (s_ + 1) * 6 > min(len(g), len(g0)): continue
            if all(g[s_ * 6 + k] == g0[s_ * 6 + k] for k in (2, 3, 4)): same.append('%s(칸 %d)' % (nm, s_))
        for x in same: trace('전투 그림 안 바뀜(원래 포켓몬 그림이 남음): ' + x)
        note('전투 그림 새로 들어가야 하는 칸 %d, 안 바뀐 칸 %d' % (sum(1 for v in slots.values() if v[2]), len(same)))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--base'); ap.add_argument('--quiet', action='store_true'); ap.add_argument('--out', default='롬검사.txt'); ap.add_argument('--slots', default='hg2_out/칸표.tsv')
    A = ap.parse_args()
    rom = NDS(open(A.rom, 'rb').read()); base = NDS(open(A.base, 'rb').read()) if A.base else None
    for fn in (check_fs, ):
        fn(rom)
    if base: check_counts(rom, base)
    for fn in (check_data, check_scripts, check_msgs, check_sound):
        try: fn(rom, base)
        except Exception as ex: fail('%s 중 오류: %s' % (fn.__name__, ex))
    try: check_traces(rom, base, load_slots(A.slots))
    except Exception as ex: fail('check_traces 중 오류: %s' % ex)
    L = ['== 롬 검사 — %s' % A.rom] + ['  ' + x for x in NOTE] + ['', '-- 실패 %d건' % len(FAIL)] + ['  ' + x for x in FAIL[:300]]
    L += ['', '-- 완성 조건 실패(포켓몬 흔적) %d건 — 롬은 켜도 되지만 완성 전에 고칠 것, 줄 그대로 보고' % len(TRACE)] + ['  ' + x for x in TRACE[:300]]
    L.append(('검사 통과' if not FAIL else '검사 실패 %d건 — 이 롬은 폰에 넣지 말고 실패 줄을 보고' % len(FAIL)) + ('' if not TRACE else ' / 완성 조건 실패 %d건(흔적)' % len(TRACE)))
    open(A.out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L if not A.quiet else [x for x in L if x.startswith('  ') and (x[2:] in FAIL or x[2:] in TRACE)][:30] + L[-1:]))
    sys.exit(1 if FAIL else 0)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
