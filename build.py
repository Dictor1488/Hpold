#!/usr/bin/env python3
"""Build an installable inq_hpold WOTMOD with Python 2.7 bytecode."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION = '0.1.0-rc2'
SOURCES = (
    'res/scripts/client/gui/mods/mod_inq_hpold.py',
    'res/scripts/client/gui/mods/inq_hpold_ui.py',
)
IMAGES = ('hp_alive_cb.png', 'hp_alive_l.png', 'hp_alive_r.png', 'hp_bg.png')
PANEL = 'res/gui/gameface/mods/inq_hpold/panel/'
UI_FILES = ('Panel.html', 'Panel.css', 'Panel.js')
RESOURCE = 'res/gui/gen_resources/tv.inq.hpold.json'
PYC_MAGIC = b'\x03\xf3\r\n'


def assets():
    entries = {}
    for name in UI_FILES:
        entries[PANEL + name] = (ROOT / PANEL / name).read_bytes()
    entries[RESOURCE] = (ROOT / RESOURCE).read_bytes()
    for name in IMAGES:
        data = (ROOT / 'hpbars' / name).read_bytes()
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Invalid PNG: ' + name)
        entries[PANEL + name] = data
    json.loads(entries[RESOURCE].decode('utf-8'))
    return entries


def compile_scripts(python27):
    if not python27:
        raise ValueError('Python 2.7 required. Pass --python27 PATH')
    compiled = {}
    for relative in SOURCES:
        source = ROOT / relative
        result = subprocess.run(
            [str(python27), '-m', 'py_compile', str(source)],
            capture_output=True, text=True
        )
        if result.returncode:
            raise RuntimeError('Python 2.7 compile failed: %s\n%s\n%s' %
                               (relative, result.stdout, result.stderr))
        pyc = source.with_suffix('.pyc')
        try:
            data = pyc.read_bytes()
        finally:
            pyc.unlink(missing_ok=True)
        if not data.startswith(PYC_MAGIC):
            raise ValueError('Bad Python 2.7 magic: ' + relative)
        compiled[relative + 'c'] = data
    return compiled


def contents(python27):
    entries = assets()
    entries.update(compile_scripts(python27))
    root = ET.Element('root')
    for key, value in (
        ('id', 'inq_hpold'),
        ('version', VERSION),
        ('name', 'inq_hpold'),
        ('description', 'Standalone Gameface HP indicators'),
    ):
        ET.SubElement(root, key).text = value
    entries['meta.xml'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    return entries


def create_wotmod(output, python27):
    entries = contents(python27)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for path, content in sorted(entries.items()):
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(entries):
            raise RuntimeError('Invalid WOTMOD archive')
        for entry in archive.infolist():
            if entry.compress_type != zipfile.ZIP_STORED:
                raise RuntimeError('Unexpected archive compression: ' + entry.filename)
        for name, value in entries.items():
            if archive.read(name) != value:
                raise RuntimeError('Invalid payload: ' + name)
    print('Built:', output, 'SHA256:', hashlib.sha256(output.read_bytes()).hexdigest())
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python27', help='Python 2.7 interpreter used for client bytecode')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'build' / ('inq_hpold_' + VERSION + '.wotmod'))
    opts = parser.parse_args()
    try:
        entries = assets()
        if opts.check:
            for source in SOURCES:
                if not (ROOT / source).is_file():
                    raise FileNotFoundError(source)
            print('Sources validated:', len(entries), 'assets')
        else:
            create_wotmod(opts.output, opts.python27)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print('BUILD FAILED:', exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
