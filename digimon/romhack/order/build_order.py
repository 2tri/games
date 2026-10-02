"""그림 주문서 다시 만들기 (롬 없이) → 아티팩트 「디지몬스터 그림 주문서」
    python3 build_order.py --rom-json <이전 주문서의 D.json> --out <html>
 - 남은 주문: specs.py 종 중 art/<id>-f.png·-b.png 가 없는 것 + 다시 받을 것(NOTES)
 - 받은 그림: art/ 에 앞·뒤가 다 있는 종
 - 다시 그리기: redraw.py 34칸 (지금 롬 그림은 --rom-json 에서, 롬 그림이라 저장소에 안 올림)
첨부 1장은 LCD 원래 칸 ×8 (tools/lcd2sketch.py 가 art/sketch/<id>_lcd_x8.png 로 만듦)."""
import argparse, base64, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(os.path.dirname(HERE)) + '/'
sys.path.insert(0, HERE)
import specs, redraw, prompts

# 종별 지금 상태 (사용자 판정·롬 쪽 세션 평가표, 2026-10-02 기준). need: 받을 것 'f'·'b'
NOTES = {
    'kuwagamon': ('b', '뒷모습 다시 받기 (사용자 판정)'),
    'angewomon': ('f', '앞모습 다시 받기 권장: 날개 8장이 56칸에서 안 보임'),
    'pinochimon': ('fb', '앞: 긴 코가 십자 나무에 가려 안 보임 → 다시. 뒤는 받았지만 채팅 그림만 와서 파일이 없음 → 파일로 다시 올려 주세요'),
    'apocalymon': ('fb', '앞 받음(판정 좋음)이지만 채팅 그림만 와서 파일이 없음 → 파일로 다시 올려 주세요'),
    'tyranomon': ('fb', '앞 받음이지만 파일이 없음 → 파일로 다시 올려 주세요. 손발톱이 뭉개짐'),
    'metalseadramon': ('b', '앞모습 받음 (시드라몬 칸에 잘못 들어가 있던 그림을 옮김) · 뒷모습 필요'),
    'shellmon': ('b', '앞모습 받음 · 뒷모습 필요'),
    'seadramon': ('fb', '앞모습으로 받은 그림이 메탈시드라몬이었음 → 앞부터 다시'),
    'mugendramon': ('b', '앞모습 받음 · 뒷모습 필요'),
}
PRIO = ['kuwagamon', 'seadramon', 'shellmon', 'mugendramon', 'metalseadramon']


def b64(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode() if p and os.path.exists(p) else ''


def art(i, s): return b64(WEB + 'art/%s-%s.png' % (i, s))
def lcdx8(i): return b64(WEB + 'art/sketch/%s_lcd_x8.png' % i)


def card(e, need, note, lcd_url, img, ref):
    if lcd_url: prompts.LCD_OF.add(e['id'])
    e = dict(e); e.setdefault('keep_back', e['keep']); e.setdefault('not_back', [])
    p = {}
    if 'f' in need: p['f'] = prompts.sketch_prompt(e) if lcd_url else prompts.front_prompt(e)
    if 'b' in need: p['b'] = prompts.back_prompt(e)
    p['flat'] = prompts.flat_prompt(e)
    return {'id': e['id'], 'ko': e['ko'], 'en': e['en'], 'grade': e['grade'], 'use': e.get('use', ''), 'need': need, 'note': note,
            'img': img, 'ref': ref, 'lcd': lcd_url, 'lcd8': lcdx8(e['id']) if lcd_url else '',
            'f': art(e['id'], 'f'), 'b': art(e['id'], 'b'), 'prompt': p, 'sketch_mode': bool(lcd_url) and 'f' in need}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--rom-json'); ap.add_argument('--out', required=True); a = ap.parse_args()
    lcd = json.load(open(HERE + '/lcd.json'))
    todo, done = [], []
    for e in specs.S:
        f, b = os.path.exists(WEB + 'art/%s-f.png' % e['id']), os.path.exists(WEB + 'art/%s-b.png' % e['id'])
        need, note = NOTES.get(e['id'], ('' if f and b else ('b' if f else 'fb'), ''))
        if not note and need == 'fb': note = '앞·뒤 모두 필요'
        lu = lcd.get(e.get('wiki'), {}).get('url', '')
        img = 'https://digimon.net/cimages/digimon/%s.jpg' % e['dir']; ref = 'https://digimon.net/reference_ko/detail.php?directory_name=' + e['dir']
        if need: todo.append(dict(card(e, need, note, lu, img, ref), tier=e['tier']))
        else: done.append({'id': e['id'], 'ko': e['ko'], 'f': art(e['id'], 'f'), 'b': art(e['id'], 'b')})
    todo.sort(key=lambda c: (PRIO.index(c['id']) if c['id'] in PRIO else 9, c['tier'] or 9, len(c['need'])))
    rom = {}
    if a.rom_json and os.path.exists(a.rom_json):
        for r in json.load(open(a.rom_json))['rom']: rom[r['no']] = r
    red, red_done = [], []
    ALIAS = {'tailmon': 'gatomon', 'plotmon': 'salamon'}      # art/ 파일 이름이 다른 종
    for e in redraw.R:
        r = rom.get(e['no'], {}); aid = ALIAS.get(e['id'], e['id'])
        if os.path.exists(WEB + 'art/%s-f.png' % aid) and os.path.exists(WEB + 'art/%s-b.png' % aid):
            red_done.append({'id': e['id'], 'ko': e['ko'], 'no': e['no'], 'f': art(aid, 'f'), 'b': art(aid, 'b'), 'romf': r.get('f', ''), 'romb': r.get('b', '')})
            continue
        c = card(dict(e, use='지금 롬 %d번 칸' % e['no']), 'fb', '' if e['lcd'] else 'LCD 도트 없음 → 공식 그림만 붙이는 앞 주문문',
                 e['lcd'], 'https://digimon.net/cimages/digimon/%s.jpg' % e['id'], 'https://digimon.net/reference_ko/detail.php?directory_name=' + e['id'])
        c.update(no=e['no'], romf=r.get('f', ''), romb=r.get('b', ''))
        red.append(c)
    D = {'todo': todo, 'done': done, 'redraw': red, 'redraw_done': red_done}
    tpl = open(HERE + '/order2_tpl.html', encoding='utf-8').read()
    html = tpl.replace('/*DATA*/null', json.dumps(D, ensure_ascii=False))
    assert 'pokemon' not in html.lower() and 'pokémon' not in html.lower()
    open(a.out, 'w', encoding='utf-8').write(html)
    print(a.out, '남은 주문 %d · 받은 그림 %d · 다시 그리기 %d (끝 %d) · %.0fKB' % (len(todo), len(done), len(red), len(red_done), len(html) / 1024))


if __name__ == '__main__':
    main()
