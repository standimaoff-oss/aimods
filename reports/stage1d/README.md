# Этап 1г — хват, прицелы, каталог эпох и миграция

**alpha.4 прошла итоговый CI и просмотр ключевых игровых кадров.** Функциональный контент
этапа 1 реализован; это prerelease, не заявление о закрытии всех гейтов ТЗ.
Непроверенные условия явно перечислены ниже. Дальнейшие армии/эпохи не добавлялись.

## Скачать и установить

- [Релиз alpha.4](https://github.com/standimaoff-oss/aimods/releases/tag/stage1d-38718947164).
- **[Прямой JAR](https://github.com/standimaoff-oss/aimods/releases/download/stage1d-38718947164/aiarsenal-1.0.1-alpha.4.jar)** — 48 268 481 байт.
- Minecraft **1.20.1**, проверенный Forge **47.4.23**, Java **17**.
- Заменить старый AI Arsenal JAR, не оставлять две версии. Обновить клиент и сервер вместе.
  Донорский VolPyro отдельно устанавливать не нужно.
- **Перед обновлением скопировать свой мир.** Проверялся одноразовый QA-мир, не мир пользователя.

SHA-256:
```
eb8a06f8370e803bdf58aa048a5984884fb0cfe4db90eceac7e9804219acea22
```
Digest GitHub asset `643520683` совпадает с SHA-256 JAR, действительно установленного на
Forge-сервер в тесте миграции. Повторная локальная загрузка через release CDN не заявляется.

## Что изменилось относительно alpha.3

- C96/ТТ-33: одноручный хват при стрельбе и ADS; вторая рука используется при перезарядке.
  В третьем лице отдельная поза, а не CROSSBOW_HOLD. Исправлен выявленный клиентским
  сценарием вылет из-за позднего создания расширяемого ArmPose.
- Исправлены масштаб/положение пистолетов: целик дальше от камеры, модель не занимает весь экран.
  Руки при reload отведены от ствольной коробки, кисть C96 подведена к обойме.
- При ADS устранено наследуемое смещение матрицы руки; equip-анимация не уводит наведённое оружие.
  Смена оружия сбрасывает ADS, reload/затвор выводят из увеличения. Оптика/зум только от первого лица.
- Панель чата и название выбранного предмета больше не перекрывают оптический или открытый
  прицел. Вне ADS чат сохраняется. Маска оптики рисуется с корректной глубиной HUD.
- Общий каталог всего мода разделён по эпохам и назначению; порядок явно задан, а не алфавитный.
  Русские заголовки помещаются в creative-инвентаре.
- Уран уже удалён в alpha.3; теперь проверена **настоящая миграция старого сохранения**,
  а не только отсутствие регистраций. Ядерки, дроны и боеприпасы действующих носителей сохранены.
  Среди проверенных ракет бесхозных не найдено: ради количества ракет не удаляли.

Предыдущие составляющие этапа: [ППШ](../stage1/README.md),
[VolPyro](../stage1b/README.md), [четыре WWII-оружия и удаление урана](../stage1c/README.md).

## Итоговая проверка

[CI 38718947164 — SUCCESS](https://github.com/standimaoff-oss/aimods/actions/runs/38718947164),
source `6ce22280a4621c282aae72f937d7daf9c7b31458`, evidence `02780ef`.

| Проверка | Результат |
|---|---|
| Живой Blender 4.2.5 + MCP, экспорт GLB/текстур/анимаций | PASS, 4 viewport-кадра и packed .blend сохранены |
| Сборка/reobfuscation | PASS |
| Minecraft GameTests | **156/156 PASS**, включая полноту каталога |
| ППШ, Мосин ПУ, Kar98k ZF39, C96, ТТ-33 | Настоящие mouse/key inputs, серверные Ammo/Health, стрельба и reload PASS |
| Оптика, свежий чат, FOV 70/90, движение, третье лицо | PASS; 7 проверок маски дали black fraction 1.000 |
| Фон чата | Явно `textBackgroundOpacity=0.5`, не скрыт прозрачной настройкой |
| GUI/окно | **Эффективный** GUI scale 3 на 1000×740; отдельный resize 1100×760 на scale 2 |
| Resource reload | PASS; после него снова видны прицел и объёмный дым |
| Nether → Overworld | PASS; списки эффектов очищены в обоих мирах |
| Настоящая ошибка GLSL-компилятора | PASS: отключился только renderer, резервные частицы видны; reload восстановил объёмный дым |
| VolPyro | Дым, ранняя огненная вспышка, обычный взрыв, BM-21, Tu Bombers, шлейф, оба nuclear-маршрута, лимиты/off/on PASS |
| Creative UI | Оба раздела открыты в игре; реальный Forge sort order совпал с заданным |
| Дополнительные Python-проверки | **13 PASS**: 5 оружие/данные + 5 порт VolPyro + 3 socket/RCON |

Логи: [GameTests](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/gametest-driver.log),
[клиентский сценарий](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/client-driver.log),
[клиент](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/client-latest.log),
[Python](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/local-python-checks.log).
Ошибка GLSL в конце клиентского лога **намеренно внесена opt-in тестом**, после неё проверено
восстановление. Она не активируется у обычного игрока.

### Каталог

| Раздел | Предметов |
|---|---:|
| WWII: оружие / техника / форма / боеприпасы | 8 / 16 / 0 / 25 |
| Холодная война–современность: оружие / техника и дроны / форма / боеприпасы | 21 / 36 / 68 / 54 |
| Общие детали / снаряжение / строительство | 33 / 9 / 103 |

11 зарегистрированных секций, 10 непустых. Пустая WWII-форма скрыта до этапа 2;
афганская советская форма не выдаётся за WWII. Общие 122/152-мм снаряды доступны в обеих эпохах.

### Миграция старого мира — установленный JAR

Сервер старой alpha.2 (`4ced8a4`) действительно создал/сохранил мир. Перед обновлением
создан архив. Затем установлен Forge + релизный reobfuscated JAR alpha.4, проверены блоки
и сундук, выполнен save/stop и **повторный запуск с повторением всех проверок**.

| До | После, включая повторное открытие |
|---|---|
| uranium_ore / deepslate_uranium_ore в мире | stone / deepslate |
| raw_uranium ×9 | iron_nugget ×9 |
| uranium_ingot ×7 | iron_ingot ×7 |
| uranium_ore ×3 / deepslate_uranium_ore ×2 в сундуке | stone ×3 / deepslate ×2 |
| rds1 ×1 / shahed136 ×1 в том же сундуке | Сохранены без смены ID/количества |

[Полный сценарий](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/ore-migration-driver.log),
[provenance и SHA-256 архива](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage1d/run-38718947164/migration-provenance.json).
Бэкап репозитория перед этапом: `/home/user/backups/aimods-before-stage1d.bundle`, проверен;
он **не содержит пользовательского мира**.

## Настоящие игровые кадры

Сохранены **62 F2-скриншота**. Вручную просмотрены 18 ключевых кадров итогового прогона:
оба каталога, C96 ADS/reload/третье лицо, ТТ ADS/движение/третье лицо, ПУ со свежим чатом
и при движении, ZF39 FOV90/reload, ППШ ADS/третье лицо, эффективный scale 3,
shader fallback/recovery и ранняя вспышка. Остальные доступны для самостоятельного просмотра.
Blender viewport не выдаётся за Minecraft.

- [Вся папка F2](../../shots/aiarsenal/stage1d/run-38718947164).
- [C96 — одноручный хват](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-c96-10-third-person-aim.png).
- [ТТ-33 — ADS со свежим чатом](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-tt33-06-chat-ads.png).
- [ПУ — чистая маска](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-mosin_pu-06-chat-ads.png).
- [ZF39 — FOV 90](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-k98k_zf39-07-fov90.png).
- [Каталог WWII](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-catalog-01-ww2-weapons.png).
- [Современная техника и дроны](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/shots/aiarsenal/stage1d/run-38718947164/stage1d-catalog-02-modern-vehicles.png).

## Границы проверки

- **Клиент — ForgeGradle userdev, llvmpipe.** Установленный JAR проверен на dedicated server,
  не в отдельной клиентской установке. Это различие не скрывается.
- Аппаратные NVIDIA/AMD/Intel GPU, высокий графический пресет, FPS и дальнее terrain occlusion
  отдельно не подтверждены. QA имеет render distance 2 и пониженный software-проход VolPyro.
- Аудио не прослушано; пистолеты пока используют общий звук ППШ. Полного видеоревью всех фаз
  анимаций нет: F2 показывает отдельные моменты, не непрерывное движение.
- Reload ресурсов прошёл с heap клиента 2 ГиБ; прежнего 1 ГиБ не хватило при одновременном
  хранении старых и заново запекаемых моделей. Это настройка проверки, не оптимизация FPS.
- Оптимизация по танковому референсу и новые crouch/run/idle/slowwalk-анимации отложены
  по просьбе пользователя. Следующие армии и эпохи — отдельные этапы.

История ошибок и исправлений, включая неудачные/отменённые прогоны:
[notes/stage1d/STATUS.md](../../notes/stage1d/STATUS.md). Промежуточный зелёный
`stage1d-38716020029` остаётся draft; выдаваемая сборка — только `stage1d-38718947164`.
