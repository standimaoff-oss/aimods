# Франция и Российская империя 1812 · alpha.8

**[Скачать aiarsenal-1.0.1-alpha.8.jar](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/aiarsenal-1.0.1-alpha.8.jar)** · 51 751 823 байта.  
Minecraft **1.20.1**, Forge **47.4.23**, Java **17**.

## Что добавлено

| Франция | Российская империя |
|---|---|
| Мушкет 1777 / An IX | Пехотное ружьё обр. 1808 |
| Кремнёвый пистолет An XIII | Кавалерийский пистолет обр. 1809 |
| Тесак-брикет | Кавалерийская сабля |
| 6-фунтовая пушка An XI | 12-фунтовая пушка обр. 1805 |

13 настоящих текстурированных GLB: восемь образцов оружия/артиллерии и пять моделей
боеприпасов. Живой Blender 4.2.5 + закреплённый MCP, восемь viewport-проверок;
[исходная сцена .blend с упакованными текстурами](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/napoleonic_arms.blend).
Это узнаваемые игровые исторические стилизации, не музейные обмеры.

Кремнёвое оружие однозарядное: бумажный патрон, шомпол, курок, отдельные звуки
выстрела и заряжания. Мушкет заряжается 8 секунд, пистолет 6 — ускоренный игровой темп.
Пушки заряжаются вручную, различают калибры, стреляют одним баллистическим ядром на заряд.
Откатывается весь лафет. Ядро — небольшой физический GLB, не огромный предмет-билборд
и не взрывной снаряд. Сабли — ближний бой. RU/EN, рецепты, иконки и отдельные вкладки 1812.

**[Управление, боеприпасы и ID](../../notes/stage4/CONTROLS.md)**.

## Объёмный дым

- Для обычных выстрелов, чёрного пороха, пушек, выхлопа, пыли попадания и дыма обычного
  взрыва сделаны собственное эллипсоидальное поле плотности, направленность,
  турбулентное разрушение и палитры (type 11). Это не переименованный дым донора 1:1.
- Общий raymarch-рендер, шум и освещение основаны на VolPyro. Это не утверждение,
  что весь движок объёмного рендера написан заново.
- Четыре исходных шейдера донора и ядерные ветви сохранены; ядерные эффекты используют
  готовую реализацию донора. [Разграничение и лицензии](../../THIRD_PARTY_NOTICES.md).
- Эмиссия привязана к игровым выстрелам/попаданиям и работающим двигателям.
  В проверке обычный взрыв создал настоящий выстрел РПГ-7 в стену, не команда показа эффекта.
- Ту-95МС и Ту-160 проверены живыми, с работающими двигателями на стоянке. На малом газу
  выхлоп слабый; это не дым пожара. Готовность подтверждена серверным состоянием и клиентским callback.

## Движение и сохранённый контент

Завершены idle / медленный шаг / ходьба / бег / приседание, смешивание с ADS,
перезарядкой и отдачей. Бег больше не уводит ТТ полностью за нижнюю границу кадра.
Движение удалённых игроков измеряется по реальному перемещению с коротким окном,
не сбрасывается в idle на пустом межпакетном тике. Это не принудительное выставление позы.

Включён индекс групп GLB вместо повторного полного обхода; проверена идентичность
порядка/состава, в том числе после перезагрузки ресурсов. Сохранены прежние стволы,
прицелы, форма, ядерное оружие, дроны и боеприпасы действующих носителей/ПВО.
У ППШ добавлен запас по уровню при совпадении нескольких звуковых голосов после
пакетной доставки; запись не нормализовалась и не обрабатывалась лимитером.

## Проверки

[Полный CI — SUCCESS](https://github.com/standimaoff-oss/aimods/actions/runs/38770590840), **15.10.2026, 16:37:43–17:13:11 UTC**.

- **27 Python-тестов**: модели, ресурсы, рецепты, протокол и звук; release build PASS.
- **168/168 Minecraft GameTests**, включая один выстрел на заряд и межпакетные провалы скорости.
- Установленный релизный JAR на dedicated server и двух независимых Forge-клиентах.
- Четыре кремнёвых ствола действительно уменьшили здоровье живой серверной цели;
  перезарядка восстановила ровно один патрон. Обе пушки реально заряжены и подожжены вводом мыши.
- Реальное попадание РПГ и разрушение стены; живые двигатели обоих бомбардировщиков.
- **25 наблюдений режимов движения**: 15 от первого лица, 10 у второго игрока;
  дополнительные third-person кадры, ADS и перезарядка во время ходьбы.
- Старые оптические прицелы, форма и хват у второго клиента; resource reload,
  переходы мира и намеренная поломка шейдера с восстановлением после reload.
- Обновление старого мира и повторное открытие PASS, с проверкой сохранённых предметов.
- **212 настоящих Minecraft F2**, **17 непрерывных MP4** с X11 + нативным PulseAudio.
  Все записи прошли неизменённые пороги длительности, RMS и пика по всем каналам.

Ручной просмотр: новые мушкеты/пистолеты и их дым, сабли, обе пушки, оба живых самолёта,
ТТ при беге, набор кадров всех режимов движения, удалённый хват, ПУ/ZF39, восемь
Blender viewport и 24 извлечённых исходных кадра перезарядки новых стволов.
Сводные листы использовались только для просмотра; ниже ссылки на исходные F2, не монтажи.
Метрики звука не заменяют субъективного прослушивания каждого ролика.

[Игровой протокол](run-38770590840/stage4-gameplay.json) ·
[Два клиента](run-38770590840/stage2-multiplayer.json) ·
[Движение и ABBA](run-38770590840/stage3-motion.json) ·
[Миграция](run-38770590840/migration-provenance.json) ·
[Установленный JAR](run-38770590840/installed-provenance.json).

В логе есть **намеренная** ошибка GLSL в проверке безопасного отключения рендера;
она не выдаётся за штатный успешный compile. После reload рендер восстанавливается.

## Исходные скриншоты

[Все 212 F2](https://github.com/standimaoff-oss/aimods/tree/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840).

- [Мушкет Франции: пороховой выстрел](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-musket_1777-powder-shot.png)
- [Мушкет РИ: шомпол](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-musket_1808-ramrod.png)
- [Пистолет An XIII: выстрел](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-pistol_an13-powder-shot.png)
- [Пистолет РИ](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-pistol_1809-hip.png)
- [Французская пушка](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-cannon_fr6-ready.png)
- [Русская пушка: выстрел](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-cannon_ri12-fire.png)
- [Тесак-брикет](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-sabre_briquet-hand.png)
- [Кавалерийская сабля](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-sabre_1809-hand.png)
- [Обычный взрыв после попадания РПГ](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-custom-rpg-impact.png)
- [Ту-95МС: работающие двигатели](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-engine-tu95ms-exhaust.png)
- [Ту-160: работающие двигатели](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-engine-tu160-exhaust.png)
- [ТТ при беге](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-motion-tt33-run.png)
- [Пистолет у другого игрока](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-remote-pistol_1809-grip.png)
- [Прицел ПУ](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-mosin_pu-02-aim.png)
- [Прицел ZF39](https://github.com/standimaoff-oss/aimods/blob/66f580615accb82e70f76820449b967598fa6a3f/shots/aiarsenal/stage4/run-38770590840/stage4-k98k_zf39-02-aim.png)

## Непрерывные видео и нативный звук

Без синтеза кадров, нормализации, downmix или постобработки уровня. Stereo 48 kHz.

| Видео | Длительность, с | Peak | RMS |
|---|---:|---:|---:|
| [1812-cannon_fr6.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-cannon_fr6.mp4) | 22.86 | 0.2698 | 0.03366 |
| [1812-cannon_ri12.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-cannon_ri12.mp4) | 22.05 | 0.2528 | 0.03823 |
| [1812-musket_1777.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-musket_1777.mp4) | 21.71 | 0.1769 | 0.01276 |
| [1812-musket_1808.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-musket_1808.mp4) | 21.65 | 0.1344 | 0.01381 |
| [1812-pistol_1809.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-pistol_1809.mp4) | 21.65 | 0.1583 | 0.03776 |
| [1812-pistol_an13.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/1812-pistol_an13.mp4) | 21.65 | 0.1386 | 0.01593 |
| [c96.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/c96.mp4) | 36.00 | 0.2519 | 0.01004 |
| [custom-ordinary-explosion.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/custom-ordinary-explosion.mp4) | 13.30 | 0.4709 | 0.04484 |
| [engine-tu160.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/engine-tu160.mp4) | 10.37 | 0.3291 | 0.05944 |
| [engine-tu95ms.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/engine-tu95ms.mp4) | 10.35 | 0.2535 | 0.05419 |
| [k98k_zf39.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/k98k_zf39.mp4) | 14.25 | 0.4361 | 0.03431 |
| [mosin_pu.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/mosin_pu.mp4) | 14.30 | 0.3952 | 0.06525 |
| [motion-mosin_pu.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/motion-mosin_pu.mp4) | 38.75 | 0.4134 | 0.00856 |
| [motion-ppsh41.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/motion-ppsh41.mp4) | 53.85 | 0.4208 | 0.02291 |
| [motion-tt33.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/motion-tt33.mp4) | 40.65 | 0.3037 | 0.00627 |
| [ppsh41.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/ppsh41.mp4) | 13.83 | 0.2120 | 0.00539 |
| [tt33.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage4-38770590840/tt33.mp4) | 14.30 | 0.2510 | 0.00405 |

## Производительность: без обещания FPS

Одна сцена с 16 комплектами формы на стойках, одна камера, ABBA, по 40 измеряемых
кадров после прогрева. Программная Mesa llvmpipe, не аппаратная видеокарта.

| Проход | Render median, мс | Render p95, мс | Frame interval median, мс |
|---|---:|---:|---:|
| scan | 41.653 | 54.345 | 58.891 |
| index | 40.990 | 74.086 | 57.983 |
| index | 37.919 | 63.510 | 57.995 |
| scan | 38.729 | 53.066 | 54.597 |

**Убедительный прирост FPS этим замером не доказан:** разница медиан мала, p95 у
индексированного варианта хуже в этом прогоне. Оптимизация обхода подтверждена по
корректности, но выдавать эти числа за ускорение на пользовательском GPU нельзя.
Переработка танков по отсутствующему референсу в этот релиз не входит.

## Установка и происхождение

1. Сделать копию своего мира.
2. Заменить прежний AI Arsenal JAR на alpha.8 на клиенте и сервере, не оставлять две версии.
3. Отдельный VolPyro не нужен. Публичный alpha.6 сохранён как предыдущая версия.

Source: `db0e1cfbac91c9bfe6bfb5f1d2607f1baa7efa01`. Evidence: `66f580615accb82e70f76820449b967598fa6a3f`.  
SHA-256 совпадает между установленной сборкой, миграцией и digest release asset:
```
08dde5cf9b082444968a19ee4def60b6dd6e0b363548bda85ac2efb74ef2abb3
```

Ранее отклонённые прогоны не являются доказательством полного успеха: 38764280939
обнаружил сбой remote WALK, неудачный кадр бега, падение самолётов в неверно заданной
сцене и перегрузку аудио. Всё исправлено и заново проверено в указанном выше прогоне;
пороги аудио и GameTests не ослаблены. История: [PLAN](../../notes/stage4/PLAN.md).
