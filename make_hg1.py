"""hg1.py(틀) + design.json → C:/개인/넘길것_HG1.py (붙여넣기용 한 파일)"""
import zlib, base64, hashlib, os
H = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(H, 'design.json'), 'rb').read(); c = zlib.compress(d, 9)
b = base64.b64encode(c).decode(); b = '\n'.join(b[i:i + 100] for i in range(0, len(b), 100))
s = open(os.path.join(H, 'hg1.py'), encoding='utf-8').read()
s = s.replace("'@@SHA1@@'", "'%s'" % hashlib.sha1(c).hexdigest()).replace('@@B64@@', b)
out = os.path.join(H, '..', '넘길것_HG1.py')
open(out, 'w', encoding='utf-8', newline='\n').write(s)
open(os.path.join(H, 'hg1_full.py'), 'w', encoding='utf-8', newline='\n').write(s)
print(os.path.getsize(out))
