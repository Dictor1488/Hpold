#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build independent Hpold .wotmod using original visual assets.

Usage:
  python build.py --reference playersPanelHP_1.2.4.zip --version 2.4.1.0

The reference ZIP is used ONLY at build time to extract the original
players-panel injector SWF; it is NOT bundled with modsCore Python code.
No third-party core is required at game runtime.
"""
import argparse
import io
import os
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT_NAMES = ('mod_hpold.py', 'hpold_bridge.py')
SWF = 'res/gui/flash/playersPanelAPI_modsCore.swf'


def original_swf(path):
    with zipfile.ZipFile(path) as outer:
        core = next((n for n in outer.namelist()
                     if n.endswith('/oldskool.modscore_1.4.1.wotmod')), None)
        if core is None:
            raise RuntimeError('Original modsCore wotmod missing from reference')
        with zipfile.ZipFile(io.BytesIO(outer.read(core))) as inner:
            return inner.read(SWF)


def build(reference, version, output):
    swf = original_swf(reference)
    meta = ('<root><id>hpold</id><version>0.1.0</version>'
            '<name>Hpold Independent HP Bars</name>'
            '<description>Standalone PlayersPanel HP Bars</description></root>')
    ET.fromstring(meta)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as dest:
        dest.writestr('meta.xml', meta)
        dest.writestr(SWF, swf)
        for name in SCRIPT_NAMES:
            src = os.path.join(ROOT, 'res', 'scripts', 'client', 'gui', 'mods', name)
            dest.write(src, 'res/scripts/client/gui/mods/' + name)
        for name in ('hp_alive_cb.png', 'hp_alive_l.png', 'hp_alive_r.png', 'hp_bg.png'):
            src = os.path.join(ROOT, 'hpbars', name)
            dest.write(src, 'res/gui/hpbars/' + name)
    with zipfile.ZipFile(output) as check:
        assert check.testzip() is None
        assert SWF in check.namelist()
    print('Built:', output)
    print('Copy .wotmod into mods/%s/ of the WoT client.' % version)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True)
    parser.add_argument('--version', default='2.4.1.0')
    parser.add_argument('--output', default='hpold_0.1.0.wotmod')
    opts = parser.parse_args()
    build(opts.reference, opts.version, opts.output)
