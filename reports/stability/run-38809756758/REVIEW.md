# Catalogue regression — workflow FAIL, installed audit PASS

Workflow: https://github.com/standimaoff-oss/aimods/actions/runs/38809756758

The complete workflow failed its GameTest gate: `mirv_children_finish_outside_player_chunks` did not separate the parent missile (175/176 tests passed). This candidate is **not released**. See `ci-result.json` and the separate contextual failures in `reports/context/run-38809035391/REVIEW.md`.

Installed runtime nevertheless completed: 448 generic checks, 288 item-specific actions, 14/14 freefall-bomb destruction cases, and 448 archived items verified after both JVMs stopped and reopened the world. The 160 NOT_VERIFIED baseline rows are not silently reclassified: recipe checks and additional contextual scenarios are separate evidence, not universal item acceptance.

Installed SHA256 `3282ee75984dd023934a91c23d70cf456bf713c7bbb96accee95d7d574893359` matches the second contextual and successful Photon runs. This is the preceding candidate, **not** the new lease/orphan/session-ack changes in `3703e1f`.

Four original F2 images reviewed: C96 loaded (one-handed presentation, HUD 10 rounds), Mosin PU loaded (model/scope visible, HUD 5 rounds; this is not an ADS test), FAB5000 explosion (ordinary smoke plume visible), AN602 explosion (nuclear cloud visible against a darkened background; not proof of terrain rendering or performance). Screenshots supplement, rather than replace, the destructive counters in the JSON report. Other screenshots have not been individually reviewed in this pass.

Large raw logs were backed up before lossless gzip compression. `compressed-logs.json` lists original byte sizes and SHA256; decompress with `gzip -dk <file>.log.gz`. No evidence was discarded.
