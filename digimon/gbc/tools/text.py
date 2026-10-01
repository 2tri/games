"""글자 모음·문자열 부호화.
바이트 부호: 00 끝 · 01 줄바꿈 · 02 다음 장(▼ 기다림) · 03 변수(다음 바이트) · 04 조사(다음 바이트)
           10~EF 글자 0~223 · F0~F7 + 바이트 = 글자 224~2271
한 줄 18칸(8px 고정 폭), 한 장 2줄 — 금판 글상자와 같음"""
import re

COLS = 18
VARS = {'kid': (0, 3), 'partner': (1, 5), 'comp': (2, 3), 'baby': (3, 4), 'rookie': (4, 4),
        's0': (5, 6), 's1': (6, 6), 'n0': (7, 3), 'm0': (8, 7), 'i0': (9, 6), 'n1': (10, 3), 'f0': (11, 7)}
JOSA = {'이/가': 0, '은/는': 1, '을/를': 2, '와/과': 3, '으로/로': 4}
JOSA_CHARS = '이가은는을를와과으로'


class Strings:
    def __init__(self):
        self.items = []; self.idx = {}; self.chars = {}

    def add(self, s):
        if s in self.idx: return self.idx[s]
        self.idx[s] = len(self.items); self.items.append(s)
        for ch in self.tokens_text(s): self.chars[ch] = self.chars.get(ch, 0) + 1
        return self.idx[s]

    @staticmethod
    def tokenize(s):
        """문자열 → [('c',글자) | ('v',이름) | ('j',조사) | ('n',) | ('f',)]"""
        out = []; i = 0
        while i < len(s):
            ch = s[i]
            if ch == '{':
                j = s.index('}', i); k = s[i + 1:j]
                if k in VARS: out.append(('v', k))
                elif k in JOSA: out.append(('j', k))
                else: raise ValueError('모르는 {%s} in %r' % (k, s))
                i = j + 1; continue
            if ch == '\n': out.append(('n',))
            elif ch == '\f': out.append(('f',))
            else: out.append(('c', ch))
            i += 1
        return out

    def tokens_text(self, s):
        return [t[1] for t in self.tokenize(s) if t[0] == 'c']

    def finalize(self, extra=''):
        """글자 번호: 많이 쓰는 글자부터 (1바이트 부호를 많이 쓰게)"""
        for ch in extra + JOSA_CHARS + '0123456789 ': self.chars[ch] = self.chars.get(ch, 0) + 1
        order = sorted(self.chars, key=lambda c: (-self.chars[c], c))
        self.charidx = {c: i for i, c in enumerate(order)}
        self.charlist = order
        return order

    # ── 줄 나누기 (단어 단위, 18칸) ──
    def layout(self, s):
        toks = self.tokenize(s)
        pages = [[]]; line = []; col = 0; lines = pages[-1]

        def width(tk):
            return 1 if tk[0] == 'c' else VARS[tk[1]][1] if tk[0] == 'v' else 1 if tk[0] == 'j' else 0

        # 단어 = 공백으로 나뉜 조각
        words = []; cur = []
        for tk in toks:
            if tk[0] in ('n', 'f'):
                if cur: words.append(cur); cur = []
                words.append([tk]); continue
            if tk == ('c', ' '):
                if cur: words.append(cur); cur = []
                words.append([tk]); continue
            cur.append(tk)
        if cur: words.append(cur)
        out_lines = []  # [(tokens, endkind)] endkind: 'n' 줄 / 'f' 장
        line = []; col = 0
        for w in words:
            if w[0][0] == 'n': out_lines.append((line, 'n')); line = []; col = 0; continue
            if w[0][0] == 'f': out_lines.append((line, 'f')); line = []; col = 0; continue
            if w == [('c', ' ')]:
                if col == 0: continue
                if col + 1 > COLS: out_lines.append((line, 'n')); line = []; col = 0; continue
                line.append(w[0]); col += 1; continue
            ww = sum(width(t) for t in w)
            if col + ww > COLS and col > 0:
                while line and line[-1] == ('c', ' '): line.pop()
                out_lines.append((line, 'n')); line = []; col = 0
            for t in w:
                if col + width(t) > COLS: out_lines.append((line, 'n')); line = []; col = 0
                line.append(t); col += width(t)
        out_lines.append((line, 'end'))
        # 2줄마다 장 넘김
        res = []; n = 0
        for k, (ln, end) in enumerate(out_lines):
            if n == 2: res.append(('f',)); n = 0
            res += ln; n += 1
            if end == 'f': n = 2
            if k < len(out_lines) - 1 and n == 1 and end != 'f': res.append(('n',))
        return res

    def encode(self, s, wrap=True):
        toks = self.layout(s) if wrap else self.tokenize(s)
        b = []
        for t in toks:
            if t[0] == 'c':
                i = self.charidx[t[1]]
                if i < 224: b.append(0x10 + i)
                else: i -= 224; b += [0xF0 + (i >> 8), i & 255]
            elif t[0] == 'n': b.append(1)
            elif t[0] == 'f': b.append(2)
            elif t[0] == 'v': b += [3, VARS[t[1]][0]]
            elif t[0] == 'j': b += [4, JOSA[t[1]]]
        b.append(0)
        return b


def batchim(ch):
    """받침 여부(bit0), ㄹ받침(bit1). 숫자는 읽는 소리 기준"""
    if ch in '178': return 3          # 일·칠·팔
    if ch in '036': return 1          # 영·삼·육
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3:
        j = (o - 0xAC00) % 28
        return 0 if j == 0 else (3 if j == 8 else 1)
    return 0
