"""20판: 위키몬 DS 전투 그림을 주소로 직접 받기 (wikimon_ds.py 가 제목으로 못 찾는 종용). python3 ds_extra.py
images/digimon/<id>-ds-f.png (전투 앞모습), <id>-ds-b.png (공격 자세를 좌우 뒤집어 뒷모습 자리)"""
import os, urllib.request
from io import BytesIO
from PIL import Image, ImageOps
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'images', 'digimon')
UA = {'User-Agent': 'Mozilla/5.0 (personal fan project; one-time fetch)'}
EXTRA = {'redvegimon': ('/images/e/e6/Redvegimon_dssm_battle.png', '/images/2/23/Redvegimon_dssm_battle_attack.png')}      # 레드베지몬 (Red Vegimon, 성숙기)


def get(u): return urllib.request.urlopen(urllib.request.Request('https://wikimon.net' + u, headers=UA), timeout=30).read()


for did, (f, b) in EXTRA.items():
    open(os.path.join(OUT, did + '-ds-f.png'), 'wb').write(get(f))
    ImageOps.mirror(Image.open(BytesIO(get(b))).convert('RGBA')).save(os.path.join(OUT, did + '-ds-b.png'))
    print('받음', did)
