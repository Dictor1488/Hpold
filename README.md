# Hpold

Автономний порт OldSkool PlayersPanelHP 1.2.4 для World of Tanks **2.4.1**. Жодних імпортів `modsCore` у бойовому коді.

## Структура
- `res/scripts/client/gui/mods/mod_hpold.py` — оригінальна логіка HP, hotkey, кеш, battle lifecycle.
- `res/scripts/client/gui/mods/hpold_bridge.py` — самостійна Scaleform DAAPI інтеграція.
- `hpbars/*.png` — чотири оригінальні іконки HP.
- `build.py` — повторювана збірка з перевіркою вмісту архіву.
- `mods/configs/hpold/config.json` — приклад конфігурації.

## Build
Знадобиться Python **3.8+** лише для збірки і вихідний `playersPanelHP_1.2.4.zip` (тільки **на етапі збірки**). Жоден Python-модуль старого ядра не потрапляє у вихідний файл.

```bash
python build.py --reference playersPanelHP_1.2.4.zip --check
python build.py --reference playersPanelHP_1.2.4.zip
```

Результат: `dist/hpold_0.1.0-rc1.wotmod`. Перенести його в `mods/2.4.1.0/`. За потреби приклад конфігурації окремо скопіювати в `mods/configs/hpold/config.json`.

SWF-компонент `playersPanelAPI_modsCore.swf` фізично входить у WOTMOD; під час гри **окремого modsCore не потрібно**. Він залишається старим Flash-ресурсом, тому сумісність з 2.4.1 потребує перевірки.

## Управління
Ctrl + налаштована кнопка перемикає постійний показ / показ при натиснутому Alt. У репозиторному прикладі конфігурації кнопка `X` (keycode 88). Без зовнішнього JSON fallback — Ctrl+F12 за оригінальним кодом.

## Статус
**Release candidate (RC), не stable.** Збірка перевіряє файли, але не може замінити запуск в реальному клієнті: потрібні `game.log`, скріншот бойової панелі, перевірка Ctrl+X, Alt, початку/кінця бою. Не встановлювати разом зі старим PlayersPanelHP/modsCore, щоб уникнути дублювання елементів.