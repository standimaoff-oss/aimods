# Reply 12 plan (user msg after r11 WW2 planes)

User (r12):
- Cockpits (1st person): instruments block the view -> FIX (eye above coaming, panel lower).
- Cockpit "almost fully filled with the aeroplane", no proper interior besides panel/seat -> real hollow cockpit
  (inner skin, seat, stick, pedals, side consoles, gunsight, canopy frame) for Bf 109, Yak-3, He 111, Pe-8.
- "put the sight in already" -> impact reticle (ImpactReticle, r11) + reflector gunsight glass reticle.
- IMMEDIATELY: M2 Bradley, Ural-4320, TOS-1A, Su-57 ("and that's the end") - max beauty + detail + optimisation.
- Where is the list of additions (blocks, mechanics, rockets, transport ...) -> notes/ideas.md + reply.

Carry-over r11 (unreleased): PlaneEntity + 4 planes, salvo, decks tilt, terrain pose, ImpactReticle, bombs.
Gametest r11a: all plane tests passed; 1 failure: bismarck deck carry (zombie not carried) -> diagnose.

## Work order
1. [ ] recover toolchain; Bismarck carry failure
2. [ ] cockpits: eye render check from Blender at the game eye (seatY + 0.77), rebuild 4 planes
3. [ ] Su-57: Blender model (+cockpit MFDs, K-36 seat, stick, HUD glass), jet PlaneEntity variant (thrust, AB,
       maneuver mode = no AoA limiter + high rates + inertia), loads: GSh-30-1, R-77/R-73?, KAB/FAB bombs, S-8/S-13
       rockets, Kh-38 ATGM-like guided
4. [ ] M2 Bradley: GunVehicle: M242 25 mm (APDS/HE), TOW (guided), M240C coax; 3 crew + 6 troops seats
5. [ ] TOS-1A: tracked MLRS (T-72 chassis), 24 x 220 mm thermobaric, elevation, reload
6. [ ] Ural-4320: 6x6 truck, troop seats, resupply mechanic (re-arms nearby vehicles) if time
7. [ ] ideas list, lang, tabs, icons, tests, build, photos/5, report, zip, SHA
/home/user/tools/blender/jet_textures.py
