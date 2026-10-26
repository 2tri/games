#!/usr/bin/env python3
"""python inject_story_fix.py <입력 롬> <출력 롬> — 1부 처음부터 끝까지 직접 플레이하며 찾은 「설계표 ≠ 롬」 어긋남을 한 번에 고침 (2026-10-26)
 ① 바위산 마을 수련장 레오몬: 보상이 기술머신 31(설계표는 번호 328로 적어 못 찾고 지나감)이라 사랑의 디지멘탈이 1부 어디서도 안 나옴
    → 파일 877 의 도구 0x166 → 0x50(사랑의 디지멘탈). 보상 뒤 설명 대사(기술머신 설명)도 디지멘탈 설명으로.
 ② 보상 뒤 설명 대사가 옛 기술머신 설명 그대로인 곳 5곳(미나·가트몬·안드로몬·정석·리키)도 실제 받은 도구 설명으로.
 ③ 호크몬(설계표: 진청시티 선물 Lv27) · 브이몬(설계표: 35번도로 편지 배달 선물 Lv18): 야생표에서 빼 놓고 선물 스크립트는 안 만들어져 1부에서 얻을 길이 없었음
    → 호크몬: 바위산 마을 바닷가 노인(지도385, 파일884)에게 처음 말 걸면 선물 · 브이몬: 장난감 마을 메일 아주머니(지도101, 파일241)가 배달 사례 때 선물.
 ④ 방울탑 청룡몬 레벨: 하트골드 분기 55(0x37) → 설계표 Lv60(0x3C) (파일21).
 ⑤ 아폴로 뒤 국장 대사·방울탑 무녀 대사의 「투명한방울」은 도구 이름이 아님(가방에는 「무지갯빛날개」·「크리스탈방울」)
    → 국장이 주는 것은 무지갯빛날개, 무녀가 말하는 것은 크리스탈방울로 대사를 맞춤.
이미 고친 롬이면 「이미 고침」으로 건너뜀(여러 번 돌려도 같은 결과)."""
import sys, os, struct, csv
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import hg1
from hg1 import NDS, NARC, msg_decode, msg_encode
src, dst = sys.argv[1], sys.argv[2]
nds = NDS(open(src, 'rb').read()); done = []

# ---------- 글(메시지) 도구 ----------
draft = {r['이름'] for r in csv.DictReader((l for l in open(os.path.join(H, '..', 'NDS_종_초안.tsv'), encoding='utf-8') if not l.startswith('#')), delimiter='\t')}
mn = NARC(nds.get(hg1.NARC_PATHS['msg'])); MSG = []
for f in mn.files:
    try: MSG.append(msg_decode(f))
    except Exception: MSG.append((0, []))
CM = hg1.infer_charmap(MSG, draft)[0]
mfiles = list(mn.files); mdirty = False
SP = '{01DE}'
def T(s): return s.replace(' ', SP)            # 보기 편하게 띄어쓰기는 공백으로 적고 여기서 {01DE} 로
def set_msg(bank, idx, new, old_part=None):
    """bank:idx 글을 new 로 바꿈. old_part 가 있으면 현재 글에 그 조각이 있을 때만(없으면 이미 고친 것으로 보고 new 와 같은지 확인)."""
    global mdirty
    seed, ents = MSG[bank]; ents = list(ents); cur = CM.dec(ents[idx]); new = T(new)
    if cur == new: return False
    if old_part is not None: assert old_part in cur, '글 %d:%d 가 예상과 다름: %r' % (bank, idx, cur[:60])
    enc = CM.enc(new); assert CM.dec(enc) == new, '글 %d:%d 검산 실패' % (bank, idx)
    ents[idx] = enc; MSG[bank] = (seed, ents); mfiles[bank] = msg_encode(seed, ents); mdirty = True; return True
def add_msg(bank, text):
    """글 끝에 새 글을 더함 → 번호. 같은 글이 이미 있으면 그 번호(여러 번 돌려도 안 늘어남)."""
    global mdirty
    seed, ents = MSG[bank]; ents = list(ents); text = T(text)
    for i, e in enumerate(ents):
        if CM.dec(e) == text: return i
    enc = CM.enc(text); assert CM.dec(enc) == text, '새 글 검산 실패'
    ents.append(enc); assert len(ents) <= 255, '글 번호가 1바이트를 넘음'
    MSG[bank] = (seed, ents); mfiles[bank] = msg_encode(seed, ents); mdirty = True; return len(ents) - 1

# ---------- 스크립트 도구 ----------
sn = NARC(nds.get(hg1.NARC_PATHS['script'])); sfiles = list(sn.files)
def p16(*a): return struct.pack('<%dH' % len(a), *a)
OP_CHECKFLAG, OP_SETFLAG, OP_GOTO, OP_GOTOIF, OP_NPCMSG, OP_CLOSEMSG, OP_WAITBUTTON = 32, 30, 22, 28, 45, 53, 50
def checkflag(f): return p16(OP_CHECKFLAG, f)
def setflag(f): return p16(OP_SETFLAG, f)
def npcmsg(n): return p16(OP_NPCMSG)[:2] + bytes([n])
def bufplayer(): return p16(190)[:2] + bytes([0])
def fanfare(): return p16(78, 0x04A3) + p16(79)
def givemon(sp, lv): return p16(137, sp, lv, 0, 0, 0, 0x800C)
def closemsg(): return p16(OP_CLOSEMSG)
def waitbutton(): return p16(OP_WAITBUTTON)
def goto_to(at, dest): return struct.pack('<Hi', OP_GOTO, dest - (at + 6))             # 이 명령이 놓일 자리 at → dest
def gotoif_to(at, cond, dest): return struct.pack('<HBi', OP_GOTOIF, cond, dest - (at + 7))
def hook(fi, where, size, make_block, what):
    """파일 fi 의 where 부터 size(≥6) 바이트를 GoTo 새토막 으로 바꿈. make_block(blk_addr, back_addr) → 새 토막 바이트(마지막은 GoTo back 포함하게 호출자가 만듦).
    이미 고친 롬(where 에 GoTo 가 있음)이면 건너뜀."""
    d = bytearray(sfiles[fi])
    if d[where:where + 2] == p16(OP_GOTO): done.append('이미 고침: ' + what); return False
    while len(d) % 4: d += b'\0'
    blk = len(d); back = where + size
    d += make_block(blk, back)
    while len(d) % 4: d += b'\0'
    d[where:where + size] = goto_to(where, blk) + b'\0' * (size - 6)
    sfiles[fi] = bytes(d); done.append(what + ' (파일 %d @%X → 새 토막 @%X)' % (fi, where, blk)); return True
def patch16(fi, off, old, new, what):
    d = bytearray(sfiles[fi]); cur = struct.unpack_from('<H', d, off)[0]
    if cur == new: done.append('이미 고침: ' + what); return
    assert cur == old, '%s: 파일 %d @%X 값이 %d (예상 %d)' % (what, fi, off, cur, old)
    struct.pack_into('<H', d, off, new); sfiles[fi] = bytes(d); done.append(what)

# ========= ① 레오몬: 사랑의 디지멘탈 =========
patch16(877, 0x12A, 0x166, 0x50, '레오몬 보상 기술머신 31 → 사랑의 디지멘탈')
set_msg(569, 6, '레오몬{01C4} 사랑의 디지멘탈은\\n호크몬을 호루스몬으로\\f진화시킨다{01AB}\\r가방에서 호크몬에게\\n사용해 봐라{01AB}', '기술머신')
# ========= ② 보상 뒤 옛 기술머신 설명 =========
set_msg(577, 7, '미나{01C4} 그건 기력의조각이야\\n쓰러진 디지몬을\\f기운차게 되살려 줘{01AB}\\r귀여운 나한테 딱이지{01AC}\\r아 맞아{01AB}\\r여기에서 북쪽에 있는\\n자연공원의 옆에\\f디지슬론이라는 경기장이\\f오픈했어{01AB}\\r너 굉장히\\n능숙하게 디지몬을 다루잖아\\f가보는 게 좋을 것 같아', '헤롱헤롱')
set_msg(609, 5, '가트몬{01C4} 그건 희망의 디지멘탈\\r파닥몬이나 엔젤몬에게 쓰면\\n페가수몬으로 진화한다\\r가방에서 사용해 봐', '섀도볼')
set_msg(601, 5, '안드로몬{01C4} 그건 태그입니다{01AE}{01AE}{01AE}\\r성숙기 디지몬이 지니고\\n레벨을 올리면\\f완전체로 진화합니다{01AE}{01AE}{01AE}', '아이언테일')
set_msg(617, 4, '정석{01C4} 그건 지식의 디지멘탈\\r아르마몬에게 쓰면\\n디그몬으로 진화한다\\f가방에서 디지몬에게\\n사용해 봐라', '싸라기눈')
set_msg(626, 7, '리키{01C4} 궁극의 문장은 완전체가\\n지니고 레벨을 올리면\\f궁극체로 진화시켜 줘{01AB}\\r필요 없다면 무리해서\\n가져가지 않아도 돼{01AB}\\r', '용의파동')
done.append('보상 뒤 설명 대사 6곳(레오몬·미나·가트몬·안드로몬·정석·리키)')

# ========= ③ 호크몬 · 브이몬 선물 =========
SP_V, SP_H = 287, 296                                     # 칸표(hg2_out/칸표.tsv): 브이몬 287 · 호크몬 296
FLAG_H = 0x9FD                                            # 안 쓰는 플래그(vardep 로 확인)
# 호크몬: 바위산 마을 바닷가 노인(파일 884, 글 575)의 처음 말 걸기 — 원래 GetGameVersion(4)+CompareVarToValue 800C,7(6) 10바이트 자리를 후킹
mh1 = add_msg(575, '어라{01AB} 너{01AE}{01AE}{01AE}\\n디지몬 트레이너로구나{01AB}\\f이 호크몬을 데려가 주겠니{01AC}\\n내가 키우기에는 너무\\f힘이 센 녀석이라서{01AB}\\r사양하지 마{01AB}\\r')
mh2 = add_msg(575, '{FFFE}{0103}{0002}{0000}{0001}\\n호크몬을 받았다{01AB}')
def blk_h(blk, back):
    c = bytearray(); a = blk
    def put(b):
        nonlocal a
        c.extend(b); a += len(b)
    put(checkflag(FLAG_H))
    # GoToIf TRUE → 원래 흐름(아래 orig 자리). orig 위치는 모든 명령 길이를 알아야 하므로 길이 먼저 계산
    seq_len = 4 + 7 + 3 + 2 + 2 + 3 + 3 + 4 + 2 + 14 + 4 + 2
    orig = blk + seq_len
    c.clear(); a = blk
    put(checkflag(FLAG_H)); put(gotoif_to(a, 1, orig))
    put(npcmsg(mh1)); put(waitbutton()); put(closemsg()); put(bufplayer()); put(npcmsg(mh2)); put(fanfare()); put(givemon(SP_H, 27)); put(setflag(FLAG_H)); put(closemsg())
    assert a == orig, (a, orig)
    put(struct.pack('<HH', 495, 0x800C) + p16(17, 0x800C, 7))            # 후킹으로 가려진 GetGameVersion 800C · CompareVarToValue 800C,7
    put(goto_to(a, back))
    return bytes(c)
hook(884, 0x0E, 10, blk_h, '호크몬 선물(바위산 마을 바닷가 노인) Lv27')
# 브이몬: 장난감 마을 메일 아주머니(파일 241, 글 383) 배달 사례 — CallStd 7F1(4)+CompareVarToValue 4114,3(6) 10바이트 자리를 후킹
mv1 = add_msg(383, '그리고{01AB} 이 아이도{01DE}데려가 줘{01AB}\\r내 친구가 아끼던\\n디지몬인데 너라면\\f잘 키워 줄 것 같아{01AB}\\r')
mv2 = add_msg(383, '{FFFE}{0103}{0002}{0000}{0001}\\n브이몬을 받았다{01AB}')
def blk_v(blk, back):
    c = bytearray(); a = blk
    def put(b):
        nonlocal a
        c.extend(b); a += len(b)
    put(p16(20, 0x7F1))                                                   # 원래 CallStd 7F1(도구 받기)
    put(npcmsg(mv1)); put(waitbutton()); put(closemsg()); put(bufplayer()); put(npcmsg(mv2)); put(fanfare()); put(givemon(SP_V, 18)); put(closemsg())
    put(p16(17, 0x4114, 3))                                               # 원래 CompareVarToValue 4114,3
    put(goto_to(a, back))
    return bytes(c)
hook(241, 0x135, 10, blk_v, '브이몬 선물(편지 배달 사례) Lv18')

# ========= ④ 청룡몬 Lv60 =========
patch16(21, 0x4E, 0x37, 0x3C, '방울탑 청룡몬(하트골드 분기) Lv55 → 60')

# ========= ⑤ 투명한방울 대사 =========
KEEP = '고맙다{01AB} 살았어\\f이건 무지갯빛날개\\n방울탑을 오를 자격의\\f증표란다{01AB}\\r크리스탈방울은 유령 마을의\\n전통무용수들이 알고 있단다'
for i in (5, 7): set_msg(69, i, KEEP, '투명한방울')
set_msg(57, 0, '크리스탈방울을\\n가져왔군요\\f탑 꼭대기에서\\n청룡몬이 기다려요\\f그 전에 우리 다섯을\\n다시 이겨 보세요', '투명한방울')
done.append('「투명한방울」 대사 → 무지갯빛날개/크리스탈방울')

# ========= ⑥ 말하는 사람 이름표 「그대로」 =========
# 용어표(NDS_용어표.tsv)의 「랜스·람다·아테나 → 그대로(바꾸지 않음)」가 글 속 이름표에 글자 그대로 들어가 「그대로: …」로 나옴 → 제 이름으로
LABELS = {(68, 3): '람다', (90, 1): '랜스', (90, 2): '랜스', (722, 1093): '랜스', (722, 1097): '랜스', (722, 1108): '아테나',
          (112, 6): '아테나', (112, 3): '간부', (112, 4): '간부', (112, 8): '간부', (113, 7): '간부'}
fixed = 0
for (b, i), nm in LABELS.items():
    cur = CM.dec(MSG[b][1][i])
    if cur.startswith('그대로{01C4}'):
        assert set_msg(b, i, nm + cur[len('그대로'):]); fixed += 1
done.append('이름표 「그대로」 → 제 이름 %d곳(이미 고친 곳 제외)' % fixed if fixed else '이름표 「그대로」 이미 고침')
# 소용돌이섬 소문 대사의 「그대로를 흩날리며」는 「은빛날개」가 글자 그대로 바뀐 것
cur = CM.dec(MSG[722][1][817])
if '그대로를{01DE}흩날리며' in cur:
    set_msg(722, 817, cur.replace('그대로를{01DE}흩날리며', '은빛날개를{01DE}흩날리며')); done.append('소용돌이섬 소문 대사 「은빛날개」 복구')

# ========= ⑦ 「유인 피리」 =========
# 꽃집 언니·길 막은 나무 대사(글 385·383#11 등)는 「유인 피리」인데 가방에 들어오는 도구 이름은 「물뿌리개」(용어표 「물뿌리개 → 유인 피리」가 도구 이름표에는 안 먹음)
if set_msg(220, 477, '유인 피리', '물뿌리개'):
    set_msg(219, 477, '이상한 나무나 커다란\\n벌레 디지몬을 불러내는\\n피리{01AE}')
    done.append('도구 「물뿌리개」 → 「유인 피리」(이름·설명)')
else: done.append('이미 고침: 도구 유인 피리')

# ---------- 쓰기 ----------
sn.files = sfiles; how = nds.put(hg1.NARC_PATHS['script'], sn.build())
if mdirty: mn.files = mfiles; nds.put(hg1.NARC_PATHS['msg'], mn.build())
open(dst, 'wb').write(bytes(nds.d)); print('ok', ' / '.join(done))
