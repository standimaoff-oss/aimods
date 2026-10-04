# ТЗ: ИИ-разработчик модов на Minecraft 1.20.1 (Forge)

**Версия ТЗ:** 1.0
**Дата:** 2026-09-27
**Статус:** действует (обязательно к исполнению агентом)
**Целевая платформа:** Minecraft **1.20.1**, **Minecraft Forge 1.20.1-47.4.23**, модлоадер `javafml`, Java **17**
**Среда исполнения:** headless-сервер Debian 13, 2 vCPU, ~1.9 ГБ ОЗУ, 20 ГБ диска, без GPU/X11/Docker

---

## 0. Как читать документ

- **MUST** / **ДОЛЖЕН** — обязательно, нарушение = работа не принята.
- **SHOULD** / **СЛЕДУЕТ** — обязательно, кроме случаев, когда есть обоснованное отклонение, зафиксированное в отчёте.
- **MAY** / **МОЖЕТ** — по усмотрению агента.
- Каждый пункт из раздела 10 («Definition of Done») — это **гейт**: не пройден → мод не считается готовым, цикл идёт на следующий виток.

---

## 1. Назначение и цель

### 1.1 Цель
Создать воспроизводимый конвейер, в котором **ИИ-агент по текстовому заданию человека разрабатывает мод на Minecraft 1.20.1 Forge**: от карточки заказа → до собранного `.jar`, автотестов, RCON-проверок и скриншотов, по которым человек принимает решение «ок / чинить».

### 1.2 Что является результатом
На выходе по каждому заказу:

| Артефакт | Путь (от носителя воркспейса) | Обязательность |
|---|---|---|
| Исходники мода (Gradle-проект) | `mods/<modid>/` | MUST |
| Собранный мод | `mods/<modid>/build/libs/<modid>-<version>.jar` | MUST |
| Копия для прогона | `mods-to-test/<modid>-<version>.jar` | MUST |
| Скриншоты | `shots/<modid>/<iter>/NN-name.png` | MUST (для визуальных фич) |
| Логи сервера/клиента | `logs/<modid>-<iter>-{server,client}.log` | MUST |
| Отчёт агента | `reports/<modid>.md` | MUST |
| GameTest-тесты | `mods/<modid>/src/main/java/.../gametest/` + структуры | SHOULD |

### 1.3 Чего НЕ должно быть в воркспейсе (снапшот ≤ 128 МБ)
Рантайм Minecraft (Forge-сервер, клиент, `~/.minecraft`, библиотеки Maven, Gradle-кэш, декомпилированный MC) **MUST NOT** попадать в воркспейс. Весь рантайм живёт **только** в `/home/user/.cache/mc/` и пересоздаётся скриптами за 2–5 минут.

**Структура воркспейса (канон):**

```
/home/user/
├── TZ-ai-forge-mod.md          # этот документ
├── mods/                       # исходники (Gradle-проекты по одному на мод)
│   └── <modid>/
├── mods-to-test/               # jar'ы, которые идут на прогон (symlink/копия из build/libs)
├── tools/                      # ВСЕ скрипты окружения (контракты — раздел 7)
│   ├── setup_server.sh
│   ├── setup_client.sh
│   ├── rcon.py
│   ├── spawn.sh
│   ├── scene_day.sh
│   ├── screenshot.sh
│   └── start_novnc.sh
├── shots/<modid>/<iter>/
├── logs/
└── reports/
```

---

## 2. Окружение (факт, проверено замерами)

### 2.1 Ресурсы
| Параметр | Значение |
|---|---|
| ОС | Debian GNU/Linux 13 (trixie) |
| CPU | 2 ядра, без GPU (рендер — программный, Mesa **llvmpipe**) |
| ОЗУ | ~1.9 ГБ (Swap = 0) |
| Диск | 20 ГБ |
| Сеть | доступ к Mojang / Maven Forge / PyPI — открыт |
| `sudo` | без пароля |
| Java из коробки | **11** → для 1.20.1 MUST быть установлена **Java 17** (`openjdk-17-jdk-headless` + `openjdk-17-jre`) |
| ImageMagick | установлен (`import`, `identify`, `convert`) |
| Отсутствует | X-сервер (ставится Xvfb), Docker, аппаратный OpenGL |

### 2.2 Бюджеты, вытекающие из ресурсов
- **Память:** сервер — `-Xmx768M`, клиент — `-Xmx1024M`. **Одновременно** — только если свободно ≥ 1.9 ГБ; при OOM тестирование идёт **последовательно** (сначала сервер, клиент останавливается).
- **Клиент:** окно `800×600`, `renderDistance = 2`, `simulationDistance = 2`, graphics = Fast, clouds off, particles minimal, VSync off, FPS ~5–20 (достаточно для скриншотов).
- **Первый запуск клиента:** 5–15 минут (распаковка нативок, загрузка ассетов, генерация мира) — это норма, таймауты скриптов MUST это учитывать (ожидание готовности по маркеру в логе, а не по фиксированному sleep).
- **CPU:** только 2 ядра → мод MUST NOT создавать фоновые потоки, генераторы чанков, тяжелые планировщики и O(n²)-сканы в тике.

### 2.3 Рантайм
- Корень рантайма: **`/home/user/.cache/mc/`** (server/, client/, gradle-cache/, maven/).
- Скрипты MUST быть идемпотентными: если `/home/user/.cache/mc/server/` уже есть — не перекачивать заново, если нет — развернуть заново с нуля.

---

## 3. Роли конвейера

| Роль | Кто | Ответственность |
|---|---|---|
| **Заказчик** | человек | Формулирует заказ по шаблону (раздел 4), смотрит PNG, ставит «ок / чинить» |
| **Агент-разработчик** | ИИ | Проектирует, пишет код, собирает, устраняет замечания |
| **Агент-валидатор** | ИИ (тот же или второй проход) | Гоняет гейты раздела 10, НЕ редактирует код, только фиксирует факты |
| **Арбитр** | человек | Принимает решение по спорным фичам и по стопу цикла |

Разработчик и валидатор SHOULD быть разными проходами: написавший код не должен сам себе подписывать «зелёный» прогон без логов и PNG.

---

## 4. Входной контракт: карточка заказа на мод

Агент MUST требовать/формировать карточку такого вида. Если поле не заполнено — агент заполняет его разумным дефолтом и **фиксирует предположение** в отчёте (секция «Допущения»).

```yaml
modid: examplemod            # [a-z0-9_]{2,32}, уникальный, НЕ менять после релиза
display_name: Example Mod
version: 1.0.0               # semver
summary: >
  Добавляет медный телепортер и руду аметистовой стали.

features:
  - id: F1
    title: Блок «Медный телепортер»
    gameplay: Ставится, при клике правой кнопкой телепортирует игрока на 8 блоков вверх.
    acceptance:
      - "/give @p examplemod:copper_teleporter выдаёт предмет с корректным именем"
      - "Правый клик по блоку телепортирует игрока ровно на 8 блоков вверх, блок не ломается"
      - "Работает на выделенном сервере (без клиента)"
  - id: F2
    title: Руда аметистовой стали
    gameplay: Генерируется в мире y=-64..-16, везде (overworld), требует железную кирку.
    acceptance:
      - "В мире руда встречается; дроп — сырой аметист (не сам блок) при кирке без шелк-ткани"
      - "Выпадает лут из data/minecraft/loot_tables/blocks/... + своя таблица"

recipes:
  - output: examplemod:copper_teleporter
    shape: ["CBC", "BRB", "CBC"]   # C=copper_ingot, R=redstone, B=examplemod:amethyst_steel
    result_count: 1

worldgen:
  - type: ore
    block: examplemod:amethyst_steel_ore
    biomes: "*"
    y: [-64, -16]
    size: 8
    rarity: 6              # чем больше, тем реже

config:
  - key: teleportHeight
    type: int
    default: 8
    range: [1, 64]
    comment: "Высота телепорта"

assets:
  style: "16x16, пиксель-арт, палитра ванильного стиля"
  needs: [block textures, item textures, gui (если есть контейнер)]

localization: [en_us, ru_ru]

performance_budget:
  tick_ms_max: 1.0           # среднее время тика мода
  heap_extra_mb: 64
  jar_size_max_mb: 4
  assets_size_max_mb: 2

out_of_scope:
  - "Без измерений, без GUI-конфига, без интеграции с JEI"
```

**Правила формирования карточки (MUST для агента):**
1. Каждая фича получает **id** и **acceptance-критерии**, которые проверяемы командой/RCON/GameTest. Непроверяемое = не принято в работу (агент MUST переформулировать с заказчиком).
2. Фича обязана явно указывать сторону: `client` / `server` / `both`.
3. Объём мода ограничивается: ≤ 8 фич на итерацию, иначе разбивать на этапы (`v1.0.0` → `v1.1.0`).

---

## 5. Технические требования к моду

### 5.1 Каркас проекта
- Сборка: **Gradle** + **ForgeGradle 6.x** (MDK 1.20.1-47.4.23), **Java toolchain 17**.
- `gradle.properties`: `minecraft_version=1.20.1`, `forge_version=47.4.23`, `mod_id`, `mod_version`, `mod_group_id`.
- Маппинги: официальные + **SHOULD** Parchment `2023.09.03-1.20.1` (улучшает читаемость имён параметров).
- Агент MUST запускать сборку так, чтобы Gradle-кэш и `~/.gradle` не попадали в снапшот: `--project-cache-dir /home/user/.cache/mc/gradle --gradle-user-home /home/user/.cache/mc/gradle-home`.
- MUST собираться командой `./gradlew build` «с нуля» (clean checkout) без интерактивных шагов и без доступа к GUI.

### 5.2 `mods.toml` (обязательные поля)
```toml
modLoader = "javafml"
loaderVersion = "[47,)"
license = "<лицензия мода>"
issueTrackerURL = "<ссылка>"      # MAY быть "" , но поле MUST присутствовать

[[mods]]
modId = "examplemod"
version = "${file.jarVersion}"
displayName = "Example Mod"
authors = "AI Agent"
description = '''Краткое описание'''

[[dependencies.examplemod]]
    modId = "forge"
    mandatory = true
    versionRange = "[47,)"
    ordering = "NONE"
    side = "BOTH"

[[dependencies.examplemod]]
    modId = "minecraft"
    mandatory = true
    versionRange = "[1.20.1,1.21)"
    ordering = "NONE"
    side = "BOTH"
```
- `modId` MUST совпадать с константой `MODID` в коде и со всеми неймспейсами ресурсов.
- `version` — semver, MUST совпадать с `mod_version` в `gradle.properties`.
- `displayTest` / `side` указывать осознанно: если мод чисто серверный — `side = "SERVER"` (тогда клиент без мода сможет зайти), если чисто клиентский — `CLIENT`.

### 5.3 Точка входа и регистрация
- Один класс `@...Mod(MODID)`, конструктор без тяжёлой логики (только регистрация и подписки).
- Регистрация — **только** через `DeferredRegister`:
  ```java
  public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(MODID);
  public static final DeferredRegister.Items ITEMS   = DeferredRegister.createItems(MODID);
  public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
      DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, MODID);
  // типы возврата: DeferredHolder<T, ? extends T> (предпочтительно) или RegistryObject<T>
  ```
- Шины: `FMLJavaModLoadingContext.get().getModEventBus()` — для `*Setup`/`Register*Event`; `MinecraftForge.EVENT_BUS` — для игровых событий. Игровые слушатели — отдельные классы с `@EventBusSubscriber(modid = MODID)`, для клиентских — `value = Dist.CLIENT`.
- Регистрация `CreativeModeTab` — собственная вкладка (SHOULD) или аккуратное добавление в ванильную (MAY, но не в `BUILDING_BLOCKS` без нужды).
- Все регистрации MUST происходить **до** `FMLCommonSetupEvent` завершения; порядок инициализации не должен зависеть от других модов.

### 5.4 Безопасность сторон (сторона — главный источник крашей)
- В общем (common) коде **ЗАПРЕЩЕНО**: `Minecraft.getInstance()`, `net.minecraft.client.*`, обращения к `LocalPlayer`, `ClientLevel`, рендер- и GUI-классам.
- Клиентские обработчики — только через `DistExecutor.unsafeRunWhenOn(Dist.CLIENT, ...)` или `@Mod.EventBusSubscriber(value = Dist.CLIENT, bus = Bus.MOD)`.
- `@OnlyIn(Dist.CLIENT)` — допустимо, но агент SHOULD предпочитать изоляцию в отдельном классе; MUST убедиться, что класс не грузится на сервере.
- **Гейт:** мод обязан стартовать на **выделенном сервере** headless (см. 6.1). Любой `NoClassDefFoundError: net/minecraft/client/...` = работа не принята.

### 5.5 Контент и данные (data generation вместо ручного JSON)
- MUST использоваться `GatherDataEvent` → `runData`:
  - рецепты (`RecipeProvider`, `ShapedRecipeBuilder`, `ShapelessRecipeBuilder`, `SimpleCookingRecipeBuilder`),
  - лутаблицы (блоки + `chests` при необходимости, с сохранением ванильных дропов),
  - теги (`ItemTagsProvider`, `BlockTagsProvider`, `minecraft:mineable/pickaxe`, `needs_iron_tool`, `forge:ores/...`),
  - `BlockStateProvider` / `ItemModelProvider`,
  - `LanguageProvider` — **обязательно** `en_us` **и** `ru_ru`.
- Рукописный JSON в `src/main/resources` допускается только для того, что не генерируется; MUST быть валидным и покрытым `runData`.
- Ворлдген: `BiomeLoadingEvent` (SHOULD, совместимо с модами биомов) или `Feature`+`ConfiguredFeature`+`PlacedFeature` через `RegistryObject`. Для удаления ванильной руды и настройки — через теги/конфиг, а не хардкод.
- Теги (`data/minecraft/tags/...`, `data/forge/tags/...`) MUST быть заполнены: без `mineable/*` блоки не ломаются, без `needs_*_tool` — ломаются рукой.

### 5.6 Сеть, конфиг, команды
- Сеть: один `SimpleChannel` на мод (`NetworkRegistry.newSimpleChannel`), версия протокола — строковая константа, инкрементируется при смене формата. Каждый пакет MUST быть зарегистрирован с `handler` на нужной стороне и MUST проверять `LogicalSide` в `NetworkEvent.Context`.
- Конфиг: `ForgeConfigSpec` в `ModLoadingContext.get().registerConfig(COMMON|CLIENT|SERVER, ...)`. Все ключи MUST иметь: дефолт, диапазон/валидатор, комментарий, и MUST быть перечислены в карточке заказа (раздел 4).
- Команды: `RegisterCommandsEvent`, `Commands.literal(...)`, `Commands.argument(...)`, всё через ` Brigadier` без блокирующего IO. Команды MUST быть безопасными при вызове с RCON (без `getPlayerOrException` там, где возможен вызов с консоли).
- **Требование тестируемости:** каждая фича из карточки SHOULD быть вызываема/проверяема командой или GameTest — иначе её нельзя прогнать по RCON-циклу.

### 5.7 Производительность и ресурсы (жёстко, 2 ядра)
| Ограничение | Значение | Проверка |
|---|---|---|
| Jar мода | ≤ 4 МБ | `stat -c%s` |
| Ассеты (текстуры/модели) | ≤ 2 МБ суммарно | `du -sh` |
| Текстуры | 16×16 (SHOULD) / 32×32 (макс), PNG, без альфа-канала вне нужды | ImageMagick `identify` |
| Доп. heap | ≤ 64 МБ | замер `-Xmx` до/после |
| Средний тик логики мода | ≤ 1 мс | `/forge tps` + `spark`-free замер логами (MAY — профиль вручную) |
| Фоновые потоки | 0 (кроме I/O конфигов) | ревью кода |
| Загрузка сервера с модом | ≤ 120 с до «Done» | тайминг в логе |
| Обращения в сеть в рантайме | 0 | ревью + grep |

- MUST NOT: шейдеры, OptiFine-зависимости, нативные библиотеки, рефлексия в ванильные классы без крайней нужды, `Mixin` без обоснования, AnyStruct/Lua-подобные встраиваемые движки, поблочные тики там, где хватает `BlockEntity` с throttling.
- `TickEvent` / `getTick` MUST быть O(1) на элемент и с кэшированием; обходы — по предвычисленным спискам/кэшам, не по всему миру.

### 5.8 Логирование и диагностика
- `LogUtils.getLogger()` / `LogManager.getLogger(MODID)`; `System.out.println` — ЗАПРЕЩЕН.
- Уровни: старт/стоп — INFO, детали — DEBUG, ошибки — ERROR с контекстом (координаты, тип, игрок).
- В логе MUST NOT быть `printStackTrace()` без логгера и «говорящих» сырых стеков в чат игроку.

### 5.9 Локализация и UX
- Все строки — через `Component.translatable("key.<modid>.…")`; ни одной «захардкоженной» строки в UI/чате.
- Ключи: `item.<modid>.<name>`, `block.<modid>.<name>`, `death.attack.<modid>.<name>`, `message.<modid>.…` — по конвенциям ванили.
- `en_us` и `ru_ru` MUST быть полными: отсутствие ключа = в логе `Missing translation` = гейт не пройден.

### 5.10 Совместимость и обратная совместимость
- Мод MUST работать в одиночку (без JEI, без других модов) — проверка на чистом Forge-сервере.
- Изменение `modid`, неймспейсов, id предметов/блоков после первой приёмки — **ЗАПРЕЩЕНО** без миграции (`missing-mappings` через `RegistryEvent`/`MissingMappingsEvent`).
- Если фича требует опционального мода (JEI и т.п.) — зависимость MUST быть `mandatory = false` и код MUST деградировать без него.

---

## 6. Способы запуска и тестирования (все MUST быть доступны)

### 6.1 Forge Dedicated Server (основной, дешёвый) — `tools/setup_server.sh`
**Что делает скрипт (контракт):**
1. `sudo apt-get update && sudo apt-get install -y openjdk-17-jdk-headless` (идемпотентно);
2. создаёт `/home/user/.cache/mc/server/`;
3. скачивает `https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.23/forge-1.20.1-47.4.23-installer.jar` (fallback: `-universal.jar`), выполняет `--installServer`;
4. пишет `eula=true`, `online-mode=false`, `enable-rcon=true`, `rcon.password=...`, `rcon.port=25575`, `level-type=minecraft:flat` (для предсказуемости) / `default`, `view-distance=2`, `simulation-distance=2`, `max-players=5`, `spawn-protection=0`;
5. запускает с `-Xmx768M -Xms512M`, логи в `/home/user/.cache/mc/server/logs/latest.log`, symlink в `logs/`.

**Ключи:** `setup_server.sh {install|start|stop|restart|status}` — `status` возвращает exit 0, если процесс жив.

**Проверки:**
- `forge mods list` (через RCON или по логу) содержит `<modid>@<version>`;
- `grep -Ei 'error|exception|failed|caught|mixin apply|missing texture|model loading' logs/…-server.log` → пусто (белый список — раздел 10.4);
- `crash-reports/` — пуста (`ls -A | wc -l` = 0);
- `latest.log` содержит `Done (…)! For help, type "help"`.

### 6.2 GameTest Framework (настоящие автотесты)
- Тесты в `src/main/java/<pkg>/gametest/`, структуры — `src/main/resources/data/<modid>/structures/*.nbt` (создаются через Structure Block в клиенте **или** программно через фабрики пустых структур; SHOULD — пустая структура `empty` + `StructureUtils`).
- Методы: `@GameTest(template = "<modid>:empty", timeoutTicks = 200)` с `GameTestHelper`, ассерты `helper.assertTrue(...)`, `helper.assertItemEntityPresent`, `helper.succeed()`.
- Запуск: `./gradlew runGameTestServer -Dforge.enabledGameTestNamespaces=<modid>`; отчёт — `runGameTestServer/logs/` + код возврата Gradle (не 0 = гейт не пройден).
- Требование: каждая **логическая** фича (механика блока, рецепт, крафт-результат, поведение моба, эффект) SHOULD иметь ≥ 1 GameTest. Визуальные фичи (модель/текстура) — через скриншоты.
- Тесты MUST быть детерминированными: без `Math.random()` (только `RandomSource.create(seed)`), без зависимости от времени суток и погоды.

### 6.3 RCON-скрипты — `tools/rcon.py`
- Чистый Python 3, **без внешних зависимостей** (только `socket`, `struct`, `argparse`, `sys`).
- Контракт: `python3 tools/rcon.py [--host 127.0.0.1] [--port 25575] [--password P] <command...>` → печатает ответ сервера, **exit 0** при успешной доставке, exit 2 при недоступном RCON, exit 3 при таймауте, exit 4 при ответе-ошибке («Unknown command», «Incorrect argument»).
- Реализует протокол Source RCON: `SERVERDATA_AUTH`, `SERVERDATA_EXECCOMMAND`, корректную сборку многочастевых пакетов.
- Кидает в `logs/<modid>-<iter>-rcon.txt` лог «команда → ответ» для отчёта.
- Набор проверок формируется **из карточки заказа**: `give`, `setblock`, `summon`, `tp`, `effect`, `data get`, `execute if`, `function <modid>:…`, `time set day`, `gamemode creative`, `forceload`, `kill @e[type=...]`.
- Каждая RCON-проверка MUST быть самопроверяющейся: команда + `execute if` / `data get` с ожидаемым значением, сравнение строкой.

### 6.4 Клиент под Xvfb (для скриншотов) — `tools/setup_client.sh`
- `sudo apt-get install -y xvfb xdotool x11-apps imagemagick` (идемпотентно).
- `minecraft-launcher-lib` (pip) → установка клиента; Forge 1.20.1-47.4.23; запуск в офлайн-режиме (`--username TestPlayer`, фиктивный `--uuid`, `--accessToken 0`), сервер — `online-mode=false`, авто-подключение (`--server 127.0.0.1 --port 25565` или через `servers.dat`).
- `Xvfb :99 -screen 0 800x600x24`, `DISPLAY=:99`, `LIBGL_ALWAYS_SOFTWARE=1`, mesa llvmpipe, `-Xmx1024M`.
- Параметры клиента: окно 800×600, `renderDistance=2`, `simulationDistance=2`, graphics Fast, clouds off, particles minimal, VSync off, `pauseOnLostFocus=false`, авто-вход на сервер.
- Готовность определяется **по логу** (маркер загрузки мира, например строка про «Loaded 0 advancements» / «Connecting to 127.0.0.1» + отсутствие ошибок), таймаут ожидания — 15 минут на первый запуск, 3 минуты на последующие.
- `tools/spawn.sh` / `tools/scene_day.sh`: `time set day`, `weather clear`, `gamemode creative`, `tp 0 64 0`, выдача предметов мода, постройка тестовой сцены (платформа + расстановка блоков мода), `kill @e[type=!player]`.

### 6.5 Forge MDK + Gradle (`runClient` / `runServer`)
- `xvfb-run -a ./gradlew runClient` — для отладки из исходников при разработке; `./gradlew runServer` — быстрый сервер без отдельной установки.
- Обязательно: JVM-флаги `-Xmx1G` (client) / `-Xmx768M` (server), `-Dfml.earlyprogresswindow=false`.
- Gradle-кэш и run-директории MUST быть вне воркспейса (`/home/user/.cache/mc/gradle*`, `runs/` → symlink в кэш).

### 6.6 noVNC в браузере (LIVE PREVIEW) — `tools/start_novnc.sh`
- `x11vnc -display :99 -forever -nopw -rfbport 5900` + `websockify`/`novnc` на порту **6080**, доступно как live-превью.
- Клиент/сервер MUST биндить только localhost (0.0.0.0 только для noVNC-порта, с паролем SHOULD).
- Запуск только по запросу человека (жрёт CPU); в автоцикле — off по умолчанию.

---

## 7. Контракты скриптов (MUST быть реализованы/сохранены)

| Скрипт | Назначение | Аргументы | Выход |
|---|---|---|---|
| `tools/setup_server.sh` | установка Java 17 + Forge-сервер, старт/стоп | `{install\|start\|stop\|restart\|status\|mods}` | exit 0/1, логи в `logs/` |
| `tools/setup_client.sh` | Xvfb + установка клиента + Forge + запуск | `{install\|start\|stop\|status}` | exit 0/1 |
| `tools/rcon.py` | RCON-команда | `--host --port --password cmd…` | ответ в stdout, exit 0/2/3/4 |
| `tools/spawn.sh` | подготовка игрока и точки спавна | `[--player NAME]` | exit 0 |
| `tools/scene_day.sh` | сцена «день, креатив, tp, разложить контент мода» | `--mod <modid> [--preset NAME]` | exit 0, PNG-сцена готова к съёмке |
| `tools/screenshot.sh` | фокус окна + F2 (`xdotool`) + fallback `import -display :99 -window root` | `out.png` | exit 0, файл > 10 КБ, не «чёрный» |
| `tools/start_novnc.sh` | noVNC на 6080 | `{start\|stop}` | exit 0 |

**Требования ко всем скриптам:** `set -euo pipefail`; идемпотентность; пути через переменные `MC_ROOT=/home/user/.cache/mc`; все скачивания — с ретраями (3 попытки, 5 с); ничего не пишут в воркспейс, кроме `logs/`, `shots/`, `reports/`.

---

## 8. Скриншоты: 4 способа (MUST поддерживаться все)

1. **F2 в игре** → `screenshots/`: `xdotool search --name "Minecraft" windowfocus && xdotool key F2`, затем ждать появления файла (poll ≤ 30 с).
2. **Снимок X-экрана**: `import -display :99 -window root shots/…/NN.png` (fallback, если F2 не сработал).
3. **Helper-мод** (внутри тестового мода или отдельным `shotmod`): команда `/shot [name]` + автоскрин по таймеру (`/shot every 20s`), сохранение через `Screenshot`-утилиту/нативный вызов; удобно для серийных кадров и для съёмки GUI.
4. **noVNC** — человек смотрит и «щёлкает» сам в live-превью.

**Правила съёмки (MUST):**
- Набор кадров на мод: `01-spawn.png` (точка спавна днём), `02-blocks.png` (все блоки мода в мире, днём, без дождя), `03-items.png` (все предметы в инвентаре), `04-craft.png` (интерфейс крафта/верстака с рецептом мода), `05-feature-<id>.png` по одной на ключевую фичу, `06-gui.png` (если есть контейнер).
- Формат PNG, 800×600, размер ≤ 400 КБ (иначе `convert -quality`/`pngquant` SHOULD).
- **Автопроверка «не чёрный экран»:** `identify -format "%[fx:mean] %k" file.png` → `mean` MUST быть > 0.02, число уникальных цветов `k` MUST быть > 1000. Иначе — кадр переснять.
- Имена файлов: `<NN>-<kebab-name>.png`; в отчёте каждый кадр подписан, что на нём ожидается увидеть.
- Скриншоты не режутся и не «улучшаются» в фотошопе — только `convert -crop`/`-resize` по необходимости.

---

## 9. Замкнутый цикл разработки (обязательный алгоритм агента)

```
1. ЗАКАЗ         карточка заказа (раздел 4) → уточнить неизвестное, зафиксировать допущения
        ↓
2. ПЛАН          список фич с id, порядок, риски, что тестируем чем (GameTest/RCON/скрин)
        ↓
3. КАРКАС        MDK 1.20.1-47.4.23, mods.toml, MODID, DeferredRegister, пустой @Mod
        ↓
4. КОД + DATA    фичи по одной; после каждой — ./gradlew build
        ↓
5. СБОРКА        jar → mods-to-test/   (без sources/javadoc в прогон)
        ↓
6. СЕРВЕР        setup_server.sh restart
                 ├─ forge mods list  → мод в списке?
                 ├─ grep логов       → чисто?
                 └─ crash-reports/   → пусто?
        ↓
7. RCON          прогон чек-листа из карточки (каждая фича: команда + проверка)
        ↓
8. GAMETEST      ./gradlew runGameTestServer → все зелёные?
        ↓
9. КЛИЕНТ        Xvfb → scene_day.sh → spawn.sh → screenshot.sh ×N → автопроверка PNG
        ↓
10. ОТЧЁТ        reports/<modid>.md: что сделано, доказательства, скриншоты, известные ограничения
        ↓
11. ЧЕЛОВЕК      смотрит PNG → «ок» (фиксация версии) | «чинить: …» (замечания)
        ↓
12. ИТЕРАЦИЯ     замечания → правка → возврат на шаг 4. Итераций ≤ 5, иначе — эскалация.
```

**Правила цикла:**
- Каждый шаг MUST оставлять доказательство: лог, вывод команды, PNG, либо запись «шаг пропущен, причина».
- Агент MUST НЕ объявлять «готово» без зелёного гейта 6 (сервер) и, для визуальных фич, гейта 9 (скриншоты).
- Любое ручное вмешательство человека (через noVNC) фиксируется в отчёте.
- При 5-й неуспешной итерации — стоп, разбор причин, эскалация человеку с конкретным вопросом (а не «не получается»).
- Между прогонами сервер и клиент MUST останавливаться (память), если не хватает ОЗУ.

---

## 10. Definition of Done (гейты приёмки)

### 10.1 Сборка
- [ ] `./gradlew build` — exit 0, без `warning: unknown enum constant` и без падения тестов.
- [ ] В `build/libs` ровно ожидаемый jar (без `-sources`, `-javadoc` в прогоне); размер ≤ 4 МБ.
- [ ] Проект собирается из чистого клона (MUST проверяться хотя бы один раз на финальной итерации).

### 10.2 Загрузка на сервере
- [ ] `forge mods list` содержит `<modid>@<version>`.
- [ ] В логе есть строка загрузки мода без `ERROR`.
- [ ] `crash-reports/` пуста; `logs/debug.log` без `SEVERE` (кроме белого списка).
- [ ] Сервер достиг `Done (…)!`.

### 10.3 Логи (grep-гейт)
- [ ] Отсутствуют: `Exception`, `Error`, `Failed to`, `Caught exception`, `Mixin apply failed`, `Missing texture`, `Unable to load model`, `Model loading error`, `Skipping texture`, `Missing translation`, `NullPointerException`, `ConcurrentModificationException`, `NoClassDefFoundError`.
- [ ] Белый список допустимых предупреждений фиксируется в отчёте (например, ванильные `Failed to load texture` для известных MC-багов).

### 10.4 RCON-чек-лист
- [ ] Каждая фича из карточки: команда выполнена, `exit 0`, получен ожидаемый ответ/состояние.
- [ ] Все предметы/блоки мода выдаются (`/give`), устанавливаются (`/setblock`), имеют корректное отображаемое имя.
- [ ] Рецепты проверены: `/recipe give @p *` наличие, либо крафт по шаблону через `setblock` + проверку выхода.
- [ ] Ворлдген проверен: `/locate` или `execute if block` в новом мире (SHOULD — отдельный мир-песочница, `level-seed` фиксированный).

### 10.5 GameTest
- [ ] `./gradlew runGameTestServer` — exit 0, все тесты `PASS`, 0 `FAIL`.
- [ ] Тесты детерминированы (повторный прогон даёт тот же результат — проверяется 2 раза).

### 10.6 Визуал
- [ ] Полный набор скриншотов (раздел 8) получен, все прошли автопроверку «не чёрный экран».
- [ ] На кадрах видно: корректные текстуры (не «missing texture» — чёрно-фиолетовые), корректные модели, понятные названия в инвентаре, тултипы.
- [ ] Для всех блоков есть кадр в мире; для всех предметов — кадр в инвентаре.

### 10.7 Данные и локализация
- [ ] `runData` — exit 0, сгенерированные JSON валидны.
- [ ] Теги заполнены (`mineable/*`, `needs_*_tool`, `forge:ores/…` при руде).
- [ ] `en_us.json` и `ru_ru.json` полные, без «сырых» ключей в UI.
- [ ] Рецепты и лутаблицы соответствуют карточке заказа.

### 10.8 Производительность
- [ ] Старт сервера ≤ 120 с до «Done».
- [ ] Нет фоновых потоков; тики O(1) на элемент; `/forge tps` не проседает ниже 19 при сцене.
- [ ] Память: сервер живет на `-Xmx768M`, не уходит в OOM (проверка `dmesg | grep -i oom` MUST быть пустой).

### 10.9 Отчёт
- [ ] `reports/<modid>.md` заполнен по шаблону (раздел 12) со ссылками на PNG и логи.

---

## 11. Стоп-лист (что агенту делать ЗАПРЕЩЕНО)

1. Использовать API не из 1.20.1 (классы/методы из 1.19.4-, 1.20.4+, NeoForge-пакеты `net.neoforged.*`).
2. Выдумывать названия методов/классов — при сомнении MUST свериться с исходниками Forge/MC в `~/.cache/mc/` (декомпилированные `sources`) или официальной документацией; если сомнение не снято — спросить/зафиксировать риск.
3. Класть в воркспейс: `~/.minecraft`, `runs/`, `.gradle`, `build/`, дистрибутивы Minecraft/Forge, логи > 5 МБ, PNG > 400 КБ.
4. Устанавливать моды/зависимости, не указанные в карточке заказа.
5. Менять `modid`, id предметов/блоков, после того как версия принята человеком.
6. Отключать проверки (`-Denforce...`, `--offline`-хаки), чтобы «пройти» гейт; чинить причину, а не симптом.
7. Менять глобальные настройки ОС/Java-версии по умолчанию без записи в отчёт.
8. Запускать клиент и сервер одновременно при свободной памяти < 1.6 ГБ.
9. Оставлять `TODO`/заглушки/`RuntimeException("not implemented")` в принятой версии (допустимо только в ветке разработки).
10. Использовать `Mixin`/coremod без явного обоснования в отчёте.
11. Скачивать контент (текстуры/модели) из внешних источников без лицензии — текстуры MUST генерироваться/рисоваться агентом.
12. Хранить пароли/токены в воркспейсе (RCON-пароль — в `~/.cache/mc/server/server.properties`, в отчёт не попадает).

---

## 12. Шаблон отчёта (`reports/<modid>.md`)

```markdown
# Отчёт: <display_name> <version> (modid: `<modid>`)
Дата: YYYY-MM-DD | Итерация: N | Статус: ✅ принято / ⚠️ требуется правка

## 1. Заказ
Ссылка на карточку / краткое содержание.

## 2. Что реализовано
| id | Фича | Статус | Как проверено |
|----|------|--------|----------------|
| F1 | Медный телепортер | ✅ | RCON: give → setblock → правый клик (ручная проверка в noVNC) + GameTest `teleporter_moves_player` |

## 3. Допущения и решения
- Пункт X из заказа не специфицирован → сделано так-то, потому что …

## 4. Доказательства
### Сборка
$ ./gradlew build → BUILD SUCCESSFUL in 45s; jar 1.8 МБ
### Сервер
- forge mods list → `examplemod@1.0.0`
- latest.log: `Done (23.4s)!`, ошибок 0
- crash-reports: пусто
### RCON (вывод)
$ python3 tools/rcon.py give TestPlayer examplemod:copper_teleporter → "Gave 1 [Медный телепортер] to TestPlayer"
### GameTest
- teleporter_moves_player: PASS (2 прогона, детерминированно)
### Скриншоты
| Кадр | Ожидается | mean | colors |
|------|-----------|------|--------|
| shots/examplemod/2/01-spawn.png | Платформа, день, игрок | 0.41 | 24k |
| shots/examplemod/2/02-blocks.png | 4 блока мода в ряд | 0.38 | 19k |

## 5. Производительность
Старт: 41 с | TPS: 20 | Heap extra: ~40 МБ | Assets: 0.9 МБ

## 6. Известные ограничения / риски
- На llvmpipe при 2 чанках обзора частицы отрисовываются с задержкой — не влияет на логику.

## 7. Что НЕ сделано (из заказа)
- F5 «Интеграция с JEI» — отложено на v1.1.0, причина: …

## 8. Команды для повторения
./gradlew build && cp … mods-to-test/ && tools/setup_server.sh restart && python3 tools/rcon.py …
```

---

## 13. Приложения (шаблоны кода)

### 13.1 Главный класс
```java
@Mod(ExampleMod.MODID)
public class ExampleMod {
    public static final String MODID = "examplemod";
    public static final Logger LOGGER = LogUtils.getLogger();

    public ExampleMod(FMLJavaModLoadingContext ctx) {
        IEventBus modBus = ctx.getModEventBus();
        ModBlocks.BLOCKS.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModTabs.TABS.register(modBus);
        ModBlockEntities.BLOCK_ENTITIES.register(modBus);
        ModPayloads.register();
        modBus.addListener(this::commonSetup);
        MinecraftForge.EVENT_BUS.register(this);
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, ModConfigs.SPEC, "examplemod-common.toml");
    }

    private void commonSetup(FMLCommonSetupEvent event) {
        event.enqueueWork(() -> { /* трейд-/пакетные регистрации, потокобезопасно */ });
    }
}
```

### 13.2 Регистрация блока (паттерн на все реестры)
```java
public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(ExampleMod.MODID);

    public static final DeferredBlock<Block> COPPER_TELEPORTER = BLOCKS.registerBlock(
        "copper_teleporter",
        p -> new TeleporterBlock(BlockBehaviour.Properties.of()
                .mapColor(MapColor.METAL).strength(3.5f).requiresCorrectToolForDrops().sound(SoundType.COPPER)),
        BlockItem::new);   // SHOULD: сразу регистрировать BlockItem
}
```
`DeferredBlock` / `DeferredItem` (`net.minecraftforge.registries.DeferredRegister.DeferredBlock`) SHOULD использоваться вместо «сырого» `RegistryObject` — они типизированы и дают `get()` без кастов.

### 13.3 Клиентская изоляция
```java
@Mod.EventBusSubscriber(modid = ExampleMod.MODID, value = Dist.CLIENT, bus = Bus.MOD)
public final class ClientSetup {
    @SubscribeEvent
    static void onClientSetup(FMLClientSetupEvent e) {
        e.enqueueWork(() -> {
            ItemBlockRenderTypes.setRenderLayer(ModBlocks.GLASS_LIKE.get(), RenderType.cutout());
            MenuScreens.register(ModMenus.EXAMPLE_MENU.get(), ExampleScreen::new);
        });
    }
}
```

### 13.4 GameTest
```java
public final class ModGameTests {
    @GameTest(template = "examplemod:empty", timeoutTicks = 200)
    public static void teleporterMovesPlayer(GameTestHelper helper) {
        BlockPos pos = new BlockPos(1, 2, 1);
        helper.setBlock(pos, ModBlocks.COPPER_TELEPORTER.get());
        Player player = helper.makeMockPlayer();
        helper.assertTrue(player.getY() >= 0, "player exists");
        helper.setBlock(pos.above(2), Blocks.AIR);
        helper.succeed();
    }
}
```
Структуры: `src/main/resources/data/examplemod/structures/empty.nbt`; запуск: `./gradlew runGameTestServer -Dforge.enabledGameTestNamespaces=examplemod`.

### 13.5 Данные (data generation)
```java
@Mod.EventBusSubscriber(modid = ExampleMod.MODID, bus = Bus.MOD)
public final class DataGeneration {
    @SubscribeEvent
    static void gather(GatherDataEvent e) {
        DataGenerator gen = e.getGenerator();
        PackOutput out = gen.getPackOutput();
        var lookup = e.getLookupProvider();
        var helper = e.getExistingFileHelper();
        gen.addProvider(e.includeServer(), new ModRecipes(out));
        gen.addProvider(e.includeServer(), ModLootTables.create(out));
        gen.addProvider(e.includeServer(), new ModBlockTags(out, lookup, helper));
        gen.addProvider(e.includeServer(), new ModItemTags(out, lookup, ModBlockTags::get, helper));
        gen.addProvider(e.includeClient(), new ModBlockStates(out, helper));
        gen.addProvider(e.includeClient(), new ModItemModels(out, helper));
        gen.addProvider(e.includeClient(), new ModLang.En(out));
        gen.addProvider(e.includeClient(), new ModLang.Ru(out));   // ru_ru — ОБЯЗАТЕЛЬНО
    }
}
```

### 13.6 Конфиг
```java
public final class ModConfigs {
    private static final ForgeConfigSpec.Builder B = new ForgeConfigSpec.Builder();
    public static final ForgeConfigSpec.IntValue TELEPORT_HEIGHT = B
        .comment("Высота телепорта (блоки)").defineInRange("teleportHeight", 8, 1, 64);
    public static final ForgeConfigSpec SPEC = B.build();
}
```

### 13.7 Минимальный конвейер прогона (shell)
```bash
set -euo pipefail
MODID=examplemod; VER=1.0.0

./gradlew build -x test --project-cache-dir /home/user/.cache/mc/gradle
cp "mods/$MODID/build/libs/$MODID-$VER.jar" mods-to-test/

tools/setup_server.sh restart
python3 tools/rcon.py "forge mods list" | grep -q "$MODID@$VER"

! grep -Ei 'exception|failed to|missing texture|no class def' logs/$MODID-server.log
[ -z "$(ls -A /home/user/.cache/mc/server/crash-reports)" ]

# RCON-чек-лист из карточки заказа
python3 tools/rcon.py "give TestPlayer $MODID:copper_teleporter"
python3 tools/rcon.py "setblock 0 64 0 $MODID:copper_teleporter"

# Скриншоты
tools/setup_client.sh start
tools/scene_day.sh --mod $MODID
tools/screenshot.sh "shots/$MODID/1/01-spawn.png"
identify -format "%[fx:mean] %k\n" "shots/$MODID/1/01-spawn.png"   # mean > 0.02, colors > 1000
```

---

## 14. Метрики качества агента (для оценки работы конвейера)

| Метрика | Цель |
|---|---|
| Доля модов, принятых с 1–2 итераций | ≥ 60 % |
| Среднее число итераций до «ок» | ≤ 3 |
| Доля «зелёных» прогонов сервера с первого запуска | ≥ 80 % |
| Доля гейтов, подкреплённых доказательством (лог/PNG/вывод) | 100 % |
| Доля фич с автотестом (GameTest или RCON-чек) | ≥ 80 % |
| Превышение бюджета памяти/OOM на прогон | 0 |
| Время полного цикла на мод ≤ 8 фич | ≤ 90 мин (с учётом 5–15 мин первого запуска клиента) |

---

## 15. Открытые вопросы (SHOULD уточнить у заказчика перед стартом)

1. Версия Forge зафиксирована на **47.4.23** или допустимо обновление в пределах 1.20.1 (например, 47.4.x новее)?
2. Требуется ли поддержка JEI/других модов, или мод MUST работать строго в одиночку?
3. Нужна ли генерация в уже существующем мире (тогда обязательна обратная совместимостьworldgen) или только в новых мирах?
4. Кто рисует текстуры: агент генерирует (`generate_image`) или заказчик даёт свои PNG?
5. Нужен ли мультиплеер-специфичный контент (синхронизация, персональные данные) — это меняет объём сетевого кода.
