# France + Russian Empire, 1812; original smoke emitters

Baseline 0572294; Java and gradle.properties backed up in `/home/user/backups/stage4` before edits.
Existing accepted alpha.6 remains the public version until alpha.8 completes all gates.
Specs: `notes/_tz/TZ-ai-forge-mod.md`, `TZ_MODEL_VIEW_PRO_v2.0.md`.

- Four flintlocks: French 1777/An IX musket, Russian infantry 1808, French An XIII pistol, Russian cavalry 1809.
- French briquet and Russian cavalry sabre; stylised rather than museum-accurate scans.
- French An XI 6-pounder / Russian 1805 12-pounder: load matching powder/roundshot charge, wait 8 s, ignite with flint and steel. Empty hand aligns yaw; sneak-use adjusts elevation. Solid roundshot is **not explosive**.
- Fast 8/6-second firearm reloads are gameplay pacing, not claims of historical drill speed.
- Genuine live Blender/MCP exports, packed textures and native .blend. No image substitutes for models or gameplay.
- Original powder, muzzle, engine and ordinary-explosion emitter layout, expansion and transport on the MIT donor volume renderer. Nuclear routines and all four donor shaders preserved. This is **not** a claim of an independently rewritten rendering engine.
- Engine exhaust on prop/jet/helicopter craft and both Tu bomber families; bomber anchors follow the original Blender nozzle dimensions and aircraft quaternion.
- Runtime: installed Forge 1.20.1/47.4.23/Java 17. Survival cartridge consumption, cannon loading/fire, actual falling-bomb impact, live bomber engines, F2 and real X11+PulseAudio recordings. Prior scope/uniform/multiplayer/motion/index regression gates retained.
- Stage3 run 38750364719 failed because ffmpeg could not read an occluded/unmapped X11 window (zero video frames), not a passing motion release. New recording maps, moves and raises the actual window and captures its visible screen rectangle. No fabricated frames or audio normalization.
- Static validation already passes donor-shader identity and resource recipes. Compilation, modelling and visual acceptance pending CI; do not publish merely on generation or build success.
