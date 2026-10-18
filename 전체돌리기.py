#!/usr/bin/env python3
r"""롬 전체 만들기 — 단계마다 롬 검사(rom_check)까지 한 번에. (2026-10-16, 회사 설계 세션 마지막 날 작성)
사용:   python 전체돌리기.py --rom "디지몬골드 v1.6 (이지).nds"
        python 전체돌리기.py --rom "<롬>" --from hg4          ← 그 단계부터 다시(앞 단계 결과 파일이 있어야 함)
        python 전체돌리기.py --rom "<롬>" --specials-mode reuse ← 필살기 칸이 모자라다고 나올 때만(1~2종 기술을 롬에서 더 바꿈)
단계: art(그림) → hg2 → hg3 → hg4 → icons → event → follow → trainer → 집도구 → hard → song
- 「집도구」: 집 PC 에만 있는 네 도구(태일·나리·도구 아이콘·타이틀·배지·떠돌이)를 부르는 집도구.py 가 이 폴더에 있으면
  python 집도구.py <입력 롬> <출력 롬> 으로 부른다(네가 한 번 만들어 두면 됨). 없으면 그 단계는 건너뛰고 trainer 결과를 그대로 최종_오늘.nds 로.
- 롬 검사: 「검사 실패」면 멈춘다. 「완성 조건 실패(흔적)」는 기록만 하고 계속.
- 기록: 돌리기_기록.txt (단계 · 걸린 초 · 검사 끝줄 · 각 보고의 핵심 줄)"""
import os, sys, time, shutil, subprocess, argparse

H = os.path.dirname(os.path.abspath(__file__))
def py(*a): return [sys.executable, os.path.join(H, a[0])] + list(a[1:])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', required=True)
    ap.add_argument('--art-dirs', default='dsw_ow,그림_보충,games/images/digimon,games/digimon/art/src,games/digimon/art', help='그림 폴더(쉼표, 앞이 우선)')
    ap.add_argument('--people', default='games/digimon/art/src/people', help='트레이너 그림 폴더(none = 건너뜀)')
    ap.add_argument('--paltab', default='arm9:0x10023B')
    ap.add_argument('--specials-mode', default='free', choices=('reuse', 'free'))
    ap.add_argument('--from', dest='start', default='art')
    ap.add_argument('--stop', default='song')
    ap.add_argument('--no-song', action='store_true'); ap.add_argument('--no-hard', action='store_true')
    A = ap.parse_args()
    R = A.rom
    steps = [
        ('art', py('art_nds.py', *[d for d in A.art_dirs.split(',') if d], '--out', 'nds_art'), None),
        ('hg2', py('hg2.py', R, '--specials-mode', A.specials_mode), 'hg2_out/hg2_test.nds'),
        ('hg3', py('hg3.py', 'hg2_out/hg2_test.nds', '--base', R), 'hg3_out/hg3_test.nds'),
        ('hg4', py('hg4.py', 'hg3_out/hg3_test.nds', 'nds_art', '--base', R), 'hg4_out/hg4_test.nds'),
        ('icons', py('hg4_icons.py', 'hg4_out/hg4_test.nds', 'nds_art', '--base', R, '--paltab', A.paltab, '--dex-order', next((q for q in (os.path.join(H, 'NDS_도감순서.tsv'), os.path.join(H, '..', 'NDS_도감순서.tsv')) if os.path.exists(q)), 'NDS_도감순서.tsv')), 'hg4i_out/hg4i_test.nds'),
        ('event', py('hg_event.py', 'hg4i_out/hg4i_test.nds', '--base', R, '--apply'), 'hg_ev_out/hg_ev_test.nds'),
        ('follow', py('hg4_follow.py', 'hg_ev_out/hg_ev_test.nds', 'nds_art', '--base', R), 'hg4f_out/hg4f_test.nds'),
        ('trainer', py('hg4_trainer.py', 'hg4f_out/hg4f_test.nds', A.people, '--base', R) if A.people != 'none' else None, 'hg4t_out/hg4t_test.nds'),
        ('집도구', 'HOME', '최종_오늘.nds'),
        ('hard', py('hg_hard.py', '최종_오늘.nds', '--out', '최종_하드.nds') if not A.no_hard else None, '최종_하드.nds'),
        ('song', 'SONG', '최종_노래.nds'),
    ]
    names = [s[0] for s in steps]
    if A.start not in names or A.stop not in names: sys.exit('실패: --from/--stop 은 %s 중 하나' % names)
    i0, i1 = names.index(A.start), names.index(A.stop)
    log = open('돌리기_기록.txt', 'a', encoding='utf-8')
    def say(*a):
        t = ' '.join(str(x) for x in a); print(t); log.write(t + '\n'); log.flush()
    say('\n== 전체돌리기 %s  롬=%s  %s→%s  필살기=%s' % (time.strftime('%m/%d %H:%M'), R, A.start, A.stop, A.specials_mode))
    last_rom = None
    def check(out):
        r = subprocess.run(py('rom_check.py', out, '--base', R, '--quiet'), capture_output=True, text=True, encoding='utf-8', errors='replace')
        tail = (r.stdout.strip().split('\n') or [''])[-1]
        say('   검사:', tail)
        if '검사 실패' in tail:
            say('   ★ 멈춤: 롬 검사 실패 — 위 줄과 롬검사.txt 를 보고 고친 뒤 --from 으로 다시'); sys.exit(1)
    for name, cmd, out in steps[i0:i1 + 1]:
        t0 = time.time()
        if cmd is None:
            say('[%s] 건너뜀' % name); continue
        if cmd == 'HOME':
            src = 'hg4t_out/hg4t_test.nds' if os.path.exists('hg4t_out/hg4t_test.nds') else 'hg4f_out/hg4f_test.nds'
            if os.path.exists('집도구.py'):
                r = subprocess.run([sys.executable, '집도구.py', src, out])
                if r.returncode: say('[집도구] 실패(종료 코드 %d) — 집도구.py 를 고친 뒤 --from 집도구' % r.returncode); sys.exit(1)
            else:
                shutil.copyfile(src, out); say('[집도구] 집도구.py 없음 — %s 를 그대로 %s 로(태일·나리·도구 아이콘·타이틀·배지·떠돌이 없음!)' % (src, out))
            check(out); last_rom = out; continue
        if cmd == 'SONG':
            if A.no_song: say('[song] 건너뜀'); continue
            for a, b in (('최종_오늘.nds', '최종_노래.nds'), ('최종_하드.nds', '최종_하드_노래.nds')):
                if not os.path.exists(a): continue
                r = subprocess.run(py('hg_song.py', a, '--out', b))
                say('[song] %s → %s 종료 코드 %d (%.0f초)' % (a, b, r.returncode, time.time() - t0))
                if r.returncode: sys.exit(1)
                if not os.path.exists(b): say('   ★ %s 를 안 만듦 — 노래 파일(노래 폴더·노래_링크.txt)이 없거나 바꿀 곡이 없음. 노래가 있어야 하면 hg_song 출력을 보고' % b); continue
                check(b)
            continue
        r = subprocess.run(cmd)
        say('[%s] 종료 코드 %d (%.0f초)' % (name, r.returncode, time.time() - t0))
        if r.returncode: say('   ★ 멈춤: 이 단계가 실패 — 출력 마지막 줄들을 보고 고친 뒤 --from %s' % name); sys.exit(1)
        if out: check(out); last_rom = out
    # 10/16: 끝난 롬을 두 기준으로 점검(보고만) — 기술(초반 위력·진화 뒤·물리/특수 …) · 야생(물가·단계·반복·얻을 길)
    fin = next((q for q in ('최종_노래.nds', '최종_오늘.nds') if os.path.exists(q)), None)
    if fin and os.path.exists('hg2_out/칸표.tsv'):
        for tool in ('기술_점검.py', '야생_검토.py', '글_넘침.py'):
            if os.path.exists(os.path.join(H, tool)):
                r = subprocess.run(py(tool, fin, *(('--base', R) if tool == '글_넘침.py' else ())), capture_output=True, text=True, encoding='utf-8', errors='replace')
                say('[점검] %s: %s' % (tool, (r.stdout.strip().split(chr(10)) or [''])[-1] if r.returncode == 0 else '실패 ' + r.stderr.strip()[-300:]))
    say('== 끝. 최종_오늘·최종_하드·최종_노래·최종_하드_노래 (만든 것만)')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
