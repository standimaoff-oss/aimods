# Этап 2 — форма четырёх армий и хват оружия, alpha.6

## Результат

**[Скачать aiarsenal-1.0.1-alpha.6.jar](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/aiarsenal-1.0.1-alpha.6.jar)**  
Minecraft **1.20.1**, Forge **47.4.23**, Java **17**. JAR: **49 745 703 байта**.

Добавлено 16 комплектов × 4 слота = **64 новых надеваемых предмета**:
- СССР / Германия, 1943–45: по пять — пехота, офицер, танкист, лётчик, генерал.
- Франция / Российская империя, около 1812: по три — пехота, офицер, генерал.

Старые 16 комплектов / 64 части сохранены: всего 32 комплекта / 128 частей.
Новые модели созданы в живом Blender 4.2.5 через закреплённый MCP addon, экспортированы
в настоящий текстурированный GLB; .blend содержит упакованные текстуры.
64 иконки, RU/EN, 64 непересекающихся рецепта, отдельные вкладки «Вторая мировая · Форма»
и «1812 · Форма». [Каталог, ID и рецепты](../../notes/stage2/UNIFORMS.md).

Это игровые исторические стилизации указанных периодов, не все полки/годы и не музейные копии.
На германской форме нейтральные кокарды без политических эмблем.

## Хват

- C96 / ТТ: отдельный одноручный хват вместо позы длинного оружия; first-person плечо,
  предплечье и ладонь, корректный участок текстуры кисти и рукав надетого исторического мундира.
- Все 17 FirearmItem в third-person привязаны к GLB-узлу рукояти, а не центру модели;
  убрана инвентарная нормализация размера, поддерживающая рука следует узлу цевья.
- Масштаб рассчитан на читаемость рядом с квадратной Minecraft-кистью, не на строгое 1:1:
  ТТ ×2.0, C96 ×1.8, остальные ×1.15 относительно исходных метровых GLB.
  Оружие поднято относительно центра ладони, чтобы затвор/ствол не тонули в коже.
- Исправлены закрывающие ладони манжеты, выступающие внешние слои скина,
  подгонка узких рук, перенос масштаба руки между рендерами; кэш узлов формы ограничен по asset.
- Это исправление позы удержания, не обещание новой системы локтей/пальцев в third-person.
  Новые анимации бега/ходьбы/приседания и общая оптимизация остаются следующим этапом.

## Проверки и происхождение

[Полный CI — SUCCESS](https://github.com/standimaoff-oss/aimods/actions/runs/38744123986), 15.10.2026, 13:36–14:05 UTC.
- 22 Python-теста (ресурсы, GLB/иконки/рецепты, протокол, аудио), сборка PASS.
- **158/158 Minecraft GameTests**.
- Миграция мира со старой версии и повторное открытие PASS; ядерное оружие, дроны,
  предметы и нужные боеприпасы действующих носителей сохранены.
- Настоящий установленный Forge (`forgeclient`), dedicated server, одинаковый релизный JAR.
- **Два настоящих клиента: TestPlayer и Observer** на одном сервере. Не манекен вместо другого игрока.
- Все 16 комплектов спереди/сзади, каталоги, приседание, resource reload, пистолеты с рукавами;
  17 remote-стволов, леворукий ТТ, дополнительные боковые виды C96/ТТ/ППШ/Мосина ПУ.
- **128 подлинных Minecraft F2**, пять непрерывных MP4 X11 + PulseAudio.

Ручная приёмка: просмотрены 32 кадра формы, обзор 17 remote-стволов, отдельные крупные
кадры пистолетов/винтовок и бокового хвата, леворукий ТТ, четыре FP-вида пистолетов с формой,
оба оптических прицела, каталоги, приседание, reload и 30 извлечённых кадров пяти видео.
Сводные листы использовались только для обзора; ссылки ниже ведут к исходным игровым PNG.

Предыдущие кандидаты 38735566696 и 38739693777 прошли автоматику, но были отклонены
при ручном просмотре (рукава/слои скина/меню, затем утопленные пистолеты).
Они остались неопубликованными draft, не выдаются как итог.

Source: `7bc05a12d5d35ab92ba42b45f0fb2b8a2b04423b`. Evidence: `4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e`.
[Протокол установленного JAR](run-38744123986/installed-provenance.json),
[два клиента](run-38744123986/stage2-multiplayer.json),
[миграция](run-38744123986/migration-provenance.json).
SHA-256 совпадает между installed client/server, миграцией и digest GitHub release asset:
```
20903247f92eed0e617958d176b6c4fe88fdbd7b7faa318eae07bbd186d4ec46
```

## Настоящие игровые скриншоты

[Все 128 F2](https://github.com/standimaoff-oss/aimods/tree/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986).

| Комплект | Спереди | Сзади |
|---|---|---|
| `ww2_su_infantry` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_infantry-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_infantry-back.png) |
| `ww2_su_officer` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_officer-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_officer-back.png) |
| `ww2_su_tanker` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_tanker-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_tanker-back.png) |
| `ww2_su_pilot` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_pilot-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_pilot-back.png) |
| `ww2_su_general` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_general-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_su_general-back.png) |
| `ww2_de_infantry` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_infantry-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_infantry-back.png) |
| `ww2_de_officer` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_officer-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_officer-back.png) |
| `ww2_de_tanker` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_tanker-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_tanker-back.png) |
| `ww2_de_pilot` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_pilot-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_pilot-back.png) |
| `ww2_de_general` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_general-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-ww2_de_general-back.png) |
| `nap_fr_infantry` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_infantry-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_infantry-back.png) |
| `nap_fr_officer` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_officer-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_officer-back.png) |
| `nap_fr_general` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_general-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_fr_general-back.png) |
| `nap_ri_infantry` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_infantry-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_infantry-back.png) |
| `nap_ri_officer` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_officer-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_officer-back.png) |
| `nap_ri_general` | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_general-front.png) | [F2](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-nap_ri_general-back.png) |

### Хват и проверка рендера

- [C96 у второго игрока, боковой вид](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-remote-c96-side-grip.png)
- [ТТ у второго игрока](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-remote-tt33-grip.png)
- [Леворукий ТТ](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-remote-tt33-left-handed.png)
- [ППШ у второго игрока, сбоку](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-remote-ppsh41-side-grip.png)
- [Мосин ПУ у второго игрока](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-remote-mosin_pu-grip.png)
- [ТТ: прицеливание в форме](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-grip-tt33-uniform-ads.png)
- [C96: вид от бедра в форме](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-grip-c96-uniform-hip.png)
- [Прицел ПУ](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-mosin_pu-02-aim.png)
- [Прицел ZF39](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-k98k_zf39-02-aim.png)
- [После загрузки ресурсов](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-resource-reload.png)
- [Приседание](https://github.com/standimaoff-oss/aimods/blob/4ef08f3ad1aacb5c9103aea1e14f0ee6dbe4449e/shots/aiarsenal/stage2/run-38744123986/stage2-uniform-crouching.png)

## Видео и звук

Без синтеза кадров и без лимитера/нормализации поверх записи. Native stereo, 48 kHz;
пик измерен по всем каналам без downmix. Эти метрики не заменяют субъективное прослушивание.

| Видео | Длительность, с | Peak | RMS |
|---|---:|---:|---:|
| [ppsh41.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/ppsh41.mp4) | 14.15 | 0.563 | 0.0341 |
| [mosin_pu.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/mosin_pu.mp4) | 15.63 | 0.356 | 0.0372 |
| [k98k_zf39.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/k98k_zf39.mp4) | 17.10 | 0.345 | 0.0352 |
| [c96.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/c96.mp4) | 42.90 | 0.293 | 0.0296 |
| [tt33.mp4](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/tt33.mp4) | 17.10 | 0.249 | 0.0035 |

## Установка, исходники и ограничения

1. Скопировать свой мир в резервную папку.
2. Заменить старый AI Arsenal JAR на этот на клиенте **и** сервере; не оставлять две версии.
3. Отдельный VolPyro устанавливать не требуется.

[Packed .blend](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/historical_uniforms.blend) ·
[SHA256SUMS](https://github.com/standimaoff-oss/aimods/releases/download/stage2-38744123986/SHA256SUMS) ·
[Резервная точка до этапа 2](https://github.com/standimaoff-oss/aimods/releases/tag/backup-before-stage2-20261015).

Проверка рендера выполнена на **llvmpipe**, не аппаратном GPU. FPS/высокий графический
пресет на пользовательском ПК не сертифицированы. Внешние shader packs/моды анимаций
не входят в проверенную конфигурацию. В main не слито; работа сохранена в
`arena/10158ad9-aimods`, PR #3 оставлен для пользовательской приёмки.
