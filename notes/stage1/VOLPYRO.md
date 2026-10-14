# Аудит дыма VolPyro — перед переносом (F3 ещё не выполнен)

Источник: `volpyro-1.5.6-nuclear (1).jar`, 217351 байт.
SHA-256: `48a015439cf4ac955cd0aec65ecfef488a09381246e17bb9ea6a687160d1bd3c`.
Вторая копия лежит в `mods/aiarsenal/`. В `META-INF/mods.toml` заявлена MIT,
авторы — VolPyro Contributors. При переносе сохранить атрибуцию; отдельного LICENSE
в архиве не найдено. Не подключать JAR целиком: он также регистрирует ракеты,
блоки, рецепты и ядерные боеприпасы, которые не нужны вторым дубликатом.

## Что находится внутри (проверено ZIP-инвентаризацией)
- `client/render/VolumeGlRenderer.class` — рендерер.
- `client/sim/VolumeInstance.class`, `VolumetricFxManager.class`, вложенный `RocketTrack` — симуляция/эмиттеры.
- `sim/ObstacleVoxelCache.class` — учёт окружения.
- `client/ClientForgeEvents.class`, `ClientPacketHandlers.class`, `ClientSetup.class` — точки подключения.
- `client/NukeClientFx.class`, `WarheadClientFx.class` — обработчики эффектов.
- `config/VolPyroClientConfig.class` и `QualityPreset` — настройки качества.
- Четыре GLSL 150 файла в `assets/volpyro/shaders/core/`:
  `volumetric_raymarch.fsh` (32321 байт), `volumetric_raymarch.vsh` (137),
  `volumetric_composite.fsh` (1114), `volumetric_composite.vsh` (137).

Это **не пакет текстур дыма**. Raymarch принимает `uDepthTex`, `uVolumeDataTex`,
`uVolumeCount`, `uStepCount`, базис камеры, параметры перспективы и освещения.
Composite смешивает текстуру объёма с учётом глубины. Извлечь только шейдеры
и переименовать PNG существующих частиц недостаточно.

## Покрытие существующих эффектов, которое нельзя забыть
- `realwar/client/fx/{TrailFx,ConvFx,NukeFx,ClientBlastManager}` и `particle/FxSystem`.
- `arsenal/client/NukeFx` — отдельная система, не только realwar.
- `bm21grad/client/ClientFx`, `BigPuffParticle`.
- `tubombers/client/ClientFx`, `BigPuffParticle`.
- Оружие (`GunFxPacket`), эффекты повреждений, `SmokeScreen`, дым авиации/кораблей.

## Порядок переноса
1. Декомпилировать нужные клиентские классы; сопоставить обфусцированные вызовы с Forge 1.20.1 mappings.
2. Перенести рендерер/симуляцию/шейдеры как собственный клиентский модуль, без регистраций VolPyro.
3. Сохранить существующие серверные расчёты урона, радиации и сетевые контракты;
   заменить только создание визуальных объёмов.
4. Подключить все перечисленные источники эффектов. Для выводимых из игры ракет
   сохранить обработку оставшихся сущностей на время миграции старых миров.
5. Очистка при смене мира; освобождение FBO/текстур; resize; восстановление GL state;
   клиентские классы никогда не должны загружаться выделенным сервером.
6. Лимиты объёмов/шагов и профили качества. Проверить llvmpipe, не обещать FPS заранее.
7. Реальные F2: выстрел, обычный взрыв, дымовая завеса, ядерный гриб в нескольких фазах;
   убедиться, что старый дым не рисуется поверх нового. Проверить ошибку компиляции
   шейдера и безопасный fallback; выход/повторный вход в мир.

Статус: архив изучен, перенос в исполняемый мод **не начат**. Эта запись не является
доказательством замены дыма или визуальной приёмки.
