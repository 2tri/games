#!/usr/bin/env python3
"""보고 모으기 (2026-10-14) — 집에서 돌린 결과 파일을 「보고_모음.txt」 하나로 이어 붙인다(손으로 모으지 않게).
사용:   python 모아보고.py        → 보고_모음.txt (없는 파일은 「(없음)」으로 적음 → 무엇이 빠졌는지도 보고가 됨)
작업일지.txt 와 그림자리.md([10b] 결과 표)는 집 Claude 가 먼저 써 둔다."""
import os, sys, glob

def rd(p):
    try: return open(p, encoding='utf-8', errors='replace').read()
    except OSError: return None

def lines_with(p, words):
    t = rd(p)
    return None if t is None else '\n'.join(l for l in t.split('\n') if any(w in l for w in words))

def head(p, n):
    t = rd(p)
    return None if t is None else '\n'.join(t.split('\n')[:n])

def find_tool(name):
    hits = [h for h in glob.glob('**/' + name, recursive=True) if 'node_modules' not in h]
    return min(hits, key=len) if hits else None

ITEMS = [
    ('작업일지.txt', lambda: rd('작업일지.txt')),
    ('그림자리.md ([10b] 결과 표)', lambda: rd('그림자리.md')),
    ('hg1_out/report.txt (표 위치·직업 앞 20)', lambda: lines_with('hg1_out/report.txt', ('== 표 위치', '직업 앞 20', '표 위치'))),
    ('hg1_out/classes.tsv', lambda: rd('hg1_out/classes.tsv')),
    ('hg2_out/report.txt', lambda: rd('hg2_out/report.txt')),
    ('hg3_out/report.txt', lambda: rd('hg3_out/report.txt')),
    ('hg4_out/report.txt', lambda: rd('hg4_out/report.txt')),
    ('hg4i_out/report.txt (앞 10줄)', lambda: head('hg4i_out/report.txt', 10)),
    ('hg_ev_out 또는 hg_event 보고', lambda: rd('hg_ev_out/report.txt') or rd('hg_event_보고.txt')),
    ('hg4f_out/report.txt', lambda: rd('hg4f_out/report.txt')),
    ('hg4t_out/report.txt', lambda: rd('hg4t_out/report.txt')),
    ('흔적_조사.txt (앞 40줄)', lambda: head('흔적_조사.txt', 40)),
    ('balance_report.txt', lambda: rd('balance_report.txt')),
    ('nds_art/보고.txt (그림 없음·실패·회색)', lambda: lines_with('nds_art/보고.txt', ('그림 없음', '실패', '회색'))),

    ('wikimon_속성.tsv (못 찾음)', lambda: lines_with('wikimon_속성.tsv', ('못 찾음',))),
    ('hg1_out/trainers.tsv (기모노·무희·간부·엘리트)', lambda: lines_with('hg1_out/trainers.tsv', ('기모노', '무희', '간부', '엘리트'))),
    ('2부대사_결과.md', lambda: rd('2부대사_결과.md')),
    ('2부대사_검사.txt', lambda: rd('2부대사_검사.txt')),
    # 10/15: 소리 목록(sdat_목록 6천 줄)은 이미 받아 둠 → 빼고, 노래 배정은 요약 줄만(보고가 50만 자 넘던 원인의 절반)
    ('노래_배정결과.txt (요약)', lambda: lines_with('노래_배정결과.txt', ('==', '[', '만듦', '넣음 ', 'MIDI 없음', '경고', '→ ', '악기 시험'))),
    ('악기표.txt', lambda: rd('악기표.txt')),
    ('피아노_고른것.txt', lambda: rd('피아노_고른것.txt')),
    ('피아노_맞춤.txt', lambda: rd('피아노_맞춤.txt')),
    ('야생_지명.tsv', lambda: rd('야생_지명.tsv')),
    ('실마리_후보.txt', lambda: rd('실마리_후보.txt')),
    ('실마리_찾기.txt (앞 300줄)', lambda: head('실마리_찾기.txt', 300)),
]
TOOLS = ('inject_front.py', 'inject_back.py', 'inject_walk.py', 'lz10.py', 'ds_mchr.py', 'emu_run.py', 'encounters.py')

def main():
    out = []; miss = []
    for name, fn in ITEMS:
        try: t = fn()
        except Exception as e: t = '(읽기 오류 %s)' % e
        if t is None: miss.append(name); t = '(없음)'
        out.append('=== %s ===\n%s\n' % (name, t.rstrip()))
    for tn in TOOLS + tuple(os.path.basename(p) for p in glob.glob('inject_*.py') + glob.glob('*_넣기*.py') + glob.glob('put_*.py')):
        p = find_tool(tn)
        import time
        if p and os.path.getmtime(p) < time.time() - 20 * 3600: out.append('=== 도구 %s (%s) — 어제와 같음(원본 생략) ===\n' % (tn, p)); continue   # 10/15: 바뀐 도구만 원본을 붙임
        if p and ('=== 도구 %s' % tn) not in ''.join(out): out.append('=== 도구 %s (%s) ===\n%s\n' % (tn, p, rd(p).rstrip()))
        elif not p: miss.append('도구 ' + tn)
    # 10/15: 설계자가 먼저 볼 「핵심 줄」을 보고 맨 위에 — 확인 항목마다 찾은 줄(없으면 「없음」)
    KEY = [('스타팅 표', 'hg4i_out/report.txt', '스타팅 표'), ('상점 표', 'hg4i_out/report.txt', '일반 상점 표'), ('알 그림', 'hg4_out/report.txt', '알 그림'),
           ('색 검산', 'hg4_out/report.txt', '색 검산'), ('트레이너 글 표', 'hg3_out/report.txt', '트레이너 글 표'), ('전투 글', 'hg3_out/report.txt', '전투 글('),
           ('장면 대사', 'hg3_out/report.txt', '장면 대사:'), ('도구 이름 번호', 'hg3_out/report.txt', '도구 이름 번호'), ('도구 설명', 'hg3_out/report.txt', '도구 설명 바꿈'),
           ('야생 규칙', 'hg3_out/report.txt', '야생 규칙으로'), ('빛의 무녀', 'hg3_out/report.txt', '무녀'), ('주요 트레이너', 'hg3_out/report.txt', '주요 트레이너'),
           ('필살기', 'hg2_out/report.txt', '필살기'), ('진화 못 찾음', 'hg2_out/report.txt', '값을 롬에서 못 찾음'), ('선물 도구', 'hg_ev_out/report.txt', '선물 도구'),
           ('관동 연구소', 'hg_ev_out/report.txt', '관동 스타팅'), ('빌', 'hg_ev_out/report.txt', '빌('), ('도구 값', 'hg_ev_out/report.txt', '도구 값'),
           ('노래 검사', '노래_배정결과.txt', '검사 실패'), ('롬 검사', '롬검사.txt', '검사 '), ('걷기 그림 출처', 'nds_art/보고.txt', '데리고 다니는 그림 출처'), ('포켓몬 흔적', '롬검사.txt', '흔적'), ('그림 안 바뀜', '롬검사.txt', '그림 안 바뀜'), ('걷기 전수', '걷기_전수.md', '== 결과')]
    kl = ['=== 핵심 줄(설계자가 먼저 봄) ===']
    for nm, f, w in KEY:
        t = rd(f); hits = [l.strip() for l in (t or '').split('\n') if w in l][:6]
        kl.append('[%s] %s' % (nm, ' / '.join(hits) if hits else ('(파일 없음)' if t is None else '없음')))
    out.insert(0, '\n'.join(kl) + '\n')
    # 10/15: 「못 함·못 찾음·일부만」 줄을 맨 위로 — 설계자가 놓치지 않게(사용자: 「내가 안 물어봤으면 어쩌려고」)
    OPEN_W = ('열린 일:', '못 찾', '못 봄', '못 넣', '못 함', '못 감', '확인 못', '시간이 모자', '시간 안에', '일부만', '건너뜀', '완성 조건 실패')
    ol = []
    for f in ('작업일지.txt', '롬검사.txt', 'nds_art/보고.txt', 'hg_ev_out/report.txt', 'hg3_out/report.txt', 'hg4f_out/report.txt', '걷기_전수.md', '전종_확인.md'):
        t = rd(f)
        if t: ol += ['[%s] %s' % (f, l.strip()[:220]) for l in t.split('\n') if any(w in l for w in OPEN_W) and '실패 0' not in l]
    out.insert(0, '=== 열린 일 후보(설계자가 열린일.md 에 옮길 것) %d줄 ===\n%s\n' % (len(ol), '\n'.join(ol[:150])))
    out.insert(0, '=== 모으기 요약 ===\n없는 것 %d: %s\n' % (len(miss), ', '.join(miss)))
    open('보고_모음.txt', 'w', encoding='utf-8').write('\n'.join(out))
    print('→ 보고_모음.txt (%d바이트). 없는 것: %s' % (os.path.getsize('보고_모음.txt'), ', '.join(miss) or '없음'))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
