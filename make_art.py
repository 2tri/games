"""art_nds.py + design.json → C:/개인/넘길것_ART.py (붙여넣기용 한 파일)"""
import zlib, base64, os
H = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(H, 'design.json'), 'rb').read()
b = base64.b64encode(zlib.compress(d, 9)).decode(); b = '\n'.join(b[i:i + 100] for i in range(0, len(b), 100))
s = open(os.path.join(H, 'art_nds.py'), encoding='utf-8').read().replace("DESIGN_B64 = '@@'", 'DESIGN_B64 = """\n%s\n"""' % b)
out = os.path.join(H, '..', '넘길것_ART.py'); open(out, 'w', encoding='utf-8', newline='\n').write(s); print(os.path.getsize(out))
