"""롬 전체 종 목록 (그림 세션 주문서용, 2026-10-04) → order/allmons.json
  python3 order/allmons.py            지금 패치 롬(work/myver.gbc) 기준. 그림(f·b)은 우리 그림(src "art")만 넣음
  python3 order/allmons.py --with-14 OUT.json   1.4 원래 그림도 넣은 판 (롬에서 뽑은 그림이라 공개 저장소에 올리지 않음 — 사용자 확인 전)
항목: no·ko·grade·line(뿌리 → 이 종)·next(진화 → 조건)·id(art/<id>-f.png)·src_f·src_b("art" 우리 그림 / "1.4" 디지몬스터 원래 그림 / "egg" 빈 칸)
      ·f·b(롬 팔레트 입힌 PNG data URL, 앞 56칸·뒤 48칸)·where(나오는 곳 한 줄)·family(진화 줄 뿌리 번호)·order(단계순, 같은 단계는 줄끼리)"""
import base64, io, json, os, re, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import dmrom, check, remap, rules

GRADES = ['유아기', '유년기Ⅰ', '유년기Ⅱ', '유년기', '성장기', '아머체', '성숙기', '완전체', '궁극체']
TIME = re.compile(r' (아침|낮|밤)$')


def png_url(idx, pal, size):
    cols = np.array([(255, 255, 255), pal[0], pal[1], (0, 0, 0)], np.uint8)
    h, w = idx.shape; can = np.full((size, size, 3), 255, np.uint8)
    oy, ox = size - h, (size - w) // 2                                  # 게임처럼 아래·가운데 맞춤
    can[oy:oy + h, ox:ox + w] = cols[idx]
    buf = io.BytesIO(); Image.fromarray(can).save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def ids():
    """이름 → art id: rules.REDRAW · slots.json · 주문서 자료 · keep_dirs(칸 번호)"""
    m = {}
    for v in json.load(open(os.path.join(HERE, 'order', 'needs.json'))).values():
        if isinstance(v, dict) and v.get('name') and v.get('dir'): m.setdefault(v['name'], v['dir'])
    sys.path.insert(0, os.path.join(HERE, 'order')); import specs, redraw
    for s in specs.S: m[s['ko']] = s['id']
    for e in redraw.R: m[e['ko']] = e['id']
    for s in json.load(open(os.path.join(HERE, 'slots.json')))['mons']: m[s['name']] = s['id']
    m.update({k: v for k, v in rules.REDRAW.items()})
    m.update({'코로몬': 'koromon', '메탈그레몬': 'metalgreymon', '워가루몬': 'weregarurumon'})
    return m, {int(k): v for k, v in json.load(open(os.path.join(HERE, 'order', 'keep_dirs.json'))).items()}


def from14(nm, back):
    """롬 그림이 바뀌었어도 1.4 그림에서 나온 것(확대·뒤집기)이면 True — 공개 allmons.json 에 넣지 않음 (patch.py 설치 순서와 같은 판정)"""
    art = lambda a, s: os.path.exists(os.path.join(HERE, '..', 'art', '%s-%s.png' % (a, s)))
    a = rules.REDRAW.get(nm)
    if a and art(a, 'f') and art(a, 'b'): return False
    if back:
        a = rules.BACK_ONLY.get(nm)
        if a and art(a, 'b') and not art(a, 'f'): return False
        return nm in rules.ENLARGE14_BACK or nm in rules.FLIP_BACK or nm in rules.FRONT_ART_BIG_BACK or (nm, '뒤') in rules.SCALE14
    a = rules.FRONT_ONLY.get(nm)
    if a and art(a, 'f') and not art(a, 'b'): return False
    if nm in rules.FRONT_ART_BIG_BACK: return False
    return nm in rules.ENLARGE14_FRONT or (nm, '앞') in rules.SCALE14


def main(out, with14=False):
    c = check.Ctx(os.path.join(dmrom.WORK, 'myver.gbc')); r = c.r; base = c.base
    name_id, keep_dirs = ids()
    pre = {}
    for n in range(1, 252):
        for e in c.evos(n): pre.setdefault(e[-1], n)
    def chain(n):
        out = [n]
        while out[-1] in pre and pre[out[-1]] not in out: out.append(pre[out[-1]])
        return out[::-1]
    where = {}
    for s in c.sites:
        k = s['kind'] if s['kind'] not in remap.WILD else '야생'
        if k in ('트레이너', '경품 확인', '선물 돌려받기', '교환(주는 종)'): continue
        where.setdefault(s['cur'], {}).setdefault(k, set()).add(TIME.sub('', s['where']))
    tr = {}
    for t in c.trainers:
        for _, sp, _ in t['mons']: tr.setdefault(sp, set()).add(check.GROUPS[t['group']])
    rows = []
    for n in range(1, 252):
        nm = c.name(n)
        ent = r.pics + 6 * (n - 1); bent = base.pics + 6 * (n - 1)
        empty = nm == rules.EMPTY_NAME
        src = []
        for k in (0, 3):
            src.append('egg' if empty else '1.4' if r.d[ent + k:ent + k + 3] == base.d[bent + k:bent + k + 3] or from14(nm, k == 3) else 'art')
        row = dict(no=n, ko=nm, grade=c.grade.get(n, ''), pokemon=n in c.pk,
                   line='→'.join(c.name(x) for x in chain(n)),
                   next=['%s %s' % (c.name(e[-1]), c.cond(e)) for e in c.evos(n)],
                   id=name_id.get(nm) or ('' if empty else keep_dirs.get(n, '')),
                   src_f=src[0], src_b=src[1], f='', b='')
        w = []
        for k, locs in sorted(where.get(n, {}).items()):
            locs = sorted(locs); w.append('%s: %s%s' % (k, ', '.join(locs[:4]), ' 외 %d곳' % (len(locs) - 4) if len(locs) > 4 else ''))
        if n in tr: g = sorted(tr[n]); w.append('트레이너: %s%s' % (', '.join(g[:4]), ' 외 %d' % (len(g) - 4) if len(g) > 4 else ''))
        row['where'] = ' / '.join(w)
        if not empty and n != rules.UNOWN[0]:
            pal = r.palette(n)
            for key, back, s_ in (('f', False, src[0]), ('b', True, src[1])):
                if s_ == 'art' or with14:
                    row[key] = png_url(r.pic(n, back), pal, 48 if back else 56)
        rows.append(row)
    # 순서: 단계(유년기 → … → 궁극체) 먼저, 같은 단계 안에서는 진화 줄(family = 줄 뿌리 번호)끼리. 빈 칸은 맨 뒤
    for row in rows: row['family'] = chain(row['no'])[0]
    def key(row):
        g = row['grade']
        return (row['ko'] == rules.EMPTY_NAME, GRADES.index(g) if g in GRADES else 99, row['family'], row['no'])
    rows.sort(key=key)
    for i, row in enumerate(rows): row['order'] = i + 1
    json.dump(rows, open(out, 'w'), ensure_ascii=False, indent=0)
    n_art = sum(1 for x in rows if x['src_f'] == 'art'); n14 = sum(1 for x in rows if x['src_f'] == '1.4')
    print('%d종 → %s (앞 그림: 우리 그림 %d, 1.4 원래 %d, 빈 칸 %d)%s' % (len(rows), out, n_art, n14, sum(1 for x in rows if x['src_f'] == 'egg'),
                                                               '' if with14 else ' — 1.4 그림은 비워 둠'))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--with-14': main(a[1], True)
    else: main(os.path.join(HERE, 'order', 'allmons.json'))
