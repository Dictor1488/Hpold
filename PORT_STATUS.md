# Hpold port status

- [x] Репозиторій ініціалізований.
- [x] Визначено оригінальні PNG і поля конфігурації.
- [x] Створено власний Python entry point і відокремлений bridge (без import oldskool).
- [ ] Достовірно відновити захищену логіку `mod_playersPanelHP.pyc`.
- [ ] Під'єднати власний SWF з повною прив'язкою до рядків панелей.
- [ ] Перевірити й скоригувати виклики WoT 2.4.1 у реальному клієнті.
- [ ] Перевірити HP, режими панелей, клавішу X, повторний вхід у бій та replay.

Поки що **це кодова основа, НЕ робочий реліз**. Не повідомляти про сумісність із WoT 2.4.1 до тесту з game.log.

## 2026-10-17 — forensic bytecode inspection
Received standalone original `mod_playersPanelHP.pyc` (45,513 bytes, Python 2.7 magic `03 f3 0d 0a`). Static Python 3 marshal reader successfully parsed all 45,505 bytes after the 8-byte pyc header without execution. The outer code object is `<pjorion_protected>`, with `co_filename=b'mod_playersPanelHP'` and 45,167 bytes of protected `co_code`. Constants are `(-1, None, b'', 1, 2, 8, b'0')`. The file DOES NOT yet expose original HP callbacks: inner payload remains protected/encrypted. See `tools/inspect_py27_pyc.py` for repeatable static examination.

Warning: Python 2.7 and the separately referenced `deobfuscate_protected.py` are unavailable in this sandbox; pip installation failed because package index DNS/network is unavailable. Existing mod_hpold.py remains an untested scaffold, not faithfully reconstructed logic.
