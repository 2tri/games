"""롬의 대사 모두 뽑기 → work/texts.json (+ work/texts.txt 읽기용)
  python3 texts.py [롬]
대사 = text 명령(0x00)으로 시작해 <DONE>/<PROMPT>/'@' 로 끝나는 덩어리. 스크립트가 가리키는 곳이 있어야 대사로 인정:
  writetext(4D 주소2) · jumptext(53 주소2) · jumptextfaceplayer(52 주소2) — 같은 뱅크
  farwritetext(4C 주소2 뱅크) · text_far(16 주소2 뱅크) — 다른 뱅크
나중에 고친 대사를 다시 넣을 때: 원래 자리에 들어가면 그대로, 길면 빈 뱅크로 옮기고 가리키는 곳을 모두 바꾼다 (put_text).
대사 원문은 디지몬스터 것이므로 work/ 에만 둔다."""
import collections, json, os, sys
import dmrom, krtext

END = {0x5e: '<DONE>', 0x5f: '<PROMPT>', 0x50: '@'}


def read_text(d, p, limit=600):
    """p = text 명령(0x00) 자리. 글자열을 끝까지 읽어 (끝 자리, 글자 수, 문자열) 또는 None"""
    if d[p] != 0x00: return None
    i, n, out = p + 1, 0, []
    while i < len(d) and i - p < limit:
        b = d[i]
        if b in END: return i, n, ''.join(out) + END[b]
        if 1 <= b <= 0x0b:
            ch = krtext.DEC2.get(bytes(d[i:i + 2]))
            if ch is None: return None
            out.append(ch); n += 1; i += 2; continue
        ch = krtext.DEC1.get(b)
        if ch is None: return None
        out.append(ch); i += 1
        if not ch.startswith('<'): n += 1
    return None


def refs_index(d):
    """(뱅크, 주소) → 가리키는 곳 목록"""
    idx = collections.defaultdict(list)
    for i in range(len(d) - 3):
        op = d[i]
        if op in (0x4d, 0x53, 0x52):
            ptr = d[i + 1] | d[i + 2] << 8
            if 0x4000 <= ptr < 0x8000: idx[(i // 0x4000, ptr)].append((i, op))
        elif op in (0x4c, 0x16):
            ptr = d[i + 1] | d[i + 2] << 8; bank = d[i + 3]
            if 0x4000 <= ptr < 0x8000 and 0 < bank < 0x80: idx[(bank, ptr)].append((i, op))
    return idx


def main(path):
    r = dmrom.Rom(path); d = bytes(r.d); idx = refs_index(d)
    out = []
    for (bank, ptr), rf in idx.items():
        p = dmrom.addr(bank, ptr)
        if p >= len(d): continue
        t = read_text(d, p)
        if not t or t[1] < 2: continue
        end, n, s = t
        out.append({'addr': p, 'end': end, 'bank': bank, 'refs': [[a, op] for a, op in rf], 'chars': n, 'text': s})
    out.sort(key=lambda o: o['addr'])
    json.dump(out, open(os.path.join(dmrom.WORK, 'texts.json'), 'w'), ensure_ascii=False, indent=0)
    with open(os.path.join(dmrom.WORK, 'texts.txt'), 'w') as f:
        for o in out: f.write('%06X  %s\n' % (o['addr'], o['text'].replace('<LINE>', ' / ').replace('<PARA>', ' // ').replace('<CONT>', ' / ')))
    words = collections.Counter()
    for o in out:
        for w in ('포켓몬', '몬스터볼', '오박사', '공박사', '트레이너', '체육관', '배지', '디지몬'):
            if w in o['text']: words[w] += 1
    print('대사 %d덩어리, 글자 %d자, 바이트 %d' % (len(out), sum(o['chars'] for o in out), sum(o['end'] - o['addr'] + 1 for o in out)))
    print('단어가 들어간 덩어리 수:', dict(words))
    print('뱅크 수:', len({o['bank'] for o in out}))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(dmrom.WORK, 'myver.gbc'))
