#!/usr/bin/env python3
"""python inject_well.py <입력 롬> <출력 롬> [개수=3] — 곤충 마을 우물 간부 랜스(트레이너 486)를 이기면 어둠의돌을 준다(2026-10-22 사용자 요청, 진화표 결정3 「1부 첫 어둠의돌」)
위치: 스크립트 파일 a/0/1/2 #60 의 세 번째 스크립트. 흐름(pret script.inc 명령표로 읽음):
  PlaySE · LockAll · FacePlayer · NPCMsg 1(싸우기 전) · CloseMsg · TrainerBattle 486 · CheckBattleWon 0x800C · Compare 0x800C,0 · GoToIf EQ → 져서 쓰러짐(DB 00 = 블랙아웃)
  · NPCMsg 2(진 뒤 대사) · CloseMsg · FadeScreen · WaitFade · HidePerson ×4 · SetFlag 0x1A9 …
  → 이긴 쪽 흐름 중 「CloseMsg 뒤 FadeScreen(10바이트)」을 GoTo 새 토막으로 바꾼다. 새 토막 = 도구 주기(SetVar 8004 도구 / SetVar 8005 개수 / CallStd 2033 = 받았다 글·팡파르·가방에 넣기) + 원래 FadeScreen + 원래 자리 다음으로 GoTo.
  가방이 가득 차면 CallStd 2033 이 알아서 처리(이브이 알 고침과 같은 방식)."""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(H, '..')))
import hg1
from hg1 import NDS, NARC
src, dst = sys.argv[1], sys.argv[2]; QTY = int(sys.argv[3]) if len(sys.argv) > 3 else 3
ITEM_DARK, FILE = 108, 60
nds = NDS(open(src, 'rb').read()); nar = NARC(nds.get('a/0/1/2')); files = list(nar.files); d = bytearray(files[FILE])
FADE = bytes.fromhex('ae00 0600 0100 0000 0000'.replace(' ', ''))               # FadeScreen(174) 6,1,0,0
anchor = bytes.fromhex('d500 e601 0000 0000 dc00 0c80 1100 0c80 0000 1c00 01'.replace(' ', ''))   # TrainerBattle 486 · CheckBattleWon · Compare · GoToIf EQ
a = bytes(d).find(anchor); assert a >= 0 and bytes(d).count(anchor) == 1, '우물 간부 전투 스크립트를 못 찾음'
k = bytes(d).find(bytes.fromhex('2d0002' '3500'), a)                               # NPCMsg 2 · CloseMsg (이긴 뒤 대사)
assert k == a + len(anchor) + 4, 'NPCMsg 2 위치가 예상과 다름(GoToIf 바로 뒤여야 함)'
f0 = k + 5
if bytes(d[f0:f0 + 10]) != FADE:
    # 이미 고친 롬이면 GoTo 로 바뀌어 있음
    assert d[f0:f0 + 2] == struct.pack('<H', 22), '이긴 뒤 FadeScreen 이 없음 — 예상과 다름'
    print('ok 이미 고침(우물 간부 어둠의돌)'); open(dst, 'wb').write(bytes(nds.d)); sys.exit(0)
while len(d) % 4: d += b'\0'
blk = len(d)
d += struct.pack('<HHH', 41, 0x8004, ITEM_DARK) + struct.pack('<HHH', 41, 0x8005, QTY) + struct.pack('<HH', 20, 2033)   # SetVar · SetVar · CallStd 2033
d += FADE
back = f0 + 10
d += struct.pack('<H', 22) + struct.pack('<i', back - (len(d) + 2) - 4)
while len(d) % 4: d += b'\0'
d[f0:f0 + 10] = struct.pack('<H', 22) + struct.pack('<i', blk - (f0 + 2) - 4) + b'\0' * 4
files[FILE] = bytes(d); nar.files = files; nds.put('a/0/1/2', nar.build())
open(dst, 'wb').write(bytes(nds.d)); print('ok 우물 간부 랜스 이기면 어둠의돌 ×%d (스크립트 #60 @%05X → 새 토막 @%05X, 돌아갈 곳 @%05X)' % (QTY, f0, blk, back))
