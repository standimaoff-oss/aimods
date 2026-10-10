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
    """r29 'Vikhr': futuristic tank after the reference render - armoured skirts with ribs, yellow glowing track
    shoes, blue lamps and mesh grille, an eight-tube launcher on the turret, yellow underglow and cable looms.
    Node contract unchanged (root > hull, rw_/rr_/spk_/idl_, launcher_yaw > launcher_pitch > barrel)."""
    sc = trimesh.Scene()
    P = "plasma_tank"
    sc.graph.update(frame_to="root", frame_from="world", matrix=np.eye(4))
    TX, TW, RR = 1.395, 0.58, 0.375
    ZW = RR + 0.07
    W = mat((0.66, 0.68, 0.66), 0.5, 0.32)                   # pale grey armour
    D = mat((0.12, 0.13, 0.14), 0.5, 0.45)                   # dark rubber/alloy
    Y = mat((1.0, 0.82, 0.10), 0.1, 0.25, (1.0, 0.80, 0.10), 2.6)   # yellow glow
    B = mat((0.20, 0.45, 1.0), 0.1, 0.2, (0.20, 0.55, 1.0), 2.2)    # blue lamps
    GR = mat((0.22, 0.25, 0.28), 0.8, 0.4)                   # grille / steel

    # hull: T-90M side profile extruded across the width (front = +Z)
    prof = [(3.00, 0.55), (3.43, 0.95), (2.05, 1.40), (-2.15, 1.42), (-3.43, 1.30), (-3.40, 0.70), (-2.95, 0.50)]
    from trimesh.creation import extrude_polygon
    from shapely.geometry import Polygon
    hull = extrude_polygon(Polygon(np.array(prof)), height=2.00)
    v = hull.vertices.copy()
    nv = np.stack([v[:, 2] - 1.00, v[:, 1], v[:, 0]], axis=1)
    hull = trimesh.Trimesh(nv, hull.faces, process=True).fix_normals()
    hull.visual.material = W
    sc.add_geometry(hull, node_name=P + "_hull", geom_name=P + "_hull", parent_node_name="root")

    # side armour skirts: ribbed plates covering the tracks, with a yellow shoe at the bottom front/rear corners
    for sx in (1, -1):
        sc.add_geometry(box((0.10, 0.62, 6.6), (sx * 1.46, 0.66, 0.0), D), node_name="%s_skirt%d" % (P, sx),
                        geom_name="%s_skirt%d" % (P, sx), parent_node_name="root")
        for k in range(12):
            z = 2.9 - k * 0.53
            sc.add_geometry(box((0.12, 0.50, 0.30), (sx * 1.52, 0.70, z), W),
                            node_name="%s_rib%d_%d" % (P, sx, k), geom_name="%s_rib%d_%d" % (P, sx, k),
                            parent_node_name="root")
            sc.add_geometry(sphere(0.03, (sx * 1.58, 0.92, z), D), node_name="%s_rivet%d_%d" % (P, sx, k),
                            geom_name="%s_rivet%d_%d" % (P, sx, k), parent_node_name="root")
        for z in (-2.85, 2.85):
            sc.add_geometry(box((0.42, 0.14, 0.95), (sx * 1.30, 0.13, z), Y),
                            node_name="%s_shoe%d_%d" % (P, sx, int(z > 0)), geom_name="%s_shoe%d_%d" % (P, sx, int(z > 0)),
                            parent_node_name="root")
        # blue headlamp and grille block on the front plate
        sc.add_geometry(box((0.42, 0.10, 0.06), (sx * 0.85, 1.10, 3.30), B), node_name="%s_lamp%d" % (P, sx),
                        geom_name="%s_lamp%d" % (P, sx), parent_node_name="root")
        sc.add_geometry(box((0.42, 0.10, 0.05), (sx * 0.85, 0.78, 3.31), GR), node_name="%s_mesh%d" % (P, sx),
                        geom_name="%s_mesh%d" % (P, sx), parent_node_name="root")
    # rear engine block with yellow exhaust grille and two side pods (photo: rear wings)
    sc.add_geometry(box((2.60, 0.60, 0.40), (0.0, 1.30, -3.40), D), node_name=P + "_engrear",
                    geom_name=P + "_engrear", parent_node_name="root")
    sc.add_geometry(box((2.0, 0.34, 0.06), (0.0, 1.42, -3.62), Y), node_name=P + "_exhaust",
                    geom_name=P + "_exhaust", parent_node_name="root")
    # yellow underglow under the belly (the photo's floating glow)
    sc.add_geometry(box((2.6, 0.02, 5.4), (0.0, 0.05, 0.0), Y), node_name=P + "_underglow",
                    geom_name=P + "_underglow", parent_node_name="root")
    # cable looms along the hull
    for sx in (1, -1):
        sc.add_geometry(cyl(0.03, 4.8, (sx * 1.05, 1.44, 0.0), "z", D, sections=8), node_name="%s_loom%d" % (P, sx),
                        geom_name="%s_loom%d" % (P, sx), parent_node_name="root")

    # track assemblies and wheels (same node names and pivots as T-90M)
    for sx, side, xw in ((1, "L", TX), (-1, "R", -TX)):
        sc.add_geometry(box((TW, 0.42, 7.6), (xw, 0.66, 0.0), D), node_name=P + "_track%d" % sx,
                        geom_name=P + "_track%d" % sx, parent_node_name="root")
    road = [2.15 - k * 0.812 for k in range(6)]
    for sx, side, xw in ((1, "L", TX), (-1, "R", -TX)):
        for k, z in enumerate(road):
            nm = "rw_%s_%d" % (side, k)
            sc.add_geometry(cyl(RR, TW * 0.86, (0, 0, 0), "x", D, sections=24), node_name=nm, geom_name=nm,
                            parent_node_name="root", transform=translation_matrix([xw, ZW, z]))
        for k, z in enumerate((-1.25, 0.0, 1.25)):
            nm = "rr_%s_%d" % (side, k)
            sc.add_geometry(cyl(0.11, TW * 0.7, (0, 0, 0), "x", GR, sections=16), node_name=nm, geom_name=nm,
                            parent_node_name="root", transform=translation_matrix([xw, 0.975, z]))
        nm = "spk_" + side
        sc.add_geometry(cyl(0.33, TW * 0.6, (0, 0, 0), "x", GR, sections=16), node_name=nm, geom_name=nm,
                        parent_node_name="root", transform=translation_matrix([xw, 0.70, -2.86]))
        nm = "idl_" + side
        sc.add_geometry(cyl(0.30, TW * 0.6, (0, 0, 0), "x", GR, sections=16), node_name=nm, geom_name=nm,
                        parent_node_name="root", transform=translation_matrix([xw, 0.62, 2.93]))

    # turret ring (launcher_yaw pivot 0, 1.47, 0.30)
    Yp = np.array([0.0, 1.47, 0.30])
    sc.graph.update(frame_to="launcher_yaw", frame_from="root", matrix=translation_matrix(Yp))
    sc.add_geometry(sphere(1.0, (0, 0.50, -0.15), W, scale=(1.00, 0.34, 1.22)), node_name="launcher_yaw_shell",
                    geom_name="launcher_yaw_shell", parent_node_name="launcher_yaw")
    sc.add_geometry(cyl(1.04, 0.10, (0, 0.10, -0.15), "y", D, sections=36), node_name="launcher_yaw_ring",
                    geom_name="launcher_yaw_ring", parent_node_name="launcher_yaw")
    # front wedge and angled armour plates of the turret
    sc.add_geometry(box((1.5, 0.22, 0.6), (0, 0.72, 0.85), W), node_name="launcher_yaw_wedge",
                    geom_name="launcher_yaw_wedge", parent_node_name="launcher_yaw")
    for sx in (1, -1):
        sc.add_geometry(box((0.10, 0.36, 1.2), (sx * 1.06, 0.55, -0.2), W), node_name="launcher_yaw_cheek%d" % sx,
                        geom_name="launcher_yaw_cheek%d" % sx, parent_node_name="launcher_yaw")
        sc.add_geometry(box((0.05, 0.10, 1.0), (sx * 1.12, 0.62, -0.2), Y), node_name="launcher_yaw_band%d" % sx,
                        geom_name="launcher_yaw_band%d" % sx, parent_node_name="launcher_yaw")
        sc.add_geometry(box((0.20, 0.10, 0.20), (sx * 0.55, 0.92, -0.45), B), node_name="launcher_yaw_sensor%d" % sx,
                        geom_name="launcher_yaw_sensor%d" % sx, parent_node_name="launcher_yaw")
    # commander cupola with a green screen, sensor mast with a dish, twin antennas
    sc.add_geometry(cyl(0.30, 0.22, (-0.5, 0.82, 0.9), "y", W, sections=24), node_name="launcher_yaw_cup",
                    geom_name="launcher_yaw_cup", parent_node_name="launcher_yaw")
    sc.add_geometry(box((0.22, 0.04, 0.16), (-0.5, 1.05, 1.1), mat((0.1, 0.5, 0.2), 0.1, 0.2, (0.1, 0.9, 0.3), 1.5)),
                    node_name="launcher_yaw_screen", geom_name="launcher_yaw_screen", parent_node_name="launcher_yaw")
    sc.add_geometry(cyl(0.03, 1.6, (-0.2, 1.50, -1.0), "y", D, sections=8), node_name="launcher_yaw_mast",
                    geom_name="launcher_yaw_mast", parent_node_name="launcher_yaw")
    sc.add_geometry(cyl(0.22, 0.04, (-0.2, 2.30, -1.0), "y", GR, sections=20), node_name="launcher_yaw_dish",
                    geom_name="launcher_yaw_dish", parent_node_name="launcher_yaw")
    for sx in (1, -1):
        sc.add_geometry(cyl(0.012, 1.2, (sx * 0.8, 1.65, -0.6), "y", D, sections=6), node_name="launcher_yaw_ant%d" % sx,
                        geom_name="launcher_yaw_ant%d" % sx, parent_node_name="launcher_yaw")

    # launcher_pitch: trunnion at 0, 1.86, 1.45 relative to the yaw ring
    TRN = np.array([0.0, 1.86, 1.45])
    sc.graph.update(frame_to="launcher_pitch", frame_from="launcher_yaw", matrix=translation_matrix(TRN - Yp))
    sc.add_geometry(box((0.62, 0.42, 0.40), (0, 0.0, 0.05), W), node_name="launcher_pitch_cradle",
                    geom_name="launcher_pitch_cradle", parent_node_name="launcher_pitch")
    sc.add_geometry(cyl(0.11, 1.30, (0, 0.0, 0.0), "x", GR, sections=20), node_name="launcher_pitch_trunnion",
                    geom_name="launcher_pitch_trunnion", parent_node_name="launcher_pitch")
    for sx in (1, -1):
        sc.add_geometry(box((0.10, 0.20, 0.5), (sx * 0.34, 0.06, 0.1), Y), node_name="launcher_pitch_hose%d" % sx,
                        geom_name="launcher_pitch_hose%d" % sx, parent_node_name="launcher_pitch")

    # barrel: eight-tube launcher (2 rows x 4), breech at the trunnion, recoils along -Z, muzzle at local 4.75
    sc.graph.update(frame_to="barrel", frame_from="launcher_pitch", matrix=np.eye(4))
    sc.add_geometry(box((0.62, 0.34, 3.2), (0, 0.0, 1.70), D), node_name="barrel_housing",
                    geom_name="barrel_housing", parent_node_name="barrel")
    for r, yy in enumerate((0.09, -0.09)):
        for c, xx in enumerate((-0.15, -0.05, 0.05, 0.15)):
            i = r * 4 + c
            sc.add_geometry(cyl(0.042, 4.75, (xx, yy, 2.375), "z", GR, sections=14), node_name="barrel_tube%d" % i,
                            geom_name="barrel_tube%d" % i, parent_node_name="barrel")
            sc.add_geometry(cyl(0.048, 0.10, (xx, yy, 4.70), "z", Y, sections=14), node_name="barrel_cap%d" % i,
                            geom_name="barrel_cap%d" % i, parent_node_name="barrel")
            sc.add_geometry(cyl(0.030, 0.04, (xx, yy, 0.70), "z", Y, sections=10), node_name="barrel_ring%d" % i,
                            geom_name="barrel_ring%d" % i, parent_node_name="barrel")
    sc.add_geometry(sphere(0.24, (0, 0, -0.6), Y, scale=(1, 1, 1.0)), node_name="barrel_breech",
                    geom_name="barrel_breech", parent_node_name="barrel")
    return sc


def _extrude_yz(pts, width, x0):
    """Side profile (z, y) extruded across x in [x0, x0 + width]."""
    from trimesh.creation import extrude_polygon
    from shapely.geometry import Polygon
    m = extrude_polygon(Polygon(np.array(pts)), height=width)
    v = m.vertices.copy()
    nv = np.stack([v[:, 2] + x0, v[:, 1], v[:, 0]], axis=1)
    return trimesh.Trimesh(nv, m.faces, process=True).fix_normals()


def _extrude_xz(pts, thick, y0):
    """Plan outline (x, z) extruded upward from y0 by thickness."""
    from trimesh.creation import extrude_polygon
    from shapely.geometry import Polygon
    m = extrude_polygon(Polygon(np.array(pts)), height=thick)
    v = m.vertices.copy()
    nv = np.stack([v[:, 0], v[:, 2] + y0, v[:, 1]], axis=1)
    return trimesh.Trimesh(nv, m.faces, process=True).fix_normals()


def plasma_heli():
    """r30 'Plazmolet': plasma-lift helicopter, no propellers. Ducts with glowing plasma rings replace rotors;
    the coaxial model in HeliEntity keeps the torque balance. Photo style: pale armour, yellow glow, blue lamps."""
    sc = trimesh.Scene()
    P = "plasma_heli"
    sc.graph.update(frame_to="root", frame_from="world", matrix=np.eye(4))
    W = mat((0.66, 0.68, 0.66), 0.5, 0.32)
    D = mat((0.12, 0.13, 0.14), 0.5, 0.45)
    Y = mat((1.0, 0.82, 0.10), 0.1, 0.25, (1.0, 0.80, 0.10), 2.6)
    B = mat((0.20, 0.45, 1.0), 0.1, 0.2, (0.20, 0.55, 1.0), 2.2)
    G = mat((0.10, 0.22, 0.30), 0.2, 0.05, (0.2, 0.7, 1.0), 0.6)
    # fuselage: side profile (z, y) extruded across the width (+-1.05)
    body = _extrude_yz([(4.6, 1.2), (4.1, 1.9), (2.4, 2.4), (-2.3, 2.5), (-4.3, 2.0), (-4.6, 1.5), (-2.2, 0.9),
                        (2.0, 0.8), (3.6, 0.8)], 2.1, -1.05)
    body.visual.material = W
    sc.add_geometry(body, node_name=P + "_body", geom_name=P + "_body", parent_node_name="root")
    # glass canopy and blue lamps
    sc.add_geometry(sphere(1.0, (0.0, 1.75, 3.1), B, scale=(0.95, 0.62, 1.3)), node_name=P + "_canopy",
                    geom_name=P + "_canopy", parent_node_name="root")
    for sx in (1, -1):
        sc.add_geometry(box((0.35, 0.12, 0.06), (sx * 0.7, 1.12, 4.55), B), node_name="%s_lamp%d" % (P, sx),
                        geom_name="%s_lamp%d" % (P, sx), parent_node_name="root")
    # plasma-lift ducts: two side pods, each ring glowing cyan (replaces the rotor discs)
    for sx in (1, -1):
        sc.add_geometry(cyl(0.95, 3.2, (sx * 2.2, 1.9, 0.2), "z", D, sections=28), node_name="%s_duct%d" % (P, sx),
                        geom_name="%s_duct%d" % (P, sx), parent_node_name="root")
        sc.add_geometry(cyl(0.80, 0.08, (sx * 2.2, 1.9, 1.80), "z", G, sections=28), node_name="%s_ring%d_f" % (P, sx),
                        geom_name="%s_ring%d_f" % (P, sx), parent_node_name="root")
        sc.add_geometry(cyl(0.80, 0.08, (sx * 2.2, 1.9, -1.40), "z", G, sections=28), node_name="%s_ring%d_r" % (P, sx),
                        geom_name="%s_ring%d_r" % (P, sx), parent_node_name="root")
        sc.add_geometry(box((0.6, 0.12, 2.6), (sx * 1.25, 1.55, 0.2), W), node_name="%s_pylon%d" % (P, sx),
                        geom_name="%s_pylon%d" % (P, sx), parent_node_name="root")
    # yellow underglow and cable looms
    sc.add_geometry(box((1.8, 0.02, 4.2), (0.0, 0.05, 0.3), Y), node_name=P + "_underglow",
                    geom_name=P + "_underglow", parent_node_name="root")
    # tail boom with a vertical plasma fin
    sc.add_geometry(cyl(0.45, 2.8, (0.0, 1.9, -6.4), "z", W, sections=20), node_name=P + "_boom",
                    geom_name=P + "_boom", parent_node_name="root")
    sc.add_geometry(box((0.10, 1.45, 1.0), (0.0, 2.9, -7.5), W), node_name=P + "_fin",
                    geom_name=P + "_fin", parent_node_name="root")
    sc.add_geometry(box((0.12, 0.45, 0.6), (0.0, 3.1, -7.9), Y), node_name=P + "_fin_glow",
                    geom_name=P + "_fin_glow", parent_node_name="root")
    # gun turret: pivots gun_yaw / gun_pitch (renderer rotates them), barrel forward along +Z
    sc.graph.update(frame_to="gun_yaw", frame_from="root", matrix=translation_matrix([0.0, 0.8, 2.3]))
    sc.add_geometry(sphere(0.45, (0, 0, 0), D, scale=(1.0, 0.7, 1.0)), node_name="gun_yaw_ball",
                    geom_name="gun_yaw_ball", parent_node_name="gun_yaw")
    sc.graph.update(frame_to="gun_pitch", frame_from="gun_yaw", matrix=np.eye(4))
    sc.add_geometry(box((0.36, 0.30, 0.8), (0, 0, 0.2), D), node_name="gun_pitch_body",
                    geom_name="gun_pitch_body", parent_node_name="gun_pitch")
    for i, (xx, yy) in enumerate(((-0.08, 0.06), (0.08, 0.06), (-0.08, -0.06), (0.08, -0.06))):
        sc.add_geometry(cyl(0.03, 1.6, (xx, yy, 1.2), "z", GR_STEEL(), sections=10), node_name="gun_barrel%d" % i,
                        geom_name="gun_barrel%d" % i, parent_node_name="gun_pitch")
        sc.add_geometry(cyl(0.04, 0.08, (xx, yy, 2.0), "z", Y, sections=10), node_name="gun_cap%d" % i,
                        geom_name="gun_cap%d" % i, parent_node_name="gun_pitch")
    return sc


def GR_STEEL():
    return mat((0.22, 0.25, 0.28), 0.8, 0.4)


def starship():
    """r30 'Zvezdolet': plasma-jet delta starship, 18 m span, 22 m long, two aft plasma nozzles, no propellers.
    Origin at the ground under the centre of mass; the flat belly sits 0.6 m up on the skids."""
    sc = trimesh.Scene()
    P = "starship"
    sc.graph.update(frame_to="root", frame_from="world", matrix=np.eye(4))
    W = mat((0.66, 0.68, 0.66), 0.5, 0.32)
    D = mat((0.12, 0.13, 0.14), 0.5, 0.45)
    Y = mat((1.0, 0.82, 0.10), 0.1, 0.25, (1.0, 0.80, 0.10), 2.6)
    B = mat((0.20, 0.45, 1.0), 0.1, 0.2, (0.20, 0.55, 1.0), 2.2)
    # delta wing (plan outline x, z) and a lenticular body on top of it
    wing = _extrude_xz([(0, 11.0), (9.0, -7.0), (4.2, -9.4), (0, -7.6), (-4.2, -9.4), (-9.0, -7.0)], 0.7, 0.6)
    wing.visual.material = W
    sc.add_geometry(wing, node_name=P + "_wing", geom_name=P + "_wing", parent_node_name="root")
    body = _extrude_yz([(10.8, 1.25), (8.0, 1.85), (2.0, 2.25), (-6.0, 2.30), (-9.4, 2.0), (-10.8, 1.25),
                        (-9.4, 0.95), (2.0, 0.95), (8.0, 0.95)], 2.4, -1.2)
    body.visual.material = W
    sc.add_geometry(body, node_name=P + "_body", geom_name=P + "_body", parent_node_name="root")
    # canopy, plasma edge lights on the wing tips and along the leading edges
    sc.add_geometry(sphere(1.0, (0.0, 2.25, 5.0), B, scale=(0.9, 0.55, 2.0)), node_name=P + "_canopy",
                    geom_name=P + "_canopy", parent_node_name="root")
    for sx in (1, -1):
        sc.add_geometry(box((0.5, 0.18, 1.6), (sx * 8.6, 1.00, -7.0), B), node_name="%s_tip%d" % (P, sx),
                        geom_name="%s_tip%d" % (P, sx), parent_node_name="root")
    # two aft plasma nozzles: dark housings with yellow cores
    for sx in (1, -1):
        sc.add_geometry(cyl(1.05, 2.0, (sx * 2.8, 1.25, -9.6), "z", D, sections=24), node_name="%s_nozzle%d" % (P, sx),
                        geom_name="%s_nozzle%d" % (P, sx), parent_node_name="root")
        sc.add_geometry(cyl(0.80, 0.12, (sx * 2.8, 1.25, -10.7), "z", Y, sections=24), node_name="%s_core%d" % (P, sx),
                        geom_name="%s_core%d" % (P, sx), parent_node_name="root")
    # belly glow and three skids (origin on the ground)
    sc.add_geometry(box((9.0, 0.05, 6.0), (0.0, 0.62, -1.5), Y), node_name=P + "_underglow",
                    geom_name=P + "_underglow", parent_node_name="root")
    for k, (xx, zz) in enumerate(((0.0, 6.5), (-2.8, -6.0), (2.8, -6.0))):
        sc.add_geometry(box((0.22, 0.62, 0.22), (xx, 0.31, zz), D), node_name="%s_skid%d" % (P, k),
                        geom_name="%s_skid%d" % (P, k), parent_node_name="root")
    return sc


def main():
    os.makedirs(OUT, exist_ok=True)
    export_rifle("laser", "cyan", "laser.glb")
    export_rifle("plasma", "orange", "plasma.glb")
    cell_s = cell("mag_laser", "body", "cyan")
    cell_s.export(os.path.join(OUT, "mag_laser.glb"))
    plasma_cell("mag_plasma").export(os.path.join(OUT, "mag_plasma.glb"))
    tank().export(os.path.join(OUT, "plasma_tank.glb"))
    plasma_heli().export(os.path.join(OUT, "plasma_heli.glb"))
    starship().export(os.path.join(OUT, "starship.glb"))
    print("written to", OUT)


if __name__ == "__main__":
    main()
