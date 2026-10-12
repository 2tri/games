"""난이도 (7판, 설계자 2026-10-06): 환경 변수 DIFF=easy|normal|hard 로 빌드하면
 · 트레이너 파티 레벨 × rules.DIFF_LEVEL (0.9 / 1.0 / 1.15, 2~100 사이로)
 · 야생(풀숲·물) 레벨 × 같은 비율
 · 포획률 × rules.DIFF_CATCH (1.5 / 1.0 / 0.7, 0 은 0 그대로, 1~255)
 · 완전체 배지 수는 rules.BADGES_COMPLETE 가 DIFF 에 따라 2 / 3 / 4 (진화 코드는 rules 값을 읽으므로 자동)
patch.build 맨 끝(story2 다음)에 `import diff7; P.log += diff7.apply(P)`. normal 이면 아무것도 안 바꿈
빌드: DIFF=easy python3 -c "import patch,dmrom; patch.build(dmrom.default_rom(),'work/myver_easy.gbc','work/myver_easy.ips')" (hard 도 같이)"""
import os, re
import dmrom, encounters, rules


def apply(P):
    f, c = rules.DIFF_LEVEL, rules.DIFF_CATCH
    add = getattr(rules, 'DIFF_LEVEL_ADD', 0)
    KO = {'easy': '이지', 'normal': '노말', 'hard': '하드'}
    if f == 1.0 and c == 1.0 and add == 0:
        return ['난이도: 노말 (바꾼 것 없음)']
    P.r.d = P.d
    log = []
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(encounters.KR, 'data/trainers/party_pointers.asm')).read())
    nt = 0
    for t in P.r.trainers(len(groups)):
        for lv, sp, a in t['mons']:
            P.d[a - 1] = max(2, min(100, int(round(lv * f)) + add))
            nt += 1
    nw = 0
    for s in encounters.find_all(dmrom.Rom(dmrom.default_rom())):
        if s['kind'] in ('풀숲', '물'):
            lv = P.d[s['addr'] - 1]
            if 1 <= lv <= 100:
                P.d[s['addr'] - 1] = max(2, min(100, int(round(lv * f)) + add))
                nw += 1
    nc = 0
    for n in range(1, dmrom.NUM + 1):
        e = P.r.bs + 0x20 * (n - 1) + 9
        cr = P.d[e]
        if cr:
            P.d[e] = max(1, min(255, int(round(cr * c))))
            nc += 1
    log.append('난이도 %s: 트레이너 레벨 ×%.2f%+d %d칸, 야생 레벨 ×%.2f%+d %d칸, 포획률 ×%.2f %d종, 완전체 문장 %d' % (
        KO.get(rules.DIFFICULTY, rules.DIFFICULTY), f, add, nt, f, add, nw, c, nc, rules.BADGES_COMPLETE))
    return log
