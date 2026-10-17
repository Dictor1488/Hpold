# -*- coding: utf-8 -*-
"""Hpold - independent WoT HP panels data source (Python 2.7).
No dependencies on oldskool/modsCore. Experimental until battle testing.
"""
import json
import os
import traceback

try:
    import BigWorld
    import Keys
except ImportError:
    BigWorld = None
    Keys = None

DEFAULTS = {
    'enabled': True,
    'switchModeHotKey': [88],
    'displayState': 0,
    'configVersion': 2,
    'pollInterval': 0.2
}
CONFIG_PATH = os.path.join('mods', 'configs', 'hpold', 'config.json')


def log(message):
    try:
        print '[Hpold] %s' % message
    except Exception:
        pass


def read_config():
    data = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, 'rb') as stream:
            value = json.load(stream)
        if isinstance(value, dict):
            for key in DEFAULTS:
                if key in value:
                    data[key] = value[key]
    except (IOError, ValueError, TypeError):
        pass
    return data


class HpoldController(object):
    def __init__(self):
        self.config = read_config()
        self.running = False
        self.tick_id = None
        self._snapshot = {}
        self._mode = int(self.config.get('displayState', 0))
        self._input_registered = False
        self._bridge = None

    def start(self):
        if self.running or not self.config.get('enabled', True):
            return
        self.running = True
        self._snapshot.clear()
        self._register_input()
        self._connect_bridge()
        self._tick()
        log('battle start')

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.tick_id is not None:
            try:
                BigWorld.cancelCallback(self.tick_id)
            except Exception:
                pass
            self.tick_id = None
        self._unregister_input()
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None
        self._snapshot.clear()
        log('battle stop')

    def _register_input(self):
        try:
            from gui import InputHandler
            InputHandler.g_instance.onKeyDown += self._on_key_down
            self._input_registered = True
        except Exception:
            log('key event registration unavailable')

    def _unregister_input(self):
        if not self._input_registered:
            return
        try:
            from gui import InputHandler
            InputHandler.g_instance.onKeyDown -= self._on_key_down
        except Exception:
            pass
        self._input_registered = False

    def _on_key_down(self, event):
        try:
            key = getattr(event, 'key', None)
            if key is None and hasattr(event, 'keyCode'):
                key = event.keyCode
            hotkey = self.config.get('switchModeHotKey', [88])
            if key in hotkey and not getattr(event, 'isRepeat', False):
                self._mode = (self._mode + 1) % 3
                if self._bridge is not None:
                    self._bridge.set_mode(self._mode)
        except Exception:
            log('key handler error: %s' % traceback.format_exc())

    def _connect_bridge(self):
        try:
            from gui.mods import hpold_bridge
            self._bridge = hpold_bridge.Bridge()
            self._bridge.open()
            self._bridge.set_mode(self._mode)
        except Exception:
            self._bridge = None
            log('bridge unavailable: %s' % traceback.format_exc())

    def _collect(self):
        player = BigWorld.player()
        arena = getattr(player, 'arena', None)
        if arena is None:
            return {}
        out = {}
        vehicles = getattr(arena, 'vehicles', {})
        for vehicle_id, item in vehicles.iteritems():
            if not isinstance(item, dict):
                continue
            max_hp = item.get('maxHealth') or item.get('maxHP') or 0
            current = item.get('health')
            alive = item.get('isAlive', True)
            if current is None:
                # Arena data alone may not provide current HP: do not fake it.
                continue
            if not max_hp:
                continue
            out[vehicle_id] = {
                'vehicleID': vehicle_id,
                'health': max(0, current),
                'maxHealth': max_hp,
                'alive': bool(alive),
                'team': item.get('team', 0)
            }
        return out

    def _tick(self):
        self.tick_id = None
        if not self.running:
            return
        try:
            snapshot = self._collect()
            if snapshot != self._snapshot:
                self._snapshot = snapshot
                if self._bridge is not None:
                    self._bridge.update(snapshot)
        except Exception:
            log('hp polling failed: %s' % traceback.format_exc())
        if self.running:
            try:
                interval = max(0.1, float(self.config.get('pollInterval', 0.2)))
                self.tick_id = BigWorld.callback(interval, self._tick)
            except Exception:
                log('callback scheduling failed')


controller = HpoldController()


def on_battle_loaded():
    controller.start()


def on_battle_closed():
    controller.stop()


def register():
    if BigWorld is None:
        return
    try:
        from gui.shared.personality import ServicesLocator
        from skeletons.gui.app_loader import GuiGlobalSpaceID
        loader = ServicesLocator.appLoader

        def entered(space_id):
            if space_id == GuiGlobalSpaceID.BATTLE:
                on_battle_loaded()

        def left(space_id):
            if space_id == GuiGlobalSpaceID.BATTLE:
                on_battle_closed()

        loader.onGUISpaceEntered += entered
        loader.onGUISpaceLeft += left
        # Retain references so event handlers aren't collected.
        controller._on_entered = entered
        controller._on_left = left
        log('registered')
    except Exception:
        log('battle lifecycle unavailable: %s' % traceback.format_exc())


register()
