# inq_hpold

Незалежний мод HP-індикаторів у панелях команд World of Tanks 2.4.1.

## Файли
- `res/scripts/client/gui/mods/mod_inq_hpold.py` — збір даних HP, режими відображення й обробка клавіш.
- `res/scripts/client/gui/mods/inq_hpold_ui.py` — Wulf/Gameface view і передавання стану.
- `res/gui/gameface/mods/inq_hpold/panel/Panel.html`, `Panel.css`, `Panel.js` — візуал шкал.
- `res/gui/gen_resources/tv.inq.hpold.json` — Gameface layout.
- `hpbars/*.png` — графічні елементи.
- `mods/configs/inq_hpold/config.json` — конфігурація.

## Збірка
```bash
python -m unittest discover -s tests -v
python build.py --check
python build.py --python27 C:/Python27/python.exe
```

Результат: `build/inq_hpold_0.1.0-rc2.wotmod`. Для білда потрібен лише Python 3.8+.

## Важливо
Це **дослідна Gameface-збірка**, ще не стабільний реліз. Точне позиціювання поверх штатних панелей, завантаження layout і сигнатури клієнта мають бути перевірені у грі. Gameface layout тепер знаходиться через штатний `gui.impl.gen.R`, без імпорту зовнішньої бібліотеки. Потрібно перевірити реєстрацію ресурсу в клієнті 2.4.1. Немає SWF, але твердження про повну runtime-незалежність поки передчасне.
