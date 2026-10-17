# -*- coding: utf-8 -*-
"""Standalone Scaleform bridge for inq_hpold (independent game module).

Own copy of the internal players-panel injector protocol. Uses a dedicated inq_hpold.swf renderer shipped as part of this mod.
"""
import copy
import traceback

import Event
from gui.Scaleform.framework import g_entitiesFactories, ViewSettings, ScopeTemplates
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID
from frameworks.wulf import WindowLayer

VIEW_INJECTOR = 'InqHpPanelInjector'
VIEW_COMPONENT = 'InqHpPanelUI'
SWF_NAME = 'inq_hpold.swf'
PANEL_DEFAULTS = {
    'isHtml': False,
    'left': {'x': 0, 'y': 0, 'height': 24, 'width': 100, 'align': 'left'},
    'right': {'x': 0, 'y': 0, 'height': 24, 'width': 100, 'align': 'right'},
    'shadow': {'alpha': 90, 'blur': 2, 'color': '000000',
               'strength': 2, 'distance': 0, 'angle': 0}
}


def _merge(data, defaults):
    for key, value in defaults.iteritems():
        if key not in data:
            data[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(data[key], dict):
            _merge(data[key], value)


class _Events(object):
    def __init__(self):
        self.create = Event.Event()
        self.update = Event.Event()
        self.delete = Event.Event()
        self.ready = Event.Event()


events = _Events()
cache = {}


class InqHpPanelUI(BaseDAAPIComponent):
    def _populate(self):
        super(InqHpPanelUI, self)._populate()
        events.create += self.as_createS
        events.update += self.as_updateS
        events.delete += self.as_deleteS
        for name, record in cache.iteritems():
            self.as_createS(name, record['type'], record['definition'])
            for data in record['values'].itervalues():
                self.as_updateS(name, data)
        events.ready()

    def _dispose(self):
        events.create -= self.as_createS
        events.update -= self.as_updateS
        events.delete -= self.as_deleteS
        super(InqHpPanelUI, self)._dispose()

    def destroy(self):
        if self.getState() == EntityState.CREATED:
            super(InqHpPanelUI, self).destroy()

    def as_createS(self, name, kind, definition):
        if self._isDAAPIInited():
            self.flashObject.as_create(name, kind, definition)

    def as_updateS(self, name, data):
        if self._isDAAPIInited():
            self.flashObject.as_update(name, data)

    def as_deleteS(self, name):
        if self._isDAAPIInited():
            self.flashObject.as_delete(name)


class Renderer(object):
    def create_field(self, name, definition):
        # Overwrites allow new battle / graphics settings without stale data.
        config = copy.deepcopy(definition)
        _merge(config, PANEL_DEFAULTS)
        if name not in cache:
            cache[name] = {'type': 'Label', 'definition': config, 'values': {}}
            events.create(name, 'Label', config)

    def update_field(self, name, vehicleID, text):
        if name not in cache:
            return
        data = {'vehicleID': vehicleID, 'text': text}
        cache[name]['values'][vehicleID] = data
        events.update(name, data)

    def close(self):
        for name in tuple(cache):
            events.delete(name)
        cache.clear()


_renderer = Renderer()
_bridges = []


def register_renderer(renderer):
    global _renderer
    _renderer = renderer
    for bridge in list(_bridges):
        bridge._create_fields()
        bridge.flush()


class Bridge(object):
    def __init__(self):
        self._active = False
        self._templates = {}
        self._state = {}

    def open(self, templates=None):
        self._active = True
        self._templates = templates or {}
        if self not in _bridges:
            _bridges.append(self)
        self._create_fields()

    def _create_fields(self):
        if self._active and _renderer is not None:
            for name, definition in sorted(self._templates.iteritems()):
                _renderer.create_field('HPbars_' + name, definition)

    def update_vehicle(self, vehicleID, side, fields):
        if not self._active:
            return
        self._state[vehicleID] = (side, dict(fields))
        if _renderer is not None:
            for name, value in fields.iteritems():
                _renderer.update_field(name, vehicleID, value)

    def flush(self):
        if _renderer is not None and self._active:
            for vehicleID, (side, fields) in self._state.iteritems():
                for name, value in fields.iteritems():
                    _renderer.update_field(name, vehicleID, value)

    def close(self):
        if self in _bridges:
            _bridges.remove(self)
        self._active = False
        self._state.clear()
        if _renderer is not None:
            _renderer.close()


def _enter_battle(space_id):
    if space_id != GuiGlobalSpaceID.BATTLE:
        return
    app = ServicesLocator.appLoader.getDefBattleApp()
    if app is not None:
        try:
            app.loadView(SFViewLoadParams(VIEW_INJECTOR))
        except Exception:
            traceback.print_exc()


def _ready():
    for bridge in list(_bridges):
        bridge.flush()


def _initialize():
    # Dedicated UI linkage.
    g_entitiesFactories.addSettings(ViewSettings(
        VIEW_INJECTOR, View, SWF_NAME, WindowLayer.WINDOW,
        None, ScopeTemplates.GLOBAL_SCOPE))
    g_entitiesFactories.addSettings(ViewSettings(
        VIEW_COMPONENT, InqHpPanelUI, None, WindowLayer.UNDEFINED,
        None, ScopeTemplates.DEFAULT_SCOPE))
    ServicesLocator.appLoader.onGUISpaceEntered += _enter_battle
    events.ready += _ready


_initialize()
