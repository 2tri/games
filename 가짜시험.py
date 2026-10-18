#!/usr/bin/env python3
r"""가짜 롬 자동 시험 — 스크립트·표를 고친 뒤 진짜 롬에 돌리기 전에 「도구가 끝까지 도는지」를 1~2분에 확인. (2026-10-16)
사용:   python 가짜시험.py            → 가짜시험\ 폴더를 새로 만들어 그 안에서: 가짜 롬(test_fake_rom.py) + 가짜 그림 188장 → 전체돌리기(그림~follow, hard)
                                         → 끝줄 「가짜 시험 통과」 또는 「가짜 시험 실패」
주의:   가짜 롬은 진짜 롬의 「꼴」만 흉내 낸 것이다. 통과해도 게임 화면이 맞는지는 모른다(진짜 롬 + 에뮬레이터로 따로 확인).
        Pillow 필요(python -m pip install pillow)."""
import os, sys, shutil, subprocess, random
H = os.path.dirname(os.path.abspath(__file__))

def main():
    from PIL import Image, ImageDraw
    work = os.path.join(os.getcwd(), '가짜시험')
    if os.path.isdir(work): shutil.rmtree(work)
    os.makedirs(os.path.join(work, 'fakeart'))
    os.chdir(work)
    r = subprocess.run([sys.executable, os.path.join(H, 'test_fake_rom.py'), 'fake.nds'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); print('가짜 시험 실패: 가짜 롬을 못 만듦'); sys.exit(1)
    tp = next(q for q in (os.path.join(H, 'NDS_종_초안.tsv'), os.path.join(H, '..', 'NDS_종_초안.tsv')) if os.path.exists(q))
    names = [l.split('\t')[2] for l in open(tp, encoding='utf-8').read().split('\n')[1:] if l.count('\t') > 3]
    random.seed(2)
    for n in names:                                   # 종마다 다른 색의 가짜 그림(흰 배경, 검은 외곽선)
        im = Image.new('RGB', (120, 120), (255, 255, 255)); d = ImageDraw.Draw(im)
        c = (random.randint(120, 230), random.randint(20, 100), random.randint(20, 230))
        d.ellipse((20, 15, 100, 110), fill=c, outline=(0, 0, 0)); d.rectangle((45, 40, 75, 55), fill=(250, 250, 250)); d.ellipse((30, 90, 50, 115), fill=(c[2], c[0], c[1]))
        im.save(os.path.join('fakeart', '%s_앞.png' % n))
    r = subprocess.run([sys.executable, os.path.join(H, '전체돌리기.py'), '--rom', 'fake.nds', '--art-dirs', 'fakeart', '--people', 'none', '--paltab', 'arm9:0x500',
                        '--no-song', '--stop', 'hard'])
    ok = r.returncode == 0 and os.path.exists('최종_하드.nds')
    print('가짜 시험 %s (자세히: 가짜시험\\돌리기_기록.txt, 각 *_out\\report.txt)' % ('통과' if ok else '실패'))
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
