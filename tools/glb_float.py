#!/usr/bin/env python3
"""r27: detached-part audit straight on the exported GLBs (rest pose, all nodes, glTF coords x left, y up, z fwd).

usage: glb_float.py model.glb [tol_m=0.03] [min_size_m=0.04]

Every primitive is split into connected components (shared vertex indices); triangles are surface-sampled
(<= 4 cm spacing). Components whose samples come within tol of another component's samples are merged into
clusters. Everything that is not part of the largest cluster is reported: node, centre, size, gap to the main
cluster. Track links / wheels are skipped (they ride on their own pivots and always touch something anyway).
"""
import json, struct, sys, re
import numpy as np
from scipy.spatial import cKDTree

SKIP = re.compile(r"_link_|^rw_|^spk_|^idl_|^rr_|wheel|rotor|prop|flash|_lod|smoke|fx_|_glass", re.I)
CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}


def load(p):
    b = open(p, 'rb').read()
    L = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + L])
    o = 20 + L
    bl = struct.unpack('<I', b[o:o + 4])[0]
    return j, b[o + 8:o + 8 + bl]


def acc(j, bin_, i):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = np.dtype(CT[a['componentType']])
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0) or dt.itemsize * n
    out = np.ndarray(shape=(a['count'], n), dtype=dt, buffer=bin_, offset=off, strides=(stride, dt.itemsize)).copy()
    out = out.astype(np.float64)
    if a.get('normalized'):
        out /= float(np.iinfo(dt).max)
    return out


def qm(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def uf_find(p, a):
    while p[a] != a:
        p[a] = p[p[a]]
        a = p[a]
    return a


def main():
    path = sys.argv[1]
    tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.03
    mins = float(sys.argv[3]) if len(sys.argv) > 3 else 0.04
    j, bin_ = load(path)
    nodes = j['nodes']
    par = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []):
            par[c] = i

    def world(i):
        n = nodes[i]
        M = np.eye(4)
        if 'matrix' in n:
            M = np.array(n['matrix']).reshape(4, 4).T
        else:
            M[:3, :3] = qm(n.get('rotation', [0, 0, 0, 1])) @ np.diag(n.get('scale', [1, 1, 1]))
            M[:3, 3] = n.get('translation', [0, 0, 0])
        return world(par[i]) @ M if i in par else M

    def skipped(i):
        while True:
            if SKIP.search(nodes[i].get('name', '')):
                return True
            if i not in par:
                return False
            i = par[i]

    samples, labels, comps = [], [], []          # comps: (node name, bbmin, bbmax)
    for i, n in enumerate(nodes):
        if 'mesh' not in n or skipped(i):
            continue
        W = world(i)
        for prim in j['meshes'][n['mesh']]['primitives']:
            P = acc(j, bin_, prim['attributes']['POSITION'])
            P = (W[:3, :3] @ P.T).T + W[:3, 3]
            if 'indices' not in prim:
                continue
            I = acc(j, bin_, prim['indices']).astype(np.int64).reshape(-1, 3)
            from scipy.sparse import coo_matrix
            from scipy.sparse.csgraph import connected_components
            e0 = np.concatenate([I[:, 0], I[:, 1]]); e1 = np.concatenate([I[:, 1], I[:, 2]])
            _, root = connected_components(coo_matrix((np.ones(len(e0)), (e0, e1)), shape=(len(P), len(P))), directed=False)
            ids = {}
            for r in np.unique(root):
                ids[r] = len(comps)
                pts = P[root == r]
                comps.append((n.get('name', '?'), pts.min(0), pts.max(0)))
            # surface samples: vertices + barycentric grid per triangle (spacing <= 4 cm)
            samples.append(P)
            labels.append(np.array([ids[r] for r in root]))
            A, B, C = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
            L = np.maximum(np.linalg.norm(B - A, axis=1), np.maximum(np.linalg.norm(C - B, axis=1), np.linalg.norm(A - C, axis=1)))
            k = np.clip(np.ceil(L / 0.04).astype(int), 1, 40)
            tri_lab = np.array([ids[r] for r in root[I[:, 0]]])
            for kk in np.unique(k):
                if kk < 2:
                    continue
                sel = k == kk
                g = [(u / kk, v / kk) for u in range(kk + 1) for v in range(kk + 1 - u)]
                uv = np.array(g)
                a, b, c = A[sel], B[sel], C[sel]
                S = a[:, None, :] + uv[None, :, 0:1] * (b - a)[:, None, :] + uv[None, :, 1:2] * (c - a)[:, None, :]
                samples.append(S.reshape(-1, 3))
                labels.append(np.repeat(tri_lab[sel], len(g)))
    if not comps:
        print(path, "no meshes")
        return
    S = np.vstack(samples)
    Lb = np.concatenate(labels)
    tree = cKDTree(S)
    pairs = tree.query_pairs(tol, output_type='ndarray')
    cp = list(range(len(comps)))
    for a, b in pairs:
        la, lb = Lb[a], Lb[b]
        if la != lb:
            ra, rb = uf_find(cp, la), uf_find(cp, lb)
            if ra != rb:
                cp[rb] = ra
    croot = np.array([uf_find(cp, k) for k in range(len(comps))])
    sizes = {}
    for k, (nm, lo, hi) in enumerate(comps):
        sizes[croot[k]] = sizes.get(croot[k], 0) + np.prod(np.maximum(hi - lo, 0.01))
    main_c = max(sizes, key=sizes.get)
    main_pts = S[croot[Lb] == main_c]
    mtree = cKDTree(main_pts)
    rep = []
    for c in sizes:
        if c == main_c:
            continue
        ks = np.where(croot == c)[0]
        lo = np.min([comps[k][1] for k in ks], axis=0)
        hi = np.max([comps[k][2] for k in ks], axis=0)
        size = hi - lo
        if size.max() < mins:
            continue
        cpts = S[croot[Lb] == c]
        d, _ = mtree.query(cpts[:: max(1, len(cpts) // 4000)])
        names = sorted({comps[k][0] for k in ks})
        rep.append((size.max(), names, (lo + hi) / 2, size, d.min()))
    rep.sort(key=lambda r: -r[0])
    print("%s: %d components, %d clusters, %d detached >= %.0f cm" % (path.split('/')[-1], len(comps), len(sizes), len(rep), mins * 100))
    for sz, names, c, size, gap in rep[:40]:
        print("  gap %5.2f m  size %s  at %s  nodes %s" % (gap, np.round(size, 2).tolist(), np.round(c, 2).tolist(), ",".join(names)[:90]))


if __name__ == "__main__":
    main()
