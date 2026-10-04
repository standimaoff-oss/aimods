#!/usr/bin/env python3
"""r27: does each turret sit on its hull?  usage: turret_gap.py X.glb [X2.glb ...]

Turret = geometry under every node named launcher_yaw / *_yaw (not *_pitch-only), hull = the rest (links / wheels
skipped). The lowest 6 cm of the turret geometry is the footprint; for every footprint sample the nearest hull surface
straight below (within 12 cm horizontally) gives the vertical gap. A turret whose median gap is > 4 cm floats.
"""
import sys, re, numpy as np
sys.path.insert(0, '/home/user/tools')
from glb_float import load, acc, qm, SKIP
from scipy.spatial import cKDTree


def samples(P, I, step=0.04):
    out = [P]
    A, B, C = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    L = np.maximum(np.linalg.norm(B - A, axis=1), np.maximum(np.linalg.norm(C - A, axis=1), np.linalg.norm(C - B, axis=1)))
    n = np.clip((L / step).astype(int), 1, 40)
    for k in np.unique(n):
        m = n == k
        a, b, c = A[m], B[m], C[m]
        for u in range(k + 1):
            for v in range(k + 1 - u):
                w = k - u - v
                out.append((a * u + b * v + c * w) / k)
    return np.concatenate(out)


def run(path):
    j, bin_ = load(path)
    nodes = j['nodes']
    par = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}

    def world(i):
        n = nodes[i]
        M = np.eye(4)
        if 'matrix' in n:
            M = np.array(n['matrix']).reshape(4, 4).T
        else:
            M[:3, :3] = qm(n.get('rotation', [0, 0, 0, 1])) @ np.diag(n.get('scale', [1, 1, 1]))
            M[:3, 3] = n.get('translation', [0, 0, 0])
        return world(par[i]) @ M if i in par else M

    def chain(i):
        out = []
        while True:
            out.append(nodes[i].get('name', ''))
            if i not in par:
                return out
            i = par[i]
    groups = {}
    hull = []
    for i, n in enumerate(nodes):
        if 'mesh' not in n:
            continue
        ch = chain(i)
        if any(SKIP.search(c) for c in ch):
            continue
        yaw = [c for c in ch if re.fullmatch(r'(launcher_yaw|.*_yaw)', c)]
        W = world(i)
        for prim in j['meshes'][n['mesh']]['primitives']:
            if 'indices' not in prim:
                continue
            P = acc(j, bin_, prim['attributes']['POSITION'])
            P = (W[:3, :3] @ P.T).T + W[:3, 3]
            I = acc(j, bin_, prim['indices']).astype(np.int64).reshape(-1, 3)
            S = samples(P, I)
            (groups.setdefault(yaw[-1], []) if yaw else hull).append(S)
    if not hull:
        return
    H = np.concatenate(hull)
    tree = cKDTree(H[:, [0, 2]])
    for name, parts in sorted(groups.items()):
        T = np.concatenate(parts)
        y0 = T[:, 1].min()
        F = T[T[:, 1] < y0 + 0.06]
        gaps = []
        for p in F[:: max(1, len(F) // 1500)]:
            idx = tree.query_ball_point([p[0], p[2]], 0.12)
            if not idx:
                continue
            ys = H[idx, 1]
            ys = ys[ys <= p[1] + 0.02]
            if len(ys):
                gaps.append(p[1] - ys.max())
        g = np.array(gaps) if gaps else np.array([np.inf])
        flag = 'FLOATS' if np.median(g) > 0.04 else 'ok'
        print('%-28s %-16s footprint %5d  median gap %6.3f m  p10 %6.3f  p90 %6.3f  bottom y %.2f  %s' % (
            path.split('/')[-1], name, len(F), np.median(g), np.percentile(g, 10), np.percentile(g, 90), y0, flag))


for p in sys.argv[1:]:
    run(p)
