"""디지몬스터 2.0 해부 페이지 만들기 (비공개 아티팩트용 HTML 한 장)
  python3 anat_page.py OUT.html
입력: work/anat/ 의 romanat·romdump·romtext·scriptdis·romgfx 결과 (2.0·1.4·우리 판·원본 금 빌드), series20.json, art_judge.json
원작 내용(이름·대사·그림)이 들어가므로 OUT 은 스크래치/비공개 페이지에만."""
import os, sys, json, re, collections, html
import wild

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, 'work', 'anat')
J = lambda n: json.load(open(os.path.join(A, n)))

D20, D14, DV, DO = J('d20.json'), J('d14.json'), J('dvan.json'), J('dours.json')
G20, G14, GV0, GVF, GO = J('g20.json'), J('g14.json'), J('gv00.json'), J('gvff.json'), J('gours.json')
T20 = J('t20.json'); S20, S14 = J('s20.json'), J('s14.json')
SER = J('series20.json'); ART = J('art_judge.json')
R20, R14 = J('reg20.json'), J('reg14.json'); LF = J('labfile.json')
MAPN = wild.map_names()
ours_names = {s['name'].strip() for s in DO['species']}

TYPE = lambda D: {int(k): v for k, v in D['types']['names'].items()}
T20N, TVN = TYPE(D20), TYPE(DV)
mon20 = {s['no']: s['name'] for s in D20['species']}
mov20 = {m['no']: m['name'] for m in D20['moves']}
item20 = {i['no']: i['name'] for i in D20['items']}
monV = {s['no']: s['name'] for s in DV['species']}
movV = {m['no']: m['name'] for m in DV['moves']}


def gi(G, cat): return {x['key']: x for x in G[cat]}


def vhash(cat):
    a, b = gi(GV0, cat), gi(GVF, cat)
    return {k: (a[k].get('hash') if a[k].get('hash') == b.get(k, {}).get('hash') else None) for k in a}


def evo_txt(e):
    k = e[0]
    if k == 1: how = 'Lv%d' % e[1]
    elif k == 2: how = item20.get(e[1], '도구%d' % e[1])
    elif k == 3: how = '교환' + ('(' + item20.get(e[1], '') + ')' if e[1] not in (0, 255) else '')
    elif k == 4: how = '친밀도' + {1: '', 2: '(낮)', 3: '(밤)'}.get(e[1], '')
    elif k == 5: how = 'Lv%d 능력치%s' % (e[1], {1: '공>방', 2: '공<방', 3: '공=방'}.get(e[2], ''))
    else: how = '종류%d' % k
    return '%s → %s' % (how, mon20.get(e[-1], '?'))


# ── 디지몬 ──
gm20, gm14, gmo = gi(G20, 'mons'), gi(G14, 'mons'), gi(GO, 'mons')
species = []
for s in D20['species']:
    nm = s['name'].strip(); no = s['no']
    s14 = D14['species'][no - 1]
    f, b = gm20.get('%03df' % no, {}), gm20.get('%03db' % no, {})
    same14 = [f.get('hash') == gm14.get('%03df' % no, {}).get('hash'), b.get('hash') == gm14.get('%03db' % no, {}).get('hash')]
    ser = SER.get(nm, {}).get('series', '?')
    species.append(dict(
        no=no, name=nm, ser=ser, ours=nm in ours_names, gold=monV.get(no), n14=s14['name'].strip(),
        types='/'.join(dict.fromkeys(T20N.get(t, str(t)) for t in s['types'])), stats=s['stats'], bst=sum(s['stats']),
        catch=s['catch'], exp=s['exp'], growth=s['growth'],
        evos=[evo_txt(e) for e in s['evos']], learn=' '.join('%d %s' % (lv, mov20.get(m, m)) for lv, m in s['learn']),
        egg=len(s['egg_moves']), dex=D20['dex'][no - 1], f=f.get('png'), b=b.get('png'), same14=same14,
        stat14=s14['stats'] == s['stats'], evo14=s14['evos'] == s['evos'], learn14=s14['learn'] == s['learn']))

# ── 기술 ──
moves = []
for k, m in enumerate(D20['moves']):
    v, o = DV['moves'][k], D14['moves'][k]
    core = lambda x: (x['anim'], x['effect'], x['power'], x['type'], x['acc'], x['pp'], x['chance'])
    moves.append(dict(no=m['no'], name=m['name'], gold=v['name'], type=T20N.get(m['type'], m['type']), power=m['power'],
                      acc=round(m['acc'] * 100 / 255), pp=m['pp'], eff=m['effect_name'].replace('EFFECT_', '').lower(),
                      ch=round(m['chance'] * 100 / 255), desc=m['desc'], anim=m['anim'],
                      nmchg=m['name'] != v['name'], numchg=core(m) != core(v), vs14=core(m) != core(o) or m['name'] != o['name'],
                      effchg=m['effect'] != v['effect'], animchg=m['anim'] != v['anim']))

# ── 타입·도구·트레이너·지명 ──
def mt(D): return {tuple(x) for x in D['types']['matchups'] if isinstance(x, list)}
TN = lambda t: T20N.get(t, t)
EFF = {0: '×0', 5: '×0.5', 10: '×1', 20: '×2'}
mt_add = sorted(mt(D20) - mt(DV)); mt_rem = sorted(mt(DV) - mt(D20))
types = dict(names=[[k, TVN.get(k), T20N.get(k)] for k in sorted(T20N) if not 10 <= k <= 18],
             add=['%s → %s %s' % (TN(a), TN(b), EFF.get(c, c)) for a, b, c in mt_add],
             rem=['%s → %s %s' % (TN(a), TN(b), EFF.get(c, c)) for a, b, c in mt_rem])
items = []
for k, i in enumerate(D20['items']):
    v, o = DV['items'][k], D14['items'][k]
    if i['name'] != v['name'] or i['attr'] != v['attr'] or i['desc'] != v['desc']:
        items.append(dict(no=i['no'], gold=v['name'], n14=o['name'], name=i['name'], price=i['price'], vprice=v['price'], desc=i['desc'],
                          vs14=i['name'] != o['name'] or i['attr'] != o['attr'] or i['desc'] != o['desc']))
tm = [[k + 1, movV.get(a), mov20.get(b), b != a] for k, (a, b) in enumerate(zip(DV['tmhm'], D20['tmhm']))]
classes = [[c['no'], DV['trainers']['classes'][k]['name'], D14['trainers']['classes'][k]['name'], c['name']] for k, c in enumerate(D20['trainers']['classes'])]
parties = []
p14 = {(p['cls'], p['idx']): p for p in D14['trainers']['parties']}
for p in D20['trainers']['parties']:
    o = p14.get((p['cls'], p['idx']))
    parties.append(dict(cls=D20['trainers']['classes'][p['cls'] - 1]['name'], name=p['name'],
                        mons=', '.join('%s %d' % (mon20.get(m['sp'], '?'), m['lv']) for m in p['mons']),
                        chg=o is None or o['mons'] != p['mons'] or o['name'] != p['name']))
landmarks = [[l['no'], DV['landmarks'][k]['name'], D14['landmarks'][k]['name'], l['name']] for k, l in enumerate(D20['landmarks'])]

# ── 야생 ──
wildrows = []
for lab in ('JohtoGrassWildMons', 'KantoGrassWildMons', 'JohtoWaterWildMons', 'KantoWaterWildMons'):
    w14 = {tuple(r['map']): r for r in D14['wild'][lab]}
    for r in D20['wild'][lab]:
        mp = MAPN.get(tuple(r['map']), ('?', '?'))
        def names(sl): return ', '.join(dict.fromkeys('%s' % mon20.get(sp, '?') for lv, sp in sl))
        def lv(sl): return '%d~%d' % (min(x[0] for x in sl), max(x[0] for x in sl))
        o = w14.get(tuple(r['map']))
        if 'slots' in r:
            wildrows.append(dict(kind='물', map=mp[1], lab=mp[0], lv=lv(r['slots']), mons=names(r['slots']), chg=o is None or o['slots'] != r['slots']))
        else:
            wildrows.append(dict(kind='풀', map=mp[1], lab=mp[0], lv=lv(r['morn'] + r['day'] + r['nite']), morn=names(r['morn']), day=names(r['day']), nite=names(r['nite']),
                                 chg=o is None or (o['morn'], o['day'], o['nite']) != (r['morn'], r['day'], r['nite'])))

# ── 이벤트 (맵별 핵심 명령 1.4 → 2.0) ──
P = {'givepoke', 'giveegg', 'loadwildmon', 'trade', 'verbosegiveitem', 'giveitem', 'takeitem', 'checkitem', 'pokemart', 'loadtrainer'}
def keys(m):
    out = collections.Counter()
    for s in m['scripts']:
        for k in s['key']:
            if k.split()[1] in P: out[re.sub(r'^\w+ ', '', k)] += 1
    return out
events = []
for a, b in zip(S14, S20):
    ka, kb = keys(a), keys(b)
    add = [k for k in kb - ka if k.split()[0] in ('givepoke', 'giveegg', 'loadwildmon', 'trade', 'verbosegiveitem', 'takeitem', 'checkitem')]
    rem = [k for k in ka - kb if k.split()[0] in ('givepoke', 'giveegg', 'loadwildmon', 'trade')]
    if add or rem: events.append(dict(map=b['area'], lab=b['label'], add=add, rem=rem))
newtext = [dict(map=(t.get('map') or ['', ''])[1] or (t.get('map') or [''])[0], text=t['text']) for t in T20 if 't14' not in t and '<NULL><NULL>' not in t['text']]
chtext = [dict(scene=(t['refs'][0][3] if t['refs'] else ''), old=t['t14'], new=t['text']) for t in T20 if 't14' in t and t['t14'] != t['text']]

# ── 그림 ──
gfx = []
for cat, nm in (('trainers', '트레이너'), ('sprites', '필드 인물'), ('misc', '제목·기타'), ('tilesets', '타일셋'), ('icons', '메뉴 아이콘')):
    a, o, v, vh = gi(G20, cat), gi(G14, cat), gi(GV0, cat), vhash(cat)
    for k, x in a.items():
        if x.get('hash') != o[k].get('hash') or (vh.get(k) and o[k].get('hash') != vh[k]):
            label = k
            if cat == 'trainers': label = classes[int(k[3:]) - 1][3] + ' (' + (classes[int(k[3:]) - 1][1] or '') + ')'
            gfx.append(dict(cat=nm, key=label, v=v[k].get('png') if vh.get(k) else None, o=o[k].get('png'), n=x.get('png'),
                            s14=x.get('hash') == o[k].get('hash'), sv=vh.get(k) == x.get('hash')))
gstat = {}
for cat in ('mons', 'trainers', 'sprites', 'icons', 'tilesets', 'misc'):
    a, o, vh = gi(G20, cat), gi(G14, cat), vhash(cat)
    gstat[cat] = dict(n=len(a), same14=sum(1 for k in a if a[k].get('hash') == o[k].get('hash')),
                      samev=sum(1 for k in a if vh.get(k) and a[k].get('hash') == vh[k]), unkv=sum(1 for k in a if not vh.get(k)))

# ── 어떻게 만들었나: 바뀐 바이트 분류 ──
def cat_of(lab):
    f = LF.get(lab.split('.')[0], '')
    if not f: return '?'
    if 'pics' in f: return '디지몬 그림'
    if f.startswith('maps'): return '맵 스크립트·대사'
    if f.startswith('data/text'): return '공용 대사'
    if f.startswith('data/pokemon'): return '종 자료(능력치·진화·기술·도감·색)'
    if f.startswith('data/moves'): return '기술 자료'
    if f.startswith('data/items'): return '도구'
    if f.startswith('data/trainers'): return '트레이너'
    if f.startswith('data/wild'): return '야생'
    if f.startswith('data/maps') or f.startswith('data/events'): return '맵·이벤트 표'
    if f.startswith('gfx'): return '그림(그 밖)'
    if f.startswith('engine') or f.startswith('home'): return '엔진 파일 안 글자·그림·색'
    if f.startswith('audio'): return '음악'
    return '그 밖'
def regstat(R):
    c = collections.Counter()
    for x in R['changed']: c[cat_of(x['top'])] += x['n']
    return c
rs20, rs14 = regstat(R20), regstat(R14)
regcats = sorted(set(rs20) | set(rs14), key=lambda k: -rs20.get(k, 0))
regtab = [[k, rs14.get(k, 0), rs20.get(k, 0)] for k in regcats]
engine = collections.OrderedDict()
for x in R20['changed']:
    f = LF.get(x['top'], '')
    if f.startswith('engine') or f.startswith('home'):
        engine.setdefault((x['top'], f), 0); engine[(x['top'], f)] += x['n']
engine = [[k[0], k[1], n] for k, n in engine.items()]
d20 = open(os.path.join(HERE, 'work', 'v20.gbc'), 'rb').read(); d14 = open(os.path.join(HERE, 'work', 'base.gbc'), 'rb').read()
same_bytes = sum(1 for x, y in zip(d20, d14) if x == y); DATA_SAME = round(same_bytes * 100 / len(d20), 1)

# ── 그림 판정·후보 ──
def png(G, no, fb):
    x = gi(G, 'mons').get('%03d%s' % (no, fb)) if no else None
    return x.get('png') if x else None
n14 = {s['name'].strip(): s['no'] for s in D14['species']}
n20 = {s['name'].strip(): s['no'] for s in D20['species']}
alias = {'메탈그레몬': '메탈그레몬'}
judge = []
for j in ART['판정']:
    a, b = n14.get(j['ko']), n20.get(j['ko'])
    judge.append(dict(j, i14=[png(G14, a, 'f'), png(G14, a, 'b')], io=[png(GO, j['no'], 'f'), png(GO, j['no'], 'b')], i20=[png(G20, b, 'f'), png(G20, b, 'b')]))
cands = []
for s in species:
    if s['ser'] in ('어드벤처', '어드벤처 극장판') and not s['ours']:
        an = [t for t in SER.get(s['name'], {}).get('anime', []) if t.startswith('Digimon Adventure') and 'tri' not in t and 'Kizuna' not in t and 'Adventure:' not in t and 'Beginning' not in t and 'Beyond' not in t]
        cands.append(dict(no=s['no'], name=s['name'], ser=s['ser'], f=s['f'], b=s['b'], anime=', '.join(dict.fromkeys(an)), types=s['types'], bst=s['bst']))
sercount = collections.Counter(s['ser'] for s in species)

# ── 포켓몬 흔적 ──
pk = re.findall(r'dname "([^"]+)"', open(os.path.join(wild.KR, 'data/pokemon/names.asm')).read())
trace_words = collections.Counter(); trace_ex = collections.defaultdict(list)
for t in T20:
    s = t['text']
    for w in ('포켓몬', '몬스터볼', '포켓기어'):
        if w in s: trace_words[w] += 1; trace_ex[w].append(s[:60])
traces = dict(names=[[s['no'], s['name']] for s in D20['species'] if s['name'].strip() in pk],
              words=[[w, n, trace_ex[w][:3]] for w, n in trace_words.items()],
              icons=gstat['icons'], trainers_gold=gstat['trainers']['samev'])

rep = sum(1 for x in D20['species'] if x['learn'] and max(collections.Counter(m for lv, m in x['learn']).values()) >= 3)
avg20 = sum(len({m for lv, m in x['learn']}) for x in D20['species']) / 251
avg14 = sum(len({m for lv, m in x['learn']}) for x in D14['species']) / 251
flat = sum(1 for x in D20['species'] if len(set(x['stats'])) == 1)
nmch = sum(1 for m in moves if m['nmchg']); numch = sum(1 for m in moves if m['numchg']); effch = sum(1 for m in moves if m['effchg']); anch = sum(1 for m in moves if m['animchg'])
overview = [
    ['판의 정체', '2.0은 1.4를 바탕으로 크게 고친 판. 2.0과 1.4의 바이트 %s%%가 같음. 원본 금(값을 아는 54%% 구역) 대비 바꾼 바이트: 1.4 %s · 2.0 %s' % (DATA_SAME, format(sum(r[1] for r in regtab), ','), format(sum(r[2] for r in regtab), ','))],
    ['포켓몬 남은 것', '이름은 안농(201) 하나뿐(엔진이 특별 취급하는 칸). 메뉴 아이콘 38종은 전부 원본 포켓몬 아이콘 그대로. 대사 속 「포켓몬」 %d곳·「몬스터볼」 %d곳' % (trace_words.get('포켓몬', 0), trace_words.get('몬스터볼', 0))],
    ['디지몬 250종', '어드벤처 TV %d · 같은 시기 극장판 %d · 테이머즈 %d · 그 뒤 작품 %d · 애니 없음 %d · 분류 못 함 %d · 게임 오리지널 %d. 우리 판 101종 중 69종이 2.0에도 있고, 어드벤처·02 시기인데 우리에게 없는 것 %d종' % (
        sercount['어드벤처'], sercount['어드벤처 극장판'], sercount['테이머즈'], sercount['그 밖'], sercount['애니 없음'], sercount['모름'], sercount.get('게임 오리지널(유대 형태)', 0), len(cands))],
    ['능력치·진화·기술 배우기', '능력치는 1.4 대비 250종 바뀜(그중 %d종은 6개 같은 값: 성장기 55·성숙기 65·완전체 80…). 진화 %d종 바뀜(도구 진화·유대 형태). 배우는 기술은 전부 다시 짬 — %d종이 같은 기술을 3번 이상 반복, 종마다 서로 다른 기술 평균 %.1f개(1.4는 %.1f개)' % (
        flat, sum(1 for x in species if not x['evo14']), rep, avg20, avg14)],
    ['기술 251개', '이름 %d개를 디지몬 필살기로, 위력·타입·명중·PP %d개, 효과 %d개, 연출 %d개 바꿈' % (nmch, numch, effch, anch)],
    ['타입', '이름 2개(비행→바람, 에스퍼→빛), 상성 4곳 (빛→악 ×2 등)'],
    ['도구', '9개를 진화·육성용으로: 진화 카드·오메가블레이드·왕룡검·바이러스·대량 데이터·초월의데이터·파닥인형·X항체·유령퇴치용 부적'],
    ['트레이너', '직업 이름 8개(로켓단→악군단, 디지몬 트레이너→디테이머), 파티 %d/%d 바뀜, 트레이너 그림 3개(라이벌·오박사→겐나이 등)' % (sum(1 for x in parties if x['chg']), len(parties))],
    ['야생', '풀숲·물 표 %d/%d 바뀜' % (sum(1 for w in wildrows if w['chg']), len(wildrows))],
    ['이벤트', '로얄나이츠 숨은 보스 찾기 → 이그드라실, 사성수(주작·청룡·현무·백호) 전설 만남, 선물 디지몬(루체몬·아그니몬·볼프몬·래피드몬 등), 진화 도구 NPC(왕룡검·오메가블레이드), 디지털게이트, 제작자 카메오. 새 대사 %d덩어리, 1.4에서 바뀐 대사 %d' % (len(newtext), len(chtext))],
    ['그림', '디지몬 앞·뒤 500장 중 원본 포켓몬 그림 0장(1.4는 249장 남아 있었음), 1.4에서 바꾼 것 %d장. 필드 인물 %d·트레이너 3·제목 로고·저작권 화면·트레이너 카드 바뀜' % (500 - gstat['mons']['same14'], 95 - gstat['sprites']['same14'])],
    ['음악', '곡 표·맵별 배치는 1.4와 같음. 6곡은 곡 본문 일부 바이트가 다름 — 들리는 차이인지 불확실'],
    ['코드', '새 엔진 기능 없음. 원본 코드 파일 안에서 바뀐 곳은 메뉴 글자(포켓몬→디지몬)·제목 화면·색 표·트레이너 카드 그림·포켓기어 지도 등 데이터뿐 (원본을 모르는 46% 구역은 1.4 대비로만 확인 — 불확실)'],
]
how = [
    '원본 표 자리 그대로 고침: 능력치·기술·진화 포인터·도감·야생·트레이너 파티·도구 속성 표가 원본 금 주소에 그대로 있어 금 심볼 지도로 전부 읽힘.',
    '옮긴 것은 이름표 하나: 기술 이름이 길어져 NamesPointers 6바이트를 고쳐 기술 이름표를 다른 곳으로 옮김.',
    '그림: 원본 그림 자리에 새 압축 그림을 덮어쓰고, 넘치는 것은 그림 포인터 표(1,713바이트 고침)로 다른 뱅크를 가리킴.',
    '이벤트: 기존 스크립트 명령(givepoke·loadwildmon·verbosegiveitem·checkitem·takeitem·setevent 등)만으로 새 사람·대사·전투를 넣음. 새 스크립트·대사는 원본 디스어셈블리가 모르는 뱅크(1.4도 쓰던 구역)에 둠.',
    '새 엔진 코드 없음 → 우리 판처럼 진화 엔진을 늘리거나(유대·암흑 진화) 안전장치를 넣은 판이 아님. 그래서 2.0의 「유대 형태」 진화는 친밀도 진화를, 특수 진화는 도구 진화를 이름만 바꿔 씀.',
    '우리 판으로 가져올 때: 종 자료·기술·그림·도구는 데이터 단위로 바로 옮길 수 있음. 맵 이벤트는 스크립트가 주소에 묶여 있어 우리 판에 맞게 다시 짜야 함(대사·흐름은 참고).',
    '확인 범위: 원본 금 디스어셈블리(pokegold-kr)를 빌드해 얻은 심볼 41,275개 기준, 원본 값을 아는 바이트 54.5%. 나머지 구역은 1.4·2.0끼리만 비교.',
]
DATA_OVERVIEW = dict(overview=overview, how=how)

DATA = dict(species=species, moves=moves, types=types, items=items, tm=tm, classes=classes, parties=parties, landmarks=landmarks,
            wild=wildrows, events=events, newtext=newtext, chtext=chtext, gfx=gfx, gstat=gstat, regtab=regtab, engine=engine,
            judge=judge, judgeinfo=dict(기준=ART['기준'], 요약=ART['요약']), cands=cands, sercount=dict(sercount), traces=traces,
            same_bytes=DATA_SAME, **DATA_OVERVIEW)
print('species %d moves %d items %d parties %d wild %d events %d newtext %d chtext %d gfx %d judge %d cands %d' % (
    len(species), len(moves), len(items), len(parties), len(wildrows), len(events), len(newtext), len(chtext), len(gfx), len(judge), len(cands)))
json.dump(DATA, open(os.path.join(A, 'page_data.json'), 'w'), ensure_ascii=False)

tpl = open(os.path.join(HERE, 'anat_tpl.html'), encoding='utf-8').read()
out = tpl.replace('/*DATA*/null', json.dumps(DATA, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
open(sys.argv[1], 'w', encoding='utf-8').write(out)
print('%s %d KB' % (sys.argv[1], len(out.encode()) // 1024))
