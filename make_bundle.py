"""집 묶음: hg1·hg2·hg3·art_nds 와 자료 표들을 하나의 「스스로 풀리는」 파이썬 파일로 → C:/개인/넘길것_묶음.py
집 PC 에서: 메모장에 붙여 「넘길것_묶음.py」로 저장 → python 넘길것_묶음.py → 같은 폴더에 파일이 풀린다(토큰 0).
붙여넣기가 한 번에 안 되면 「조각 n/m」 줄을 경계로 나눠 붙여도 된다(순서만 지키면 됨)."""
import zlib, base64, hashlib, json, os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
NL = chr(10)

def rd(path): return open(path, encoding='utf-8').read()

files = {   # 스크립트는 자료를 품지 않은 틀, 자료는 한 번만
    'hg1.py': rd(os.path.join(H, 'hg1.py')),
    'hg2.py': rd(os.path.join(H, 'hg2.py')),
    'hg3.py': rd(os.path.join(H, 'hg3.py')),
    'art_nds.py': rd(os.path.join(H, 'art_nds.py')),
    'hg_scan.py': rd(os.path.join(H, 'hg_scan.py')),
    'hg4.py': rd(os.path.join(H, 'hg4.py')),
    'wikimon_get.py': rd(os.path.join(H, 'wikimon_get.py')),
    'dsprobe.py': rd(os.path.join(H, 'dsprobe.py')),
    'dsdump.py': rd(os.path.join(H, 'dsdump.py')),
    'dsraw.py': rd(os.path.join(H, 'dsraw.py')),
    'hg_clues.py': rd(os.path.join(H, 'hg_clues.py')),
    'hg4_icons.py': rd(os.path.join(H, 'hg4_icons.py')),
    'hg4_follow.py': rd(os.path.join(H, 'hg4_follow.py')),
    'sdat_scan.py': rd(os.path.join(H, 'sdat_scan.py')),
    'hg_trace.py': rd(os.path.join(H, 'hg_trace.py')),
    'hg_hard.py': rd(os.path.join(H, 'hg_hard.py')),
    'hg4_trainer.py': rd(os.path.join(H, 'hg4_trainer.py')),
    'hg_event.py': rd(os.path.join(H, 'hg_event.py')),
    'merge_2bu.py': rd(os.path.join(H, 'merge_2bu.py')),
    'hg_song.py': rd(os.path.join(H, 'hg_song.py')),
    'sheet_cut.py': rd(os.path.join(H, 'sheet_cut.py')),
    'rom_check.py': rd(os.path.join(H, 'rom_check.py')),
    'rom_bisect.py': rd(os.path.join(H, 'rom_bisect.py')),
    'midi_match.py': rd(os.path.join(H, 'midi_match.py')),
    'piano_get.py': rd(os.path.join(H, 'piano_get.py')),
    '모아보고.py': rd(os.path.join(H, '모아보고.py')),

    '2부_초안.md': rd(os.path.join(P, 'NDS_스토리_2부_초안.md')),
    '2부대사_지시.md': rd(os.path.join(P, '넘길것_2부대사_지시.md')),
    'design.json': rd(os.path.join(H, 'design.json')),
    'wikimon_속성.tsv': rd(os.path.join(H, 'wikimon_속성.tsv')),
    'NDS_종_초안.tsv': rd(os.path.join(P, 'NDS_종_초안.tsv')),
    'NDS_대체표.tsv': rd(os.path.join(P, 'NDS_대체표.tsv')),
    'NDS_용어표.tsv': rd(os.path.join(P, 'NDS_용어표.tsv')),
    'NDS_트레이너.tsv': rd(os.path.join(P, 'NDS_트레이너.tsv')),
    'NDS_장면대사.tsv': rd(os.path.join(P, 'NDS_장면대사.tsv')),
    '집지시.md': rd(os.path.join(P, '넘길것_집지시.md')),          # 10/16: 지시문을 묶음 안에 — 붙여넣기 중 지시가 잘려 [3c]·[10d] 등이 빠졌던 일(집 보고)
}
for opt in ('NDS_도감_보충.tsv', 'NDS_진화.tsv', 'NDS_이벤트표.tsv', 'NDS_글자표_추가.tsv', 'NDS_귀한종.tsv', 'NDS_실마리_고침.tsv', 'NDS_속성_고침.tsv', 'NDS_칸_고정.tsv', 'NDS_도감순서.tsv', 'NDS_기술이름.tsv', 'NDS_필살기.tsv', 'NDS_트레이너그림.tsv', 'NDS_도구설명.tsv', 'NDS_노래배정.tsv', 'NDS_피아노출처.tsv', 'NDS_선물도구.tsv', 'NDS_흔적_예외.tsv'):          # 있으면 넣음
    if os.path.exists(os.path.join(P, opt)): files[opt] = rd(os.path.join(P, opt))
# 10/16: 마지막 묶음 — 집이 설계자가 되므로 설계 문서·표 생성 스크립트·남은 일 표까지 한 파일에
for d_ in ('넘길것_그림주문_1016.md', '사용자_선택.md', '인수인계_집.md', '열린일.md', '자율작업_진행.md', '공략_초안.md', '기술표.md', '기술표.tsv', 'NDS_계획.md', 'NDS_스토리.md', 'NDS_대사.md', 'NDS_진화표.md', 'NDS_밸런스.md', 'NDS_트레이너_초안.md',
           'DG_대조표.md', 'DG_받을목록_표.md', 'DG_조사.md', 'HG_작업표.md', 'NDS_스토리_2부_초안.md', '넘길것_그림주문_합본.md', '작업_보고.md'):
    if os.path.exists(os.path.join(P, d_)): files['문서/' + d_] = rd(os.path.join(P, d_))
for s_ in sorted(os.listdir(H)):
    if s_.endswith('.py') and s_ not in files: files[s_] = rd(os.path.join(H, s_))          # 표 생성·점검 스크립트(make_*·check_balance·test_fake_rom 등)도 같이
# 지시문 잘림 검사: 맨 위 「꼭 지킬 순서」의 단계가 모두 줄 머리에 정의돼 있어야 함(10/15 설계자 실수로 [3c]·[10d] 정의가 지워졌던 일)
import re as _re
_j = files['집지시.md']; _ord = next(l for l in _j.split(NL) if '꼭 지킬 순서' in l)
_miss = [k for k in _re.findall(r'\[[^\]]+\]', _ord) if not any(l.startswith(k) for l in _j.split(NL))]
if _miss: raise SystemExit('실패: 집지시.md 에 정의가 없는 단계 %s — 지시문이 잘렸음. 묶음을 만들지 않음' % _miss)
blob = zlib.compress(json.dumps(files, ensure_ascii=False).encode('utf-8'), 9)
sha = hashlib.sha1(blob).hexdigest()
b = base64.b64encode(blob).decode()
lines = [b[i:i + 100] for i in range(0, len(b), 100)]
parts = 4; per = (len(lines) + parts - 1) // parts
head = NL.join([
    '#!/usr/bin/env python3',
    '# 집 묶음 (' + __import__('datetime').date.today().isoformat() + ' 판) — 메모장에 붙여 「넘길것_묶음.py」로 저장(파일 형식: 모든 파일, 인코딩 UTF-8)',
    '# 롬과 같은 폴더에서:   python 넘길것_묶음.py   → hg1.py hg2.py hg3.py art_nds.py 와 표 3개가 풀린다(토큰 0)',
    '# 「조각 n/m」 줄은 나눠 붙일 때 경계 표시일 뿐이다. 순서대로 이어 붙이면 된다.',
    'import base64, zlib, json, hashlib, sys',
    'try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
    'except Exception: pass',
    "SHA = '%s'" % sha,
    'DATA = """']) + NL
body = ''
for k in range(parts):
    chunk = lines[k * per:(k + 1) * per]
    if chunk: body += '# ---- 조각 %d/%d ----' % (k + 1, parts) + NL + NL.join(chunk) + NL
tail = NL.join([
    '"""',
    'NL = chr(10)',
    "raw = ''.join(l.strip() for l in DATA.split(NL) if l.strip() and not l.strip().startswith('#'))",
    'blob = base64.b64decode(raw)',
    'if hashlib.sha1(blob).hexdigest() != SHA:',
    "    print('실패: 붙여넣기 중에 글자가 빠졌거나 순서가 바뀜. 조각을 처음부터 순서대로 다시 붙여 주세요'); sys.exit(1)",
    "files = json.loads(zlib.decompress(blob).decode('utf-8'))",
    'for name, text in files.items():',
    "    import os; (os.makedirs(os.path.dirname(name), exist_ok=True) if os.path.dirname(name) else None)",
    "    open(name, 'w', encoding='utf-8', newline=NL).write(text)",
    "    print('풀림:', name, len(text))",
    "print('끝. 이제 같은 폴더의 「집지시.md」를 열어 처음부터 끝까지 그대로 하세요(묶음 안에 들어 있어 잘리지 않음).')",
    ''])
out = os.path.join(P, '넘길것_묶음.py')
open(out, 'w', encoding='utf-8', newline=NL).write(head + body + tail)
print(os.path.getsize(out), '바이트,', len(lines), '줄')
