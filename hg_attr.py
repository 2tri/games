#!/usr/bin/env python3
"""디지몬 속성 상성(백신 > 바이러스 > 데이터 > 백신)을 전투 피해에 넣는다. (Claude 작성, 2026-10-18)
사용:   python hg_attr.py <in.nds> <out.nds> --base "<원본 롬>"            → 속성표 + 코드 훅을 넣고 스스로 검산
        python hg_attr.py <in.nds> <out.nds> --base "<원본 롬>" --adv 1.2 --dis 0.8   (배율 바꾸기, 0.01 단위)
        python hg_attr.py <in.nds> <out.nds> --set 파닥몬=백신 --set 기자몬=바이러스  (시험용으로 몇 종만 덮어쓰기)
        python hg_attr.py <롬> --check                                     → 롬에 들어 있는 속성표·배율·훅만 읽어 보여 줌(쓰지 않음)
무엇을 하나
  - 피해 계산 중 「자속 보정 + 타입 상성」을 곱하는 함수(pret ov12_02251D28, 한국판 0x0225272C)가 피해를 돌려주기 직전
    (0x02252A3A `ldr r0,[sp,#0x50]; add sp,#0x30`)을 BL 로 바꿔, 공격·방어 디지몬의 속성을 보고 피해에 배율을 곱한다.
      유리(백신→바이러스, 바이러스→데이터, 데이터→백신) ×ADV, 불리(그 반대) ×DIS, 같은 속성·프리·언노운·기타 ×1.
      고정 피해 기술(battleStatus 1<<11·1<<15), 일격필살(moveStatusFlag 1<<5), 피해 0, 발버둥은 건드리지 않음.
      나눗셈은 게임의 DamageDivide(0x02253B7C, 0 이 되면 ±1)를 그대로 씀 → 원래 타입 상성과 같은 반올림.
  - 코드와 표를 넣을 자리: 오버레이 12 안에 남아 있는 원래 타입 상성표(0x0226D680~0x0226D7CF, 336바이트).
      디지몬골드 v1.6 의 페어리 타입 패치가 상성표를 오버레이 18 끝(0x021FC4A0)으로 옮겨서, 이 자리를 가리키는 곳이 없다
      (모든 arm9·오버레이에서 이 범위를 가리키는 4바이트 값 0개 — 이 도구가 쓰기 전에 다시 확인함).
      0x0226D680 속성표 128바이트(종 0~511, 종마다 2비트: 0 중립, 1 백신, 2 데이터, 3 바이러스)
      0x0226D700 배율 4바이트 [유리 분자, 불리 분자, 분모(100), 판 1]   0x0226D704 'DGAT'   0x0226D708 코드
  - 오버레이 12 는 압축을 풀어 놓는다(오버레이 표의 압축 표시를 끔, hg4_icons 와 같은 방식).
속성 자료: wikimon_속성.tsv + NDS_속성_고침.tsv(뒤가 이김), 종 칸: hg2_out/slots.tsv (이름 → 칸)
코드 원본(어셈블리): 수정판_시험/attr/build_hook.py (keystone 로 다시 만들어 이 파일의 HOOK_CODE 와 같은지 확인)"""
import os, sys, csv, struct, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hg1
from hg1 import NDS
import hg_scan

OV_ID = 12
OV_RAM = 0x022382C0
OV_SIZE = 0x37380
TABLE_ADDR = 0x0226D680          # 원래 sTypeEffectiveness (쓰는 곳 없음)
PARAM_ADDR = 0x0226D700
SIG_ADDR = 0x0226D704
CODE_ADDR = 0x0226D708
REGION_END = 0x0226D7D0          # 바로 뒤 0x0226D7D0 은 다른 표(0x02258DB4 가 가리킴) — 넘으면 안 됨
SIG = b'DGAT'
HOOK_SITE = 0x02252A3A           # ov12_02251D28 끝: ldr r0,[sp,#0x50]; add sp,#0x30; pop {r3-r7,pc}
HOOK_ORIG = bytes.fromhex('14980cb0f8bd')
NEW_TYPE_TABLE = 0x021FC4A0      # 페어리 패치가 옮긴 상성표(오버레이 18) — ov12 가 이걸 가리켜야 옛 표 자리가 비어 있는 것
OLD_TABLE_HEAD = bytes.fromhex('0005050008050a0a050a0b050a0c14')
OLD_TABLE_TAIL = bytes.fromhex('fefe00000700010700ffff00')      # FORESIGHT 줄 + 고스트 면역 2줄 + 끝 표시
ATTR_CODE = {'백신': 1, 'vaccine': 1, '데이터': 2, 'data': 2, '바이러스': 3, 'virus': 3}
ATTR_NAME = {0: '중립', 1: '백신', 2: '데이터', 3: '바이러스'}
DEN = 100

# 수정판_시험/attr/build_hook.py 의 SRC 를 keystone 으로 어셈블한 것(0x0226D708 에 놓임, Thumb)
HOOK_CODE = bytes.fromhex(
    '10b51e4969581e4a11421fd1179909688906'
    '1bd41698002818d0381c00f01bf8041c13d0'
    '301c00f016f800280ed0241a0cd0144a1178'
    '012c02d0a31c00d05178169848439178e6f7'
    '15fa00e0169810bc02bc0cb00847c0214143'
    '69180a4a895a4a0a08d1094a8b08d05c8907'
    '490fc8400321084070470020704700003c21'
    '00000088000000d72602402d000080d62602')

def thumb_bl(src, dst):
    off = dst - (src + 4)
    if not -0x400000 <= off < 0x400000 or off & 1: raise ValueError('BL 거리 밖 %X → %X' % (src, dst))
    off &= 0x7FFFFF
    return struct.pack('<HH', 0xF000 | (off >> 12), 0xF800 | ((off >> 1) & 0x7FF))

def bl_target(src, b):
    h1, h2 = struct.unpack('<HH', b)
    if (h1 & 0xF800) != 0xF000 or (h2 & 0xF800) != 0xF800: return None
    off = ((h1 & 0x7FF) << 12) | ((h2 & 0x7FF) << 1)
    if off & 0x400000: off -= 0x800000
    return src + 4 + off

def ov_entry(nds):
    y9o, y9s = struct.unpack_from('<II', nds.d, 0x50)
    for k in range(y9s // 32):
        e = list(struct.unpack_from('<8I', nds.d, y9o + 32 * k))
        if e[0] == OV_ID: return y9o + 32 * k, e
    raise SystemExit('오버레이 %d 이 오버레이 표에 없음' % OV_ID)

def ov_read(nds):
    pos, e = ov_entry(nds); s, t = nds.fat(e[6]); raw = bytes(nds.d[s:t])
    if e[7] & 0x01000000:
        dec = hg_scan.blz_decompress(raw)
        if not dec: raise SystemExit('오버레이 %d 압축 풀기 실패' % OV_ID)
        return pos, e, bytearray(dec), True
    return pos, e, bytearray(raw), False

def put_fid(nds, fid, data):
    """파일 번호로 놓기(hg4_icons.put_fid 와 같음): 제자리에 맞으면 제자리, 아니면 롬 끝"""
    s0, e0 = nds.fat(fid)
    if len(data) <= e0 - s0:
        nds.d[s0:s0 + len(data)] = data; struct.pack_into('<II', nds.d, nds.fat_off + fid * 8, s0, s0 + len(data)); how = '제자리'
    else:
        ns = (nds.used_end() + 0x1FF) & ~0x1FF; ne = ns + len(data)
        if len(nds.d) < ne: nds.d += b'\xff' * (ne - len(nds.d))
        nds.d[ns:ne] = data; struct.pack_into('<II', nds.d, nds.fat_off + fid * 8, ns, ne)
        if ne > struct.unpack_from('<I', nds.d, 0x80)[0]: struct.pack_into('<I', nds.d, 0x80, ne)
        while (0x20000 << nds.d[0x14]) < len(nds.d): nds.d[0x14] += 1
        how = '롬 끝(0x%X)' % ns
    struct.pack_into('<H', nds.d, 0x15E, hg1.crc16(bytes(nds.d[0:0x15E])))
    return how

def o(addr): return addr - OV_RAM

def region_refs(nds):
    """모든 arm9·오버레이에서 옛 상성표 자리(TABLE_ADDR~REGION_END)를 가리키는 4바이트 값 → [(이름, 위치, 값)] (그 자리 안에 있는 값 = 우리 코드의 상수는 뺌)"""
    hits = []
    for name, b in hg_scan.binaries(nds):
        for i in range(0, len(b) - 3, 4):
            v = struct.unpack_from('<I', b, i)[0]
            if not TABLE_ADDR <= v < REGION_END: continue
            if name.split('(')[0] == 'overlay12' and o(TABLE_ADDR) <= i < o(REGION_END): continue    # 우리 코드 안의 상수(표·배율 주소)
            hits.append((name, i, v))
    return hits

def read_tsv(path):
    if not os.path.exists(path): return []
    return list(csv.DictReader((l for l in open(path, encoding='utf-8') if not l.startswith('#')), delimiter='\t'))

def load_attrs(sets):
    attr = {}
    for fn in ('wikimon_속성.tsv', 'NDS_속성_고침.tsv'):
        for r in read_tsv(os.path.join(HERE, fn)):
            n, a = (r.get('이름') or '').strip(), (r.get('속성') or '').strip()
            if n and a: attr[n] = a
    attr.update(load_attrs_sets(sets))
    return attr

def load_attrs_sets(sets):
    return {n.strip(): a.strip() for n, a in (x.split('=', 1) for x in sets or [])}

def build_table(slots, attr):
    tab = bytearray(128); per = {}; missing = []
    for name, sp in slots.items():
        a = attr.get(name)
        if a is None: missing.append(name); continue
        c = ATTR_CODE.get(a.lower(), 0)
        if not 0 <= sp < 512: continue
        tab[sp >> 2] |= c << ((sp & 3) * 2); per[sp] = (name, a, c)
    return tab, per, missing

def dex_attrs(nds, slots):
    """도감 분류 글 파일(속성 이름으로 시작하는 줄이 50개 넘는 글 묶음)을 찾아 {칸: '백신'|'데이터'|'바이러스'|'중립'} (프리·언노운 → 중립)"""
    import re
    MSG = []
    for f in hg1.NARC(nds.get(hg1.NARC_PATHS['msg'])).files:
        try: MSG.append(hg1.msg_decode(f))
        except Exception: MSG.append((0, []))
    res = hg1.infer_charmap(MSG, set(slots))
    if not res: return None
    CM = res[0]; best = None
    for fi, (_, ent) in enumerate(MSG):
        if not 400 <= len(ent) <= 600: continue
        try: ds = [CM.dec(e) for e in ent]
        except Exception: continue
        k = sum(1 for d in ds if re.match(r'(백신|데이터|바이러스|프리|언노운)', d))
        if k > 50 and (best is None or k > best[0]): best = (k, fi, ds)
    if not best: return None
    out = {'_file': best[1]}
    for sp, d in enumerate(best[2]):
        m = re.match(r'(백신|데이터|바이러스|프리|언노운)', d)
        if m: out[sp] = {'프리': '중립', '언노운': '중립'}.get(m.group(1), m.group(1))
    return out

def lookup(tab, sp): return 0 if sp >= 512 else (tab[sp >> 2] >> ((sp & 3) * 2)) & 3

def model(att, dfn, dmg, adv, dis):
    """훅과 같은 계산(검산·설명용). 반환: 새 피해"""
    if dmg == 0 or att == 0 or dfn == 0 or att == dfn: return dmg
    diff = att - dfn
    num = adv if diff in (1, -2) else dis
    q = int(dmg * num / DEN)                    # C 의 나눗셈(0 쪽으로 자름)
    return q if q else (-1 if dmg < 0 else 1)   # DamageDivide

def show(nds, slots=None):
    pos, e, ov, comp = ov_read(nds)
    site = bytes(ov[o(HOOK_SITE):o(HOOK_SITE) + 6])
    if site == HOOK_ORIG: print('훅 없음(원래 코드)'); return None
    tgt = bl_target(HOOK_SITE, site[:4])
    sig = bytes(ov[o(SIG_ADDR):o(SIG_ADDR) + 4])
    print('훅: 0x%08X → 0x%08X, 표시 %r, 코드 같음 %s, 압축 %s' % (HOOK_SITE, tgt or 0, sig, bytes(ov[o(CODE_ADDR):o(CODE_ADDR) + len(HOOK_CODE)]) == HOOK_CODE, comp))
    p = ov[o(PARAM_ADDR):o(PARAM_ADDR) + 4]
    print('배율: 유리 ×%.2f, 불리 ×%.2f (분자 %d·%d / 분모 %d, 판 %d)' % (p[0] / p[2], p[1] / p[2], p[0], p[1], p[2], p[3]))
    tab = bytes(ov[o(TABLE_ADDR):o(TABLE_ADDR) + 128])
    cnt = {k: 0 for k in range(4)}
    for sp in range(512): cnt[lookup(tab, sp)] += 1
    print('속성표: ' + ', '.join('%s %d' % (ATTR_NAME[k], v) for k, v in cnt.items()))
    if slots:
        for name, sp in sorted(slots.items(), key=lambda x: x[1]): print('  칸 %3d %-10s %s' % (sp, name, ATTR_NAME[lookup(tab, sp)]))
    return tab

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('rom'); ap.add_argument('out', nargs='?')
    ap.add_argument('--base', help='원본 롬(훅 자리·옛 상성표가 원래 그대로인지 대조)')
    ap.add_argument('--slots', default=os.path.join(HERE, 'hg2_out', 'slots.tsv'))
    ap.add_argument('--adv', type=float, default=1.2, help='유리할 때 배율(기본 1.2)')
    ap.add_argument('--dis', type=float, default=0.8, help='불리할 때 배율(기본 0.8)')
    ap.add_argument('--set', action='append', help='이름=속성 (시험용 덮어쓰기, 여러 번)')
    ap.add_argument('--all', help='시험용: 모든 종을 이 속성으로(예: 프리 → 전부 중립). --set 이 그 위에 덮어씀')
    ap.add_argument('--check', action='store_true', help='읽기만: 들어 있는 훅·배율·속성표 보여 줌')
    ap.add_argument('--bps', help='--base 에서 결과까지의 BPS 패치를 이 경로에 씀')
    A = ap.parse_args()
    slots = {}
    for r in read_tsv(A.slots):
        try: slots[r['이름'].strip()] = int(r['칸'])
        except (KeyError, ValueError): pass
    nds = NDS(open(A.rom, 'rb').read())
    if A.check: show(nds, slots); return
    if not A.out: ap.error('out 롬 경로가 필요함')
    problems = []
    adv, dis = round(A.adv * DEN), round(A.dis * DEN)
    if not (0 <= adv <= 255 and 0 <= dis <= 255): raise SystemExit('배율은 0.00~2.55 (1바이트, 분모 100)')
    if not slots: raise SystemExit('종 칸표 없음: %s (hg2.py 를 먼저 돌릴 것)' % A.slots)

    # 1) 오버레이 12 확인
    pos, e, ov, comp = ov_read(nds)
    if e[1] != OV_RAM or len(ov) != OV_SIZE or e[2] != OV_SIZE or e[3] != 0:
        raise SystemExit('오버레이 12 모양이 다름(램 %08X 크기 %X/%X bss %X) — 한국판 디지몬골드 v1.6 바탕이 아님' % (e[1], e[2], len(ov), e[3]))
    site = bytes(ov[o(HOOK_SITE):o(HOOK_SITE) + 6])
    already = site[4:] == HOOK_ORIG[4:] and bl_target(HOOK_SITE, site[:4]) == CODE_ADDR and bytes(ov[o(SIG_ADDR):o(SIG_ADDR) + 4]) == SIG
    if not already:
        if site != HOOK_ORIG: raise SystemExit('훅 자리 0x%08X 바이트가 예상과 다름: %s (기대 %s)' % (HOOK_SITE, site.hex(), HOOK_ORIG.hex()))
        reg = bytes(ov[o(TABLE_ADDR):o(REGION_END)])
        if not (reg.startswith(OLD_TABLE_HEAD) and reg.endswith(OLD_TABLE_TAIL)):
            raise SystemExit('0x%08X~0x%08X 가 옛 타입 상성표가 아님 — 다른 패치가 이 자리를 썼을 수 있음, 멈춤' % (TABLE_ADDR, REGION_END))
    n_new = sum(1 for i in range(0, len(ov) - 3, 4) if struct.unpack_from('<I', ov, i)[0] in (NEW_TYPE_TABLE, NEW_TYPE_TABLE + 1, NEW_TYPE_TABLE + 2))
    if n_new < 10: raise SystemExit('ov12 의 상성표 주소(0x%08X)가 %d곳뿐(디지몬골드 v1.6 은 10곳) — 페어리 패치가 없는 롬이면 옛 표가 쓰이는 중일 수 있음, 멈춤' % (NEW_TYPE_TABLE, n_new))
    refs = region_refs(nds)
    if refs: raise SystemExit('옛 상성표 자리를 가리키는 값이 있음 → 쓸 수 없음: %s' % refs[:5])
    hg1.say('오버레이 12: %s, 상성표 주소 0x%08X %d곳(페어리 패치), 옛 표 자리를 가리키는 곳 0, 훅 %s' % ('압축' if comp else '압축 아님', NEW_TYPE_TABLE, n_new, '이미 있음 → 표·배율만 다시 씀' if already else '새로 넣음'))
    if A.base:
        bn = NDS(open(A.base, 'rb').read()); _, be, bov, _ = ov_read(bn)
        if bytes(bov[o(HOOK_SITE):o(HOOK_SITE) + 6]) != HOOK_ORIG: problems.append('원본 롬의 훅 자리가 예상과 다름')
        breg = bytes(bov[o(TABLE_ADDR):o(REGION_END)])
        if not (breg.startswith(OLD_TABLE_HEAD) and breg.endswith(OLD_TABLE_TAIL)): problems.append('원본 롬의 옛 상성표 자리가 예상과 다름')
        diff = sum(1 for a, b in zip(bov, ov) if a != b)
        hg1.say('원본 롬 오버레이 12 와 다른 바이트(쓰기 전): %d' % diff)

    # 2) 속성표
    attr = load_attrs(None)
    if A.all: attr = {n: A.all for n in slots}
    attr.update(load_attrs_sets(A.set))
    tab, per, missing = build_table(slots, attr)
    cnt = {k: sum(1 for v in per.values() if v[2] == k) for k in range(4)}
    others = sorted({v[1] for v in per.values() if v[2] == 0})
    hg1.say('속성표: %d종 — 백신 %d, 데이터 %d, 바이러스 %d, 중립 %d(%s), 속성 자료 없음 %d%s' % (len(per), cnt[1], cnt[2], cnt[3], cnt[0], '·'.join(others), len(missing), (' ' + ', '.join(missing)) if missing else ''))
    if missing: problems.append('속성 자료 없는 종(중립으로 둠): ' + ', '.join(missing))
    # 도감과 같은지: hg2 가 도감 분류 글 앞에 붙인 속성(「바이러스 양서류형」)과 전투 속성표가 칸마다 같은지 대조
    dex = dex_attrs(nds, slots)
    if dex is None: problems.append('도감 분류 글(속성 붙은 것)을 못 찾아 도감 대조를 못 함')
    else:
        bad = [(n, sp, ATTR_NAME[c], dex.get(sp, '-')) for sp, (n, a, c) in per.items() if dex.get(sp, '중립') != ATTR_NAME[c]]
        bad += [(n, sp, '중립', dex[sp]) for n, sp in slots.items() if sp not in per and dex.get(sp, '중립') != '중립']
        if bad: problems.append('도감 속성과 전투 속성이 다른 칸 %d: %s' % (len(bad), bad[:8]))
        hg1.say('도감 분류 글(msg %d)의 속성 ↔ 전투 속성표: %d종 대조, 다름 %d' % (dex['_file'], len(slots), len(bad)))

    # 3) 쓰기
    blob = bytes(tab) + bytes([adv, dis, DEN, 1]) + SIG + HOOK_CODE
    if TABLE_ADDR + len(blob) > REGION_END: raise SystemExit('코드가 자리보다 큼')
    blob += bytes(REGION_END - TABLE_ADDR - len(blob))
    ov[o(TABLE_ADDR):o(REGION_END)] = blob
    ov[o(HOOK_SITE):o(HOOK_SITE) + 4] = thumb_bl(HOOK_SITE, CODE_ADDR)
    how = put_fid(nds, e[6], bytes(ov))
    e[7] = 0; struct.pack_into('<8I', nds.d, pos, *e)       # 압축 아님 표시
    struct.pack_into('<H', nds.d, 0x15E, hg1.crc16(bytes(nds.d[0:0x15E])))
    hg1.say('오버레이 12 (압축 풀어 %d바이트) 놓은 곳: %s, 배율 유리 ×%.2f / 불리 ×%.2f' % (len(ov), how, adv / DEN, dis / DEN))
    out = bytes(nds.d)
    open(A.out, 'wb').write(out)

    # 4) 검산: 다시 읽어서
    n2 = NDS(open(A.out, 'rb').read()); _, e2, ov2, comp2 = ov_read(n2)
    ok = not comp2 and bytes(ov2) == bytes(ov)
    ok &= bl_target(HOOK_SITE, bytes(ov2[o(HOOK_SITE):o(HOOK_SITE) + 4])) == CODE_ADDR and bytes(ov2[o(HOOK_SITE) + 4:o(HOOK_SITE) + 6]) == HOOK_ORIG[4:]
    ok &= bytes(ov2[o(CODE_ADDR):o(CODE_ADDR) + len(HOOK_CODE)]) == HOOK_CODE
    t2 = bytes(ov2[o(TABLE_ADDR):o(TABLE_ADDR) + 128])
    wrong = [n for sp, (n, a, c) in per.items() if lookup(t2, sp) != c]
    ok &= not wrong
    # 코드 안 상수(문자 그대로 박힌 주소)가 이 파일의 상수와 맞는지
    lits = HOOK_CODE[-20:]
    ok &= struct.unpack('<5I', lits) == (0x213C, 0x8800, PARAM_ADDR, 0x2D40, TABLE_ADDR)
    ok &= sum(1 for k in range(0, len(HOOK_CODE) - 20, 2) if bl_target(CODE_ADDR + k, HOOK_CODE[k:k + 4]) == 0x02253B7C) == 1   # DamageDivide 부름 1곳
    # 오버레이 크기·위치표
    ok &= e2[1] == OV_RAM and e2[2] == OV_SIZE and e2[7] == 0 and n2.fat(e2[6])[1] - n2.fat(e2[6])[0] == OV_SIZE
    ok &= not region_refs(n2)
    hg1.say('검산(다시 읽어 훅·코드·표·오버레이 표): %s%s' % ('OK' if ok else '실패', (' 표 틀린 종 %s' % wrong[:5]) if wrong else ''))
    ex = []
    for (an, a), (dn, d) in (((1, '백신'), (3, '바이러스')), ((3, '바이러스'), (2, '데이터')), ((2, '데이터'), (1, '백신')), ((3, '바이러스'), (1, '백신')), ((1, '백신'), (1, '백신'))):
        ex.append('%s→%s 피해 100 → %d' % (a, d, -model(an, dn, -100, adv, dis)))
    hg1.say('예: ' + ', '.join(ex))
    if A.bps and A.base:
        base = open(A.base, 'rb').read(); patch = hg1.bps_make(base, out); open(A.bps, 'wb').write(patch)
        hg1.say('패치 %d바이트, 적용 확인 %s' % (len(patch), 'OK' if hg1.bps_apply(base, patch) == out else '실패'))
    hg1.say('== 문제 %d건' % len(problems)); [hg1.say('-', x) for x in problems]
    if not ok: sys.exit(1)

if __name__ == '__main__':
    main()
