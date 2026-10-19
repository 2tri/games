"""hg2.py + NDS_종_초안.tsv → C:/개인/넘길것_HG2.py (hg1.py 와 같은 폴더에서 실행)"""
import zlib, base64, os
H = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(H, '..', 'NDS_종_초안.tsv'), 'rb').read()
b = base64.b64encode(zlib.compress(d, 9)).decode(); b = '\n'.join(b[i:i + 100] for i in range(0, len(b), 100))
s = open(os.path.join(H, 'hg2.py'), encoding='utf-8').read().replace("DRAFT_B64 = '@@'", 'DRAFT_B64 = """\n%s\n"""' % b)
out = os.path.join(H, '..', '넘길것_HG2.py'); open(out, 'w', encoding='utf-8', newline='\n').write(s); print(os.path.getsize(out))
