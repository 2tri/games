#!/usr/bin/env python3
"""python inject_v15_fix.py <입력 롬> <출력 롬> — 2부 PC 점검(2026-10-27)에서 찾은 것 고침
 ① 2부 수호자 7명(산해·엔젤우몬·예지·릴리몬·재하·쥬드몬·스팅몬)의 보상 뒤 대사가 하트골드 관장의 옛 기술머신 설명
    (전격파·스킬스왑·물의파동·기가드레인·독찌르기·스톤샤워·오버히트) 그대로 → 실제로 주는 디지멘탈·플레이트 설명으로.
    (리키는 실제로 기술머신92 트릭룸을 줘서 그대로)
 ② 매몰탑 「그란돈」 방(지도524, 스크립트 133): 오메가몬 Lv50(오메가몬은 옆 방에 Lv60이 또 있음) + 대사 「그란돈」
    → 설계표대로 메탈에테몬 Lv55(종 57, 롬에서 얻을 길이 없던 종) + 대사도 메탈에테몬으로. 구슬 이야기(겐나이)의 그란돈·가이오가·레쿠쟈도
    이 롬의 실제 상대(메탈에테몬·황제드라몬·오메가몬)로.
 ③ 2부 지역·전화·라디오 대사에 남은 원작 포켓몬 이름(v15_names.py).
여러 번 돌려도 같은 결과."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..'))); sys.path.insert(0, H)
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
import v15_names
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []

draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(H, '..', 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
mfiles = list(mn.files); mdirty = False
SP = '{01DE}'
def T(s): return s.replace(' ', SP)
def set_msg(bank, idx, new, old_part):
    """bank:idx 를 new 로. 이미 new 면 건너뜀, 아니면 old_part 가 있어야 바꿈."""
    global mdirty
    seed, ents = MSG[bank]; ents = list(ents); cur = CM.dec(ents[idx]); new = T(new)
    if cur == new: return False
    assert T(old_part) in cur, '글 %d:%d 가 예상과 다름: %r' % (bank, idx, cur[:60])
    enc = CM.enc(new); assert CM.dec(enc) == new, '글 %d:%d 검산 실패' % (bank, idx)
    ents[idx] = enc; MSG[bank] = (seed, ents); mfiles[bank] = msg_encode(seed, ents); mdirty = True; return True

# ========= ① 2부 수호자 보상 대사 =========
G = [
 (480, 3, '산해{01C4} 이 용기의 증표는\\n미한테 이긴 자에게 어울려{01AB}\\f소중히 해주세{01BE}요{01AB}\\r그리고 원 모어 프레젠트{01AB}\\r우정의 디지멘탈을\\n유에게 프레젠트 할게요{01AB}\\r', '훌륭한 기술머신을'),
 (480, 4, '산해{01C4} 우정의 디지멘탈은\\n브이몬을 번개드라몬으로\\f진화시켜요{01AB}\\r가방에서 브이몬에게\\n써 보세요{01AB}\\r이 마을을 나가면\\n북쪽에는 빛의 언덕이라는\\f큰 시티가 있어{01BE}요{01AB}', '일렉트릭 쇼'),
 (526, 3, '엔젤우몬{01C4} 너의 강함을\\n난 예지하지 못했어{01AE}{01AE}{01AE}\\r즉 너의 강함은\\n내 초능력을\\f넘었다는 것{01AE}{01AE}{01AE}\\r그런 너에게\\n빛의 디지멘탈을 줄게{01AB}\\r', '이 기술머신을 줄게'),
 (526, 4, '엔젤우몬{01C4} 빛의 디지멘탈은\\n가트몬을 네페르티몬으로\\f진화시켜{01AB}\\r가방에서 가트몬에게\\n써 봐{01AB}\\r너의 미래는 밝아\\n훌륭한 챔피언으로서\\f환영받을 거야{01AB}', '스킬스웹'),
 (464, 12, '예지{01C4} 순수의 디지멘탈은\\n호크몬을 수리몬으로\\f진화시켜\\r가방에서 호크몬에게\\n써 봐\\r파일섬에서 여기까지\\n이겨서 온 너니까\\f유용하게 써 주겠지', '물의파동'),
 (487, 3, '릴리몬{01C4} 멋있는 시합이었어요\\n저 아주 감동했어요\\r특별히 이것을 드리지요\\n기적의 디지멘탈{01AE}{01AE}{01AE}\\r브이몬이나 엑스브이몬에게\\n지니게 하고 레벨을 올리면\\f매그너몬으로 진화한답니다{01AB}\\r', '기가드레인'),
 (509, 3, '재하{01C4} 너 강하구나{01AB}\\n특별히 이걸 줄게{01AB}\\r성실의 디지멘탈이야{01AB}\\n아르마몬에게 쓰면\\f잠수몬으로 진화해{01AB}\\r', '독찌르기'),
 (457, 3, '쥬드몬{01C4} 고마워\\n{FFFE}{0103}{0002}{0000}{0000}{01AB}\\f좋은 승부였어{01AB}\\r보답으로 또 하나\\n암석플레이트를\\f너에게 선물할게{01AB}\\r지니게 하면 바위타입\\n기술이 강해져{01AB}\\r', '스톤샤워'),
 (457, 4, '쥬드몬{01C4} 고마워\\n{FFFE}{0103}{0002}{0000}{0000}{01AB}\\f좋은 승부였어{01AB}\\r보답으로 또 하나\\n암석플레이트를\\f너에게 선물할게{01AB}\\r지니게 하면 바위타입\\n기술이 강해져{01AB}\\r', '스톤샤워'),
 (52, 3, '스팅몬{01C4} 그리고 또 하나\\n이것을 주지{01AB}\\r불구슬플레이트다\\n지니게 하면\\f불꽃 기술이 강해진다\\r', '오버히트'),
 (52, 4, '스팅몬{01C4} 이번에는 내가 졌지만\\n주인이 돌아오면\\f다음번이야말로 이긴다{01AB}\\r언젠가 다시 싸우자{01AB}', '홍련체육관'),
 (52, 5, '스팅몬{01C4} 주인과 함께\\n더 강해지겠다{01AB}', '불꽃디지몬을'),
]
n = sum(set_msg(*g) for g in G)
done.append('2부 수호자 보상 대사 → 실제 보상 %d줄' % n if n else '이미 고침: 2부 수호자 보상 대사')

# ========= ② 매몰탑 그란돈 방 → 메탈에테몬 Lv55 =========
SP_METALETEMON, OLD_SP = 57, 383
sn = NARC(nds.get(hg1.NARC_PATHS['script'])); sfiles = list(sn.files); f = bytearray(sfiles[133]); ch = 0
for k in range(len(f) - 6):
    op = struct.unpack_from('<H', f, k)[0]
    if op == 0x4c and struct.unpack_from('<H', f, k + 2)[0] in (OLD_SP, SP_METALETEMON):      # PlayCry 종
        if struct.unpack_from('<H', f, k + 2)[0] == OLD_SP: struct.pack_into('<H', f, k + 2, SP_METALETEMON); ch += 1
    if op == 0x24d and struct.unpack_from('<H', f, k + 2)[0] in (OLD_SP, SP_METALETEMON):     # WildBattle 종,레벨
        if struct.unpack_from('<HH', f, k + 2) == (OLD_SP, 50): struct.pack_into('<HH', f, k + 2, SP_METALETEMON, 55); ch += 1
        else: assert struct.unpack_from('<HH', f, k + 2) == (SP_METALETEMON, 55), '매몰탑 전투 값이 예상과 다름'
if ch:
    sfiles[133] = bytes(f); sn.files = sfiles; nds.put(hg1.NARC_PATHS['script'], sn.build())
    done.append('매몰탑(지도524) 오메가몬 Lv50 → 메탈에테몬 Lv55 (울음·전투 %d곳)' % ch)
else: done.append('이미 고침: 매몰탑 메탈에테몬')
M = [
 (147, 0, '메탈에테몬{01C4} 우키키키{01AB}\\r', '그란돈'),
 (147, 1, '메탈에테몬은 모습을 감췄다{01AE}{01AE}{01AE}', '그란돈'),
 (147, 2, '야{01BE} 반가워요{01AB}\\n이야{01BE} 깜짝 놀랐어요{01BE}{01AB}\\r지금의 디지몬은\\n호연지방에 전해지는\\f건국 신화에 등장하는\\f메탈에테몬{01AB}{01AB}\\r그렇군요 그렇군요{01BE}\\r이 매몰탑은\\n호연지방의 사람들이\\f만든 것이었군요{01BE}\\r', '그란돈'),
 (147, 3, '그렇다고 하면{01AE}{01AE}{01AE}{01AC}\\r바다와 육지와 하늘을\\n연결한 탑{01AE}{01AE}{01AE}\\r호연의 신화에\\n등장하는 디지몬은\\f메탈에테몬만은 아니었다{01AE}{01AE}{01AE}\\r이곳에는\\n아직 밝혀지지 않은\\f수수께끼가 있군요{01BE}\\r', '그란돈'),
 (147, 4, '높{01BE}은 디지몬 박사에게\\n메탈에테몬을 보여주면\\f뭔가 힌트를 얻을 수 있을지도{01AC}\\r이야{01BE}\\n디지몬과 신화의 관계는\\f뜻이 깊네요{01BE}\\r그러면 또\\n어디선가 만납시다{01BE}\\r', '그란돈'),
]
n = sum(set_msg(*m) for m in M)
if n: done.append('매몰탑 대사 그란돈 → 메탈에테몬 %d줄' % n)

# ========= ③ 2부 대사의 원작 포켓몬 이름 =========
nfix = 0
for bank, idx in sorted(set(v15_names.plan()) | set(v15_names.CRY)):
    seed, ents = MSG[bank]; ents = list(ents)
    cur = CM.dec(ents[idx]).replace(SP, ' ')
    new = v15_names.fix(bank, idx, cur)
    if new == cur: continue
    new = new.replace(' ', SP); enc = CM.enc(new); assert CM.dec(enc) == new, '글 %d:%d 검산 실패' % (bank, idx)
    ents[idx] = enc; MSG[bank] = (seed, ents); mfiles[bank] = msg_encode(seed, ents); mdirty = True; nfix += 1
done.append('2부 대사 원작 포켓몬 이름 → 디지몬 %d줄' % nfix if nfix else '이미 고침: 2부 대사 이름')

if mdirty:
    mn.files = mfiles; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d))
for d in done: print(' -', d)
print('v1.5 수정 %d건' % len(done))
