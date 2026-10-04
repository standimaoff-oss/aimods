# План r22 (запрос после r21)

## Что просил пользователь
1. Полоса действий (B Z K M R X) — в ТОЙ ЖЕ нижней строке сразу после слотов снарядов, как в War Thunder (фото uploads/maxresdefault (32).jpg),
   никакого второго ряда. Сами квадраты меньше, чтобы всё влезало.
2. Перезарядка: после выстрела выбранный слот снаряда становится серым, серость убывает по кругу (как часы) до конца перезарядки.
3. Оружие игрока: часть списка (1/3–1/4), ДЕТАЛЬНО ПО РЕАЛЬНЫМ ЧЕРТЕЖАМ (раньше было плохо).
   Выбрано 3 из 13 (~1/4): **АК-12 (6П70, 2018)**, **M4A1 (+ Aimpoint CompM4)**, **РПГ-7В2 (+ ПГО-7В3, ПГ-7ВЛ)**.
   Игла/Javelin остаются старыми (переделка — позже), остальное из списка — позже.
4. Бронежилеты/каски/форма ВОВ — переносятся на следующий ответ (r23).

## Реализация
### HUD
- ActionBar: один ряд [ammo slots][action tiles], tile size адаптивный (уменьшается, пока ряд не влезет между картой и карточкой).
- Reload wipe: ammo slot of the selected round: grey overlay pie, angle = remaining/total, clockwise shrink.

### Оружие (realwar/handheld/…)
- GunKind enum: AK12 (5.45, 30, 700 rpm, 900 m/s, single/auto), M4A1 (5.56, 30, 800 rpm, 880 m/s, semi/auto).
- RifleItem: NBT ammo, mode; server fire loop by trigger packet; reload consumes magazine item (mag_545_ak12 / mag_stanag).
- Bullets: reuse existing bullet entity if any (VehicleHit-aware); else hitscan with drop.
- FP render: own RenderHandEvent: weapon GLB + vanilla arms, sway/bob, recoil kick, ADS (sight on axis), reload anim (mag node out/in, bolt).
- 3rd person: two-handed pose (CROSSBOW_HOLD / BOW).
- Keys: LMB fire, RMB aim, R reload (KEY_RELOAD), B fire mode (KEY_BRAKE on foot).
- HUD: ammo counter + mode.
- Recipes in workbench (gun + mags), lang en/ru, creative tab.
- RPG-7: new detailed GLB, keep LauncherWeaponItem logic; FP arms + reload anim.

### Модели (Blender, tools/blender/weapons_r22.py) — реальные размеры
- AK-12 6P70: L 945 (stock ext), barrel 415, rail on cover, 6L31 mag, muzzle device, 4-pos telescoping folding stock.
- M4A1: L 838/757, barrel 368 (14.5"), flat-top, A2 FSB, M4 handguard, 6-pos stock, STANAG, A2 birdcage, CompM4.
- RPG-7V2: tube 950 mm 40 mm, venturi, 2 heat shields, grips, PGO-7V3 left, PG-7VL (93 mm head) loaded.
- Nodes: mag, bolt/charging, selector, trigger, (rpg: grenade) for animation.

## r22e (после сброса песочницы)
- Снимок превысил 128 МБ → все НОВЫЕ java/ресурсы r22 потерялись (src откатился к r21). Восстановлено заново:
  GunKind / FirearmItem / MagazineItem / Firearms (+пули), GunActionPacket / GunFxPacket, GunClient (ввод, ADS, отдача,
  HUD, Aimpoint, ПГО-7В3), GunRenderer (FP + BEWLR), HandheldView.raw + override config/aiarsenal_view.json,
  ModItems/ModTabs/ModSounds, item models, recipes (+refill), lang, sounds.json, SmallArmsTests (140/140).
- Текстуры tools/blender/tex_r22 извлечены из models/weapons_r22.blend; GLB пересобраны weapons_r22.py.
- WtHud: пирог перезарядки танка = клиентский таймер fireInterval (fireCd сервера не синхронизирован).
- ПРАВИЛО: в конце КАЖДОГО ответа glb_stash strip + logs без картинок, держать workspace < 110 МБ.

## r22g/h — СДАНО
- Панель оружия в стиле WT-слотов (WtHud.drawSlots + ActionBar.gun R/B), строка инфо не обрезается (left-align в полосе).
- ПГО: дальномер в левом верхнем поле. Gametest 140/140. Фото photos/15/03–09 пересняты.
