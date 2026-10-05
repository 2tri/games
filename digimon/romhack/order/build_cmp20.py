"""2.0 전투 그림 비교표 (2026-10-05 사용자: 「2.0 받으면 싹 비교 — 가져올 건 가져오고 버릴 건 버리고 참고할 건 참고」)
    python3 build_cmp20.py --out <html> --r20 <r20.json> --r14all <1.4 전 종 그림 json> --r14 <지금 롬 1.4 그림 r14.json>
 자료는 모두 롬 세션 비공개 페이지 것 (romdiff.py --pics-json) — 저장소에 안 올림. 우리 그림은 art/<id>-f/-b.png
 종마다 앞·뒤: 1.4 원본 | 2.0 | 지금 게임 → 고르기 (2.0 가져옴 / 지금 유지 / 2.0 참고) + 비고, 페이지 db pick20/<칸>-<f|b>"""
import argparse, base64, io, json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(os.path.dirname(HERE)) + '/'
sys.path.insert(0, HERE)
import build_redo as B

# 롬 세션 판정 (2026-10-05, 보고서 6-7 · art_judge.json) — 참고로 보여 줌, 고르는 건 사용자
_T, _K, _R = 'take', 'keep', 'ref'
REC = {
    '팔몬': {'f': (_T, '우리 앞모습은 분홍 꽃잎이 없음'), 'b': (_T, '')},
    '데블몬': {'f': (_T, ''), 'b': (_T, '임시 — 2.0 뒤는 앞모습 복사')},
    '팬텀몬': {'f': (_T, ''), 'b': (_T, '')}, '황제팔라딘': {'f': (_T, ''), 'b': (_T, '')},
    '아포카리몬': {'f': (_T, ''), 'b': (_T, '')}, '메탈시드몬': {'f': (_T, ''), 'b': (_T, '')}, '파워드라몬': {'f': (_T, ''), 'b': (_T, '')},
    '오메가몬': {'f': (_T, ''), 'b': (_K, '뒤는 1.4=2.0 같은 그림')},
    '워그레이몬': {'f': (_T, '1.4(=2.0) 그림 — 지금 우리 그림은 갈색 덩어리, 갑옷·방패 안 보임'), 'b': (_T, '1.4(=2.0) 그림')},
    '엔젤몬': {'f': (_R, '모양은 우리 판, 색만 2.0처럼 흰·하늘색'), 'b': (_R, '색만 2.0처럼')},
    '번개드라몬': {'f': (_K, '앞은 같음'), 'b': (_T, '지금 뒤는 파랑·노랑·흰 덩어리 — 검은 몸과 안 맞음')},
    '그레이몬': {'f': (_K, ''), 'b': (_K, '뒤 줄무늬 흰색 → 공식은 파랑 (고칠 거리)')},
    '엔젤우몬': {'f': (_K, ''), 'b': (_K, '뒷모습 머리카락 지저분 — 새 뒷모습 주문 후보')},
}
for _ko in ['쉬라몬', '피요몬', '아구몬', '파피몬', '매그너몬', '고스몬', '메라몬', '묘티스몬', '메탈그레몬', '워가루몬', '피에몬', '피노키몬']:
    REC.setdefault(_ko, {'f': (_K, ''), 'b': (_K, '')})


def px(u):
    if not u: return None
    try: return np.asarray(Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA'))
    except Exception: return None

def same(a, b):
    A, Bb = px(a), px(b)
    if A is None or Bb is None: return A is None and Bb is None
    if A.shape != Bb.shape: return False
    am, bm = A[..., 3] > 128, Bb[..., 3] > 128
    return bool((am == bm).all() and (A[..., :3][am] == Bb[..., :3][am]).all())

def load(p):
    if not p or not os.path.exists(p): return {}
    d = json.load(open(p)); return d.get('data', d) if isinstance(d, dict) else d

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--r20', required=True)
    ap.add_argument('--r14all'); ap.add_argument('--r14'); a = ap.parse_args()
    L = json.load(open(HERE + '/allmons.json')); r20 = load(a.r20); r14a = load(a.r14all); r14 = load(a.r14)
    rows = []
    for x in L:
        if x['src_f'] == 'egg' or not x['id'] and x['ko'].startswith('-'): continue
        no, did = x['no'], x['id']; k = str(no)
        o = r14a.get(k) or [None, None]; t = r20.get(k) or [None, None]; g = r14.get(k) or [None, None]
        cur = [(B.b64(WEB + 'art/%s-%s.png' % (did, s)) if x['src_' + s] == 'art' and did else '') or g[i] or x.get(s, '') for i, s in enumerate('fb')]
        sides = {}; rc = REC.get(x['ko'], {})
        for i, s in enumerate('fb'):
            sides[s] = dict(o=o[i] or '', t=t[i] or '', c=cur[i], diff=bool(t[i]) and not same(o[i], t[i]), ours=x['src_' + s] == 'art', rec=list(rc.get(s, ('', ''))))
        rows.append(dict(no=no, ko=x['ko'], en=B.en_of(did, x['ko']) if did else x['ko'], grade=x['grade'] if x['grade'] in B.GRADES else '기타',
                         order=x.get('order', 999), s=sides, img='https://digimon.net/cimages/digimon/%s.jpg' % did if did else ''))
    gi = lambda g: B.GRADES.index(g) if g in B.GRADES else len(B.GRADES)
    rows.sort(key=lambda r: (gi(r['grade']), r['order'], r['no']))
    D = {'rows': rows, 'grades': B.GRADES + ['기타']}
    style = open(HERE + '/redo_tpl.html', encoding='utf-8').read()
    style = style[style.index('<style>'):style.index('</style>', style.index('</style>') + 8) + 8]
    html = open(HERE + '/cmp20_tpl.html', encoding='utf-8').read().replace('/*STYLE*/', style).replace('/*DATA*/null', json.dumps(D, ensure_ascii=False))
    open(a.out, 'w', encoding='utf-8').write(html)
    nd = sum(r['s'][s]['diff'] for r in rows for s in 'fb')
    print(a.out, '%d종 · 2.0 에서 달라진 그림 %d장 · %.0fKB' % (len(rows), nd, len(html) / 1024))

if __name__ == '__main__':
    main()
