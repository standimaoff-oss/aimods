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

## First real run: 38755279826 (source 03c5cbb)
- Live Blender/MCP, all static checks, build, **167 GameTests**, installed saved-world migration PASS.
- Actual client harness failed at the first musket because it pressed Escape **after** closing menus via `view_first`, reopening the pause screen. Server correctly did not fire through the menu. F2 inspected: explicitly a failure, not accepted gameplay evidence.
- Inspected all 8 genuine Blender viewports: recognizable wooden flintlocks, spoked artillery and brass-hilt blades. Corrected blade curvature, cannon trunnion seats, inventory-scale cannons, ammo size differentiation and HUD translations.
- Inspected stage3 sprint F2: pistol completely outside bottom edge. Reduced sprint drop/angles and added bounded-transform regression; final real-motion verification remains required.
- Next run checks new content first, then restores only the disposable bomb-test fixture and executes all prior regression suites.

- After inspecting the first real smoke frames, replaced the custom profiles' use of the donor's vertical chimney field with an original type-11 ellipsoidal lobe field and a separate pale-powder/engine/dust/blast palette. Nuclear branches and original shader resource bytes unchanged. This extension must pass the real GLSL compile/fallback/reload gates, not just text checks.

## Real run 38759375857 (46a6870)
- Build, all 167 GameTests, migration PASS. All four flintlocks fired and reloaded using actual mouse/R inputs, both cannons loaded for 160 server ticks and fired actual roundshot. All six continuous weapon videos passed native-channel audio checks.
- Inspected real F2: custom pale powder volume visible at cannon muzzle, firearms/grips and reloads rendered. Corrected low sabre first-person framing and changed roundshot from the oversized default item billboard to its actual GLB. Whole-carriage recoil replaces an anachronistic sliding barrel.
- Full suite stopped because `bomb` is deliberately `noSummon`; no bomb was spawned. Replaced faulty fixture with an actual RPG-7 shot into the wall, **not** a manually injected effect. Added live-target damage assertions for all four flintlocks and explicit loading of the disposable bomber-test chunks.
- Rejected run's empty blast screenshots/video are NOT evidence of a successful explosion test.

## Regression caught before release: 54db735
The recoil edit accidentally joined the load-reset statements onto a `//` comment.
The existing one-ball-per-charge GameTest correctly failed. Restored the explicit
LOAD=-1 and RECOIL=10 statements; no test assertion was weakened.

## Runtime review of 38764280939 — rejected, not published
- Build, 26 Python checks, 167 GameTests and saved-world migration passed. All four flintlocks damaged live husks; both cannons loaded/fired and the RPG produced an actual destructive impact with original smoke. Those seven recordings passed native audio gates.
- Remote WALK sampled a zero-displacement interpolation tick as IDLE. Added an eight-tick displacement window for remote players only, with a GameTest for packet gaps, slow walking, stopping and teleport reset; no forced animation state or relaxed expected state.
- TT-33 sprint still showed only a sliver in the F2 frame. Raised the sprint pose and changed its pitch upward rather than just reducing the previous downward angle.
- Both bomber screenshots were invalid: vanilla summon applied position after NBT initialized the separate flight state at the origin, so the aircraft fell and crashed. Replaced that fixture with the existing `/tubombers spawn` item-placement initialization and added live health/engine/destroyed-state checks before capture and an existence check afterward. No physics or damage bypass.
- The two crash recordings and the burst-fired walking PPSh recording clipped. Bomber crash recordings must be replaced, not normalized. Added PPSh sound-definition headroom for eight coincident packet-delivered voices at full master volume, preserving audible range, with a source-mix test. Native recording/audio thresholds are unchanged.
- New run must pass the entire suite and visual review before publication. The prior stage4-gameplay.json alone was insufficient evidence of live engines; the missing aircraft in actual F2 captures rejected it.

- F2 powder-shot captures also exposed a capture race: the server had consumed the cartridge while F2 still saved the preceding ADS framebuffer. Await the actual client powder-emitter receipt and one second of rendering before F2; retain continuous unedited video.

## Accepted runtime and visual review — 38770590840
Source db0e1cf, evidence 66f5806: full CI SUCCESS, 27 Python tests, 168 GameTests, migration, 25 local/remote motion observations, 212 F2 and 17 native-audio MP4s. Reviewed genuine powder discharge, both armies' weapons/cannons, live bombers, visible TT-33 sprint, scopes, remote grips, locomotion, eight MCP viewports and 24 reload source frames. Audio gates unchanged and all passed. ABBA does not establish a meaningful GPU/FPS speedup; exact measured values and limitations recorded in reports/stage4/README.md. Public alpha.6 retained.
