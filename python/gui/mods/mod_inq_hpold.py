# -*- coding: utf-8 -*-
"""Standalone HP OLD: battle HP, Scaleform fields, settings and lifecycle.

No OldSkool/ModScore runtime dependency. Python 2.7 game client.
"""
import logging
import Event
import BigWorld
import Keys
from Avatar import PlayerAvatar
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ScopeTemplates, ViewSettings
from skeletons.gui.impl import IGuiLoader
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.personality import ServicesLocator
from skeletons.gui.app_loader import GuiGlobalSpaceID
try:
    from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
except ImportError:
    PlayersPanel = None
logger = logging.getLogger('[inq_hpold]')
__version__ = '0.2.0'
__author__ = 'Dictor1488'
__mod_name__ = 'inq_hpold'

# ---------------------------------------------------------------------------
# Scaleform HP fields
# ---------------------------------------------------------------------------
INJECTOR_ALIAS = 'inq_hpold_panel_view'
COMPONENT_ALIAS = 'PlayerPanelsUI'
SWF_NAME = 'inq_hpold.swf'



class PlayerPanelsUI(BaseDAAPIComponent):
    def _populate(self):
        super(PlayerPanelsUI, self)._populate()
        g_events._populate(self)

    def _dispose(self):
        g_events._dispose(self)
        super(PlayerPanelsUI, self)._dispose()

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

    def _populate(self, component):
        self.componentUI = component
        self.viewRequested = True
        try:
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
        current, maximum = self._data.get(vehicleID, (0, 0))
        if maximum <= 0:
            return
        component.as_updateS('hp_row', {
            'vehicleID': vehicleID,
            'current': current,
            'maximum': maximum,
            'visible': bool(self._visible),
            'showBar': bool(self._showBars)
        })

    def setVisibility(self, visible):
        self._visible = bool(visible)
        self.refreshAll()

    def setDisplaySettings(self, showHpBars):
        self._showBars = bool(showHpBars)
        self.refreshAll()

    def refreshAll(self):
        for vehicleID in tuple(self._data):
            self._render(vehicleID)

    def clear(self):
        if self.componentUI is not None:
            self.componentUI.as_deleteS('hp_row')
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

# HP bars are always enabled; this mod has no settings menu.

# ---------------------------------------------------------------------------
# Event-driven HP provider and player-panel hooks
# ---------------------------------------------------------------------------
def _resolve_keys(*names):
    result = set()
    for name in names:
        value = getattr(Keys, name, None)
        if value is not None:
            result.add(value)
    return result


_ALT_KEYS = _resolve_keys('KEY_LALT', 'KEY_RALT', 'KEY_ALT')
_CTRL_KEYS = _resolve_keys(
    'KEY_LCONTROL', 'KEY_RCONTROL', 'KEY_CONTROL',
    'KEY_LCTRL', 'KEY_RCTRL', 'KEY_CTRL'
)


class HealthProvider(object):
    sessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self._arena = None
        self._health = {}
        self._maxHealth = {}
        self._session = 0
        self._subscribed = []
        self._pollInterval = 0.5
        self._healthEventCount = 0
        self._panelEventCount = 0

        self._altDown = False
        self._ctrlDown = False
        self._alwaysShow = False
        self._comboLatch = False
        self._visible = None

        try:
            g_events.onUIReady += self._onUIReady
        except Exception:
            pass

    def start(self):
        self._session += 1
        session = self._session
        self.stop(clear_session=False)
        self._resetHotkeys()
        self._tryStart(session, 0)

    def stop(self, clear_session=True):
        if clear_session:
            self._session += 1
        self._unsubscribeArena()
        self._arena = None
        logger.info('inq_hpold battle summary: health events=%s panel events=%s', self._healthEventCount, self._panelEventCount)
        self._healthEventCount = 0
        self._panelEventCount = 0
        self._health.clear()
        self._maxHealth.clear()
        self._resetHotkeys()
        self._visible = None
        try:
            g_events.setVisibility(False)
            g_events.clear()
        except Exception:
            pass

    def _resetHotkeys(self, reset_always=False):
        self._altDown = False
        self._ctrlDown = False
        self._comboLatch = False
        if reset_always:
            self._alwaysShow = False

    def _keyName(self, key):
        try:
            return str(BigWorld.keyToString(key)).upper().replace('KEY_', '')
        except Exception:
            return ''

    def _isAltKey(self, key):
        if key in _ALT_KEYS:
            return True
        return self._keyName(key) in ('ALT', 'LALT', 'RALT')

    def _isCtrlKey(self, key):
        if key in _CTRL_KEYS:
            return True
        return self._keyName(key) in (
            'CTRL', 'CONTROL', 'LCTRL', 'RCTRL', 'LCONTROL', 'RCONTROL'
        )

    def _applyVisibility(self, force=False):
        visible = bool(
            (self._alwaysShow or (self._altDown and not self._ctrlDown))
        )
        if not force and self._visible == visible:
            return
        self._visible = visible
        try:
            g_events.setVisibility(visible)
        except Exception:
            logger.exception('Could not update inq_hpold visibility')

    def handleKey(self, isDown, key, mods=0):
        isAlt = self._isAltKey(key)
        isCtrl = self._isCtrlKey(key)
        if not isAlt and not isCtrl:
            return

        down = bool(isDown)
        changed = False
        if isAlt and self._altDown != down:
            self._altDown = down
            changed = True
        if isCtrl and self._ctrlDown != down:
            self._ctrlDown = down
            changed = True
        if not changed:
            return

        combo = self._altDown and self._ctrlDown
        if combo and down and not self._comboLatch:
            self._alwaysShow = not self._alwaysShow
            self._comboLatch = True
            logger.info(
                'inq_hpold persistent HP display %s',
                'enabled' if self._alwaysShow else 'disabled'
            )
        elif not combo:
            self._comboLatch = False

        self._applyVisibility()

    def applySettings(self):
        try:
            g_events.setDisplaySettings(True)
            self._applyVisibility(force=True)
            g_events.refreshAll()
        except Exception:
            logger.exception('Could not apply inq_hpold settings')

    def _tryStart(self, session, retry):
        if session != self._session:
            return
        try:
            player = BigWorld.player()
            arena = getattr(player, 'arena', None) if player is not None else None
            if arena is None or not getattr(arena, 'vehicles', None):
                if retry < 40:
                    BigWorld.callback(0.25, lambda: self._tryStart(session, retry + 1))
                return
            self._arena = arena
            self._buildInitialState()
            self._subscribeArena()
            self._schedulePoll(session)
            self._pushAll()
            self._applyVisibility(force=True)
            logger.info('inq_hpold provider started for %s vehicles; arena events=%s; panel hook=%s',
                        len(self._maxHealth), [name for name, unused in self._subscribed],
                        bool(_origPanelHealth))
        except Exception:
            logger.exception('inq_hpold provider start failed')

    def _getArenaDP(self):
        try:
            provider = self.sessionProvider
            if provider is not None:
                return provider.getArenaDP()
        except Exception:
            pass
        return None

    def _getMaxHealth(self, vehicleData):
        if not vehicleData:
            return 0
        for key in ('maxHealth', 'maxHP', 'health'):
            try:
                value = vehicleData.get(key)
                if value:
                    return int(value)
            except Exception:
                pass
        try:
            vehicleType = vehicleData.get('vehicleType')
        except Exception:
            vehicleType = None
        if vehicleType is not None:
            for attr in ('maxHealth', 'maxHP'):
                try:
                    value = getattr(vehicleType, attr, None)
                    if value:
                        return int(value)
                except Exception:
                    pass
            try:
                descriptor = getattr(vehicleType, 'type', None)
                value = getattr(descriptor, 'maxHealth', None)
                if value:
                    return int(value)
            except Exception:
                pass
        return 0

    def _isDead(self, vehicleID):
        """Use explicit battle state, never infer a death from a missing entity."""
        try:
            data = self._arena.vehicles.get(int(vehicleID), {})
            if data.get('isAlive') is False:
                return True
        except Exception:
            pass
        arenaDP = self._getArenaDP()
        if arenaDP is not None:
            for methodName in ('getVehicleStats', 'getVehicleStatsVO'):
                try:
                    method = getattr(arenaDP, methodName, None)
                    if not callable(method):
                        continue
                    stats = method(int(vehicleID))
                    alive = stats.get('isAlive') if isinstance(stats, dict) else getattr(stats, 'isAlive', None)
                    if alive is False:
                        return True
                except Exception:
                    pass
        return False

    def _readObservedHealth(self, vehicleID):
        """Return only current HP from a live entity or battle statistics.
        Never fall back to arena.vehicles['health'] (spawn HP).
        """
        if self._isDead(vehicleID):
            return 0
        try:
            entity = BigWorld.entity(int(vehicleID))
            hp = getattr(entity, 'health', None) if entity is not None else None
            if hp is not None:
                return max(0, int(hp))
        except Exception:
            pass
        arenaDP = self._getArenaDP()
        if arenaDP is not None:
            for methodName in ('getVehicleStats', 'getVehicleStatsVO'):
                try:
                    method = getattr(arenaDP, methodName, None)
                    if not callable(method):
                        continue
                    stats = method(int(vehicleID))
                    if stats is None:
                        continue
                    hp = stats.get('health') if isinstance(stats, dict) else getattr(stats, 'health', None)
                    if hp is not None:
                        return max(0, int(hp))
                except Exception:
                    pass
        return None

    def _schedulePoll(self, session):
        # A cheap fallback for replays and game versions without arena HP events.
        if session != self._session or self._arena is None:
            return
        BigWorld.callback(self._pollInterval, lambda: self._pollHealth(session))

    def _pollHealth(self, session):
        if session != self._session or self._arena is None:
            return
        try:
            for vehicleID, maximum in tuple(self._maxHealth.items()):
                observed = self._readObservedHealth(vehicleID)
                if observed is None:
                    continue
                current = min(maximum, observed)
                if self._health.get(vehicleID) != current:
                    self._health[vehicleID] = current
                    g_events.setVehicleHealth(vehicleID, current, maximum)
            self._schedulePoll(session)
        except Exception:
            logger.exception('inq_hpold health reconciliation failed')
            self._schedulePoll(session)

    def _readCurrentHealth(self, vehicleID, defaultValue):
        observed = self._readObservedHealth(vehicleID)
        if observed is not None:
            return observed

        arenaDP = self._getArenaDP()
        if arenaDP is not None:
            for methodName in ('getVehicleStats', 'getVehicleStatsVO'):
                try:
                    method = getattr(arenaDP, methodName, None)
                    if not callable(method):
                        continue
                    stats = method(int(vehicleID))
                    if stats is None:
                        continue
                    if isinstance(stats, dict):
                        value = stats.get('health')
                    else:
                        value = getattr(stats, 'health', None)
                    if value is not None:
                        return max(0, int(value))
                except Exception:
                    pass

        try:
            vehicleData = self._arena.vehicles.get(int(vehicleID), {})
            if vehicleData.get('isAlive') is False:
                return 0
            value = vehicleData.get('health')
            if value is not None:
                return max(0, int(value))
        except Exception:
            pass
        return max(0, int(defaultValue or 0))

    def _buildInitialState(self):
        self._health.clear()
        self._maxHealth.clear()
        for vehicleID, vehicleData in self._arena.vehicles.items():
            try:
                vehicleID = int(vehicleID)
                maxHealth = self._getMaxHealth(vehicleData)
                if maxHealth <= 0:
                    continue
                current = self._readCurrentHealth(vehicleID, maxHealth)
                current = min(maxHealth, current)
                self._maxHealth[vehicleID] = maxHealth
                self._health[vehicleID] = current
            except Exception:
                logger.exception('Failed to initialize vehicle %s', vehicleID)

    def _subscribe(self, eventName, callback):
        try:
            event = getattr(self._arena, eventName, None)
            if event is None:
                return
            event += callback
            self._subscribed.append((event, callback))
            logger.debug('Subscribed arena.%s', eventName)
        except Exception:
            logger.debug('Arena event not available: %s', eventName)

    def _subscribeArena(self):
        self._unsubscribeArena()
        if self._arena is None:
            return
        self._subscribe('onVehicleHealthChanged', self._onVehicleHealthChanged)
        self._subscribe('onVehicleKilled', self._onVehicleKilled)
        self._subscribe('onNewVehicleListReceived', self._onVehicleListChanged)
        self._subscribe('onVehicleAdded', self._onVehicleListChanged)

    def _unsubscribeArena(self):
        for event, callback in self._subscribed:
            try:
                event -= callback
            except Exception:
                pass
        self._subscribed = []

    def _classForVehicle(self, vehicleID):
        return ''

    def _onVehicleHealthChanged(self, *args):
        if len(args) < 2:
            return
        try:
            vehicleID = int(args[0])
            newHealth = max(0, int(args[1]))
        except Exception:
            return
        maxHealth = self._maxHealth.get(vehicleID, 0)
        if maxHealth <= 0:
            try:
                vehicleData = self._arena.vehicles.get(vehicleID, {})
                maxHealth = self._getMaxHealth(vehicleData)
                self._maxHealth[vehicleID] = maxHealth
            except Exception:
                return
        self._healthEventCount += 1
        nextHealth = 0 if self._isDead(vehicleID) else min(maxHealth, newHealth)
        # Healing is legitimate in Onslaught and other special modes.
        # Accept authoritative changes in either direction; reject only duplicates.
        previousHealth = self._health.get(vehicleID)
        if previousHealth == nextHealth:
            return
        self._health[vehicleID] = nextHealth
        g_events.setVehicleHealth(
            vehicleID,
            self._health[vehicleID],
            maxHealth,
            self._classForVehicle(vehicleID)
        )

    def _onVehicleKilled(self, *args):
        if not args:
            return
        try:
            vehicleID = int(args[0])
        except Exception:
            return
        if vehicleID in self._maxHealth:
            self._health[vehicleID] = 0
            g_events.setVehicleHealth(
                vehicleID,
                0,
                self._maxHealth[vehicleID],
                self._classForVehicle(vehicleID)
            )

    def _onVehicleListChanged(self, *args):
        # Arena vehicle-list notifications are not health snapshots. Rebuilding
        # from arena.vehicles resets damaged tanks to their spawn HP.
        try:
            for vehicleID, vehicleData in self._arena.vehicles.items():
                vehicleID = int(vehicleID)
                if vehicleID in self._maxHealth:
                    continue
                maximum = self._getMaxHealth(vehicleData)
                if maximum <= 0:
                    continue
                self._maxHealth[vehicleID] = maximum
                self._health[vehicleID] = min(
                    maximum, self._readCurrentHealth(vehicleID, maximum))
                g_events.setVehicleHealth(
                    vehicleID, self._health[vehicleID], maximum,
                    self._classForVehicle(vehicleID))
        except Exception:
            logger.exception('Vehicle list refresh failed')

    def _onUIReady(self, *args):
        self._pushAll()
        self._applyVisibility(force=True)

    def _pushAll(self):
        if self._arena is None:
            return
        for vehicleID, maxHealth in self._maxHealth.items():
            g_events.setVehicleHealth(
                vehicleID,
                self._health.get(vehicleID, maxHealth),
                maxHealth,
                self._classForVehicle(vehicleID)
            )
        g_events.refreshAll()

    def onPanelHealth(self, vehicleID, newHealth, maxHealth):
        """Use the health values already delivered by WoT to PlayersPanel."""
        if self._arena is None:
            return
        try:
            vehicleID = int(vehicleID)
            maximum = max(0, int(maxHealth))
            current = max(0, int(newHealth))
            if maximum <= 0:
                return
            self._panelEventCount += 1
            current = 0 if self._isDead(vehicleID) else min(maximum, current)
            previous = (self._health.get(vehicleID), self._maxHealth.get(vehicleID))
            # The native panel also reports legitimate healing; never clamp HP
            # to its historical minimum.
            self._health[vehicleID] = current
            self._maxHealth[vehicleID] = maximum
            if previous != (current, maximum):
                g_events.setVehicleHealth(
                    vehicleID, current, maximum, self._classForVehicle(vehicleID))
        except Exception:
            logger.exception('Could not process WoT PlayersPanel health update')


g_provider = HealthProvider()
_origBecomePlayer = None
_origBecomeNonPlayer = None
_origHandleKey = None
_origPanelHealth = None
_hooksInstalled = False


def install_hooks():
    global _origBecomePlayer, _origBecomeNonPlayer, _origHandleKey, _origPanelHealth, _hooksInstalled
    if _hooksInstalled:
        return
    _origBecomePlayer = PlayerAvatar.onBecomePlayer
    _origBecomeNonPlayer = PlayerAvatar.onBecomeNonPlayer
    _origHandleKey = getattr(PlayerAvatar, 'handleKey', None)

    def patchedBecomePlayer(avatar, *args, **kwargs):
        result = _origBecomePlayer(avatar, *args, **kwargs)
        try:
            BigWorld.callback(0.1, g_provider.start)
        except Exception:
            logger.exception('Could not schedule inq_hpold start')
        return result

    def patchedBecomeNonPlayer(avatar, *args, **kwargs):
        try:
            g_provider.stop()
        except Exception:
            logger.exception('Could not stop inq_hpold provider')
        return _origBecomeNonPlayer(avatar, *args, **kwargs)

    def patchedHandleKey(avatar, isDown, key, mods):
        result = None
        if _origHandleKey is not None:
            result = _origHandleKey(avatar, isDown, key, mods)
        try:
            g_provider.handleKey(isDown, key, mods)
        except Exception:
            logger.exception('inq_hpold key handler failed')
        return result

    if PlayersPanel is not None:
        _origPanelHealth = getattr(PlayersPanel, 'updateVehicleHealth', None)
        if callable(_origPanelHealth):
            def patchedPanelHealth(panel, vehicleID, newHealth, maxHealth):
                result = _origPanelHealth(panel, vehicleID, newHealth, maxHealth)
                g_provider.onPanelHealth(vehicleID, newHealth, maxHealth)
                return result
            PlayersPanel.updateVehicleHealth = patchedPanelHealth
        else:
            logger.warning('PlayersPanel.updateVehicleHealth unavailable; arena events only')
    else:
        logger.warning('PlayersPanel class unavailable; arena events only')

    PlayerAvatar.onBecomePlayer = patchedBecomePlayer
    PlayerAvatar.onBecomeNonPlayer = patchedBecomeNonPlayer
    if _origHandleKey is not None:
        PlayerAvatar.handleKey = patchedHandleKey
    else:
        logger.warning('PlayerAvatar.handleKey is unavailable; inq_hpold hotkeys are disabled')
    _hooksInstalled = True


def remove_hooks():
    global _hooksInstalled
    if not _hooksInstalled:
        return
    try:
        g_provider.stop()
    except Exception:
        pass
    if _origBecomePlayer is not None:
        PlayerAvatar.onBecomePlayer = _origBecomePlayer
    if _origBecomeNonPlayer is not None:
        PlayerAvatar.onBecomeNonPlayer = _origBecomeNonPlayer
    if _origHandleKey is not None:
        PlayerAvatar.handleKey = _origHandleKey
    if PlayersPanel is not None and _origPanelHealth is not None:
        PlayersPanel.updateVehicleHealth = _origPanelHealth
    _hooksInstalled = False

# ---------------------------------------------------------------------------
# Mod entry point
# ---------------------------------------------------------------------------
_initialized = False

def init():
    global _initialized
    if _initialized:
        return
    try:
        initialize_panel()
        install_hooks()
        _initialized = True
        logger.info('inq_hpold loaded v%s', __version__)
    except Exception:
        logger.exception('inq_hpold initialization failed')

def fini():
    global _initialized
    if not _initialized:
        return
    try:
        remove_hooks()
        finalize_panel()
        _initialized = False
        logger.info('inq_hpold unloaded')
    except Exception:
        logger.exception('inq_hpold shutdown failed')
