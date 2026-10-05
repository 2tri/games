"""롬 하나를 통째로 읽어 JSON 하나로 (romanat 의 금 한글판 심볼 지도 기준, 표가 옮겨졌으면 포인터를 따라감)
  python3 romdump.py ROM OUT.json
원본 금은 디스어셈블리 빌드(van_00·van_ff)를 둘 다 뽑아 같은 값만 「원본 값」으로 본다 (romanat 참고).
롬에서 뽑은 내용은 저장소에 올리지 않는다 (work/ 에만)."""
import os, re, sys, json, struct
import romanat, asmconst, krtext, texts, wild

C = asmconst.load()
S = romanat.Sym()
NUM = 251


def nm(prefix, v, strip=True):
    n = C.names(prefix).get(v)
    if n is None: return v
    return n[len(prefix):] if strip else n


def cname(prefixes, v):
    for p in prefixes:
        n = C.names(p).get(v)
        if n: return n
    return v




def _list_consts(fname, start_pat=None):
    """constants 파일에서 const 이름을 순서대로 (값 → 이름)"""
    out = {}
    src = open(os.path.join(asmconst.KR, 'constants', fname)).read()
    for n in re.findall(r'^\s*const\s+(\w+)', src, re.M):
        if n in C.v: out.setdefault(C.v[n], n)
    return out


def _count(path, pat):
    return len(re.findall(pat, open(os.path.join(asmconst.KR, path)).read(), re.M))


MON = _list_consts('pokemon_constants.asm')
MOVES_C = _list_consts('move_constants.asm')
ITEMS_C = _list_consts('item_constants.asm')
TYPES_C = _list_consts('type_constants.asm')
TCLASS_C = {i + 1: g for i, g in enumerate(re.findall(r'dw (\w+)Group', open(os.path.join(asmconst.KR, 'data/trainers/party_pointers.asm')).read()))}
SPRITE_C = _list_consts('sprite_constants.asm')
MUSIC_C = _list_consts('music_constants.asm')
LANDMARK_C = _list_consts('landmark_constants.asm')
TILESET_C = _list_consts('tileset_constants.asm')
EFFECT_C = _list_consts('move_effect_constants.asm')
ANIM_C = MOVES_C            # 기술 연출 번호 = 기술 번호 (251 이후는 연출 전용)
EVO_KIND = {1: '레벨', 2: '도구', 3: '교환', 4: '친밀도', 5: '능력치'}
GROWTH = {0: 'MEDIUM_FAST', 1: 'SLIGHTLY_FAST', 2: 'SLIGHTLY_SLOW', 3: 'MEDIUM_SLOW', 4: 'FAST', 5: 'SLOW'}
EGG = {1: 'MONSTER', 2: 'WATER_1', 3: 'BUG', 4: 'FLYING', 5: 'GROUND', 6: 'FAIRY', 7: 'PLANT', 8: 'HUMANSHAPE',
       9: 'WATER_3', 10: 'MINERAL', 11: 'INDETERMINATE', 12: 'WATER_2', 13: 'DITTO', 14: 'DRAGON', 15: 'NONE'}


class Dump:
    def __init__(self, path):
        self.path = path
        self.d = open(path, 'rb').read()

    # ── 기본 ──
    def o(self, label): return S[label]
    def w(self, a): return self.d[a] | self.d[a + 1] << 8
    def bp(self, bank, ptr): return romanat.off(bank, ptr) if ptr >= 0x4000 or bank == 0 else ptr
    def same_bank(self, base, ptr): return romanat.off(base // 0x4000, ptr) if ptr >= 0x4000 else ptr
    def s(self, a, maxlen=40, stop=0x50):
        j = a
        while j < len(self.d) and self.d[j] != stop and j - a < maxlen: j += 1
        return krtext.decode(self.d, a, j), j

    def strlist(self, a, n, maxlen=40):
        out = []
        for _ in range(n):
            t, j = self.s(a, maxlen); out.append(t); a = j + 1
        return out

    # ── 이름 ──
    def names_pointers(self):
        a = S['NamesPointers']; out = []
        for k in range(8):
            b, p = self.d[a + 3 * k], self.w(a + 3 * k + 1)
            out.append((b, p))
        return out

    def mon_names(self):
        b, p = self.names_pointers()[0]; a = romanat.off(b, p)
        return [krtext.decode(self.d, a + 10 * k, a + 10 * k + 10) for k in range(NUM)]

    def move_names(self):
        b, p = self.names_pointers()[1]
        return self.strlist(romanat.off(b, p), NUM)

    def item_names(self):
        b, p = self.names_pointers()[3]
        return self.strlist(romanat.off(b, p), 255)

    def tclass_names(self):
        b, p = self.names_pointers()[6]
        return self.strlist(romanat.off(b, p), len(TCLASS_C))

    # ── 종 ──
    def tmhm(self):
        a = S['TMHMMoves']; out = []
        while self.d[a] and len(out) < 64: out.append(self.d[a]); a += 1
        return out

    def species(self):
        d = self.d; bs = S['BaseData']; names = self.mon_names(); tm = self.tmhm()
        evp = S['EvosAttacksPointers']; egp = S['EggMovePointers']
        pal = S['PokemonPalettes']; icons = S['MonMenuIcons']; cries = S['PokemonCries']
        pics = S['PokemonPicPointers']
        out = []
        for sp in range(1, NUM + 1):
            e = d[bs + 32 * (sp - 1):bs + 32 * sp]
            bits = int.from_bytes(e[24:32], 'little')
            # 진화·기술
            a = self.same_bank(evp, self.w(evp + 2 * (sp - 1))); ev = []
            evp_at = a
            while d[a] and len(ev) < 10:
                t = d[a]
                if t == 5: ev.append([t, d[a + 1], d[a + 2], d[a + 3]]); a += 4
                else: ev.append([t, d[a + 1], d[a + 2]]); a += 3
            a += 1; lv = []
            while d[a] and len(lv) < 40: lv.append([d[a], d[a + 1]]); a += 2
            # 알 기술
            g = self.same_bank(egp, self.w(egp + 2 * (sp - 1))); eg = []
            while d[g] != 0xff and len(eg) < 20: eg.append(d[g]); g += 1
            # 색
            pa = pal + 8 * sp
            cols = [struct.unpack('<H', d[pa + 2 * i:pa + 2 * i + 2])[0] for i in range(4)]
            # 그림 포인터
            pp = d[pics + 6 * (sp - 1):pics + 6 * sp]
            cry = struct.unpack('<3H', d[cries + 6 * (sp - 1):cries + 6 * sp])
            out.append(dict(
                no=sp, name=names[sp - 1], gold=MON.get(sp),
                stats=list(e[1:7]), types=[e[7], e[8]], catch=e[9], exp=e[10], items=[e[11], e[12]],
                gender=e[13], unk1=e[14], egg_steps=e[15], unk2=e[16], pic_size=e[17], growth=e[22],
                egg_groups=[e[23] >> 4, e[23] & 15], tmhm=[tm[i] for i in range(min(len(tm), 64)) if bits >> i & 1],
                tmhm_bits=e[24:32].hex(), evos=ev, learn=lv, egg_moves=eg, evos_at=evp_at,
                pal=cols, icon=d[icons + sp - 1], cry=list(cry),
                pic_ptr=pp.hex()))
        return out

    # ── 도감 ──
    def dex(self):
        d = self.d; tab = S['PokedexDataPointerTable']
        # GetDexEntryPointer: ... add BANK(...) (C6 xx) 다음 뱅크를 롬에서 읽음
        g = S['GetDexEntryPointer']; k = d.find(b'\xc6', g, g + 24); base = d[k + 1]
        out = []
        for sp in range(1, NUM + 1):
            bank = base + ((sp - 1) >> 7 & 1)
            a = romanat.off(bank, self.w(tab + 2 * (sp - 1)))
            if a >= len(d): out.append(None); continue
            cat, j = self.s(a, 20); h = d[j + 1]; wgt = self.w(j + 2)
            txt, j2 = self.s(j + 4, 300)
            out.append(dict(cat=cat, height=h, weight=wgt, text=txt))
        return out

    # ── 기술 ──
    def moves(self):
        d = self.d; a = S['Moves']; names = self.move_names()
        dt = S['MoveDescriptions']; out = []
        for k in range(NUM):
            e = d[a + 7 * k:a + 7 * k + 7]
            dp = romanat.off(dt // 0x4000, self.w(dt + 2 * k))
            desc, _ = self.s(dp, 120) if dp < len(d) else ('', 0)
            out.append(dict(no=k + 1, name=names[k], gold=MOVES_C.get(k + 1), anim=e[0], effect=e[1],
                            effect_name=EFFECT_C.get(e[1], e[1]), power=e[2], type=e[3], acc=e[4], pp=e[5], chance=e[6], desc=desc))
        return out

    # ── 타입 ──
    def types(self):
        d = self.d; tn = S['TypeNames']; names = {}
        for t in range(28):
            p = self.w(tn + 2 * t)
            if not (0x4000 <= p < 0x8000): continue
            names[t] = self.s(romanat.off(tn // 0x4000, p), 12)[0]
        a = S['TypeMatchups']; mt = []
        while d[a] != 0xff and len(mt) < 200:
            if d[a] == 0xfe: mt.append('foresight'); a += 1; continue
            mt.append([d[a], d[a + 1], d[a + 2]]); a += 3
        return dict(names=names, matchups=mt)

    # ── 도구 ──
    def items(self):
        d = self.d; names = self.item_names(); at = S['ItemAttributes']; ds = S['ItemDescriptions']
        out = []
        for k in range(1, 256):
            e = d[at + 7 * (k - 1):at + 7 * k] if k <= 0xf9 else b''
            desc = ''
            if k <= 0xf9:
                p = self.w(ds + 2 * (k - 1))
                if 0x4000 <= p < 0x8000: desc = self.s(romanat.off(ds // 0x4000, p), 120)[0]
            out.append(dict(no=k, name=names[k - 1], gold=ITEMS_C.get(k), attr=e.hex(),
                            price=(e[0] | e[1] << 8) if e else None, desc=desc))
        return out

    # ── 트레이너 ──
    def trainers(self):
        d = self.d; names = self.tclass_names(); n = len(names)
        att = S['TrainerClassAttributes']; dv = S['TrainerClassDVs']; pp = S['TrainerPicPointers']; tp = S['TrainerPalettes']
        tg = S['TrainerGroups']; classes = []
        counts = trainer_counts()
        parties = []
        for c in range(n):
            e = d[att + 7 * c:att + 7 * c + 7]
            classes.append(dict(no=c + 1, name=names[c], gold=TCLASS_C.get(c + 1), items=[e[0], e[1]], reward=e[2],
                                ai=e[3] | e[4] << 8, dvs=d[dv + 2 * c:dv + 2 * c + 2].hex(), pic=d[pp + 3 * c:pp + 3 * c + 3].hex(),
                                pal=d[tp + 4 * (c + 1):tp + 4 * (c + 2)].hex()))
            a = romanat.off(tg // 0x4000, self.w(tg + 2 * c))
            for k in range(counts[c] if c < len(counts) else 0):
                nmz, j = self.s(a, 20); a = j + 1; kind = d[a]; a += 1
                if kind > 3: break
                mons = []
                while d[a] != 0xff and len(mons) < 6:
                    m = dict(lv=d[a], sp=d[a + 1]); a += 2
                    if kind in (2, 3): m['item'] = d[a]; a += 1
                    if kind in (1, 3): m['moves'] = list(d[a:a + 4]); a += 4
                    mons.append(m)
                a += 1
                parties.append(dict(cls=c + 1, idx=k + 1, name=nmz, kind=kind, mons=mons))
        return dict(classes=classes, parties=parties)

    # ── 야생 ──
    def wild(self):
        d = self.d; out = {}
        for lab, water in (('JohtoGrassWildMons', 0), ('JohtoWaterWildMons', 1), ('KantoGrassWildMons', 0),
                           ('KantoWaterWildMons', 1), ('SwarmGrassWildMons', 0), ('SwarmWaterWildMons', 1)):
            a = S[lab]; rows = []
            while d[a] != 0xff and len(rows) < 200:
                g, m = d[a], d[a + 1]
                if water:
                    rate = d[a + 2]; sl = [[d[a + 3 + 2 * i], d[a + 4 + 2 * i]] for i in range(3)]; a += 9
                    rows.append(dict(map=[g, m], rate=rate, slots=sl))
                else:
                    rates = list(d[a + 2:a + 5]); sl = [[d[a + 5 + 2 * i], d[a + 6 + 2 * i]] for i in range(21)]; a += 47
                    rows.append(dict(map=[g, m], rates=rates, morn=sl[:7], day=sl[7:14], nite=sl[14:]))
            out[lab] = rows
        return out

    # ── 맵 ──
    def maps(self):
        d = self.d; gp = S['MapGroupPointers']; mn = wild.map_names()
        gd = open(os.environ['ROMDUMP_GP'], 'rb').read() if os.environ.get('ROMDUMP_GP') else d   # 원본 빌드는 이 표가 소스에 없음 → 다른 판 것을 빌림
        counts = {}
        for (g, n) in mn: counts[g] = max(counts.get(g, 0), n)
        out = []
        for g in range(1, 27):
            ga = romanat.off(gp // 0x4000, gd[gp + 2 * (g - 1)] | gd[gp + 2 * (g - 1) + 1] << 8)
            for n in range(1, counts.get(g, 0) + 1):
                try: out.append(self.map1(g, n, ga, mn))
                except IndexError: out.append(dict(group=g, num=n, label=mn.get((g, n), ('?',))[0], error='index'))
        return out

    def map1(self, g, n, ga, mn):
        d = self.d
        if True:
            if True:
                h = ga + 9 * (n - 1); e = d[h:h + 9]
                attr = romanat.off(e[0], e[3] | e[4] << 8)
                at = d[attr:attr + 12]
                border, hgt, wid = at[0], at[1], at[2]
                blocks = romanat.off(at[3], at[4] | at[5] << 8)
                sb = at[6]; scr = romanat.off(sb, at[7] | at[8] << 8); evt = romanat.off(sb, at[9] | at[10] << 8)
                conn = at[11]; conns = []; ca = attr + 12
                for bit, dn in ((8, 'N'), (4, 'S'), (2, 'W'), (1, 'E')):
                    if conn & bit: conns.append([dn, d[ca], d[ca + 1]]); ca += 12
                ev = self.events(evt, sb)
                key = mn.get((g, n), ('?', '?'))
                return dict(group=g, num=n, label=key[0], area=key[1], tileset=e[1], env=e[2], landmark=e[5], music=e[6],
                            phone_time=e[7], fish=e[8], border=border, h=hgt, w=wid, blocks_at=blocks,
                            blocks=d[blocks:blocks + hgt * wid].hex() if hgt * wid < 4000 else '',
                            scripts_at=scr, events_at=evt, conns=conns, events=ev)

    def events(self, a, bank):
        d = self.d; a += 2
        n = d[a]; a += 1; warps = []
        for _ in range(min(n, 64)): warps.append(list(d[a:a + 5])); a += 5
        n = d[a]; a += 1; coords = []
        for _ in range(min(n, 64)): coords.append(dict(scene=d[a], y=d[a + 1], x=d[a + 2], script=self.w(a + 4))); a += 8
        n = d[a]; a += 1; bgs = []
        for _ in range(min(n, 64)): bgs.append(dict(y=d[a], x=d[a + 1], kind=d[a + 2], script=self.w(a + 3))); a += 5
        n = d[a]; a += 1; objs = []
        for _ in range(min(n, 64)):
            e = d[a:a + 13]
            objs.append(dict(sprite=e[0], y=e[1] - 4, x=e[2] - 4, move=e[3], radius=e[4], h1=e[5], h2=e[6], pal_type=e[7],
                             sight=e[8], script=e[9] | e[10] << 8, flag=e[11] | e[12] << 8))
            a += 13
        return dict(warps=warps, coords=coords, bgs=bgs, objects=objs)

    # ── 기타 표 ──
    def landmarks(self):
        d = self.d; a = S['Landmarks']; out = []
        for k in range(_count('data/maps/landmarks.asm', r'^\s*landmark\s')):
            x, y, p = d[a + 4 * k], d[a + 4 * k + 1], self.w(a + 4 * k + 2)
            out.append(dict(no=k, x=x, y=y, name=self.s(romanat.off(a // 0x4000, p), 30)[0] if 0x4000 <= p < 0x8000 else ''))
        return out

    def music(self):
        d = self.d; a = S['Music']; n = _count('audio/music_pointers.asm', r'^\s*dba Music_')
        return [dict(no=k, gold=MUSIC_C.get(k), bank=d[a + 3 * k], ptr=self.w(a + 3 * k + 1),
                     hdr=d[romanat.off(d[a + 3 * k], self.w(a + 3 * k + 1)):romanat.off(d[a + 3 * k], self.w(a + 3 * k + 1)) + 12].hex()) for k in range(n)]

    def sprites(self):
        d = self.d; a = S['OverworldSprites']; n = _count('data/sprites/sprites.asm', r'^\s*overworld_sprite\s')
        out = []
        for k in range(n):
            e = d[a + 6 * k:a + 6 * k + 6]
            out.append(dict(no=k + 1, gold=SPRITE_C.get(k + 1), ptr=e[0] | e[1] << 8, tiles=e[2], bank=e[3], type=e[4], pal=e[5]))
        return out

    def tilesets(self):
        d = self.d; a = S['Tilesets']; out = []
        for k in range(_count('data/tilesets.asm', r'^\s*tileset\s')):
            e = d[a + 15 * k:a + 15 * k + 15]
            out.append(dict(no=k, gold=TILESET_C.get(k), raw=e.hex()))
        return out

    def marts(self):
        d = self.d; a = S['Marts']; out = []
        for k in range(40):
            p = self.w(a + 2 * k)
            if not (0x4000 <= p < 0x8000): break
            m = romanat.off(a // 0x4000, p); n = d[m]
            if n > 20: break
            out.append(list(d[m + 1:m + 1 + n]))
        return out

    def trades(self):
        d = self.d; a = S['NPCTrades']; out = []
        for k in range(7):
            e = d[a + 32 * k:a + 32 * k + 32]
            out.append(dict(dialog=e[0], want=e[1], give=e[2], nick=krtext.decode(e, 3, 14), dvs=e[14:16].hex(), item=e[16],
                            otid=e[17] | e[18] << 8, ot=krtext.decode(e, 19, 30), gender=e[30]))
        return out

    def header(self):
        d = self.d
        return dict(title=d[0x134:0x143].decode('latin1'), cgb=d[0x143], sgb=d[0x146], type=d[0x147], romsize=d[0x148],
                    ramsize=d[0x149], version=d[0x14c], hchk=d[0x14d], gchk=d[0x14e] << 8 | d[0x14f], size=len(d))

    def all(self):
        R = dict(rom=os.path.basename(self.path), header=self.header(), names_pointers=self.names_pointers())
        for k in ('species', 'dex', 'moves', 'types', 'items', 'tmhm', 'trainers', 'wild', 'maps', 'landmarks', 'music',
                  'sprites', 'tilesets', 'marts', 'trades'):
            try: R[k] = getattr(self, k)()
            except Exception as ex: R[k] = {'error': repr(ex)}
        return R


def trainer_counts():
    src = open(os.path.join(asmconst.KR, 'data/trainers/parties.asm')).read()
    groups = re.findall(r'dw (\w+)Group', open(os.path.join(asmconst.KR, 'data/trainers/party_pointers.asm')).read())
    out = []
    for g in groups:
        m = re.search(r'^%sGroup:\n(.*?)(?=^\w+Group:|\Z)' % g, src, re.S | re.M)
        out.append(len(re.findall(r'^\s*db "', m.group(1), re.M)) if m else 0)
    return out


if __name__ == '__main__':
    R = Dump(sys.argv[1]).all()
    json.dump(R, open(sys.argv[2], 'w'), ensure_ascii=False)
    for k, v in R.items():
        print(k, (len(v) if isinstance(v, (list, dict)) else v) if not (isinstance(v, dict) and 'error' in v) else v)
