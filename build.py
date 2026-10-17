#!/usr/bin/env python3
"""Build inq_hpold without downloading or extracting third-party modules."""
import argparse
import hashlib
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = '0.1.0-rc1'
SCRIPT_PATHS = (
    'res/scripts/client/gui/mods/mod_inq_hpold.py',
    'res/scripts/client/gui/mods/inq_hpold_ui.py',
)
IMAGE_NAMES = ('hp_alive_cb.png', 'hp_alive_l.png', 'hp_alive_r.png', 'hp_bg.png')
UI_ASSET = ROOT / 'assets' / 'inq_hpold.swf'
UI_DEST = 'res/gui/flash/inq_hpold.swf'


def content():
    if not UI_ASSET.is_file():
        raise FileNotFoundError(
            'Missing independent UI asset assets/inq_hpold.swf. '
            'No external UI will be substituted.'
        )
    swf = UI_ASSET.read_bytes()
    if swf[:3] not in (b'FWS', b'CWS', b'ZWS'):
        raise ValueError('Invalid inq_hpold.swf')
    entries = {UI_DEST: swf}
    for name in SCRIPT_PATHS:
        entries[name] = (ROOT / name).read_bytes()
    for name in IMAGE_NAMES:
        data = (ROOT / 'hpbars' / name).read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Invalid PNG: ' + name)
        entries['res/gui/hpbars/' + name] = data
    metadata = ('<root><id>inq_hpold</id><version>%s</version>'
                '<name>inq_hpold</name>'
                '<description>Players panel HP indicators</description></root>' % VERSION).encode('utf-8')
    ET.fromstring(metadata)
    entries['meta.xml'] = metadata
    return entries


def create_wotmod(output):
    entries = content()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(output), 'w') as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(str(output)) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(entries)
        assert all(archive.read(name) == data for name, data in entries.items())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print('Built:', output)
    print('SHA256:', digest)
    return digest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'dist' / ('inq_hpold_' + VERSION + '.wotmod'))
    args = parser.parse_args()
    try:
        if args.check:
            print('Validated %d entries' % len(content()))
        else:
            create_wotmod(args.output)
    except (ValueError, OSError, zipfile.BadZipFile) as err:
        parser.exit(1, 'BUILD FAILED: %s\n' % err)
