"""작업팩 S8 — 진화 장면 (S7 판정 2026-10-06)
  8-1 글: 시작 「○○몬 진화…!」(금 「…… 오잉!? ○○의 상태가……!」) → 끝 「△△몬!!」(금 「축하합니다! ○○는(은) / △△(으)로 진화했다!」)
      「축하합니다!」 줄은 비우고(그때는 새 종 이름이 아직 버퍼에 없음), 진화 뒤 글을 한 줄로
  8-2 깜빡임이 끝나고 새 그림으로 바뀌는 순간: 팔레트 전부 흰색(금 ClearPalettes) 1프레임 → 진화 팔레트로 되돌림 → 새 그림
  8-3 B 로 멈추기·길이는 금 그대로 (코드 안 건드림)
주소는 원본 금 심볼(romanat.Sym)로 찾고 바이트를 확인한 뒤 고침."""
import re, struct
import krtext
from dmrom import addr

BUF1, BUF2 = 0xd036, 0xd04b             # wStringBuffer1(새 종 이름) · wStringBuffer2(진화 전 별명)


def _expect(P, a, want, what):
    got = bytes(P.d[a:a + len(want)])
    assert got == want, '%s: %X 바이트가 다름 %s ≠ %s' % (what, a, got.hex(' '), want.hex(' '))


def apply(P):
    import romanat
    S = romanat.Sym(); log = []
    # 8-1 글 (text_far 대상, 같은 자리에 짧게 다시 씀)
    ev, cg, ei = S['_EvolvingText'], S['_CongratulationsYourPokemonText'], S['_EvolvedIntoText']
    _expect(P, ev, bytes([0x00]) + krtext.encode_text('…… 오잉!?<LINE>') + b'\x50' + bytes([0x01, BUF2 & 255, BUF2 >> 8]), '진화 시작 글')
    _expect(P, cg, bytes([0x00]) + krtext.encode('축하합니다! '), '축하합니다 글')
    _expect(P, ei, bytes([0x00]) + krtext.encode_text('<LINE>') + b'\x50' + bytes([0x01, BUF1 & 255, BUF1 >> 8]), '진화 끝 글')
    done = krtext.encode_text('<DONE>')
    P.put(ev, bytes([0x01, BUF2 & 255, BUF2 >> 8, 0x00]) + krtext.encode(' 진화…!') + done)     # 「○○몬 진화…!」
    P.put(cg, bytes([0x00]) + done)                                                              # 빈 글
    P.put(ei, bytes([0x01, BUF1 & 255, BUF1 >> 8, 0x00]) + krtext.encode('!!') + done)          # 「△△몬!!」
    log.append('8-1 진화 글: 「○○ 진화…!」 → 「△△!!」 (축하합니다 줄 비움)')
    # 8-2 흰색 1프레임: 깜빡임 끝 → 「ld a, 7*7 / ld [wEvolutionPicOffset], a / call .ReplaceFrontpic」 의 call 을 작은 함수로
    ea = S['EvolutionAnimation']; bank = ea // 0x4000
    rf = S['EvolutionAnimation.ReplaceFrontpic'] % 0x4000 + 0x4000
    gl = S['EvolutionAnimation.GetSGBLayout'] % 0x4000 + 0x4000
    lp = S['EvolutionAnimation.loop']
    seg = bytes(P.d[lp:lp + 0x30])
    m = re.search(rb'\x3e\x31\xea..\xcd' + re.escape(struct.pack('<H', rf)), seg, re.S)
    assert m, '진화 마지막 그림 바꾸기 호출'
    cp, df = S['ClearPalettes'], S['DelayFrame']
    code = bytes([0xcd, cp & 255, cp >> 8,            # call ClearPalettes  (팔레트 전부 흰색, 다음 vblank 에 반영)
                  0xcd, df & 255, df >> 8,            # call DelayFrame     (흰 화면 1프레임)
                  0x0e, 0x01,                         # ld c, TRUE
                  0xcd, gl & 255, gl >> 8,            # call .GetSGBLayout  (깜빡일 때 쓰던 진화 팔레트로 되돌림)
                  0xc3, rf & 255, rf >> 8])           # jp .ReplaceFrontpic (새 그림)
    b, p = P.sp.take(len(code), bank=bank); P.put(addr(b, p), code)
    P.put(lp + m.end() - 2, struct.pack('<H', p))
    log.append('8-2 흰색 1프레임: 뱅크 %02X:%04X %d바이트' % (b, p, len(code)))
    return log
