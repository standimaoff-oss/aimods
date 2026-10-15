# First contextual run: FAIL (do not publish this QA binary)

Source `ea2428fd0e8030c061306c09ccbde992cb5ecd99`; CI https://github.com/standimaoff-oss/aimods/actions/runs/38805010938.

* Build and all **174** existing required GameTests passed.
* **15/35 contextual cases PASS, 20 FAIL.** The entire process/workflow is FAIL.
* **430 distinct loaded crafting recipes / 1,271 ingredient-grid cases / 58 mod ingredient IDs** passed matches, assembly/result and remaining-grid checks. Not use of every crafted output.
* Both JVMs restarted; all **448** archived items reopened correctly.
* The installed diagnostic JAR has SHA256 `f1872867a0c0e0b3653ec7bff91db71b8f9a1a212b99c25e97e2cccd07587c09`. It is **not** the public alpha.10 binary and is not published as a replacement.

## Product findings

1. **Stranded ICBM MIRV child.** Parent separated into eight children. Seven completed impacts; child `aaa78ad6-148d-4a93-913a-7aeca897aec7` stayed at age 151, x=3023.52157, y=102.35748 until the 360-second timeout. Observed 9 entities, 8 removed, only 7 completed blast jobs. The reference-based check correctly refused to treat this as a completed impact. The next heavy-MIRV preparation was blocked by the still-live projectile.
2. **Cluster payload mismatch.** `missile_cruise_cluster` produced **50** completed blast tasks although its type declares **48** submunitions. The initial generic completion predicate marked its row PASS; that does not validate the payload count. `clusterTick` released one charge on each of 50 hidden ticks. Candidate fix distributes exactly the declared payload over the 45-tick release window and adds a regression test. Future acceptance requires exactly 48 completed tasks.

## Harness findings (not claimed as broken vehicles/drones)

* Brigadier `StringArgumentType.word()` rejects `:`. All 11 craft, both powder cannons and all four drone preparations received `Expected whitespace ... aiarsenal:<id>`. No functional verdict can be inferred about these items. Changed the terminal diagnostic arguments to `greedyString()` with registry validation.
* Javelin reached Lock=100 and consumed one missile. Its death check used `execute unless entity ... run say ...`; `say` does not return that broadcast as an RCON command result. Replaced this with a standalone executable condition. This run alone does not establish a weapon failure or target kill.
* A failed missile case now records explicit cleanup **after marking failure**, preventing a stranded projectile from blocking unrelated subsequent cases. Cleanup never changes a failed row into PASS.

## Visual review

Viewed three original F2s: ICBM-MIRV launch, cruise-cluster impact, entrenching tool. The launcher and trench are visible. The distant spectator impact view is mostly sky (camera/render distance), **not acceptable visual proof of crater/effect appearance**. The next harness moves the camera closer only after destructive jobs finish. Physics evidence above is server-side and independent of those poor impact frames.

No new Windows/NVIDIA native-crash reproduction was obtained. The attached user launcher file is identical to the previous attachment.
