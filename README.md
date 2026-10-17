# inq_hpold

HP-індикатори з прив'язкою до фактичних рядків штатної панелі World of Tanks 2.4.1.

## Архітектура
- Python 2.7: `python/gui/mods/mod_inq_hpold.py`, `python/gui/mods/inq_hpold_native/`.
- ActionScript 3: `as3/src_flash/src/InqHpoldPanel.as`, `as3/src_flash/src/inq/hpold/`.
- Власний `inq_hpold.swf` компілюється під час складання й включається безпосередньо у власний `.wotmod`.
- HP прив'язується до `playersPanel` через `getHolderByVehicleID` і `vehicleIcon/vehicleTF`, а не за статичними координатами Gameface.
- Окремого Python-ядра не потрібно.

## Важливо для збірки
`as3/libs/*.swc` відсутні в цьому репозиторії. Необхідно надати вихідні бібліотеки з іншого власного репозиторію через GitHub Actions secret `HPE_ACCESS_TOKEN` (токен лише з read-доступом до приватного `Dictor1488/HpE`) або додати SDK у `as3/libs` та змінити workflow на локальні бібліотеки.

Потім запустити GitHub Actions → **inq_hpold native AS3 test build** → Run workflow. При успішній компіляції файл буде доступний у Actions → Artifacts як `inq_hpold-native-0.2.0-alpha1`.

**Новий тестовий SWF/WOTMOD ще не зібраний.** Попередні RC2/RC3 залишаються Gameface-версіями з відомою проблемою позиціювання; для тесту нового AS3 потрібен саме артефакт 0.2.0-alpha1.
