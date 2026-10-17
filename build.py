#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the standalone Hpold WOTMOD (no OldSkool Python runtime).

python build.py --reference /path/to/playersPanelHP_1.2.4.zip
python build.py --reference /path/to/playersPanelHP_1.2.4.zip --check

The reference is an INPUT to the build process, not a dependency in game.
The only reused core component is the small Scaleform UI SWF.
"""
import argparse
import hashlib
import io
import re
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = '0.1.0-rc1'
NAMES = ('hp_alive_cb.png', 'hp_alive_l.png', 'hp_alive_r.png', 'hp_bg.png')
SWF_PATH = 'res/gui/flash/playersPanelAPI_modsCore.swf'
PY_PATHS = (
    'res/scripts/client/gui/mods/mod_hpold.py',
    'res/scripts/client/gui/mods/hpold_bridge.py',
)


def get_swf(reference):
    with zipfile.ZipFile(reference) as z:
        candidates = [name for name in z.namelist()
                      if name.endswith('/oldskool.modscore_1.4.1.wotmod')]
        if len(candidates) != 1:
            raise ValueError('Expected exactly one oldskool.modscore_1.4.1.wotmod')
        with zipfile.ZipFile(io.BytesIO(z.read(candidates[0]))) as core:
            swf = core.read(SWF_PATH)
    if swf[:3] not in (b'FWS', b'CWS', b'ZWS'):
        raise ValueError('Invalid player-panel SWF signature')
    return swf


def content(reference):
    entries = {SWF_PATH: get_swf(reference)}
    for relative in PY_PATHS:
        entries[relative] = (ROOT / relative).read_bytes()
    for png in NAMES:
        blob = (ROOT / 'hpbars' / png).read_bytes()
        if not blob.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Invalid PNG: ' + png)
        entries['res/gui/hpbars/' + png] = blob
    metadata = (
        '<root><id>hpold</id><version>%s</version>'
        '<name>Hpold - Players Panel HP</name>'
        '<description>Standalone HP bars; independent of modsCore</description>'
        '</root>' % VERSION
    ).encode('utf-8')
    ET.fromstring(metadata)
    entries['meta.xml'] = metadata
    # Match only actual import statements, not documentation or comments.
    # Runtime scripts are Python 2.7, so Python 3's ast.parse cannot parse them.
    forbidden_import = re.compile(
        rb'^\\s*(?:from\\s+(?:gui\\.)?oldskool(?:\\.|\\s+)|'
        rb'import\\s+(?:gui\\.)?oldskool(?:\\.|\\s|$))',
        re.MULTILINE
    )
    for name in PY_PATHS:
        if forbidden_import.search(entries[name]):
            raise ValueError('Unexpected OldSkool dependency in ' + name)
    return entries


def create_wotmod(reference, output):
    entries = content(reference)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            archive.writestr(zi, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(str(output)) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == sorted(entries)
        for name, blob in entries.items():
            assert archive.read(name) == blob, name
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    print('Built:', output)
    print('SHA256:', sha)
    print('Files:', len(entries))
    print('Install into WoT mods/2.4.1.0/')
    return sha


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'dist' / ('hpold_' + VERSION + '.wotmod'))
    parser.add_argument('--check', action='store_true',
                        help='validate inputs without creating an artifact')
    args = parser.parse_args()
    try:
        if args.check:
            entries = content(args.reference)
            print('Inputs validated:', len(entries), 'files')
        else:
            create_wotmod(args.reference, args.output)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as exc:
        print('BUILD FAILED:', exc, file=sys.stderr)
        sys.exit(1)
