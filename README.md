# Hpold — standalone PlayersPanel HP bars

Independent port of the recovered OldSkool `playersPanelHP 1.2.4` source, targeting World of Tanks **2.4.1**.

## Implementation
- `res/scripts/client/gui/mods/mod_hpold.py`: original HP updates, kill events, team selection, label/bar/background, colorblind handling, keyboard modes, start/stop.
- `res/scripts/client/gui/mods/hpold_bridge.py`: private Scaleform interface, cache + `PlayerPanelsUI` + view injector. No `gui.oldskool` dependency.
- `hpbars/*.png`: all four user-supplied original images.
- `mods/configs/hpold/config.json`: settings.
- `build.py`: creates independent installable .wotmod.

## Build
Have Python 3 installed on your computer (only needed for packaging) and place the original `playersPanelHP_1.2.4.zip` nearby. From the repository directory run:

```bash
python build.py --reference playersPanelHP_1.2.4.zip --version 2.4.1.0 --output hpold_0.1.0.wotmod
```

Copy `hpold_0.1.0.wotmod` into `mods/2.4.1.0/` in the game folder. The builder uses only `playersPanelAPI_modsCore.swf` from the old reference archive; it does **not** include the core Python code, blacklists, network checks or other oldskool modules. The original UI injector binary remains part of this build; a fully new SWF has not been rewritten.

Controls follow original source: **Ctrl + configured hotkey** changes between permanent and Alt-held mode; while in Alt-held mode, hold **Alt** to show the bars. Existing `config.json` has hotkey 88 (X); original hardcoded fallback is F12.

**Status:** Integration build only. It has not been tested inside the WoT 2.4.1 client. See `PORT_STATUS.md`.
