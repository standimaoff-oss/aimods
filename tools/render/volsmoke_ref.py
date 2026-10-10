#!/usr/bin/env python3
"""r27: numpy port of shaders/core/volsmoke.fsh for offline look-dev (no Minecraft needed).

Renders a test scene (ground plane, sky) with puffs composited back-to-front exactly like FxSystem + volsmoke.fsh:
ray/sphere, depth clip by the ground, raymarch through the same 3D noise (tools/render/volnoise.py --npy),
Beer-Lambert, analytic sun chord, HG phase, emission.  usage: volsmoke_ref.py out.png [scene] [steps]
Also prints the mean centre opacity vs. the requested alpha (calibration of the K constant).
"""
import sys, math
import numpy as np
from PIL import Image

VOL = np.load('/home/user/.cache/volnoise.npy')       # (32,32,32,4) x,y,z
N = 32
K_DIV = 0.62


def noise3(p):
    """trilinear, wrapped; p (...,3) in tile units -> (...,4)"""
    q = (p - np.floor(p)) * N - 0.5
    i0 = np.floor(q).astype(int)
    f = q - i0
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                v = VOL[(i0[..., 0] + dx) % N, (i0[..., 1] + dy) % N, (i0[..., 2] + dz) % N]
                out = out + w[..., None] * v
    return out


def ign(x, y):
    return np.mod(52.9829189 * np.mod(x * 0.06711056 + y * 0.00583715, 1.0), 1.0)


def fire_ramp(t):
    return np.stack([np.ones_like(t), 0.30 + 0.55 * t, 0.05 + 0.45 * t * t], -1)


def shade_puff(D, px, py, C, R, col, alpha, seed, heat, age, tscene, sun, sunc, amb, light, steps, detail=True, dens=1.0):
    """D (...,3) unit rays from the camera at origin. Returns premultiplied rgb, alpha (masked)."""
    b = (D * C).sum(-1)
    h = b * b - (C @ C - R * R)
    hit = h > 0
    hs = np.sqrt(np.maximum(h, 0))
    t0 = np.maximum(b - hs, 0)
    t1 = np.minimum(b + hs, tscene)
    hit &= t1 > t0 + 1e-3
    opac = min(alpha, 0.985)
    K = -math.log(1 - opac) * dens / (R * K_DIV)
    dt = (t1 - t0) / steps
    jit = ign(px, py)
    ang = (seed - 0.5) * 6.2832 + age * (seed - 0.5) * 2.5
    ca, sa = math.cos(ang), math.sin(ang)
    off = np.array([seed * 7.13, seed * 3.71 - age * 0.35, seed * 5.29])
    L = sun / np.linalg.norm(sun)
    mu = D @ L
    g = 0.35
    hg = (1 - g * g) / (1 + g * g - 2 * g * mu) ** 1.5
    phase = 1.0 + (hg - 1.0) * 0.5
    acc = np.zeros(D.shape)
    T = np.ones(D.shape[:-1])
    for i in range(int(steps)):
        t = t0 + (i + jit) * dt
        q = (D * t[..., None] - C) / R
        r2 = (q * q).sum(-1)
        m = hit & (r2 < 1.0) & (T > 0.01)
        pq = np.stack([q[..., 0] * ca - q[..., 2] * sa, q[..., 1], q[..., 0] * sa + q[..., 2] * ca], -1)
        shape = 1 - r2
        base = noise3(pq * 0.42 + off)[..., 0]
        d = shape * 1.35 - (1 - base) * 0.95
        if detail:
            det = noise3(pq * 1.1 + off * 1.7)[..., 1]
            d = d - (1 - det) * 0.3 * (1 - shape * 0.7)
        m &= d > 0
        d = np.clip(d, 0, 1)
        sig = d * K
        a = np.where(m, 1 - np.exp(-sig * dt), 0.0)
        qL = q @ L
        ex = -qL + np.sqrt(np.maximum(qL * qL - r2 + 1, 0))
        tl = ex * R * K * (0.30 + 0.40 * d)
        sunT = np.exp(-tl) + 0.25 * np.exp(-tl * 0.2)
        up = 0.62 + 0.38 * q[..., 1]
        c = col * light * (sunc * (sunT * phase)[..., None] + amb * up[..., None])
        if heat > 0:
            temp = heat * np.clip(d * 1.5, 0, 1) * (1 - 0.55 * np.sqrt(np.clip(r2, 0, 1)))
            c = c + fire_ramp(temp) * (temp * 3.0)[..., None]
        acc += (T * a)[..., None] * c
        T = T * (1 - a)
    al = np.where(hit, 1 - T, 0.0)
    return np.where(hit[..., None], acc, 0.0), al


def render(puffs, W=640, H=360, fov=70, cam=np.array([0, 1.7, 0.0]), yaw=0.0, pitch=8.0, sun=np.array([0.5, 0.75, -0.45]),
           steps=8, sunc=np.array([1.0, 0.95, 0.86]), amb=np.array([0.42, 0.47, 0.55]), detail=True):
    # camera basis: yaw about Y (0 = looking +Z), pitch up positive
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    fwd = np.array([sy * cp, sp, cy * cp]); right = np.cross(fwd, [0, 1.0, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    th = math.tan(math.radians(fov) / 2)
    ys, xs = np.mgrid[0:H, 0:W]
    u = ((xs + 0.5) / W * 2 - 1) * th * W / H
    v = (1 - (ys + 0.5) / H * 2) * th
    D = fwd + u[..., None] * right + v[..., None] * up
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    # background: sky gradient, ground plane y = 0 with soft sun shading + grid
    sky = np.array([0.55, 0.70, 0.92]) * (1 - D[..., 1:2].clip(0, 1) * 0.4) + np.array([0.2, 0.2, 0.15]) * (1 - D[..., 1:2].clip(0, 1))
    tg = np.where(D[..., 1] < -1e-4, -cam[1] / np.minimum(D[..., 1], -1e-4), 1e9)
    gp = cam + D * tg[..., None]
    chk = ((np.floor(gp[..., 0] / 4) + np.floor(gp[..., 2] / 4)) % 2)[..., None]
    ground = np.array([0.33, 0.42, 0.22]) * (0.85 + 0.15 * chk)
    img = np.where((tg < 1e8)[..., None], ground, sky)
    fogd = np.clip((tg - 120) / 200, 0, 1)[..., None]
    img = img * (1 - fogd) + sky * fogd
    order = sorted(puffs, key=lambda p: -np.linalg.norm(np.array(p['c']) - cam))
    for p in order:
        C = np.array(p['c'], float) - cam
        R = p['r']
        # screen bbox of the sphere (cheap: project centre, conservative radius)
        dist = np.linalg.norm(C)
        if dist < R * 1.2:
            sl = (slice(0, H), slice(0, W))
        else:
            ang = math.asin(min(R / dist, 0.999))
            cd = C / dist
            zc = cd @ fwd
            if zc <= 0.05:
                continue
            sx = (cd @ right) / zc / th / (W / H); syy = (cd @ up) / zc / th
            rr = math.tan(ang) / zc / th * 1.3
            x0 = int(((sx - rr * H / W) + 1) / 2 * W) - 2; x1 = int(((sx + rr * H / W) + 1) / 2 * W) + 2
            y0 = int((1 - (syy + rr)) / 2 * H) - 2; y1 = int((1 - (syy - rr)) / 2 * H) + 2
            x0, x1, y0, y1 = max(x0, 0), min(x1, W), max(y0, 0), min(y1, H)
            if x1 <= x0 or y1 <= y0:
                continue
            sl = (slice(y0, y1), slice(x0, x1))
        steps_p = max(3, min(steps, int(R / max(dist, R) * 1.0 / th * H * 0.5 / 12)))
        rgb, al = shade_puff(D[sl], xs[sl], ys[sl], C, R, np.array(p['col']), p['a'], p['seed'], p.get('heat', 0.0), p.get('age', 0.3),
                             tg[sl], sun, sunc, amb, 1.0, steps_p, detail)
        img[sl] = rgb + img[sl] * (1 - al[..., None])
    return np.clip(img, 0, 1)


def scene_test(rng):
    P = []
    # 1) explosion smoke column 40 m ahead: dark grey-brown, rising, widening
    for k in range(34):
        y = 1.5 + k * 0.9 + rng.random() * 0.8
        P.append(dict(c=(-8 + rng.normal() * (1.2 + k * 0.05), y, 45 + rng.normal() * (1.2 + k * 0.05)), r=2.0 + k * 0.10 + rng.random(),
                      col=(0.20, 0.18, 0.16), a=0.75, seed=rng.random(), age=k / 34))
    # fireball at its base
    for k in range(6):
        P.append(dict(c=(-8 + rng.normal() * 0.8, 1.6 + rng.random() * 1.5, 45 + rng.normal() * 0.8), r=1.6 + rng.random(), col=(0.3, 0.2, 0.1), a=0.9,
                      seed=rng.random(), heat=0.9, age=0.1))
    # 2) white smoke screen 25 m ahead, to the right, hugging the ground
    for k in range(26):
        P.append(dict(c=(6 + rng.random() * 14, 1.2 + rng.random() * 2.2, 22 + rng.random() * 8), r=2.2 + rng.random() * 1.6,
                      col=(0.86, 0.86, 0.84), a=0.8, seed=rng.random(), age=0.5))
    # 3) rocket trail climbing to the upper left
    for k in range(60):
        f = k / 59
        P.append(dict(c=(-30 + f * 26, 2 + f * f * 40, 70 - f * 10), r=0.7 + f * 0.9 + rng.random() * 0.3, col=(0.92, 0.92, 0.9), a=0.55,
                      seed=rng.random(), age=f))
    return P


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/home/user/.cache/render/volsmoke_ref.png'
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    rng = np.random.default_rng(7)
    # calibration: mean opacity through the centre of a lone puff for a few alphas
    for a in (0.3, 0.6, 0.85):
        vals = []
        for s in np.linspace(0.05, 0.95, 12):
            C = np.array([0, 0, 20.0]); D = np.array([[0, 0, 1.0]])
            _, al = shade_puff(D, np.array([3.0]), np.array([5.0]), C, 3.0, np.array([0.5, 0.5, 0.5]), a, s, 0, 0.3, np.array([1e9]),
                               np.array([0, 1.0, 0]), np.ones(3), np.ones(3) * 0.5, 1.0, 12)
            vals.append(al[0])
        print('alpha %.2f -> centre opacity %.2f' % (a, np.mean(vals)))
    img = render(scene_test(rng), steps=steps)
    Image.fromarray((img ** (1 / 1.0) * 255).astype(np.uint8)).save(out)
    print('wrote', out)
