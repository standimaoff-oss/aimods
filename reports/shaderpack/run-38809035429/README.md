# Alpha.11 candidate Photon compatibility — PASS, qualified environment only

CI: https://github.com/standimaoff-oss/aimods/actions/runs/38809035429 (SUCCESS).

Source `fab71763b0de636c6ca4ed1d5dc76068eb709828`; installed JAR `aiarsenal-1.0.1-alpha.11.jar`; SHA256 `3282ee75984dd023934a91c23d70cf456bf713c7bbb96accee95d7d574893359`.

Forge 47.4.23 / Oculus 1.8.0 / Embeddium 0.3.31 / Photon 1.3b, Linux llvmpipe. Photon sidecar `SH_SKYLIGHT=false` remains required for this software renderer's 32768-byte shared-memory limit. Default Photon preset and Windows/NVIDIA are **not certified**.

* Real R reload and firearm input: PPSh-41, Mosin PU and musket 1777. Oculus default bindings left unchanged.
* Mosin outside-scope black mask check passed.
* Blast/nuclear/legacy-nuclear fallback visual packets passed; these are **not** physical bomb tests.
* Two off/on cycles passed. While Photon was enabled, raw volumetric frame counts stayed 45→45 and 85→85; raw rendering resumed when disabled.
* Hostile unpack-state GL checks passed again after disabling the pack.
* Eleven original F2 captures; four manually reviewed: Mosin PU ADS, fallback blast, fallback nuke, disabled-0. Scope masking and visible smoke/fallback rendering are supported. Nuclear flash/close framing does not certify the entire mushroom shape.

This successful compatibility subset does not override the failed GameTest gate in the simultaneous contextual/catalogue runs. It is not by itself permission to publish the candidate.

Large raw logs were backed up before lossless gzip compression; original byte lengths and SHA256 are recorded in `compressed-logs.json`. Uncompressed originals also remain in the CI artifact and evidence commit `f815839`.
