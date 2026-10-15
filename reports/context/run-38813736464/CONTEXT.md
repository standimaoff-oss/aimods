# Contextual Minecraft action audit

**Process outcome: PASS**
Recorded cases: 35/35; PASS 35; FAIL 0; RUNNING 0.

**This is not full acceptance of all 448 items, all weapon slots, or Windows/NVIDIA stability.**
CI build/GameTest/upload outcomes must additionally be checked on the linked workflow run.

| Item | Result | Executed action / failure |
|---|---|---|
| aiarsenal:missile_tactical_he | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_tactical_kinetic | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_tactical_mirv | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_tactical_thermobaric | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_operational_he | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_operational_kinetic | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_operational_mirv | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_operational_penetrator | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_cruise_he | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_cruise_cluster | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_icbm_he | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_icbm_kinetic | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_icbm_mirv | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:missile_icbm_mirv_heavy | PASS | survival pad item placement -> consume missile -> real 150-tick load -> schedule -> flight/warheads -> destructive jobs finish |
| aiarsenal:ah64_vehicle | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:bf109_plane | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:bismarck_ship | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:cb90_boat | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:he111_plane | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:ka52_vehicle | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:pe8_plane | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:raptor_boat | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:su57_plane | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:sub636_vehicle | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:yak3_plane | PASS | survival item placement/boarding; real H and LMB; production service-kit interaction; real repeat LMB plus projectile/bullet proof |
| aiarsenal:cannon_fr6 | PASS | survival cannon item placement -> real charge consumption/160-tick load -> ignition/tool wear -> cannonball spawn; twice |
| aiarsenal:cannon_ri12 | PASS | survival cannon item placement -> real charge consumption/160-tick load -> ignition/tool wear -> cannonball spawn; twice |
| aiarsenal:javelin | PASS | actual RMB hold -> seeker lock -> release -> ammunition consumed -> target killed; twice |
| aiarsenal:fpv7 | PASS | survival placement -> goggles link/camera -> actual Space takeoff -> F detonation -> automatic operator/camera/dummy restoration |
| aiarsenal:fpv10 | PASS | survival placement -> goggles link/camera -> actual Space takeoff -> F detonation -> automatic operator/camera/dummy restoration |
| aiarsenal:mq9 | PASS | survival placement -> tablet link -> actual Space takeoff -> production designation -> actual F twice/projectiles/impacts -> Backspace restore -> controller reconnect -> Backspace restore |
| aiarsenal:orion | PASS | survival placement -> tablet link -> actual Space takeoff -> production designation -> actual F twice/projectiles/impacts -> Backspace restore -> controller reconnect -> Backspace restore |
| aiarsenal:entrenching_tool | PASS | production two-point tool interactions -> five actual dug cells and duckboard floors -> durability loss |
| aiarsenal:arming_plug | PASS | survival RDS-4 item placement -> production arming plug interaction -> armed -> disarmed |
| aiarsenal:remote_detonator | PASS | survival IED placement -> production sneak-link -> actual arming delay -> real RMB remote trigger -> completed destructive blast |

## Separate checks
* Save/reopen: {"status": "PASS", "archivedItems": 448}
* Recipe-context checks: {"status": "PASS", "cases": 1271, "ingredientItems": 58}
* Recipes test loaded ingredient grids, matching, assembly and remainder sizes; they do not prove use of the crafted output.
* Craft cases test primary-weapon fire, service-kit consumption/rearm and repeat fire, not every alternate slot or flight mode.
* Drone cases distinguish real client input from server-side placement/link/designation fixtures.
* Launchpad cases retain references to every missile/warhead; unloading is not mistaken for successful impact.
* Screenshots are original Minecraft F2 captures, not fabricated gameplay images.
