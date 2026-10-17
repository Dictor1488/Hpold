# -*- coding: utf-8 -*-
from inq_hpold_native import initialize, finalize
from inq_hpold_native.logger import logger

__version__ = '0.1.0'
__author__ = 'Dictor1488'
__mod_name__ = 'inq_hpold'


def init():
    try:
        logger.info('loading inq_hpold v%s', __version__)
        initialize()
        logger.info('inq_hpold loaded')
    except Exception:
        logger.exception('inq_hpold initialization failed')


def fini():
    try:
        finalize()
        logger.info('inq_hpold unloaded')
    except Exception:
        logger.exception('inq_hpold finalization failed')
