#!/usr/bin/env python3
"""python fix_linebreaks.py <입력 롬> <출력 롬> — 두 줄 대화창에서 글이 끊기는 줄바꿈 고치기 (2026-10-27)
에뮬 확인한 대화창 동작: \\n = 다음 줄, \\f = 버튼 기다린 뒤 한 줄 올림(커서 줄 그대로), \\r = 새 쪽(첫 줄).
둘째 줄에서 \\f 로 올려 쓴 뒤 \\r 없이 \\n 이 오면 셋째 줄로 넘쳐 그 뒤 글이 안 나오고 대화가 끝난다.
원작 하트골드(K) 롬에는 이런 줄이 0줄, 우리가 새로 쓴 대사에는 128줄 있었다(겐나이 안내·진화 메시지·2부 이야기 등).
고치는 법: 쪽(\\r 사이)마다 화면 줄을 「첫 줄 \\n 둘째 줄 \\f 셋째 줄 \\f …」 원작 방식으로 다시 잇는다. 글자는 그대로.
여러 번 돌려도 같은 결과."""
import sys, os, re, csv
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, '..')); sys.path.insert(0, ROOT)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
BS = chr(92); PAT = re.compile('[' + BS + BS + '][nfr]'); TOK = re.compile('[' + BS + BS + '][nfr]|[{][0-9A-F]{4}[}]')

def bad(t):
    line = 1; scrolled = False
    for m in PAT.finditer(t):
        c = m.group()[1]
        if c == 'n':
            if scrolled and TOK.sub('', t[m.end():]).strip(): return True
            line += 1
        elif c == 'f':
            if line >= 2: scrolled = True
        else: line = 1; scrolled = False
    return False

def refit(t):
    # 끝에 붙은 줄바꿈 기호(보이는 글 없음)는 그대로 둔다
    m = re.search('(?:[' + BS + BS + '][nfr])+$', t); tail = m.group() if m else ''
    body = t[:len(t) - len(tail)]
    pages = body.split(BS + 'r')
    out = []
    for p in pages:
        lines = PAT.split(p)
        s = lines[0]
        for k, l in enumerate(lines[1:], 1):
            s += (BS + 'n' if k == 1 else BS + 'f') + l
        out.append(s)
    return (BS + 'r').join(out) + tail

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    nds = NDS(open(src, 'rb').read())
    draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(ROOT, 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
    mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
    for f in mn.files:
        try: MSG.append(msg_decode(f))
        except Exception: MSG.append(None)
    CM = hg1.infer_charmap([m if m else (0, []) for m in MSG], draft)[0]
    files = list(mn.files); n = 0
    for b, m in enumerate(MSG):
        if not m: continue
        seed, ents = m; ents = list(ents); dirty = False
        for i, e in enumerate(ents):
            try: t = CM.dec(e)
            except Exception: continue
            if not bad(t): continue
            new = refit(t)
            assert not bad(new), '%d:%d 고친 뒤에도 넘침' % (b, i)
            assert PAT.sub('', new) == PAT.sub('', t), '%d:%d 글자가 바뀜' % (b, i)
            enc = CM.enc(new); assert CM.dec(enc) == new, '%d:%d 검산 실패' % (b, i)
            ents[i] = enc; dirty = True; n += 1
            print(' - %d:%d %s' % (b, i, new[:70]))
        if dirty: files[b] = msg_encode(seed, ents)
    if n: mn.files = files; nds.put(hg1.NARC_PATHS['msg'], mn.build())
    open(dst, 'wb').write(bytes(nds.d))
    print('줄바꿈 고침 %d줄' % n)
