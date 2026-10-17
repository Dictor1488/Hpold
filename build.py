#!/usr/bin/env python3
"""Package the standalone OldSkool-style inq_hpold player panel."""
from pathlib import Path
import argparse
import os
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = os.environ.get('PROJECT_VERSION', '0.2.0')
ASSETS = (
    'res/gui/hpbars/hp_bg.png',
    'res/gui/hpbars/hp_alive_l.png',
    'res/gui/hpbars/hp_alive_r.png',
    'res/gui/hpbars/hp_alive_cb.png',
)


def build(python27):
    entries = {}
    for name in ASSETS:
        path = ROOT / 'vendor' / name
        if not path.is_file():
            raise RuntimeError('Missing bundled asset: {}'.format(path))
        entries[name] = path.read_bytes()

    swf = ROOT / 'as3' / 'bin' / 'inq_hpold.swf'
    if not swf.is_file() or swf.read_bytes()[:3] not in (b'FWS', b'CWS', b'ZWS'):
        raise RuntimeError('Compile inq_hpold.swf from AS3 before packaging')
    entries['res/gui/flash/inq_hpold.swf'] = swf.read_bytes()

    for src in sorted((ROOT / 'python').rglob('*.py')):
        subprocess.check_call([python27, '-m', 'py_compile', str(src)])
        pyc = src.with_suffix('.pyc')
        try:
            raw = pyc.read_bytes()
            if raw[:4] != bytes.fromhex('03f30d0a'):
                raise RuntimeError('Requires Python 2.7 bytecode: {}'.format(src))
            dest = 'res/scripts/client/' + src.relative_to(ROOT / 'python').with_suffix('.pyc').as_posix()
            entries[dest] = raw
        finally:
            pyc.unlink(missing_ok=True)

    meta = ET.Element('root')
    for key, value in (
        ('id', 'inq_hpold'),
        ('version', VERSION),
        ('name', 'inq_hpold'),
        ('description', 'Standalone OldSkool-style players-panel HP'),
    ):
        ET.SubElement(meta, key).text = value
    entries['meta.xml'] = ET.tostring(meta, encoding='utf-8', xml_declaration=True)

    output = ROOT / 'build' / ('inq_hpold_' + VERSION + '.wotmod')
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)

    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(ASSETS).issubset(set(archive.namelist()))
        assert 'res/gui/flash/inq_hpold.swf' in archive.namelist()
    print('Built:', output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--python27', required=True)
    args = parser.parse_args()
    build(args.python27)
