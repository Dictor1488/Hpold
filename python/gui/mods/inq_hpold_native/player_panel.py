# -*- coding: utf-8 -*-
import Event

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ComponentSettings, ScopeTemplates, ViewSettings
from helpers import dependency
from skeletons.gui.impl import IGuiLoader
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.personality import ServicesLocator

from .logger import logger

HPE_VIEW_ALIAS = 'inq_hpold_panel_view'
HPE_COMPONENT_NAME = 'inqHpoldPanel'
HPE_SWF = 'inqHpoldPanel.swf'


class HpPanelMeta(BaseDAAPIComponent):
    def _populate(self):
        super(HpPanelMeta, self)._populate()
        if g_events is not None:
            g_events._populate(self)

    def _dispose(self):
        if g_events is not None:
            g_events._dispose(self)
        super(HpPanelMeta, self)._dispose()

    def flashLogS(self, *data):
        logger.debug('Flash: %s', data)

    def as_setVehicleHealthS(self, vehicleID, currentHealth, maxHealth, vehicleClass=''):
        if self._isDAAPIInited():
            return self.flashObject.as_setVehicleHealth(
                vehicleID,
                currentHealth,
                maxHealth,
                vehicleClass or ''
            )
        return None

    def as_setVisibilityS(self, visible):
        if self._isDAAPIInited():
            return self.flashObject.as_setVisibility(bool(visible))
        return None

    def as_setDisplaySettingsS(self, showHpBars, enemyHpRed):
        if self._isDAAPIInited():
            return self.flashObject.as_setDisplaySettings(
                bool(showHpBars),
                bool(enemyHpRed)
            )
        return None

    def as_setIconSettingsS(self, enabled, colorizeHeavy, ltColor, mtColor, tdColor, spgColor, heavyColor):
        if self._isDAAPIInited():
            return self.flashObject.as_setIconSettings(
                bool(enabled),
                bool(colorizeHeavy),
                int(ltColor),
                int(mtColor),
                int(tdColor),
                int(spgColor),
                int(heavyColor)
            )
        return None

    def as_refreshAllS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_refreshAll()
        return None

    def as_clearS(self):
        if self._isDAAPIInited():
            return self.flashObject.as_clear()
        return None


class Events(object):
    def __init__(self):
        self.componentUI = None
        self.viewLoad = False
        self.viewRequested = False
        self.onUIReady = Event.Event()

    def _populate(self, component):
        self.componentUI = component
        self.viewLoad = True
        self.viewRequested = True
        logger.info('inq_hpold Flash component populated')
        self.onUIReady()

    def _dispose(self, component):
        if self.componentUI is component:
            self.componentUI = None
        self.viewLoad = False
        self.viewRequested = False

    def setVehicleHealth(self, vehicleID, currentHealth, maxHealth, vehicleClass=''):
        if self.componentUI is None:
            return
        try:
            self.componentUI.as_setVehicleHealthS(
                int(vehicleID),
                int(currentHealth),
                int(maxHealth),
                vehicleClass or ''
            )
        except Exception:
            logger.exception('setVehicleHealth failed for %s', vehicleID)

    def setVisibility(self, visible):
        if self.componentUI is None:
            return
        try:
            self.componentUI.as_setVisibilityS(bool(visible))
        except Exception:
            logger.exception('setVisibility failed')

    def setDisplaySettings(self, showHpBars, enemyHpRed):
        if self.componentUI is None:
            return
        try:
            self.componentUI.as_setDisplaySettingsS(
                bool(showHpBars),
                bool(enemyHpRed)
            )
        except Exception:
            logger.exception('setDisplaySettings failed')

    def setIconSettings(self, enabled, colorizeHeavy, ltColor, mtColor, tdColor, spgColor, heavyColor):
        if self.componentUI is None:
            return
        try:
            self.componentUI.as_setIconSettingsS(
                bool(enabled),
                bool(colorizeHeavy),
                int(ltColor),
                int(mtColor),
                int(tdColor),
                int(spgColor),
                int(heavyColor)
            )
        except Exception:
            logger.exception('setIconSettings failed')

    def refreshAll(self):
        if self.componentUI is not None:
            try:
                self.componentUI.as_refreshAllS()
            except Exception:
                logger.exception('refreshAll failed')

    def clear(self):
        if self.componentUI is not None:
            try:
                self.componentUI.as_clearS()
            except Exception:
                logger.exception('clear failed')

    def onComponentRegistered(self, event):
        try:
            if getattr(event, 'alias', None) != BATTLE_VIEW_ALIASES.PLAYERS_PANEL:
                return
            if self.viewRequested:
                return
            app = ServicesLocator.appLoader.getDefBattleApp()
            if app is None:
                return
            self.viewRequested = True
            app.loadView(SFViewLoadParams(HPE_VIEW_ALIAS, HPE_VIEW_ALIAS), {})
            logger.info('Requested inq_hpold player-panel SWF')
        except Exception:
            self.viewRequested = False
            logger.exception('Could not load inq_hpold player-panel SWF')


g_events = Events()


def initialize_panel():
    entitiesFactory = dependency.instance(IGuiLoader).entitiesFactory
    if entitiesFactory.getSettings(HPE_VIEW_ALIAS) is None:
        entitiesFactory.addSettings(ViewSettings(
            HPE_VIEW_ALIAS,
            View,
            HPE_SWF,
            WindowLayer.WINDOW,
            None,
            ScopeTemplates.GLOBAL_SCOPE
        ))

    if entitiesFactory.getSettings(HPE_COMPONENT_NAME) is None:
        entitiesFactory.addSettings(ComponentSettings(
            HPE_COMPONENT_NAME,
            HpPanelMeta,
            ScopeTemplates.DEFAULT_SCOPE
        ))

    try:
        g_eventBus.removeListener(
            events.ComponentEvent.COMPONENT_REGISTERED,
            g_events.onComponentRegistered,
            scope=EVENT_BUS_SCOPE.GLOBAL
        )
    except Exception:
        pass

    g_eventBus.addListener(
        events.ComponentEvent.COMPONENT_REGISTERED,
        g_events.onComponentRegistered,
        scope=EVENT_BUS_SCOPE.GLOBAL
    )
    logger.info('inq_hpold player-panel bridge initialized')


def finalize_panel():
    try:
        g_eventBus.removeListener(
            events.ComponentEvent.COMPONENT_REGISTERED,
            g_events.onComponentRegistered,
            scope=EVENT_BUS_SCOPE.GLOBAL
        )
    except Exception:
        pass
    g_events.componentUI = None
    g_events.viewLoad = False
    g_events.viewRequested = False
