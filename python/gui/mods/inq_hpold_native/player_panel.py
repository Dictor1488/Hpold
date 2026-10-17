# -*- coding: utf-8 -*-
"""Standalone OldSkool-style players-panel HTML renderer.

Uses the original bundled PlayerPanelsAPI_modsCore SWF with no dependency
on OldSkool Python modules or modsCore. HPE health provider remains upstream.
"""
import Event
import math

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ScopeTemplates, ViewSettings
from helpers import dependency
from skeletons.gui.impl import IGuiLoader
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.DisposableEntity import EntityState
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID

from .logger import logger

INJECTOR_ALIAS = 'inq_hpold_panel_view'
COMPONENT_ALIAS = 'PlayerPanelsUI'
SWF_NAME = 'inq_hpold.swf'

# These are the original 1.2.4 field positions relative to the players panel.
# The SWF owns alignment, field insertion, and row-specific placement.
FIELDS = (
    ('3bg', {
        'isHtml': True,
        'left': {'align': 'left', 'text': "<img src='img://gui/hpbars/hp_bg.png' width='68' height='12'>", 'x': 86, 'y': 4},
        'right': {'align': 'left', 'text': "<img src='img://gui/hpbars/hp_bg.png' width='68' height='12'>", 'x': -175, 'y': 4}}),
    ('2img', {
        'isHtml': True,
        'left': {'align': 'left', 'text': "<img src='img://gui/hpbars/hp_alive_l.png' width='%(barWidth)d' height='14'>", 'width': 72, 'x': 85, 'y': 3},
        'right': {'align': 'left', 'text': "<img src='img://gui/hpbars/hp_alive_r.png' width='%(barWidth)d' height='14'>", 'width': 72, 'x': -176, 'y': 3}}),
    ('1text', {
        'isHtml': True,
        'left': {'align': 'center', 'text': "<font face='$FieldFont' color='#FFFFFF' size='11'>%(curHealth)s/%(maxHealth)s</font>", 'x': 100, 'y': 3},
        'right': {'align': 'center', 'text': "<font face='$FieldFont' color='#FFFFFF' size='11'>%(curHealth)s/%(maxHealth)s</font>", 'x': -160, 'y': 3}})
)
PREFIX = 'HPbars_'
EMPTY = '<font face="$FieldFont" color="#FFFFFF" size="11"></font>'


class PlayerPanelsUI(BaseDAAPIComponent):
    def _populate(self):
        super(PlayerPanelsUI, self)._populate()
        g_events._populate(self)

    def _dispose(self):
        g_events._dispose(self)
        super(PlayerPanelsUI, self)._dispose()

    def destroy(self):
        if self.getState() != EntityState.CREATED:
            super(PlayerPanelsUI, self).destroy()

    def as_createS(self, linkage, kind, config):
        if self._isDAAPIInited():
            self.flashObject.as_create(linkage, kind, config)

    def as_updateS(self, linkage, data):
        if self._isDAAPIInited():
            self.flashObject.as_update(linkage, data)

    def as_deleteS(self, linkage):
        if self._isDAAPIInited():
            self.flashObject.as_delete(linkage)


class Events(object):
    def __init__(self):
        self.componentUI = None
        self.viewRequested = False
        self.onUIReady = Event.Event()
        self._data = {}
        self._visible = False
        self._showBars = True
        self._enemyRed = False
        self._guiSubscribed = False

    def _populate(self, component):
        self.componentUI = component
        self.viewRequested = True
        try:
            for key, config in FIELDS:
                field = PREFIX + key
                component.as_createS(field, 'Label', _labelConfig(config))
            self.onUIReady()
            self.refreshAll()
        except Exception:
            logger.exception('OldSkool field initialization failed')

    def _dispose(self, component):
        if self.componentUI is component:
            self.componentUI = None
        self.viewRequested = False

    def setVehicleHealth(self, vehicleID, currentHealth, maxHealth, vehicleClass=''):
        vehicleID = int(vehicleID)
        maximum = max(0, int(maxHealth))
        current = min(maximum, max(0, int(currentHealth)))
        self._data[vehicleID] = (current, maximum)
        self._render(vehicleID)

    def _render(self, vehicleID):
        component = self.componentUI
        if component is None:
            return
        value = self._data.get(vehicleID)
        if value is None:
            return
        current, maximum = value
        width = int(math.ceil(72.0 * current / maximum)) if maximum else 0
        shown = self._visible and current > 0 and maximum > 0
        try:
            for key, config in FIELDS:
                fieldName = PREFIX + key
                if not shown or (not self._showBars and key != '1text'):
                    left = right = EMPTY
                else:
                    leftTemplate = config['left']['text']
                    rightTemplate = config['right']['text']
                    args = {'curHealth': current, 'maxHealth': maximum, 'barWidth': width}
                    left = leftTemplate % args
                    right = rightTemplate % args
                # Select per-side markup using arena team.
                text = self._sideText(vehicleID, left, right)
                component.as_updateS(fieldName, {'vehicleID': vehicleID, 'text': text})
        except Exception:
            logger.exception('OldSkool field update failed for %s', vehicleID)

    def _sideText(self, vehicleID, left, right):
        try:
            from helpers import dependency
            from skeletons.gui.battle_session import IBattleSessionProvider
            arenaDP = dependency.instance(IBattleSessionProvider).getArenaDP()
            info = arenaDP.getVehicleInfo(int(vehicleID))
            if info.isObserver():
                return EMPTY
            if arenaDP.isPlayerObserver():
                from gui.battle_control import avatar_getter
                return left if avatar_getter.getPlayerTeam() == info.team else right
            return left if arenaDP.isAllyTeam(info.team) else right
        except Exception:
            return EMPTY

    def setVisibility(self, visible):
        self._visible = bool(visible)
        self.refreshAll()

    def setDisplaySettings(self, showHpBars, enemyHpRed):
        self._showBars = bool(showHpBars)
        self._enemyRed = bool(enemyHpRed)
        self.refreshAll()

    def setIconSettings(self, *args):
        pass

    def refreshAll(self):
        for vehicleID in tuple(self._data):
            self._render(vehicleID)

    def clear(self):
        component = self.componentUI
        if component is not None:
            for vehicleID in tuple(self._data):
                try:
                    for key, config in FIELDS:
                        component.as_updateS(PREFIX + key, {'vehicleID': vehicleID, 'text': EMPTY})
                except Exception:
                    pass
        self._data.clear()

    def onComponentRegistered(self, event):
        if getattr(event, 'alias', None) == BATTLE_VIEW_ALIASES.PLAYERS_PANEL:
            self.requestView()

    def requestView(self):
        try:
            if self.viewRequested:
                return
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app is None:
                return
            self.viewRequested = True
            app.loadView(SFViewLoadParams(INJECTOR_ALIAS))
        except Exception:
            self.viewRequested = False
            logger.exception('Could not load standalone OldSkool panel injector')


g_events = Events()


def _labelConfig(config):
    # Match the default Label settings in original playersPanelAPI.py.
    import copy
    result = copy.deepcopy(config)
    result.setdefault('isHtml', False)
    result.setdefault('shadow', {'alpha': 90, 'blur': 2, 'color': '000000',
                                 'strength': 2, 'distance': 0, 'angle': 0})
    for side, alignment in (('left', 'left'), ('right', 'right')):
        values = result[side]
        for key, default in (('x', 0), ('y', 0), ('height', 24),
                             ('width', 100), ('align', alignment)):
            values.setdefault(key, default)
    return result


def _onSpaceEntered(spaceID):
    if spaceID == GuiGlobalSpaceID.BATTLE:
        g_events.requestView()


def initialize_panel():
    factory = dependency.instance(IGuiLoader).entitiesFactory
    if factory.getSettings(INJECTOR_ALIAS) is None:
        factory.addSettings(ViewSettings(
            INJECTOR_ALIAS, View, SWF_NAME, WindowLayer.WINDOW,
            None, ScopeTemplates.GLOBAL_SCOPE))
    if factory.getSettings(COMPONENT_ALIAS) is None:
        factory.addSettings(ViewSettings(
            COMPONENT_ALIAS, PlayerPanelsUI, None, WindowLayer.UNDEFINED,
            None, ScopeTemplates.DEFAULT_SCOPE))
    ServicesLocator.appLoader.onGUISpaceEntered += _onSpaceEntered
    g_eventBus.addListener(
        events.ComponentEvent.COMPONENT_REGISTERED,
        g_events.onComponentRegistered,
        scope=EVENT_BUS_SCOPE.GLOBAL)


def finalize_panel():
    try:
        ServicesLocator.appLoader.onGUISpaceEntered -= _onSpaceEntered
    except Exception:
        pass
    try:
        g_eventBus.removeListener(
            events.ComponentEvent.COMPONENT_REGISTERED,
            g_events.onComponentRegistered,
            scope=EVENT_BUS_SCOPE.GLOBAL)
    except Exception:
        pass
    g_events.componentUI = None
    g_events.viewRequested = False
    g_events._data.clear()
