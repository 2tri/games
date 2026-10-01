"""이야기 스크립트·지도 정의 도구 → 바이트코드
스크립트는 명령 목록. Label('이름') 으로 자리 표시, 점프는 그 이름으로."""

OPS = ['END', 'SAY', 'ASK', 'JMP', 'JF', 'JNF', 'JNO', 'SETF', 'CLRF', 'CLOSE', 'FLASH', 'FADEOUT', 'FADEIN',
       'WARP', 'GIVEMON', 'GIVEITEM', 'GIVEEGG', 'HEAL', 'SETHEAL', 'PIC', 'PICOFF', 'EVOLVE', 'BATTLE', 'CREST',
       'WAIT', 'JKID', 'PICKKID', 'SHAKE', 'FACE', 'SFX']
OP = {n: i for i, n in enumerate(OPS)}

# 특수 디지몬 번호
SP_BABY, SP_ROOKIE, SP_LEAD, SP_NONE = 0xFF, 0xFE, 0xFD, 0xF0

FLAGS = {}


def flag(name):
    if name not in FLAGS: FLAGS[name] = len(FLAGS)
    return FLAGS[name]


class Label:
    def __init__(self, name): self.name = name


def Say(t): return ('SAY', t)
def Ask(t): return ('ASK', t)
def Jmp(l): return ('JMP', l)
def IfFlag(f, l): return ('JF', f, l)          # 깃발이 서 있으면 l 로
def IfNotFlag(f, l): return ('JNF', f, l)
def IfNo(l): return ('JNO', l)                  # 바로 앞 결과(예/아니오·전투)가 아니오/짐이면 l 로
def SetFlag(f): return ('SETF', f)
def ClrFlag(f): return ('CLRF', f)
def Close(): return ('CLOSE',)
def Flash(n=1): return ('FLASH', n)
def FadeOut(white=False): return ('FADEOUT', 1 if white else 0)
def FadeIn(): return ('FADEIN',)
def Warp(m, x, y, d='down'): return ('WARP', m, x, y, d)
def GiveMon(sp, lv): return ('GIVEMON', sp, lv)
def GiveItem(it, n=1): return ('GIVEITEM', it, n)
def GiveEgg(): return ('GIVEEGG',)
def Heal(): return ('HEAL',)
def SetHeal(m, x, y, d='up'): return ('SETHEAL', m, x, y, d)
def Pic(sp): return ('PIC', sp)
def PicOff(): return ('PICOFF',)
def Evolve(to, lv): return ('EVOLVE', to, lv)
def Battle(sp, lv, kind='boss'): return ('BATTLE', sp, lv, kind)
def Crest(c): return ('CREST', c)
def Wait(n): return ('WAIT', n)
def IfKid(k, l): return ('JKID', k, l)
def PickKid(): return ('PICKKID',)
def Shake(n=6): return ('SHAKE', n)
def End(): return ('END',)


class NPC:
    def __init__(self, x, y, spr, dir='down', script=None, show_if=None, hide_if=None, hide_kid=None, fixed=False):
        self.x, self.y, self.spr, self.dir, self.script = x, y, spr, dir, script
        self.show_if, self.hide_if, self.hide_kid, self.fixed = show_if, hide_if, hide_kid, fixed


class Sign:
    def __init__(self, x, y, script): self.x, self.y, self.script = x, y, script


class Trigger:
    def __init__(self, x, y, w, h, script, once=None, need=None, unless=None):
        self.x, self.y, self.w, self.h, self.script, self.once, self.need, self.unless = x, y, w, h, script, once, need, unless


class Warp_:
    def __init__(self, x, y, to, tx, ty, dir=None): self.x, self.y, self.to, self.tx, self.ty, self.dir = x, y, to, tx, ty, dir


def edge(xs, y, to, tx0, ty):
    return [Warp_(x, y, to, tx0 + i, ty) for i, x in enumerate(xs)]


def edgeV(x, ys, to, tx, ty0):
    return [Warp_(x, y, to, tx, ty0 + i) for i, y in enumerate(ys)]


class Map:
    def __init__(self, name, rows, key, border, objs=(), npcs=(), signs=(), warps=(), triggers=(), enc=None, on_enter=None,
                 open=(), border_fn=None):
        self.name, self.rows, self.key, self.border = name, rows, key, border
        self.objs, self.npcs, self.signs, self.warps, self.triggers = list(objs), list(npcs), list(signs), list(warps), list(triggers)
        self.enc, self.on_enter, self.open, self.border_fn = enc, on_enter, list(open), border_fn


def assemble(scripts, ctx):
    """scripts: [명령목록,...] → (바이트, 각 시작 위치). ctx: 번호 바꾸는 함수들"""
    blob = []; starts = []; fix = []
    for si, sc in enumerate(scripts):
        starts.append(len(blob)); labels = {}
        for item in list(sc) + [End()]:
            if isinstance(item, Label): labels[item.name] = len(blob); continue
            op = item[0]; a = item[1:]; blob.append(OP[op])
            if op in ('SAY', 'ASK'): sid = ctx['str'](a[0]); blob += [sid & 255, sid >> 8]
            elif op == 'JMP' or op == 'JNO': fix.append((len(blob), si, a[0])); blob += [0, 0]
            elif op in ('JF', 'JNF'): f = flag(a[0]); blob += [f & 255, f >> 8]; fix.append((len(blob), si, a[1])); blob += [0, 0]
            elif op in ('SETF', 'CLRF'): f = flag(a[0]); blob += [f & 255, f >> 8]
            elif op in ('FLASH', 'FADEOUT', 'WAIT', 'SHAKE'): blob.append(a[0])
            elif op == 'WARP': blob += [ctx['map'](a[0]), a[1] & 255, a[2] & 255, ctx['dir'](a[3])]
            elif op == 'GIVEMON': blob += [ctx['sp'](a[0]), a[1]]
            elif op == 'GIVEITEM': blob += [ctx['item'](a[0]), a[1]]
            elif op == 'SETHEAL': blob += [ctx['map'](a[0]), a[1], a[2], ctx['dir'](a[3])]
            elif op == 'PIC': blob.append(ctx['sp'](a[0]))
            elif op == 'EVOLVE': blob += [ctx['sp'](a[0]), a[1]]
            elif op == 'BATTLE': blob += [ctx['sp'](a[0]), a[1], {'wild': 0, 'boss': 1}[a[2]]]
            elif op == 'CREST': blob.append(ctx['crest'](a[0]))
            elif op == 'JKID': blob.append(ctx['kid'](a[0])); fix.append((len(blob), si, a[1])); blob += [0, 0]
            elif op in ('END', 'CLOSE', 'FADEIN', 'GIVEEGG', 'HEAL', 'PICOFF', 'PICKKID'): pass
            else: raise ValueError(op)
        for (pos, s2, name) in [f for f in fix if f[1] == si]:
            if name not in labels: raise ValueError('라벨 없음: ' + name)
            blob[pos] = labels[name] & 255; blob[pos + 1] = labels[name] >> 8
    return blob, starts
