#!/usr/bin/env python3
"""위키몬(wikimon.net)에서 DS 「디지몬 스토리」 전투 앞모습·맵 그림 받기 (2026-10-12). 개인용.
사용:   python wikimon_get.py "<그림 폴더>"      ← 주말에 받은 제미나이 그림과 같은 폴더(art_nds.py 가 읽는 곳)
결과:   <id>-wk-f.png(전투 앞모습) · <id>-wk-atk.png(공격 자세 — 뒤집어서 뒷모습 자리에, 사용자 10/12 「역동적인 자세로」) · <id>-wk-map.png(맵 정면) · wikimon_결과.txt
- 디지골드에 없는 새 종(NDS_종_초안.tsv 의 출처 「새로」)만. 이미 파일이 있으면 건너뜀.
- art_nds.py 는 앞모습을 <id>-ds-f.png(제미나이) → <id>-wk-f.png(위키몬) → <id>-f.png(GBC) 순서로 쓴다. 뒷모습은 위키몬에 없으니 제미나이로.
- 못 찾은 종은 결과 파일에 「못 찾음」. 10/12 확인: DS 게임에 없어 위키몬에도 없는 종 10 = 에렉몬·메라몬·츄몬·펌프몬·가지몬·다크퍼펫몬·데드메라몬·고래몬·스컬사탄몬·고릴라몬 → 제미나이로 앞·뒤 다 받음."""
import os, sys, re, csv, json, time, urllib.request, urllib.parse
try: sys.stdout.reconfigure(errors='replace')
except Exception: pass

H = os.path.dirname(os.path.abspath(__file__))
# 위키몬 제목이 우리 영어 이름과 다른 것(일본식 로마자). 왼쪽 = design.json 의 en
TITLE = {'Arachnemon': 'Archnemon', 'MetalTyrannomon': 'MetalTyranomon', 'Pinochimon': 'Pinocchimon', 'Tonosama Gekomon': 'TonosamaGekomon', 'Flare Lizarmon': 'FlareLizamon', 'Death Meramon': 'DeathMeramon',
         'Metal Etemon': 'MetalEtemon', 'Red Vegimon': 'RedVegimon', 'Mega Seadramon': 'MegaSeadramon', 'Dark Tyranomon': 'DarkTyranomon',
         'Waru Monzaemon': 'WaruMonzaemon', 'Saber Leomon': 'SaberLeomon', 'Metal Mamemon': 'MetalMamemon', 'Skull Satamon': 'SkullSatamon',
         'Marin Devimon': 'MarinDevimon', 'Belial Vamdemon': 'BelialVamdemon', 'Imperialdramon: Paladin Mode': 'Imperialdramon_Paladin_Mode',
         'Chimairamon': 'Chimairamon', 'Mushamon': 'Musyamon', 'Gorimon': 'Gorillamon', 'Tortamon': 'Tortomon', 'Holydramon': 'Holydramon',
         'HerculesKabuterimon': 'HerakleKabuterimon', 'Centalmon': 'Centalmon', 'Tyumon': 'Chuumon', 'Hangyomon': 'Hangyomon',
         'Anomalocarimon': 'Anomalocarimon', 'Delumon': 'Deramon', 'Gerbemon': 'Garbagemon', 'Mushmon': 'Mushroomon', 'Octmon': 'Octomon',
         'Evilmon': 'Evilmon', 'Ganimon': 'Ganimon', 'Gizamon': 'Gizamon', 'Coelamon': 'Coelamon', 'Apemon': 'Apemon'}
EN_X = {'블랙워가루몬': 'BlackWereGarurumon', '에이프몬': 'Hanumon', '돌핀몬': 'Rukamon', '백호몬': 'Baihumon', '주작몬': 'Zhuqiaomon', '현무몬': 'Xuanwumon', '크리사리몬': 'Chrysalimon',
        '호우오몬': 'Hououmon', '헤라캅테몬': 'HerculesKabuterimon', '바이킹몬': 'Vikemon', '하이안드몬': 'HiAndromon', '메탈티라몬': 'MetalTyrannomon',
        '그란쿠와몬': 'GranKuwagamon', '리리스몬': 'Lilithmon', '발키리몬': 'Valkyrimon', '데비타마몬': 'Devitamamon', '데드메라몬': 'Death Meramon'}
UA = {'User-Agent': 'Mozilla/5.0 (personal fan project; one-time fetch)'}

def fid(en): return re.sub(r'[^a-z0-9]+', '-', en.lower()).strip('-')

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r: return r.read()

ATTR_KO = {'Vaccine': '백신', 'Data': '데이터', 'Virus': '바이러스', 'Free': '프리', 'Variable': '배리어블', 'Unknown': '언노운', 'No Data': '노데이터'}

def attrs():
    """우리 종 전부(디지골드 종 포함)의 속성을 위키몬 문서에서 읽어 wikimon_속성.tsv(스크립트 폴더)로 — hg2 가 도감 분류에 붙임(10/14)"""
    d = json.load(open(os.path.join(H, 'design.json'), encoding='utf-8')); EN = {s_['ko']: s_['en'] for s_ in d['species']}; EN.update(EN_X)
    dp = next(p_ for p_ in (os.path.join(H, 'NDS_종_초안.tsv'), os.path.join(H, '..', 'NDS_종_초안.tsv')) if os.path.exists(p_))
    draft = list(csv.DictReader(open(dp, encoding='utf-8'), delimiter='\t'))
    outp = os.path.join(H, 'wikimon_속성.tsv'); have = {}
    if os.path.exists(outp):
        for r in csv.DictReader(open(outp, encoding='utf-8'), delimiter='\t'): have[r['이름']] = r
    rows = []; miss = []
    for r in draft:
        ko = r['이름']
        if ko == '디지문자': continue
        if ko in have and have[ko].get('속성'): rows.append(have[ko]); continue
        en = EN.get(ko) or ''
        if not en: miss.append(ko + '(영어 이름 없음)'); continue
        titles = [TITLE.get(en, ''), en.replace(' ', ''), en.replace(' ', '_'), en.replace(':', '').replace(' ', '_')]
        titles = [t for k, t in enumerate(titles) if t and t not in titles[:k]]
        got = None
        for t in titles:
            try: html = get('https://wikimon.net/' + urllib.parse.quote(t)).decode('utf-8', 'ignore')
            except Exception: continue
            i = html.find('title="Attribute"')
            if i < 0: i = html.find('>Attribute<')
            if i < 0: continue
            m = re.search(r'>(Vaccine|Data|Virus|Free|Variable|Unknown|No Data)<', html[i:i + 1500])
            if m: got = (t, m.group(1)); break
            time.sleep(0.3)
        if not got: miss.append('%s(%s)' % (ko, en)); continue
        rows.append({'이름': ko, '속성': ATTR_KO[got[1]], '영어': got[1], '문서': got[0]})
        time.sleep(0.4)
    open(outp, 'w', encoding='utf-8', newline='\n').write('이름\t속성\t영어\t문서\n' + '\n'.join('%s\t%s\t%s\t%s' % (x['이름'], x['속성'], x.get('영어', ''), x.get('문서', '')) for x in rows) + '\n')
    print('속성 %d종, 못 찾음 %d: %s' % (len(rows), len(miss), ', '.join(miss[:40])))
    print('→ wikimon_속성.tsv')

def main():
    if '--attr' in sys.argv: return attrs()
    out = sys.argv[1] if len(sys.argv) > 1 else 'nds_in'

    os.makedirs(out, exist_ok=True)
    d = json.load(open(os.path.join(H, 'design.json'), encoding='utf-8')); EN = {s['ko']: s['en'] for s in d['species']}; EN.update(EN_X)
    dp = next(p for p in (os.path.join(H, 'NDS_종_초안.tsv'), os.path.join(H, '..', 'NDS_종_초안.tsv')) if os.path.exists(p))
    draft = list(csv.DictReader(open(dp, encoding='utf-8'), delimiter='\t'))
    todo = [r['이름'] for r in draft if r['출처'] == '새로' and r['이름'] != '디지문자']
    if len(sys.argv) > 2: todo = todo[:int(sys.argv[2])]        # 시험용: 앞 n종만
    log = []; ok = miss = skip = 0
    for ko in todo:
        en = EN.get(ko) or ''
        if not en: log.append('%s: 영어 이름 없음' % ko); miss += 1; continue
        i = fid(en); fp, mp, ap = os.path.join(out, i + '-wk-f.png'), os.path.join(out, i + '-wk-map.png'), os.path.join(out, i + '-wk-atk.png')
        if os.path.exists(fp): skip += 1; continue
        titles = [TITLE.get(en, ''), en.replace(' ', ''), en.replace(' ', '_'), en.replace(':', '').replace(' ', '_')]
        titles = [t for k, t in enumerate(titles) if t and t not in titles[:k]]
        found = None
        for t in titles:
            try: html = get('https://wikimon.net/' + urllib.parse.quote(t)).decode('utf-8', 'ignore')
            except Exception: continue
            m = {}
            # 파일 이름이 들쭉날쭉: Name_dst_battle / Name_battle_dst / Name_battle_dssm / Name_dst_battle_hit(기본 자세가 없을 때는 맞음·공격 자세라도)
            for kind in ('battle', 'map', 'attack'):
                pats = []
                for tag in ('dst', 'dssm', 'dsle'):
                    if kind == 'attack': pats += [r'_%s_battle_attack\.png' % tag, r'_battle_attack_%s\.png' % tag]; continue
                    pats += [r'_%s_%s\.png' % (tag, kind), r'_%s_%s\.png' % (kind, tag)]
                if kind == 'battle':
                    for tag in ('dst', 'dssm', 'dsle'): pats += [r'_%s_battle_hit\.png' % tag, r'_%s_battle_attack\.png' % tag, r'_battle_hit_%s\.png' % tag, r'_battle_attack_%s\.png' % tag]
                for pat in pats:
                    mm = re.search(r'(/images/[0-9a-f]/[0-9a-f]{2}/[^"\' ]+%s)' % pat, html)
                    if mm: m[kind] = mm.group(1); break
            if 'battle' in m: found = (t, m); break
            time.sleep(0.3)
        if not found: log.append('%s (%s): 못 찾음 — 시도한 제목 %s' % (ko, en, titles)); miss += 1; continue
        t, m = found
        try:
            open(fp, 'wb').write(get('https://wikimon.net' + m['battle']))
            if 'map' in m: open(mp, 'wb').write(get('https://wikimon.net' + m['map']))
            if 'attack' in m: open(ap, 'wb').write(get('https://wikimon.net' + m['attack']))
            log.append('%s: OK (%s%s%s)' % (ko, t, ', 맵' if 'map' in m else '', ', 공격 자세' if 'attack' in m else '')); ok += 1
        except Exception as e: log.append('%s: 받기 실패 %s' % (ko, e)); miss += 1
        time.sleep(0.5)
    head = '받음 %d, 이미 있음 %d, 못 찾음·실패 %d / 전체 %d' % (ok, skip, miss, len(todo))
    open(os.path.join(out, 'wikimon_결과.txt'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(log) + '\n')
    print(head); print('못 찾은 것:'); [print(' ', l) for l in log if 'OK' not in l]
    print('→ %s/wikimon_결과.txt 를 설계자에게' % out)

if __name__ == '__main__':
    main()
