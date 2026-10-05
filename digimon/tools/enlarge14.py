"""작게 들어간 전투 그림을 칸을 꽉 채우게 키우기 (2026-10-05 사용자 메모 「확대」)
    python3 enlarge14.py 입력.png 출력.png --size 56     (앞 56, 뒤 48)
외딴 점(6칸 미만) 지우기 → 그림 부분만 자르기 → scale3x 로 3배 매끄럽게 → 칸 크기로 다수결 줄이기(검정 선 우선).
1.4 그림은 롬에서 꺼낸 것이라 저장소에 올리지 않음 — 롬 세션이 빌드 때 롬 그림에 바로 씀. 색은 입력 그림의 4색 그대로."""
import argparse, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lcd2sketch as L, sheet2gbc as S2


def to_idx(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    cols = sorted({tuple(x) for x in a.reshape(-1, 3)}, key=lambda c: -sum(c))[:4]   # 흰·밝은·어두운·검정
    t = np.zeros(a.shape[:2], int)
    for i, c in enumerate(cols): t[(a == c).all(2)] = i
    return t, (cols + [(0, 0, 0)] * 4)[:4]


def enlarge(t, size):
    m = t > 0; lab, n = ndimage.label(m, structure=np.ones((3, 3))); sz = ndimage.sum(m, lab, range(1, n + 1))
    t = np.where(np.isin(lab, [i + 1 for i, s in enumerate(sz) if s >= 6]), t, 0)
    ys, xs = np.where(t > 0); t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    bg = t == 0; lab, _ = ndimage.label(bg); edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    out = np.isin(lab, list(edge))                                     # 바깥 흰 = 배경 (안쪽 흰은 몸)
    up = np.where(L.scale3x(out.astype(int)) == 1, -1, L.scale3x(t))
    k = size / max(t.shape)
    return S2.shrink(up, max(round(t.shape[0] * k), round(t.shape[1] * k)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst'); ap.add_argument('--size', type=int, default=56); a = ap.parse_args()
    t, cols = to_idx(Image.open(a.src)); r = enlarge(t, a.size)
    o = np.zeros(r.shape + (4,), np.uint8); pal = np.array([c + (255,) for c in cols], np.uint8); o[r >= 0] = pal[r[r >= 0]]
    Image.fromarray(o, 'RGBA').save(a.dst); print(a.dst, o.shape[1::-1])


if __name__ == '__main__':
    main()
