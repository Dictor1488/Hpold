# -*- coding: utf-8 -*-
from .logger import logger
from .player_panel import initialize_panel, finalize_panel
from .provider import HealthProvider, install_hooks, remove_hooks
from .settings import g_settings
from .vehicle_class import resolve_vehicle_class

_initialized = False


def _getVehicleClass(self, vehicleData):
    try:
        return resolve_vehicle_class(vehicleData) or ''
    except Exception:
        logger.exception('inq_hpold vehicle class resolver failed')
        return ''


# Use only the current client-compatible vehicle-class resolver.
HealthProvider._getVehicleClass = _getVehicleClass


def initialize():
    global _initialized
    if _initialized:
        return
    initialize_panel()
    g_settings.initialize()
    install_hooks()
    _initialized = True
    logger.info('inq_hpold initialized')


def finalize():
    global _initialized
    if not _initialized:
        return
    remove_hooks()
    g_settings.finalize()
    finalize_panel()
    _initialized = False
    logger.info('inq_hpold finalized')
