"""20판: 검수 페이지에서 「모두 틀림」으로 고른 종만 뽑아 새 그림 주문서(아티팩트 HTML)를 만든다.
python3 order_new.py [출력.html]   → 기본 work/order_new.html   (picks.json 의 f 또는 b 가 none 인 종)
주문문은 order/prompts.py 의 card_front·card_back (이름을 넣은 공통 주문문)."""
import os, sys, json, html
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'order'))
import prompts

# id → (영어 이름, 위키몬 문서, 공식 그림 직접 주소 또는 None, 메모)
INFO = {
    'leafmon': ('Leafmon', 'Leafmon', 'https://wikimon.net/images/e/ea/Leafmon.jpg', ''),
    'pegasusmon': ('Pegasusmon', 'Pegasusmon', 'https://wikimon.net/images/9/98/Pegasmon.jpg', '위키몬 문서 이름은 Pegasmon (같은 디지몬).'),
    'tsubumon': ('Tsubumon', 'Tsubumon', None, '위키몬 문서 안에서 첫 그림을 쓰세요.'),
    'shogungekomon': ('ShogunGekomon', 'ShogunGekomon', None, '위키몬 문서 이름은 Tonosama Gekomon (같은 디지몬).'),
    'nyaromon': ('Nyaromon', 'Nyaromon', 'https://wikimon.net/images/b/bc/Nyaromon.jpg', ''),
    'nefertimon': ('Nefertimon', 'Nefertimon', 'https://wikimon.net/images/c/c8/Nefertimon.jpg', ''),
    'upamon': ('Upamon', 'Upamon', 'https://wikimon.net/images/d/dd/Upamon.jpg', ''),
    'submarimon': ('Submarimon', 'Submarimon', 'https://wikimon.net/images/a/a4/Submarimon.jpg', ''),
    'giromon': ('Giromon', 'Giromon', 'https://wikimon.net/images/8/85/Giromon.jpg', ''),
    'pururumon': ('Pururumon', 'Pururumon', 'https://wikimon.net/images/0/03/Pururumon.jpg', ''),
    'scorpiomon': ('Anomalocarimon', 'Anomalocarimon', 'https://wikimon.net/images/3/33/Anomalocarimon.jpg', '한국어 이름 스콜피오몬 = Anomalocarimon (설계자 종 목록, 사용자 확인). 위키몬에 DS 전투 그림은 없음(확인함).'),
    'deathmeramon': ('DeathMeramon', 'DeathMeramon', 'https://wikimon.net/images/a/ae/Deathmeramon.jpg', '위키몬 문서 이름은 Death Meramon.'),
    'whamon': ('Whamon', 'Whamon', None, '위키몬 문서 안에서 첫 그림(Whamon_adult.jpg 등)을 쓰세요.'),
    'rosemon': ('Rosemon', 'Rosemon', 'https://wikimon.net/images/9/91/Rosemon.gif', '스타팅 특례 칸(릴리몬 → 로제몬).'),
    'garbagemon': ('Garbagemon', 'Garbagemon', 'https://wikimon.net/images/5/5b/Gerbemon.jpg', '영어판 이름 Gerbemon (위키몬 문서 이름).'),
}
GRADE_ALIAS = {'유아기Ⅰ': '유년기Ⅰ', '유아기Ⅱ': '유년기Ⅱ'}
GRADE = {'leafmon': '유년기Ⅱ', 'pegasusmon': '아머체', 'tsubumon': '유년기Ⅰ', 'shogungekomon': '완전체', 'nyaromon': '유년기Ⅱ', 'nefertimon': '아머체', 'upamon': '유년기Ⅱ',
         'submarimon': '아머체', 'giromon': '완전체', 'pururumon': '유년기Ⅰ', 'scorpiomon': '완전체', 'deathmeramon': '완전체', 'whamon': '완전체', 'rosemon': '궁극체',
         'garbagemon': '완전체'}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'work', 'order_new.html')
    picks = json.load(open(os.path.join(HERE, 'picks.json'), encoding='utf-8'))
    rows = []
    for v in picks.values():
        if 'none' not in (v['f'], v['b']): continue
        i = v['id']; en, wiki, img, memo = INFO[i]; g = GRADE[i]
        rows.append({'ko': v['name'], 'id': i, 'grade': g, 'en': en, 'wiki': wiki, 'img': img, 'memo': memo,
                     'front': prompts.card_front(en), 'back': prompts.card_back(en, g),
                     'need': '앞·뒤' if v['f'] == v['b'] == 'none' else ('앞' if v['f'] == 'none' else '뒤')})
    order = ['유년기Ⅰ', '유년기Ⅱ', '성장기', '아머체', '완전체', '궁극체']
    rows.sort(key=lambda r: (order.index(r['grade']) if r['grade'] in order else 9, r['ko']))
    tpl = open(os.path.join(HERE, 'order_new_tpl.html'), encoding='utf-8').read()
    open(out, 'w', encoding='utf-8').write(tpl.replace('/*DATA*/[]', json.dumps(rows, ensure_ascii=False, separators=(',', ':'))))
    print('%s (%d종)' % (out, len(rows)))


if __name__ == '__main__':
    main()
