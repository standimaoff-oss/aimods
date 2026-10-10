#!/usr/bin/env python3
"""GLB inspector: node tree with world translations and world AABBs of each subtree (numpy, handles KHR_mesh_quantization).
usage: glbtree.py file.glb [depth] [filter]"""
import json, struct, sys
import numpy as np
fn = sys.argv[1]; maxd = int(sys.argv[2]) if len(sys.argv) > 2 else 3; flt = sys.argv[3] if len(sys.argv) > 3 else None
d = open(fn, 'rb').read()
jl = struct.unpack('<I', d[12:16])[0]; j = json.loads(d[20:20 + jl]); o = 20 + jl
bl = struct.unpack('<I', d[o:o + 4])[0]; binc = d[o + 8:o + 8 + bl]
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
DT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32, 5122: np.int16, 5120: np.int8}
def acc(ai):
    a = j['accessors'][ai]; bv = j['bufferViews'][a['bufferView']]; dt = np.dtype(DT[a['componentType']]); nc = NC[a['type']]
    stride = bv.get('byteStride', dt.itemsize * nc); off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    raw = np.frombuffer(binc, dtype=np.uint8, count=stride * (a['count'] - 1) + dt.itemsize * nc, offset=off)
    out = np.lib.stride_tricks.as_strided(raw, shape=(a['count'], dt.itemsize * nc), strides=(stride, 1)).copy().view(dt).reshape(a['count'], nc).astype(np.float64)
    if a.get('normalized'):
        out /= {5120: 127, 5121: 255, 5122: 32767, 5123: 65535}[a['componentType']]
    return out
def qmat(q):
    x, y, z, w = q
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def local(n):
    M = np.eye(4)
    if 'matrix' in n: return np.array(n['matrix']).reshape(4, 4).T
    S = np.diag(n.get('scale', [1, 1, 1])); R = qmat(n.get('rotation', [0, 0, 0, 1]))
    M[:3, :3] = R @ S; M[:3, 3] = n.get('translation', [0, 0, 0]); return M
nodes = j['nodes']; parent = {}
for i, n in enumerate(nodes):
    for c in n.get('children', []): parent[c] = i
W = {}
def world(i):
    if i in W: return W[i]
    m = local(nodes[i]); p = parent.get(i)
    W[i] = (world(p) @ m) if p is not None else m; return W[i]
meshbox = {}
def mbox(mi):
    if mi in meshbox: return meshbox[mi]
    mn = np.full(3, 1e9); mx = np.full(3, -1e9)
    for p in j['meshes'][mi]['primitives']:
        P = acc(p['attributes']['POSITION']); mn = np.minimum(mn, P.min(0)); mx = np.maximum(mx, P.max(0))
    meshbox[mi] = (mn, mx); return meshbox[mi]
def subtree_box(i):
    mn = np.full(3, 1e9); mx = np.full(3, -1e9)
    st = [i]
    while st:
        k = st.pop(); n = nodes[k]
        if 'mesh' in n:
            a, b = mbox(n['mesh']); M = world(k)
            corners = np.array([[x, y, z, 1] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]) @ M.T
            mn = np.minimum(mn, corners[:, :3].min(0)); mx = np.maximum(mx, corners[:, :3].max(0))
        st += n.get('children', [])
    return mn, mx
roots = j['scenes'][j.get('scene', 0)]['nodes']
def show(i, dep):
    n = nodes[i]; name = n.get('name', '?')
    mn, mx = subtree_box(i); t = world(i)[:3, 3]
    if flt is None or flt in name:
        print('  ' * dep + "%s  T=(%.3f %.3f %.3f)  box=(%.2f %.2f %.2f)..(%.2f %.2f %.2f)%s" % (name, *t, *mn, *mx, " mesh" if 'mesh' in n else ""))
    if dep < maxd:
        for c in n.get('children', []): show(c, dep + 1)
for r in roots: show(r, 0)
print("animations:", [a.get('name') for a in j.get('animations', [])][:40])
