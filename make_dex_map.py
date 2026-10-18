"""골드 도감 번호(1~251) → 우리 디지몬 대체표. 하트골드 원래 야생·트레이너·이벤트의 포켓몬을 바꿀 때 쓴다.
근거 순서: ① GBC 칸(그 번호에 넣은 디지몬) ② GBC mapping.csv 의 대체(계획종·대체이름·대체칸) ③ 직접 정함(10/8)
출력: ../NDS_대체표.tsv"""
import csv, os
import pokemon_names as PN
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
rows = list(csv.DictReader(open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t'))
names = {r['이름'] for r in rows}
by = {int(r['칸(골드 도감 번호)']): r['이름'] for r in rows if r['칸(골드 도감 번호)'].isdigit()}
mp = {int(r['칸']): r for r in csv.DictReader(open(os.path.join(P, '..', 'GBC', 'repo', 'romhack', 'mapping.csv'), encoding='utf-8-sig'))}
MANUAL = {19: '파피몬', 46: '팔몬', 118: '쉬라몬', 161: '아구몬', 166: '브이몬', 179: '텐타몬', 180: '호크몬', 187: '피요몬', 240: '플롯트몬',   # 10/12: 뺀 유년기 자리 → 진화형
          36: '엔젤우몬', 144: '막음', 146: '막음', 151: '막음', 152: '팔몬', 153: '니드몬', 154: '릴리몬', 155: '아구몬', 156: '그레이몬',
          157: '메탈그레이몬', 158: '쉬라몬', 159: '원뿔몬', 160: '쥬드몬', 201: '디지문자', 233: '데이터몬', 238: '위자몬', 239: '에렉몬', 247: '모노크로몬',
          248: '트리케라몬', 251: '막음'}
# 스토리 문서로 덮어씀(10/8 교차 검증): 오메가몬은 오메가블레이드로만(스토리 3-2), 밀레니엄몬은 디지문자 유적 숨은 방(스토리 D8)
OVERRIDE = {145: ('막음', '스토리 3-2(오메가몬은 오메가블레이드로만)'), 150: ('막음', '스토리 D8(밀레니엄몬은 유적 숨은 방)')}
out = [['번호', '포켓몬', '우리 종', '근거']]
for n in range(1, 252):
    if n in OVERRIDE: out.append([n, PN.NAMES[n - 1], OVERRIDE[n][0], OVERRIDE[n][1]]); continue
    if n in by: out.append([n, PN.NAMES[n - 1], by[n], 'GBC 칸']); continue
    r = mp.get(n); got = None
    if r:
        for k, why in ((r['계획종'], '계획종'), (r['대체이름'], '대체이름')):
            if k and k in names: got = (k, 'GBC mapping.csv ' + why); break
        if not got and r['대체칸'].isdigit() and int(r['대체칸']) in by: got = (by[int(r['대체칸'])], 'GBC mapping.csv 대체칸 %s' % r['대체칸'])
    if not got: got = (MANUAL[n], '직접(10/8)')
    out.append([n, PN.NAMES[n - 1], got[0], got[1]])
BABY_EVO = {'코로몬': '아구몬', '둥실몬': '쉬라몬', '시드몬': '팔몬', '뿔몬': '파피몬', '어니몬': '피요몬', '모티몬': '텐타몬', '야옹몬': '플롯트몬', '퍼그몬': '가지몬', '츠메몬': '케라몬', '꼬마몬': '브이몬', '포로몬': '호크몬', '우파몬': '두리몬', '리프몬': '추추몬'}   # 10/12: 뺀 유년기 자리는 그 진화형으로
for x in out[1:]:
    if x[2] in BABY_EVO: x[2] = BABY_EVO[x[2]]; x[3] += ' → 유년기 뺌(10/12)'
bad = [x for x in out[1:] if x[2] not in names and x[2] not in ('막음', '디지문자')]
assert not bad, bad
open(os.path.join(P, 'NDS_대체표.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join('\t'.join(map(str, x)) for x in out) + '\n')
import collections
print('251줄:', collections.Counter(x[3].split(' ')[0] for x in out[1:]))
