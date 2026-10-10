#!/usr/bin/env python3
"""r28 (future weapons): procedural GLB models for the laser rifle, the plasma rifle, their energy cells and the
plasma tank. Built with trimesh (no Blender needed in the sandbox).

usage: /tmp/geo/bin/python tools/future/make_future_models.py   (needs: pip install trimesh numpy)

Conventions (the same as the existing GLB assets):
  * handheld weapons: node names '<gunId>.<part>'; barrel along +Z, muzzle at z = 0.534 m, receiver centred on
    x = 0; the empty anchor nodes arm_r / arm_l / muzzle / sight / dot / trigger / mag / flash are placed where the
    M4A1 model has them, so GunRenderer grips the weapon the same way.
  * tank: glTF metres, +Z forward, +Y up, +X vehicle left. Node contract of GunVehicle: root > hull, rw_L_i / rw_R_i
    (road wheels), rr_L_i / rr_R_i (return rollers), spk_L / spk_R, idl_L / idl_R, launcher_yaw (turret ring
    0, 1.47, 0.30) > launcher_pitch (trunnion 0, 1.86, 1.45) > barrel (recoil along -Z). Same pivots as T-90M.
"""
import math
import os

import numpy as np
import trimesh
from trimesh.transformations import translation_matrix, rotation_matrix

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mods", "aiarsenal", "src", "main",
                   "resources", "assets", "aiarsenal", "models", "glb")
OUT = os.path.normpath(OUT)

# ---------------------------------------------------------------- materials
def mat(rgb, metal=0.2, rough=0.5, emissive=None, strength=1.0):
    kw = dict(baseColorFactor=[int(c * 255) for c in rgb] + [255], metallicFactor=metal, roughnessFactor=rough)
    if emissive is not None:
        kw["emissiveFactor"] = [min(1.0, c * strength) for c in emissive]
    return trimesh.visual.material.PBRMaterial(**kw)


M = {
    "body": mat((0.10, 0.11, 0.13), 0.35, 0.45),          # matte polymer / dark alloy
    "light": mat((0.70, 0.73, 0.77), 0.55, 0.30),         # light armour / housing
    "steel": mat((0.35, 0.37, 0.40), 0.85, 0.35),
    "cyan": mat((0.05, 0.25, 0.30), 0.1, 0.2, (0.0, 1.0, 1.0), 2.0),
    "blue": mat((0.05, 0.10, 0.30), 0.1, 0.2, (0.1, 0.4, 1.0), 2.0),
    "orange": mat((0.35, 0.15, 0.05), 0.1, 0.2, (1.0, 0.45, 0.05), 2.2),
    "plasma": mat((0.40, 0.20, 0.05), 0.2, 0.2, (1.0, 0.55, 0.15), 2.5),
    "track": mat((0.08, 0.08, 0.08), 0.1, 0.9),
    "rubber": mat((0.04, 0.04, 0.04), 0.0, 0.95),
    "olive": mat((0.25, 0.30, 0.17), 0.1, 0.7),            # hull: matte olive-grey
    "hull": mat((0.30, 0.33, 0.30), 0.3, 0.55),
    "lens": mat((0.02, 0.02, 0.03), 0.3, 0.05),
}


def box(size, c, m, name=None):
    g = trimesh.creation.box(extents=size)
    g.apply_translation(c)
    g.visual.material = M[m] if isinstance(m, str) else m
    return g


def cyl(r, h, c, axis, m, sections=20):
    """cylinder of radius r, length h, centred at c, along axis 'x' | 'y' | 'z'."""
    g = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    if axis == "x":
        g.apply_transform(rotation_matrix(math.pi / 2, [0, 1, 0]))
    elif axis == "y":
        g.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    g.apply_translation(c)
    g.visual.material = M[m] if isinstance(m, str) else m
    return g


def sphere(r, c, m, scale=(1, 1, 1)):
    g = trimesh.creation.icosphere(subdivisions=2, radius=r)
    g.apply_scale(scale)
    g.apply_translation(c)
    g.visual.material = M[m] if isinstance(m, str) else m
    return g


def cone(r0, r1, z0, z1, m):
    """frustum along +Z from z0 (radius r0) to z1 (radius r1)."""
    h = z1 - z0
    g = trimesh.creation.cone(radius=r0, height=h, sections=16)
    # trimesh cone: base at z=0 radius r0, apex at z=h. Reshape to the frustum by scaling the apex ring is not
    # needed for the emitter flare (apex is a point, so use a cone with the apex at z1)
    g.apply_translation([0, 0, z0])          # trimesh cones already run along +Z (base at 0, apex at h)
    g.visual.material = M[m] if isinstance(m, str) else m
    return g


def empty(scene, node, parent, world_pos, parent_world=(0, 0, 0)):
    T = translation_matrix(list(np.array(world_pos) - np.array(parent_world)))
    scene.graph.update(frame_to=node, frame_from=parent, matrix=T)


# ---------------------------------------------------------------- handheld rifles (node prefix = GunKind id)
def rifle(gid, cell_kind):
    """Common chassis for the two energy rifles. Geometry in metres, barrel along +Z."""
    sc = trimesh.Scene()
    root, gun = gid, gid + ".gun"
    sc.graph.update(frame_to=root, frame_from="world", matrix=np.eye(4))
    sc.graph.update(frame_to=gun, frame_from=root, matrix=np.eye(4))
    parts = []

    # receiver, stock, grip, rail
    parts.append(("body", box((0.060, 0.14, 0.40), (0, -0.01, 0.00), "body")))
    parts.append(("stock", box((0.040, 0.10, 0.20), (0, -0.02, -0.30), "body")))
    parts.append(("grip", box((0.030, 0.12, 0.05), (0, -0.095, -0.03), "body")))
    parts.append(("rail", box((0.020, 0.012, 0.22), (0, 0.078, -0.06), "steel")))
    parts.append(("shroud", box((0.046, 0.042, 0.34), (0, 0.045, 0.22), "light")))
    parts.append(("barrel", cyl(0.011, 0.36, (0, -0.005, 0.30), "z", "steel")))
    for i, z in enumerate((0.20, 0.27, 0.34, 0.41)):
        parts.append(("coil%d" % i, cyl(0.017, 0.012, (0, -0.005, z), "z", "cyan" if gid == "laser" else "orange")))
    parts.append(("emitter", cyl(0.016, 0.03, (0, -0.005, 0.515), "z", "cyan" if gid == "laser" else "orange")))
    parts.append(("lens", cyl(0.012, 0.004, (0, -0.005, 0.535), "z", "lens")))
    parts.append(("trigger", box((0.008, 0.035, 0.012), (0, -0.07, 0.00), "steel")))
    if gid == "plasma":
        # plasma chamber on top of the receiver, rear: a glowing bottle
        parts.append(("chamber", sphere(0.040, (0, 0.10, -0.02), "light", scale=(1.0, 1.0, 1.9))))
        parts.append(("core", sphere(0.022, (0, 0.10, -0.02), "plasma", scale=(1.0, 1.0, 1.9))))
    # sight: a holo-window on the rail
    parts.append(("sight", box((0.030, 0.050, 0.04), (0, 0.112, -0.115), "body")))
    parts.append(("window", box((0.026, 0.002, 0.030), (0, 0.112, -0.095), "lens")))
    parts.append(("dot", sphere(0.0035, (0, 0.112, -0.115), "cyan" if gid == "laser" else "orange")))
    # magazine / energy cell under the receiver
    parts.append(("mag", box((0.024, 0.13, 0.060), (0, -0.165, 0.03), "body")))
    parts.append(("mag_glow", box((0.006, 0.10, 0.012), (0.0125, -0.165, 0.03), cell_kind)))
    # muzzle flash: a hidden emissive burst at the tip
    parts.append(("flash", cone(0.03, 0.0, 0.535, 0.62, cell_kind)))

    for name, g in parts:
        parent = gun
        if name in ("mag", "mag_glow"):
            parent = gun
        node = gid + "." + name
        sc.add_geometry(g, node_name=node, geom_name=node, parent_node_name=parent, transform=np.eye(4))

    # anchors copied from the M4A1 (world space, identity parents), used for grips, the sight and the muzzle
    empty(sc, gid + ".arm_r", gun, (0.0, -0.076, -0.037))
    empty(sc, gid + ".arm_l", gun, (0.0, 0.002, 0.24))
    empty(sc, gid + ".muzzle", gun, (0.0, -0.005, 0.534))
    empty(sc, gid + ".flash_pos", gun, (0.0, -0.005, 0.534))
    return sc


def export_rifle(gid, cell_kind, fname):
    sc = rifle(gid, cell_kind)
    sc.export(os.path.join(OUT, fname))


# ---------------------------------------------------------------- energy cells (item models)
def cell(name, body_kind, glow_kind):
    sc = trimesh.Scene()
    sc.add_geometry(box((0.030, 0.13, 0.070), (0, 0, 0), body_kind), node_name=name + ".body",
                    geom_name=name + ".body")
    sc.add_geometry(box((0.034, 0.09, 0.012), (0, 0, 0.034), glow_kind), node_name=name + ".glow",
                    geom_name=name + ".glow")
    sc.add_geometry(box((0.032, 0.012, 0.072), (0, 0.067, 0), "steel"), node_name=name + ".cap",
                    geom_name=name + ".cap")
    return sc


def plasma_cell(name):
    sc = trimesh.Scene()
    sc.add_geometry(cyl(0.030, 0.13, (0, 0, 0), "y", "light", sections=16), node_name=name + ".body",
                    geom_name=name + ".body")
    sc.add_geometry(cyl(0.024, 0.10, (0, 0, 0), "y", "plasma", sections=16), node_name=name + ".glow",
                    geom_name=name + ".glow")
    sc.add_geometry(cyl(0.012, 0.02, (0, 0.07, 0), "y", "steel", sections=12), node_name=name + ".cap",
                    geom_name=name + ".cap")
    return sc


# ---------------------------------------------------------------- plasma tank (T-90M node contract)
def tank():
    sc = trimesh.Scene()
    P = "plasma_tank"
    sc.graph.update(frame_to="root", frame_from="world", matrix=np.eye(4))
    TX, TW, RR = 1.395, 0.58, 0.375
    ZW = RR + 0.07

    # hull: the T-90M side profile (glTF y,z) extruded across the width; front is +Z
    prof = [(3.00, 0.47), (3.43, 0.86), (2.05, 1.44), (-2.15, 1.47), (-3.43, 1.40), (-3.40, 0.64), (-2.95, 0.47)]
    poly = np.array(prof)                       # (z, y) in the XY plane of the 2D polygon
    from trimesh.creation import extrude_polygon
    from shapely.geometry import Polygon
    hull = extrude_polygon(Polygon(poly), height=2.16)
    v = hull.vertices.copy()
    nv = np.stack([v[:, 2] - 1.08, v[:, 1], v[:, 0]], axis=1)    # (w, v, u) -> (x, y, z)
    hull = trimesh.Trimesh(nv, hull.faces, process=True).fix_normals()
    hull.visual.material = M["hull"]
    sc.add_geometry(hull, node_name=P + "_hull", geom_name=P + "_hull", parent_node_name="root")
    # reactive-armour / plasma-shield stripes on the glacis and the turret (cyan emitters)
    for sx in (1, -1):
        sc.add_geometry(box((0.03, 0.06, 5.8), (sx * 1.10, 1.08, 0.2), "cyan"), node_name=P + "_stripe%d" % sx,
                        geom_name=P + "_stripe%d" % sx, parent_node_name="root")
    # skirts / fenders / tracks (static)
    for sx, xw in ((1, TX), (-1, -TX)):
        sc.add_geometry(box((TW, 0.42, 7.6), (xw, 0.66, 0.0), "track"), node_name=P + "_track%d" % sx,
                        geom_name=P + "_track%d" % sx, parent_node_name="root")
        sc.add_geometry(box((0.66, 0.03, 6.6), (sx * 1.41, 1.2, 0.1), "body"), node_name=P + "_fender%d" % sx,
                        geom_name=P + "_fender%d" % sx, parent_node_name="root")

    # road wheels, return rollers, sprockets, idlers: one node per wheel (pivots are the axle centres)
    road = [2.15 - k * 0.812 for k in range(6)]
    for sx, side, xw in ((1, "L", TX), (-1, "R", -TX)):
        for k, z in enumerate(road):
            nm = "rw_%s_%d" % (side, k)
            g = cyl(RR, TW * 0.86, (0, 0, 0), "x", "rubber", sections=24)
            sc.add_geometry(g, node_name=nm, geom_name=nm, parent_node_name="root",
                            transform=translation_matrix([xw, ZW, z]))
        for k, z in enumerate((-1.25, 0.0, 1.25)):
            nm = "rr_%s_%d" % (side, k)
            g = cyl(0.11, TW * 0.7, (0, 0, 0), "x", "steel", sections=16)
            sc.add_geometry(g, node_name=nm, geom_name=nm, parent_node_name="root",
                            transform=translation_matrix([xw, 0.975, z]))
        nm = "spk_" + side
        sc.add_geometry(cyl(0.33, TW * 0.6, (0, 0, 0), "x", "steel", sections=16), node_name=nm, geom_name=nm,
                        parent_node_name="root", transform=translation_matrix([xw, 0.70, -2.86]))
        nm = "idl_" + side
        sc.add_geometry(cyl(0.30, TW * 0.6, (0, 0, 0), "x", "steel", sections=16), node_name=nm, geom_name=nm,
                        parent_node_name="root", transform=translation_matrix([xw, 0.62, 2.93]))
        # track bar
        sc.add_geometry(box((0.07, 0.10, 7.2), (xw, 0.32, 0.0), "track"), node_name=P + "_bar" + side,
                        geom_name=P + "_bar" + side, parent_node_name="root")

    # turret: launcher_yaw ring (0, 1.47, 0.30); shell and plasma emitter parts in the yaw frame
    Y = np.array([0.0, 1.47, 0.30])
    sc.graph.update(frame_to="launcher_yaw", frame_from="root", matrix=translation_matrix(Y))
    tur = sphere(1.0, (0, 0.50, -0.15), "olive", scale=(1.00, 0.36, 1.25))       # low dome, flat top
    tur.apply_translation((0, 0.0, 0.0))
    sc.add_geometry(tur, node_name="launcher_yaw_shell", geom_name="launcher_yaw_shell",
                    parent_node_name="launcher_yaw")
    sc.add_geometry(cyl(1.02, 0.10, (0, 0.13, -0.15), "y", "body", sections=36), node_name="launcher_yaw_ring",
                    geom_name="launcher_yaw_ring", parent_node_name="launcher_yaw")
    sc.add_geometry(box((1.2, 0.08, 1.3), (0.0, 0.62, -0.20), "steel"), node_name="launcher_yaw_plate",
                    geom_name="launcher_yaw_plate", parent_node_name="launcher_yaw")
    # side plasma capacitors (glow) on the turret cheeks
    for sx in (1, -1):
        sc.add_geometry(box((0.06, 0.20, 0.9), (sx * 1.05, 0.45, -0.1), "cyan"), node_name="launcher_yaw_cap%d" % sx,
                        geom_name="launcher_yaw_cap%d" % sx, parent_node_name="launcher_yaw")
    # commander cupola and sensor mast
    sc.add_geometry(cyl(0.32, 0.22, (-0.5, 0.80, 0.9), "y", "olive", sections=24), node_name="launcher_yaw_cup",
                    geom_name="launcher_yaw_cup", parent_node_name="launcher_yaw")
    sc.add_geometry(box((0.05, 0.6, 0.05), (0.7, 0.92, 0.1), "body"), node_name="launcher_yaw_mast",
                    geom_name="launcher_yaw_mast", parent_node_name="launcher_yaw")

    # launcher_pitch (trunnion at 0, 1.86, 1.45) relative to the yaw ring
    TRN = np.array([0.0, 1.86, 1.45])
    sc.graph.update(frame_to="launcher_pitch", frame_from="launcher_yaw", matrix=translation_matrix(TRN - Y))
    sc.add_geometry(box((0.55, 0.40, 0.36), (0, 0.0, 0.05), "olive"), node_name="launcher_pitch_cradle",
                    geom_name="launcher_pitch_cradle", parent_node_name="launcher_pitch")
    sc.add_geometry(cyl(0.11, 1.20, (0, 0.0, 0.0), "x", "steel", sections=20), node_name="launcher_pitch_trunnion",
                    geom_name="launcher_pitch_trunnion", parent_node_name="launcher_pitch")

    # barrel: from the breech (trunnion) to the muzzle (z = 6.20), recoils along -Z
    sc.graph.update(frame_to="barrel", frame_from="launcher_pitch", matrix=np.eye(4))
    sc.add_geometry(cyl(0.085, 4.75, (0, 0, 2.375 + 0.0), "z", "steel", sections=20), node_name="barrel_tube",
                    geom_name="barrel_tube", parent_node_name="barrel")
    sc.add_geometry(cyl(0.16, 0.10, (0, 0, 0.35), "z", "body", sections=20), node_name="barrel_sleeve",
                    geom_name="barrel_sleeve", parent_node_name="barrel")
    sc.add_geometry(cyl(0.12, 0.45, (0, 0, 4.60), "z", "cyan", sections=24), node_name="barrel_emitter",
                    geom_name="barrel_emitter", parent_node_name="barrel")
    sc.add_geometry(cyl(0.14, 0.04, (0, 0, 4.85), "z", "lens", sections=24), node_name="barrel_muzzle",
                    geom_name="barrel_muzzle", parent_node_name="barrel")
    for i, z in enumerate((1.2, 2.0, 2.8, 3.6)):
        sc.add_geometry(cyl(0.105, 0.10, (0, 0, z), "z", "cyan", sections=20), node_name="barrel_coil%d" % i,
                        geom_name="barrel_coil%d" % i, parent_node_name="barrel")
    sc.add_geometry(sphere(0.24, (0, 0, -0.6), "plasma", scale=(1, 1, 1.0)), node_name="barrel_breech",
                    geom_name="barrel_breech", parent_node_name="barrel")
    return sc


def main():
    os.makedirs(OUT, exist_ok=True)
    export_rifle("laser", "cyan", "laser.glb")
    export_rifle("plasma", "orange", "plasma.glb")
    cell_s = cell("mag_laser", "body", "cyan")
    cell_s.export(os.path.join(OUT, "mag_laser.glb"))
    plasma_cell("mag_plasma").export(os.path.join(OUT, "mag_plasma.glb"))
    tank().export(os.path.join(OUT, "plasma_tank.glb"))
    print("written to", OUT)


if __name__ == "__main__":
    main()
