# Hpold — integration status (WoT 2.4.1 target)

## Implemented in repository
- [x] Source-grounded Python HP callbacks from recovered `mod_playersPanelHP.py`.
- [x] Hook `PlayersPanel.updateVehicleHealth` and lifecycle `PlayerAvatar.__startGUI/__destroyGUI`.
- [x] Arena vehicle-killed event, ally/enemy selection via `IBattleSessionProvider`.
- [x] Exact three original HTML templates and bar width math, color-blind PNG selection.
- [x] Original Ctrl+hotkey and hold-Alt behavior.
- [x] Independent Scaleform injector and PlayerPanelsUI bridge implementing original `as_create/as_update/as_delete` protocol.
- [x] Game-independent build script for a standalone WOTMOD containing original 3KB visual injector (extracts it from user-supplied reference ZIP at *build time*) plus the four PNGs.
- [x] No Python import of oldskool/modsCore.

## Verification needed
- [ ] Test with WoT 2.4.1 client and inspect game.log (hook import paths/signatures).
- [ ] Confirm the original visual injector SWF can bind `PlayerPanelsUI` under the client's current Scaleform environment.
- [ ] Confirm layer positions, battle cleanup and full screen/hotkey behavior.
- [ ] Validate configuration handling and visual priority compared to vanilla HP.

**Unverified development build, not a stable release.** Source repo does not include the binary SWF directly; `build.py` extracts only that visual component from the provided reference archive and assembles the standalone WOTMOD.
