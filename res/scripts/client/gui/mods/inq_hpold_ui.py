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

    def _rows(self):
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        from gui.battle_control.arena_info import vos_collections
        from gui.battle_control import avatar_getter
        provider = dependency.instance(IBattleSessionProvider)
        arenaDP = provider.getArenaDP()
        if arenaDP is None:
            return []
        observer = arenaDP.isPlayerObserver()
        result = []
        counters = {'left': 0, 'right': 0}
        collection = vos_collections.VehiclesItemsCollection(
            sortKey=vos_collections.VehicleInfoSortKey)
        for info, stats in collection.iterator(arenaDP):
            if info.isObserver():
                continue
            ally = (avatar_getter.getPlayerTeam() == info.team
                    if observer else arenaDP.isAllyTeam(info.team))
            side = 'left' if ally else 'right'
            position = counters[side]
            counters[side] += 1
            record = self.entries.get(str(info.vehicleID))
            if record is None:
                continue
            values = record['fields']
            # The controller's HTML text contains health/max and the bar width.
            # Use the separately supplied raw HP values for Gameface instead.
            result.append({'vehicleID': info.vehicleID, 'side': side,
                           'index': position, 'current': record.get('current', 0),
                           'max': record.get('max', 1),
                           'show': record.get('show', False),
                           'colorblind': record.get('colorblind', False)})
        return result

    def publish(self):
        if self.view is not None:
            try:
                rows = self._rows()
            except Exception:
                LOG.exception('Unable to resolve team panel row order')
                rows = []
            self.view.publish({'visible': self.active, 'rows': rows})

    def update_hp(self, vehicleID, current, maximum, shown, colorblind=False):
        record = self.entries.get(str(vehicleID))
        if record is None:
            return
        record.update({'current': int(current), 'max': int(maximum),
                       'show': bool(shown), 'colorblind': bool(colorblind)})
        self.publish()

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
