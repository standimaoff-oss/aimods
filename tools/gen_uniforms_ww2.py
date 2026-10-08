#!/usr/bin/env python3
"""Generate 6 WWII uniform sets (3 USSR RKKA + 3 Germany Wehrmacht) into uniforms.glb,
plus item icons, item models, recipes, and localization (en_us.json & ru_ru.json).

Sets:
  - rkka_rifleman : Red Army Rifleman M1943 with SSh-40 helmet & SN-42 steel breastplate
  - rkka_officer  : Red Army Officer M1943 with visor cap, Sam Browne belt & Orders
  - rkka_winter   : Red Army Winter Soldier with Ushanka, quilted Telogreika & Valenki
  - wehr_soldat   : Wehrmacht Infantryman M40 with Stahlhelm M40, Feldbluse & Kar98k pouches
  - wehr_offizier : Wehrmacht Officer with Schirmmuetze, Officer Feldbluse & Iron Cross
  - wehr_panzer   : Panzerwaffe Tank Crew with black Panzerjacke, pink piping & headset
"""
import io
import json
import math
import os
import struct
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "mods", "aiarsenal", "src", "main", "resources")
GLB_PATH = os.path.join(RES, "assets", "aiarsenal", "models", "glb", "uniforms.glb")
TEX_ITEM = os.path.join(RES, "assets", "aiarsenal", "textures", "item")
MOD_ITEM = os.path.join(RES, "assets", "aiarsenal", "models", "item")
RECIPES = os.path.join(RES, "data", "aiarsenal", "recipes")
LANG_DIR = os.path.join(RES, "assets", "aiarsenal", "lang")

WW2_SETS = [
    "rkka_rifleman",
    "rkka_officer",
    "rkka_winter",
    "wehr_soldat",
    "wehr_offizier",
    "wehr_panzer",
]


# ---------------------------------------------------------------------------
# 1. Procedural textures (PIL + numpy)
# ---------------------------------------------------------------------------
def vnoise(S, cells, seed):
    r = np.random.default_rng(seed)
    g = r.uniform(-1, 1, (cells + 1, cells + 1))
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]
    y, x = np.mgrid[0:S, 0:S] / S * cells
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = x - x0
    fy = y - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = g[y0, x0]
    b = g[y0, x0 + 1]
    c = g[y0 + 1, x0]
    d = g[y0 + 1, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def fbm(S, base, octv, seed):
    v = np.zeros((S, S))
    amp = 1.0
    tot = 0.0
    for i in range(octv):
        c = base * (2 ** i)
        if c > S:
            break
        v += vnoise(S, c, seed + 17 * i) * amp
        tot += amp
        amp *= 0.5
    return v / tot


def weave(a, amt=6.0, seed=3):
    S = a.shape[0]
    y, x = np.mgrid[0:S, 0:a.shape[1]]
    w = (((x // 1) % 2) ^ ((y // 1) % 2)) * amt - amt / 2
    n = np.random.default_rng(seed).normal(0, amt * 0.35, a.shape[:2])
    a = a.astype(float)
    a[..., :3] += (w + n)[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


def flat_tex(col, S=64, amt=6.5, seed=1, grain=0.10):
    n = fbm(S, 4, 4, seed)
    a = np.zeros((S, S, 3), float)
    a[:] = col
    a *= (1 + n[..., None] * grain)
    return Image.fromarray(weave(a, amt, seed), "RGB")


def telogreika_tex(S=128):
    """Soviet WWII quilted winter vatnik (telogreika) with vertical stitch channels."""
    n = fbm(S, 4, 4, 91)
    base = np.array((128, 118, 84), float)
    a = np.zeros((S, S, 3), float)
    a[:] = base
    a *= (1 + n[..., None] * 0.11)
    y, x = np.mgrid[0:S, 0:S]
    # Vertical quilting ribs every 16 px
    rib = np.sin((x % 16) / 16.0 * math.pi)
    shade = 0.86 + 0.20 * rib
    a *= shade[..., None]
    # Stitch dots along the seams
    seam = ((x % 16 == 0) | (x % 16 == 15)) & ((y % 4) < 2)
    a[seam] *= 0.72
    return Image.fromarray(weave(a, 5.5, 92), "RGB")


def sn42_steel_tex(S=128):
    """Soviet SN-42 steel breastplate armor: protective olive-green painted steel with subtle wear."""
    n = fbm(S, 4, 4, 105)
    scratches = fbm(S, 16, 2, 109)
    base = np.array((62, 68, 48), float)
    a = np.zeros((S, S, 3), float)
    a[:] = base * (1 + n[..., None] * 0.08)
    # Metallic glint on worn edges
    glint = np.clip((scratches - 0.32) * 8.0, 0, 1)[..., None]
    a = a * (1 - glint * 0.35) + np.array((130, 136, 128), float) * (glint * 0.35)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def ushanka_fur_tex(S=64):
    """Thick grey-brown sheepskin fur for the WWII RKKA winter ushanka."""
    n1 = fbm(S, 8, 4, 121)
    n2 = fbm(S, 16, 3, 127)
    base = np.array((132, 124, 112), float)
    a = np.zeros((S, S, 3), float)
    a[:] = base * (1 + n1[..., None] * 0.16 + n2[..., None] * 0.10)
    return Image.fromarray(weave(a, 9.0, 129), "RGB")


def star_draw(d, cx, cy, R, col, outline=None, rot=-90, width=4):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        r = R if i % 2 == 0 else R * 0.40
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=col, outline=outline, width=width if outline else 0)


def make_pogon_rkka_rifle():
    W, H, SS = 96, 40, 4
    im = Image.new("RGBA", (W * SS, H * SS), (156, 28, 38, 255))  # crimson piping
    d = ImageDraw.Draw(im)
    d.rectangle([3 * SS, 3 * SS, (W - 3) * SS, (H - 3) * SS], fill=(104, 102, 68, 255))
    # Sergeant red stripe (лычка) near outer edge
    for i in range(2):
        x = (14 + i * 8) * SS
        d.rectangle([x, 4 * SS, x + 4 * SS, (H - 4) * SS], fill=(176, 32, 36, 255))
    bx = (W - 10) * SS
    d.ellipse([bx - 4 * SS, H * SS // 2 - 4 * SS, bx + 4 * SS, H * SS // 2 + 4 * SS],
              fill=(206, 170, 64, 255), outline=(120, 96, 36, 255))
    return im.resize((W, H), Image.LANCZOS).convert("RGB")


def make_pogon_rkka_off():
    W, H, SS = 96, 40, 4
    im = Image.new("RGBA", (W * SS, H * SS), (164, 26, 36, 255))  # crimson border
    d = ImageDraw.Draw(im)
    d.rectangle([3 * SS, 3 * SS, (W - 3) * SS, (H - 3) * SS], fill=(214, 180, 74, 255))
    # Central crimson stripe (просвет)
    cy = H * SS // 2
    d.rectangle([4 * SS, cy - 2 * SS, (W - 6) * SS, cy + 2 * SS], fill=(168, 26, 36, 255))
    # 4 silver officer stars (Captain RKKA)
    for (u, v) in [(0.34, -0.22), (0.34, 0.22), (0.55, 0.0), (0.74, 0.0)]:
        star_draw(d, u * W * SS, cy + v * H * SS, 0.13 * H * SS, (235, 238, 242), outline=(110, 112, 118), width=SS)
    bx = (W - 10) * SS
    d.ellipse([bx - 4 * SS, cy - 4 * SS, bx + 4 * SS, cy + 4 * SS],
              fill=(218, 184, 72, 255), outline=(120, 96, 36, 255))
    return im.resize((W, H), Image.LANCZOS).convert("RGB")


def make_pogon_wehr(field_col, pipe_col, braid=False):
    W, H, SS = 96, 40, 4
    im = Image.new("RGBA", (W * SS, H * SS), pipe_col)
    d = ImageDraw.Draw(im)
    d.rectangle([3 * SS, 3 * SS, (W - 3) * SS, (H - 3) * SS], fill=field_col)
    cy = H * SS // 2
    if braid:
        # Silver bullion officer braid + 2 gold pips (Hauptmann)
        for x in range(6 * SS, (W - 8) * SS, 5 * SS):
            d.rectangle([x, 5 * SS, x + 3 * SS, (H - 5) * SS], fill=(212, 216, 222, 255))
        for u in (0.35, 0.62):
            cx = int(u * W * SS)
            r = 5 * SS
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)],
                      fill=(218, 184, 70, 255), outline=(120, 92, 30, 255))
    bx = (W - 10) * SS
    d.ellipse([bx - 4 * SS, cy - 4 * SS, bx + 4 * SS, cy + 4 * SS],
              fill=(185, 190, 192, 255), outline=(90, 94, 96, 255))
    return im.resize((W, H), Image.LANCZOS).convert("RGB")


def png_bytes(im):
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# Extra palette swatches in row 3 of palette.png (indices 24..31):
PAL_ROW3 = [
    (24, 52, 42),      # 24: WEHR_COLLAR (dark bottle-green collar/band)
    (225, 110, 145),   # 25: PANZER_PINK (Waffenfarbe Rosa)
    (156, 26, 38),     # 26: RKKA_CRIMSON (RKKA officer raspberry/crimson)
    (58, 66, 44),      # 27: SSH40_GREEN (Soviet SSh-40 steel helmet green)
    (60, 66, 60),      # 28: STAHLHELM_GREY (Wehrmacht M40 steel helmet slate-feldgrau)
    (116, 70, 38),     # 29: AMMO_LEATHER (WWII reddish-brown leather pouches/holster)
    (86, 90, 84),      # 30: GUNMETAL (steel buckles, Iron Cross core, weapons)
    (228, 232, 238),   # 31: SILVER_LITZEN (bright silver braid, Litzen, medals)
]

# Existing palette indices (rows 0..2) + our new row 3:
GOLD      = (0, 0)
GOLD_L    = (1, 0)
RED       = (2, 0)
SILVER    = (3, 0)
BLACK     = (4, 0)
DARK      = (5, 0)
OLIVE_D   = (6, 0)
TAN_D     = (7, 0)
TAN       = (0, 1)
TAN_L     = (1, 1)
BROWN     = (2, 1)
BROWN_L   = (3, 1)
NAVY      = (4, 1)
WHITE     = (5, 1)
CHARCOAL  = (6, 1)
TAUPE     = (7, 1)
GREEN_US  = (0, 2)
OLIVE_L   = (1, 2)
BROWN_X   = (2, 2)
RUBBER    = (3, 2)
RED_L     = (4, 2)
KHAKI     = (5, 2)
CREAM     = (6, 2)
MAROON    = (7, 2)

WEHR_COLLAR    = (0, 3)
PANZER_PINK    = (1, 3)
RKKA_CRIMSON   = (2, 3)
SSH40_GREEN    = (3, 3)
STAHLHELM_GREY = (4, 3)
AMMO_LEATHER   = (5, 3)
GUNMETAL       = (6, 3)
SILVER_LITZEN  = (7, 3)


def pal_uv_gltf(cell):
    """Return glTF (u, v) for an (col, row) swatch in palette.png."""
    c, r = cell
    u = (c + 0.5) / 8.0
    v_blender = (7 - r + 0.5) / 8.0
    return (u, 1.0 - v_blender)


# ---------------------------------------------------------------------------
# 2. Pure-Python 3D mesh builder matching Blender Z-up -> glTF Y-up export
# ---------------------------------------------------------------------------
def b2g_pos(x, y, z):
    """Blender (x, y, z) -> glTF (x, z, -y)."""
    return (float(x), float(z), float(-y))


def b2g_nrm(nx, ny, nz):
    l = math.sqrt(nx * nx + ny * ny + nz * nz)
    if l > 1e-8:
        nx, ny, nz = nx / l, ny / l, nz / l
    return (float(nx), float(nz), float(-ny))


def rot_x_pt(pt, deg, pivot):
    x, y, z = pt[0] - pivot[0], pt[1] - pivot[1], pt[2] - pivot[2]
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    ny = y * ca - z * sa
    nz = y * sa + z * ca
    return (x + pivot[0], ny + pivot[1], nz + pivot[2])


def rot_x_n(n, deg):
    nx, ny, nz = n
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return (nx, ny * ca - nz * sa, ny * sa + nz * ca)


def mirror_x(b):
    x0, x1, y0, y1, z0, z1 = b
    return (-x1, -x0, y0, y1, z0, z1)


class MeshBuilder:
    """Collects quads/triangles in Blender coordinates, computes UVs, outputs glTF buffers."""

    def __init__(self):
        self.faces = []  # list of (verts_list_blender, normal_blender)

    def add_box(self, b, bevel_top=0.0):
        x0, x1, y0, y1, z0, z1 = b
        if bevel_top > 0.0:
            # Chamfered top dome for helmets/caps
            d = bevel_top
            zt = z1 - d
            xm0, xm1 = x0 + d * 0.85, x1 - d * 0.85
            ym0, ym1 = y0 + d * 0.85, y1 - d * 0.85
            # Bottom
            self.faces.append(([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0, 0, -1)))
            # Lower sides (z0 .. zt)
            self.faces.append(([(x0, y0, z0), (x1, y0, z0), (x1, y0, zt), (x0, y0, zt)], (0, -1, 0)))
            self.faces.append(([(x1, y1, z0), (x0, y1, z0), (x0, y1, zt), (x1, y1, zt)], (0, 1, 0)))
            self.faces.append(([(x0, y1, z0), (x0, y0, z0), (x0, y0, zt), (x0, y1, zt)], (-1, 0, 0)))
            self.faces.append(([(x1, y0, z0), (x1, y1, z0), (x1, y1, zt), (x1, y0, zt)], (1, 0, 0)))
            # Chamfer slopes (zt .. z1)
            self.faces.append(([(x0, y0, zt), (x1, y0, zt), (xm1, ym0, z1), (xm0, ym0, z1)], (0, -0.707, 0.707)))
            self.faces.append(([(x1, y1, zt), (x0, y1, zt), (xm0, ym1, z1), (xm1, ym1, z1)], (0, 0.707, 0.707)))
            self.faces.append(([(x0, y1, zt), (x0, y0, zt), (xm0, ym0, z1), (xm0, ym1, z1)], (-0.707, 0, 0.707)))
            self.faces.append(([(x1, y0, zt), (x1, y1, zt), (xm1, ym1, z1), (xm1, ym0, z1)], (0.707, 0, 0.707)))
            # Top cap
            self.faces.append(([(xm0, ym0, z1), (xm1, ym0, z1), (xm1, ym1, z1), (xm0, ym1, z1)], (0, 0, 1)))
            return
        self.faces.append(([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0, 0, -1)))
        self.faces.append(([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)))
        self.faces.append(([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)))
        self.faces.append(([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)))
        self.faces.append(([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)))
        self.faces.append(([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)))

    def add_crown(self, b, k_flare=1.24, front_lift=0.055):
        """Peaked visor-cap crown (flared top, raised front peak at -Y)."""
        x0, x1, y0, y1, z0, z1 = b
        v = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (x0 * k_flare, y0 * k_flare * 0.98, z1 + front_lift),
            (x1 * k_flare, y0 * k_flare * 0.98, z1 + front_lift),
            (x1 * k_flare, y1 * k_flare * 0.98, z1),
            (x0 * k_flare, y1 * k_flare * 0.98, z1),
        ]
        self.faces.append(([v[0], v[3], v[2], v[1]], (0, 0, -1)))
        self.faces.append(([v[4], v[5], v[6], v[7]], (0, 0.1, 0.99)))
        self.faces.append(([v[0], v[1], v[5], v[4]], (0, -1, 0)))
        self.faces.append(([v[2], v[3], v[7], v[6]], (0, 1, 0)))
        self.faces.append(([v[3], v[0], v[4], v[7]], (-1, 0, 0)))
        self.faces.append(([v[1], v[2], v[6], v[5]], (1, 0, 0)))

    def add_prism_xz(self, pts_xz, y0, y1):
        """Extrude a 2D polygon in (x, z) along Y from y0 to y1."""
        front = [(x, y0, z) for (x, z) in pts_xz]
        back = [(x, y1, z) for (x, z) in reversed(pts_xz)]
        self.faces.append((front, (0, -1, 0)))
        self.faces.append((back, (0, 1, 0)))
        n = len(pts_xz)
        for i in range(n):
            x0, z0 = pts_xz[i]
            x1, z1 = pts_xz[(i + 1) % n]
            dx, dz = x1 - x0, z1 - z0
            self.faces.append(([(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)], (dz, 0, -dx)))

    def transform_rot_x(self, deg, pivot):
        new_faces = []
        for fverts, fnrm in self.faces:
            nv = [rot_x_pt(p, deg, pivot) for p in fverts]
            nn = rot_x_n(fnrm, deg)
            new_faces.append((nv, nn))
        self.faces = new_faces

    def build_gltf_Buffers(self, pal=None, uv_mode="box", scale=1.3, show="-Y", flip=False):
        pos_list = []
        nrm_list = []
        uv_list = []
        idx_list = []

        if pal is not None:
            puv = pal_uv_gltf(pal)
        elif uv_mode == "fit":
            ax = {"X": 0, "Y": 1, "Z": 2}[show[1]]
            sg = -1 if show[0] == "-" else 1
            sel_pts = []
            for fverts, fnrm in self.faces:
                if fnrm[ax] * sg > 0.5:
                    sel_pts.extend(fverts)
            if not sel_pts:
                sel_pts = [p for fv, _ in self.faces for p in fv]

            def rng(i):
                vals = [p[i] for p in sel_pts]
                return min(vals), max(vals)

            if ax == 1:  # -Y or +Y
                (ua, ub), (va, vb) = rng(0), rng(2)
                gu, gv = (lambda p: p[0]), (lambda p: p[2])
            elif ax == 2:  # +Z or -Z
                (ua, ub), (va, vb) = rng(0), rng(1)
                gu = (lambda p: -p[0]) if flip else (lambda p: p[0])
                if flip:
                    ua, ub = -ub, -ua
                gv = lambda p: p[1]
            else:  # -X or +X
                (ua, ub), (va, vb) = rng(1), rng(2)
                if sg > 0:
                    gu = lambda p: p[1]
                else:
                    ua, ub = -ub, -ua
                    gu = lambda p: -p[1]
                gv = lambda p: p[2]
            du, dv = max(ub - ua, 1e-6), max(vb - va, 1e-6)

        for fverts, fnrm in self.faces:
            base_idx = len(pos_list)
            gn = b2g_nrm(*fnrm)
            nx, ny, nz = abs(fnrm[0]), abs(fnrm[1]), abs(fnrm[2])
            for p in fverts:
                pos_list.append(b2g_pos(*p))
                nrm_list.append(gn)
                if pal is not None:
                    uv_list.append(puv)
                elif uv_mode == "box":
                    if nz >= nx and nz >= ny:
                        u_b, v_b = p[0] * scale, p[1] * scale
                    elif ny >= nx:
                        u_b, v_b = p[0] * scale, p[2] * scale
                    else:
                        u_b, v_b = p[1] * scale, p[2] * scale
                    uv_list.append((float(u_b + 0.5), float(1.0 - (v_b - 0.5))))
                else:  # fit
                    inside = (fnrm[ax] * sg > 0.5)
                    if inside:
                        u_b = (gu(p) - ua) / du
                        v_b = (gv(p) - va) / dv
                    else:
                        u_b, v_b = 0.02, 0.5
                    uv_list.append((float(u_b), float(1.0 - v_b)))

            # Fan triangulation
            for k in range(1, len(fverts) - 1):
                idx_list.extend([base_idx, base_idx + k, base_idx + k + 1])

        return pos_list, nrm_list, uv_list, idx_list


# ---------------------------------------------------------------------------
# 3. Geometry definitions for the 6 WWII uniform sets
# ---------------------------------------------------------------------------
E = 0.032
BODY = (-0.272, 0.272, -0.125 - E, 0.125 + E, 0.70, 1.52)
FY = BODY[2]   # -0.157 (front face in Blender)
BY = BODY[3]   # +0.157 (back face in Blender)
ARM_R = (-0.5 - E, -0.262, -0.150, 0.150, 0.84, 1.5 + E)
LEG_R = (-0.244 - 0.025, 0.002, -0.125 - 0.025, 0.125 + 0.025, 0.0, 0.78)


def build_all_ww2_nodes():
    nodes_out = []  # list of (node_name, tex_or_none, pal_or_none, pos, nrm, uv, idx)

    def add_box(name, b, tex=None, pal=None, uv="box", scale=1.3, show="-Y", flip=False, bevel_top=0.0, rot_x=None):
        mb = MeshBuilder()
        mb.add_box(b, bevel_top=bevel_top)
        if rot_x is not None:
            mb.transform_rot_x(rot_x[0], rot_x[1])
        pos, nrm, uvs, idx = mb.build_gltf_Buffers(pal=pal, uv_mode=uv, scale=scale, show=show, flip=flip)
        nodes_out.append((name, tex, pal, pos, nrm, uvs, idx))

    def add_boxes(name, bl, tex=None, pal=None, uv="box", scale=1.3, show="-Y", flip=False):
        mb = MeshBuilder()
        for b in bl:
            mb.add_box(b)
        pos, nrm, uvs, idx = mb.build_gltf_Buffers(pal=pal, uv_mode=uv, scale=scale, show=show, flip=flip)
        nodes_out.append((name, tex, pal, pos, nrm, uvs, idx))

    def add_crown(name, b, tex, k_flare=1.24, front_lift=0.055):
        mb = MeshBuilder()
        mb.add_crown(b, k_flare=k_flare, front_lift=front_lift)
        pos, nrm, uvs, idx = mb.build_gltf_Buffers(pal=None, uv_mode="box", scale=1.6)
        nodes_out.append((name, tex, None, pos, nrm, uvs, idx))

    def add_prism(name, pts_xz, y0, y1, tex=None, pal=None, uv="box", show="-Y"):
        mb = MeshBuilder()
        mb.add_prism_xz(pts_xz, y0, y1)
        pos, nrm, uvs, idx = mb.build_gltf_Buffers(pal=pal, uv_mode=uv, scale=1.3, show=show)
        nodes_out.append((name, tex, pal, pos, nrm, uvs, idx))

    # =========================================================================
    # SET 1: rkka_rifleman (Red Army M1943 Rifleman / Assault Engineer with SN-42)
    # =========================================================================
    s = "rkka_rifleman"
    # Head: SSh-40 steel helmet with red star
    add_box(f"{s}.head", (-0.306, 0.306, -0.316, 0.316, 1.79, 2.09), pal=SSH40_GREEN, bevel_top=0.09)
    add_box(f"{s}.head.brim", (-0.314, 0.314, -0.342, -0.18, 1.78, 1.815), pal=SSH40_GREEN)
    add_box(f"{s}.head.skirt", (-0.318, 0.318, -0.06, 0.328, 1.67, 1.80), pal=SSH40_GREEN)
    add_box(f"{s}.head.star", (-0.038, 0.038, -0.326, -0.314, 1.88, 1.96), pal=RED)
    add_boxes(f"{s}.head.strap", [(0.252, 0.264, -0.04, 0.02, 1.54, 1.70), (-0.264, -0.252, -0.04, 0.02, 1.54, 1.70)], pal=BROWN)

    # Body: Gymnastyorka M43 + SN-42 Steel Breastplate (Стальной нагрудник СН-42) + Belt & Pouches
    add_box(f"{s}.body", BODY, tex="rkka_gym")
    add_boxes(f"{s}.body.collar", [(-0.19, 0.19, -0.162, 0.162, 1.52, 1.575)], tex="rkka_gym")
    # SN-42 articulated steel breastplate (upper torso plate + lower groin/abdomen plate + shoulder straps)
    add_box(f"{s}.body.sn42_top", (-0.245, 0.245, FY - 0.024, FY, 1.00, 1.48), tex="sn42_steel")
    add_box(f"{s}.body.sn42_bot", (-0.210, 0.210, FY - 0.020, FY, 0.74, 1.01), tex="sn42_steel")
    add_boxes(f"{s}.body.sn42_straps", [
        (-0.23, -0.15, FY - 0.026, BY + 0.015, 1.47, 1.535),
        (0.15, 0.23, FY - 0.026, BY + 0.015, 1.47, 1.535),
        (-0.02, 0.02, FY - 0.028, FY - 0.022, 0.96, 1.45),
    ], pal=OLIVE_D)
    # Leather belt + brass buckle + Mosin ammo pouches
    add_box(f"{s}.body.belt", (BODY[0] - 0.008, BODY[1] + 0.008, BODY[2] - 0.028, BODY[3] + 0.008, 0.84, 0.90), pal=BROWN)
    add_box(f"{s}.body.buckle", (-0.042, 0.042, FY - 0.034, FY - 0.024, 0.835, 0.905), pal=GOLD)
    add_boxes(f"{s}.body.pouches", [
        (-0.22, -0.09, FY - 0.052, FY - 0.020, 0.80, 0.93),
        (0.09, 0.22, FY - 0.052, FY - 0.020, 0.80, 0.93),
    ], pal=AMMO_LEATHER)

    # Arms, Legs, Boots
    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", A, tex="rkka_gym")
        add_box(f"{s}.arm_{side}.board", m((-0.495, -0.262, -0.058, 0.058, A[5], A[5] + 0.016)),
                tex="pogon_rkka_rifle", uv="fit", show="+Z", flip=(sx > 0))
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.004, A[1] + 0.004, A[2] - 0.004, A[3] + 0.004, 0.84, 0.88), tex="rkka_gym")

        add_box(f"{s}.leg_{side}", L, tex="rkka_gym")
        ox = L[0] if sx < 0 else L[1]
        flare = (ox - 0.018, ox, -0.09, 0.09, 0.42, 0.68) if sx < 0 else (ox, ox + 0.018, -0.09, 0.09, 0.42, 0.68)
        add_box(f"{s}.leg_{side}.galife", flare, tex="rkka_gym")

        add_box(f"{s}.boot_{side}", m((-0.292, -0.002, -0.174, 0.174, 0.0, 0.34)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.274, -0.02, -0.218, -0.17, 0.0, 0.11)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.sole", m((-0.298, 0.004, -0.224, 0.180, 0.0, 0.036)), pal=RUBBER)

    # =========================================================================
    # SET 2: rkka_officer (Red Army M1943 Officer with Visor Cap & Orders)
    # =========================================================================
    s = "rkka_officer"
    # Head: RKKA Officer Visor Cap (Фуражка обр. 1943)
    add_box(f"{s}.head", (-0.272, 0.272, -0.282, 0.282, 1.84, 1.94), pal=RKKA_CRIMSON)
    add_crown(f"{s}.head.crown", (-0.276, 0.276, -0.286, 0.286, 1.94, 2.04), tex="rkka_gym", k_flare=1.26, front_lift=0.062)
    add_box(f"{s}.head.visor", (-0.24, 0.24, -0.42, -0.27, 1.835, 1.855), tex="visor_black", uv="fit", show="+Z",
            rot_x=(18, (0, -0.27, 1.845)))
    add_box(f"{s}.head.cord", (-0.25, 0.25, -0.292, -0.282, 1.855, 1.872), pal=GOLD)
    add_box(f"{s}.head.star", (-0.030, 0.030, -0.298, -0.282, 1.878, 1.938), pal=RED)
    add_box(f"{s}.head.piping", (-0.278, 0.278, -0.288, 0.288, 1.935, 1.946), pal=RKKA_CRIMSON)

    # Body: M43 Officer Tunic + Sam Browne cross-belt + TT holster + Order of the Red Star
    add_box(f"{s}.body", BODY, tex="rkka_gym")
    add_boxes(f"{s}.body.collar", [(-0.195, 0.195, -0.163, 0.163, 1.52, 1.58)], tex="rkka_gym")
    add_box(f"{s}.body.collar_pipe", (-0.198, 0.198, FY - 0.008, FY, 1.568, 1.582), pal=GOLD)
    add_boxes(f"{s}.body.placket", [(-0.022, 0.022, FY - 0.010, FY, 1.15, 1.52)], tex="rkka_gym")
    add_boxes(f"{s}.body.buttons", [(-0.014, 0.014, FY - 0.016, FY, z - 0.014, z + 0.014) for z in (1.46, 1.36, 1.26, 1.16)], pal=GOLD)
    add_boxes(f"{s}.body.pockets", [
        (-0.22, -0.06, FY - 0.012, FY, 1.14, 1.33),
        (0.06, 0.22, FY - 0.012, FY, 1.14, 1.33),
        (-0.225, -0.055, FY - 0.016, FY, 1.29, 1.345),
        (0.055, 0.225, FY - 0.016, FY, 1.29, 1.345),
    ], tex="rkka_gym")
    # Sam Browne cross-strap + officer belt + TT-33 holster
    add_prism(f"{s}.body.sambrowne", [(-0.22, 1.52), (-0.16, 1.52), (0.14, 0.88), (0.08, 0.88)], FY - 0.019, FY - 0.010, pal=AMMO_LEATHER)
    add_box(f"{s}.body.belt", (BODY[0] - 0.008, BODY[1] + 0.008, BODY[2] - 0.018, BODY[3] + 0.008, 0.84, 0.90), pal=AMMO_LEATHER)
    add_box(f"{s}.body.buckle", (-0.042, 0.042, FY - 0.025, FY - 0.015, 0.835, 0.905), pal=GOLD_L)
    add_box(f"{s}.body.holster", (-0.288, -0.22, -0.10, 0.06, 0.72, 0.91), pal=AMMO_LEATHER)
    # Order of the Red Star (right chest) & ribbon bar (left chest)
    add_box(f"{s}.body.order_star", (-0.165, -0.115, FY - 0.020, FY - 0.012, 1.365, 1.415), pal=RED)
    add_box(f"{s}.body.ribbons", (0.08, 0.22, FY - 0.016, FY, 1.365, 1.40), tex="ribbons_colonel", uv="fit", show="-Y")

    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", A, tex="rkka_gym")
        add_box(f"{s}.arm_{side}.board", m((-0.495, -0.262, -0.058, 0.058, A[5], A[5] + 0.016)),
                tex="pogon_rkka_off", uv="fit", show="+Z", flip=(sx > 0))
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.005, A[1] + 0.005, A[2] - 0.005, A[3] + 0.005, 0.86, 0.88), pal=RKKA_CRIMSON)

        add_box(f"{s}.leg_{side}", L, tex="rkka_breeches")
        ox = L[0] if sx < 0 else L[1]
        flare = (ox - 0.020, ox, -0.09, 0.09, 0.42, 0.70) if sx < 0 else (ox, ox + 0.020, -0.09, 0.09, 0.42, 0.70)
        add_box(f"{s}.leg_{side}.galife", flare, tex="rkka_breeches")
        kant = (ox - 0.022, ox - 0.016, -0.012, 0.012, 0.34, 0.77) if sx < 0 else (ox + 0.016, ox + 0.022, -0.012, 0.012, 0.34, 0.77)
        add_box(f"{s}.leg_{side}.kant", kant, pal=RKKA_CRIMSON)

        add_box(f"{s}.boot_{side}", m((-0.292, -0.002, -0.174, 0.174, 0.0, 0.36)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.274, -0.02, -0.218, -0.17, 0.0, 0.11)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.sole", m((-0.298, 0.004, -0.224, 0.180, 0.0, 0.032)), pal=BLACK)

    # =========================================================================
    # SET 3: rkka_winter (Red Army Winter Vatnik / Telogreika & Ushanka)
    # =========================================================================
    s = "rkka_winter"
    # Head: Ushanka fur hat with ear flaps and red star
    add_box(f"{s}.head", (-0.295, 0.295, -0.300, 0.300, 1.82, 2.09), tex="rkka_telogreika", bevel_top=0.05)
    add_box(f"{s}.head.visor_fur", (-0.285, 0.285, -0.332, -0.26, 1.83, 1.98), tex="ushanka_fur")
    add_boxes(f"{s}.head.earflaps", [
        (-0.332, -0.265, -0.22, 0.20, 1.66, 1.96),
        (0.265, 0.332, -0.22, 0.20, 1.66, 1.96),
        (-0.310, 0.310, 0.24, 0.325, 1.72, 1.95),
    ], tex="ushanka_fur")
    add_box(f"{s}.head.star", (-0.036, 0.036, -0.342, -0.328, 1.87, 1.94), pal=RED)

    # Body: Padded quilted Telogreika (vatnik) + fur collar + belt & pouches
    WBODY = (-0.284, 0.284, -0.168, 0.168, 0.69, 1.525)
    WFY = WBODY[2]
    add_box(f"{s}.body", WBODY, tex="rkka_telogreika")
    add_box(f"{s}.body.collar", (-0.21, 0.21, -0.172, 0.175, 1.51, 1.585), tex="ushanka_fur")
    add_box(f"{s}.body.placket", (-0.05, 0.05, WFY - 0.010, WFY, 0.70, 1.51), tex="rkka_telogreika")
    add_boxes(f"{s}.body.buttons", [(-0.035, -0.012, WFY - 0.016, WFY, z - 0.014, z + 0.014) for z in (1.40, 1.24, 1.08, 0.92, 0.76)], pal=DARK)
    add_box(f"{s}.body.belt", (WBODY[0] - 0.006, WBODY[1] + 0.006, WBODY[2] - 0.014, WBODY[3] + 0.006, 0.85, 0.91), pal=BROWN)
    add_box(f"{s}.body.buckle", (-0.042, 0.042, WFY - 0.022, WFY - 0.012, 0.845, 0.915), pal=GOLD)
    add_boxes(f"{s}.body.pouches", [
        (-0.22, -0.09, WFY - 0.042, WFY - 0.012, 0.81, 0.94),
        (0.09, 0.22, WFY - 0.042, WFY - 0.012, 0.81, 0.94),
    ], pal=AMMO_LEATHER)

    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", (A[0] - 0.008, A[1] + 0.008, A[2] - 0.008, A[3] + 0.008, A[4], A[5]), tex="rkka_telogreika")
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.012, A[1] + 0.012, A[2] - 0.012, A[3] + 0.012, 0.84, 0.89), tex="rkka_telogreika")

        add_box(f"{s}.leg_{side}", (L[0] - 0.006, L[1] + 0.006, L[2] - 0.006, L[3] + 0.006, L[4], L[5]), tex="rkka_telogreika")
        # Valenki felt winter boots with dark rubber galoshes
        add_box(f"{s}.boot_{side}", m((-0.296, -0.002, -0.178, 0.178, 0.0, 0.35)), tex="valenki_felt", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.280, -0.018, -0.222, -0.172, 0.0, 0.12)), pal=RUBBER)
        add_box(f"{s}.boot_{side}.galosh", m((-0.302, 0.004, -0.226, 0.184, 0.0, 0.085)), pal=RUBBER)

    # =========================================================================
    # SET 4: wehr_soldat (Wehrmacht Infantryman M40 Feldgrau with Stahlhelm M40)
    # =========================================================================
    s = "wehr_soldat"
    # Head: Stahlhelm M40 with front visor, flared neck/ear skirt, side shield decal
    add_box(f"{s}.head", (-0.306, 0.306, -0.316, 0.316, 1.80, 2.09), pal=STAHLHELM_GREY, bevel_top=0.08)
    add_box(f"{s}.head.visor", (-0.314, 0.314, -0.350, -0.22, 1.79, 1.835), pal=STAHLHELM_GREY)
    add_box(f"{s}.head.skirt", (-0.324, 0.324, -0.08, 0.334, 1.66, 1.81), pal=STAHLHELM_GREY)
    add_boxes(f"{s}.head.decal", [
        (-0.328, -0.320, -0.16, -0.10, 1.83, 1.89),
        (0.320, 0.328, -0.16, -0.10, 1.83, 1.89),
    ], pal=SILVER_LITZEN)
    add_boxes(f"{s}.head.strap", [(0.252, 0.264, -0.04, 0.02, 1.54, 1.68), (-0.264, -0.252, -0.04, 0.02, 1.54, 1.68)], pal=BLACK)

    # Body: Feldbluse M40 + bottle-green collar + Litzen + Y-straps + belt & Kar98k pouches
    add_box(f"{s}.body", BODY, tex="feldgrau")
    add_box(f"{s}.body.collar", (-0.20, 0.20, -0.164, 0.164, 1.515, 1.578), pal=WEHR_COLLAR)
    add_boxes(f"{s}.body.litzen", [
        (-0.185, -0.125, FY - 0.012, FY, 1.525, 1.568),
        (0.125, 0.185, FY - 0.012, FY, 1.525, 1.568),
    ], pal=SILVER_LITZEN)
    add_boxes(f"{s}.body.buttons", [(-0.014, 0.014, FY - 0.014, FY, z - 0.014, z + 0.014) for z in (1.44, 1.31, 1.18, 1.05, 0.92)], pal=GUNMETAL)
    # 4 pleated patch pockets (2 breast + 2 lower skirt)
    add_boxes(f"{s}.body.pockets", [
        (-0.23, -0.06, FY - 0.012, FY, 1.15, 1.34),
        (0.06, 0.23, FY - 0.012, FY, 1.15, 1.34),
        (-0.24, -0.06, FY - 0.012, FY, 0.72, 0.84),
        (0.06, 0.24, FY - 0.012, FY, 0.72, 0.84),
    ], tex="feldgrau")
    # Y-straps (Koppeltragegestell) + black leather belt + silver Gott mit uns buckle + triple Kar98k pouches
    add_boxes(f"{s}.body.ystraps", [
        (-0.19, -0.14, FY - 0.018, BY + 0.014, 0.90, 1.53),
        (0.14, 0.19, FY - 0.018, BY + 0.014, 0.90, 1.53),
        (-0.025, 0.025, BY, BY + 0.016, 0.90, 1.48),
    ], pal=BLACK)
    add_box(f"{s}.body.belt", (BODY[0] - 0.008, BODY[1] + 0.008, BODY[2] - 0.020, BODY[3] + 0.008, 0.84, 0.90), pal=BLACK)
    add_box(f"{s}.body.buckle", (-0.044, 0.044, FY - 0.026, FY - 0.016, 0.835, 0.905), pal=SILVER_LITZEN)
    add_boxes(f"{s}.body.pouches", [
        (-0.235, -0.075, FY - 0.048, FY - 0.016, 0.81, 0.925),
        (0.075, 0.235, FY - 0.048, FY - 0.016, 0.81, 0.925),
    ], pal=BLACK)

    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", A, tex="feldgrau")
        add_box(f"{s}.arm_{side}.board", m((-0.495, -0.262, -0.058, 0.058, A[5], A[5] + 0.016)),
                tex="pogon_wehr_soldat", uv="fit", show="+Z", flip=(sx > 0))
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.004, A[1] + 0.004, A[2] - 0.004, A[3] + 0.004, 0.84, 0.885), tex="feldgrau")

        add_box(f"{s}.leg_{side}", L, tex="feldgrau")

        # Marschstiefel (Knobelbecher) jackboots
        add_box(f"{s}.boot_{side}", m((-0.292, -0.002, -0.174, 0.174, 0.0, 0.34)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.274, -0.02, -0.218, -0.17, 0.0, 0.11)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.sole", m((-0.298, 0.004, -0.224, 0.180, 0.0, 0.036)), pal=BLACK)

    # =========================================================================
    # SET 5: wehr_offizier (Wehrmacht Officer with Schirmmuetze & Iron Cross)
    # =========================================================================
    s = "wehr_offizier"
    # Head: High-peak Schirmmütze with dark-green band, white piping, silver cord, eagle & wreath
    add_box(f"{s}.head", (-0.272, 0.272, -0.282, 0.282, 1.84, 1.94), pal=WEHR_COLLAR)
    add_crown(f"{s}.head.crown", (-0.276, 0.276, -0.286, 0.286, 1.94, 2.05), tex="feldgrau", k_flare=1.24, front_lift=0.072)
    add_box(f"{s}.head.visor", (-0.24, 0.24, -0.42, -0.27, 1.835, 1.855), tex="visor_black", uv="fit", show="+Z",
            rot_x=(18, (0, -0.27, 1.845)))
    add_box(f"{s}.head.cord", (-0.25, 0.25, -0.292, -0.282, 1.855, 1.872), pal=SILVER_LITZEN)
    add_box(f"{s}.head.wreath", (-0.048, 0.048, -0.298, -0.282, 1.875, 1.925), pal=SILVER_LITZEN)
    add_box(f"{s}.head.cockade", (-0.018, 0.018, -0.302, -0.286, 1.888, 1.915), pal=RED)
    add_box(f"{s}.head.eagle", (-0.075, 0.075, -0.335, -0.318, 1.98, 2.025), pal=SILVER_LITZEN)
    add_box(f"{s}.head.piping", (-0.278, 0.278, -0.288, 0.288, 1.935, 1.946), pal=WHITE)

    # Body: Officer Feldbluse + bottle-green collar + silver Litzen + EK2 ribbon + EK1 badge + belt & P38 holster
    add_box(f"{s}.body", BODY, tex="feldgrau")
    add_box(f"{s}.body.collar", (-0.20, 0.20, -0.165, 0.165, 1.52, 1.585), pal=WEHR_COLLAR)
    add_boxes(f"{s}.body.litzen", [
        (-0.188, -0.122, FY - 0.014, FY, 1.528, 1.575),
        (0.122, 0.188, FY - 0.014, FY, 1.528, 1.575),
    ], pal=SILVER_LITZEN)
    add_boxes(f"{s}.body.buttons", [(-0.014, 0.014, FY - 0.015, FY, z - 0.014, z + 0.014) for z in (1.44, 1.31, 1.18, 1.05, 0.92)], pal=SILVER_LITZEN)
    # EK2 ribbon in buttonhole
    add_prism(f"{s}.body.ek2_ribbon", [(-0.01, 1.32), (0.01, 1.32), (0.06, 1.24), (0.04, 1.24)], FY - 0.017, FY - 0.010, pal=RED)
    add_boxes(f"{s}.body.pockets", [
        (-0.23, -0.06, FY - 0.012, FY, 1.15, 1.34),
        (0.06, 0.23, FY - 0.012, FY, 1.15, 1.34),
        (-0.24, -0.06, FY - 0.012, FY, 0.72, 0.84),
        (0.06, 0.24, FY - 0.012, FY, 0.72, 0.84),
    ], tex="feldgrau")
    # Iron Cross 1st Class (EK1) on left breast pocket (x > 0)
    add_boxes(f"{s}.body.ek1_frame", [
        (0.130, 0.160, FY - 0.020, FY - 0.012, 1.19, 1.27),
        (0.105, 0.185, FY - 0.020, FY - 0.012, 1.215, 1.245),
    ], pal=SILVER_LITZEN)
    add_boxes(f"{s}.body.ek1_core", [
        (0.134, 0.156, FY - 0.022, FY - 0.014, 1.196, 1.264),
        (0.111, 0.179, FY - 0.022, FY - 0.014, 1.219, 1.241),
    ], pal=BLACK)
    add_box(f"{s}.body.belt", (BODY[0] - 0.008, BODY[1] + 0.008, BODY[2] - 0.018, BODY[3] + 0.008, 0.84, 0.90), pal=BLACK)
    add_box(f"{s}.body.buckle", (-0.040, 0.040, FY - 0.024, FY - 0.014, 0.835, 0.905), pal=SILVER_LITZEN)
    add_box(f"{s}.body.holster", (0.21, 0.286, -0.11, 0.05, 0.73, 0.91), pal=BLACK)

    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", A, tex="feldgrau")
        add_box(f"{s}.arm_{side}.board", m((-0.495, -0.262, -0.058, 0.058, A[5], A[5] + 0.016)),
                tex="pogon_wehr_off", uv="fit", show="+Z", flip=(sx > 0))
        # French turn-back cuffs (deep officer cuffs)
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.006, A[1] + 0.006, A[2] - 0.006, A[3] + 0.006, 0.84, 0.92), tex="feldgrau")

        add_box(f"{s}.leg_{side}", L, tex="feldgrau")
        ox = L[0] if sx < 0 else L[1]
        flare = (ox - 0.020, ox, -0.09, 0.09, 0.42, 0.70) if sx < 0 else (ox, ox + 0.020, -0.09, 0.09, 0.42, 0.70)
        add_box(f"{s}.leg_{side}.breeches", flare, tex="feldgrau")

        add_box(f"{s}.boot_{side}", m((-0.292, -0.002, -0.174, 0.174, 0.0, 0.37)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.274, -0.02, -0.218, -0.17, 0.0, 0.11)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.sole", m((-0.298, 0.004, -0.224, 0.180, 0.0, 0.032)), pal=BLACK)

    # =========================================================================
    # SET 6: wehr_panzer (Panzerwaffe Tank Crew Sonderbekleidung with Headset)
    # =========================================================================
    s = "wehr_panzer"
    # Head: Black M43 Panzer cap / Schiffchen with rose-pink soutache + radio headphones!
    add_box(f"{s}.head", (-0.274, 0.274, -0.284, 0.284, 1.85, 2.06), tex="panzer_black", bevel_top=0.04)
    add_box(f"{s}.head.visor", (-0.21, 0.21, -0.41, -0.28, 1.85, 1.872), tex="panzer_black",
            rot_x=(10, (0, -0.28, 1.86)))
    add_box(f"{s}.head.soutache", (-0.045, 0.045, -0.294, -0.282, 1.86, 1.94), pal=PANZER_PINK)
    add_box(f"{s}.head.cockade", (-0.022, 0.022, -0.298, -0.284, 1.88, 1.93), pal=SILVER_LITZEN)
    # Tank crew radio headphones (Kopfhörer) over the ears + headband
    add_boxes(f"{s}.head.headphones", [
        (-0.312, -0.255, -0.09, 0.07, 1.66, 1.82),
        (0.255, 0.312, -0.09, 0.07, 1.66, 1.82),
        (-0.295, -0.265, -0.03, 0.01, 1.82, 2.07),
        (0.265, 0.295, -0.03, 0.01, 1.82, 2.07),
        (-0.285, 0.285, -0.03, 0.01, 2.055, 2.08),
    ], pal=GUNMETAL)

    # Body: Black double-breasted Panzerjacke with wide lapels & rose-pink Waffenfarbe piping
    add_box(f"{s}.body", BODY, tex="panzer_black")
    # Grey shirt + black tie inside V-neck
    add_prism(f"{s}.body.shirt", [(-0.12, 1.52), (0.0, 1.29), (0.12, 1.52)], FY - 0.005, FY, pal=CHARCOAL)
    # Wide double-breasted Panzerjacke lapels with rose-pink piping
    for sx_l, tag in ((-1, "r"), (1, "l")):
        pts = [(0.12, 1.52), (-0.03, 1.18), (0.08, 1.16), (0.24, 1.49)]
        if sx_l < 0:
            pts = [(-x, z) for (x, z) in pts][::-1]
        add_prism(f"{s}.body.lapel_{tag}", pts, FY - 0.014, FY - 0.003, tex="panzer_black")
    add_boxes(f"{s}.body.pink_pipe", [
        (-0.235, -0.115, FY - 0.016, FY - 0.010, 1.49, 1.505),
        (0.115, 0.235, FY - 0.016, FY - 0.010, 1.49, 1.505),
        (0.074, 0.088, FY - 0.016, FY - 0.008, 0.72, 1.22),
    ], pal=PANZER_PINK)
    add_boxes(f"{s}.body.insignia", [
        (-0.19, -0.14, FY - 0.020, FY - 0.012, 1.44, 1.48),
        (0.14, 0.19, FY - 0.020, FY - 0.012, 1.44, 1.48),
    ], pal=SILVER_LITZEN)
    # Silver Panzer Assault Badge & EK1 on left chest
    add_box(f"{s}.body.panzer_badge", (0.11, 0.17, FY - 0.018, FY - 0.010, 1.16, 1.24), pal=SILVER_LITZEN)
    add_box(f"{s}.body.belt", (BODY[0] - 0.006, BODY[1] + 0.006, BODY[2] - 0.014, BODY[3] + 0.006, 0.84, 0.895), pal=BLACK)
    add_box(f"{s}.body.buckle", (-0.040, 0.040, FY - 0.020, FY - 0.012, 0.835, 0.90), pal=SILVER_LITZEN)

    for side, sx in (("r", -1), ("l", 1)):
        A = ARM_R if sx < 0 else mirror_x(ARM_R)
        L = LEG_R if sx < 0 else mirror_x(LEG_R)
        m = lambda b, sx=sx: b if sx < 0 else mirror_x(b)
        add_box(f"{s}.arm_{side}", A, tex="panzer_black")
        add_box(f"{s}.arm_{side}.board", m((-0.495, -0.262, -0.058, 0.058, A[5], A[5] + 0.016)),
                tex="pogon_wehr_panzer", uv="fit", show="+Z", flip=(sx > 0))
        add_box(f"{s}.arm_{side}.cuff", (A[0] - 0.004, A[1] + 0.004, A[2] - 0.004, A[3] + 0.004, 0.84, 0.88), tex="panzer_black")

        add_box(f"{s}.leg_{side}", L, tex="panzer_black")

        add_box(f"{s}.boot_{side}", m((-0.290, -0.002, -0.172, 0.172, 0.0, 0.26)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.toe", m((-0.272, -0.02, -0.216, -0.17, 0.0, 0.10)), tex="leather_black", scale=2.0)
        add_box(f"{s}.boot_{side}.sole", m((-0.296, 0.004, -0.222, 0.178, 0.0, 0.034)), pal=BLACK)

    return nodes_out


# ---------------------------------------------------------------------------
# 4. Patch uniforms.glb in-place (idempotent: strips any prior ww2 nodes first)
# ---------------------------------------------------------------------------
def update_glb():
    with open(GLB_PATH, "rb") as f:
        raw = f.read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    gltf = json.loads(raw[20:20 + jlen].decode("utf-8"))
    bin_off = 20 + jlen + 8
    blob = bytearray(raw[bin_off:])

    # If we already ran before, strip previous WW2 nodes/meshes/materials/images?
    # Better: check if rkka_rifleman.body is already present; if so, restore from git first!
    if any(n.get("name", "").startswith(tuple(s + "." for s in WW2_SETS)) for n in gltf["nodes"]):
        os.system(f"git checkout -- {GLB_PATH}")
        with open(GLB_PATH, "rb") as f:
            raw = f.read()
        jlen = struct.unpack_from("<I", raw, 12)[0]
        gltf = json.loads(raw[20:20 + jlen].decode("utf-8"))
        bin_off = 20 + jlen + 8
        blob = bytearray(raw[bin_off:])

    def align4():
        while len(blob) % 4 != 0:
            blob.append(0)

    def append_bytes(data_bytes, target=None):
        align4()
        off = len(blob)
        blob.extend(data_bytes)
        bv = {"buffer": 0, "byteLength": len(data_bytes), "byteOffset": off}
        if target is not None:
            bv["target"] = target
        idx = len(gltf["bufferViews"])
        gltf["bufferViews"].append(bv)
        return idx

    # 1. Update palette.png in-place with Row 3 swatches
    pal_img_idx = next(i for i, im in enumerate(gltf["images"]) if im["name"] == "palette")
    pal_bv_idx = gltf["images"][pal_img_idx]["bufferView"]
    pal_bv = gltf["bufferViews"][pal_bv_idx]
    pal_im = Image.open(io.BytesIO(bytes(blob[pal_bv["byteOffset"]:pal_bv["byteOffset"] + pal_bv["byteLength"]]))).convert("RGB")
    d = ImageDraw.Draw(pal_im)
    for col_i, rgb in enumerate(PAL_ROW3):
        x, y = col_i * 8, 3 * 8
        d.rectangle([x, y, x + 7, y + 7], fill=rgb)
    new_pal_bytes = png_bytes(pal_im)
    new_pal_bv = append_bytes(new_pal_bytes)
    gltf["images"][pal_img_idx]["bufferView"] = new_pal_bv

    # 2. Register new textures/materials
    new_textures = {
        "rkka_gym": flat_tex((112, 108, 72), 128, 6.5, 201, 0.11),
        "rkka_breeches": flat_tex((30, 40, 66), 128, 5.5, 202, 0.09),
        "rkka_telogreika": telogreika_tex(128),
        "sn42_steel": sn42_steel_tex(128),
        "ushanka_fur": ushanka_fur_tex(64),
        "valenki_felt": flat_tex((68, 64, 58), 64, 8.0, 203, 0.14),
        "feldgrau": flat_tex((78, 88, 74), 128, 6.0, 204, 0.10),
        "panzer_black": flat_tex((26, 27, 30), 128, 5.0, 205, 0.08),
        "pogon_rkka_rifle": make_pogon_rkka_rifle(),
        "pogon_rkka_off": make_pogon_rkka_off(),
        "pogon_wehr_soldat": make_pogon_wehr((76, 86, 72, 255), (235, 235, 232, 255), braid=False),
        "pogon_wehr_off": make_pogon_wehr((24, 52, 42, 255), (225, 228, 232, 255), braid=True),
        "pogon_wehr_panzer": make_pogon_wehr((24, 25, 28, 255), (225, 110, 145, 255), braid=False),
    }

    mat_by_tex = {}
    for i, m in enumerate(gltf["materials"]):
        if m["name"].startswith("u_"):
            mat_by_tex[m["name"][2:]] = i

    sampler_idx = gltf["textures"][0].get("sampler", 0)
    for tname, pim in new_textures.items():
        bv_i = append_bytes(png_bytes(pim))
        img_i = len(gltf["images"])
        gltf["images"].append({"bufferView": bv_i, "mimeType": "image/png", "name": tname})
        tex_i = len(gltf["textures"])
        gltf["textures"].append({"sampler": sampler_idx, "source": img_i})
        mat_i = len(gltf["materials"])
        rough = 0.45 if tname == "sn42_steel" else 0.85
        metal = 0.35 if tname == "sn42_steel" else 0.0
        gltf["materials"].append({
            "doubleSided": True,
            "name": "u_" + tname,
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": tex_i},
                "metallicFactor": metal,
                "roughnessFactor": rough,
            },
        })
        mat_by_tex[tname] = mat_i

    # 3. Build and append all WW2 mesh nodes
    ww2_nodes = build_all_ww2_nodes()
    scene_nodes = gltf["scenes"][0]["nodes"]

    for (nname, tex_name, pal_cell, pos, nrm, uvs, idx) in ww2_nodes:
        mat_i = mat_by_tex["palette" if pal_cell is not None else tex_name]

        pos_bytes = struct.pack("<" + str(len(pos) * 3) + "f", *[c for p in pos for c in p])
        nrm_bytes = struct.pack("<" + str(len(nrm) * 3) + "f", *[c for n in nrm for c in n])
        uv_bytes = struct.pack("<" + str(len(uvs) * 2) + "f", *[c for u in uvs for c in u])
        idx_bytes = struct.pack("<" + str(len(idx)) + "H", *idx)

        bv_pos = append_bytes(pos_bytes, 34962)
        bv_nrm = append_bytes(nrm_bytes, 34962)
        bv_uv = append_bytes(uv_bytes, 34962)
        bv_idx = append_bytes(idx_bytes, 34963)

        pmin = [min(p[k] for p in pos) for k in range(3)]
        pmax = [max(p[k] for p in pos) for k in range(3)]

        acc_pos = len(gltf["accessors"])
        gltf["accessors"].append({
            "bufferView": bv_pos,
            "componentType": 5126,
            "count": len(pos),
            "max": pmax,
            "min": pmin,
            "type": "VEC3",
        })
        acc_nrm = len(gltf["accessors"])
        gltf["accessors"].append({
            "bufferView": bv_nrm,
            "componentType": 5126,
            "count": len(nrm),
            "type": "VEC3",
        })
        acc_uv = len(gltf["accessors"])
        gltf["accessors"].append({
            "bufferView": bv_uv,
            "componentType": 5126,
            "count": len(uvs),
            "type": "VEC2",
        })
        acc_idx = len(gltf["accessors"])
        gltf["accessors"].append({
            "bufferView": bv_idx,
            "componentType": 5123,
            "count": len(idx),
            "type": "SCALAR",
        })

        mesh_i = len(gltf["meshes"])
        gltf["meshes"].append({
            "name": nname,
            "primitives": [{
                "attributes": {
                    "POSITION": acc_pos,
                    "NORMAL": acc_nrm,
                    "TEXCOORD_0": acc_uv,
                },
                "indices": acc_idx,
                "material": mat_i,
            }],
        })
        node_i = len(gltf["nodes"])
        gltf["nodes"].append({"mesh": mesh_i, "name": nname})
        scene_nodes.append(node_i)

    align4()
    gltf["buffers"][0]["byteLength"] = len(blob)
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    while len(json_bytes) % 4 != 0:
        json_bytes += b" "

    total_len = 12 + 8 + len(json_bytes) + 8 + len(blob)
    out = bytearray()
    out.extend(struct.pack("<III", 0x46546C67, 2, total_len))
    out.extend(struct.pack("<II", len(json_bytes), 0x4E4F534A))
    out.extend(json_bytes)
    out.extend(struct.pack("<II", len(blob), 0x004E4942))
    out.extend(blob)

    with open(GLB_PATH, "wb") as f:
        f.write(out)

    print(f"Updated {GLB_PATH}: {len(gltf['nodes'])} nodes, {len(out)} bytes")
    return ww2_nodes, new_textures, pal_im


# ---------------------------------------------------------------------------
# 5. Render 96x96 3D item icons for all 24 WWII armor items
# ---------------------------------------------------------------------------
def render_ww2_icons(ww2_nodes, new_textures, pal_im):
    os.makedirs(TEX_ITEM, exist_ok=True)
    # Load existing textures from uniforms.glb for leather_black, visor_black, ribbons_colonel
    with open(GLB_PATH, "rb") as f:
        raw = f.read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    gltf = json.loads(raw[20:20 + jlen].decode("utf-8"))
    bin_off = 20 + jlen + 8
    blob = raw[bin_off:]

    tex_map = dict(new_textures)
    tex_map["palette"] = pal_im
    for im_info in gltf["images"]:
        nm = im_info["name"]
        if nm not in tex_map:
            bv = gltf["bufferViews"][im_info["bufferView"]]
            b = blob[bv["byteOffset"]:bv["byteOffset"] + bv["byteLength"]]
            tex_map[nm] = Image.open(io.BytesIO(b)).convert("RGB")

    # Group nodes by (set, slot)
    slot_prefixes = {
        "head": ("head",),
        "chest": ("body", "arm_r", "arm_l"),
        "legs": ("leg_r", "leg_l"),
        "feet": ("boot_r", "boot_l"),
    }

    # Isometric 3/4 view transform (glTF Y-up, front is +Z)
    yaw = math.radians(-28.0)
    pitch = math.radians(18.0)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def cam_pt(p):
        x, y, z = p
        # Rotate around Y by yaw, then around X by pitch
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        y2 = y * cp - z1 * sp
        z2 = y * sp + z1 * cp
        return (x1, y2, z2)

    light_dir = (0.42, 0.65, 0.63)

    for s in WW2_SETS:
        for slot, prefs in slot_prefixes.items():
            part_nodes = [
                n for n in ww2_nodes
                if any(n[0] == f"{s}.{p}" or n[0].startswith(f"{s}.{p}.") for p in prefs)
            ]
            # Per-pixel Z-buffer rasterizer with UV texture sampling (2x supersampled -> 96x96)
            tris = []
            xs, ys = [], []
            for (nname, tex_name, pal_cell, pos, nrm, uvs, idx) in part_nodes:
                t_arr = np.asarray(tex_map["palette" if pal_cell is not None else tex_name], dtype=np.float32)
                cpos = [cam_pt(p) for p in pos]
                for p in cpos:
                    xs.append(p[0])
                    ys.append(p[1])
                for k in range(0, len(idx), 3):
                    i0, i1, i2 = idx[k], idx[k + 1], idx[k + 2]
                    v0, v1, v2 = cpos[i0], cpos[i1], cpos[i2]
                    nx, ny, nz = nrm[i0]
                    ndotl = max(0.0, nx * light_dir[0] + ny * light_dir[1] + nz * light_dir[2])
                    shade = 0.50 + 0.56 * ndotl
                    # Slight depth bias for detail sub-nodes so overlays never z-fight with base boxes
                    bias = 0.004 * nname.count(".")
                    tris.append((v0, v1, v2, uvs[i0], uvs[i1], uvs[i2], t_arr, shade, bias))

            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            cx_m = 0.5 * (xmin + xmax)
            cy_m = 0.5 * (ymin + ymax)
            span = max(xmax - xmin, ymax - ymin, 0.25)

            S = 192
            scale = (S * 0.78) / span
            zbuf = np.full((S, S), -1e9, dtype=np.float32)
            cbuf = np.zeros((S, S, 4), dtype=np.uint8)

            for (v0, v1, v2, uv0, uv1, uv2, t_arr, shade, bias) in tris:
                x0 = S * 0.5 + (v0[0] - cx_m) * scale
                y0 = S * 0.5 - (v0[1] - cy_m) * scale
                x1 = S * 0.5 + (v1[0] - cx_m) * scale
                y1 = S * 0.5 - (v1[1] - cy_m) * scale
                x2 = S * 0.5 + (v2[0] - cx_m) * scale
                y2 = S * 0.5 - (v2[1] - cy_m) * scale

                ix0 = max(0, int(math.floor(min(x0, x1, x2))))
                ix1 = min(S - 1, int(math.ceil(max(x0, x1, x2))))
                iy0 = max(0, int(math.floor(min(y0, y1, y2))))
                iy1 = min(S - 1, int(math.ceil(max(y0, y1, y2))))
                if ix0 > ix1 or iy0 > iy1:
                    continue

                denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
                if abs(denom) < 1e-6:
                    continue

                py, px = np.mgrid[iy0:iy1 + 1, ix0:ix1 + 1]
                px = px.astype(np.float32) + 0.5
                py = py.astype(np.float32) + 0.5
                w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denom
                w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denom
                w2 = 1.0 - w0 - w1

                mask = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
                if not np.any(mask):
                    continue

                z = w0 * v0[2] + w1 * v1[2] + w2 * v2[2] + bias
                zslice = zbuf[iy0:iy1 + 1, ix0:ix1 + 1]
                vis = mask & (z > zslice)
                if not np.any(vis):
                    continue

                zslice[vis] = z[vis]
                u = w0[vis] * uv0[0] + w1[vis] * uv1[0] + w2[vis] * uv2[0]
                v = w0[vis] * uv0[1] + w1[vis] * uv1[1] + w2[vis] * uv2[1]
                th, tw = t_arr.shape[:2]
                tx = (np.floor((u % 1.0) * tw).astype(np.int32)) % tw
                ty = (np.floor((v % 1.0) * th).astype(np.int32)) % th
                rgb = np.clip(t_arr[ty, tx] * shade, 0, 255).astype(np.uint8)

                cslice = cbuf[iy0:iy1 + 1, ix0:ix1 + 1]
                cslice[vis, :3] = rgb
                cslice[vis, 3] = 255

            out_im = Image.fromarray(cbuf, "RGBA").resize((96, 96), Image.LANCZOS)
            icon_path = os.path.join(TEX_ITEM, f"uniform_{s}_{slot}.png")
            out_im.save(icon_path)


# ---------------------------------------------------------------------------
# 6. Item models, crafting recipes, and localization (en_us.json & ru_ru.json)
# ---------------------------------------------------------------------------
def write_models_recipes_lang():
    os.makedirs(MOD_ITEM, exist_ok=True)
    os.makedirs(RECIPES, exist_ok=True)

    recipe_Specs = {
        "rkka_rifleman": ("minecraft:green_wool", "minecraft:iron_ingot"),     # SN-42 steel breastplate!
        "rkka_officer":  ("minecraft:green_wool", "minecraft:gold_nugget"),
        "rkka_winter":   ("minecraft:brown_wool", "minecraft:white_wool"),     # Vatnik + fur
        "wehr_soldat":   ("minecraft:cyan_wool",  "minecraft:iron_nugget"),
        "wehr_offizier": ("minecraft:cyan_wool",  "minecraft:quartz"),
        "wehr_panzer":   ("minecraft:black_wool", "minecraft:pink_dye"),       # Panzerwaffe Rosa piping
    }
    patterns = {
        "head":  ["WWW", "WCI"],
        "chest": ["W W", "WCW", "WWW"],
        "legs":  ["WWW", "WCW", "W W"],
        "feet":  ["W W", "WCI"],
    }

    for s in WW2_SETS:
        wool, ins = recipe_Specs[s]
        for slot in ("head", "chest", "legs", "feet"):
            item_id = f"uniform_{s}_{slot}"
            with open(os.path.join(MOD_ITEM, item_id + ".json"), "w") as f:
                json.dump({
                    "parent": "minecraft:item/generated",
                    "textures": {"layer0": f"aiarsenal:item/{item_id}"},
                }, f, indent=2)
                f.write("\n")

            pat = patterns[slot]
            key = {"W": {"item": wool}, "C": {"item": "minecraft:leather"}}
            if "I" in "".join(pat):
                key["I"] = {"item": ins}
            with open(os.path.join(RECIPES, item_id + ".json"), "w") as f:
                json.dump({
                    "type": "minecraft:crafting_shaped",
                    "category": "equipment",
                    "pattern": pat,
                    "key": key,
                    "result": {"item": f"aiarsenal:{item_id}"},
                }, f, indent=2)
                f.write("\n")

    en_entries = {
        "item.aiarsenal.uniform.rkka_rifleman.desc": "RKKA · WWII M1943 Rifleman (SN-42 Steel Armor)",
        "item.aiarsenal.uniform_rkka_rifleman_head": "SSh-40 Steel Helmet (RKKA)",
        "item.aiarsenal.uniform_rkka_rifleman_chest": "M1943 Gymnastyorka with SN-42 Steel Breastplate",
        "item.aiarsenal.uniform_rkka_rifleman_legs": "M1943 Red Army Breeches (Galife)",
        "item.aiarsenal.uniform_rkka_rifleman_feet": "Red Army Kirza Jackboots",

        "item.aiarsenal.uniform.rkka_officer.desc": "RKKA · WWII M1943 Officer",
        "item.aiarsenal.uniform_rkka_officer_head": "RKKA Officer Visor Cap (M1943)",
        "item.aiarsenal.uniform_rkka_officer_chest": "RKKA Officer Tunic (M1943, Order of the Red Star)",
        "item.aiarsenal.uniform_rkka_officer_legs": "RKKA Officer Blue Breeches with Crimson Piping",
        "item.aiarsenal.uniform_rkka_officer_feet": "RKKA Officer Chrome Leather Boots",

        "item.aiarsenal.uniform.rkka_winter.desc": "RKKA · WWII Winter Uniform (1941–1945)",
        "item.aiarsenal.uniform_rkka_winter_head": "RKKA Winter Fur Ushanka",
        "item.aiarsenal.uniform_rkka_winter_chest": "RKKA Quilted Telogreika (Vatnik)",
        "item.aiarsenal.uniform_rkka_winter_legs": "RKKA Quilted Winter Trousers",
        "item.aiarsenal.uniform_rkka_winter_feet": "Winter Felt Valenki Boots",

        "item.aiarsenal.uniform.wehr_soldat.desc": "Wehrmacht · WWII Infantryman (M40 Feldgrau)",
        "item.aiarsenal.uniform_wehr_soldat_head": "Stahlhelm M40 (Wehrmacht)",
        "item.aiarsenal.uniform_wehr_soldat_chest": "Feldbluse M40 Tunic with Webbing (Feldgrau)",
        "item.aiarsenal.uniform_wehr_soldat_legs": "Feldhose M40 Trousers (Feldgrau)",
        "item.aiarsenal.uniform_wehr_soldat_feet": "Marschstiefel Jackboots (Wehrmacht)",

        "item.aiarsenal.uniform.wehr_offizier.desc": "Wehrmacht · WWII Officer (Offiziersfeldbluse)",
        "item.aiarsenal.uniform_wehr_offizier_head": "Wehrmacht Officer Schirmmütze Visor Cap",
        "item.aiarsenal.uniform_wehr_offizier_chest": "Wehrmacht Officer Tunic (Iron Cross 1st Class)",
        "item.aiarsenal.uniform_wehr_offizier_legs": "Wehrmacht Officer Riding Breeches",
        "item.aiarsenal.uniform_wehr_offizier_feet": "Wehrmacht Officer Riding Boots",

        "item.aiarsenal.uniform.wehr_panzer.desc": "Wehrmacht · WWII Panzerwaffe Tank Crew",
        "item.aiarsenal.uniform_wehr_panzer_head": "Panzerwaffe Field Cap with Radio Headset",
        "item.aiarsenal.uniform_wehr_panzer_chest": "Panzerjacke Wrap Tunic (Panzerwaffe)",
        "item.aiarsenal.uniform_wehr_panzer_legs": "Panzerhose Trousers (Panzerwaffe)",
        "item.aiarsenal.uniform_wehr_panzer_feet": "Panzerwaffe Laced Tank Boots",
    }

    ru_entries = {
        "item.aiarsenal.uniform.rkka_rifleman.desc": "РККА · Стрелок-штурмовик ВОВ (обр. 1943 г., панцирь СН-42)",
        "item.aiarsenal.uniform_rkka_rifleman_head": "Стальной шлем СШ-40 (РККА)",
        "item.aiarsenal.uniform_rkka_rifleman_chest": "Гимнастёрка обр. 1943 г. со стальным нагрудником СН-42",
        "item.aiarsenal.uniform_rkka_rifleman_legs": "Шаровары-галифе обр. 1943 г. (РККА)",
        "item.aiarsenal.uniform_rkka_rifleman_feet": "Кирзовые сапоги (РККА)",

        "item.aiarsenal.uniform.rkka_officer.desc": "РККА · Офицер ВОВ (обр. 1943 г.)",
        "item.aiarsenal.uniform_rkka_officer_head": "Офицерская фуражка РККА (обр. 1943 г.)",
        "item.aiarsenal.uniform_rkka_officer_chest": "Офицерский китель РККА с портупеей и орденом Красной Звезды",
        "item.aiarsenal.uniform_rkka_officer_legs": "Офицерские синие галифе с малиновым кантом (РККА)",
        "item.aiarsenal.uniform_rkka_officer_feet": "Офицерские хромовые сапоги (РККА)",

        "item.aiarsenal.uniform.rkka_winter.desc": "РККА · Зимняя форма ВОВ (1941–1945 гг.)",
        "item.aiarsenal.uniform_rkka_winter_head": "Шапка-ушанка обр. 1940 г. (РККА)",
        "item.aiarsenal.uniform_rkka_winter_chest": "Стёганая ватная телогрейка (ватник РККА)",
        "item.aiarsenal.uniform_rkka_winter_legs": "Ватные стёганые шаровары (РККА)",
        "item.aiarsenal.uniform_rkka_winter_feet": "Валенки с галошами (РККА)",

        "item.aiarsenal.uniform.wehr_soldat.desc": "Вермахт · Пехотинец ВМВ (Feldbluse M40)",
        "item.aiarsenal.uniform_wehr_soldat_head": "Стальной шлем Stahlhelm M40 (Вермахт)",
        "item.aiarsenal.uniform_wehr_soldat_chest": "Полевой китель Feldbluse M40 с разгрузкой (Фельдграу)",
        "item.aiarsenal.uniform_wehr_soldat_legs": "Полевые брюки Feldhose M40 (Фельдграу)",
        "item.aiarsenal.uniform_wehr_soldat_feet": "Маршевые сапоги Marschstiefel (Вермахт)",

        "item.aiarsenal.uniform.wehr_offizier.desc": "Вермахт · Офицер ВМВ (Offiziersfeldbluse)",
        "item.aiarsenal.uniform_wehr_offizier_head": "Офицерская фуражка Schirmmütze (Вермахт)",
        "item.aiarsenal.uniform_wehr_offizier_chest": "Офицерский китель Вермахта (Железный крест I класса)",
        "item.aiarsenal.uniform_wehr_offizier_legs": "Офицерские бриджи (Вермахт)",
        "item.aiarsenal.uniform_wehr_offizier_feet": "Офицерские высокие сапоги (Вермахт)",

        "item.aiarsenal.uniform.wehr_panzer.desc": "Вермахт · Танкист Панцерваффе ВМВ",
        "item.aiarsenal.uniform_wehr_panzer_head": "Кепи танкиста Панцерваффе с танковым шлемофоном",
        "item.aiarsenal.uniform_wehr_panzer_chest": "Чёрная куртка танкиста Panzerjacke (Панцерваффе)",
        "item.aiarsenal.uniform_wehr_panzer_legs": "Чёрные танковые брюки Panzerhose (Панцерваффе)",
        "item.aiarsenal.uniform_wehr_panzer_feet": "Танковые ботинки со шнуровкой (Панцерваффе)",
    }

    for fname, entries in (("en_us.json", en_entries), ("ru_ru.json", ru_entries)):
        for s in WW2_SETS:
            entries[f"tooltip.aiarsenal.uniform.{s}"] = entries[f"item.aiarsenal.uniform.{s}.desc"]
        p = os.path.join(LANG_DIR, fname)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.update(entries)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    ww2_nodes, new_textures, pal_im = update_glb()
    render_ww2_icons(ww2_nodes, new_textures, pal_im)
    write_models_recipes_lang()
    print("WW2_UNIFORMS_COMPLETE:", len(WW2_SETS), "sets,", len(WW2_SETS) * 4, "items")
