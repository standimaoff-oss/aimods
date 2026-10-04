# Plan — reply 6: helicopters, boats, submarine (physics first)

User (msg 6): "Дальше плаванье и полет прям физично! И вертолет у нас прям мышкой поворот идёт! Крен и т.д.
крен можно отключить (режим висения) разное вооружения птур, или шашки/нары"
Interpretation: realistic flight/swim physics; heli steered with the MOUSE (cyclic), with roll; a mode that disables
roll (stabilisation/hover mode); weapons: ATGM, flares ("шашки" = тепловые ловушки), NAR rocket pods, + cannon.

## Package ru.aiforge.realwar.craft (new, independent of ground VehicleEntity)
- CraftKind: KA52, AH64, RAPTOR (pr.03160), CB90 (SE), SUB636 (pr.636.3) — physical params, seats, weapons.
- CraftEntity (abstract): yaw/pitch/roll (+ rates), velocity m/s, seats with full 3D transform, HP/fuel/engine,
  client-authoritative physics for the pilot (CraftStatePacket C->S), server physics when no pilot,
  CraftControlPacket (fire held, actions: engine, weapon cycle, flare, mode, seat, salvo), weapons + ammo.
- HeliEntity: rotor RPM spool, collective, thrust along body-up, ground effect, ETL, vortex ring state, retreating
  blade stall near Vne, climb-rate thrust loss, body-axis quadratic drag, weathervane, torque coupling (AH-64),
  autorotation, gear contact, hard landing / dynamic rollover / rotor strike (chops leaves), stabilisation mode
  (roll auto-level, mouse X -> yaw, altitude hold).
- BoatEntity: buoyancy from hull sample points (per-point submersion -> force + torque), pitch/roll dynamics,
  planing drag drop, propeller/waterjet thrust, rudder yaw ~ speed, heel into turn, small waves, beaching.
- SubEntity: same buoyancy + ballast fraction (Space blow / C flood), hydroplanes, depth hold mode (V),
  battery/diesel, torpedoes (6 tubes, 18), periscope depth.
- CraftOrdnance entity: VIKHR (laser beam riding), HELLFIRE (SAL laser spot), S8 / HYDRA (unguided), TORPEDO
  (acoustic homing), FLARE (IR decoy: Igla re-targets). 30 mm cannon = ShellEntity with new Ballistics profiles.
- Client: CraftClient (mouse cyclic via per-frame look delta in ComputeCameraAngles, camera roll, free look LAlt),
  CraftHud (speed/alt/VS/heading/rotor/collective/horizon/warnings/weapon + bottom control hints), CraftRenderer.
- Items: ka52, ah64, raptor, cb90, sub636 spawners (VEHICLES tab) + craft_service_kit (rearm + refuel, AMMO tab).
- GameTests batch rw_craft.

## Models (Blender, tools/rwveh/*.py, armor_lib helpers, auto_attach + floatcheck, _lod1)
- ka52.py, ah64.py, raptor.py, cb90.py, sub636.py, craft_ordnance.py (vikhr, hellfire, s8, hydra, torpedo)
- Node contract: heli rotor_main/rotor_upper/rotor_lower/rotor_tail, rotor_disc*, gun_yaw/gun_pitch, gear_*;
  boat turret_yaw/turret_pitch, radar, rudder/jet_L/jet_R; sub rudder, planes_bow, planes_stern, prop, periscope.

## Deferred to msg 7: A4 (RW missile models), A5 (RW Tu-95 -> Tu-95MS rig), A6 (prune nukes.glb TEL).
