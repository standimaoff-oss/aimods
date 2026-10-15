# Installed catalogue PASS; complete workflow FAIL

Workflow: https://github.com/standimaoff-oss/aimods/actions/runs/38813736418
Source: `3703e1f39206378afab75f893ca4240c73fce059`.
Installed alpha.11 SHA256: `19d26960e4aba5037a170919fd78f3ef40bf8bbc5b3291420c692242cf16245b` (same bytes as contextual 35/35 and Photon PASS).

* 448/448 generic inventory/use checks.
* 288 item-specific results: 132 equipment, 111 placement, 21 firearm/reload, 18 vehicle primary fire/reload/repeat, 4 consumption, 2 melee.
* 14/14 freefall-bomb destruction scenarios; every living witness has final HP 0. AN602 changes 453,125 RealWar-counted blocks. TuBombers uses a separate explosion algorithm/counter; its zero RealWar task count is not absence of detonation.
* All 448 archived stacks survive both JVMs stopping and world reopen.
* No ERROR/FATAL lines in the installed server log.

The 160 baseline contextual rows remain NOT_VERIFIED here; consult the separate 35 action cases and recipe-context results rather than inferring blanket acceptance. This run's screenshots were retained but not individually re-reviewed; the same-byte Photon/context originals have separate visual review reports and qualifications.

176/177 GameTests passed, with the off-player MIRV test failing. Therefore the workflow is FAIL and this binary is not released. Later readiness-barrier and test-clock fixes are not covered by these results.

Large logs were backed up before lossless compression; see `compressed-logs.json` for original byte sizes/hashes and `ci-result.json` for the workflow conclusion.
