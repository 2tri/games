"""큰 그림(이미지 AI 배경·제목)을 GBC 규칙으로: 8×8 칸마다 팔레트 1개(4색), 팔레트 최대 N개.
1) 전체 색을 K개로 줄임(k-평균) 2) 칸마다 4색 이하로 3) 색 묶음을 팔레트 N개로 합침(많이 쓰는 색을 지킴)
4) 칸마다 가장 잘 맞는 팔레트 고르기 5) 거의 같은 칸은 하나로 (타일 수 줄이기)"""
import numpy as np


def kmeans_colors(px, w, k, iters=12, seed=1):
    rng = np.random.default_rng(seed)
    uniq, inv = np.unique(px.reshape(-1, 3), axis=0, return_inverse=True)
    wt = np.bincount(inv.ravel(), weights=np.repeat(w, 1) if np.ndim(w) else None, minlength=len(uniq)) if False else np.bincount(inv.ravel(), minlength=len(uniq)).astype(float)
    if len(uniq) <= k: return uniq.astype(float)
    # 시작점: 무게 큰 색 + 멀리 떨어진 색
    c = [uniq[np.argmax(wt)].astype(float)]
    d = ((uniq - c[0]) ** 2).sum(1).astype(float)
    while len(c) < k:
        i = int(np.argmax(d * np.sqrt(wt))); c.append(uniq[i].astype(float)); d = np.minimum(d, ((uniq - uniq[i]) ** 2).sum(1))
    c = np.array(c)
    for _ in range(iters):
        lab = np.argmin(((uniq[:, None, :] - c[None]) ** 2).sum(2), 1)
        for j in range(k):
            m = lab == j
            if m.any(): c[j] = (uniq[m] * wt[m, None]).sum(0) / wt[m].sum()
    return c


def fit(subtiles, maxp=7, k=24, keep=None, weights=None):
    """subtiles: [8×8×3] → (팔레트 목록 [[(r,g,b)]*4], [(팔레트번호, 8×8 색번호)])
    weights: 칸마다 지도에서 쓰이는 횟수 (많이 보이는 풀·길 색을 지킴)"""
    if weights is None: weights = [1] * len(subtiles)
    allpx = np.concatenate([s.reshape(-1, 3) for s, w in zip(subtiles, weights) for _ in range(min(int(w), 6))]).astype(float)
    G = kmeans_colors(allpx, None, k)
    gw = np.zeros(len(G))
    idx = []
    for s, w in zip(subtiles, weights):
        p = s.reshape(-1, 3).astype(float)
        li = np.argmin(((p[:, None] - G[None]) ** 2).sum(2), 1); idx.append(li)
        gw += np.bincount(li, minlength=len(G)) * w
    def dist(a, b): return float(((G[a] - G[b]) ** 2).sum())
    sets = {}
    for li in idx:
        cnt = np.bincount(li, minlength=len(G)); cols = [int(c) for c in np.nonzero(cnt)[0]]
        cw = {c: cnt[c] for c in cols}
        while len(cols) > 4:
            i = min(cols, key=lambda c: cw[c]); cols.remove(i)
            j = min(cols, key=lambda c: dist(i, c)); cw[j] += cw[i]
        key = frozenset(cols); sets[key] = sets.get(key, 0) + 1
    pals = []
    for st in sorted(sets, key=lambda x: (-len(x), -sets[x])):
        if any(st <= p for p in pals): continue
        best = None
        for p in pals:
            un = p | st
            if len(un) <= 4 and (best is None or len(un) - len(p) < best[0]): best = (len(un) - len(p), p)
        if best: pals.remove(best[1]); pals.append(best[1] | st)
        else: pals.append(frozenset(st))
    def reduce(cols):
        cols = list(cols); w = {c: gw[c] for c in cols}
        while len(cols) > 4:
            i = min(cols, key=lambda c: w[c]); cols.remove(i)
            j = min(cols, key=lambda c: dist(i, c)); w[j] += w[i]
        return cols
    def cost(p, q):
        un = list(p | q); red = reduce(un)
        return sum(gw[c] * min(dist(c, r) for r in red) for c in un), frozenset(red)
    while len(pals) > maxp:
        best = None
        for i in range(len(pals)):
            for j in range(i + 1, len(pals)):
                c_, red = cost(pals[i], pals[j])
                if best is None or c_ < best[0]: best = (c_, i, j, red)
        _, i, j, red = best
        pals = [p for t, p in enumerate(pals) if t not in (i, j)] + [red]
    out_p = []
    for p in pals:
        cols = sorted([tuple(int(round(v)) for v in G[c]) for c in p], key=lambda c: -(c[0] * .299 + c[1] * .587 + c[2] * .114))
        out_p.append((cols + [cols[-1]] * 4)[:4])
    if keep:      # 앞에 꼭 넣을 팔레트
        out_p = keep + out_p
    res = []
    PA = [np.array(p, float) for p in out_p]
    for s in subtiles:
        px = s.reshape(-1, 3).astype(float); best = None
        for pi, pa in enumerate(PA):
            d = ((px[:, None] - pa[None]) ** 2).sum(2); e = d.min(1).sum()
            if best is None or e < best[0]: best = (e, pi, d.argmin(1).reshape(8, 8).astype(np.uint8))
        res.append((best[1], best[2]))
    return out_p, res


def merge_tiles(res, budget, protect=()):
    """거의 같은 칸을 하나로: 타일 수가 budget 이하가 될 때까지 기준을 올림 → (대표 타일 목록, 칸마다 대표 번호)"""
    keys = [(pi, t.tobytes()) for pi, t in res]
    freq = {}
    for k in keys: freq[k] = freq.get(k, 0) + 1
    order = sorted(freq, key=lambda k: -freq[k])
    arr = {k: np.frombuffer(k[1], np.uint8).reshape(8, 8) for k in order}
    for thr in range(0, 40, 2):
        reps = []; rep_of = {}
        for k in order:
            a = arr[k]; hit = None
            if thr:
                for ri, r in enumerate(reps):
                    if r[0] == k[0] and (r[1] != a).sum() <= thr: hit = ri; break
            if hit is None: rep_of[k] = len(reps); reps.append((k[0], a))
            else: rep_of[k] = hit
        if len(reps) <= budget: break
    tiles = [r[1] for r in reps]
    # 대표 타일은 그 칸의 팔레트를 그대로 씀 (같은 팔레트끼리만 합쳤음)
    return tiles, [rep_of[k] for k in keys], [r[0] for r in reps], thr


CW = np.array([3.0, 4.0, 2.0])      # 색 거리 무게 (초록 차이에 민감하게)


def _km4(px, w, k=4, iters=8):
    """화소 무게 k-평균 → k색 (화소가 적으면 있는 색 그대로)"""
    uniq, inv = np.unique(px, axis=0, return_inverse=True)
    wt = np.bincount(inv.ravel(), weights=w, minlength=len(uniq))
    if len(uniq) <= k: return np.vstack([uniq, np.repeat(uniq[-1:], k - len(uniq), 0)]).astype(float)
    c = [uniq[np.argmax(wt)].astype(float)]
    d = (((uniq - c[0]) ** 2) * CW).sum(1)
    while len(c) < k:
        i = int(np.argmax(d * wt)); c.append(uniq[i].astype(float)); d = np.minimum(d, (((uniq - uniq[i]) ** 2) * CW).sum(1))
    c = np.array(c)
    for _ in range(iters):
        lab = np.argmin((((uniq[:, None, :] - c[None]) ** 2) * CW).sum(2), 1)
        for j in range(k):
            m = lab == j
            if m.any(): c[j] = (uniq[m] * wt[m, None]).sum(0) / wt[m].sum()
    return c


def fit2(subtiles, maxp=7, weights=None, iters=12):
    """타일 묶기 방식: 팔레트 maxp 개를 '오차가 가장 큰 타일'부터 하나씩 늘리며 만들고,
    (타일 → 가장 잘 맞는 팔레트, 팔레트 → 맡은 타일 화소로 4색 다시 뽑기)를 되풀이.
    드물게 나오는 색(파란 지붕·불꽃)도 자기 팔레트를 얻기 쉬움"""
    n = len(subtiles)
    if weights is None: weights = [1] * n
    tw = np.sqrt(np.array(weights, float))          # 많이 쓰는 칸을 조금 더 중요하게 (제곱근)
    T = np.array([s.reshape(-1, 3) for s in subtiles], float)     # n×64×3

    def err_all(P):     # n×p 오차, n×p×64 색번호
        d = (((T[:, None, :, None, :] - P[None, :, None, :, :]) ** 2) * CW).sum(-1)   # n×p×64×4
        return d.min(-1).sum(-1), d.argmin(-1)

    def refit(assign, P):
        P = P.copy()
        for j in range(len(P)):
            m = assign == j
            if not m.any(): continue
            px = T[m].reshape(-1, 3); w = np.repeat(tw[m], 64)
            P[j] = _km4(np.round(px).astype(int), w)
        return P

    P = np.array([_km4(np.round(T[int(np.argmax(tw))]).astype(int), np.ones(64))])
    while True:
        for _ in range(3):
            e, _i = err_all(P); a = e.argmin(1); P = refit(a, P)
        if len(P) >= maxp: break
        e, _i = err_all(P); be = e.min(1) * tw
        worst = int(np.argmax(be))
        P = np.concatenate([P, _km4(np.round(T[worst]).astype(int), np.ones(64))[None]])
    for _ in range(iters):
        e, _i = err_all(P); a = e.argmin(1); P2 = refit(a, P)
        if np.allclose(P2, P): break
        P = P2
    e, idx = err_all(P); a = e.argmin(1)
    out_p = []
    order = []
    for p in P:
        cols = [tuple(int(round(v)) for v in c) for c in p]
        o = sorted(range(4), key=lambda i: -(cols[i][0] * .299 + cols[i][1] * .587 + cols[i][2] * .114))
        out_p.append([cols[i] for i in o]); order.append(o)
    res = []
    for t in range(n):
        pi = int(a[t]); inv = {old: new for new, old in enumerate(order[pi])}
        res.append((pi, np.vectorize(inv.get)(idx[t, pi]).reshape(8, 8).astype(np.uint8)))
    return out_p, res
