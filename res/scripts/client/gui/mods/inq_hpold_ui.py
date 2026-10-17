# -*- coding: utf-8 -*-
"""Standalone Gameface/Wulf view for inq_hpold."""
import json
import logging
import BigWorld
from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer
from gui.impl.pub import ViewImpl, WindowImpl
from skeletons.gui.impl import IGuiLoader
from helpers import dependency

LOG = logging.getLogger('inq_hpold')
LAYOUT = 'mods/inq_hpold/panel/layoutID'


class HPModel(ViewModel):
    def __init__(self):
        super(HPModel, self).__init__(properties=1, commands=1)

    def _initialize(self):
        super(HPModel, self)._initialize()
        self._addStringProperty('payload', '{}')

    def setPayload(self, payload):
        self._setString(0, payload)


class HPView(ViewImpl):
    def __init__(self):
        from openwg_gameface import ModDynAccessor
        layout_id = ModDynAccessor(LAYOUT)()
        super(HPView, self).__init__(
            ViewSettings(layout_id, flags=ViewFlags.VIEW, model=HPModel()))

    def publish(self, state):
        try:
            with self.getViewModel().transaction() as model:
                model.setPayload(json.dumps(state, separators=(',', ':')))
        except Exception:
            LOG.exception('Failed to publish UI state')


class Bridge(object):
    def __init__(self):
        self.window = None
        self.view = None
        self.active = False
        self.entries = {}
        self.retry_id = None
        self.generation = 0

    def open(self, templates=None):
        self.active = True
        self.generation += 1
        self.entries.clear()
        self._load(self.generation, 0)

    def _load(self, generation, tries):
        self.retry_id = None
        if not self.active or generation != self.generation or self.window is not None:
            return
        try:
            from openwg_gameface import ModDynAccessor
            parent = dependency.instance(IGuiLoader).windowsManager.getMainWindow()
            if parent is None or getattr(parent, 'proxy', None) is None:
                raise RuntimeError('Main window not ready')
            view = HPView()
            window = WindowImpl(WindowFlags.WINDOW | WindowFlags.WINDOW_FULLSCREEN,
                                content=view, layer=WindowLayer.OVERLAY,
                                name='inq_hpold', parent=parent)
            window.load()
            self.window = window
            self.view = view
            self.publish()
        except Exception:
            if tries < 80:
                self.retry_id = BigWorld.callback(
                    0.15, lambda: self._load(generation, tries + 1))
            elif tries == 80:
                LOG.exception('Gameface overlay unavailable')

    def update_vehicle(self, vehicleID, side, fields):
        if not self.active:
            return
        self.entries[str(vehicleID)] = {'vehicleID': vehicleID, 'side': side,
                                        'fields': dict(fields)}
        self.publish()

    def publish(self):
        if self.view is not None:
            self.view.publish({'visible': self.active, 'vehicles': self.entries})

    def close(self):
        self.active = False
        self.generation += 1
        if self.retry_id is not None:
            try:
                BigWorld.cancelCallback(self.retry_id)
            except Exception:
                pass
            self.retry_id = None
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                LOG.exception('Failed to close UI')
        self.window = None
        self.view = None
        self.entries.clear()
