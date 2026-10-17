# -*- coding: utf-8 -*-
"""Hpold independent interface contract.

UI implementation must call register_renderer(renderer) with an object
implementing create_field(name, definition), update_field(name, vehicleID, text),
and optionally close(). No dependency on OldSkool.
"""
_renderer = None
_active_bridges = []


def register_renderer(renderer):
    global _renderer
    _renderer = renderer
    for bridge in list(_active_bridges):
        bridge._create_fields()
        bridge.flush()


def unregister_renderer(renderer):
    global _renderer
    if _renderer is renderer:
        _renderer = None


class Bridge(object):
    def __init__(self):
        self._open = False
        self._templates = {}
        self._state = {}

    def open(self, templates=None):
        self._open = True
        self._templates = templates or {}
        if self not in _active_bridges:
            _active_bridges.append(self)
        self._create_fields()

    def _create_fields(self):
        if not self._open or _renderer is None:
            return
        for name, definition in sorted(self._templates.iteritems()):
            _renderer.create_field('HPbars_' + name, definition)

    def update_vehicle(self, vehicleID, side, fields):
        if not self._open:
            return
        self._state[vehicleID] = (side, dict(fields))
        if _renderer is not None:
            for field, text in fields.iteritems():
                _renderer.update_field(field, vehicleID, text)

    def flush(self):
        if not self._open or _renderer is None:
            return
        for vehicleID, pair in self._state.iteritems():
            for field, text in pair[1].iteritems():
                _renderer.update_field(field, vehicleID, text)

    def close(self):
        if self in _active_bridges:
            _active_bridges.remove(self)
        self._open = False
        self._state.clear()
        if _renderer is not None and hasattr(_renderer, 'close'):
            _renderer.close()
