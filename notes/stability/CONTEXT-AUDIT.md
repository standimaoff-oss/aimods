# Second-phase contextual audit

Requested after public alpha.10: use every item, reload/fire repeatedly, explode every bomb and investigate frequent crashes.

## Baseline, not new results

Public alpha.10 is still the tested binary from source `5c6ef4b`, SHA256 `8eaef8fff814804a5fcaf389a6d91235f702802647ca4bba005a8b1a72ac421b`. Its catalogue run `38798168570` passed 448 generic checks, 288 item-specific checks, 14 free-fall detonations and save/reopen. This did **not** close 160 contextual positions or every alternate mode.

The reattached launcher log was compared byte-for-byte with the previous private copy: identical. It reports the same native NVIDIA crash at 18:14:20 / PID 27388. It does not identify a new crash of alpha.10. No private launcher log is committed. The corresponding `hs_err_pid27388.log` is still needed for native-stack diagnosis.

Backup before changes: `/home/user/backups/context-audit-20261015/source.tar.gz` and private launcher copy.

## New executable scope (results come only from CI evidence)

* All 14 `MissileType` entries: survival placement of the correct pad, ammunition consumption, real loading delay, launch, trajectory, all MIRV children, destructive jobs completed with changed blocks. References to entities survive unload; unload cannot satisfy completion.
* Every runtime `CraftItem` (11): survival item placement, boarding, real H engine command, real LMB primary discharge with projectile/bullet evidence, service-kit interaction and consumption, repeat discharge. Other slots, full navigation/flight and defensive AI remain separate.
* Both powder cannons: item placement, correct national charge, production loading timer, flint-and-steel ignition/durability and actual cannonball creation; twice.
* Javelin: actual RMB seeker lock/release, ammunition consumption and destroyed targets; twice.
* FPV7/10: placed item, goggles linking/session camera, real Space takeoff, real F detonation, restoration of player mode/position/camera and dummy removal.
* MQ-9/Orion: placement/tablet link, real Space takeoff, production designation, real F twice with projectile/impact checks, real Backspace exit, controller reconnect and second exit. Full RTB/landing and rearming are not claimed.
* Entrenching tool: actual two-point plan, excavation/duckboards and durability. Arming plug: placed RDS-4 armed then disarmed. Remote detonator: placed IED, link, arming delay and real RMB destructive detonation.
* Every loaded ordinary mod crafting recipe and each mod ingredient/tag alternative: actual `RecipeManager` matching, assembly, result and remaining-grid checks. This is recipe-context evidence, **not** firing/using the crafted output or GUI crafting.
* Both installed JVMs stopped, world reopened, real client rejoined, all 448 archived item IDs verified again. Fatal render/server/save/blast errors fail the whole run.

All added Java diagnostic commands are gated by `-Daiarsenal.stressQa=true` and operator permission. They are not registered during normal play. No timer, ammunition, seeker lock or projectile progress is overwritten by these fixtures.

## Gates

No new public release or assertion that all 448 items are fully functional until actual results have been reviewed. Individual green rows cannot hide a failed process or CI workflow. Linux llvmpipe does not certify Windows/NVIDIA/Oculus. Existing published JAR is not silently replaced by a different QA build with the same version.
