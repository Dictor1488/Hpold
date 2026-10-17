# -*- coding: utf-8 -*-
import BigWorld
import Keys
from Avatar import PlayerAvatar
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

from .logger import logger
from .player_panel import g_events
from .settings import g_settings


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
        self._vehicleClass = {}
        self._callback = None
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
        if self._callback is not None:
            try:
                BigWorld.cancelCallback(self._callback)
            except Exception:
                pass
            self._callback = None
        self._unsubscribeArena()
        self._arena = None
        self._health.clear()
        self._maxHealth.clear()
        self._vehicleClass.clear()
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
            g_events.setIconSettings(*g_settings.iconSettings())
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
            self._schedulePoll(session)
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

    def _getVehicleClass(self, vehicleData):
        if not vehicleData:
            return ''

        vehicleType = None
        try:
            vehicleType = vehicleData.get('vehicleType')
        except Exception:
            pass

        candidates = []
        if vehicleType is not None:
            candidates.append(vehicleType)
            try:
                descriptor = getattr(vehicleType, 'type', None)
                if descriptor is not None:
                    candidates.append(descriptor)
            except Exception:
                pass

        for candidate in candidates:
            try:
                tags = getattr(candidate, 'tags', None)
            except Exception:
                tags = None
            if not tags:
                continue
            for className in ('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG'):
                try:
                    if className in tags:
                        return className
                except Exception:
                    pass

        return ''

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
        self._vehicleClass.clear()
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
                self._vehicleClass[vehicleID] = self._getVehicleClass(vehicleData)
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
        vehicleClass = self._vehicleClass.get(vehicleID, '')
        if vehicleClass:
            return vehicleClass
        try:
            vehicleData = self._arena.vehicles.get(vehicleID, {})
            vehicleClass = self._getVehicleClass(vehicleData)
            self._vehicleClass[vehicleID] = vehicleClass
        except Exception:
            vehicleClass = ''
        return vehicleClass

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
                self._vehicleClass[vehicleID] = self._getVehicleClass(vehicleData)
            except Exception:
                return
        self._health[vehicleID] = min(maxHealth, newHealth)
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
        try:
            self._buildInitialState()
            self._pushAll()
        except Exception:
            logger.exception('Vehicle list refresh failed')

    def _onUIReady(self, *args):
        self._pushAll()
        self._applyVisibility(force=True)

    def _pushAll(self):
        if self._arena is None:
            return
        g_events.setIconSettings(*g_settings.iconSettings())
        for vehicleID, maxHealth in self._maxHealth.items():
            g_events.setVehicleHealth(
                vehicleID,
                self._health.get(vehicleID, maxHealth),
                maxHealth,
                self._classForVehicle(vehicleID)
            )
        g_events.refreshAll()

    def _schedulePoll(self, session):
        if session != self._session or self._arena is None:
            return
        try:
            self._callback = BigWorld.callback(0.35, lambda: self._poll(session))
        except Exception:
            self._callback = None

    def _poll(self, session):
        self._callback = None
        if session != self._session or self._arena is None:
            return
        try:
            changed = False
            for vehicleID, maxHealth in self._maxHealth.items():
                value = self._readCurrentHealth(vehicleID, self._health.get(vehicleID, maxHealth))
                value = min(maxHealth, value)
                if self._health.get(vehicleID) != value:
                    self._health[vehicleID] = value
                    g_events.setVehicleHealth(
                        vehicleID,
                        value,
                        maxHealth,
                        self._classForVehicle(vehicleID)
                    )
                    changed = True
            if changed:
                g_events.refreshAll()
        except Exception:
            logger.exception('inq_hpold health poll failed')
        self._schedulePoll(session)


g_provider = HealthProvider()
_origBecomePlayer = None
_origBecomeNonPlayer = None
_origHandleKey = None
_hooksInstalled = False


def install_hooks():
    global _origBecomePlayer, _origBecomeNonPlayer, _origHandleKey, _hooksInstalled
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
    _hooksInstalled = False
