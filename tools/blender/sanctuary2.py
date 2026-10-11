"""
«Убежище II» — фантастический корабль Таноса (вымышленный, по мотивам «Мстителей: Финал»).

Запуск (Blender 4.2+/5.x или модуль bpy; см. future_weapons.py):
    python sanctuary2.py                    # построить models/future_vehicles/sanctuary2.blend
    python sanctuary2.py -- --glb DIR       # + GLB для мода (DIR/sanctuary2.glb)
    python sanctuary2.py -- --qa DIR        # QA-рендер ракурсов (не входит в поставку)
    python sanctuary2.py -- --check         # проверка файла (открытие без аддонов)

Соглашения (как у оружия, см. future_weapons.py):
  * Метры, scale = 1, трансформы применены, нос вдоль +Y, вверх +Z.
  * Начало координат — центр корпуса на уровне киля.
  * Примитивы + фаски 1.5 мм + сглаживание по углу 35°, процедурные материалы.
  * Якоря ANCHOR_* — пустышки с пользовательскими свойствами для игровой логики.
  * Размеры вымышленные: длина ≈ 64.5 м, размах крыльев ≈ 47 м, высота ≈ 21.5 м (с антенной).
"""

import importlib.util
import math
import os
import sys

import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT_BLEND = os.path.join(ROOT, "models", "future_vehicles", "sanctuary2.blend")
COL = "COL_sanctuary2"


def _load_helpers():
    spec = importlib.util.spec_from_file_location("future_weapons", os.path.join(HERE, "future_weapons.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FW = _load_helpers()


def part(col, name, kind, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=None, **dims):
    """Деталь через helper из future_weapons; scale применяется к мешу (без масштаба объекта)."""
    if scale is None:
        return FW.add_part(col, name, kind, mat, loc=loc, rot=rot, **dims)
    # сначала масштаб вокруг начала меша, потом перенос (иначе смещение тоже умножится)
    obj = FW.add_part(col, name, kind, mat, loc=(0, 0, 0), rot=rot, **dims)
    obj.data.transform(Matrix.Diagonal(scale).to_4x4())
    obj.data.transform(Matrix.Translation(loc))
    obj.data.update()
    return obj


def build():
    FW.reset_scene()
    col = FW.get_collection(COL)

    M = {
        "hull": FW.make_material("M_San_Hull", (0.055, 0.058, 0.066), metallic=0.65, roughness=0.32),
        "gold": FW.make_material("M_San_Gold", (0.72, 0.55, 0.22), metallic=1.0, roughness=0.28),
        "wing": FW.make_material("M_San_Wing", (0.07, 0.075, 0.085), metallic=0.5, roughness=0.4),
        "vent": FW.make_material("M_San_Vent", (0.01, 0.012, 0.014), metallic=0.4, roughness=0.7),
        "purple": FW.make_material("M_San_Purple", (0.55, 0.2, 1.0), metallic=0.0, roughness=0.2,
                                   emit=(0.6, 0.2, 1.0), emit_strength=10.0, bump=0.0),
        "cyan": FW.make_material("M_San_Cyan", (0.3, 0.9, 1.0), metallic=0.0, roughness=0.2,
                                 emit=(0.3, 0.9, 1.0), emit_strength=8.0, bump=0.0),
    }

    # --- корпус: длинный киль, хвостовой блок, острый нос -------------------
    part(col, "SM_San_Hull_Main", "box", M["hull"], loc=(0, -2, 0), size=(9.0, 44.0, 7.0))
    part(col, "SM_San_Nose", "sphere", M["hull"], loc=(0, 24, -0.3), r=4.5, scale=(1.0, 1.6, 0.85))
    part(col, "SM_San_Tail_Block", "box", M["hull"], loc=(0, -27, 0), size=(10.0, 8.0, 8.0))
    part(col, "SM_San_Spine", "box", M["hull"], loc=(0, -4, 5.0), size=(3.5, 20.0, 3.0))
    part(col, "SM_San_Spire_L", "box", M["hull"], loc=(-1.2, -4, 8.5), size=(0.6, 6.0, 3.0))
    part(col, "SM_San_Spire_R", "box", M["hull"], loc=(1.2, -4, 8.5), size=(0.6, 6.0, 3.0))
    part(col, "SM_San_Antenna", "cyl", M["gold"], loc=(0, -4, 12.5), r=0.12, L=4.0)

    # --- золотые кольца-бандажи вокруг корпуса (по оси Y) ---------------------
    for i, y in enumerate((-14.0, 2.0, 16.0)):
        part(col, f"SM_San_Band_{i}", "torus", M["gold"], loc=(0, y, 0), rot=(90, 0, 0), R=5.0, r=0.28)

    # --- боковые вентиляционные решётки -------------------------------------
    for side in (-1, 1):
        for j, y in enumerate((-12.0, -6.0, 0.0, 6.0)):
            part(col, f"SM_San_Vent_{'LR'[side > 0]}{j}", "box", M["vent"],
                 loc=(side * 4.55, y, 0.0), size=(0.12, 1.4, 0.9))

    # --- крылья (плоские стреловидные плиты) ----------------------------------
    for side in (-1, 1):
        part(col, f"SM_San_Wing_{'LR'[side > 0]}", "box", M["wing"],
             loc=(side * 12.5, -3.0, -1.0), rot=(0, 0, -20 * side),
             size=(20.0, 9.0, 1.0))
        part(col, f"SM_San_Winglet_{'LR'[side > 0]}", "box", M["hull"],
             loc=(side * 21.2, -9.0, 2.5), rot=(0, 0, -20 * side),
             size=(0.8, 6.0, 5.0))

    # --- маршевые подвесные гондолы под крыльями ----------------------------
    for side in (-1, 1):
        x = side * 16.0
        tag = "LR"[side > 0]
        part(col, f"SM_San_Pod_{tag}", "cyl", M["hull"], loc=(x, -6.0, -2.2), rot=(90, 0, 0), r=2.0, L=20.0, seg=24)
        part(col, f"SM_San_PodNozzle_{tag}", "torus", M["purple"], loc=(x, -16.2, -2.2), rot=(90, 0, 0),
             R=1.5, r=0.22)
        part(col, f"SM_San_PodIntake_{tag}", "torus", M["gold"], loc=(x, 3.6, -2.2), rot=(90, 0, 0),
             R=1.9, r=0.2)

    # --- четыре маршевых двигателя в хвосте ---------------------------------
    for sx in (-1, 1):
        for sz in (-1, 1):
            tag = f"{'LR'[sx > 0]}{'DU'[sz > 0]}"
            x, z = sx * 2.6, sz * 2.2
            part(col, f"SM_San_Engine_{tag}", "cyl", M["hull"], loc=(x, -30.0, z), rot=(90, 0, 0), r=1.6, L=6.0, seg=24)
            part(col, f"SM_San_EngineGlow_{tag}", "torus", M["cyan"], loc=(x, -33.1, z), rot=(90, 0, 0),
                 R=1.2, r=0.18)

    # --- носовая пушка на брюхе ------------------------------------------------
    part(col, "SM_San_Cannon_Turret", "sphere", M["hull"], loc=(0, 8.0, -4.6), r=2.4)
    part(col, "SM_San_Cannon_Barrel", "cyl", M["gold"], loc=(0, 12.5, -4.6), rot=(90, 0, 0), r=0.6, L=9.0, seg=20)
    part(col, "SM_San_Cannon_Muzzle", "torus", M["purple"], loc=(0, 17.0, -4.6), rot=(90, 0, 0), R=0.75, r=0.14)

    # --- светящиеся окна рубки на носу ----------------------------------------
    part(col, "SM_San_Bridge_Glass", "box", M["cyan"], loc=(0, 22.5, 3.0), size=(4.6, 1.2, 0.5))

    # --- якоря для игровой логики ---------------------------------------------
    anchors = {
        "ANCHOR_Bridge": ((0, 20.0, 2.6), {"role": "pilot_seat"}),
        "ANCHOR_Cannon_Muzzle": ((0, 17.5, -4.6), {"role": "cannon_muzzle"}),
        "ANCHOR_Engine_L": ((-2.6, -33.5, 0.0), {"role": "engine_left"}),
        "ANCHOR_Engine_R": ((2.6, -33.5, 0.0), {"role": "engine_right"}),
        "ANCHOR_Strike_Drop": ((0, 0.0, -4.6), {"role": "strike_drop_point"}),
        "ANCHOR_Pod_L": ((-16.0, -16.2, -2.2), {"role": "pod_nozzle_left"}),
        "ANCHOR_Pod_R": ((16.0, -16.2, -2.2), {"role": "pod_nozzle_right"}),
    }
    for name, (loc, props) in anchors.items():
        FW.add_anchor(col, name, loc, props)

    FW.setup_showroom(col)
    return col


def export_glb(glb_path):
    return FW.export_glb(COL, glb_path)


def main(argv):
    if "--glb" in argv:
        glb_dir = argv[argv.index("--glb") + 1]
        build()
        print("[GLB]", export_glb(os.path.join(glb_dir, "sanctuary2.glb")))
        return
    if "--qa" in argv:
        outdir = argv[argv.index("--qa") + 1]
        build()
        FW.finalize_and_save(OUT_BLEND)
        FW.qa_render(OUT_BLEND, outdir)
        return
    if "--check" in argv:
        FW.check_file(OUT_BLEND)
        return
    build()
    FW.finalize_and_save(OUT_BLEND)
    print("[BUILD]", OUT_BLEND)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
