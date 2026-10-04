#!/usr/bin/env python3
"""r27: are the guns attached?  For every animated node subtree (*_pitch, barrel*, *_yaw ...) the smallest distance
between its own geometry and the geometry of its parent subtree. usage: gun_gap.py X.glb ... [--min 0.03]"""
import sys, re, numpy as np
sys.path.insert(0, '/home/user/tools')
from glb_float import load, acc, qm
from turret_gap import samples
from scipy.spatial import cKDTree
ANIM = re.compile(r'(launcher_yaw|launcher_pitch|barrel|.*_yaw|.*_pitch|.*_g\d|.*_barrel\d*)$')
SKIP = re.compile(r"_link_|^rw_|^spk_|^idl_|^rr_|wheel|rotor|prop|flash|smoke|fx_|_glass|disc", re.I)


def run(path, mn):
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

    def owner(i):          # nearest animated ancestor (or root -1)
        while True:
            nm = nodes[i].get('name', '')
            if SKIP.search(nm):
                return None
            if ANIM.fullmatch(nm):
                return i
            if i not in par:
                return -1
            i = par[i]
    pts = {}
    for i, n in enumerate(nodes):
        if 'mesh' not in n:
            continue
        o = owner(i)
        if o is None:
            continue
        W = world(i)
        for prim in j['meshes'][n['mesh']]['primitives']:
            if 'indices' not in prim:
                continue
            P = acc(j, bin_, prim['attributes']['POSITION'])
            P = (W[:3, :3] @ P.T).T + W[:3, 3]
            I = acc(j, bin_, prim['indices']).astype(np.int64).reshape(-1, 3)
            pts.setdefault(o, []).append(samples(P, I, 0.05))
    pts = {k: np.concatenate(v) for k, v in pts.items()}
    for o, P in pts.items():
        if o < 0:
            continue
        # parent subtree owner
        q = par.get(o)
        po = owner(q) if q is not None else -1
        while po is not None and po not in pts and po >= 0:
            q = par.get(po)
            po = owner(q) if q is not None else -1
        if po is None or po not in pts:
            continue
        d, _ = cKDTree(pts[po]).query(P[:: max(1, len(P) // 4000)], k=1)
        g = d.min()
        if g > mn:
            print('%-24s %-22s -> %-22s gap %.3f m  %s' % (path.split('/')[-1], nodes[o]['name'], nodes[po]['name'] if po >= 0 else 'hull', g, 'DETACHED'))


mn = 0.03
args = [a for a in sys.argv[1:]]
if '--min' in args:
    k = args.index('--min'); mn = float(args[k + 1]); del args[k:k + 2]
for p in args:
    run(p, mn)
