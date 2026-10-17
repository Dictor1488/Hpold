# inq_hpold

Незалежний мод індикаторів HP для панелей команд World of Tanks 2.4.1.

## Файли
- `res/scripts/client/gui/mods/mod_inq_hpold.py` — бойова логіка HP.
- `res/scripts/client/gui/mods/inq_hpold_ui.py` — інтерфейсний адаптер.
- `hpbars/*.png` — зображення індикаторів.
- `assets/inq_hpold.swf` — **потрібний власний UI-компонент** (поки відсутній).
- `mods/configs/inq_hpold/config.json` — конфігурація.

## Збірка
```bash
python -m unittest discover -s tests -v
python build.py --check
python build.py
```

Готовий файл: `dist/inq_hpold_0.1.0-rc1.wotmod`. Збірка не використовує інші моди, архіви або мережеві завантаження. Якщо немає `assets/inq_hpold.swf`, збірка зупиняється з поясненням помилки.

**Стан:** UI-компонент ще необхідно створити та перевірити в клієнті 2.4.1, тому працездатний реліз наразі не підтверджений.
