"""디지골드 대조표·받을목록 표 만들기 (기준: 제작자 엑셀 「포켓몬 정보 및 기타 변경사항」 메인 시트 411~475행, 디지몬 65종)."""
import json, re, os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
d = json.load(open(os.path.join(H, 'design.json'), encoding='utf-8')); S = {s['ko']: s for s in d['species']}
# 사용자 10/8: 유아기는 게임에서 뺀다(알에서도 유년기로 나옴). 흐름 = 유년기 → 성장기 → 성숙기 → 완전체 → 궁극체
DROP = [s['ko'] for s in d['species'] if s['grade'] == '유아기Ⅰ' or (s['grade'].startswith('유년기') and s['ko'] != '토코몬')]   # 10/12: 유년기도 뺌(토코몬만)
ORDER = [s['ko'] for s in d['species'] if s['ko'] != '디지문자' and s['ko'] not in DROP]
# 엑셀 순서 그대로: (디지골드 이름, 내 설계 이름)
EXCEL = [('아구몬', '아구몬'), ('그레이몬', '그레이몬'), ('메탈그레이몬', '메탈그레이몬'), ('워그레이몬', '워그레이몬'), ('메탈그레이몬(B)', '다크그레몬'),
         ('스컬그레이몬', '스컬그레이몬'), ('파피몬', '파피몬'), ('가루몬', '가루몬'), ('워가루몬', '워가루몬'), ('메탈가루몬', '메탈가루몬'),
         ('텐타몬', '텐타몬'), ('캅테리몬', '캅테리몬'), ('아트라캅테리몬', '아트라캅테리몬'), ('피요몬', '피요몬'), ('버드라몬', '버드라몬'),
         ('가루다몬', '가루다몬'), ('팔몬', '팔몬'), ('니드몬', '니드몬'), ('릴리몬', '릴리몬'), ('쉬라몬', '쉬라몬'), ('원뿔몬', '원뿔몬'),
         ('쥬드몬', '쥬드몬'), ('포요몬', '포요몬'), ('토코몬', '토코몬'), ('파닥몬', '파닥몬'), ('엔젤몬', '엔젤몬'), ('홀리엔젤몬', '홀리엔젤몬'),
         ('페가수스몬', '페가수몬'), ('데블몬', '데블몬'), ('가트몬', '가트몬'), ('엔젤우몬', '엔젤우몬'), ('레이디데블몬', '레이디데블몬'),
         ('네페르티몬', '네페르티몬'), ('브이몬', '브이몬'), ('엑스브이몬', '엑스브이몬'), ('파일드라몬', '파일드라몬'), ('황제드라몬(D)', '황제드라몬'),
         ('황제드라몬(F)', '황제파이터'), ('화염드라몬', '화염드라몬'), ('번개드라몬', '번개드라몬'), ('매그너몬', '매그너몬'), ('호크몬', '호크몬'),
         ('아큐라몬', '아쿠이라몬'), ('실피드몬', '실피드몬'), ('호루스몬', '할세몬'), ('수리몬', '슈림몬'), ('아르마몬', '두리몬'),
         ('황금아르마몬', '안킬로몬'), ('토우몬', '샤코몬'), ('디그몬', '디그몬'), ('잠수몬', '서브마리몬'), ('추추몬', '추추몬'), ('스팅몬', '스팅몬'),
         ('워매몬', '워매몬'), ('스카몬', '슈카몬'), ('에테몬', '에테몬'), ('피코데블몬', '피코데블몬'), ('묘티스몬', '묘티스몬'),
         ('베놈묘티스몬', '베놈묘티몬'), ('베타몬', '베타몬'), ('시드라몬', '시드라몬'), ('메탈시드라몬', '메탈시드라몬'), ('파워드라몬', '파워드라몬'),
         ('오메가몬', '오메가몬'), ('디아블로몬', '디아블로몬')]
assert len(EXCEL) == 65 and all(m in S for _, m in EXCEL), [m for _, m in EXCEL if m not in S]
have = {m for _, m in EXCEL}
# 디지골드에 이름은 「워그레이몬」으로 들어 있는 검은 워그레이몬(사용자 확인 10/8) → 블랙워그레이몬 그림으로 씀
EXTRA = [('워그레이몬(검정)', '블랙워그레이몬')]
have |= {m for _, m in EXTRA}
G1 = [k for k in ['레오몬', '안드로몬', '피노키몬', '피에몬', '아포카리몬'] if k not in have]
G2 = [k for k in ['코로몬', '둥실몬', '시드몬', '깜몬', '푸니몬', '뿔몬', '뇨키몬', '어니몬', '파브몬', '모티몬', '유라몬', '피치몬', '유키보타몬', '야옹몬', '플롯트몬', '세라피몬', '마그나드몬'] if k not in have and k not in DROP]
G4 = [k for k in ORDER if '보류' in S[k]['use'] and k not in have]
G3 = [k for k in ORDER if k not in have and k not in G1 + G2 + G4]
G5 = ['호우오몬', '헤라캅테몬', '바이킹몬', '하이안드몬', '메탈티라몬', '그란쿠와몬', '리리스몬', '발키리몬', '데비타마몬']   # 데드메라몬 = ③ 의 데스메라몬(결정7)
X = {m['name']: m for m in json.load(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'slots.json'), encoding='utf-8'))['mons'] if m['name'] in G5}
EN_X = {'호우오몬': 'Hououmon', '헤라캅테몬': 'HerculesKabuterimon', '바이킹몬': 'Vikemon', '하이안드몬': 'HiAndromon', '메탈티라몬': 'MetalTyrannomon',
        '그란쿠와몬': 'GranKuwagamon', '리리스몬': 'Lilithmon', '발키리몬': 'Valkyrimon', '데비타마몬': 'Devitamamon', '데드메라몬': 'DeathMeramon'}
for k in G5:
    S[k] = {'ko': k, 'en': EN_X[k], 'grade': X[k]['grade'], 'use': '10/8 추가(GBC 10/7 추가 종)'}
need = len(G1) + len(G2) + len(G3) + len(G4) + len(G5)
groups = [('① 먼저 — 주요 인물 · 맵에 디지몬으로 나옴', G1), ('② 다음 — 파트너 줄의 빠진 단계 · 스타팅(코로몬·둥실몬·시드몬) 먼저', G2),
          ('③ 그다음 — 1부 야생·트레이너·보스', G3), ('④ 마지막 — 2부(02)', G4), ('⑤ 추가(10/8 저녁) — GBC 마지막 주 추가 종. 호우오몬·헤라캅테몬·바이킹몬은 파트너 줄 궁극체라 중요', G5)]
diff = ['%s(=%s)' % (g, m) for g, m in EXCEL if g != m]
L = ['# 디지골드 대조표 (2026-10-08, 제작자 엑셀 기준) — 「없는 것부터」 그림 받기용', '',
     '## 디지골드에 있음 → 그림 안 받음 (65종 + 검은 워그레이몬 = 66, 엑셀 순서)', ', '.join(g for g, _ in EXCEL) + ', 워그레이몬(검정)=블랙워그레이몬', '',
     '이름이 내 설계와 다른 것: ' + ', '.join(diff), '', '게임에서 뺀 유아기·유년기(%d): %s (10/12: 성장기부터 시작. 유년기는 토코몬만 — 알 선물)' % (len(DROP), ', '.join(DROP)), '',
     '## 디지골드에 없음 → 그림 받을 것 (%d종, 위에서부터)' % need, '']
for t, g in groups: L += ['### %s (%d)' % (t, len(g)), ', '.join(g), '']
open(os.path.join(P, 'DG_대조표.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L).replace('데스메라몬', '데드메라몬'))   # 결정7 이름
ROLE = {'호우오몬': '피요몬 줄 궁극체', '헤라캅테몬': '텐타몬 줄 궁극체', '바이킹몬': '쉬라몬 줄 궁극체', '레오몬': '수호자(용기)·맵 등장', '안드로몬': '수호자(우정)·맵 등장', '피노키몬': '어둠의 4천왕·맵 등장', '피에몬': '어둠의 4천왕·맵 등장', '아포카리몬': '챔피언·맵 등장',
        '코로몬': '스타팅', '둥실몬': '스타팅', '시드몬': '스타팅'}
EN = {'크리사리몬': 'Chrysalimon', '백호몬': 'Baihumon', '주작몬': 'Zhuqiaomon', '현무몬': 'Xuanwumon', '돌핀몬': 'Dolphmon', '에이프몬': 'Apemon'}
# 메모는 NDS 표에서(10/8 교차 검증: GBC 쓰임 메모가 NDS 파티와 달랐음 — 지로몬·다크퍼펫몬 「시바 파티」 등)
import csv
NDS_USE = {}
for r in csv.DictReader(open(os.path.join(P, 'NDS_트레이너.tsv'), encoding='utf-8'), delimiter='	'):
    who = r['새 이름'] or r['키'].split('#')[0]
    for tok in r['파티'].split(','):
        nm = tok.strip().rpartition(':')[0]
        if nm and nm not in NDS_USE: NDS_USE[nm] = '%s 파티' % who
if os.path.exists(os.path.join(P, 'NDS_이벤트표.tsv')):
    for r in csv.DictReader(open(os.path.join(P, 'NDS_이벤트표.tsv'), encoding='utf-8'), delimiter='	'):
        if r['우리 종'] and r['우리 종'] not in NDS_USE: NDS_USE[r['우리 종']] = '%s(%s)' % (r['종류'], r['장소'])
# 순서는 퇴근 전에 가져간 표 그대로 두고(번호가 바뀌면 헷갈림), 1부에서 먼저 쓰이는 종에 표시만
EARLY = {'청룡몬', '백호몬', '주작몬', '현무몬', '무사몬', '나이트몬', '키메라몬', '밀레니엄몬', '마린데블몬', '에렉몬'}
def memo(s):
    m = ROLE.get(s['ko']) or NDS_USE.get(s['ko'], '')
    return ('⚑ 먼저(1부에서 씀) ' if s['ko'] in EARLY else '') + m
BABY = ('유아기Ⅰ', '유아기Ⅱ', '유년기Ⅰ', '유년기Ⅱ', '유년기')   # 사용자 10/8: 유년기 이하는 걷기 그림 대신 공용 알(디지타마)
def fid(en): return re.sub(r'[^a-z0-9]+', '-', (en or '').lower()).strip('-')
groups = [(t, [('데드메라몬' if x == '데스메라몬' else x) for x in g]) for t, g in groups]   # 결정7 이름
S['데드메라몬'] = S.get('데스메라몬', {'ko': '데드메라몬', 'en': 'DeathMeramon', 'grade': '완전체', 'use': ''})
T = ['# 그림 받을 목록 (디지골드에 없는 %d종, 2026-10-08, 제작자 엑셀 기준) — 위에서부터 차례로' % need, '',
     '파일 이름: 앞 = `<id>-ds-f.png`, 뒤 = `<id>-ds-b.png`, 걷기 = `<id>-ow.png`. 주문문의 영어 이름은 「영어」 칸.', '유아기·유년기는 걷기 그림을 받지 않는다(맵에서는 공용 알 그림으로 따라다님).', '']
n = 0
for t, g in groups:
    T += ['## %s (%d종)' % (t.split(' — ')[0], len(g)), '', '| # | 한글 | 영어 | id | 단계 | 받을 그림 | 메모 |', '|---|---|---|---|---|---|---|']
    for ko in g:
        s = S[ko]; n += 1; en = s['en'] or EN.get(ko, '?')
        baby = s['grade'] in BABY
        T.append('| %d | %s | %s | %s | %s | %s | %s |' % (n, ko, en, fid(en), s['grade'] or '-', '앞·뒤 (걷기=알)' if baby else '앞·뒤·걷기', memo(s)))
    T.append('')
open(os.path.join(P, 'DG_받을목록_표.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(T))
print('있음', len(have), '받을', need, [len(g) for _, g in groups])
