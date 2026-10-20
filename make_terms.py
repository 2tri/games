"""NDS_대사.md(스토리·대사 담당이 쓴 문서) → 롬에 적용할 두 표
  ../NDS_용어표.tsv   : 옛 | 새 | 범위 | 비고      (범위: 전체 / 문맥 / 트레이너이름 / 타입표)
  ../NDS_장면대사.tsv : 번호 | 장면 | 화자 | 실마리 | 새 대사
범위 규칙(hg3.py 가 씀)
- 전체: 앞이 한글이 아닐 때만 바꿈(「완성도」의 성도 보호)
- 이름: 앞이 한글이 아니고 뒤가 조사·문장부호·끝일 때만(「비상구」「그린 그림」 보호) — 1-5 인물 이름
- 문맥: 「이름」 조건 + 같은 글에 관장·체육관·수련장·수호자·사천왕·챔피언·배지·문장·트레이너 중 하나가 있거나 바로 뒤가 『 일 때만 — 1-9 손으로만 낱말
- 타입표: 타입 이름 글에서만
GBC 설계에서 온 타입 이름(결정 필요: 페어리=빛)은 여기서 덧붙인다."""
import os, re, json
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
doc = open(os.path.join(P, 'NDS_대사.md'), encoding='utf-8').read()

def sections(doc):
    cur = None; out = {}
    for line in doc.split('\n'):
        m = re.match(r'^###\s+(\S+)\s*(.*)', line)
        if m: cur = m.group(1); out[cur] = {'title': m.group(2), 'rows': []}; continue
        if cur and line.startswith('|') and not re.match(r'^\|\s*-', line):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            out[cur]['rows'].append(cells)
    return out

S = sections(doc)
manual = set()
for cells in S.get('1-9.', {}).get('rows', [])[1:]:
    for w in re.split(r'[·/]', cells[0]): manual.add(w.strip())
rows = []
def add(old, new, scope, note):
    old = old.strip(); new = new.strip()
    if old and new and old != new and all(r[0] != old for r in rows): rows.append([old, new, scope, note])
for sec in ('1-2.', '1-3.', '1-4.', '1-5.', '1-6.', '1-7.', '1-8.'):
    if sec not in S: continue
    for cells in S[sec]['rows'][1:]:
        if len(cells) < 2: continue
        if '손으로만' in cells[1] or '파티(' in cells[1]: continue      # 지시문(무녀 파티·손으로만)은 치환이 아님(교차 검증 10/8)
        olds = [o for o in re.split(r'\s+/\s+', cells[0]) if o]
        news = [x for x in re.split(r'\s+/\s+', cells[1]) if x]
        if len(olds) > 1 and len(news) == len(olds): pairs = list(zip(olds, news))   # 「A / B / C → X / Y / Z」는 하나씩 짝
        else: pairs = [(o, cells[1]) for o in olds]
        if len(pairs) == 1 and '·' in pairs[0][0] and '·' not in pairs[0][1]:      # 「뮤·뮤츠 → 환상의 디지몬」은 각각
            pairs = [(o, pairs[0][1]) for o in pairs[0][0].split('·') if o]
        for o, nw in pairs:
            base = re.sub(r'\s*\(.*?\)\s*', '', o)
            if base in ('프리져', '썬더', '파이어'): continue          # 문장째 고침(장면 대사)
            if base in manual or sec == '1-5.': scope = '문맥'     # 사람 이름은 모두 문맥(코드 검토 10/8: 「이걸 사도 괜찮아」 같은 일반 낱말 보호)
            elif sec == '1-8.': scope = '이름'                     # 포켓몬 이름: 뒤가 조사·부호·끝일 때만(「뮤직」「우파몬」 보호)
            else: scope = '전체'
            add(base, nw, scope, '%s %s %s' % (sec, cells[2] if len(cells) > 2 else '', cells[3] if len(cells) > 3 else ''))
# 문서에 없던 기본값(10/8 시험에서 필요해짐)
add('성도 지방', '파일섬', '전체', '기본값'); add('관동 지방', '신대륙', '전체', '기본값')
add('실버', '매튜', '트레이너이름', '라이벌 기본 이름(트레이너 이름표에서만 — 실버스프레이 등 보호)')
# 타입 이름(GBC 설계 + 결정 필요 추천)
d = json.load(open(os.path.join(H, 'design.json'), encoding='utf-8'))
for o, n in d['rules']['TYPE_RENAME'].items():
    if o == '에스퍼': continue      # 10/19 v1.1: 에스퍼는 원래 이름 그대로(「영혼」은 포켓몬에 없는 이름이라 뺌)
    add(o, n, '타입표', '타입 이름(결정 필요: 페어리=빛)')
add('페어리', '빛', '타입표', '결정 필요 — 추천')
rows.sort(key=lambda r: -len(r[0]))
open(os.path.join(P, 'NDS_용어표.tsv'), 'w', encoding='utf-8', newline='\n').write('옛\t새\t범위\t비고\n' + '\n'.join('\t'.join(r) for r in rows) + '\n')
# 장면 대사
# 실마리가 비었거나 「(24의 전투 글)」 같은 자리표시인 줄 → HG3 가 트레이너 글 표(trtbl)로 찾는 표시(교차 검증 10/8)
#   @라이벌 n 이김|짐 : 라이벌 n차(1~5 = 1부 실버, 6~7 = 2부) 세 가지(스타팅별) 모두
#   @트레이너 <NDS_트레이너.tsv 키> 이김|짐 : 그 트레이너(하트골드 이름 첫 번째)
#   @트레이너이름 <하트골드 트레이너 이름> 이김|짐
#   @무녀 <가트몬|엔젤몬|위자몬|고스몬|데블몬|방울탑> 전|이김 : 빛의 무녀(HG3 가 이브이 진화형 1마리 트레이너로 찾음)
#   전 = 만남 글(종류 0), 이김 = 주인공이 이겼을 때 그 트레이너가 하는 말(종류 1), 짐 = 주인공이 졌을 때
CLUE_FIX = {'25': '@라이벌 1 이김', '26': '@라이벌 1 짐', '52': '@라이벌 2 이김', '53': '@라이벌 2 짐', '74': '@라이벌 3 이김', '75': '@라이벌 3 짐',
            '127': '@라이벌 4 이김', '128': '@라이벌 4 짐', '146': '@라이벌 5 이김', '147': '@라이벌 5 짐',
            '192': '@라이벌 6 이김', '193': '@라이벌 6 짐', '201': '@라이벌 7 이김', '202': '@라이벌 7 짐',
            '104': '@트레이너이름 미나키 이김', '151': '@트레이너 Will 이김', '152': '@트레이너 Will 짐', '154': '@트레이너 Koga 이김', '155': '@트레이너 Koga 짐',
            '157': '@트레이너 Bruno 이김', '158': '@트레이너 Bruno 짐', '160': '@트레이너 Karen 이김', '161': '@트레이너 Karen 짐',
            '163': '@트레이너 Champion 이김', '164': '@트레이너 Champion 짐', '207': '@트레이너 Red 이김', '208': '@트레이너 Red 짐',
            '204': '(확인: 스이쿤을 잡은 뒤 미나키 글 — HG1 texts 에서 실마리 찾기. 76번과 실마리가 같았음)',
            # 빛의 무녀(가무연장 5명): 원래 이브이 진화형으로 찾은 트레이너의 「만남(전)」·「짐(이김)」 글. 방울탑은 5명 모두
            '80': '@무녀 가트몬 전', '81': '@무녀 가트몬 이김', '82': '@무녀 엔젤몬 전', '83': '@무녀 엔젤몬 이김', '84': '@무녀 위자몬 전',
            '85': '@무녀 위자몬 이김', '86': '@무녀 고스몬 전', '87': '@무녀 고스몬 이김', '88': '@무녀 데블몬 전', '89': '@무녀 데블몬 이김',
            '137': '@무녀 방울탑 이김',
            '119': '(HG1 뒤: 아지트 간부가 하트골드의 어느 간부 트레이너인지 짝지은 뒤 @트레이너이름 으로)',
            '131': '(HG1 뒤: 라디오 타워 꼭대기 간부 아폴로 트레이너 이름 확인 뒤 @트레이너이름 으로)',
            '132': '(HG1 뒤: 라디오 타워 꼭대기 간부 아폴로 트레이너 이름 확인 뒤 @트레이너이름 으로)',
            '198': '(HG1 뒤: 마일도 자리 트레이너를 정한 뒤 @트레이너이름 으로)', '199': '(HG1 뒤: 마일도 자리 트레이너를 정한 뒤 @트레이너이름 으로)',
            '169': '(HG1 texts 에서 항구 마을 상점 앞 NPC 원문 찾기)'}
# 10/14: 실마리 고침 표(NDS_실마리_고침.tsv — 집 보고 「실마리_후보」에서 원문 위치를 고름). 새 대사 칸이 있으면 대사도 바꿈
FIX2, TXT2 = {}, {}
fp2 = os.path.join(P, 'NDS_실마리_고침.tsv')
if os.path.exists(fp2):
    for ln in open(fp2, encoding='utf-8').read().split(chr(10))[1:]:
        c = ln.split(chr(9))
        if len(c) >= 2 and c[0].strip().isdigit():
            FIX2[c[0].strip()] = c[1].strip()
            if len(c) >= 3 and c[2].strip(): TXT2[c[0].strip()] = c[2].strip()
CLUE_FIX.update(FIX2)
scenes = []
for sec, v in S.items():
    if not sec.startswith('2-'): continue
    for cells in v['rows'][1:]:
        if len(cells) >= 5 and cells[0].isdigit():
            scenes.append([cells[0], v['title'] + ' / ' + cells[1], cells[2], CLUE_FIX.get(cells[0], cells[3]), TXT2.get(cells[0], cells[4])])
open(os.path.join(P, 'NDS_장면대사.tsv'), 'w', encoding='utf-8', newline='\n').write('번호\t장면\t화자\t실마리\t새 대사\n' + '\n'.join('\t'.join(c.replace('\t', ' ') for c in r) for r in scenes) + '\n')
import collections
print('용어 %d %s / 손으로만 %d / 장면 대사 %d' % (len(rows), dict(collections.Counter(r[2] for r in rows)), len(manual), len(scenes)))
