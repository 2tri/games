#!/usr/bin/env python3
"""이벤트 종(스타팅·선물·알·고정 전투) 바꾸기 — 스크립트(a/0/1/2) 안 명령의 종 번호를 NDS_이벤트표.tsv 대로 (2026-10-14)
사용:   python hg_event.py "<앞 단계 롬.nds>" --base "<원본 롬>"            → 보고만(hg_ev_out/report.txt, 찾은 명령 전부)
        python hg_event.py "<앞 단계 롬.nds>" --base "<원본 롬>" --apply    → hg_ev_out/hg_ev_test.nds 까지
근거(10/14 웹 조사, 하트골드 스크립트 명령표): 명령 번호 u16 →
  0x0089 GiveStoredPokemon [종 u16][레벨 u16][도구 u16][? u16][? u16][? u16]   (선물·알)
  0x0029 SetVar [변수 u16][값 u16]  — 변수 0x8004~0x8007 에 종 번호를 넣고 0x00DE StoreStarter / 0x00C1 SetVariablePokemon 이 쓰는 꼴(스타팅)
  0x02BD WildBattle2 [종 u16][레벨 u16][? u16][? u16],  0x024D LegendaryBattle [종 u16][레벨 u16][? u16]   (고정 전투)
바꾸는 규칙: NDS_이벤트표.tsv 의 「번호」(하트골드 원래 종) → 「우리 종」 칸. 같은 원래 종이 여러 줄이면 첫 줄. 표에 없는 종 번호(1~493)는 바꾸지 않고 보고만.
안전장치: 명령 번호 바로 뒤에 오는 값이 1~493 이고 레벨 칸이 1~100 일 때만 명령으로 본다. 파일 크기는 안 바뀜(값만 덮음) — 빌 파일만 예외.
빌(10/14): 「종류=도구」 줄(이브이 133 → 행복의알)은 종 바꾸기가 아니라 스크립트를 고친다(근거 pret/pokeheartgold scr_seq_0892_T25R0401.s, 명령표 asm/macros/script.inc).
  원래: GetPartyCount 8005 / Compare 8005,6 / GoToIfEq(가득) / NPCMsg 1 / GiveMon 이브이 Lv5 / SetFlag 받음 / 받았다·팡파르·별명 짓기 / _00C6: NPCMsg 3 …
  고침: Compare 의 6 → 7(파티가 가득 차도 막지 않음), GiveMon 자리 → GoTo 새 토막(파일 끝에 붙임):
        SetVar 8004 도구 / SetVar 8005 1 / CallStd 2033(std_give_item_verbose: 받았다 글·팡파르·가방에 넣기) / SetFlag 받음 / GoTo _00C6
  명령 번호(10진): GiveMon 137, SetFlag 30, SetVar 41, CallStd 20, GoTo 22, GoToIf 28, Compare 17, GetPartyCount 332, NicknameInput 173, NPCMsg 45"""
import os, sys, csv, struct, argparse, collections, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hg1, hg2
from hg1 import NDS, NARC, bps_make, bps_apply, say, R

LUCKY_EGG = 231          # 4세대 도구 번호: 행복의알(Lucky Egg)

def kanto_lab_patch(d, MAP, level=35):
    """10/14 관동 스타팅을 2부 시작으로(근거 pret scr_seq_0740_T01R0301.s / _hdr.s, D41R0108.s).
    원래: VAR 4131 = 0 이면 연구소 볼 3개가 잠김, 레드를 이기면 1 + 볼 숨김 깃발 3개 풀림. 들어갈 때 도는 스크립트(010) 첫 명령 = Compare 4131,3.
    고침: 010 첫 명령 자리 → GoTo 새 토막 { Compare 4131,0 / GoToIf ne 건너뜀 / SetVar 4131,1 / ClearFlag ×3 / 건너뜀: Compare 4131,3(옮긴 것) / GoTo 010+6 }
          → 2부에 연구소에 들어가면 바로 풀림(4131=1 이면 장면 006 = 「셋 중 하나를 골라라」).
    + 볼 3개 종: SetVar 8004,1/4/7 → 우리 칸, 그림 보이기(452)·울음(PlayCry 76)의 종 번호, GiveMon VAR8004 레벨 5 → level.
    → (새 바이트 또는 None, 설명)"""
    hide = None
    for k in range(0, len(d) - 20):
        if d[k:k + 2] == b'\x1e\x00' and d[k + 4:k + 6] == b'\x1e\x00' and d[k + 8:k + 10] == b'\x1e\x00' and d[k + 12:k + 18] == bytes([0x29, 0, 0x31, 0x41, 6, 0]):
            hide = [struct.unpack_from('<H', d, k + 2 + 4 * j)[0] for j in range(3)]; break
    if not hide: return None, '볼 숨김 깃발(SetFlag×3 + SetVar 4131,6) 없음'
    st = d.find(bytes([17, 0, 0x31, 0x41, 3, 0, 28, 0, 1]))
    if st < 0 or d.find(bytes([17, 0, 0x31, 0x41, 4, 0]), st + 6, st + 20) < 0: return None, '들어갈 때 스크립트(Compare 4131,3 …) 없음'
    d = bytearray(d); notes = []
    # 종·그림·울음·레벨
    for old, new in sorted(MAP.items()):
        if old not in (1, 4, 7) or not new: continue
        for pat, off in ((struct.pack('<HHH', 41, 0x8004, old), 4), (struct.pack('<HH', 452, old), 2), (struct.pack('<HH', 76, old), 2)):
            q = 0; n = 0
            while True:
                q = d.find(pat, q)
                if q < 0: break
                struct.pack_into('<H', d, q + off, new); n += 1
                q += 1
            notes.append('%d→%d(%s %d곳)' % (old, new, {4: 'SetVar', 2: '그림/울음'}[off] if off == 4 else ('그림' if pat[:2] == struct.pack('<H', 452) else '울음'), n))
    g = d.find(bytes([0x89, 0, 0x04, 0x80, 5, 0]))
    if g >= 0: d[g + 4] = level; notes.append('레벨 5→%d' % level)
    else: notes.append('GiveMon VAR8004 Lv5 못 찾음(레벨 그대로)')
    # 들어갈 때 스크립트 앞에 풀기 토막
    while len(d) % 4: d += b'\0'
    blk = len(d)
    d += struct.pack('<HHH', 17, 0x4131, 0)
    jpos = len(d); d += struct.pack('<HB', 28, 5) + b'\0\0\0\0'
    d += struct.pack('<HHH', 41, 0x4131, 1) + b''.join(struct.pack('<HH', 31, f) for f in hide)
    skip = len(d); struct.pack_into('<i', d, jpos + 3, skip - (jpos + 3) - 4)
    d += bytes([17, 0, 0x31, 0x41, 3, 0])
    d += struct.pack('<H', 22) + struct.pack('<i', (st + 6) - (len(d) + 2) - 4)
    while len(d) % 4: d += b'\0'
    d[st:st + 6] = struct.pack('<H', 22) + struct.pack('<i', blk - (st + 2) - 4)
    return bytes(d), '들어갈 때 스크립트 @%05X → 풀기 토막 @%05X(깃발 %s), %s' % (st, blk, hide, ', '.join(notes))

def bill_patch(d, item=LUCKY_EGG):
    """→ (새 바이트 또는 None, 설명). 이브이(133) GiveMon 을 도구 주기로."""
    o = -1; p0 = 0
    while True:                                                            # 이브이(133), 레벨 1~100 (디지골드가 레벨을 바꿨을 수 있음)
        p0 = d.find(bytes([0x89, 0x00, 0x85, 0x00]), p0)
        if p0 < 0: break
        if 1 <= struct.unpack_from('<H', d, p0 + 4)[0] <= 100: o = p0; break
        p0 += 1
    if o < 0: return None, 'GiveMon 이브이 없음'
    if struct.unpack_from('<H', d, o + 14)[0] != 30: return None, 'GiveMon 뒤가 SetFlag 가 아님 — 원본과 다름'
    flag = struct.unpack_from('<H', d, o + 16)[0]
    # _00C6 = 별명 메뉴의 GoToIfGe(조건 4) 목적지
    tgt = None; p = o + 18
    while p < min(len(d) - 7, o + 200):
        if d[p] == 28 and d[p + 1] == 0 and d[p + 2] == 4:
            tgt = p + 3 + 4 + struct.unpack_from('<i', d, p + 3)[0]; break
        p += 1
    if tgt is None or not (0 <= tgt < len(d) - 2) or struct.unpack_from('<H', d, tgt)[0] != 45:
        return None, '별명 뒤 대사 자리(_00C6)를 못 찾음'
    d = bytearray(d)
    # 파티 가득 검사 끄기: GiveMon 앞 40바이트 안 Compare(17) 8005,6
    q = d.rfind(bytes([17, 0, 0x05, 0x80, 6, 0]), max(0, o - 40), o)
    full = '파티 가득 검사 끔' if q >= 0 else '파티 가득 검사 못 찾음(그대로)'
    if q >= 0: d[q + 4] = 7
    while len(d) % 4: d += b'\0'
    blk = len(d)
    d += struct.pack('<HHH', 41, 0x8004, item) + struct.pack('<HHH', 41, 0x8005, 1) + struct.pack('<HH', 20, 2033) + struct.pack('<HH', 30, flag)
    d += struct.pack('<H', 22) + struct.pack('<i', tgt - (len(d) + 2) - 4)
    while len(d) % 4: d += b'\0'
    d[o:o + 14] = struct.pack('<H', 22) + struct.pack('<i', blk - (o + 2) - 4) + b'\0' * 8
    return bytes(d), 'GiveMon @%05X → 도구 %d 주기(새 토막 @%05X, 받음 깃발 %d, 돌아갈 곳 @%05X), %s' % (o, item, blk, flag, tgt, full)

def find_itemdata(rom):
    """도구 자료 NARC 찾기: 멤버 500개 넘고 크기가 같고(30~40바이트), 값(첫 u16)이 몬스터볼 200·상처약 300·해독제 100 인 것 → (경로, NARC) 또는 (None, None)"""
    for p in sorted(rom.paths):
        if not p.startswith('a/'): continue
        try:
            n = NARC(rom.get(p)); fs = n.files
        except Exception: continue
        if len(fs) < 500 or not (30 <= len(fs[17]) <= 40) or len({len(f) for f in fs[1:500]}) != 1: continue
        pr = lambda i: struct.unpack_from('<H', fs[i], 0)[0]
        if pr(4) == 200 and pr(17) == 300 and pr(18) == 100: return p, n
    return None, None

CMDS = {0x0089: ('GiveStoredPokemon', 0, 1), 0x02BD: ('WildBattle2', 0, 1), 0x024D: ('LegendaryBattle', 0, 1)}   # (이름, 종 칸, 레벨 칸) — 칸 = 명령 뒤 u16 순서

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--base', required=True); ap.add_argument('--out', default='hg_ev_out'); ap.add_argument('--apply', action='store_true')
    ap.add_argument('--draft', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_종_초안.tsv'))
    ap.add_argument('--events', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_이벤트표.tsv'))
    A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
    raw = open(A.rom, 'rb').read(); rom = NDS(raw)
    say('== 이벤트 종(스크립트) — 롬 %s%s' % (rom.code, '' if A.apply else ' (보고만, --apply 없음)'))
    draft = list(csv.DictReader(open(A.draft, encoding='utf-8'), delimiter='\t'))
    slot = {r['이름']: int(r['NDS 칸']) for r in draft if r['NDS 칸'].isdigit()}
    import re
    for r in draft:
        mm = re.search(r'디지골드 칸: (\S+)', r['메모'])
        if r['출처'] == '디지골드' and mm and mm.group(1) in hg2.REPLACED_DEX: slot[r['이름']] = hg2.REPLACED_DEX[mm.group(1)]
    ev = list(csv.DictReader(open(A.events, encoding='utf-8'), delimiter='\t'))
    MAP = {}; names = {}
    for r in ev:
        if r['번호'].strip().isdigit() and r['우리 종'].strip() in slot and int(r['번호']) not in MAP:
            MAP[int(r['번호'])] = slot[r['우리 종'].strip()]; names[int(r['번호'])] = (r['하트골드 원래'], r['우리 종'].strip(), r['종류'])
    LVMAP = {int(r['번호']): int(r['Lv']) for r in ev if r['종류'].strip() == '선물' and r['번호'].strip().isdigit() and (r.get('Lv') or '').strip().isdigit()}   # 10/15 평론: 선물 레벨을 받을 때 파티 레벨에 맞춤
    BLV = {int(r['번호']): int(r['Lv']) for r in ev if r['종류'].strip() in ('고정', '심볼') and r['번호'].strip().isdigit() and (r.get('Lv') or '').strip().isdigit() and r['우리 종'].strip() in slot}   # 10/15: 고정·심볼 전투 레벨도 표대로(뮤츠 Lv70 → 아포카리몬 Lv80)
    say('이벤트표: 원래 종 번호 %d개 → 우리 칸 (%s)' % (len(MAP), ', '.join('%d %s→%s' % (k, v[0][:6], v[1]) for k, v in list(names.items())[:12])))
    nar = NARC(rom.get(hg1.NARC_PATHS['script'])); files = list(nar.files); sizes0 = [len(f) for f in files]
    found = []; changed = 0
    for fi, f in enumerate(files):
        d = bytearray(f); n = len(d)
        for o in range(0, n - 5):          # 10/14: 명령은 홀수 자리에서도 시작함(GoToIf 7바이트) — 전에는 짝수만 봐서 놓칠 수 있었음
            cmd = d[o] | (d[o + 1] << 8)
            if cmd in CMDS:
                nm, si, li = CMDS[cmd]
                if o + 2 + 2 * (max(si, li) + 1) > n: continue
                sp = struct.unpack_from('<H', d, o + 2 + 2 * si)[0]; lv = struct.unpack_from('<H', d, o + 2 + 2 * li)[0]
                if not (1 <= sp <= 493 and 1 <= lv <= 100): continue
                new = MAP.get(sp)
                found.append((fi, o, nm, sp, lv, new))
                if A.apply and new: struct.pack_into('<H', d, o + 2 + 2 * si, new); changed += 1
                if A.apply and new and nm == 'GiveStoredPokemon' and sp in LVMAP: struct.pack_into('<H', d, o + 2 + 2 * li, LVMAP[sp])
                if A.apply and new and nm != 'GiveStoredPokemon' and sp in BLV: struct.pack_into('<H', d, o + 2 + 2 * li, BLV[sp])
            elif cmd == 0x0029:
                var = struct.unpack_from('<H', d, o + 2)[0]; val = struct.unpack_from('<H', d, o + 4)[0]
                if 0x8004 <= var <= 0x800C and 1 <= val <= 493:
                    nxt = [struct.unpack_from('<H', d, o + 6 + 2 * k)[0] for k in range(0, 6) if o + 8 + 2 * k <= n]
                    tag = 'SetVar(스타팅)' if any(x in (0x00DE, 0x00C1, 0x00CD) for x in nxt) else 'SetVar'
                    new = MAP.get(val)
                    found.append((fi, o, tag + ' 0x%04X' % var, val, 0, new))
                    # 10/15: SetVar 추정은 바꾸지 않음(보고만) — 스타팅은 hg4_icons 의 코드 표(152·155·158)로 바꿈. 어제 2곳을 바꾼 것이 다른 스크립트였을 위험
        files[fi] = bytes(d)
    by = collections.Counter(x[2].split()[0] for x in found)
    say('찾은 명령 %d개: %s' % (len(found), dict(by)))
    say('-- 파일 | 오프셋 | 명령 | 종(원래 번호) | 레벨 | → 우리 칸(표에 있을 때)')
    for fi, o, nm, sp, lv, new in [x for x in found if not x[2].startswith('SetVar ')][:200] + [x for x in found if x[2].startswith('SetVar ')][:100]:      # 10/15: 선물·스타팅 줄 먼저(SetVar 잡담은 뒤 100줄만)
        say('  %4d @%05X %-22s %3d%s Lv%-3d %s' % (fi, o, nm, sp, ('(' + names[sp][0][:8] + ')') if sp in names else '', lv, ('→ %d %s' % (new, names[sp][1])) if new else ''))
    hit = {sp for _, _, _, sp, _, new in found if new}
    miss = [k for k in MAP if k not in hit]
    if miss: say('이벤트표에 있지만 스크립트에서 못 찾은 원래 종 %d: %s' % (len(miss), ', '.join('%d %s(%s)' % (k, names[k][0][:8], names[k][2]) for k in miss)))
    lab_fi = None
    if A.apply or True:
        lv = next((int(r['Lv']) for r in ev if r['번호'].strip() in ('1', '4', '7') and r['Lv'].strip().isdigit()), 35)
        for fi, f in enumerate(files):
            if f.find(bytes([0x29, 0, 0x31, 0x41, 6, 0])) < 0 or f.find(bytes([17, 0, 0x31, 0x41, 3, 0, 28, 0, 1])) < 0: continue
            nd, why = kanto_lab_patch(f, MAP, lv)
            say('관동 스타팅(연구소, 2부 시작에 풀림): 파일 %d — %s' % (fi, why))
            if nd and A.apply: files[fi] = nd; lab_fi = fi
            break
        else: say('관동 스타팅: 연구소 스크립트를 못 찾음(Compare 4131 …)')
    # 10/15 선물 도구: 관장이 주는 기술머신(SetVar 8004 TM번호 / SetVar 8005 개수 / HasSpaceForItem … CallStd 2033 — pret T22GYM0101.s)을 NDS_선물도구.tsv 대로 바꿈
    gp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NDS_선물도구.tsv')
    if os.path.exists(gp):
        rows_g = [r for r in csv.DictReader((l for l in open(gp, encoding='utf-8') if not l.startswith('#')), delimiter='	')]
        for r in rows_g:
            try: old_i, new_i, qty = int(r['원래 도구 번호']), int(r['새 도구 번호']), int(r['수량'] or 1)
            except ValueError: continue
            pat = struct.pack('<HHH', 41, 0x8004, old_i) + struct.pack('<HH', 41, 0x8005); hits_g = []
            for fi, f in enumerate(files):
                q = 0
                while True:
                    q = f.find(pat, q)
                    if q < 0: break
                    nxt = f[q + 12:q + 60]
                    if struct.pack('<H', 127) in nxt or struct.pack('<HH', 20, 2033) in nxt or struct.pack('<HH', 20, 2008) in nxt: hits_g.append((fi, q))
                    q += 2
            for fi, q in hits_g:
                if A.apply:
                    d_ = bytearray(files[fi]); struct.pack_into('<H', d_, q + 4, new_i); struct.pack_into('<H', d_, q + 10, qty); files[fi] = bytes(d_)
            say('선물 도구 %s: 도구 %d → %d ×%d — %s' % (r['키'], old_i, new_i, qty, ('파일 ' + ', '.join('%d@%05X' % h for h in hits_g)) if hits_g else '스크립트에서 못 찾음'))
            if len(hits_g) > 1: say('  (같은 기술머신을 주는 곳이 %d곳 — 관장이 아닌 곳이면 확인)' % len(hits_g))
    bill_fi = None
    if any(r['종류'].strip() == '도구' and r['번호'].strip() == '133' for r in ev):
        for fi, f in enumerate(files):
            nd, why = bill_patch(f)
            if nd or why != 'GiveMon 이브이 없음':
                say('빌(이브이 → 행복의알): 파일 %d — %s' % (fi, why))
                if nd and A.apply: files[fi] = nd; bill_fi = fi
                if nd: break
        else: say('빌: 이브이 주는 스크립트를 못 찾음')
    if not A.apply:
        open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n'); return
    if [len(f) for i, f in enumerate(files) if i not in (bill_fi, lab_fi)] != [x for i, x in enumerate(sizes0) if i not in (bill_fi, lab_fi)]: raise SystemExit('실패: 스크립트 파일 크기가 바뀜 — 쓰지 않음')
    nar.files = files; out = NDS(raw); out.put(hg1.NARC_PATHS['script'], nar.build())
    # 10/14 문장 값: 상점에서 파는 문장(심해의이빨 226)을 3000원으로(진화의 돌 2100보다 조금 비싸게). 궁극의 문장(227)은 안 팔지만 같이 맞춤
    ip, inar = find_itemdata(out)
    if inar is None: say('도구 자료(값)를 못 찾음 — 문장 값은 그대로')
    else:
        ifs = list(inar.files); chg = []
        for it, price in ((226, 3000), (227, 5000)):
            if it < len(ifs) and len(ifs[it]) >= 2:
                old = struct.unpack_from('<H', ifs[it], 0)[0]; d_ = bytearray(ifs[it]); struct.pack_into('<H', d_, 0, price); ifs[it] = bytes(d_); chg.append('%d: %d → %d원' % (it, old, price))
        inar.files = ifs; out.put(ip, inar.build()); say('도구 값(%s): %s' % (ip, ', '.join(chg)))
    new_raw = bytes(out.d)
    chk = NARC(NDS(new_raw).get(hg1.NARC_PATHS['script'])).files
    bad = sum(1 for fi, f in enumerate(files) if chk[fi] != f)
    say('종 번호 바꿈 %d곳, 검산 실패 %d' % (changed, bad))
    open(os.path.join(A.out, 'hg_ev_test.nds'), 'wb').write(new_raw)
    braw = open(A.base, 'rb').read(); patch = bps_make(braw, new_raw); open(os.path.join(A.out, 'hg_ev.bps'), 'wb').write(patch)
    say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if bps_apply(braw, patch) == new_raw else '실패'))
    open(os.path.join(A.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(R) + '\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        traceback.print_exc(); print('실패: 위 오류 전체를 그대로 보고'); sys.exit(1)
