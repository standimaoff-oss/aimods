#!/usr/bin/env python3
"""r27: tileable 3D noise for the volumetric smoke shader (assets/aiarsenal/shaders/core/volsmoke.fsh).

32^3 voxels packed into a 2D atlas: 32 slices of 32x32, each with a 1 px wrap border (34x34), 8 columns x 4 rows
-> 272 x 136 RGBA.   R = billowy Perlin-Worley (base shape, ~4 cells per tile)
                     G = inverted Worley fbm (detail, 8/16/32 cells)
                     B = Perlin fbm (distortion)       A = 255
usage: volnoise.py out.png
"""
import sys
import numpy as np
from PIL import Image

N = 32
rng = np.random.default_rng(2027)
g = (np.indices((N, N, N)).transpose(1, 2, 3, 0) + 0.5) / N          # voxel centres in [0,1)^3, shape (N,N,N,3)


def worley(freq, seed):
    """F1 distance (in cell units, ~0..1) to tileable random feature points, freq cells per tile."""
    r = np.random.default_rng(seed)
    feat = r.random((freq, freq, freq, 3))
    p = g * freq
    cell = np.floor(p).astype(int)
    best = np.full(p.shape[:3], 9.0)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = cell + np.array([dx, dy, dz])
                fp = feat[c[..., 0] % freq, c[..., 1] % freq, c[..., 2] % freq] + c
                d = np.sqrt(((fp - p) ** 2).sum(-1))
                best = np.minimum(best, d)
    return np.clip(best, 0, 1.2)


def perlin(freq, seed):
    r = np.random.default_rng(seed)
    grads = r.normal(size=(freq, freq, freq, 3))
    grads /= np.linalg.norm(grads, axis=-1, keepdims=True)
    p = g * freq
    i0 = np.floor(p).astype(int)
    f = p - i0
    u = f * f * f * (f * (f * 6 - 15) + 10)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                c = i0 + np.array([dx, dy, dz])
                gr = grads[c[..., 0] % freq, c[..., 1] % freq, c[..., 2] % freq]
                d = f - np.array([dx, dy, dz])
                w = (u[..., 0] if dx else 1 - u[..., 0]) * (u[..., 1] if dy else 1 - u[..., 1]) * (u[..., 2] if dz else 1 - u[..., 2])
                out = out + w * (gr * d).sum(-1)
    return out                                                    # ~[-0.9, 0.9]


def norm01(a, lo=1.0, hi=99.0):
    a0, a1 = np.percentile(a, lo), np.percentile(a, hi)
    return np.clip((a - a0) / (a1 - a0), 0, 1)


pf = norm01(perlin(4, 1) * 0.6 + perlin(8, 2) * 0.3 + perlin(16, 3) * 0.1)
wb = (1 - worley(4, 11)) * 0.625 + (1 - worley(8, 12)) * 0.25 + (1 - worley(16, 13)) * 0.125
R = norm01(wb * (0.65 + 0.7 * pf))
G = norm01((1 - worley(8, 21)) * 0.55 + (1 - worley(16, 22)) * 0.3 + (1 - worley(32, 23)) * 0.15)
B = norm01(perlin(4, 31) * 0.7 + perlin(8, 32) * 0.3)
vol = np.stack([R, G, B, np.ones_like(R)], -1)                     # (x, y, z, 4)

T = N + 2
atlas = np.zeros((4 * T, 8 * T, 4), np.float32)
for z in range(N):
    sl = vol[:, :, z, :].transpose(1, 0, 2)                          # rows = y, cols = x
    sl = np.pad(sl, ((1, 1), (1, 1), (0, 0)), mode='wrap')
    col, row = z % 8, z // 8
    atlas[row * T:(row + 1) * T, col * T:(col + 1) * T] = sl
img = Image.fromarray((atlas * 255 + 0.5).astype(np.uint8), 'RGBA')
out = sys.argv[1] if len(sys.argv) > 1 else 'volnoise.png'
img.save(out, optimize=True)
np.save(out.replace('.png', '.npy'), vol.astype(np.float32)) if '--npy' in sys.argv else None
print('wrote', out, img.size, 'R mean %.2f G mean %.2f' % (R.mean(), G.mean()))
