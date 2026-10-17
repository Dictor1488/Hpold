# -*- coding: utf-8 -*-
from .logger import logger

try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

MOD_LINKAGE = 'me.inq.hpe'

DEFAULTS = {
    'enabled': True,
    'showHpBars': True,
    'enemyHpRed': False,
    'colorizeIcons': True,
    'colorizeHeavy': False,
    'ltColor': '596E4B',
    'mtColor': '8B6526',
    'tdColor': '3D4658',
    'spgColor': '684940',
    'heavyColor': '808080'
}


def _normalize_color(value, fallback):
    try:
        text = str(value or '').strip().upper().replace('#', '').replace('0X', '')
        if len(text) != 6:
            return fallback
        int(text, 16)
        return text
    except Exception:
        return fallback


class inq_hpoldSettings(object):
    def __init__(self):
        self.values = dict(DEFAULTS)
        self._registered = False
        self._uiHooked = False

    def initialize(self):
        self._hookUIReady()
        if self._registered or g_modsSettingsApi is None:
            if g_modsSettingsApi is None:
                logger.info('inq_hpold ModsSettingsAPI is unavailable; using default settings')
            return

        template = {
            'modDisplayName': u'inq_hpold',
            'enabled': True,
            'column1': [
                {
                    'type': 'CheckBox',
                    'text': u'Показувати смуги HP',
                    'tooltip': u'{HEADER}Смуги HP{/HEADER}{BODY}Вимкни, щоб у вухах залишалося тільки числове значення HP без чотирьох сегментів.{/BODY}',
                    'value': DEFAULTS['showHpBars'],
                    'varName': 'showHpBars'
                },
                {
                    'type': 'CheckBox',
                    'text': u'HP противників червоним',
                    'tooltip': u'{HEADER}Червоні HP противників{/HEADER}{BODY}Фарбувати заповнені сегменти HP противників у червоний колір. Числове значення HP залишається сірим.{/BODY}',
                    'value': DEFAULTS['enemyHpRed'],
                    'varName': 'enemyHpRed'
                },
                {
                    'type': 'CheckBox',
                    'text': u'Фарбувати іконки техніки',
                    'tooltip': u'{HEADER}Фарбування іконок{/HEADER}{BODY}Використовувати власні кольори для класів техніки у вухах команд.{/BODY}',
                    'value': DEFAULTS['colorizeIcons'],
                    'varName': 'colorizeIcons'
                },
                {
                    'type': 'ColorChoice',
                    'text': u'ЛТ — колір іконки',
                    'tooltip': u'{HEADER}Колір ЛТ{/HEADER}{BODY}Колір іконок легких танків. За замовчуванням #%s.{/BODY}' % DEFAULTS['ltColor'],
                    'value': DEFAULTS['ltColor'],
                    'varName': 'ltColor'
                },
                {
                    'type': 'ColorChoice',
                    'text': u'СТ — колір іконки',
                    'tooltip': u'{HEADER}Колір СТ{/HEADER}{BODY}Колір іконок середніх танків. За замовчуванням #%s.{/BODY}' % DEFAULTS['mtColor'],
                    'value': DEFAULTS['mtColor'],
                    'varName': 'mtColor'
                },
                {
                    'type': 'ColorChoice',
                    'text': u'ПТ — колір іконки',
                    'tooltip': u'{HEADER}Колір ПТ{/HEADER}{BODY}Колір іконок ПТ-САУ. За замовчуванням #%s.{/BODY}' % DEFAULTS['tdColor'],
                    'value': DEFAULTS['tdColor'],
                    'varName': 'tdColor'
                }
            ],
            'column2': [
                {
                    'type': 'ColorChoice',
                    'text': u'САУ — колір іконки',
                    'tooltip': u'{HEADER}Колір САУ{/HEADER}{BODY}Колір іконок артилерії. За замовчуванням #%s.{/BODY}' % DEFAULTS['spgColor'],
                    'value': DEFAULTS['spgColor'],
                    'varName': 'spgColor'
                },
                {
                    'type': 'CheckBox',
                    'text': u'Фарбувати ТТ',
                    'tooltip': u'{HEADER}Фарбування ТТ{/HEADER}{BODY}За замовчуванням важкі танки залишаються штатно сірими. Увімкни, щоб застосувати вибраний нижче колір.{/BODY}',
                    'value': DEFAULTS['colorizeHeavy'],
                    'varName': 'colorizeHeavy'
                },
                {
                    'type': 'ColorChoice',
                    'text': u'ТТ — колір іконки',
                    'tooltip': u'{HEADER}Колір ТТ{/HEADER}{BODY}Використовується тільки якщо увімкнено «Фарбувати ТТ».{/BODY}',
                    'value': DEFAULTS['heavyColor'],
                    'varName': 'heavyColor'
                }
            ]
        }

        try:
            saved = g_modsSettingsApi.setModTemplate(
                MOD_LINKAGE,
                template,
                self._onSettingsChanged
            )
            if saved:
                self._apply(saved)
            self._registered = True
            logger.info('inq_hpold settings registered in ModsSettingsAPI')
        except Exception:
            logger.exception('Could not register inq_hpold settings')

    def _hookUIReady(self):
        if self._uiHooked:
            return
        try:
            from .player_panel import g_events
            g_events.onUIReady += self._applyDisplayToFlash
            self._uiHooked = True
        except Exception:
            logger.exception('Could not hook inq_hpold settings to UI ready')

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
        if not values:
            return
        if 'enabled' in values:
            self.values['enabled'] = bool(values['enabled'])
        if 'showHpBars' in values:
            self.values['showHpBars'] = bool(values['showHpBars'])
        if 'enemyHpRed' in values:
            self.values['enemyHpRed'] = bool(values['enemyHpRed'])
        if 'colorizeIcons' in values:
            self.values['colorizeIcons'] = bool(values['colorizeIcons'])
        if 'colorizeHeavy' in values:
            self.values['colorizeHeavy'] = bool(values['colorizeHeavy'])

        for key in ('ltColor', 'mtColor', 'tdColor', 'spgColor', 'heavyColor'):
            if key in values:
                self.values[key] = _normalize_color(values[key], DEFAULTS[key])

    def _applyDisplayToFlash(self, *args):
        try:
            from .player_panel import g_events
            g_events.setDisplaySettings(*self.displaySettings())
        except Exception:
            logger.exception('Could not apply inq_hpold display settings to Flash')

    def _onSettingsChanged(self, linkage, newSettings):
        if linkage != MOD_LINKAGE:
            return
        self._apply(newSettings)
        self._applyDisplayToFlash()
        try:
            from .provider import g_provider
            g_provider.applySettings()
        except Exception:
            logger.exception('Could not apply changed inq_hpold settings')

    def isEnabled(self):
        return bool(self.values.get('enabled', True))

    def displaySettings(self):
        return (
            bool(self.values.get('showHpBars', True)),
            bool(self.values.get('enemyHpRed', False))
        )

    def iconSettings(self):
        return (
            bool(self.values.get('colorizeIcons', True)) and self.isEnabled(),
            bool(self.values.get('colorizeHeavy', False)),
            int(self.values.get('ltColor', DEFAULTS['ltColor']), 16),
            int(self.values.get('mtColor', DEFAULTS['mtColor']), 16),
            int(self.values.get('tdColor', DEFAULTS['tdColor']), 16),
            int(self.values.get('spgColor', DEFAULTS['spgColor']), 16),
            int(self.values.get('heavyColor', DEFAULTS['heavyColor']), 16)
        )


g_settings = inq_hpoldSettings()
