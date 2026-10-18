#!/usr/bin/env python3
r"""글 넘침 점검 (2026-10-16) — 이름·용어를 바꿔 원래보다 길어진 줄을 찾는다(대화 칸 밖으로 나가 잘리거나 겹칠 수 있음). 롬은 읽기만.
사용:   python 글_넘침.py <만든 롬.nds> --base "<원본 롬.nds>"     → 글_넘침.md, 끝줄 「글 넘침 후보 n줄」
기준:   같은 글 항목에서, 새 줄의 너비가 원본 항목의 가장 긴 줄보다 길고(+1칸 이상) 새 너비가 16칸 이상인 줄.
        너비: 한글·문장부호 1칸, 띄어쓰기·영숫자 0.5칸, 이름 같은 변수 6칸. (실제 칸 너비는 화면으로 확인 — 이 도구는 「후보」만)
고치는 법: NDS_용어표.tsv 의 새 이름을 짧게, 또는 NDS_장면대사.tsv 로 그 항목 글을 줄바꿈까지 손으로 다시 씀."""
import os, sys, re, csv, argparse
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import hg1
from hg1 import NDS, NARC, msg_decode
P = H if os.path.exists(os.path.join(H, 'NDS_종_초안.tsv')) else os.path.join(H, '..')

def load(path):
    rom = NDS(open(path, 'rb').read()); out = []
    for f in NARC(rom.get(hg1.NARC_PATHS['msg'])).files:
        try: out.append(msg_decode(f))
        except Exception: out.append((0, []))
    return out

def width(line):
    line = re.sub(r'\{FFFE\}(\{[0-9A-F]{4}\}){4}', '＊＊＊＊＊＊', line)
    line = line.replace('{01DE}', ' ')
    line = re.sub(r'\{[0-9A-F]{4}\}', '．', line)
    return sum(0.5 if (c == ' ' or c.isascii()) else 1 for c in line)

def lines(t): return re.split(r'\\[nrf]', t)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--base', required=True); ap.add_argument('--out', default='글_넘침.md'); ap.add_argument('--min', type=float, default=16)
    A = ap.parse_args()
    draft = {r['이름'] for r in csv.DictReader(open(os.path.join(P, 'NDS_종_초안.tsv'), encoding='utf-8'), delimiter='\t')}
    new, old = load(A.rom), load(A.base)
    CMn = hg1.infer_charmap(new, draft)[0]; CMo = CMn          # 같은 글꼴(같은 게임)이라 글자표 하나로
    rows = []
    for fi in range(min(len(new), len(old))):
        en, eo = new[fi][1], old[fi][1]
        for ei in range(min(len(en), len(eo))):
            if en[ei] == eo[ei]: continue
            try: tn, to = CMn.dec(en[ei]), CMo.dec(eo[ei])
            except Exception: continue
            omax = max((width(l) for l in lines(to)), default=0)
            for l in lines(tn):
                w = width(l)
                if w >= A.min and w >= omax + 1: rows.append((fi, ei, omax, w, l))
    L = ['# 글 넘침 후보 (글_넘침.py)', '', '> 원본보다 길어진 줄 %d — 화면에서 잘리거나 겹치는지 확인. 표: 글 묶음 / 항목 / 원래 가장 긴 줄 / 새 줄 너비 / 새 줄' % len(rows), '',
         '| msg | 항목 | 원래 | 새 | 줄 |', '|---|---|---|---|---|']
    for fi, ei, o, w, l in sorted(rows, key=lambda r: -(r[3] - r[2]))[:400]:
        L.append('| %d | %d | %g | %g | %s |' % (fi, ei, o, w, l.replace('{01DE}', ' ').replace('|', '/')[:80]))
    open(A.out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('글 넘침 후보 %d줄 → %s' % (len(rows), A.out))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
