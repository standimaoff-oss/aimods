# Contextual Minecraft action audit

**Process outcome: RUNNING**
Recorded cases: 8/35; PASS 7; FAIL 0; RUNNING 1.

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
| aiarsenal:missile_operational_penetrator | RUNNING | incomplete |

## Separate checks
* Save/reopen: {"status": "NOT_RUN"}
* Recipe-context checks: {}
* Recipes test loaded ingredient grids, matching, assembly and remainder sizes; they do not prove use of the crafted output.
* Craft cases test primary-weapon fire, service-kit consumption/rearm and repeat fire, not every alternate slot or flight mode.
* Drone cases distinguish real client input from server-side placement/link/designation fixtures.
* Launchpad cases retain references to every missile/warhead; unloading is not mistaken for successful impact.
* Screenshots are original Minecraft F2 captures, not fabricated gameplay images.
