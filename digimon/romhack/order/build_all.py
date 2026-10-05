"""전체 종 주문서 (2026-10-04 사용자 지시: 「총 200몇 종 다 넣고 유년기부터, 게임에서 어떻게 보이는지 앞·뒤로, 그림 필요·검색 필요 표시」)
    python3 build_all.py --out <html> [--allmons allmons.json]
 자료: allmons.json (롬 쪽 세션이 패치 롬에서 뽑음 — 251칸, 게임 그대로 앞·뒤 그림)
       + specs.py·redraw.py 의 종 중 아직 롬 칸이 없는 것(그림이 오면 칸이 생김)
       + art/<id>-f/-b.png (받은 그림) + tools/rip2art.py 의 게임 도트 후보 (art/src/rip 에 시트가 있을 때)
 상태: 완료(앞·뒤 우리 그림이 롬에) / 받음·롬 반영 대기 / 1.4 그림 사용 중(다시 그리기 체크하면 할 일로) / 게임 도트 후보 있음 / 검색·재미나이 필요"""
import argparse, base64, io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROMHACK = os.path.dirname(HERE); WEB = os.path.dirname(ROMHACK) + '/'
sys.path.insert(0, HERE); sys.path.insert(0, WEB + 'tools')
import specs, redraw, prompts, build_order as BO

GRADES = ['유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '성장기', '아머체', '성숙기', '완전체', '궁극체']
NEW_BABY = [('chibimon', '꼬마몬', 'Chibimon', '유년기Ⅱ', '브이몬 줄 · 세 번째 스타팅'), ('minomon', '데롱몬', 'Minomon', '유년기Ⅱ', '추추몬 줄'),
            ('pagumon', '퍼그몬', 'Pagumon', '유년기Ⅱ', '가지몬 줄 · 초반 야생'), ('poromon', '포로몬', 'Poromon', '유년기Ⅱ', '호크몬 줄 · 초반 야생')]
T = lambda w, l, d, b: dict(white=w, light=l, dark=d, black=b)
BABY_SPEC = {   # 새 유년기 4종 주문문용 (specs.py 형식). 몸 색은 redraw.PAL
    'chibimon': dict(id='chibimon', ko='꼬마몬', en='Chibimon (DemiVeemon)', grade='유년기Ⅱ', dir='chibimon', wiki='Chibimon',
                     tones=T('belly, the V mark on the forehead', 'blue body', 'shadow on the ears and back', 'eyes'),
                     keep=['A tiny blue creature with two long floppy ear-like horns pointing backwards.', 'A white belly and a small white muzzle.', 'Short arms and legs, big round eyes, a cheerful smile.'],
                     not_=['Not Veemon: no long legs, no V-shaped horn on the nose.']),
    'minomon': dict(id='minomon', ko='데롱몬', en='Minomon', grade='유년기Ⅱ', dir='minomon', wiki='Minomon',
                    tones=T('eye whites', 'green head', 'the brown leaf bag around the body', 'eyes'),
                    keep=['A small green larva head poking out of a bag made of dried leaves (a bagworm).', 'Two small antennae on top of the head.', 'Big round eyes.'],
                    not_=['No legs, no arms.']),
    'pagumon': dict(id='pagumon', ko='퍼그몬', en='Pagumon', grade='유년기Ⅱ', dir='pagumon', wiki='Pagumon',
                    tones=T('eye whites', 'purple-gray round body', 'the long ears and shadow under the body', 'red eyes'),
                    keep=['A flat round blob with two long floppy ears sticking out sideways.', 'Mischievous narrow eyes and a grin.'],
                    not_=['No legs, no arms, no tail.']),
    'poromon': dict(id='poromon', ko='포로몬', en='Poromon', grade='유년기Ⅱ', dir='poromon', wiki='Poromon',
                    tones=T('eye whites, beak tip', 'pink round body', 'the small wings and the red feather on the head', 'eyes'),
                    keep=['A round pink bird ball with two small wings on the sides.', 'One long red feather on top of the head.', 'A small yellow beak and big round eyes.'],
                    not_=['No legs.']),
}
KEEP14 = {'devimon': '지금 게임 그림(1.4, 날개를 펴서 칸을 꽉 채운 「B형태」)을 그대로 씀 — 사용자 판정 2026-10-05'}
REDO = {}   # 받은 그림이 있어도 다시 받을 것
ALIAS = {'tailmon': 'gatomon', 'plotmon': 'salamon'}
# 게임 도트 후보 — 2026-10-04 사용자 판정으로 7종만 씀(art/ 에 넣음, decisions.md). 나머지는 안 씀
# (rip2art.py LIST 이름, 색 나누기 방식, 판정). 판정 '애매' 는 써도 되는지 사용자 확인 필요. 못 쓴 것(모노크로몬·데블몬·황제드라몬)은 넣지 않음
RIP = {}
NO_SRC = {'gottsumon': '게임 도트 후보 안 씀(사용자 판정)', 'flymon': '게임 도트 후보 안 씀(사용자 판정)', 'drimogemon': '게임 도트 후보 안 씀(사용자 판정)', 'mamemon': '게임 도트 후보 안 씀(사용자 판정)', 'okuwamon': '게임 도트 후보 안 씀(사용자 판정)', 'mammon': '게임 도트 후보 안 씀(사용자 판정)', 'kiwimon': '게임 도트 후보 안 씀(사용자 판정)', 'vegimon': '게임 도트 후보 안 씀(사용자 판정)', 'meramon': '게임 도트 후보 안 씀(사용자 판정)', 'whamon': '게임 도트 후보 안 씀(사용자 판정)', 'digmon': '게임 도트 후보 안 씀(사용자 판정)', 'andromon': '게임 도트 후보 안 씀(사용자 판정)',
          'devimon': '게임 도트를 찾았지만 4색으로 줄이면 뭉개짐',
          'snimon': '원더스완·GBA·NDS 에서 못 찾음', 'hanumon': '원더스완·GBA·NDS 에서 못 찾음'}


TAI = ("Taichi \"Tai\" Yagami, the boy hero of the anime Digimon Adventure (1999): spiky messy brown hair, blue goggles worn on the forehead with a blue strap, "
       "blue short-sleeved shirt with a yellow star, white gloves, brown shorts, brown shoes")
STYLE = ("Style: late-1990s Game Boy Color RPG sprite. VERY low resolution, big chunky pixels, every pixel a crisp square of the same size, thick black outline. "
         "No anti-aliasing, no blur, no gradients, no dithering, no shadow.\n"
         "Exactly 4 tones, GRAYSCALE only: white, light gray, dark gray, black.\n"
         "  - white = goggle lenses, gloves, highlights\n  - light gray = skin\n  - dark gray = hair, shirt, shorts (all clothes and hair)\n  - black = outline, eyes")
PEOPLE_ORDER = [
    dict(id='taichi_back', ko='태일 · 전투 시작 뒷모습', size='48칸', file='taichi_back.png',
         use='전투가 시작될 때 화면 왼쪽 아래에 나오는 주인공 뒷모습 (지금은 금 주인공 그대로)',
         prompt=(f"This is {TAI}. Keep this exact character.\n\nTask: draw him as the PLAYER'S BACK sprite shown at the start of a battle in a Game Boy Color monster RPG.\n\n"
                 "View: from BEHIND and a little ABOVE, upper body only (head, shoulders, back, arms), cut off at the waist by the bottom edge. "
                 "We see the back of his spiky brown hair and the goggle strap around the back of his head. "
                 "His right arm is raised a little to the side holding a small handheld Digivice (a small white device with a screen). "
                 "Turned slightly toward the upper-right, NOT a mirror of a front view, no face visible.\n\n"
                 "Composition: ONE square image, pure white background, the figure fills about 90% of the image. About 48 pixels wide and tall.\n\n" + STYLE +
                 "\n\nNo text, no frame, no grid lines, no background.")),
    dict(id='taichi_front', ko='태일 · 인트로 앞모습', size='56칸 (폭 40칸 이하면 트레이너 카드에도)', file='taichi_front.png',
         use='이름 정하기·겐나이 대화 화면의 주인공 앞모습. 폭이 40칸 이하면 트레이너 카드에도 그대로 씀',
         prompt=(f"This is {TAI}. Keep this exact character: same face, hair, goggles and clothes as the attached picture.\n\n"
                 "Task: redraw the attached picture as a Game Boy Color RPG portrait sprite of the player, like the hero shown in the game's intro.\n\n"
                 "Composition: ONE square image, pure white background. Front view, whole body, standing on the bottom edge, hands on hips. "
                 "About 56 pixels tall and NARROW: the body at most about 40 pixels wide (keep the hair spikes close to the head).\n\n" + STYLE +
                 "\n\nMUST KEEP: 1. The big spiky brown hair. 2. The goggles on the forehead (two round lenses). 3. The star on the shirt.\n"
                 "MUST NOT: no Digimon, no extra people, no text, no frame, no grid lines, no background.")),
]


def b64png(im):
    buf = io.BytesIO(); im.save(buf, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def rip_pic(name, split):
    try:
        import rip2art as R
    except Exception: return ''
    e = next((x for x in R.LIST if x[0] == name), None)
    if not e or not os.path.exists(os.path.join(R.RIP, e[1] + '.png')): return ''
    R.SPLIT = split; t, pal = R.convert(e, R.back_pal(name.split('~')[0]))
    return b64png(R.to_rgba(t, pal))


def spec_of(did, no):
    s = specs.by_id(did) if did else None
    if s: return s
    if did in BABY_SPEC: return BABY_SPEC[did]
    for e in redraw.R:
        if (did and e['id'] == did) or (no and e['no'] == no): return e
    return None


def row(no, ko, grade, did, f, b, src_f, src_b, where, nxt, line, order):
    aid = ALIAS.get(did, did)
    has_f = bool(aid) and os.path.exists(WEB + 'art/%s-f.png' % aid); has_b = bool(aid) and os.path.exists(WEB + 'art/%s-b.png' % aid)
    sp = spec_of(did, no); rd = any(e['no'] == no for e in redraw.R) if no else False
    rip = RIP.get(did)
    side = {}
    for s, has, src in (('f', has_f, src_f), ('b', has_b, src_b)):
        if src == 'art': side[s] = 'done'
        elif has: side[s] = 'got'                                         # 받았는데 롬에 아직 (칸 대기·롬 세션 반영 대기)
        elif src == '1.4' and not rd and not sp: side[s] = 'keep14'
        elif s == 'f' and rip: side[s] = 'rip'
        else: side[s] = 'need'
    if did in REDO:
        for x in REDO[did][0]: side[x] = 'need'
    if did in KEEP14: side = {'f': 'keep14', 'b': 'keep14'}
    st = 'done' if side['f'] == side['b'] == 'done' else ('keep14' if side['f'] == side['b'] == 'keep14' else
          ('got' if {side['f'], side['b']} <= {'done', 'got'} else 'todo'))
    need = ''.join(s for s in 'fb' if side[s] in ('need', 'rip'))
    c = {'no': no, 'ko': ko, 'grade': grade if grade in GRADES else '기타', 'id': did, 'en': (sp or {}).get('en', ''), 'where': where, 'next': nxt, 'line': line, 'order': order,
         'gf': f, 'gb': b, 'src_f': src_f, 'src_b': src_b, 'side': side, 'st': st,
         'af': BO.art(aid, 'f') if has_f and src_f != 'art' else '', 'ab': BO.art(aid, 'b') if has_b and src_b != 'art' else '',
         'rip': rip_pic(rip[0], rip[1]) if rip and side['f'] == 'rip' else '', 'rip_name': rip[0] if rip else '', 'rip_note': rip[2] if rip else '',
         'nosrc': REDO[did][1] if did in REDO else NO_SRC.get(did, ''), 'use': KEEP14.get(did, ''), 'prompt': {}, 'lcd8': '', 'img': '', 'ref': '', 'sketch_mode': False}
    if sp and need:
        lu = sp.get('lcd') or ''
        if not lu:
            try: lu = json.load(open(HERE + '/lcd.json')).get(sp.get('wiki'), {}).get('url', '')
            except Exception: lu = ''
        d = sp.get('dir') or sp['id']
        k = BO.card(sp, need, '', lu, 'https://digimon.net/cimages/digimon/%s.jpg' % d, 'https://digimon.net/reference_ko/detail.php?directory_name=' + d)
        c.update(prompt=k['prompt'], lcd8=k['lcd8'], img=k['img'], ref=k['ref'], sketch_mode=k['sketch_mode'], en=sp.get('en', ''))
    # 뒷모습이 필요하고 앞모습이 확정된 종: 첨부용 앞모습(×8, 흰 바탕) + 앞모습 기준 뒷모습 주문문
    front = WEB + 'art/%s-f.png' % aid if has_f else ''
    if side['b'] in ('need', 'rip') and (front or f):
        from PIL import Image
        if front: im = Image.open(front).convert('RGBA')
        else: im = Image.open(io.BytesIO(base64.b64decode(f.split(',', 1)[1]))).convert('RGBA')
        bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
        c['attf'] = b64png(bg.convert('RGB').resize((im.width * 8, im.height * 8), Image.NEAREST))
        c['prompt']['b'] = prompts.back_from_front(dict(sp or {}, ko=ko, en=c['en'] or (sp or {}).get('en', '')))
        if not c['img'] and did: c['img'] = 'https://digimon.net/cimages/digimon/%s.jpg' % ((sp or {}).get('dir') or did)
    # PixelLab (2026-10-05): 「B형태」 설명 + 참조 그림(256칸 이하, 투명 바탕). 앞모습이 있으면 그 앞모습 ×4, 없으면 공식 그림을 256 안으로
    if need and (sp or did):
        e = dict(sp or {}, ko=ko, en=c['en'] or (sp or {}).get('en', ''))
        d = (sp or {}).get('dir') or did
        c['off256'] = off256(d)                                           # 공식 그림 256×256 (재미나이·PixelLab 첨부용)
        c['g_front'] = prompts.gemini_front(e) if side['f'] in ('need', 'rip') else ''
        c['g_back'] = prompts.gemini_back(e, not front) if side['b'] in ('need', 'rip') else ''
        if grade in PL_GRADES or did in PL_HARD:                          # PixelLab 은 무료 횟수가 적음 → 재미나이가 어려운 것만
            c['pl'] = prompts.pixellab_prompt(e); c['pl_type'] = prompts.body_type(e)
            c['plref'] = pl_ref(front, d)
    return c


PL_GRADES = {'궁극체'}
PL_HARD = {'metalseadramon', 'imperialdramondragonmode', 'qinglongmon', 'mugendramon', 'archnemon', 'whamon'}   # 재미나이가 여러 번 틀린 것


def off256(d):
    pl_ref('', d); return BO.b64(WEB + 'art/ref/%s_256.png' % d)


def pl_ref(front, d):
    from PIL import Image
    import numpy as np
    if front:
        im = Image.open(front).convert('RGBA'); return b64png(im.resize((im.width * 4, im.height * 4), Image.NEAREST))
    cache = WEB + 'art/ref/%s_256.png' % d                                # 공식 그림이라 저장소에 안 올림 (art/ref/.gitignore)
    if not os.path.exists(cache):
        try:
            import urllib.request
            raw = urllib.request.urlopen('https://digimon.net/cimages/digimon/%s.jpg' % d, timeout=20).read()
            a = np.asarray(Image.open(io.BytesIO(raw)).convert('RGB')).astype(int); bg = a.min(2) > 235
            ys, xs = np.where(~bg)
            im = Image.fromarray(np.dstack([a, np.where(bg, 0, 255)]).astype('uint8'), 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
            im.thumbnail((240, 240), Image.LANCZOS); out = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); out.alpha_composite(im, ((256 - im.width) // 2, 248 - im.height))
            out.save(cache)
        except Exception: return ''
    return BO.b64(cache)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--allmons', default=HERE + '/allmons.json'); a = ap.parse_args()
    L = json.load(open(a.allmons)); rows = []; empty = 0; seen = set()
    for x in L:
        if x['src_f'] == 'egg': empty += 1; continue
        seen.add(x['id'])
        rows.append(row(x['no'], x['ko'], x['grade'], x['id'], x.get('f', ''), x.get('b', ''), x['src_f'], x['src_b'], x.get('where', ''),
                        ', '.join(x.get('next') or []), x.get('line', ''), x.get('order', 999)))
    extra = [(i, ko, en, g, use) for i, ko, en, g, use in NEW_BABY] + [(e['id'], e['ko'], e['en'], e['grade'], e.get('use', '')) for e in specs.S if e['id'] not in seen]
    for i, ko, en, g, use in extra:
        if i in seen: continue
        seen.add(i); r = row(0, ko, g, i, '', '', 'none', 'none', '', '', '', 900); r['en'] = r['en'] or en; r['use'] = '아직 롬 칸 없음 — 앞·뒤 그림이 다 오면 칸이 생김' + (' · ' + use if use else '')
        rows.append(r)
    gi = lambda g: GRADES.index(g) if g in GRADES else len(GRADES)
    rows.sort(key=lambda r: (gi(r['grade']), r['order'], r['no']))
    people = [{'ko': '겐나이', 'done': True, 'portrait': BO.b64(WEB + 'art/gennai_portrait.png'), 'walk': BO.b64(WEB + 'art/gennai_ow.png')}]
    from PIL import Image
    ref = Image.open(WEB + 'art/src/people/taichi_portrait_ai.png').convert('RGB'); ref.thumbnail((256, 256))
    for e in PEOPLE_ORDER:
        got = BO.b64(WEB + 'art/' + e['file'])
        people.append(dict(e, done=bool(got), got=got, ref=b64png(ref) if e['id'] == 'taichi_front' and not got else ''))
    D = {'primer': prompts.GEMINI_PRIMER, 'rows': rows, 'grades': GRADES + ['기타'], 'empty': empty, 'people': people}
    tpl = open(HERE + '/allorder_tpl.html', encoding='utf-8').read()
    html = tpl.replace('/*DATA*/null', json.dumps(D, ensure_ascii=False))
    assert 'pokemon' not in html.lower() and 'pokémon' not in html.lower()
    open(a.out, 'w', encoding='utf-8').write(html)
    from collections import Counter
    print(a.out, '%d종 + 빈 칸 %d' % (len(rows), empty), dict(Counter(r['st'] for r in rows)), '%.0fKB' % (len(html) / 1024))


if __name__ == '__main__':
    main()
