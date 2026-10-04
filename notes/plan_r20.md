# r20 — fixes after msg 20

| # | request | done |
|---|---------|------|
| 1 | hit-cam window small; hit parts literally on the model (no squares) | HitCam rewrite: W = 22 % GUI width (100..140 px); GLB X-ray with per-node tints (barrel / turret / L,R track nodes turn orange / red); internal modules = Blender props `models/hitcam_modules.blend` (engine, round, crew, turret drive) placed per ammo layout (carousel 22 / bustle 3×6 / sponson 2×2 per side / pack 4×4) and crew seats; interior nodes hidden |
| 2 | Ratte interior passage blocked | `tools/rwveh/ratte.py`: racks moved aft of the door, aisle free; rebuilt glb + lod |
| 3 | sight inside the tubes (Grad, TOS, Ratte) | `VehicleClient.gunnerSight`: perTube TOS side sight, Ratte twin centre; BM-21 GunnerControl side sight |
| 4 | action hints as square tiles | `ActionBar` Chip(key, icon, count, state) tiles 20×26 next to the ammo slots, icons `textures/gui/actions.png` (Blender) |
| 5 | bottom-left top-down view accurate | WtHud.cardModel: the vehicle's own GLB from above (flat shaded), real turret bearing/elevation, damaged parts painted on it, damaged engine/ammo/drive props over the roof |
| 6 | crosshair colour = penetration chance | ImpactReticle.judge: Armour.solve best/worst roll vs. target under the impact point; green / yellow / red; no text |
| 7 | several shots in one hit cam | HitCam keeps up to 6 shots on the same target while the camera is open; header best result ×N |

Also: VehicleDamage bustle ammo zone turns with the turret; GlbRenderer NODE_TINT / XRAY_RGB / FLAT modes.
