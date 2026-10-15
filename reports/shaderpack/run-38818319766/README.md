# Photon regression — PASS (qualified platform scope)

Workflow: https://github.com/standimaoff-oss/aimods/actions/runs/38818319766
Source: `93af8c371117da14035d6fabf1225ecb9df34af5`.
Installed alpha.11 SHA256: `dd4f997426c06dcbf1579909650cc40ae6435d7ba4c5d6b8f569a8a929a8fa82`.

Forge 47.4.23 / Oculus 1.8.0 / Embeddium 0.3.31 / Photon 1.3b. Real R reload and ADS for PPSh-41, Mosin PU and musket 1777; ordinary, nuclear and legacy-nuclear fallback packets; two shader-pack disable/re-enable cycles. Raw-renderer counters stay 54→54 and 95→95 while the pack is active; the hostile unpack-state regression also completes (driver log).

11 original Minecraft F2 captures retained. Four reviewed individually: Mosin PU circular scope/reticle; PPSh ADS and loaded HUD; musket ADS and loaded HUD; ordinary fallback smoke. No full-frame black output in these reviewed frames. This is not a rendered-video FPS measurement or a new third-person grip review.

**Linux llvmpipe only**, with Photon `SH_SKYLIGHT=false` for the software renderer shared-memory limit. Default Photon preset and Windows/NVIDIA crash resolution are NOT certified. Visual-only explosion packets are not proof of physics/damage; use the separate destructive audit.

This workflow is PASS. Installed contextual/catalogue acceptance must also pass before publishing this candidate. Logs were backed up and losslessly compressed; original sizes/SHA256 are in `compressed-logs.json`, completed CI metadata in `ci-result.json`.
