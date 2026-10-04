# r19 — рация / удары + 6 комплектов формы

## Удары (StrikeType, append-only)
| id | что | носитель | боеприпас | КД (с) |
|----|-----|----------|-----------|--------|
| ARTILLERY | 3 залпа батареи 2С19 «Мста-С» (6×152 мм) | — | ShellEntity MSTA_HE | 60 |
| FAB500 | ковёр: звено 4×Су-34, по 8 ФАБ-500 | Су-34 (новая модель) | AirBombType.FAB500 | 180 |
| FAB1000 | ковёр: пара Су-34, по 4 ФАБ-1000 | Су-34 | AirBombType.FAB1000 | 240 |
| FAB5000 | 1×ФАБ-5000 | Ту-95МС (tu95ms.glb, створки) | AirBombType.FAB5000 | 400 |
| NUCLEAR | свободнопадающая ЯБ (РДС-1 22 кт): воздушный подрыв ИЛИ по пульту | Ту-160 (tu160.glb, стреловидность 65°) | arsenal NukeEntity | 1200, в выживании тратит предмет rds1 |

* Рация Р-187П1 «Азарт» (`radio`): ПКМ → RadioScreen: тип удара, цель (карта MapScreen 5×5 км / прицел / целеуказатель), заход
  (от меня / по взгляду), взрыватель для ЯБ. Пакет StrikeRequestPacket → StrikeManager (сервер).
* StrikeManager: виртуальные траектории самолётов и бомб (работает и в незагруженных чанках), видимая сущность StrikePlaneEntity
  создаётся только в entity-ticking чанках; бомба становится реальной AirBombEntity / NukeEntity при входе в загруженную зону.
  Тикет чанков вокруг цели (TicketType с таймаутом, не сохраняется).
* Точка сброса = цель − вынос (численная интеграция той же физики, что у AirBombEntity / NukeEntity).
* Самолёты: реальные скорости (Су-34 160 м/с, Ту-95 150, Ту-160 230), высота над целью 180 / 250 / 320 м, после сброса — набор.

## Форма (6 комплектов × 4 = 24 предмета)
su_afghan (афганка), su_tanker (комбинезон+шлемофон), us_vietnam (OG-107 + M1), us_desert (DCU + PASGT),
ru_vdv (тельняшка+голубой берет+«горка»), ru_pilot (летный комбинезон + ЗШ). Blender `tools/blender/uniforms.py` (добавить),
текстуры `uniform_textures.py`, предметы/рецепты/язык `tools/gen_uniforms_r19.py`.

## Модель
Су-34 (`tools/rwveh/su34.py`, Blender, по чертежам: L 23.34, размах 14.7, H 6.09): «утконос», кабина бок-о-бок, ПГО, два киля,
хвостовой «жало» с РЛС, 12 точек; узлы fab500_0..7, fab1000_0..3, bay/gear не нужны (только полёт) — шасси убрано.

## r19 B/C (delivered)
* B: SelectWeaponPacket (hotbar keys consumed at ClientTick START), ActionBar chips, tank smoke (B key, SmokeScreen server clouds).
* C: Armour.java (tables/ammo/solve/spall/travel), VehicleDamage.armoured + Cam, HitCamPacket, client HitCam (GLB X-ray + module voxels).
* Test tool: /realwar shot <shooter> <target> <ammo> [lx ly lz]. Tests 136/136 (PenetrationTests).
* Next: roadmap Step 3 (weather/NV/thermal, body armour + helmets, WW2 RKKA/Wehrmacht uniforms, player weapons).
