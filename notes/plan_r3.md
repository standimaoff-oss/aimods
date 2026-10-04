# Plan — replies 3..5 (user: "давай дальше" + new weapons over 2-3 messages)

## Backlog from reply 2
- [x] A1 Drivable Yars TEL (MZKT-79221): driver seat + operator seat, WASD, wheel spin/steer (16 wheels, 6 steered axles), jacks, erect only when stopped.
- [x] A2 Yars launch by radar: target picked on the radar map (operator), TEL erects, launches ICBM at the map target.
- [x] A3 Radar map 5000x5000 blocks: heightmap-shaded terrain (mountains), water (rivers/lakes), villages (structures), optimized
      (server samples coarse tiles async/incremental, cached per chunk column, client texture 256..512 px, zoom).
- [ ] A4 Better RW missile models (rocket 9M22/9M55, 48N6 SAM, RW cruise/ballistic missiles in models/glb).
- [ ] A5 RW Tu-95 entity uses our Tu-95MS model (re-rig to RW AircraftRenderer node contract).
- [ ] A6 Prune old TEL from nukes.glb.

## New content (user list)
### Fortification blocks (msg 3)
- [x] Sandbags (wall block, connects + stacks; half-slab variant), sandbag corner
- [x] Barbed wire (connects like a fence; slows + damages entities), concertina coil
- [x] Czech hedgehog (anti-tank, blocks vehicles), dragon's teeth (concrete pyramid)
- [x] Concrete barrier (Jersey / Т-образный блок), camo net (decorative, see-through)
### Ground vehicles (3) — msg 4
- [x] T-90M (RU) MBT: turret + 125 mm cannon (HE/APFSDS shells), coaxial MG
- [x] M1A2 Abrams (US) MBT
- [x] BMP-3 (RU) / or M2 Bradley IFV with 30 mm autocannon
### Artillery — msg 4
- [x] D-30 122 mm howitzer (stationary, towed)
- [x] M777 155 mm howitzer (stationary, towed)
- [x] 2S19 Msta-S self-propelled 152 mm (SPG)
### Air (2) — msg 6
- [ ] Ka-52 attack helicopter (RU) — rockets + cannon
- [ ] AH-64 Apache or Su-25 — decide
### Water (2) + underwater (1) — msg 6
- [ ] Patrol boat (Raptor / Mk VI), landing craft or fast attack boat
- [ ] Submarine (Kilo-class / project 636) — dives, torpedoes
### Handheld (3) — msg 3 or 4
- [x] RPG-7 (rocket, AT damage vs vehicles)
- [x] Igla / Stinger MANPADS (IR homing vs aircraft, drones, helicopters)
- [x] Javelin ATGM (top-attack lock-on) or AT4

## Split
- msg 3 (this): A1 A2 A3 + fortification blocks + handheld RPG-7 / MANPADS / Javelin (gameplay quick wins)
- msg 4: 3 ground vehicles + 3 artillery (DONE). A4 A5 A6 moved to msg 5 (model-only work, no gameplay impact)
- msg 5: (user request) FPS optimisation + detached parts — DONE (renderer rewrite, LOD1, 0 floating parts, 82/82)
- msg 6: A4 A5 A6 + 2 air + 2 water + 1 sub

## r3 test status (21:33)
- 76/76 gametests x3 runs. New batches: rw_fort (fort connect/collision), rw_hh (RPG hit, Igla homing, Javelin top-attack 60 m, seeker cone).
- tools/gametest.sh = deterministic run (superflat, fixed seed, fresh world). GameTestServer otherwise used random-seed noise world.
- TestChunks.follow/path: keeps far flight paths entity-ticking (no players in gametest server).
- ZU-23 test: target spawned after the gun settles (it drops 2 blocks), on the barrel line.
- Javelin guidance tuned with tools/sim/javelin_sim.py: direct <45 m, dive turn x2.8, dive trigger horiz < dy + 2*sp.
- Igla: segment proximity fuse.

## r4 test status (08:26 Oct 2)
- 82/82 gametests (new batch rw_gun: 6 tests — spawn/nodes, reload, HE vs vehicle, APFSDS, howitzer range, towed seat).
- In-game: lineup of all 6 rendered OK; T-90M gunner: lase 1090 m, solution -2.0 deg, HE hit Abrams 650 -> 601.9 HP.
- In-game fixes: gunner eye raised above cupola/RWS for all 6 (Specs gunner seats); gun status strip moved to top centre (no overlap with hints panel).

## r5 status (10:05 Oct 2)
- FPS (llvmpipe): 3 tanks near 5 -> 15-17, far 5 -> 17-20, empty 26 -> 29. Gametest 82/82.
- New models for msg 6 must: use armor_lib low-poly helpers, run auto_attach + floatcheck, and get a _lod1 via
  tools/rwveh/make_lod.py (+ STRIP_IMAGES=1 glb_quant). Budget: ground vehicles <=32k tris, aircraft <=60k.
- Note: a summoned (crew-less) Tu-95MS starts airborne at ~45 m/s and crashes - old behaviour, not a regression.
- Workspace 114 MB after r5 cleanup (shots → jpg, old shot dirs and legacy mods' GLBs removed). msg 6 adds ~6 models: keep raw GLBs in .cache, check du before finishing.
