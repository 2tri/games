"""다른 판(2.0 등)의 디지몬 이름 → 애니 시리즈 분류 (series.py 와 같은 방법, 이름이 같으면 series.json 결과 재사용)
  python3 series20.py DUMP.json OUT.json"""
import json, os, sys
import series

HERE = os.path.dirname(os.path.abspath(__file__))
# 롬 이름이 공식 도감 이름과 다른 것 (한국 방영판·줄임 이름 → 위키몬 문서)
MANUAL = {'알포스브몬': 'Ulforce V-dramon', '알포스브이드라몬': 'Ulforce V-dramon', '오메가몬S': 'Omegamon', '오메가몬B': 'Omegamon',
          '오메가몬Z': 'Omegamon Zwart', '오메가몬X': 'Omegamon (X-Antibody)', '오메가몬D': 'Omegamon Zwart Defeat', '메탈그레몬': 'Metal Greymon',
          '로드나이몬': 'Lordknightmon', '황제파이터': 'Imperialdramon: Fighter Mode', '루체몬사탄': 'Lucemon: Satan Mode',
          '루체폴다운': 'Lucemon: Falldown Mode', '켈비몬악': 'Cherubimon (Vice)', '매그너몬X': 'Magnamon (X-Antibody)',
          '간쿠몬X': 'Gankoomon (X-Antibody)', '제스몬X': 'Jesmon (X-Antibody)', '제스몬GX': 'Jesmon GX', '베르제브X': 'Beelzebumon (X-Antibody)',
          '알파몬각성': 'Alphamon: Ouryuken', '알포스퓨처': 'Ulforce V-dramon: Future Mode', '코어드몬녹': 'Coredramon (Green)',
          '코어드몬청': 'Coredramon (Blue)', '크레스가루': 'Crescemon', '블세가고몬': 'Bloomlordmon', '세인가고몬': 'Saint Galgomon',
          '돌그레몬': 'Doruguremon', '그랜쿠가몬': 'Grand Kuwagamon', '그랑쿠가몬': 'Grand Kuwagamon', '데크돌고몬': 'Dexdorugoramon',
          '데크스몬': 'Dexmon', '스트드라몬': 'Strikedramon', '타일런캅몬': 'Tyrant Kabuterimon', '라이즈그몬': 'Rize Greymon',
          '메가로그몬': 'Megalo Growmon', '토리에몬': 'Tortomon', '블리츠그몬': 'Blitz Greymon', '배리얼묘몬': 'Valvemon',
          '미라버스트': 'Mirage Gaogamon: Burst Mode', '샤인버스트': 'Shine Greymon: Burst Mode', '레이버스트': 'Ravemon: Burst Mode',
          '로제버스트': 'Rosemon: Burst Mode', '듀크림존': 'Dukemon: Crimson Mode', '아마게몬': 'Amphimon', '헉몬': 'Hackmon',
          '실즈드라몬': 'Sieg Seadramon', '우정의유대': None, '용기의유대': None}


def main(dump, outp):
    D = json.load(open(dump)); old = json.load(open(os.path.join(HERE, 'series.json')))
    byname = {v['name']: v for v in old.values() if v.get('page')}
    cache = json.load(open(outp)) if os.path.exists(outp) else {}
    for s in D['species']:
        nm = s['name'].strip()
        if not nm or nm in cache: continue
        if nm in byname:
            v = byname[nm]; cache[nm] = dict(page=v['page'], anime=v['anime'], series=series.classify(v['anime']), src='series.json')
        else:
            dn = MANUAL.get(nm, '?')
            if dn is None: cache[nm] = dict(page=None, anime=[], series='게임 오리지널(유대 형태)', src='manual'); continue
            if dn == '?': dn = series.directory(nm)
            page, titles = series.anime_titles(dn) if dn else (None, [])
            cache[nm] = dict(page=page, anime=titles, series=series.classify(titles) if page else '모름', src=dn)
        print(s['no'], nm, cache[nm]['page'], cache[nm]['series'], flush=True)
        json.dump(cache, open(outp, 'w'), ensure_ascii=False, indent=0)
    json.dump(cache, open(outp, 'w'), ensure_ascii=False, indent=0)
    from collections import Counter
    print(Counter(cache[s['name'].strip()]['series'] for s in D['species'] if s['name'].strip() in cache))


if __name__ == '__main__':
    main(*sys.argv[1:3])
