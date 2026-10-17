# -*- coding: utf-8 -*-
"""HP-only options; no tank icon controls."""
from .logger import logger

try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

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
            from .player_panel import g_events
            g_events.onUIReady += self._applyDisplayToFlash
            self._uiHooked = True
        except Exception:
            logger.exception('inq_hpold UI settings callback failed')

    def finalize(self):
        if self._uiHooked:
            try:
                from .player_panel import g_events
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
            from .player_panel import g_events
            g_events.setDisplaySettings(*self.displaySettings())
        except Exception:
            logger.exception('inq_hpold display settings failed')

    def _onSettingsChanged(self, linkage, newSettings):
        if linkage != MOD_LINKAGE:
            return
        self._apply(newSettings)
        self._applyDisplayToFlash()
        try:
            from .provider import g_provider
            g_provider.applySettings()
        except Exception:
            logger.exception('inq_hpold applying settings failed')

    def isEnabled(self):
        return bool(self.values.get('enabled', True))

    def displaySettings(self):
        return (bool(self.values.get('showHpBars', True)),
                bool(self.values.get('enemyHpRed', False)))


g_settings = inq_hpoldSettings()
