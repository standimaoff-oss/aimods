# Alpha.11 candidate — not yet accepted

Product source: `fab71763b0de636c6ca4ed1d5dc76068eb709828`.

The first contextual installed-client run (`38805010938`) found a stranded ICBM MIRV child and a 50-versus-48 cluster-payload mismatch. See its retained FAIL report and raw evidence under `reports/context/run-38805010938/`.

Candidate fixes:

* Missile movement now prewarms a **bounded**, continuous chunk-ticket corridor instead of two disconnected current/far-ahead tickets. New parent/child entities acquire tickets before being published. At most 13 centres per update, 192-block lookahead, temporary 60-tick tickets; no persistent forced chunks or synchronous generation added to the flight tick.
* Cluster release distributes exactly the declared payload across 45 release ticks; late hidden ticks cannot create extra charges.
* Two new GameTests check exact cluster scheduling and completion of all eight ICBM MIRV children away from player/forced test chunks.
* Harness namespace parsing, Javelin's RCON condition acknowledgement, failed-case isolation and crater camera framing are corrected. These are not claimed as product crashes.

Verification gates in progress:

1. `38809035391`: build, 176 required GameTests, 35 contextual actions, 430 ordinary crafting recipes/ingredient variants, save/reopen. No PASS claimed until evidence arrives.
2. `38809035429`: same candidate through installed Oculus/Embeddium/Photon, qualified llvmpipe preset only.
3. Full registry catalogue regression is requested again through the existing `[catalogue]` push trigger: all 448 smoke checks, item-specific actions, firearm reload/fire cycles, 14 real free-fall detonations, world reopen. GitHub workflow-dispatch returned 500 then 403 (integration permission); normal repository push automation remains available.

These findings do not establish the cause or resolution of the user's Windows `nvoglv64.dll` crash. The supplied launcher log is unchanged; the matching `hs_err_pid27388.log` remains missing. Do not replace the public alpha.10 asset with a same-name diagnostic binary. Alpha.11 must be a separately identified, reviewed binary.
