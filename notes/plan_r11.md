# Reply 11 plan / status  (user msg after r10 Bismarck)

User (r11), verbatim intents:
- WW2 aviation NOW: only 2 bombers + 2 fighters (1 USSR + 1 Germany each), NO dive bombers
  -> He 111 H-6 (DE bomber), Pe-8 (SU bomber), Bf 109 G-6 (DE fighter), Yak-3 (SU fighter)  [ask_user: "ww2first"]
- Twin-barrel guns (Ratte, Bismarck...) fire only one barrel -> FIX: both barrels at once (salvo)  [ask_user: "salvo"]
- Impact-point cross: shows where the shells of the ACTIVE weapon will land, 1st + 3rd person,
  designer RED with animation (not a plain white dot/cross), for every selected weapon.
- Tilted hitboxes: ships / vehicles that pitch/roll -> model tilts, deck boxes did not -> walking on air. FIX.
- Everything that drives must climb obstacles: front wheels/tracks go up the block, vehicle pitches, rear lower.
- Make a LIST of what can be added: new blocks, mechanics, rockets, transport, etc.
- Order after this: (r12) M2 Bradley, Ural-4320, TOS-1A, Su-57 (max beauty + detail + optimisation);
  (r13) Titan super-zeppelin (German airship) + cruiser Kirov.
- r10 leftovers: Bismarck release (photos/4, zip, SHA) - jar already built with r10 code.

## Work order (r11)
1. [ ] r10 wrap: photos/4 (have 01 broadside, 02 aft turrets), zip, SHA
2. [ ] Salvo fix: GunVehicle (Ratte main 2x28cm, others with 2 barrels), BattleshipEntity fireMain/fireSecondary both guns
3. [ ] Impact predictor cross (client): simulate active weapon ballistics -> world point -> project to screen;
       red animated reticle (rotating ticks, pulsing ring, range text), 1st + 3rd person, vehicles + craft + ship
4. [ ] Tilted decks: Decks pose with pitch/roll; transform point into body frame using full basis
5. [ ] Climbing: ground vehicles sample terrain under front/rear axle -> pitch (+ roll), raise front on step-up
6. [ ] WW2 planes: Blender models (He 111, Pe-8, Bf 109, Yak-3) + LOD + deck + flight code + weapons + tests
7. [ ] Ideas list (in reply + notes/ideas.md)
8. [ ] build, gametests, photos/5, report, zip, release
