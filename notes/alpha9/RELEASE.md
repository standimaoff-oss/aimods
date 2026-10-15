# AI Arsenal alpha.9 — исправлена загрузка бомбардировщиков

Полный мод для Minecraft 1.20.1 · Forge 47.4.23 · Java 17.

- Исправлена синхронизация позиции полётной модели после vanilla `/summon` и load. Самолёт больше не начинает физику в (0,0,0); сохранённые ориентация, скорость, здоровье и управление не сбрасываются.
- Два новых регрессионных GameTests для обоих бомбардировщиков. Установленная игра проверяет именно обычный summon, координаты, жизнь и настоящий выхлоп.
- Сохранён весь набор alpha.8: Франция/РИ 1812, мушкеты, пистолеты, сабли, пушки, собственный объёмный дым, ядерные эффекты, форма, движения и прежнее вооружение.

**[Скачать JAR](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38777157178/aiarsenal-1.0.1-alpha.9.jar)** · [Отчёт и скриншоты](https://github.com/standimaoff-oss/aimods/blob/arena/10158ad9-aimods/reports/alpha9/README.md) · [Управление](https://github.com/standimaoff-oss/aimods/blob/arena/10158ad9-aimods/notes/stage4/CONTROLS.md).

[Полный CI: SUCCESS](https://github.com/standimaoff-oss/aimods/actions/runs/38777157178) — 27 Python-тестов, **170 GameTests**, миграция, два настоящих клиента, 212 F2 и 17 непрерывных MP4 с нативным звуком. Свежие кадры исправленной сцены просмотрены. JAR, видео и .blend приложены ниже.

Перед обновлением скопировать мир и заменить прежний JAR на клиенте и сервере. Alpha.8 и alpha.6 сохранены. Проверка на llvmpipe, не сертификация аппаратного FPS; танки по отсутствующему референсу не переделывались.

SHA-256: `82893af2454cd99e8a651d6d9cdeae219c6f87cb35a7ae4a79d18130ab842419`.
Source `b5fbba79350f8b78d3f692cbd7ecdf3a02837984`; evidence `6af927a2435a4a311b510f9ef7d9a713f3324dcf`.
