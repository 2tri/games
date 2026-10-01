"""한글판 금·은 글자 부호표 → charmap.json (pokegold-kr 디스어셈블리의 constants/charmap 에서 읽음)
글자 부호 자체는 공개된 사실(Bulbapedia 'Korean character encoding (Generation II)')."""
import re, os, json, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('POKEGOLD_KR', '/home/user/narishma-gb/pokegold-kr'), 'constants')
enc = {}                       # 글자 → 바이트열(16진 문자열)
for t in range(1, 12):
    for line in open(os.path.join(SRC, 'charmap', 'korean_table_%x.asm' % t)):
        m = re.match(r'\s*kr_charmap "(.+)", \$([0-9a-fA-F]+)', line)
        if m: enc.setdefault(m.group(1), '%02x%02x' % (t, int(m.group(2), 16)))
single = {}
for line in open(os.path.join(SRC, 'charmap.asm')):
    m = re.match(r'\s*charmap "(.+?)",\s*\$([0-9a-fA-F]+)', line)
    if m: single.setdefault(m.group(1), '%02x' % int(m.group(2), 16))
json.dump({'kr': enc, 'single': single}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'charmap.json'), 'w'), ensure_ascii=False, indent=0)
print(len(enc), len(single))
