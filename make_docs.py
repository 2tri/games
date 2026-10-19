"""문서 묶음: NDS 설계 문서 + 표를 다시 만드는 스크립트를 하나의 「스스로 풀리는」 파이썬 파일로 → C:/개인/넘길것_문서.py
집 묶음(넘길것_묶음.py)은 롬 작업에 필요한 것만, 이 묶음은 회사 PC 를 못 쓰게 된 뒤(10/19~)에도 집에서 설계를 이어 가기 위한 것.
집 PC 에서: 메모장에 붙여 「넘길것_문서.py」로 저장 → python 넘길것_문서.py → 문서는 그 폴더에, 스크립트는 src_hg/ 에 풀린다."""
import zlib, base64, hashlib, json, os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
NL = chr(10)
DOCS = ['공략_초안.md', '인수인계_집.md', '작업_보고.md', '집_시작_설명.md', '넘길것_집지시.md', '자율작업_진행.md', 'NDS_계획.md', 'NDS_스토리.md', 'NDS_대사.md',
        'NDS_진화표.md', 'NDS_밸런스.md', 'NDS_트레이너_초안.md', 'DG_대조표.md', 'DG_받을목록_표.md', 'DG_조사.md', 'HG_작업표.md', '넘길것_주인공_주문.md', '넘길것_트레이너_주문.md', '넘길것_그림주문_합본.md', '넘길것_그림주문_2.md', 'NDS_스토리_2부_초안.md', '넘길것_2부대사_지시.md', '넘길것_GBC_질문.md']
SCRIPTS = ['make_guide.py', 'make_species_draft.py', 'make_dex_map.py', 'make_terms.py', 'make_trainers.py', 'make_digigold_lists.py', 'check_balance.py',
           'test_fake_rom.py', 'pokemon_names.py', 'export_design.py', 'make_bundle.py', 'make_docs.py', 'make_order_sheet.py']
files = {}
for d in DOCS:
    if os.path.exists(os.path.join(P, d)): files[d] = open(os.path.join(P, d), encoding='utf-8').read()
for s in SCRIPTS:
    if os.path.exists(os.path.join(H, s)): files['src_hg/' + s] = open(os.path.join(H, s), encoding='utf-8').read()
blob = zlib.compress(json.dumps(files, ensure_ascii=False).encode('utf-8'), 9)
sha = hashlib.sha1(blob).hexdigest()
b = base64.b64encode(blob).decode()
lines = [b[i:i + 100] for i in range(0, len(b), 100)]
parts = 3; per = (len(lines) + parts - 1) // parts
head = NL.join([
    '#!/usr/bin/env python3',
    '# 문서 묶음 (2026-10-08 작성) — 메모장에 붙여 「넘길것_문서.py」로 저장(파일 형식: 모든 파일, 인코딩 UTF-8)',
    '# 넘길것_묶음.py 를 푼 같은 폴더에서:   python 넘길것_문서.py   → 설계 문서(.md)와 src_hg/ 스크립트가 풀린다(토큰 0)',
    '# 「조각 n/m」 줄은 나눠 붙일 때 경계 표시일 뿐이다. 순서대로 이어 붙이면 된다.',
    'import base64, zlib, json, hashlib, sys, os',
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
    "    if os.path.dirname(name): os.makedirs(os.path.dirname(name), exist_ok=True)",
    "    if os.path.exists(name): print('덮어씀:', name)",
    "    open(name, 'w', encoding='utf-8', newline=NL).write(text)",
    "    print('풀림:', name, len(text))",
    "import shutil",
    "for f in ('hg1.py', 'hg2.py', 'hg3.py', 'hg4.py', 'art_nds.py', 'hg_scan.py', 'design.json'):   # 집 묶음에서 풀린 것을 src_hg 에도(표 만드는 스크립트가 옆에서 찾음)",
    "    if os.path.exists(f) and not os.path.exists(os.path.join('src_hg', f)): shutil.copy(f, os.path.join('src_hg', f)); print('복사:', f, '→ src_hg/')",
    "if not os.path.exists('hg1.py'): print('알림: 넘길것_묶음.py 를 먼저 푼 폴더에서 실행해야 src_hg 스크립트가 돌아갑니다')",
    "print('끝. 인수인계_집.md 부터 읽으세요.')",
    ''])
out = os.path.join(P, '넘길것_문서.py')
open(out, 'w', encoding='utf-8', newline=NL).write(head + body + tail)
print(os.path.getsize(out), '바이트,', len(lines), '줄,', len(files), '파일')
