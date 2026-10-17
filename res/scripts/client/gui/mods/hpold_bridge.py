# -*- coding: utf-8 -*-
"""Hpold UI boundary.

This module is deliberately independent from modsCore. The original interface
uses a proprietary SWF (playersPanelAPI_modsCore.swf). Until a replacement view
and its binding are implemented, this bridge buffers state without claiming
that it is visually rendering HP bars.
"""
class Bridge(object):
    def __init__(self):
        self._open = False
        self._values = {}
        self._mode = 0

    def open(self):
        self._open = True

    def close(self):
        self._open = False
        self._values.clear()

    def set_mode(self, value):
        self._mode = int(value)

    def update(self, snapshot):
        if self._open:
            self._values = dict(snapshot)
