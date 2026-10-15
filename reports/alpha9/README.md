# Alpha.9 — исправление загрузки самолётов и завершение выдачи

**[Скачать aiarsenal-1.0.1-alpha.9.jar](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/aiarsenal-1.0.1-alpha.9.jar)** · 51 753 909 байт.
Minecraft **1.20.1**, Forge **47.4.23**, Java **17**.

## Что доделано после alpha.8

Исправлена **сама загрузка BomberEntity**, а не только сценарий проверки.
Ванильная команда `/summon` задаёт окончательные координаты после чтения NBT;
раньше физическая модель уже запоминала начало координат и самолёт мог переместиться
туда, упасть и разбиться. Теперь перед первым физическим шагом после load координаты
однократно согласуются с фактической позицией сущности. Сохранённые ориентация,
скорость, здоровье и управление не сбрасываются. Штатное размещение предметом сохранено.

Добавлены два GameTests, каждый проверяет **Ту-95МС и Ту-160**:
- порядок NBT → окончательная позиция, как в vanilla summon;
- save/load с сохранением положения и динамического состояния.

В установленной игре проверка снова использует **обычный `/summon`**, без обходной
команды размещения, бессмертия или отключения физики. После работы двигателей:

| Самолёт | Запрошенная позиция | Измеренная серверная позиция |
|---|---|---|
| Ту-95МС | 0.5, −60, 48.5 | 0.5, −60, 48.616071430300764 |
| Ту-160 | 0.5, −60, 48.5 | 0.5, −60, 48.57976628321329 |

Проверены жизнь, флаг двигателя, отсутствие флага разрушения, расположение рядом
с точкой появления и реальная клиентская эмиссия выхлопа. Небольшое перемещение
вдоль стоянки — физика работающей машины, а не телепорт в начало координат.

## Полный состав сохранён

Это полный JAR, **не отдельный патч**. В нём остаются мушкеты 1777/1808,
пистолеты An XIII/1809, тесак-брикет и сабля, французская 6-фунтовая и русская
12-фунтовая пушки, боеприпасы и мундиры обеих армий. Собственное поле объёмного
дыма обычных выстрелов/взрывов/двигателей на основе рендера VolPyro; готовые ядерные
эффекты сохранены. Прежние оружие, прицелы, техника, дроны, ракеты действующих
носителей/ПВО и пять режимов движения не удалены.

[Каталог и описание alpha.8](../stage4/README.md) ·
[Управление, включая медленный шаг](../../notes/stage4/CONTROLS.md).

Обновлены README и статусы этапов: главная страница ветки больше не предлагает
alpha.5 как текущую сборку и не называет завершённые движения будущей работой.

## Проверки именно alpha.9

[Полный CI — SUCCESS](https://github.com/standimaoff-oss/aimods/actions/runs/38777157178), 15.10.2026, **17:25:06–18:02:32 UTC**.

- **27 Python-тестов**, сборка PASS; **170/170 Minecraft GameTests**.
- Миграция старого мира и повторное открытие, одинаковый JAR на сервере и клиентах.
- Два настоящих клиента; 25 local/remote наблюдений режимов движения, ADS/reload,
  resource reload, идентичность GLB-индекса и прежнего обхода, ABBA в одинаковой сцене.
- Настоящая стрельба четырёх кремнёвых стволов по живой цели, обе пушки,
  попадание РПГ и дым обычного взрыва, работа обоих бомбардировщиков после summon.
- **212 исходных F2**, **17 непрерывных MP4** с нативным игровым звуком.
  Пороги аудио не ослаблены, записи не нормализованы и не обработаны лимитером.
- Повторно просмотрены свежие F2 обоих самолётов, порохового выстрела и ТТ при беге.
  Расширенная визуальная приёмка неизменённых моделей/анимаций описана в отчёте alpha.8.

[Протокол игры](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage4/run-38777157178/stage4-gameplay.json) ·
[Движение и ABBA](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage4/run-38777157178/stage3-motion.json) ·
[Два клиента](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage4/run-38777157178/stage2-multiplayer.json) ·
[Миграция](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage4/run-38777157178/migration-provenance.json) ·
[RCON с командами и координатами](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/stage4/run-38777157178/rcon.log).

## Скриншоты и видео

[Все 212 исходных F2](https://github.com/standimaoff-oss/aimods/tree/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178).

- [Ту-95МС после обычного summon](https://github.com/standimaoff-oss/aimods/blob/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178/stage4-engine-tu95ms-exhaust.png)
- [Ту-160 после обычного summon](https://github.com/standimaoff-oss/aimods/blob/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178/stage4-engine-tu160-exhaust.png)
- [Выстрел французского мушкета](https://github.com/standimaoff-oss/aimods/blob/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178/stage4-musket_1777-powder-shot.png)
- [Русская пушка](https://github.com/standimaoff-oss/aimods/blob/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178/stage4-cannon_ri12-fire.png)
- [ТТ при беге](https://github.com/standimaoff-oss/aimods/blob/6af927a2435a4a311b510f9ef7d9a713f3324dcf/shots/aiarsenal/stage4/run-38777157178/stage4-motion-tt33-run.png)

| Непрерывное видео | Длительность, с | Peak | RMS |
|---|---:|---:|---:|
| [1812-cannon_fr6.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-cannon_fr6.mp4) | 23.10 | 0.2964 | 0.05053 |
| [1812-cannon_ri12.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-cannon_ri12.mp4) | 23.10 | 0.2931 | 0.04931 |
| [1812-musket_1777.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-musket_1777.mp4) | 20.65 | 0.1403 | 0.00973 |
| [1812-musket_1808.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-musket_1808.mp4) | 20.70 | 0.2353 | 0.03797 |
| [1812-pistol_1809.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-pistol_1809.mp4) | 21.73 | 0.2656 | 0.05094 |
| [1812-pistol_an13.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/1812-pistol_an13.mp4) | 21.70 | 0.2748 | 0.05195 |
| [c96.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/c96.mp4) | 37.01 | 0.3561 | 0.05281 |
| [custom-ordinary-explosion.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/custom-ordinary-explosion.mp4) | 13.30 | 0.5558 | 0.06708 |
| [engine-tu160.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/engine-tu160.mp4) | 10.41 | 0.4527 | 0.06648 |
| [engine-tu95ms.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/engine-tu95ms.mp4) | 10.35 | 0.3258 | 0.06221 |
| [k98k_zf39.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/k98k_zf39.mp4) | 15.35 | 0.4662 | 0.10268 |
| [mosin_pu.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/mosin_pu.mp4) | 14.30 | 0.3899 | 0.05793 |
| [motion-mosin_pu.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/motion-mosin_pu.mp4) | 40.95 | 0.3993 | 0.00841 |
| [motion-ppsh41.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/motion-ppsh41.mp4) | 57.30 | 0.7860 | 0.00662 |
| [motion-tt33.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/motion-tt33.mp4) | 40.25 | 0.2103 | 0.00215 |
| [ppsh41.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/ppsh41.mp4) | 14.20 | 0.1855 | 0.00324 |
| [tt33.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/tt33.mp4) | 14.30 | 0.4087 | 0.09781 |

[Нативная сцена Blender](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/napoleonic_arms.blend). Кадры — Minecraft F2;
MP4 — захват X11 и PulseAudio, не синтезированные ролики. Метрики звука не заменяют
субъективного прослушивания каждого ролика.

## Установка и границы результата

Сначала сделать копию мира, затем **заменить** старый JAR на клиенте и сервере.
Не оставлять две версии AI Arsenal одновременно. Отдельный VolPyro не требуется.
Публичные alpha.8 и alpha.6 сохранены, их файлы не перезаписывались.

Тестовый GPU — llvmpipe. Аппаратный прирост FPS не доказан; улучшение производительности
не выдаётся за подтверждённый результат. Танки по отсутствующему пользовательскому
референсу не переделаны. Это исправление загрузки, не новый дизайн авиации или танков.

Source `b5fbba79350f8b78d3f692cbd7ecdf3a02837984`. Evidence `6af927a2435a4a311b510f9ef7d9a713f3324dcf`. SHA-256 совпадает у установленного JAR,
сборки миграции и GitHub release asset:
```
82893af2454cd99e8a651d6d9cdeae219c6f87cb35a7ae4a79d18130ab842419
```
