# -*- coding: utf-8 -*-
"""Standalone port of the recovered OldSkool PlayersPanelHP battle logic.

Uses native PlayersPanel.updateVehicleHealth (not arena polling) and original
HP templates. No imports of gui.oldskool/modsCore.
This module still needs a working Hpold UI adapter for visible output.
Python 2.7 / WoT client; client 2.4.1 integration is pending battle testing.
"""
import json
import math
import os
import traceback

try:
    import BigWorld
    import Keys
    import game
    from Avatar import PlayerAvatar
    from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
    from gui.Scaleform.daapi.view.meta.PlayersPanelMeta import PlayersPanelMeta
    from gui.battle_control import avatar_getter
    from helpers import dependency
    from skeletons.gui.battle_session import IBattleSessionProvider
    from skeletons.account_helpers.settings_core import ISettingsCore
    from account_helpers.settings_core.settings_constants import GRAPHICS
    from constants import ARENA_GUI_TYPE
    from gui.mods import hpold_bridge
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False

CONFIG_PATH = os.path.join('mods', 'configs', 'hpold', 'config.json')
DEFAULTS = {'enabled': True, 'displayState': 1, 'configVersion': 2,
            'switchModeHotKey': [Keys.KEY_F12] if IMPORTS_OK else [88]}


def log(message):
    print '[Hpold] %s' % message


def read_config():
    result = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, 'rb') as stream:
            parsed = json.load(stream)
        if isinstance(parsed, dict):
            result.update((key, parsed[key]) for key in DEFAULTS if key in parsed)
    except (IOError, TypeError, ValueError):
        pass
    return result


def override(klass, method_name, callback):
    """Safe native method wrapper; calls original exactly once."""
    original = getattr(klass, method_name, None)
    if original is None:
        log('hook missing: %s.%s' % (klass.__name__, method_name))
        return False
    if getattr(original, '_hpold_hook', False):
        return True
    def wrapped(*args, **kwargs):
        return callback(original, *args, **kwargs)
    wrapped._hpold_hook = True
    setattr(klass, method_name, wrapped)
    return True


class HPController(object):
    def __init__(self):
        self.config = read_config()
        self.hp = {}
        self.displayed = self.config.get('displayState', 1) == 0
        self.only_on_key = not self.displayed
        self.arena = None
        self.bridge = hpold_bridge.Bridge()
        self.enemy_image = 'hp_alive_r.png'
        try:
            if dependency.instance(ISettingsCore).getSetting(GRAPHICS.COLOR_BLIND):
                self.enemy_image = 'hp_alive_cb.png'
        except Exception:
            pass
        self.templates = {
            '1text': {
                'left': {'text': "<font face='$FieldFont' color='#FFFFFF' size='11'>%(curHealth)s/%(maxHealth)s</font>", 'align': 'center', 'x': 100, 'y': 3},
                'right': {'text': "<font face='$FieldFont' color='#FFFFFF' size='11'>%(curHealth)s/%(maxHealth)s</font>", 'align': 'center', 'x': -160, 'y': 3}},
            '2img': {
                'left': {'text': "<img src='img://gui/hpbars/hp_alive_l.png' width='%(barWidth)d' height='14'>", 'width': 72, 'align': 'left', 'x': 85, 'y': 3},
                'right': {'text': "<img src='img://gui/hpbars/" + self.enemy_image + "' width='%(barWidth)d' height='14'>", 'width': 72, 'align': 'left', 'x': -176, 'y': 3}},
            '3bg': {
                'left': {'text': "<img src='img://gui/hpbars/hp_bg.png' width='68' height='12'>", 'align': 'left', 'x': 86, 'y': 4},
                'right': {'text': "<img src='img://gui/hpbars/hp_bg.png' width='68' height='12'>", 'align': 'left', 'x': -175, 'y': 4}}
        }

    def special(self):
        arena = avatar_getter.getArena()
        if arena is None:
            return True
        modes = ('EPIC_BATTLE', 'EVENT_BATTLES', 'HALLOWEEN',
                 'EPIC_RANDOM', 'EPIC_RANDOM_TRAINING')
        return arena.guiType in tuple(getattr(ARENA_GUI_TYPE, name)
                                     for name in modes if hasattr(ARENA_GUI_TYPE, name))

    def start_gui(self):
        self.close_gui()
        avatar = BigWorld.player()
        self.arena = getattr(avatar, 'arena', None)
        if self.arena is not None:
            try:
                self.arena.onVehicleKilled += self.on_killed
            except Exception:
                log('arena.onVehicleKilled subscription failed')
        self.bridge.open(self.templates)
        if self.displayed:
            BigWorld.callback(1.0, self.refresh)

    def close_gui(self):
        if self.arena is not None:
            try:
                self.arena.onVehicleKilled -= self.on_killed
            except Exception:
                pass
        self.arena = None
        self.hp.clear()
        self.bridge.close()

    def on_killed(self, targetID, attackerID, equipmentID, reason, numVehiclesAffected):
        if targetID in self.hp and not self.special():
            self.hp[targetID]['current'] = 0
            self.render(targetID)

    def health_changed(self, vehicleID, newHealth, maxHealth):
        if self.special():
            return
        if maxHealth <= 0:
            return
        self.hp[vehicleID] = {'current': max(0, newHealth), 'max': maxHealth}
        self.render(vehicleID)

    def refresh(self):
        if self.arena is None:
            return
        for vehicleID in tuple(self.hp):
            self.render(vehicleID)

    def render(self, vehicleID):
        record = self.hp.get(vehicleID)
        if not record or record['max'] <= 0 or self.special():
            return
        try:
            provider = dependency.instance(IBattleSessionProvider)
            arenaDP = provider.getArenaDP()
            info = arenaDP.getVehicleInfo(vehicleID)
            if info is None or info.isObserver():
                return
            if arenaDP.isPlayerObserver():
                ally = avatar_getter.getPlayerTeam() == info.team
            else:
                ally = arenaDP.isAllyTeam(info.team)
            side = 'left' if ally else 'right'
            current = record['current']
            maximum = record['max']
            payload = {}
            for field_name, pair in sorted(self.templates.iteritems()):
                field = pair[side]
                width = current
                if 'width' in field:
                    width = int(math.ceil(field['width'] * float(current) / maximum))
                    width = max(0, min(field['width'], width))
                text = ''
                if self.displayed and current > 0:
                    text = field['text'] % {'curHealth': current,
                                            'maxHealth': maximum,
                                            'barWidth': width}
                payload['HPbars_' + field_name] = text
            self.bridge.update_vehicle(vehicleID, side, payload)
        except Exception:
            log('render error: %s' % traceback.format_exc())

    def redraw(self):
        for vehicleID in tuple(self.hp):
            self.render(vehicleID)

    def on_key(self, event):
        if self.special() or not self.config.get('enabled', True):
            return
        key = getattr(event, 'key', None)
        down = bool(event.isKeyDown())
        hotkey = self.config.get('switchModeHotKey', [Keys.KEY_F12])
        # Original hotkey requires Ctrl; F12 by default, configurable.
        try:
            modifier_down = (BigWorld.isKeyDown(Keys.KEY_LCONTROL) or
                             BigWorld.isKeyDown(Keys.KEY_RCONTROL))
        except Exception:
            modifier_down = False
        if down and key in hotkey and modifier_down:
            self.only_on_key = not self.only_on_key
            self.displayed = not self.only_on_key
            self.redraw()
        elif self.only_on_key and key in (Keys.KEY_LALT, getattr(Keys, 'KEY_RALT', -1)):
            self.displayed = down
            self.redraw()


controller = HPController() if IMPORTS_OK else None


def install():
    if controller is None:
        print '[Hpold] Missing WoT client modules; initialization skipped'
        return
    if not controller.config.get('enabled', True):
        return

    def update_health(original, panel, vehicleID, newHealth, maxHealth):
        result = original(panel, vehicleID, newHealth, maxHealth)
        controller.health_changed(vehicleID, newHealth, maxHealth)
        return result

    def start_gui(original, avatar, *args, **kwargs):
        result = original(avatar, *args, **kwargs)
        controller.start_gui()
        return result

    def destroy_gui(original, avatar, *args, **kwargs):
        try:
            controller.close_gui()
        finally:
            return original(avatar, *args, **kwargs)

    def key_event(original, event, *args, **kwargs):
        result = original(event, *args, **kwargs)
        controller.on_key(event)
        return result

    override(PlayersPanel, 'updateVehicleHealth', update_health)
    override(PlayerAvatar, '_PlayerAvatar__startGUI', start_gui)
    override(PlayerAvatar, '_PlayerAvatar__destroyGUI', destroy_gui)
    override(game, 'handleKeyEvent', key_event)
    # Deliberately do not suppress vanilla HP bars until the custom UI renders.
    log('battle hooks installed')


install()
