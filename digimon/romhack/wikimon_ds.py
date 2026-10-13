"""위키몬(wikimon.net)에서 DS 「디지몬 스토리」 전투 그림 받기 — 저장소용 (16판, 개인용 한 번).
python3 wikimon_ds.py [n]
결과: ../../images/digimon/<id>-ds-f.png(전투 앞모습), <id>-ds-b.png(공격 자세를 좌우 뒤집어 뒷모습 자리에), work/wikimon_결과.txt.
이미 받은 종은 건너뜀. 종 목록·영어 이름은 아래 EN 에 내장(설계자 PC 에서 만든 표). SKIP 은 위키몬에 DS 그림이 없는 것으로 확인된 종."""
import os, sys, re, json, time, urllib.request, urllib.parse
from io import BytesIO
import dmrom

HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.dirname(HERE); OUT = os.path.join(os.path.dirname(WEB), 'images', 'digimon')      # 저장소 루트 images/digimon (WEB 은 digimon/)
EN = {"팔몬": "Palmon", "니드몬": "Togemon", "릴리몬": "Lilimon", "아구몬": "Agumon", "그레이몬": "Greymon", "워그레이몬": "War Greymon", "파피몬": "Gabumon", "가루몬": "Garurumon", "메탈가루몬": "Metal Garurumon", "쿠네몬": "Kunemon", "플라이몬": "Flymon", "오쿠와몬": "Okuwamon", "스나이몬": "Snimon", "아르케니몬": "Arachnemon", "피요몬": "Piyomon", "버드라몬": "Birdramon", "가루다몬": "Garudamon", "뿔몬": "Tunomon", "할세몬": "Holsmon", "호크몬": "Hawkmon", "실피드몬": "Silphymon", "수리몬": "Shurimon", "잠수몬": "Submarimon", "콩알몬": "Mamemon", "페가수스몬": "Pegasmon", "두리몬": "Armadimon", "디그몬": "Digmon", "네페르몬": "Nefertimon", "미이라몬": "Mummymon", "키메라몬": "Chimairamon", "메탈티라몬": "MetalTyrannomon", "그란쿠와몬": "GranKuwagamon", "리리스몬": "Lilithmon", "가트몬": "Tailmon", "발키리몬": "Valkyrimon", "트리케라몬": "Triceramon", "골레몬": "Golemon", "홀리엔젤몬": "Holy Angemon", "마그나드몬": "Holydramon", "피코데블몬": "Pico Devimon", "피에몬": "Piemon", "텐타몬": "Tentomon", "캅테리몬": "Kabuterimon", "아트캅테몬": "AtlurKabuterimon", "시드몬": "Tanemon", "티라노몬": "Tyranomon", "도쿠구몬": "Dokugumon", "데비타마몬": "Devitamamon", "아르마몬": "Armadimon", "위자몬": "Wizarmon", "스타몬": "Starmon", "기자몬": "Gizamon", "에테몬": "Etemon", "메탈에테몬": "Metal Etemon", "다크리자몬": "Flare Lizarmon", "토르토몬": "Tortamon", "에렉몬": "Elecmon", "레오몬": "Leomon", "샤벨레오몬": "Saber Leomon", "고릴라몬": "Gorimon", "옥토몬": "Octmon", "하누몬": "Hanumon", "미노타루몬": "Minotaurmon", "레볼몬": "Revolmon", "썬더볼몬": "Thunderballmon", "추추몬": "Wormmon", "스팅몬": "Stingmon", "플로라몬": "Floramon", "게소몬": "Gesomon", "다이버몬": "Hangyomon", "울퉁몬": "Gottsumon", "황금아르마": "Magnamon", "샤코몬": "Shakkoumon", "유니몬": "Unimon", "오타마몬": "Otamamon", "메카노리몬": "Mechanorimon", "탱크몬": "Tankmon", "꼬끼몬": "Cockatrimon", "키위몬": "Kiwimon", "데라몬": "Delumon", "워매몬": "Numemon", "슈카몬": "Scumon", "쉘몬": "Shellmon", "고스몬": "Bakemon", "데블몬": "Devimon", "베놈묘티몬": "Venom Vamdemon", "모노크로몬": "Monochromon", "베이더몬": "Vademon", "스콜피오몬": "Anomalocarimon", "가니몬": "Ganimon", "톱니몬": "Hagurumon", "가드로몬": "Guardromon", "디지타마몬": "Digitamamon", "다고몬": "Dagomon", "나이트몬": "Knightmon", "우가몬": "Orgemon", "나니몬": "Nanimon", "블랙워그몬": "BlackWarGreymon", "다크그레몬": "Metal Greymon (Virus)", "에이프몬": "Hanumon", "맘몬": "Mammon", "블로섬몬": "Blossomon", "베지몬": "Vegimon", "쉬라몬": "Gomamon", "원뿔몬": "Ikkakumon", "둥실몬": "Pukamon", "시드라몬": "Seadramon", "호우오몬": "Hououmon", "헤라캅테몬": "HerculesKabuterimon", "메라몬": "Meramon", "켄터스몬": "Centalmon", "베타몬": "Betamon", "메가시라몬": "Mega Seadramon", "돌핀몬": "Rukamon", "케라몬": "Keramon", "브이몬": "V-mon", "매그너몬": "Magnamon", "번개드라몬": "Lighdramon", "화염드라몬": "Fladramon", "데이터몬": "Nanomon", "실러캔몬": "Coelamon", "스컬그레몬": "SkullGreymon", "안드로몬": "Andromon", "에어드라몬": "Airdramon", "퍼펫몬": "Monzaemon", "오메가몬": "Omegamon", "무사몬": "Mushamon", "메가드라몬": "Megadramon", "기가드라몬": "Gigadramon", "푸루루몬": "Pururumon", "츠부몬": "Tsubumon", "코로몬": "Koromon", "츄몬": "Tyumon", "토코몬": "Tokomon", "파롯트몬": "Parrotmon", "데블드라몬": "Devidramon", "꼬마몬": "Chibimon", "인펠몬": "Infermon", "디아블로몬": "Diablomon", "묘티스몬": "Vamdemon", "피노키몬": "Pinochimon", "아포카리몬": "Apocalymon", "번개콩알몬": "Metal Mamemon", "플롯트몬": "Plotmon", "엔젤몬": "Angemon", "파닥몬": "Patamon", "세라피몬": "Seraphimon", "아쿠이라몬": "Aquilamon", "파일드라몬": "Paildramon", "모티몬": "Mochimon", "포로몬": "Poromon", "퍼그몬": "Pagumon", "로제몬": "Rosemon", "데롱몬": "Numemon", "메탈시드몬": "MetalSeadramon", "쿠가몬": "Kuwagamon", "개굴몬": "Gekomon", "어니몬": "Pyocomon", "파워드라몬": "Mugendramon", "머슈룸몬": "Mushmon", "쥬레이몬": "Jyureimon", "우드몬": "Woodmon", "바이킹몬": "Vikemon", "엑스브이몬": "XV-mon", "황제드라몬": "Imperialdramon: Dragon Mode", "황제파이터": "Imperialdramon: Fighter Mode", "황제팔라딘": "Imperialdramon: Paladin Mode", "왕개굴몬": "Tonosama Gekomon", "팬텀몬": "Fantomon", "쿠라몬": "Kuramon", "펌프몬": "Pumpmon", "츠메몬": "Tsumemon", "크리사리몬": "Chrysalimon", "가지몬": "Gazimon", "이비르몬": "Evilmon", "메탈그레몬": "MetalGreymon", "지로몬": "Giromon", "다크퍼펫몬": "Waru Monzaemon", "워가루몬": "Were Garurumon", "데드메라몬": "Death Meramon", "프리지몬": "Yukidarumon", "모야몬": "Mojyamon", "유키보타몬": "Yukimi Botamon", "레어몬": "Raremon", "가베지몬": "Gerbemon", "레이디데블": "LadyDevimon", "쥬드몬": "Zudomon", "다크티라몬": "Dark Tyranomon", "파브몬": "Bubbmon", "유라몬": "Yuramon", "피치몬": "Pitchmon", "포요몬": "Poyomon", "깜몬": "Botamon", "푸니몬": "Punimon", "야옹몬": "Nyaromon", "뇨키몬": "Nyokimon", "엔젤우몬": "Angewomon", "백호몬": "Baihumon", "주작몬": "Zhuqiaomon", "현무몬": "Xuanwumon", "우파몬": "Upamon", "리프몬": "Leafmon", "피콜로몬": "Piccolomon", "고래몬": "Whamon", "청룡몬": "Qinglongmon"}
SKIP = ["할세몬", "잠수몬", "페가수스몬", "디그몬", "네페르몬", "아트캅테몬", "에렉몬", "고릴라몬", "다크그레몬", "둥실몬", "메라몬", "번개드라몬", "푸루루몬", "츠부몬", "츄몬", "꼬마몬", "모티몬", "포로몬", "어니몬", "정우베지몬:", "펌프몬", "가지몬", "다크퍼펫몬", "데드메라몬", "유키보타몬", "파브몬", "유라몬", "피치몬", "푸니몬", "야옹몬", "뇨키몬", "우파몬", "리프몬", "고래몬"]
TITLE = {'Arachnemon': 'Archnemon', 'MetalTyrannomon': 'MetalTyranomon', 'Pinochimon': 'Pinocchimon', 'Tonosama Gekomon': 'TonosamaGekomon', 'Flare Lizarmon': 'FlareLizamon', 'Death Meramon': 'DeathMeramon', 'Metal Etemon': 'MetalEtemon', 'Red Vegimon': 'RedVegimon', 'Mega Seadramon': 'MegaSeadramon', 'Dark Tyranomon': 'DarkTyranomon', 'Waru Monzaemon': 'WaruMonzaemon', 'Saber Leomon': 'SaberLeomon', 'Metal Mamemon': 'MetalMamemon', 'Skull Satamon': 'SkullSatamon', 'Marin Devimon': 'MarinDevimon', 'Belial Vamdemon': 'BelialVamdemon', 'Imperialdramon: Paladin Mode': 'Imperialdramon_Paladin_Mode', 'Chimairamon': 'Chimairamon', 'Mushamon': 'Musyamon', 'Gorimon': 'Gorillamon', 'Tortamon': 'Tortomon', 'Holydramon': 'Holydramon', 'HerculesKabuterimon': 'HerakleKabuterimon', 'Centalmon': 'Centalmon', 'Tyumon': 'Chuumon', 'Hangyomon': 'Hangyomon', 'Anomalocarimon': 'Anomalocarimon', 'Delumon': 'Deramon', 'Gerbemon': 'Garbagemon', 'Mushmon': 'Mushroomon', 'Octmon': 'Octomon', 'Evilmon': 'Evilmon', 'Ganimon': 'Ganimon', 'Gizamon': 'Gizamon', 'Coelamon': 'Coelamon', 'Apemon': 'Apemon', 'Imperialdramon': 'Imperialdramon_Dragon_Mode', 'Imperialdramon: Fighter Mode': 'Imperialdramon_Fighter_Mode', 'Imperialdramon Fighter Mode': 'Imperialdramon_Fighter_Mode', 'Imperialdramon Dragon Mode': 'Imperialdramon_Dragon_Mode', 'Magnamon': 'Magnamon', 'Ultimate Chaosmon': 'Ultimate_Chaosmon'}
# 19판: EN 표의 영어 이름이 프로젝트 id(slots·allmons)와 다른 종 — id 쪽이 맞아서 그 제목만 씀 (두리몬=Drimogemon 이지 Armadimon 아님 등)
FIX_TITLE = {'두리몬': 'Drimogemon', '황금아르마': 'Ankylomon', '플롯트몬': 'Salamon', '데롱몬': 'Minomon', '스콜피오몬': 'Scorpiomon', '다크리자몬': 'DarkLizamon', '다이버몬': 'Divermon'}
UA = {'User-Agent': 'Mozilla/5.0 (personal fan project; one-time fetch)'}


def fid(en): return re.sub(r'[^a-z0-9]+', '', en.lower().replace('-', ''))


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    os.makedirs(OUT, exist_ok=True)
    ID = {}
    for p in (os.path.join(HERE, 'slots.json'), os.path.join(HERE, 'order', 'allmons.json')):
        try:
            j = json.load(open(p, encoding='utf-8'))
            lst = j['mons'] if isinstance(j, dict) else j
            for m in lst:
                nm = m.get('name') or m.get('ko')
                if nm and m.get('id'): ID.setdefault(nm, m['id'])
        except Exception as ex:
            print('id 표 못 읽음', p, ex)
    r = dmrom.Rom(os.path.join(dmrom.WORK, 'myver.gbc'))      # 고친 롬의 이름(새 종 포함)
    todo = [r.name(n) for n in range(1, dmrom.NUM + 1) if r.name(n) in EN and r.name(n) not in SKIP]
    if len(sys.argv) > 1: todo = todo[:int(sys.argv[1])]
    log = []
    ok = miss = skip = 0
    for ko in todo:
        en = EN.get(ko) or ''
        if not en:
            log.append('%s: 영어 이름 없음' % ko)
            miss += 1
            continue
        i = ID.get(ko) or fid(en)
        fp, bp = os.path.join(OUT, i + '-ds-f.png'), os.path.join(OUT, i + '-ds-b.png')
        if os.path.exists(fp):
            skip += 1
            continue
        titles = [FIX_TITLE.get(ko, '')] + ([] if ko in FIX_TITLE else [TITLE.get(en, ''), en.replace(' ', ''), en.replace(' ', '_'), en.replace(':', '').replace(' ', '')])      # 19판: FIX_TITLE 종은 그 제목만
        titles = [t for k, t in enumerate(titles) if t and t not in titles[:k]]
        found = None
        for t in titles:
            try:
                html = get('https://wikimon.net/' + urllib.parse.quote(t)).decode('utf-8', 'ignore')
            except Exception:
                continue
            m = {}
            for kind in ('battle', 'attack'):
                pats = []
                for tag in ('dst', 'dssm', 'dsle', 'ds[a-z]'):      # 2차: 어느 DS 게임 태그든
                    if kind == 'attack':
                        pats += [r'%s_battle_attack.png' % tag, r'battle_attack%s.png' % tag]
                        continue
                    pats += [r'%s_battle.png' % tag, r'battle%s.png' % tag]
                if kind == 'battle':
                    for tag in ('dst', 'dssm', 'dsle', 'ds[a-z]'):
                        pats += [r'%s_battle_hit.png' % tag, r'%s_battle_attack.png' % tag, r'battle_hit%s.png' % tag, r'battle_attack%s.png' % tag]
                for pat in pats:
                    mm = re.search(r'(/images/[0-9a-f]/[0-9a-f]{2}/%s[^"\' ]*%s)' % (re.escape(t), pat), html, re.I)      # 18판: 파일 이름이 제목으로 시작해야 함 (안킬로몬에 다른 그림이 받아짐)
                    if mm:
                        m[kind] = mm.group(1)
                        break
            if 'battle' in m:
                found = (t, m)
                break
            time.sleep(0.3)
        if not found:
            log.append('%s (%s): 못 찾음 — 시도한 제목 %s' % (ko, en, titles))
            miss += 1
            continue
        t, m = found
        try:
            open(fp, 'wb').write(get('https://wikimon.net' + m['battle']))
            if 'attack' in m:
                raw = get('https://wikimon.net' + m['attack'])
                try:
                    from PIL import Image, ImageOps
                    ImageOps.mirror(Image.open(BytesIO(raw)).convert('RGBA')).save(bp)      # 공격 자세 좌우 뒤집기 → 뒷모습 자리
                except Exception:
                    open(bp, 'wb').write(raw)
            log.append('%s: OK (%s%s) → %s' % (ko, t, ', 공격 자세→뒤' if 'attack' in m else '', i))
            ok += 1
        except Exception as e:
            log.append('%s: 받기 실패 %s' % (ko, e))
            miss += 1
        time.sleep(0.5)
    head = '받음 %d, 이미 있음 %d, 못 찾음·실패 %d / 전체 %d' % (ok, skip, miss, len(todo))
    open(os.path.join(dmrom.WORK, 'wikimon_결과.txt'), 'w', encoding='utf-8').write(head + '\n' + '\n'.join(log) + '\n')
    print(head)
    print('못 찾은 것:')
    for l in log:
        if 'OK' not in l: print(' ', l)


if __name__ == '__main__':
    main()
