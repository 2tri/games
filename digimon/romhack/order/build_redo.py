"""그림 주문서 v4 (2026-10-05 사용자: 「다시 뽑기 체크·메모를 다 읽어 새로 — 예전 내용 다 빼고, 재미나이 앞·뒤 스크립트만, 다시 뽑기의 그림 전부 보면서 고르게」)
    python3 build_redo.py --out <html> --r14 <r14.json> --redo <redo 폴더>
 자료: allmons.json (게임에 나오는 종) · r14.json (1.4 원래 그림, 롬 세션 비공개 아티팩트 — 저장소에 안 올림)
       · redo/*.json (롬 세션 「전투 그림 다시 뽑기」 페이지의 체크·메모, ArtifactData list redo) · art/<id>-f/-b.png
 카드마다: 지금 게임 앞·뒤, 체크(앞/뒤 다시)·메모, 받아 둔 새 그림, 할 일, 재미나이 한 줄(FRONT/BACK)"""
import argparse, base64, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(os.path.dirname(HERE)) + '/'
sys.path.insert(0, HERE)
import prompts, specs, redraw

GRADES = ['유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '성장기', '아머체', '성숙기', '완전체', '궁극체']
# 사용자 메모를 읽고 정한 할 일 (side: 'f'|'b'). how: gemini = 재미나이로 새로 / have = 받아 둔 그림 씀 / claude = 내가 고침 / ask = 확인 필요
PLAN = {
    3: {'f': ('gemini', '새로 뽑기'), 'b': ('gemini', '확대 → 상반신 크게 새로')},
    5: {'b': ('gemini', '90° 뒤가 아니라 옆뒤(3/4)로 새로')},
    8: {'b': ('gemini', '새로')},
    12: {'b': ('gemini', '새로')},
    15: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '상반신 크게 새로')},
    21: {'f': ('gemini', '크게 새로'), 'b': ('gemini', '크게 새로')},
    27: {'b': ('claude', '모양은 그대로, 색칠만 고침')},
    35: {'b': ('claude', '좌우 뒤집어 반대쪽 보기')},
    39: {'f': ('gemini', '크게 새로')},
    41: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '새로')},
    44: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '상반신 크게 새로')},
    56: {'f': ('gemini', '크게 새로'), 'b': ('gemini', '크게 새로')},
    57: {'f': ('gemini', '크게 새로'), 'b': ('gemini', '크게 새로')},
    60: {'b': ('claude', '바라보는 방향 → 롬 세션이 좌우 뒤집기')},
    92: {'f': ('gemini', '새로 (지금 앞모습 성의 없음)')},
    102: {'f': ('gemini', '크게 새로')},
    105: {'f': ('gemini', '크게 새로'), 'b': ('gemini', '크게 새로')},
    109: {'f': ('gemini', '새로 (워그레이몬 색만 바꾼 듯 뭉개짐)'), 'b': ('gemini', '새로')},
    111: {'f': ('have', '받아 둔 앞모습 씀')},
    112: {'b': ('gemini', '얼굴~몸 중간까지만 크게 새로')},
    117: {'f': ('gemini', '조금 크게 새로'), 'b': ('gemini', '조금 크게 새로')},
    129: {'f': ('ask', '보내 준 앞모습을 이 세션에서 못 찾음 — 다시 보내 주세요'), 'b': ('gemini', '조금 크게 새로')},
    130: {'b': ('gemini', '새로')},
    133: {'f': ('gemini', '크게 새로'), 'b': ('gemini', '크게 새로')},
    134: {'f': ('gemini', '새로'), 'b': ('gemini', '새로')},
    135: {'f': ('gemini', '새로'), 'b': ('gemini', '새로')},
    139: {'f': ('ask', '미사일 주황: 롬은 몸 색 2개뿐(지금 뼈색·회색) — 하나를 주황으로 바꿀지'), 'b': ('ask', '앞과 같은 색')},
    174: {'b': ('claude', '엉덩이까지 보이게 덜 확대')},
    186: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '크게 새로')},
    194: {'f': ('gemini', '크게 새로')},
    197: {'f': ('gemini', '크게 새로')},
}
# 메모를 주문문에 넣을 말 (영어)
EXTRA = {(5, 'b'): 'Turn it more to the side: a three-quarter rear view, not straight from behind.',
         (112, 'b'): 'Show only from the head down to the middle of the body, very big.',
         (109, 'f'): 'BlackWarGreymon: black armor (not orange). Keep the armor details readable at this size.',
         (109, 'b'): 'BlackWarGreymon: black armor.',
         (21, 'f'): 'Draw it larger than usual; it must fill the square.', (21, 'b'): 'Draw it larger than usual.',
         (133, 'f'): 'Draw it larger than usual; it must fill the square.', (133, 'b'): 'Draw it larger than usual.'}
HOW = {'gemini': '재미나이', 'have': '받아 둔 그림', 'claude': 'Claude가 고침', 'ask': '확인 필요'}


def b64(p): return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode() if p and os.path.exists(p) else ''


def en_of(did, ko):
    s = specs.by_id(did) or next((e for e in redraw.R if e['id'] == did), None)
    return (s or {}).get('en') or ({'v-mon': 'Veemon', 'xv-mon': 'ExVeemon', 'orgemon': 'Ogremon', 'imperialdramonpaladinmode': 'Imperialdramon Paladin Mode',
                                    'lilimon': 'Lilimon', 'fladramon': 'Flamedramon', 'lighdramon': 'Raidramon', 'megaseadramon': 'MegaSeadramon'}.get(did) or (did or ko).capitalize())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--r14', required=True); ap.add_argument('--redo', required=True)
    a = ap.parse_args()
    L = json.load(open(HERE + '/allmons.json')); r14 = json.load(open(a.r14))
    redo = {}
    for f in glob.glob(os.path.join(a.redo, '*.json')):
        d = json.load(open(f)); d = d.get('data', d); redo[int(d['no'])] = d
    rows = []
    for x in L:
        if x['src_f'] == 'egg' or x['ko'] in ('디지문자',): continue
        no, did = x['no'], x['id']
        g = r14.get(str(no)) or [None, None]
        gf = g[0] or (b64(WEB + 'art/%s-f.png' % did) if x['src_f'] == 'art' and did else '') or x.get('f', '')
        gb = g[1] or (b64(WEB + 'art/%s-b.png' % did) if x['src_b'] == 'art' and did else '') or x.get('b', '')
        newf = b64(WEB + 'art/%s-f.png' % did) if did and x['src_f'] != 'art' else ''      # 받아 뒀지만 아직 롬에 안 들어간 그림
        newb = b64(WEB + 'art/%s-b.png' % did) if did and x['src_b'] != 'art' else ''
        r = redo.get(no, {}); plan = PLAN.get(no, {})
        en = en_of(did, x['ko'])
        rows.append(dict(no=no, ko=x['ko'], en=en, grade=x['grade'] if x['grade'] in GRADES else '기타', order=x.get('order', 999), src=x['src_f'],
                         gf=gf, gb=gb, newf=newf, newb=newb, chk_f=bool(r.get('front')), chk_b=bool(r.get('back')), note=r.get('note', ''),
                         plan={k: [HOW[v[0]], v[1], v[0]] for k, v in plan.items()},
                         g_front=prompts.full_front(en, EXTRA.get((no, 'f'), '')), g_back=prompts.full_back(en, EXTRA.get((no, 'b'), '')),
                         img='https://digimon.net/cimages/digimon/%s.jpg' % did if did else ''))
    gi = lambda g: GRADES.index(g) if g in GRADES else len(GRADES)
    rows.sort(key=lambda r: (gi(r['grade']), r['order'], r['no']))
    D = {'rows': rows, 'grades': GRADES + ['기타']}
    html = open(HERE + '/redo_tpl.html', encoding='utf-8').read().replace('/*DATA*/null', json.dumps(D, ensure_ascii=False))
    assert 'pokemon' not in html.lower()
    open(a.out, 'w', encoding='utf-8').write(html)
    n = sum(1 for r in rows if r['chk_f'] or r['chk_b'])
    print(a.out, '%d종 · 체크 %d · %.0fKB' % (len(rows), n, len(html) / 1024))


if __name__ == '__main__':
    main()
