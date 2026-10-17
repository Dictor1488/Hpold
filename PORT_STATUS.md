# Hpold — стан перенесення

## Відновлено з `mod_playersPanelHP.py`
- [x] Обробник `PlayersPanel.updateVehicleHealth(vehicleID,newHealth,maxHealth)` як джерело HP.
- [x] Кеш HP та `arena.onVehicleKilled` для обнулення HP.
- [x] Визначення ally/enemy за `IBattleSessionProvider.getArenaDP()`.
- [x] Оригінальні HTML-шаблони для `1text`, `2img`, `3bg`, з координатами та адресами PNG.
- [x] Ширина активної шкали `ceil(72 * current / max)` (оригінальний HTML-розмір 72).
- [x] Режим постійного показу або показу через Alt; Ctrl + налаштована клавіша перемикає режим.
- [x] Прямі Python-обгортки (без `gui.oldskool`/modsCore) для battle lifecycle і HP.
- [x] Відокремлений renderer contract `hpold_bridge.register_renderer(renderer)`.

## Не завершено
- [ ] Підключити перенесений користувачем UI до `register_renderer`; потрібен об'єкт з методами `create_field(name, definition)`, `update_field(name,vehicleID,text)`. Без цього HP обчислюється, але НЕ малюється.
- [ ] Перевірити точні сигнатури й наявність викликів у клієнті World of Tanks 2.4.1.
- [ ] Перевірити реальне малювання, щільність рядків панелей, помилки game.log, режим Alt, повторний бій.
- [ ] Перенести PNG-ресурси в репозиторій/пакет із відповідними шляхами.

Це **інтеграційна версія, не реліз**. Джерело — декомпільований оригінальний `mod_playersPanelHP.py`; стара спроба polling HP видалена.
