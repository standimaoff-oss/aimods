# Ответ 8 — бронетехника и РСЗО Второй мировой (фото → photos/2/)
Пользователь (сообщение r8): «танки второй мировой, А ТАКЖЕ Штурмтигр, БМ-13, Маус, Бисмарк — реальные размеры,
максимально точно, все виды вооружения у Бисмарка».
Решение по разбиению: r8 = 11 сухопутных машин (ниже). r9 = «Бисмарк» отдельно (251 м, все батареи: 8×380, 12×150,
16×105 Flak, 16×37, 20 мм, палуба проходима) — это отдельный корабельный класс + огромная модель.
r10 = авиация ВМВ (He 111, Ju 87, Bf 109, Fw 190; Пе-8, Пе-2, Як-3, Ла-5ФН). r11–12 = современный список.

## Машины r8 (GunVehicle; новые VehicleKind ТОЛЬКО в конец enum; Ballistics.Profile только в конец)
| id | машина | L корпус / с пушкой, W, H (м) | масса | мощн. | v км/ч | вооружение | углы |
|---|---|---|---|---|---|---|---|
| pz2 | Pz.Kpfw. II Ausf. F | 4.81, 2.28, 2.15 | 9.5 т | 103 кВт | 40 | 2 cm KwK 30 (180), MG34 | −9.5..+20 |
| pz4 | Pz.Kpfw. IV Ausf. H | 5.92/7.02, 2.88 (3.29 экраны), 2.68 | 25 т | 221 кВт | 38 | 7.5 cm KwK 40 L/48 (87) | −8..+20 |
| tiger | Tiger I Ausf. E | 6.316/8.45, 3.56 (3.705), 3.0 | 57 т | 515 кВт | 45 | 8.8 cm KwK 36 L/56 (92) | −9..+10 |
| sturmtiger | Sturmtiger | 6.28, 3.57, 2.85 | 65 т | 515 кВт | 40 | 38 cm RW 61 ракетомортира (14) | ±10 гориз., 0..+85 |
| maus | Pz.Kpfw. VIII Maus | 9.03/10.09, 3.67, 3.63 | 188 т | 883 кВт | 20 | 12.8 cm KwK 44 L/55 (32) + 7.5 cm KwK 44 спарка (200) | −7..+23 |
| ratte | Landkreuzer P.1000 Ratte | 35, 14, 11 | 1000 т | 2×MAN V12Z32/44 = 12.5 МВт | 40 | 2×28 cm SK C/34 (баш. Gneisenau), 12.8 cm KwK 44 (корм.), 8×2 cm Flak 38 | −5..+40 |
| t34 | Т-34-85 (1944) | 6.1/8.15, 3.0, 2.72 | 32 т | 368 кВт | 55 | 85 мм ЗиС-С-53 (55) | −5..+22 |
| kv2 | КВ-2 | 6.95, 3.32, 3.24 | 52 т | 441 кВт | 34 | 152 мм М-10Т (36) | −3..+18 |
| is2 | ИС-2 (1944) | 6.77/9.9, 3.07, 2.73 | 46 т | 382 кВт | 37 | 122 мм Д-25Т (28), разд. заряжание | −3..+20 |
| kv5 | КВ-5 (Объект 225, сверхтяжёлый проект 1941) | 8.9, 4.0, 3.3 | 100 т | 2×В-2СН 883 кВт | 40 | 107 мм ЗиС-6 | −5..+15 |
| bm13 | БМ-13Н «Катюша» на Studebaker US6 | 6.55, 2.24, 2.9 | 7.2 т | 71 кВт | 70 | 16× М-13 132 мм | ±10 гориз., +4..+45 |

## Боеприпасы (новые предметы, вкладка «Боеприпасы»)
shells_20 (2 cm Sprgr), shells_75 (7.5 cm Sprgr 34 / Pzgr 39), shells_88 (8.8 cm Sprgr / Pzgr 39), shells_85 (О-365 / БР-365),
shells_107 (ОФ-420), shells_128 (12.8 cm Sprgr), shells_280 (28 cm Sprgr L/4.4 330 кг), rocket_380 (38 cm R-Sprgr 4581, 345 кг, 135 кг ВВ),
rocket_m13 (М-13 132 мм, 42.5 кг, ВВ 4.9 кг). КВ-2 → shells_152 (как «Мста»), ИС-2 → shells_122 (как Д-30).
Баллистика: 2cm 0.148 кг 780 м/с; 75 мм HE 5.74 кг 550, AP 6.8 кг 790; 88 HE 9.5 кг 820, AP 10.2 кг 773; 85 HE 9.5 кг 793, AP 9.2 кг 792;
107 HE 18.8 кг 830; 128 HE 28 кг 750, AP 28.3 кг 920; 280 HE 315 кг 890; RW61 345 кг ~300 м/с (тяга: мотор); М-13 42.5 кг, 355 м/с макс.
152 М-10Т — 40 кг 436 м/с (свой профиль KV2_HE); 122 Д-25Т HE 25 кг 800 м/с, AP 25 кг 795 (IS2_HE / IS2_AP).

## Конвейер (как r4/r5)
- Blender: tools/rwveh/<id>.py на armor_lib (+ ww2_lib.py для общих деталей: литые/сварные корпуса, шахматные катки, Кристи,
  экраны, циммерит) → raw GLB в .cache/rwveh/raw → auto_attach + floatcheck → glb_quant → assets/.../models/glb/<id>.glb
  + make_lod → <id>_lod1.glb. Узлы как у T-90M: root, rw_L_i/rw_R_i, spk_*, idl_*, rr_*, track_L/R, launcher_yaw > launcher_pitch > barrel.
- Java: Specs, VehicleKind (append), GunVehicle.cfg, ModEntities, ModItems (+ammo), VehicleItem, ModTabs, ClientModEvents,
  рецепты, модели предметов, lang en/ru (tools/lang/lang_r8.py), иконки (icons.py), DeckShapes (gen_decks.py), камера.
- Тесты: каждая машина спавнится/едет/стреляет (GunTests), BM-13 залп, Штурмтигр — ракета взрывается.
- Фото: photos/2/ — новые машины в игре.

## Java решения (зафиксировано по ходу r8)
- GunVehicle: режимы sel = [primary, secondary?, coax-MG?]; nModes = 1 + (sec!=null) + (coax). coaxSelected = coax && sel==nModes-1
  (BMP-3/T-90 совместимо). Пулемёт из tubes[last]. Маус: secondary 7.5 cm из tubes[1]. Ратте: 2×28 cm попеременно tubes[0]/[1],
  пулемёт MG 151/15 — tubes[2]. Штурмтигр: primary RW61 = ракетный профиль (mp>0) -> RocketEntity.launch вместо ShellEntity.
  WW2 coax roundKey = "coax_mg", coaxCd = 2. `big`-звук: tiger/maus/ratte/kv2/is2/kv5/sturmtiger.
- Ballistics: isShell() = mp <= 0 (а не ordinal). Новые профили в конец: KW20_HE/AP, K75_HE/AP, K88_HE/AP, S85_HE/AP, S107_HE,
  K128_HE/AP, K75S_HE (7.5 KwK 44 Мауса), SK280_HE, KV2_HE, IS2_HE/AP, RW61 (ракета), M13 (ракета).
- BM-13 = MlrsEntity (как Град): узлы wheel_0..5, steering_wheel, launcher_yaw/pitch, jack_0/1, plug_0..15, rocket_load;
  VehicleKind.isGun() исключает BM13; profile()/ammoItem()/звук по kind.
- Модели: ww2_lib.py (chull для наклонной брони, ww2_gear с шахматными катками, belt_path теперь умеет провис на катки).

## Статус (конец ответа 8)
- ГОТОВО: 11 машин (модели, LOD, Java, тесты 98/98, фото photos/2, отчёт, src zip, SHA256SUMS).
- GLB хранятся только в jar: перед правкой ассетов `tools/glb_stash.sh restore`, в конце хода `strip` (build.sh делает restore сам).
- Следующий ответ 9: «Бисмарк» (251 м): 4 башни 2×380 (Anton/Bruno/Caesar/Dora), 6×2×150, 8×2×105 Flak, 8×2×37, 2 см Flak,
  Arado 196, проходимая палуба (DeckShapes с c≈4–5 м, как подлодка 74 м), BoatEntity-физика.
