# Second contextual run: FAIL — 32/35 actions passed

Source `fab71763b0de636c6ca4ed1d5dc76068eb709828`; installed candidate SHA256 `3282ee75984dd023934a91c23d70cf456bf713c7bbb96accee95d7d574893359`. Workflow https://github.com/standimaoff-oss/aimods/actions/runs/38809035391.

Passed: 13 missile types; all 11 craft primary fire/service/repeat cycles; both powder cannons twice; Javelin twice; FPV7 flight/detonation/restore; MQ-9 flight/two strikes/restore/reconnect; all three tool scenarios. All 430 ordinary recipes / 1,271 ingredient grids passed again, and all 448 archived items survived both-JVM restart/reopen.

## Confirmed improvements and remaining failures

* Cluster now completes **48**, not 50, blast tasks.
* Normal ICBM MIRV now completes all **8** impacts. Heavy MIRV still fails: **5/8** impacts; three children stop at age **105**, `present=false` but `removed=false`. Expanding the corridor alone did not solve lease renewal after an entity becomes non-ticking/hidden. A level-clock lease keeper is needed; no PASS is claimed for the heavy variant.
* Orion fires both weapons successfully and restores survival mode, camera and original position. But its operator dummy, unloaded during flight, **reappears after returning**. `restore()` only removes currently loaded dummies. This is a product defect, not a screenshot timeout.
* FPV10's session ends immediately while the drone remains alive/idle; takeoff never happens. The reason is not established by this run. Preparation is being separated from linking so entity tracking precedes camera control; real client camera acknowledgements and stop-reason diagnostics are added. Do not claim a fixed FPV10 until rechecked.

GameTests: **175/176 passed**; the new off-player MIRV regression fails with `MIRV parent did not separate`. The fixture also needs to keep an empty GameTest dimension awake (vanilla stops entity ticks after 300 empty ticks), without forcing the flight/target chunks. Its final verdict is pending rerun together with the level-clock lease correction.

## Visual review

Four originals reviewed: AH-64 craft, French cannon, MQ-9 reconnect, normal ICBM MIRV impact. The AH-64 HUD/engine state and cannon smoke are visible. The cannon is partly out of frame. The MQ-9 reconnect shot still shows the previous player view; server session success is **not** client-camera acceptance. The impact shot is mostly sky/smoke, not adequate crater framing. Next harness adds client READY/STOP acknowledgements and closer ground-level framing after destructive jobs finish.

The entire workflow remains FAIL. The separate Photon success for these bytes does not override these failures. No alpha.11 release is authorized from this run.
