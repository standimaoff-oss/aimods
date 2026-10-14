# aimods — AI Arsenal (Forge 1.20.1)

Мод `aiarsenal`: техника, авиация, ракеты, стрелковое оружие (АК-12, M4A1, РПГ-7В2, ORSIS T-5000, ПКП «Печенег») и т.д.

- `mods/aiarsenal/` — исходники мода (Forge 47.4.23, Java 17). Сборка: `cd mods/aiarsenal && ./gradlew build`
- `mods/aiarsenal/src/main/resources/` — ресурсы (GLB-модели, текстуры, звуки, json)
- `tools/` — скрипты Blender (`tools/blender/*.py` — все модели), генераторы звуков/данных, сборка и тесты
- `notes/` — планы и ТЗ, `reports/aiarsenal.md` — отчёт по всем изменениям

## Обновление армий (2026-10-14)

Работа идёт по частям: [план этапов и критерии проверки](notes/stage1/PLAN.md).
Текущая версия `1.0.1-alpha.1` — подэтап **1а: исправление барабана ППШ**, а не
весь запрошенный набор оружия/дыма/эпох. Ракеты и промышленность ещё не удалены.
[Аудит исходного JAR дыма](notes/stage1/VOLPYRO.md).

Сборка из любого расположения checkout: `bash tools/build.sh` (Java 17 на PATH
или через `JAVA_HOME`). Minecraft/Gradle caches остаются в `~/.cache/mc/`.

Проверки подэтапа:
- Blender 4.2 LTS: `blender -b --python tools/blender/weapons_r22.py -- --only-ppsh`.
  Обновляет только два GLB и сохраняет `models/ppsh41.blend` с встроенными текстурами.
- `python tools/check_ppsh.py` проверяет ориентацию обоих барабанов, реальные PNG,
  UV, узлы крепления и наличие анимаций в экспортированных GLB.
- `.github/workflows/stage1-verify.yml` собирает Forge-мод и запускает настоящий
  Minecraft: GameTests и отдельный userdev-клиент под Xvfb/llvmpipe.
  Артефакт `stage1-evidence` содержит JAR, GLB, .blend, логи и F2-снимки, если
  клиентский прогон успешно дошёл до них. Отсутствие снимков не заменяется макетами.
