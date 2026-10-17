# Hpold — standalone HP panel port

Порт бойової логіки з декомпільованого `mod_playersPanelHP.py` (OldSkool PlayersPanelHP v1.2.4) без залежностей від `modsCore`.

## Реалізована Python-логіка
- Hook `PlayersPanel.updateVehicleHealth` для отримання `vehicleID, newHealth, maxHealth`.
- Очищення HP при `arena.onVehicleKilled`; очищення кешу після бою.
- Вибір left/right на підставі `IBattleSessionProvider.getArenaDP()`.
- Три оригінальні HTML-поля на техніку: `1text`, `2img`, `3bg`; оригінальні координати і PNG.
- Обчислення ширини `ceil(width * currentHP / maxHP)`, приховування при 0 HP.
- Режими постійного показу та утримання Alt; перемикання Ctrl + hotkey.
- Колір для дальтонізму (cb) з системних графічних налаштувань.

## Підключення незалежного UI
`res/scripts/client/gui/mods/hpold_bridge.py` надає:
```python
from gui.mods.hpold_bridge import register_renderer
register_renderer(your_renderer)
```
Адаптер `your_renderer` має реалізувати `create_field(name, definition)` і `update_field(name, vehicleID, text)`, за потреби `close()`.

**Без реального renderer/UI-адаптера шкали не з'являться.** Існуючий код не імпортує `gui.oldskool` і не використовує `playersPanelAPI_modsCore.swf`.

## Стан
Це інтеграційна основа. Перед релізом перевірити сигнатури у WoT 2.4.1, додати графічні ресурси `gui/hpbars`, зв'язати перенесений користувачем інтерфейс з bridge та протестувати бойовий `game.log`. Див. `PORT_STATUS.md`.
