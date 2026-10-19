"""hg3.py + 표 3개(종 초안·포켓몬 대체표·용어표) → C:/개인/넘길것_HG3.py (hg1.py·hg2.py 와 같은 폴더에서 실행)"""
import zlib, base64, os
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(H, '..')
t = {k: open(os.path.join(P, k), encoding='utf-8').read() for k in ('NDS_종_초안.tsv', 'NDS_대체표.tsv', 'NDS_용어표.tsv', 'NDS_트레이너.tsv', 'NDS_장면대사.tsv')}
b = base64.b64encode(zlib.compress(repr(t).encode('utf-8'), 9)).decode(); b = '\n'.join(b[i:i + 100] for i in range(0, len(b), 100))
s = open(os.path.join(H, 'hg3.py'), encoding='utf-8').read().replace("TABLES_B64 = '@@'", 'TABLES_B64 = """\n%s\n"""' % b)
out = os.path.join(P, '넘길것_HG3.py'); open(out, 'w', encoding='utf-8', newline='\n').write(s); print(os.path.getsize(out))
