# Photon regression on candidate 3703e1f — PASS, limited platform scope

Workflow: https://github.com/standimaoff-oss/aimods/actions/runs/38813736609

Installed alpha.11 SHA256: `19d26960e4aba5037a170919fd78f3ef40bf8bbc5b3291420c692242cf16245b`.

Forge 47.4.23, Oculus 1.8.0, Embeddium 0.3.31, Photon 1.3b. Real R reload and ADS for PPSh-41, Mosin PU and musket 1777; ordinary/nuclear/legacy-nuclear fallback visual packets; two shader-pack disable/re-enable cycles. The raw renderer frame counters remain 14→14 and 27→27 while the pack is active. Hostile unpack-state regression also completed (see driver log).

11 original F2 captures saved. Four reviewed individually: Mosin PU ADS (circular mask/reticle visible), musket ADS (weapon and HUD visible), ordinary fallback blast (dark smoke), legacy nuclear fallback (large bright effect, terrain/HUD retained). These are visual-path checks, not explosive damage tests or FPS certification.

**Linux llvmpipe only**, with Photon `SH_SKYLIGHT=false` to accommodate the software renderer's shared-memory limit. Does not establish default-Photon-preset compatibility, a Windows/NVIDIA crash fix, or acceptance of gameplay. The same-source contextual and catalogue GameTest gates failed; no release is authorized by this isolated PASS.

Large logs were backed up before lossless gzip compression; `compressed-logs.json` records original SHA256 and sizes. `ci-result.json` records the completed workflow result.
