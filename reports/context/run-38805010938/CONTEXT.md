# Contextual Minecraft action audit

**Process outcome: FAIL**
Recorded cases: 35/35; PASS 15; FAIL 20; RUNNING 0.

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
| aiarsenal:missile_icbm_mirv | FAIL | AssertionError('context action timed out') |
| aiarsenal:missile_icbm_mirv_heavy | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:ah64_vehicle | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:bf109_plane | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:bismarck_ship | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:cb90_boat | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:he111_plane | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:ka52_vehicle | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:pe8_plane | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:raptor_boat | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:su57_plane | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:sub636_vehicle | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:yak3_plane | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:cannon_fr6 | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:cannon_ri12 | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:javelin | FAIL | AssertionError('context action timed out') |
| aiarsenal:fpv7 | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:fpv10 | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:mq9 | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
| aiarsenal:orion | FAIL | JSONDecodeError('Expecting value: line 1 column 1 (char 0)') |
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

## Process failure

AssertionError('one or more contextual cases failed')
