"""롬 2~3개를 영역별로 비교 (1.4 / 2.0 / 우리 판) → work/romdiff.json  — 원작 내용이 들어가므로 work/ 와 비공개 페이지에만 (저장소에 안 올림)
  python3 romdiff.py 1.4.gbc 2.0.gbc work/myver.gbc --labels 1.4 2.0 우리판
  python3 romdiff.py 2.0.gbc --pics-json work/r20.json        2.0 전투 그림을 r14.json 처럼 {칸: [앞, 뒤]} (롬 팔레트 PNG data URL)
영역: 종(이름·능력치·타입·포획·경험치·성장) · 진화 · 레벨업 기술 · 기술(이름·위력 등) · 야생 출현 · 트레이너 편성 · 도구 이름 · 음악 · 전투 그림 · 대사
  디지몬 단위 영역(종·진화·기술 배우기·그림)은 이름으로 맞춤 (판마다 칸이 달라도 같은 디지몬끼리 비교, 칸 번호는 값에 같이 적음)
  맵 배치·이벤트·제목·UI 는 아직 안 함 — 대사·야생·트레이너로 간접 비교 (2.0 을 받은 뒤 구조를 보고 추가)"""
import argparse, base64, difflib, hashlib, io, json, os, re, sys
import numpy as np
from PIL import Image
import dmrom, encounters, gblz, krtext, texts

HERE = os.path.dirname(os.path.abspath(__file__))
GROUPS = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
TYPE = {0: '노말', 1: '격투', 2: '비행', 3: '독', 4: '땅', 5: '바위', 6: '새', 7: '벌레', 8: '고스트', 9: '강철', 19: '???',
        20: '불꽃', 21: '물', 22: '풀', 23: '전기', 24: '에스퍼', 25: '얼음', 26: '드래곤', 27: '악'}
EVK = {1: '레벨', 2: '도구', 3: '교환', 4: '친밀도', 5: '능력치'}


def png_url(idx, pal, size):
    cols = np.array([(255, 255, 255), pal[0], pal[1], (0, 0, 0)], np.uint8)
    h, w = idx.shape; can = np.full((size, size, 3), 255, np.uint8)
    can[size - h:, (size - w) // 2:(size - w) // 2 + w] = cols[idx]
    buf = io.BytesIO(); Image.fromarray(can).save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def names_list(d, first, count, maxlen=20):
    """첫 이름(한글)으로 0x50 으로 끝나는 이름 목록을 찾아 count 개 읽음"""
    i = d.find(krtext.encode(first) + b'\x50')
    if i < 0: return None
    out = []
    for _ in range(count):
        j = d.index(0x50, i); out.append(krtext.decode(d, i, j)); i = j + 1
    return out


def move_table(d):
    for m in re.finditer(rb'\x01..', d, re.S):
        a = m.start()
        if a + 7 * 251 < len(d) and all(d[a + 7 * k] == k + 1 for k in range(1, 80)): return a
    return None


def music_table(d):
    m = re.search(rb'\x21(..)\x19\x19\x19\x2a\xea', d, re.S)
    return dmrom.addr(m.start() // 0x4000, int.from_bytes(m.group(1), 'little')) if m else None


def collect(path, with_pics=False):
    r = dmrom.Rom(path); d = bytes(r.d); A = {}
    nm = {n: r.name(n) for n in range(1, dmrom.NUM + 1)}
    seen = {}
    def key(n):                                        # 디지몬 단위 열쇠 = 이름 (빈 이름·겹치는 이름은 칸 번호를 붙임)
        k = nm[n].strip() or '(빈 이름)'
        if k in ('-----', '(빈 이름)') or list(nm.values()).count(nm[n]) > 1: k = '%s #%03d' % (k, n)
        return k
    keys = {n: key(n) for n in range(1, dmrom.NUM + 1)}
    mv_names = names_list(d, '막치기', 251) or ['기술%d' % i for i in range(1, 252)]
    # 종
    A['종'] = {}
    for n in range(1, dmrom.NUM + 1):
        b = r.base_stats(n); t = '/'.join(dict.fromkeys(TYPE.get(x, str(x)) for x in b['type']))
        A['종'][keys[n]] = '칸 %03d · HP %d 공 %d 방 %d 스 %d 특공 %d 특방 %d · %s · 포획 %d · 경험 %d · 성장 %d' % (
            n, b['hp'], b['atk'], b['def'], b['spd'], b['sat'], b['sdf'], t, b['catch'], b['exp'], b['growth'])
    # 진화 · 레벨업 기술
    A['진화'] = {}; A['기술 배우기'] = {}
    for n in range(1, dmrom.NUM + 1):
        try: ev, mv = r.evos_attacks(n)
        except Exception as e: A['진화'][keys[n]] = '읽기 실패 %s' % e; continue
        A['진화'][keys[n]] = ', '.join('%s %s → %s' % (EVK.get(e[0], e[0]), '/'.join(str(x) for x in e[1:-1]), nm.get(e[-1], e[-1])) for e in ev) or '없음'
        A['기술 배우기'][keys[n]] = ', '.join('Lv%d %s' % (lv, mv_names[m - 1] if 0 < m <= 251 else m) for lv, m in mv) or '없음'
    # 기술
    A['기술'] = {}; T0 = move_table(d)
    for i in range(251):
        if T0 is None: break
        b = d[T0 + 7 * i:T0 + 7 * i + 7]
        A['기술']['%03d' % (i + 1)] = '%s · %s 위력 %d 명중 %d%% PP %d · 효과 %d(확률 %d%%) · 연출 %d' % (
            mv_names[i], TYPE.get(b[3], b[3]), b[2], round(b[4] * 100 / 255), b[5], b[1], round(b[6] * 100 / 255), b[0])
    # 야생 · 트레이너
    A['야생'] = {}; A['트레이너'] = {}; cnt = {}
    try: sites = encounters.find_all(r)                            # 원작 롬(1.4·2.0)은 그 롬에서 바로 찾음
    except Exception: sites = encounters.find_all(dmrom.Rom(dmrom.default_rom()))   # 고친 롬(우리 판)은 표 모양이 바뀌어 못 찾으면 1.4 자리에서 지금 값을 읽음
    for s in sites:
        if s['kind'] == '트레이너': continue
        k0 = '%s · %s' % (s['kind'], s['where']); cnt[k0] = cnt.get(k0, 0) + 1
        sp = d[s['addr']]; lv = d[s['addr'] - 1] if s['kind'] not in ('고정 만남', '선물', '경품', '교환(주는 종)', '알') else s.get('lv', '')
        A['야생']['%s · %d' % (k0, cnt[k0])] = '%s Lv%s' % (nm.get(sp, sp), lv)
    for t in r.trainers(len(GROUPS)):
        A['트레이너']['%s #%02d %s' % (GROUPS[t['group']], t['idx'], t['name'])] = ', '.join('%s Lv%d' % (nm.get(sp, sp), lv) for lv, sp, _ in t['mons'])
    # 도구
    it = names_list(d, '마스터볼', 255) or []
    A['도구'] = {'%03d' % (i + 1): x for i, x in enumerate(it)}
    # 음악: 번호마다 곡 머리 + 채널 앞 512바이트 해시 (곡이 같은지만)
    A['음악'] = {}; mt = music_table(d)
    for i in range(0x67 if mt else 0):
        bank = d[mt + 3 * i]; ptr = d[mt + 3 * i + 1] | d[mt + 3 * i + 2] << 8
        if not 0x4000 <= ptr < 0x8000: continue
        h = dmrom.addr(bank, ptr)
        if h + 12 >= len(d): continue                              # 음악 표 끝 너머 (판마다 곡 수가 다를 수 있음)
        n = (d[h] >> 6) + 1; blob = d[h:h + 3 * n]
        for k in range(n):
            c = dmrom.addr(bank, d[h + 3 * k + 1] | d[h + 3 * k + 2] << 8)
            if c < len(d): blob += d[c:c + 512]
        A['음악']['%02X' % i] = '곡 %s' % hashlib.md5(blob).hexdigest()[:8]
    # 전투 그림: 이름별 앞·뒤 해시 (그림 자체는 with_pics 일 때만)
    A['전투 그림'] = {}; pics = {}
    for n in range(1, dmrom.NUM + 1):
        if n == 201: continue
        hs = []
        for back in (False, True):
            try: t = r.pic(n, back=back); hs.append(hashlib.md5(t.tobytes()).hexdigest()[:8] if t is not None else '-')
            except Exception: t = None; hs.append('읽기 실패')
            if with_pics and t is not None: pics.setdefault(str(n), [None, None])[back] = png_url(t.astype(np.uint8), r.palette(n), 48 if back else 56)
        A['전투 그림'][keys[n]] = '칸 %03d · 앞 %s · 뒤 %s' % (n, hs[0], hs[1])
    # 대사 (주소 순서)
    idx = texts.refs_index(d); tx = []
    for (bank, ptr) in sorted(idx):
        p = dmrom.addr(bank, ptr)
        if p >= len(d): continue
        t = texts.read_text(d, p)
        if t and t[1] >= 2: tx.append(t[2])
    return A, tx, pics


def compare(paths, labels):
    data = [collect(p) for p in paths]
    out = {'labels': labels, 'areas': {}}
    for area in data[0][0]:
        keys = []
        for A, _, _ in data:
            for k in A.get(area, {}):
                if k not in keys: keys.append(k)
        rows = []
        for k in keys:
            vals = [A.get(area, {}).get(k) for A, _, _ in data]
            rows.append({'key': k, 'vals': vals, 'same': len(set(map(str, vals))) == 1})
        out['areas'][area] = rows
    # 대사: 첫 판과 나머지를 차례 맞춰 비교 (바뀐 덩어리만)
    base = data[0][1]; rows = []
    for j, (_, tx, _) in enumerate(data[1:], 1):
        sm = difflib.SequenceMatcher(None, base, tx, autojunk=False)
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == 'equal': continue
            for k in range(max(a2 - a1, b2 - b1)):
                va = base[a1 + k] if a1 + k < a2 else None; vb = tx[b1 + k] if b1 + k < b2 else None
                vals = [va] + [None] * (len(data) - 1); vals[j] = vb
                rows.append({'key': '%s 대사 %d' % (labels[j], len(rows) + 1), 'vals': vals, 'same': False})
    out['areas']['대사'] = rows
    out['texts_count'] = [len(tx) for _, tx, _ in data]
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('roms', nargs='+'); ap.add_argument('--labels', nargs='*')
    ap.add_argument('--out', default=os.path.join(dmrom.WORK, 'romdiff.json')); ap.add_argument('--pics-json')
    a = ap.parse_args()
    if a.pics_json:
        _, _, pics = collect(a.roms[0], with_pics=True)
        json.dump(pics, open(a.pics_json, 'w'), separators=(',', ':')); print('전투 그림 %d칸 → %s' % (len(pics), a.pics_json)); sys.exit()
    labels = a.labels or [os.path.basename(p) for p in a.roms]
    out = compare(a.roms, labels)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False)
    print('비교:', ' / '.join(labels), '→', a.out)
    for area, rows in out['areas'].items():
        print('  %-8s %5d줄, 다름 %d' % (area, len(rows), sum(1 for r in rows if not r['same'])))
    print('  대사 덩어리 수:', out['texts_count'])
