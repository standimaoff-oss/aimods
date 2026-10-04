# Reply 10 plan / status

User (r10): "давай дальше" + some vehicles don't drive (= WW2 tanks) + Bismarck now, Su-57 next reply;
WW2 aviation list shrinks to 6 (He 111 + Pe-8, Ju 87 + Pe-2, Bf 109 + Yak-3).

## r10 (this reply)
- [x] WW2 tanks drive again (track roll / fmax, Ratte step 2.1, maxAccel) + gametest all_tanks_drive (15 kinds)
- [x] Bismarck model (Blender, 1:1, 251 m, May 1941 Rheinübung scheme), LOD, deck boxes (4093, 11 groups)
- [x] Ar 196 A-3 floatplane model
- [x] BattleshipEntity: 38 mounts (4x2 38 cm, 6x2 15 cm, 8x2 10.5 cm, 8x2 3.7 cm, 10+2x4 2 cm),
      director aim from the bridge view, range tables, slew rates, arcs, half-salvos, reloads, dispersion,
      automatic flak (time-fuzed 10.5 cm bursts, 3.7/2 cm tracer streams), catapult
- [x] AradoEntity: AI floatplane - coordinated-turn flight model, spotting orbit (halves dispersion),
      dive attacks with MG FF + 2 SC 50, return, water landing, crane recovery, can be shot down
- [x] Client: per-mount pose, recoil, rangefinders, catapult; big gun FX; fire-control HUD; hints
- [x] Decks: N rotating groups (turrets are walkable and rotate), large-host search radius
- [x] Camera 120 m, sight x6, LOD distance 150, yaw inertia (tau 10 s for L > 100 m)
- [ ] gametest bismarck_floats_fights_launches_and_steams
- [ ] in-game photos -> photos/4, report, zip, release

## r11 (next): Su-57
- maneuver mode (no AoA limiter, easy turns with inertia), many loadouts (bombs, S-8/S-13, Kh-38/ATGM),
  detailed first-person cockpit (MFDs/radar, stick, K-36 seat)

## later
- r9b: Tiger, Pz.IV, Pz.II, Sturmtiger, T-34-85, KV-5, BM-13 remodel from drawings
- WW2 aviation (6), modern list (Bradley, Su-25, Ural, Gepard, T-14, Kirov, TOS-1A), Titan zeppelin, A-40
