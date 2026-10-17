#!/usr/bin/env python3
"""Package the native, vehicle-row-attached implementation.

Requires Python 2.7 to compile client files and a compiled, independent
as3/bin/inq_hpold.swf produced from this repository's ActionScript sources.
The build intentionally fails if either prerequisite is absent.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
NATIVE = ROOT / 'python'
SWF = ROOT / 'as3/bin/inq_hpold.swf'
OUTPUT = ROOT / 'build/inq_hpold_native_0.2.0-test.wotmod'


def build(python27):
    if not SWF.exists():
        raise RuntimeError('Missing independently compiled as3/bin/inq_hpold.swf')
    if SWF.read_bytes()[:3] not in (b'FWS', b'CWS', b'ZWS'):
        raise RuntimeError('Invalid SWF signature')
    files = {}
    for src in NATIVE.rglob('*.py'):
        subprocess.check_call([python27, '-m', 'py_compile', str(src)])
        pyc = src.with_suffix('.pyc')
        try:
            blob = pyc.read_bytes()
            if blob[:4] != b'\x03\xf3\r\n':
                raise RuntimeError('Invalid Python 2.7 code: ' + str(src))
            files['res/scripts/client/' + str(src.relative_to(NATIVE).with_suffix('.pyc')).replace('\\', '/')] = blob
        finally:
            pyc.unlink(missing_ok=True)
    files['res/gui/flash/inq_hpold.swf'] = SWF.read_bytes()
    files['meta.xml'] = (b'<?xml version="1.0" encoding="utf-8"?>'
                         b'<root><id>inq_hpold</id><version>0.2.0-test</version>'
                         b'<name>inq_hpold</name><description>Native HP row renderer</description></root>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w') as archive:
        for path, value in sorted(files.items()):
            entry = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_STORED
            archive.writestr(entry, value)
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
    print(OUTPUT, hashlib.sha256(OUTPUT.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--python27', required=True)
    args = parser.parse_args()
    try:
        build(args.python27)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        sys.exit('Native package failed: ' + str(error))
