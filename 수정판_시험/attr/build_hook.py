#!/usr/bin/env python3
"""디지몬 속성 상성 훅(Thumb) 어셈블러 — hg_attr.py 에 박아 둔 기계어(HOOK_CODE)를 다시 만들고 같은지 확인한다. (Claude 작성, 2026-10-18)
사용:   pip install keystone-engine capstone
        python 수정판_시험/attr/build_hook.py            → 어셈블 + 역어셈블 출력 + hg_attr.HOOK_CODE 와 비교
배경:   hg_attr.py 는 keystone 없이 돌도록 바이트를 그대로 갖고 있다. 이 파일은 그 바이트의 「원본 소스」다.
주의:   DS 의 CPU(ARM946E-S)는 ARMv5TE — Thumb 에서 낮은 레지스터끼리 `mov rd, rm`(0x46xx) 은 ARMv6 부터라 쓰지 않고 `adds rd, rm, #0` 을 쓴다."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); PROJ = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, PROJ)
import hg_attr as H

SRC = r'''
hook:
    push {r4, lr}
    ldr  r1, lit_bstat          @ ctx->battleStatus (ctx+0x213C)
    ldr  r1, [r5, r1]
    ldr  r2, lit_mask           @ IGNORE_TYPE_EFFECTIVENESS(1<<11) | IGNORE_TYPE_IMMUNITY(1<<15) = 고정 피해 기술
    tst  r1, r2
    bne  keep
    ldr  r1, [sp, #0x5C]        @ u32 *moveStatusFlag (호출자 [sp+0x54])
    ldr  r1, [r1]
    lsls r1, r1, #26            @ MOVE_STATUS_ONE_HIT_KO(1<<5) → 부호 비트
    bmi  keep
    ldr  r0, [sp, #0x58]        @ damage (호출자 [sp+0x50])
    cmp  r0, #0
    beq  keep
    adds r0, r7, #0             @ r7 = battlerIdAttacker
    bl   attr_of
    adds r4, r0, #0
    beq  keep
    adds r0, r6, #0             @ r6 = battlerIdTarget
    bl   attr_of
    cmp  r0, #0
    beq  keep
    subs r4, r4, r0             @ diff = att - def  (1 백신, 2 데이터, 3 바이러스)
    beq  keep
    ldr  r2, lit_param
    ldrb r1, [r2, #0]           @ 유리 배율 분자
    cmp  r4, #1                 @ 백신>바이러스(1-3=-2), 바이러스>데이터(3-2=1), 데이터>백신(2-1=1)
    beq  apply
    adds r3, r4, #2
    beq  apply
    ldrb r1, [r2, #1]           @ 불리 배율 분자
apply:
    ldr  r0, [sp, #0x58]
    muls r0, r1, r0
    ldrb r1, [r2, #2]           @ 분모
    bl   0x02253B7C             @ DamageDivide(num, den): 0 이 되면 ±1
    b    out
keep:
    ldr  r0, [sp, #0x58]
out:
    pop  {r4}
    pop  {r1}
    add  sp, #0x30              @ 덮어쓴 원래 명령 (ldr r0,[sp,#0x50]; add sp,#0x30) 대신
    bx   r1                     @ → 0x02252A3E: pop {r3-r7, pc}

attr_of:                        @ r0 = battler → r0 = 속성 0~3 (r1-r3 씀)
    movs r1, #0xC0
    muls r1, r0, r1
    adds r1, r5, r1
    ldr  r2, lit_mons           @ ctx->battleMons (ctx+0x2D40), species 는 u16 맨 앞
    ldrh r1, [r1, r2]
    lsrs r2, r1, #9             @ 종 512 이상 → 0
    bne  zero
    ldr  r2, lit_table
    lsrs r3, r1, #2
    ldrb r0, [r2, r3]
    lsls r1, r1, #30
    lsrs r1, r1, #29            @ (종 & 3) * 2
    lsrs r0, r0, r1
    movs r1, #3
    ands r0, r1
    bx   lr
zero:
    movs r0, #0
    bx   lr
    .short 0                    @ 문자 상수를 4바이트 줄에 맞춤(실행 안 됨; .align 은 Thumb-2 nop 0xBF00 을 넣어서 안 씀)
lit_bstat: .word 0x213C
lit_mask:  .word 0x8800
lit_param: .word 0x%08X
lit_mons:  .word 0x2D40
lit_table: .word 0x%08X
''' % (H.PARAM_ADDR, H.TABLE_ADDR)

def build():
    import keystone
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)
    src = '\n'.join(l.split('@')[0] for l in SRC.split('\n'))
    enc, _ = ks.asm(src, H.CODE_ADDR)
    code = bytes(enc)
    assert (H.CODE_ADDR + len(code) - 20) % 4 == 0, '문자 상수가 4바이트 줄에 안 맞음 — .short 0 을 빼거나 넣을 것'
    return code

def disasm(code, addr):
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for ins in md.disasm(code, addr): print('%08X  %-10s %s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

if __name__ == '__main__':
    code = build()
    disasm(code, H.CODE_ADDR)
    print('길이 %d바이트, 끝 0x%08X (한도 0x%08X)' % (len(code), H.CODE_ADDR + len(code), H.REGION_END))
    print('훅 자리 BL:', H.thumb_bl(H.HOOK_SITE, H.CODE_ADDR).hex())
    if code == H.HOOK_CODE: print('hg_attr.HOOK_CODE 와 같음')
    else: print('다름! hg_attr.HOOK_CODE 를 이것으로 바꿀 것:\n' + code.hex()); sys.exit(1)
