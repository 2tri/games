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
    3: {'f': ('gemini', '새로 뽑기'), 'b': ('claude', '확대 — 시험해 보니 됨, 롬 세션이 키움')},
    5: {'b': ('gemini', '90° 뒤가 아니라 옆뒤(3/4)로 새로')},
    8: {'b': ('gemini', '새로')},
    12: {'b': ('gemini', '새로')},
    15: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '받아 둔 앞모습에 맞춰 새로 (색이 같아야 함)')},
    21: {'f': ('gemini', '새로 (사용자: 호크몬도 주문)'), 'b': ('gemini', '새로')},
    27: {'b': ('claude', '모양은 그대로, 색칠만 고침')},
    35: {'b': ('claude', '좌우 뒤집어 반대쪽 보기')},
    39: {'f': ('claude', '확대 — 시험해 보니 됨, 롬 세션이 키움')},
    41: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '뒷모습 사진을 찾아 「공통 주문문」으로 (지금 롬은 앞·뒤 1.4)')},
    44: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '받아 둔 앞모습에 맞춰 새로 (색이 같아야 함)')},
    56: {'f': ('claude', '확대 — 됨, 롬 세션이 키움'), 'b': ('claude', '확대 — 됨, 롬 세션이 키움')},
    57: {'f': ('claude', '확대 — 됨, 롬 세션이 키움'), 'b': ('claude', '확대 — 됨, 롬 세션이 키움')},
    60: {'b': ('gemini', '뒷모습 새로 — 첨부 = 이 카드의 「지금 게임 앞」 (길게 눌러 저장)')},
    92: {'f': ('gemini', '새로 (지금 앞모습 성의 없음)')},
    102: {'f': ('claude', '확대 — 됨, 롬 세션이 키움')},
    105: {'f': ('claude', '확대 — 됨, 롬 세션이 키움'), 'b': ('gemini', '확대하면 검게 뭉개짐 → 크게 새로')},
    109: {'f': ('gemini', '새로 (워그레이몬 색만 바꾼 듯 뭉개짐)'), 'b': ('gemini', '새로')},
    111: {'f': ('have', '받아 둔 앞모습 씀')},
    112: {'b': ('claude', '확대 — 됨, 롬 세션이 키움 (얼굴~몸 중간이 크게 보임)')},
    117: {'f': ('claude', '확대 — 됨, 롬 세션이 키움'), 'b': ('claude', '확대 — 됨, 롬 세션이 키움')},
    129: {'f': ('gemini', '새로 — 작고 생김새가 까다로워 설명을 넣은 주문문'), 'b': ('gemini', '새로 — 같은 설명')},
    130: {'b': ('gemini', '새로')},
    133: {'f': ('gemini', '새로 그리기 (사용자: 확대본 말고 새로)'), 'b': ('gemini', '새로 그리기')},
    134: {'f': ('gemini', '새로'), 'b': ('gemini', '새로')},
    135: {'f': ('gemini', '새로'), 'b': ('gemini', '새로')},
    139: {'f': ('claude', '미사일만 주황으로 고침 (뼈 그늘 회색은 뼈색으로 합침)'), 'b': ('claude', '같게 고침')},
    174: {'b': ('claude', '엉덩이까지 보이게 덜 확대')},
    186: {'f': ('have', '받아 둔 앞모습 씀'), 'b': ('gemini', '받아 둔 앞모습에 맞춰 크게 새로')},
    194: {'f': ('claude', '확대 — 됨, 롬 세션이 키움')},
    197: {'f': ('claude', '확대 — 됨, 롬 세션이 키움')},
}
# 메모를 주문문에 넣을 말 (영어)
EXTRA = {(133, 'f'): 'Veemon: small blue dragon with a white muzzle and belly, a yellow V mark on the forehead, one small horn on the nose, big eyes. Draw it BIG so it fills the square.',
         (133, 'b'): 'Veemon: blue back, the tips of its pointed ears, small tail.',
         (129, 'f'): 'Betamon is a small green amphibian: a big round head with a very wide mouth, a single tall red fin running from the top of its head down its back, four short legs, a pale belly. Draw it BIG so the head and fin fill the square; keep the red fin clearly visible.',
         (129, 'b'): 'Betamon: green amphibian seen from behind; the tall red fin along its head and back is the main shape, big and clear.',
         (5, 'b'): 'Turn it more to the side: a three-quarter rear view, not straight from behind.',
         (112, 'b'): 'Show only from the head down to the middle of the body, very big.',
         (109, 'f'): 'BlackWarGreymon: black armor (not orange). Keep the armor details readable at this size.',
         (109, 'b'): 'BlackWarGreymon: black armor.',
         (21, 'f'): 'Draw it larger than usual; it must fill the square.', (21, 'b'): 'Draw it larger than usual.',
         }
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
                         plan={k: ([HOW['have'], '받음 — 롬에 넣는 중', 'have'] if (newf if k == 'f' else newb) and v[0] == 'gemini' else [HOW[v[0]], v[1], v[0]]) for k, v in plan.items()},
                         g_front=prompts.COMMON_CONVERT, g_back=prompts.COMMON_BACK,   # 2026-10-05 사용자: 색은 Claude 가 넣으니 주문문은 모든 종 똑같이
                         img='https://digimon.net/cimages/digimon/%s.jpg' % did if did else ''))
    gi = lambda g: GRADES.index(g) if g in GRADES else len(GRADES)
    rows.sort(key=lambda r: (gi(r['grade']), r['order'], r['no']))
    D = {'common': prompts.COMMON_CONVERT, 'common_b': prompts.COMMON_BACK, 'rows': rows, 'grades': GRADES + ['기타']}
    html = open(HERE + '/redo_tpl.html', encoding='utf-8').read().replace('/*DATA*/null', json.dumps(D, ensure_ascii=False))
    assert 'pokemon' not in html.lower()
    open(a.out, 'w', encoding='utf-8').write(html)
    n = sum(1 for r in rows if r['chk_f'] or r['chk_b'])
    print(a.out, '%d종 · 체크 %d · %.0fKB' % (len(rows), n, len(html) / 1024))


if __name__ == '__main__':
    main()
