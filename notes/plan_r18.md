# r18 plan (user: uniforms +6, WT module damage incl. heli blades / plane wings / ship guns & hull holes / engine smoke, radio strikes)
Split (standing rule: 2-3 replies):
- r18 (this): WT module damage for ALL vehicle classes + debris physics/animations + HUD module schematic + repair;
  Blender: wing_L/wing_R split for bf109/yak3/he111/pe8/su57, damage_fx.glb (shell holes) ; uniforms +6 if budget allows.
- r19: radio strikes (Tu-160 nuke, FAB-5000, FAB-500/1000 carpet by modern jets) + remaining uniforms.

## Damage core (ru.aiforge.realwar.damage)
- HitContext: ThreadLocal hit point + dir + kind(AP/HE/PROX/BULLET) set by ShellEntity/RocketEntity/SamMissile/Bullet/ConventionalBlast before hurt().
- Module bitmasks synced: DMG_BROKEN (int), DMG_HURT (int), REPAIR (float 0..1), holes (CompoundTag).
- Tanks: ENGINE, TRACK_L, TRACK_R, BARREL, TURRET (ring drive), AMMO, FIRE, DEAD. AP ray-marches through local zones; HE splash radius.
  Ammo detonation chance ~ rounds fraction; turret toss speed ~ sqrt(rounds*kg / turretTons); Abrams blow-out panels -> no toss.
  Track lost -> TrackDebris unroll animation (links peel off one by one and lie flat behind the tank).
  Crew repair when stationary: track 15 s, barrel 25 s, engine 20 s, turret 12 s. Fire 8 s -> HP loss, may reach ammo.
  Dead hull stays 90 s burning (tinted dark), then despawns.
- Heli: ROTOR (rotor node flies off spinning, lift 0), TAIL_ROTOR (uncontrolled yaw), ENGINE (smoke, lift x0.6), FIRE.
- Plane: WING_L/WING_R (wing + aileron fly off, roll moment, lift x0.45), ENGINE (smoke trail, thrust x0.4 / 0), TAIL (pitch/yaw authority x0.3), FIRE.
- Ship: GUN_i (one barrel blown off as debris, rest droop, turret smoking, cannot fire), HULL holes (Blender hole decal, list + draft, sinks when many below waterline), ENGINE (props stop), FIRE.
- DebrisEntity (mode RIGID / TRACK / ROTOR), DebrisRenderer renders GLB node subtrees with optional pose overrides.
- HUD: WT schematic (green ok / yellow damaged / red destroyed / grey missing) + repair timer.

## STATUS (end of r18)
DONE: damage for all classes, debris (track unroll / turret toss / rotor / wing / ship gun), holes+flood, HUD, repair,
/realwar damage command, DamageTests (5), 131/131, photos/11, report section 18.
NEXT (r19): radio strikes (Tu-160 nuke, FAB-5000, FAB-500/1000 carpet) + 6 uniform sets (+2 USSR, +2 US, +2 RF).
