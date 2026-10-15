# Photon: ограниченная проверка совместимости — PASS

[Успешный CI](https://github.com/standimaoff-oss/aimods/actions/runs/38798168717), исходники `5c6ef4bc098575044d71cc3e61c638c945095c6f`.

Установленный JAR: `aiarsenal-1.0.1-alpha.10.jar`, SHA-256
`8eaef8fff814804a5fcaf389a6d91235f702802647ca4bba005a8b1a72ac421b`.

## Точная конфигурация

Forge 47.4.23, Oculus 1.8.0, Embeddium 0.3.31, Photon 1.3b; Linux llvmpipe.
[Файлы поставщиков, SHA-512 и настройка](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/shaderpack/run-38798168717/shaderpack-provenance.json).
ZIP Photon не редактировался; публичная настройка **SH_SKYLIGHT=false** необходима из-за лимита
32768 байт compute shared memory стенда. Стандартный пресет требует 36860 байт и здесь не запускается.
**Это не проверка Windows/NVIDIA, аппаратного FPS или стандартного пресета Photon.**

## Выполнено

- Настоящие R, ПКМ и ЛКМ для PPSh-41, Мосина ПУ и мушкета 1777. Дождались полного заряжания;
  выстрел подтверждён уменьшением Ammo на настоящем сервере.
- Привязки Oculus не менялись. Нажатие R также действительно перезагружало шейдеры.
- Маска прицела Мосина: контрольная область вне оптики полностью чёрная (`black=1.000`).
- Обычный, ядерный и legacy-ядерный визуальные пакеты с активным Photon.
  Это проверка отображения и стабильности, **не** замена физических взрывов из отдельного каталожного прогона.
- Два цикла K: выключение → возврат собственного объёмного рендера → включение → прекращение собственных GL-проходов.
  При включённом Photon счётчики raw-кадров не изменялись: **45 → 45**, затем **83 → 83**.
- На каждом выключении Photon: три враждебных pixel-unpack состояния, настоящий upload 64×64,
  отсутствие GL-ошибки и точное восстановление состояния вызывающего кода — PASS.

[Машинный результат](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/shaderpack/run-38798168717/shaderpack-gameplay.json), [клиентский журнал](https://github.com/standimaoff-oss/aimods/blob/4be7c6b9586dd2a761bd425b75d348ab47c245b5/reports/shaderpack/run-38798168717/client.log).

## Просмотренные оригиналы F2

Из 11 кадров вручную просмотрены следующие четыре (не заявляется просмотр всех кадров):

- [Мосин ПУ, ADS с Photon](https://github.com/standimaoff-oss/aimods/blob/204887f/shots/aiarsenal/shaderpack/run-38798168717/shaderpack-photon-mosin_pu-ads.png): круг оптики и сетка видны, внешняя маска чёрная, мир отображается внутри.
- [Мушкет, ADS с Photon](https://github.com/standimaoff-oss/aimods/blob/204887f/shots/aiarsenal/shaderpack/run-38798168717/shaderpack-photon-musket_1777-ads.png): модель и руки отображаются.
- [Ядерный fallback с Photon](https://github.com/standimaoff-oss/aimods/blob/204887f/shots/aiarsenal/shaderpack/run-38798168717/shaderpack-photon-fallback-nuke.png): кадр яркой вспышки; полный внешний силуэт облака по нему не оценивается.
- [После отключения Photon](https://github.com/standimaoff-oss/aimods/blob/204887f/shots/aiarsenal/shaderpack/run-38798168717/shaderpack-photon-disabled-0.png): игровой мир и облако остаются видимыми, процесс работает. Сам факт возврата raw-рендера подтверждён отдельно счётчиком кадров.

[Все оригиналы](https://github.com/standimaoff-oss/aimods/tree/204887f/shots/aiarsenal/shaderpack/run-38798168717).

Этот PASS относится только к перечисленным сценариям. Он не закрывает весь аудит мода и не подтверждает причину присланного native NVIDIA crash.
