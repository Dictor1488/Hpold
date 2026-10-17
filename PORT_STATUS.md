# Release readiness: Hpold 0.1.0-rc1

## Implemented
- [x] Реальна логіка HP відновлена з `mod_playersPanelHP.py` і використовується замість ненадійного polling.
- [x] Окремий bridge Scaleform `PlayerPanelsAPIInjector` / `PlayerPanelsUI` з оригінальними linkage-іменами.
- [x] Збережено три поля HTML, зображення, обробку HP=0, colorblind-варіант, вибір панелі, Ctrl+hotkey і Alt.
- [x] Жодної runtime-залежності від `gui.oldskool` або ядра.
- [x] Детермінований build та валідація ZIP і ресурсів.
- [x] Вилучено старий helper декомпіляції з репозиторію.

## Remaining release gates
- [ ] Повна перевірка викликів у WoT 2.4.1.
- [ ] Тест того, що SWF з версії 2.4.0.0 відкривається та показує дані.
- [ ] Тест заповнення смуг, обнулення HP, режимів Alt/гарячої клавіші, зміни типу панелі, colorblind.
- [ ] Відсутність Python/Scaleform traceback у game.log.
- [ ] Створення фінального тега та GitHub Release **лише після** цих тестів.

Репозиторій має RC-білд-скрипт, але автоматична перевірка архіву не доводить працездатності в клієнті.
