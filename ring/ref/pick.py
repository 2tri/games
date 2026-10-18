import json, os, urllib.request
from PIL import Image, ImageDraw, ImageFont
UA = "RingFanGameResearch/0.1 (personal non-commercial)"
PICK = {  # 캐릭터: [(후보번호, 메모)]
 'gandalf':  [(38, '회색 전신, 흰 배경'), (13, '칼 든 자세'), (12, '지팡이 전신'), (56, '백색 전신'), (9, '백색 동작')],
 'frodo':    [(11, '전신, 백엔드 계단'), (2, '스팅 든 자세'), (4, '얼굴')],
 'sam':      [(16, '앉은 전신, 흰 배경'), (26, '빛의 병 든 자세'), (22, '얼굴·망토')],
 'aragorn':  [(7, '전신, 흰 배경'), (0, '안두릴 든 자세'), (16, '칼 휘두름')],
 'legolas':  [(42, '활 든 전신, 회색 배경'), (27, '활 당김 전신'), (18, '상반신')],
 'gimli':    [(17, '도끼 든 전신'), (6, '양손 도끼 동작'), (7, '상반신')],
 'balrog':   [(13, '다리 위 간달프와 대치'), (15, '전신 그림'), (17, '전신 어둠')],
 'gollum':   [(22, '웅크린 전신, 흰 배경'), (24, '반지 든 모습'), (6, '바위 위')],
 'saruman':  [(5, '지팡이 전신, 흰 배경'), (12, '전신'), (15, '상반신·지팡이')],
 'witchking':[(31, '갑옷 전신 설정화'), (22, '말 탄 모습'), (38, '칼 든 모습')],
 'nazgul':   [(43, '칼 든 전신'), (18, '두건·칼'), (12, '말 탄·서 있는 모습')],
 'uruk':     [(4, '전신'), (2, '얼굴·갑옷'), (5, '얼굴')],
 'cavetroll':[(1, '사슬·몽둥이 전신, 흰 배경'), (2, '전신'), (4, '동작')],
 'shelob':   [(10, '전신, 흰 배경'), (3, '덮치는 모습'), (11, '굴 속')],
 'boromir':  [(12, '전신'), (1, '뿔나팔 부는 모습'), (6, '상반신·방패')],
 'galadriel':[(12, '전신, 흰 배경'), (6, '옆모습 긴 머리'), (13, '얼굴·머리띠')],
}
NAMES = {'gandalf': '간달프', 'frodo': '프로도', 'sam': '샘', 'aragorn': '아라곤', 'legolas': '레골라스', 'gimli': '김리', 'balrog': '발로그',
         'gollum': '골룸', 'saruman': '사루만', 'witchking': '마술사왕', 'nazgul': '검은 기사(나즈굴)', 'uruk': '우루크하이', 'cavetroll': '동굴 트롤',
         'shelob': '쉴로브', 'boromir': '보로미르', 'galadriel': '갈라드리엘'}
lines = ['# 참고 이미지 목록 (캐릭터별)', '', '출처: lotr.fandom.com 위키 문서에 걸린 이미지. `python3 pick.py`로 다시 받을 수 있음(이미지 파일은 저장소에 올리지 않음).', '']
for name, picks in PICK.items():
    meta = {m['i']: m for m in json.load(open(f'cand/{name}/meta.json'))}
    os.makedirs(name, exist_ok=True)
    lines.append(f'## {NAMES[name]} (`{name}/`)')
    for k, (i, memo) in enumerate(picks, 1):
        m = meta[i]; p = f'{name}/{k}.jpg'
        if not os.path.exists(p):
            data = urllib.request.urlopen(urllib.request.Request(m['url'], headers={'User-Agent': UA}), timeout=60).read()
            open(p, 'wb').write(data)
            try:
                im = Image.open(p); im.thumbnail((900, 900)); im.convert('RGB').save(p, quality=92)
            except Exception as e: print('bad', p, e)
        lines.append(f'{k}. {memo} — {m["file"]} ({m["w"]}×{m["h"]}) {m["url"]}')
    lines.append('')
open('목록.md', 'w').write('\n'.join(lines))
print('ok')
