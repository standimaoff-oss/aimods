# AI Arsenal — merged mod plan (user request 2026-10-01)

User (RU): "drones: 2 recon (Reaper-like), 4 Shahed-like, 2 FPV kamikaze (different payloads); 4 different cruise missiles;
3 nuclear bombs: RDS-1, AN602 (Tsar Bomba), + intercontinental medium; detonate them remotely from a distance.
EVERYTHING IN ONE MOD: Tu + BM-21 + this." User skipped the clarifying questions -> defaults below.

## Decisions (defaults chosen by agent)
- One mod: modid `aiarsenal`, name "AI Arsenal", project `/home/user/mods/aiarsenal`, jar `release/aiarsenal-1.0.0.jar`.
  Old packages kept: `ru.aiforge.bm21grad.*`, `ru.aiforge.tubombers.*` (MODID constants -> "aiarsenal", @Mod removed);
  new code `ru.aiforge.arsenal.*` (main @Mod class `AiArsenal`).
- Shared registry names deduped: particles fireball/blast_smoke/smoke_wall + sounds explosion_near/far/hydraulics
  registered once (bm21 registry), tubombers ModRegistry aliases them.
- Drone control "mixed": recon = tablet camera (loiter autopilot, gimbal, zoom, designate);
  Shahed = rail launch to coordinates/tablet target, autonomous; FPV = goggles, first-person piloting, video noise.
- Nukes scaled with real proportions: r = 40 * (Y/22kt)^(1/3), Tsar capped ~170. Airburst vs ground burst.
  Column-based progressive destruction, fireball, mushroom, flash, shock wave, fallout zone.
- Third nuke = ICBM (Yars-like) with ~300-800 kt medium warhead, launched from a canister launcher to coordinates.
- Remote detonation: "Detonator" item + SavedData registry of armed charges (works at any distance, forceloads chunk).
- Cruise missiles: Kh-101, Kh-55 (air-launched from Tu-95/Tu-160 bay as load types + ground canister),
  3M14 Kalibr, BGM-109 Tomahawk (ground/ship canister with booster).
- Drones: MQ-9 Reaper, Orion (Inokhodets); Shahed-136 (Geran-2), Shahed-131 (Geran-1), Shahed-238 (Geran-3 jet),
  Liutyi; FPV 7" with PG-7VL, FPV 10" with TM-62.

## Blender files (models/)
- recon.blend/glb, shahed.blend/glb, fpv.blend/glb, cruise.blend/glb, nukes.blend/glb (+ launchers inside)

## Steps
1. [x] merge project — compile OK, 18/18 gametests pass (logs/aiarsenal_gametest.log)
2. [x] Blender models: models/{recon,shahed,fpv,cruise,nukes}.{blend,glb} (scripts tools/blender/{arsenal_textures,arsenal_lib,recon,shahed,fpv,cruise,nukes}.py; run via mcp.py exec lib alib arsenal_lib X)
3. [ ] code: nukes, detonator, missiles, drones, tablet, goggles, launchers
4. [ ] sounds, lang, icons, recipes
5. [ ] tests (gametests, rcon, client screenshots), report reports/aiarsenal.md, release

## Progress (session 3)
- [x] Step 3 code: client NukeFx/ArsSounds/LauncherScreen/DetonatorScreen written; compileJava clean.
- [x] sounds.json (+14), lang en/ru (+~165 keys; colliding msg keys renamed a_busy/a_no_target/a_empty/a_full/a_loaded/a_target_set/a_no_ammo).
- [x] Tablet: Shift+RMB (or unlinked RMB) designates target by look ray 1 km.
- [x] Icons: tools/render_ars_icons.sh (Blender Cycles from models/*.blend) + tools/gadget_icons.py; recipes 21.
- [x] Gametests: arsenal/gametest/ArsenalGameTests (6) -> 24/24 pass (logs/aiarsenal_gametest.log).
- [ ] Step 4: build jar, server/client install, in-game screenshots.

# NEW TASK (msg after aiarsenal 1.0 build) — merge Real War 0.4.0 + improvements, split in 2 messages
User (RU): always deliver an extra zip of sources where every file has ".txt" appended (tools/src_zip.sh -> release/aiarsenal-sources-txt.zip), refresh it every time.
Take attached mod realwar-0.4.0 (uploads/realwar-0.4.0 (1).jar.txt, compiled only) and bring everything into ONE mod;
improve all missile models, drones not yet improved, air-defence vehicles etc.; Yars mobile launcher model is bad -> beautiful;
split work over 2 messages. Explosions for nukes & drones like Real War. Yars TEL drivable + launch by radar.
Radar shows 5k x 5k terrain map (mountains, rivers, lakes, villages) but optimized. Smoke/trail on missile launches.

Real War facts: decompiled with CFR -> ~/.cache/rwsrc (139 classes, 21k lines, SRG names m_/f_ -> remap with createSrgToMcp output).
Contents: missiles tactical/operational/icbm/cruise x warheads (he/kinetic/mirv/mirv_heavy/thermobaric/penetrator/cluster), missile_rv,
launch_pad_1..3 + launch_computer + siren blocks, radar_mobile/radar_post vehicles (RadarNet), s400 + sam_48n6, zu23 flak, grad, smerch,
tu95 (simple), fab500/1500/5000 air bombs, little_boy, rds_4 + crafting chain (ores uranium/fluorite/bismuth, centrifuge, reactor,
radiochem plant), hazmat, geiger, radiation, blast system (BlastManager/NuclearBlast/ConventionalBlast), client FX (ClientBlastManager,
NukeFx CapKind, ConvFx, TrailFx, FxParticle/FxSystem sprites), MapScreen sight.
Collisions to rename on merge: items fab500/fab1500 -> fab500m54/fab1500m54; entity ids missile/rocket/bomb -> rw_*; sounds
bomb_whistle/nuke_blast/nuke_far -> rw_*; ~15 hud/key lang keys; channel realwar:main -> aiarsenal:realwar; configs -> aiarsenal-realwar-*.toml.

PLAN msg 1: src zip; merge RW (package ru.aiforge.realwar); RW blast FX for our nukes/drones/missiles; trails; new Yars TEL model.
PLAN msg 2: improved models for RW missiles/S-400/radars/ZU-23/Smerch/pads + drones; drivable TEL + radar launch; radar 5k terrain map.

## Real War merge — progress (reply 1)
- tools/port_realwar.py <rwsrc> <rwjar-dir> <mod> <srg> : full port (package, SRG->Mojang via build/createSrgToMcp/output.srg,
  namespace + key rules [registry keys -> .aiarsenal., others -> .aiarsenal.rw., key.categories.aiarsenal_rw],
  id renames fab500/1500->fab500m54/fab1500m54, entities rw_missile/rw_rocket, sounds rw_*; channel aiarsenal:realwar).
  NOTE: re-running it OVERWRITES src/main/java/ru/aiforge/realwar (hand fixes then lost) -> do not re-run.
- tools/fix_cfr.py: generic CFR fixes; hand fixes: VehicleHud.vehicleGuide, ColumnOrder (p = pos[q]++), GlbModel (JsonArray a),
  ClientBlastManager iterators, LaunchComputerBlockEntity iterator, RocketEntity HitResult, RemoteDetonatorItem bent,
  GlbAssets try-with-resources, AircraftClient pitch, RealWarCommand gy + literal "realwar", tests generics.
- RealWar.init(context) called from AiArsenal ctor; configs aiarsenal-realwar-common/client.toml; RealWar.ownsItem().
- Integration: ArsenalConfig nuclear.realWarBlast / conventional.realWarBlast (default true):
  arsenal NuclearBlast.detonate -> realwar NuclearBlast.start(burst, kt, ground<12 blocks);
  Warheads.detonate -> realwar ConventionalBlast.explode(heKg(k), frag(k)).
  TrailFx.trail()/engineWisp() public; arsenal/client/ArsTrails (missile/icbm/shahed clientTick).
- Gametests run 1: 64/68 (fails: command_realwar [fixed], little_boy_block_detonation lining 0, computer_salvo 3, tuReleasesKh101 released 1).

## Real War merge — reply 1 finished (2026-10-01)
- little_boy test fixed: GameTest world is void + neighbour water flooded the crater → `groundBed` builds a sealed dirt bed (stone walls r30..36, drains fluids). Diagnostic suffix `dbgInfo(...)` in the assert message; NuclearBlast.dbg* counters harmless.
- Gametests 68/68.
- New Yars TEL model: tools/blender/yarstel.py → models/yarstel.{glb,blend}; slimmed copy in assets/aiarsenal/glb/yarstel.glb. Kind YARS_TEL glb = "yarstel". ArsRenderer applies yarstel_jacks (min(1, erect*6)) + yarstel_erect.
  Nodes: YARSTEL root, _geo, _Erector(_Cap,_Missile), _St{a}{L,R} > _W{a}{L,R} (a=0..7, L = +x), _Jack0..3, _RamL/R>_S1>_S2.
- Old TEL still inside nukes.glb (unused now) — can be pruned in reply 2.
- Reply 2 TODO: missile/S-400/radar/ZU-23/Smerch/pad/drone models; drivable TEL (wheel spin W*, steer St*), radar launch; radar 5k×5k map.

## Reply 2 (done): tabs by category + all RW vehicles remodelled
- ModTabs: Техника/Дроны/Ядерное/Ракеты/Боеприпасы/Узлы/Руды/Снаряжение; old arsenal/artillery/aviation tabs removed.
- New GLBs (tools/rwveh/*.py, lib tools/blender/rwveh_lib.py, quantized by glb_quant.py): grad (our BM-21 re-rig, fires FORWARD), smerch
  (pivot at front end, yaw (0,1.3,1.0), muzzles z -7.25, traverse 30), s400, radar_mobile, zu23, radar_post. Blends: models/rw_*.blend.
- FlakEntity recoil along +Z. Gametests 68/68. In-game client render verified (shots/rwveh/ingame_*.jpg).
- Pending: drivable Yars TEL + radar launch, radar 5k map, RW missile models, RW tu95 re-rig, prune old TEL from nukes.glb.
