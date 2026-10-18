#!/usr/bin/env python3
"""떠돌이(라이코·앤테이·라티아스·라티오스)의 종·레벨을 arm9 코드 안에서 바꾼다. 롬은 읽기만 하고 새 파일로 저장. (Claude 작성, 2026-10-15)
사용:   python inject_roamer.py <입력 롬.nds> <출력 롬.nds> [--species 243,244,40,176] [--levels 40,40,50,50]
        (순서 = 떠돌이 번호 0·1·2·3 = 라이코·앤테이·라티아스·라티오스. 기본값 = 백호몬 243·주작몬 244·마그나드몬 40·세라피몬 176, Lv 40·40·50·50)
위치:   압축 푼 arm9(롬 머리말의 arm9 자리, hg4_icons 가 압축 푼 채 롬 끝에 놓은 것) 안의 두 함수 — 한국판 하트골드 기준 주소(arm9 시작 = 0x02000000)
        ① 0x6780C~0x6782E  Save_CreateRoamerByID : 번호별 case 가 「movs r6,#종 / movs r5,#레벨」 (라티는 종 380 = 95<<2, 381 = 리터럴 @0x678EC)
        ② 0x678F0~        SpeciesToRoamerIdx : 종 → 번호(243→0, 244→1, 380→2, 381→3). 새 종 번호로 비교하도록 직선 비교 사슬로 다시 씀
        (미국판 0x020676EC / 0x020677F4 와 같은 함수. 종 번호는 칸 번호 — 255 이하만 바로 비교 가능)
읽는 법: 바꾸기 전 바이트가 기대와 다르면 멈춘다(다른 롬이면 주소가 다름)."""
import sys, struct, argparse

ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('out')
ap.add_argument('--species', default='243,244,40,176'); ap.add_argument('--levels', default='40,40,50,50')
A = ap.parse_args()
SP = [int(x) for x in A.species.split(',')]; LV = [int(x) for x in A.levels.split(',')]
assert len(SP) == 4 and len(LV) == 4, '종·레벨 4개씩'
assert all(1 <= s <= 255 for s in SP), '종 칸은 255 이하만(직접 비교) — 더 크면 리터럴 방식이 필요'
assert all(1 <= l <= 100 for l in LV)

d = bytearray(open(A.rom, 'rb').read())
a9o, a9ram, a9sz = struct.unpack_from('<III', d, 0x20)[0], struct.unpack_from('<I', d, 0x28)[0], struct.unpack_from('<I', d, 0x2C)[0]
assert a9ram == 0x02000000, 'arm9 시작 주소가 0x02000000 아님'
BASE = a9o
def h(o): return struct.unpack_from('<H', d, BASE + o)[0]
def sh(o, v): struct.pack_into('<H', d, BASE + o, v)

# 기대 바이트(원래) — 이미 바꾼 롬이면 「이미 바뀜」으로 보고 같은 값으로 다시 씀
orig = {0x67818: 0x26F3, 0x6781A: 0x2528, 0x6781E: 0x26F4, 0x67820: 0x2528, 0x67824: 0x265F, 0x67826: 0x00B6, 0x67828: 0x2523, 0x6782C: 0x4E2F, 0x6782E: 0x2523, 0x678F0: 0xB508, 0x678F2: 0x215F}
bad = [hex(o) for o, v in orig.items() if h(o) != v]
if bad:
    # 이미 이 도구로 바꾼 롬인지: 0x678F2 가 cmp r0,#imm8 (28xx)
    if h(0x678F2) >> 8 == 0x28 and h(0x678F0) == 0xB508: print('이미 바뀐 롬 — 같은 값으로 다시 씀')
    else: sys.exit('기대한 원래 바이트가 아님: %s — 다른 롬이면 주소가 다름' % bad)
assert a9sz >= 0x67930 and BASE + 0x67930 < len(d)
print('arm9 @0x%X 크기 0x%X' % (a9o, a9sz))

# ① Save_CreateRoamerByID
sh(0x67818, 0x2600 | SP[0]); sh(0x6781A, 0x2500 | LV[0])
sh(0x6781E, 0x2600 | SP[1]); sh(0x67820, 0x2500 | LV[1])
sh(0x67824, 0x2600 | SP[2]); sh(0x67826, 0x46C0); sh(0x67828, 0x2500 | LV[2])       # movs r6,#종 / nop / movs r5,#레벨
struct.pack_into('<I', d, BASE + 0x678EC, SP[3])                                     # 리터럴 풀의 종(원래 381)
sh(0x6782E, 0x2500 | LV[3])
# ② SpeciesToRoamerIdx
code = [0xB508,                        # push {r3,lr}
        0x2800 | SP[0], 0xD007,        # cmp r0,#s0 ; beq idx0
        0x2800 | SP[1], 0xD007,
        0x2800 | SP[2], 0xD007,
        0x2800 | SP[3], 0xD007,
        0x2004, 0xBD08,                # 아니면 4
        0x2000, 0xBD08, 0x2001, 0xBD08, 0x2002, 0xBD08, 0x2003, 0xBD08]
for i, v in enumerate(code): sh(0x678F0 + 2 * i, v)
open(A.out, 'wb').write(bytes(d))
print('떠돌이 종 %s 레벨 %s → %s' % (SP, LV, A.out))
