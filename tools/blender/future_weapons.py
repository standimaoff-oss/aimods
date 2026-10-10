"""
Футуристическое стрелковое оружие: пистолет и две винтовки (лазер / плазма).

Запуск (Blender 4.2+/5.x, модуль bpy или бинарник blender):
    python future_weapons.py            # построить три .blend в models/future_weapons/
    python future_weapons.py --check    # проверка файлов (открытие без аддонов, ORPHANS, пустые меши)
    python future_weapons.py --qa DIR   # QA-рендер ракурсов (не входит в поставку)

Соглашения (ТЗ MODEL-VIEW PRO v2.0):
  * Метры, scale = 1, трансформы применены, ствол вдоль +Y, вверх +Z.
  * Начало координат — точка хвата (рукоять) / центр рукояти.
  * Геометрия — примитивы + фаски (bevel) + сглаживание по углу 35°.
  * Материалы процедурные (фототекстуры недоступны: сеть разрешает только github/pypi/npm).
    Шероховатость и бамп варьируются шумом по объекту, эмиссия — только на светящихся элементах.
  * Якоря выстрела (ANCHOR_*) — пустышки с пользовательскими свойствами для системы стрельбы.
  * Камера и HDRI в поставку не входят; для просмотра есть ключевой свет и нейтральный мир.
"""

import math
import os
import sys

import bpy  # noqa: E402  (должен идти первым: без него bmesh/mathutils недоступны)
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models", "future_weapons")
OUT_DIR = os.path.normpath(OUT_DIR)

BEVEL_DEFAULT = 0.0015  # 1.5 мм фаска на твёрдых рёбрах
SHARP_ANGLE = math.radians(35)


# ----------------------------------------------------------------- сцена

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.context.preferences.filepaths.save_version = 0
    except Exception:
        pass


def get_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


# ----------------------------------------------------------------- материалы

def make_material(name, color, metallic=0.0, roughness=0.4, emit=None, emit_strength=0.0,
                  rough_var=0.18, bump=0.02, noise_scale=18.0):
    """PBR-материал: шероховатость меняется шумом (потёртости читаются блеском), лёгкий бамп."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    coord = nodes.new("ShaderNodeTexCoord")
    coord.location = (-1000, 0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-700, 0)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.55
    links.new(coord.outputs["Object"], noise.inputs["Vector"])

    rmap = nodes.new("ShaderNodeMapRange")
    rmap.location = (-400, 200)
    rmap.inputs["From Min"].default_value = 0.0
    rmap.inputs["From Max"].default_value = 1.0
    rmap.inputs["To Min"].default_value = max(0.02, roughness * (1.0 - rough_var))
    rmap.inputs["To Max"].default_value = min(1.0, roughness * (1.0 + rough_var))
    links.new(noise.outputs["Fac"], rmap.inputs["Value"])
    links.new(rmap.outputs["Result"], bsdf.inputs["Roughness"])

    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic

    if bump > 0:
        bmp = nodes.new("ShaderNodeBump")
        bmp.location = (-200, -200)
        bmp.inputs["Strength"].default_value = bump
        bmp.inputs["Distance"].default_value = 0.01
        links.new(noise.outputs["Fac"], bmp.inputs["Height"])
        links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])

    if emit is not None:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


# ----------------------------------------------------------------- геометрия (bmesh)

def _box(bm, size):
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal(Vector(size)).to_4x4(), verts=bm.verts)


def _cyl(bm, radius, length, segments=20):
    # вдоль Z, центр в начале координат
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=length)


def _torus(bm, big_r, small_r, nu=28, nv=8):
    verts = []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        for j in range(nv):
            v = 2 * math.pi * j / nv
            d = big_r + small_r * math.cos(v)
            verts.append(bm.verts.new((d * math.cos(u), d * math.sin(u), small_r * math.sin(v))))
    bm.verts.ensure_lookup_table()
    for i in range(nu):
        for j in range(nv):
            a = verts[i * nv + j]
            b = verts[((i + 1) % nu) * nv + j]
            c = verts[((i + 1) % nu) * nv + (j + 1) % nv]
            d = verts[i * nv + (j + 1) % nv]
            bm.faces.new((a, b, c, d))


def _sphere(bm, radius, seg=24, rings=12):
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=radius)


def _bevel(bm, width):
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(20)]
    if edges and width > 0:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=2, profile=0.5,
                        affect="EDGES", clamp_overlap=True)


def _smooth_by_angle(bm):
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) <= SHARP_ANGLE
    for f in bm.faces:
        f.smooth = True
    bm.normal_update()


def _matrix(loc, rot_deg):
    rx, ry, rz = (math.radians(a) for a in rot_deg)
    return Matrix.Translation(Vector(loc)) @ Euler((rx, ry, rz)).to_matrix().to_4x4()


def add_part(col, name, kind, mat, loc=(0, 0, 0), rot=(0, 0, 0), bevel=None, **dims):
    """Строит один меш, применяет трансформ, фаски и сглаживание, кладёт в коллекцию."""
    bm = bmesh.new()
    if kind == "box":
        size = dims["size"]
        _box(bm, size)
        width = BEVEL_DEFAULT if bevel is None else bevel
        width = min(width, 0.3 * min(size))
    elif kind == "cyl":
        _cyl(bm, dims["r"], dims["L"], dims.get("seg", 20))
        width = 0.0006 if bevel is None else bevel
        width = min(width, 0.3 * dims["r"])
    elif kind == "torus":
        _torus(bm, dims["R"], dims["r"])
        width = 0.0 if bevel is None else bevel
    elif kind == "sphere":
        _sphere(bm, dims["r"])
        width = 0.0 if bevel is None else bevel
    else:
        raise ValueError(kind)

    if width > 0:
        _bevel(bm, width)
    bmesh.ops.transform(bm, matrix=_matrix(loc, rot), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _smooth_by_angle(bm)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    col.objects.link(obj)
    return obj


def add_anchor(col, name, loc, props):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.03
    obj.location = Vector(loc)
    for k, v in props.items():
        obj[k] = v
    col.objects.link(obj)
    return obj


# ----------------------------------------------------------------- свет и мир (для просмотра)

def setup_showroom(col):
    world = bpy.data.worlds.new("W_Showroom")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.045, 0.05, 0.06, 1.0)
        bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = world

    def area(name, loc, energy, size, color):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.size = size
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = Vector(loc)
        ob.rotation_euler = Euler((math.radians(60), 0, math.radians(35)))
        col.objects.link(ob)

    area("L_Key", (0.9, -1.1, 1.2), 220.0, 0.8, (1.0, 0.97, 0.92))
    area("L_Fill", (-1.0, -0.6, 0.6), 60.0, 1.2, (0.7, 0.85, 1.0))


def finalize_and_save(path):
    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except Exception:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True, check_existing=False)


# ----------------------------------------------------------------- модели

def build_iskra9(col):
    """ИСКРА-9 — импульсный лазерный пистолет ближнего боя. Длина ≈ 0.26 м."""
    M = {
        "frame": make_material("M_Iskra_Frame", (0.035, 0.038, 0.045), metallic=0.55, roughness=0.34),
        "accent": make_material("M_Iskra_Accent", (0.82, 0.84, 0.86), metallic=0.1, roughness=0.28),
        "grip": make_material("M_Iskra_Grip", (0.02, 0.02, 0.022), metallic=0.0, roughness=0.8, rough_var=0.25),
        "metal": make_material("M_Iskra_Steel", (0.45, 0.47, 0.5), metallic=1.0, roughness=0.3),
        "vent": make_material("M_Iskra_Vent", (0.01, 0.012, 0.014), metallic=0.4, roughness=0.6),
        "glow": make_material("M_Iskra_Glow", (0.0, 0.0, 0.0), emit=(0.05, 0.85, 1.0), emit_strength=9.0,
                              rough_var=0.0, bump=0.0),
    }
    P = [
        dict(name="Frame", kind="box", size=(0.034, 0.20, 0.036), loc=(0, 0.075, 0.038), mat="frame"),
        dict(name="Frame_RailTop", kind="box", size=(0.020, 0.17, 0.008), loc=(0, 0.085, 0.060), mat="accent"),
        dict(name="Muzzle_Housing", kind="box", size=(0.030, 0.035, 0.040), loc=(0, 0.19, 0.036), mat="frame"),
        dict(name="Emitter_Barrel", kind="cyl", r=0.0075, L=0.05, rot=(90, 0, 0), loc=(0, 0.2325, 0.036), mat="metal"),
        dict(name="Emitter_Ring", kind="torus", R=0.0105, r=0.0022, rot=(90, 0, 0), loc=(0, 0.2575, 0.036), mat="glow"),
        dict(name="Emitter_Core", kind="cyl", r=0.0045, L=0.002, rot=(90, 0, 0), loc=(0, 0.2572, 0.036), mat="glow"),
        dict(name="Grip", kind="box", size=(0.030, 0.050, 0.100), loc=(0, 0.008, -0.030), rot=(-12, 0, 0), mat="grip"),
        dict(name="Grip_PowerCell", kind="box", size=(0.026, 0.030, 0.014), loc=(0, 0.0, -0.088), rot=(-12, 0, 0), mat="glow"),
        dict(name="Trigger", kind="box", size=(0.006, 0.012, 0.022), loc=(0, 0.030, 0.004), mat="frame"),
        dict(name="TriggerGuard_Front", kind="box", size=(0.006, 0.006, 0.035), loc=(0, 0.050, 0.002), mat="frame"),
        dict(name="TriggerGuard_Bottom", kind="box", size=(0.006, 0.040, 0.006), loc=(0, 0.030, -0.012), mat="frame"),
        dict(name="Sight_Rear", kind="box", size=(0.018, 0.012, 0.008), loc=(0, 0.160, 0.068), mat="frame"),
        dict(name="Sight_Front", kind="box", size=(0.012, 0.008, 0.012), loc=(0, 0.182, 0.068), mat="glow"),
        dict(name="SideStrip_L", kind="box", size=(0.0025, 0.100, 0.005), loc=(-0.0175, 0.100, 0.045), mat="glow"),
        dict(name="SideStrip_R", kind="box", size=(0.0025, 0.100, 0.005), loc=(0.0175, 0.100, 0.045), mat="glow"),
    ]
    for i, y in enumerate((0.090, 0.115, 0.140)):
        for side, sx in (("L", -1), ("R", 1)):
            P.append(dict(name=f"Vent_{side}{i+1}", kind="box", size=(0.004, 0.022, 0.024),
                          loc=(sx * 0.019, y, 0.035), mat="vent"))
    for p in P:
        p = dict(p)
        mat = M[p.pop("mat")]
        name = "SM_Iskra9_" + p.pop("name")
        add_part(col, name, p.pop("kind"), mat, **p)
    return {
        "ANCHOR_Muzzle": (0.0, 0.2605, 0.036),
        "ANCHOR_Grip": (0.0, 0.008, -0.030),
        "ANCHOR_Sight": (0.0, 0.160, 0.072),
        "ANCHOR_Foregrip": (0.0, 0.0, 0.0),  # pistol: off hand on the grip
    }


def build_zarya4(col):
    """ЗАРЯ-4 — лазерная штурмовая винтовка. Длина ≈ 0.88 м. Энергоячейка-магазин."""
    M = {
        "body": make_material("M_Zarya_Body", (0.05, 0.055, 0.065), metallic=0.45, roughness=0.42),
        "ceramic": make_material("M_Zarya_Ceramic", (0.80, 0.82, 0.84), metallic=0.0, roughness=0.32),
        "grip": make_material("M_Zarya_Grip", (0.02, 0.02, 0.024), metallic=0.0, roughness=0.85, rough_var=0.25),
        "metal": make_material("M_Zarya_Steel", (0.42, 0.44, 0.48), metallic=1.0, roughness=0.28),
        "vent": make_material("M_Zarya_Vent", (0.008, 0.009, 0.01), metallic=0.3, roughness=0.6),
        "coil": make_material("M_Zarya_Coil", (0.85, 0.45, 0.2), metallic=1.0, roughness=0.25,
                              emit=(1.0, 0.45, 0.15), emit_strength=0.6),
        "glow": make_material("M_Zarya_Glow", (0.0, 0.0, 0.0), emit=(0.05, 0.85, 1.0), emit_strength=8.0,
                              rough_var=0.0, bump=0.0),
        "glass": make_material("M_Zarya_Glass", (0.01, 0.03, 0.04), metallic=0.0, roughness=0.04,
                               emit=(0.1, 0.6, 0.9), emit_strength=1.2, rough_var=0.0, bump=0.0),
    }
    P = [
        dict(name="Receiver_Upper", kind="box", size=(0.052, 0.26, 0.068), loc=(0, 0.10, 0.09), mat="body"),
        dict(name="Receiver_Lower", kind="box", size=(0.050, 0.22, 0.040), loc=(0, 0.07, 0.04), mat="ceramic"),
        dict(name="Rail_Top", kind="box", size=(0.022, 0.20, 0.010), loc=(0, 0.12, 0.130), mat="metal"),
        dict(name="Shroud", kind="box", size=(0.046, 0.31, 0.050), loc=(0, 0.385, 0.090), mat="body"),
        dict(name="Barrel", kind="cyl", r=0.010, L=0.30, rot=(90, 0, 0), loc=(0, 0.69, 0.090), mat="metal"),
        dict(name="MuzzleBrake", kind="cyl", r=0.013, L=0.04, rot=(90, 0, 0), loc=(0, 0.86, 0.090), mat="metal"),
        dict(name="MuzzleGlow", kind="cyl", r=0.0095, L=0.004, rot=(90, 0, 0), loc=(0, 0.882, 0.090), mat="glow"),
        dict(name="MuzzleRing", kind="torus", R=0.0125, r=0.0022, rot=(90, 0, 0), loc=(0, 0.876, 0.090), mat="glow"),
        dict(name="Stock", kind="box", size=(0.040, 0.13, 0.100), loc=(0, -0.095, 0.085), mat="body"),
        dict(name="ButtPlate", kind="box", size=(0.044, 0.012, 0.110), loc=(0, -0.166, 0.085), mat="ceramic"),
        dict(name="Grip", kind="box", size=(0.034, 0.050, 0.120), loc=(0, 0.000, -0.040), rot=(-15, 0, 0), mat="grip"),
        dict(name="PowerCell_Mag", kind="box", size=(0.034, 0.050, 0.130), loc=(0, 0.140, -0.035), rot=(8, 0, 0), mat="ceramic"),
        dict(name="PowerCell_Strip", kind="box", size=(0.004, 0.012, 0.110), loc=(0.018, 0.140, -0.035), rot=(8, 0, 0), mat="glow"),
        dict(name="Holo_Housing", kind="box", size=(0.030, 0.070, 0.050), loc=(0, 0.060, 0.165), mat="body"),
        dict(name="Holo_Lens", kind="box", size=(0.002, 0.040, 0.034), loc=(0, 0.060, 0.172), mat="glass"),
        dict(name="Foregrip", kind="box", size=(0.030, 0.040, 0.100), loc=(0, 0.360, 0.005), rot=(-10, 0, 0), mat="grip"),
        dict(name="SideStrip_L", kind="box", size=(0.0025, 0.220, 0.012), loc=(-0.0265, 0.050, 0.090), mat="glow"),
        dict(name="SideStrip_R", kind="box", size=(0.0025, 0.220, 0.012), loc=(0.0265, 0.050, 0.090), mat="glow"),
    ]
    for i, y in enumerate((0.00, 0.05, 0.10, 0.15)):
        P.append(dict(name=f"RailTooth_{i+1}", kind="box", size=(0.026, 0.006, 0.004), loc=(0, 0.02 + y, 0.137), mat="metal"))
    for i, y in enumerate((0.26, 0.31, 0.36, 0.41, 0.46, 0.51)):
        sx = -1 if i % 2 else 1
        P.append(dict(name=f"Shroud_Vent_{i+1}", kind="box", size=(0.004, 0.040, 0.022),
                      loc=(sx * 0.024, y, 0.090), mat="vent"))
    for i, y in enumerate((0.58, 0.64, 0.70)):
        P.append(dict(name=f"CoilRing_{i+1}", kind="torus", R=0.0165, r=0.0028, rot=(90, 0, 0), loc=(0, y, 0.090), mat="coil"))
    for i, sx in enumerate((-1, 1)):
        P.append(dict(name=f"SlingMount_{i+1}", kind="cyl", r=0.006, L=0.03, rot=(0, 90, 0),
                      loc=(sx * 0.027, -0.02, 0.05), mat="metal"))
    for p in P:
        p = dict(p)
        mat = M[p.pop("mat")]
        name = "SM_Zarya4_" + p.pop("name")
        add_part(col, name, p.pop("kind"), mat, **p)
    return {
        "ANCHOR_Muzzle": (0.0, 0.892, 0.090),
        "ANCHOR_Grip": (0.0, 0.000, -0.040),
        "ANCHOR_Sight": (0.0, 0.060, 0.178),
        "ANCHOR_Foregrip": (0.0, 0.360, 0.005),
    }


def build_spolokh7(col):
    """СПОЛОХ-7 — плазменная винтовка с камерой-сферой и магазином-канистрой. Длина ≈ 1.17 м."""
    M = {
        "armor": make_material("M_Spolokh_Armor", (0.06, 0.065, 0.07), metallic=0.6, roughness=0.36),
        "body": make_material("M_Spolokh_Body", (0.16, 0.18, 0.13), metallic=0.1, roughness=0.6, rough_var=0.25),
        "grip": make_material("M_Spolokh_Grip", (0.02, 0.02, 0.022), metallic=0.0, roughness=0.85, rough_var=0.25),
        "gold": make_material("M_Spolokh_Gold", (0.9, 0.7, 0.3), metallic=1.0, roughness=0.22),
        "vent": make_material("M_Spolokh_Vent", (0.008, 0.009, 0.01), metallic=0.3, roughness=0.6),
        "plasma": make_material("M_Spolokh_Plasma", (0.0, 0.0, 0.0), emit=(1.0, 0.15, 0.7), emit_strength=12.0,
                                rough_var=0.0, bump=0.0),
        "glow": make_material("M_Spolokh_Glow", (0.0, 0.0, 0.0), emit=(1.0, 0.45, 0.1), emit_strength=6.0,
                              rough_var=0.0, bump=0.0),
        "glass": make_material("M_Spolokh_Glass", (0.01, 0.03, 0.04), metallic=0.0, roughness=0.04,
                               emit=(0.2, 0.7, 1.0), emit_strength=1.0, rough_var=0.0, bump=0.0),
    }
    P = [
        dict(name="Body_Main", kind="box", size=(0.070, 0.40, 0.110), loc=(0, 0.05, 0.100), mat="armor"),
        dict(name="Body_TopCover", kind="box", size=(0.060, 0.30, 0.020), loc=(0, 0.06, 0.165), mat="body"),
        dict(name="Chamber_Housing", kind="box", size=(0.070, 0.140, 0.130), loc=(0, 0.300, 0.100), mat="armor"),
        dict(name="Plasma_Cradle", kind="box", size=(0.030, 0.100, 0.030), loc=(0, 0.300, 0.170), mat="armor"),
        dict(name="Plasma_Chamber", kind="sphere", r=0.036, loc=(0, 0.300, 0.200), mat="plasma"),
        dict(name="Chamber_Ring", kind="torus", R=0.040, r=0.004, rot=(90, 0, 0), loc=(0, 0.300, 0.200), mat="gold"),
        dict(name="Barrel_Shroud", kind="cyl", r=0.024, L=0.25, rot=(90, 0, 0), loc=(0, 0.495, 0.100), mat="armor"),
        dict(name="Barrel", kind="cyl", r=0.014, L=0.16, rot=(90, 0, 0), loc=(0, 0.700, 0.100), mat="gold"),
        dict(name="Muzzle_Nozzle", kind="cyl", r=0.020, L=0.03, rot=(90, 0, 0), loc=(0, 0.800, 0.100), mat="armor"),
        dict(name="Muzzle_Plasma", kind="cyl", r=0.015, L=0.006, rot=(90, 0, 0), loc=(0, 0.818, 0.100), mat="plasma"),
        dict(name="Canister_Mag", kind="cyl", r=0.034, L=0.150, loc=(0, 0.100, -0.050), mat="body", seg=28),
        dict(name="Canister_Band", kind="torus", R=0.034, r=0.004, loc=(0, 0.100, -0.010), mat="glow"),
        dict(name="Grip", kind="box", size=(0.040, 0.070, 0.140), loc=(0, -0.060, -0.040), rot=(-15, 0, 0), mat="grip"),
        dict(name="TriggerGuard", kind="box", size=(0.006, 0.040, 0.005), loc=(0, -0.020, 0.000), mat="armor"),
        dict(name="Stock", kind="box", size=(0.055, 0.160, 0.140), loc=(0, -0.270, 0.100), mat="body"),
        dict(name="ButtPlate", kind="box", size=(0.060, 0.015, 0.150), loc=(0, -0.355, 0.100), mat="armor"),
        dict(name="Optic_Body", kind="cyl", r=0.022, L=0.120, rot=(90, 0, 0), loc=(0, 0.050, 0.200), mat="armor"),
        dict(name="Optic_Lens", kind="cyl", r=0.018, L=0.004, rot=(90, 0, 0), loc=(0, 0.112, 0.200), mat="glass"),
        dict(name="SideStrip_L", kind="box", size=(0.003, 0.220, 0.012), loc=(-0.0365, 0.000, 0.100), mat="glow"),
        dict(name="SideStrip_R", kind="box", size=(0.003, 0.220, 0.012), loc=(0.0365, 0.000, 0.100), mat="glow"),
    ]
    for i, y in enumerate((-0.05, 0.02, 0.09, 0.16)):
        P.append(dict(name=f"TopVent_{i+1}", kind="box", size=(0.050, 0.016, 0.004), loc=(0, y, 0.177), mat="vent"))
    for i, y in enumerate((0.42, 0.50, 0.58)):
        P.append(dict(name=f"TeslaRing_{i+1}", kind="torus", R=0.032, r=0.0045, rot=(90, 0, 0), loc=(0, y, 0.100), mat="gold"))
    for p in P:
        p = dict(p)
        mat = M[p.pop("mat")]
        name = "SM_Spolokh7_" + p.pop("name")
        add_part(col, name, p.pop("kind"), mat, **p)
    return {
        "ANCHOR_Muzzle": (0.0, 0.830, 0.100),
        "ANCHOR_Grip": (0.0, -0.060, -0.040),
        "ANCHOR_Sight": (0.0, 0.050, 0.232),
        "ANCHOR_Foregrip": (0.0, 0.120, -0.030),
    }


# ----------------------------------------------------------------- спецификация системы стрельбы

WEAPONS = {
    "iskra9_pistol_laser": dict(
        title="ИСКРА-9 (лазерный пистолет)", build=build_iskra9, root="WPN_Iskra9", mod_id="iskra9",
        cell=("cell_iskra9", "iskra9_cell"),
        props=dict(weapon_id="iskra9", kind="pistol_laser", fire_mode="semi", rpm=240, magazine=24,
                   reload_s=1.8, damage=6.0, headshot_mult=1.5, range_m=60, projectile="laser_bolt",
                   spread_deg=1.0, heat_per_shot=4.0, heat_max=100.0, cooldown_s=0.4,
                   muzzle_flash_color="#33D9FF", ammo_item="energy_cell_pistol")),
    "zarya4_laser_rifle": dict(
        title="ЗАРЯ-4 (лазерная штурмовая винтовка)", build=build_zarya4, root="WPN_Zarya4", mod_id="zarya4",
        cell=("cell_zarya4", "zarya4_cell"),
        props=dict(weapon_id="zarya4", kind="rifle_laser", fire_mode="auto", rpm=600, magazine=40,
                   reload_s=2.4, damage=9.0, headshot_mult=2.0, range_m=150, projectile="laser_beam",
                   spread_deg=0.6, heat_per_shot=2.5, heat_max=100.0, cooldown_s=3.0,
                   muzzle_flash_color="#33D9FF", ammo_item="energy_cell_rifle")),
    "spolokh7_plasma_rifle": dict(
        title="СПОЛОХ-7 (плазменная винтовка)", build=build_spolokh7, root="WPN_Spolokh7", mod_id="spolokh7",
        cell=("canister_spolokh7", "spolokh7_canister"),
        props=dict(weapon_id="spolokh7", kind="rifle_plasma", fire_mode="semi_burst", rpm=180, magazine=12,
                   reload_s=3.2, damage=16.0, aoe_radius_m=1.5, headshot_mult=1.3, range_m=200,
                   projectile="plasma_ball", spread_deg=1.5, heat_per_shot=12.0, heat_max=100.0, cooldown_s=2.0,
                   muzzle_flash_color="#FF26B3", ammo_item="plasma_canister")),
}


def add_mod_nodes(col, mod_id, anchors):
    """Узлы, которые читает мод (realwar GunRenderer): <id>.sight, <id>.arm_r, <id>.arm_l, <id>.bolt, <id>.flash."""
    grip = anchors["ANCHOR_Grip"]
    add_anchor(col, f"{mod_id}.sight", anchors["ANCHOR_Sight"], {})
    add_anchor(col, f"{mod_id}.arm_r", grip, {})
    add_anchor(col, f"{mod_id}.arm_l", anchors["ANCHOR_Foregrip"], {})
    add_anchor(col, f"{mod_id}.bolt", grip, {})
    flash_mat = make_material(f"M_{mod_id}_Flash", (0.0, 0.0, 0.0), emit=(1.0, 0.8, 0.4), emit_strength=25.0,
                              rough_var=0.0, bump=0.0)
    add_part(col, f"{mod_id}.flash", "sphere", flash_mat, loc=anchors["ANCHOR_Muzzle"], r=0.016)


def build_cell(key, spec):
    """Патрон-источник для винтовки/пистолета: энергоячейка или канистра (модели в мод отдельные)."""
    cell_name, _ = spec["cell"]
    reset_scene()
    col = get_collection("COL_" + cell_name)
    body = make_material("M_" + cell_name + "_Body", (0.12, 0.13, 0.15), metallic=0.5, roughness=0.35)
    glow = make_material("M_" + cell_name + "_Glow", (0.0, 0.0, 0.0), emit=(0.05, 0.85, 1.0), emit_strength=8.0,
                         rough_var=0.0, bump=0.0)
    if key == "spolokh7_plasma_rifle":
        add_part(col, cell_name + "_body", "cyl", body, loc=(0, 0, 0), r=0.034, L=0.150, seg=28)
        add_part(col, cell_name + "_band", "torus", glow, loc=(0, 0, 0.040), R=0.034, r=0.004)
    else:
        size = (0.034, 0.050, 0.130) if key == "zarya4_laser_rifle" else (0.026, 0.030, 0.014)
        add_part(col, cell_name + "_body", "box", body, loc=(0, 0, 0), size=size)
        add_part(col, cell_name + "_strip", "box", glow, loc=(size[0] / 2 + 0.002, 0, 0),
                 size=(0.004, size[1] * 0.6, size[2] * 0.8))
    path = os.path.join(OUT_DIR, cell_name + ".blend")
    finalize_and_save(path)
    return path


def export_glb(collection_name, glb_path):
    """GLB для мода: только меши и пустышки коллекции (без света и камер)."""
    bpy.ops.object.select_all(action="DESELECT")
    col = bpy.data.collections[collection_name]
    for o in col.objects:
        if o.type in {"MESH", "EMPTY"}:
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", use_selection=True,
                              export_apply=True, export_lights=False, export_cameras=False)
    return glb_path


def build_one(key):
    spec = WEAPONS[key]
    reset_scene()
    col = get_collection("COL_" + spec["root"])
    anchors = spec["build"](col)
    for name, loc in anchors.items():
        props = dict(spec["props"]) if name == "ANCHOR_Muzzle" else {}
        props.setdefault("anchor", name)
        add_anchor(col, name, loc, props)
    add_mod_nodes(col, spec["mod_id"], anchors)
    root = bpy.data.objects.new(spec["root"], None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.05
    root["title"] = spec["title"]
    col.objects.link(root)
    setup_showroom(col)
    path = os.path.join(OUT_DIR, key + ".blend")
    finalize_and_save(path)
    return path


# ----------------------------------------------------------------- проверка

def check_file(path):
    """Открывает файл без аддонов и печатает нарушения ТЗ §3.2.5/§11."""
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    bad_empty = [o.name for o in bpy.data.objects if o.type == "MESH" and len(o.data.polygons) == 0]
    missing_img = [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]
    no_mat = [o.name for o in bpy.data.objects if o.type == "MESH" and len(o.data.materials) == 0]
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    meshes = sum(1 for o in bpy.data.objects if o.type == "MESH")
    print(f"[CHECK] {os.path.basename(path)}: мешей={meshes}, треугольников={tris}")
    print("[CHECK] пустых мешей:", bad_empty)
    print("[CHECK] неупакованных текстур:", missing_img)
    print("[CHECK] мешей без материала:", no_mat)
    ok = not bad_empty and not missing_img and not no_mat
    print("[OK] файл открылся без аддонов" if ok else "[FAIL] файл зависит от аддонов / пустые объекты")
    return ok


def qa_render(path, outdir):
    """Рендер ракурсов для самопроверки (только в outdir, не в поставку)."""
    os.makedirs(outdir, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=path, load_ui=False)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    center = (lo + hi) / 2
    size = (hi - lo).length
    print(f"[QA] {os.path.basename(path)} габариты (м): {tuple(round(v, 3) for v in (hi - lo))}")

    target = bpy.data.objects.new("QA_Target", None)
    target.location = center
    bpy.context.scene.collection.objects.link(target)
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    trk = cam.constraints.new("TRACK_TO")
    trk.target = target
    trk.track_axis = "TRACK_NEGATIVE_Z"
    trk.up_axis = "UP_Y"
    scene.camera = cam

    views = {
        "front": Vector((0.0, -1.0, 0.25)),
        "side": Vector((1.0, 0.0, 0.25)),
        "three_quarter": Vector((0.6, -0.8, 0.45)),
        "top": Vector((0.1, -0.2, 1.0)),
    }
    base = os.path.splitext(os.path.basename(path))[0]
    for vname, d in views.items():
        cam.location = center + d.normalized() * size * 1.1
        scene.render.filepath = os.path.join(outdir, f"{base}_{vname}.png")
        bpy.ops.render.render(write_still=True)
        print("[QA] сохранено", scene.render.filepath)


def main(argv):
    if "--check" in argv:
        files = sorted(os.path.join(OUT_DIR, f) for f in os.listdir(OUT_DIR) if f.endswith(".blend"))
        results = [check_file(f) for f in files]
        sys.exit(0 if all(results) else 1)
    if "--qa" in argv:
        outdir = argv[argv.index("--qa") + 1]
        for key in WEAPONS:
            qa_render(os.path.join(OUT_DIR, key + ".blend"), outdir)
        return
    if "--glb" in argv:
        # GLB для мода: открыть каждый .blend и экспортировать коллекцию оружия и патрона
        glb_dir = argv[argv.index("--glb") + 1]
        for key, spec in WEAPONS.items():
            bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT_DIR, key + ".blend"), load_ui=False)
            print("[GLB]", export_glb("COL_" + spec["root"], os.path.join(glb_dir, spec["mod_id"] + ".glb")))
            cell_file = os.path.join(OUT_DIR, spec["cell"][0] + ".blend")
            bpy.ops.wm.open_mainfile(filepath=cell_file, load_ui=False)
            print("[GLB]", export_glb("COL_" + spec["cell"][0], os.path.join(glb_dir, spec["cell"][0] + ".glb")))
        return
    for key in WEAPONS:
        p = build_one(key)
        print("[BUILD]", p)
        c = build_cell(key, WEAPONS[key])
        print("[BUILD]", c)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
