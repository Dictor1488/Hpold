# -*- coding: utf-8 -*-
"""Standalone HP OLD: battle HP, Scaleform fields, settings and lifecycle.

No OldSkool/ModScore runtime dependency. Python 2.7 game client.
"""
import logging
import math
import copy
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
try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

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
        'left': {'align': 'center', 'text': "<font face='$FieldFont' color='#FFFFFF' size='12'><b>%(curHealth)s/%(maxHealth)s</b></font>", 'width': 72, 'height': 18, 'x': 85, 'y': 1},
        'right': {'align': 'center', 'text': "<font face='$FieldFont' color='#FFFFFF' size='12'><b>%(curHealth)s/%(maxHealth)s</b></font>", 'width': 72, 'height': 18, 'x': -176, 'y': 1}})
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
        self.refreshAll()

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

# ---------------------------------------------------------------------------
# Optional in-game settings (no external dependency required)
# ---------------------------------------------------------------------------
MOD_LINKAGE = 'inq_hpold'
DEFAULTS = {'enabled': True, 'showHpBars': True, 'enemyHpRed': False}


class inq_hpoldSettings(object):
    def __init__(self):
        self.values = dict(DEFAULTS)
        self._registered = False
        self._uiHooked = False

    def initialize(self):
        self._hookUIReady()
        if self._registered or g_modsSettingsApi is None:
            return
        template = {
            'modDisplayName': u'inq_hpold',
            'enabled': True,
            'column1': [
                {'type': 'CheckBox', 'text': u'Показувати HP-шкали',
                 'value': True, 'varName': 'showHpBars'},
                {'type': 'CheckBox', 'text': u'Червоний HP противників',
                 'value': False, 'varName': 'enemyHpRed'}
            ],
            'column2': []
        }
        try:
            saved = g_modsSettingsApi.setModTemplate(
                MOD_LINKAGE, template, self._onSettingsChanged)
            if saved:
                self._apply(saved)
            self._registered = True
        except Exception:
            logger.exception('inq_hpold settings registration failed')

    def _hookUIReady(self):
        if self._uiHooked:
            return
        try:
            g_events.onUIReady += self._applyDisplayToFlash
            self._uiHooked = True
        except Exception:
            logger.exception('inq_hpold UI settings callback failed')

    def finalize(self):
        if self._uiHooked:
            try:
                        g_events.onUIReady -= self._applyDisplayToFlash
            except Exception:
                pass
        self._uiHooked = False
        self._registered = False

    def _apply(self, values):
        if values:
            for key in DEFAULTS:
                if key in values:
                    self.values[key] = bool(values[key])

    def _applyDisplayToFlash(self, *args):
        try:
            g_events.setDisplaySettings(*self.displaySettings())
        except Exception:
            logger.exception('inq_hpold display settings failed')

    def _onSettingsChanged(self, linkage, newSettings):
        if linkage != MOD_LINKAGE:
            return
        self._apply(newSettings)
        self._applyDisplayToFlash()
        try:
            g_provider.applySettings()
        except Exception:
            logger.exception('inq_hpold applying settings failed')

    def isEnabled(self):
        return bool(self.values.get('enabled', True))

    def displaySettings(self):
        return (bool(self.values.get('showHpBars', True)),
                bool(self.values.get('enemyHpRed', False)))


g_settings = inq_hpoldSettings()

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
            g_settings.isEnabled() and
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
            g_events.setDisplaySettings(*g_settings.displaySettings())
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
            self._pushAll()
            self._applyVisibility(force=True)
            logger.info('inq_hpold provider started for %s vehicles', len(self._maxHealth))
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

    def _readCurrentHealth(self, vehicleID, defaultValue):
        try:
            entity = BigWorld.entity(int(vehicleID))
            value = getattr(entity, 'health', None) if entity is not None else None
            if value is not None:
                return max(0, int(value))
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
        nextHealth = min(maxHealth, newHealth)
        # Arena event values may lag behind the native panel callback.
        # In a standard battle health cannot spontaneously increase.
        previousHealth = self._health.get(vehicleID)
        if previousHealth is not None and nextHealth > previousHealth:
            return
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
            current = min(maximum, current)
            previous = (self._health.get(vehicleID), self._maxHealth.get(vehicleID))
            # Ignore an out-of-order full-health callback after damage.
            # A new battle resets the cache in start()/stop().
            if (previous[0] is not None and current > previous[0]):
                return
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
        g_settings.initialize()
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
        g_settings.finalize()
        finalize_panel()
        _initialized = False
        logger.info('inq_hpold unloaded')
    except Exception:
        logger.exception('inq_hpold shutdown failed')
