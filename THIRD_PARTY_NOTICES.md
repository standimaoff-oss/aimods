# VolPyro volumetric effects

The files under `ru/aiforge/arsenal/volumetric/` and
`assets/aiarsenal/shaders/volpyro/` are adapted from the user-supplied
`volpyro-1.5.6-nuclear (1).jar`, version 1.5.6, authors **VolPyro Contributors**.
Its `META-INF/mods.toml` declares the **MIT** license. No separate copyright or
license-text entry was present in the supplied archive. The existing authorship
and license declaration are preserved here; no ownership of the donor work is claimed.

SHA-256 of donor JAR:
`48a015439cf4ac955cd0aec65ecfef488a09381246e17bb9ea6a687160d1bd3c`.

Port changes: namespace/Forge mappings, resource lifecycle and OpenGL state safety,
bounded caches/queues and effect priorities, adapters to AI Arsenal's existing
visual events. Donor items, blocks, recipes, entities and server damage logic are
NOT imported. Shader sources are extracted byte-for-byte from the supplied JAR.

Decompiled, remapped reference text is retained under
`notes/stage1/volpyro-reference/` for comparison, not compiled into the mod.
