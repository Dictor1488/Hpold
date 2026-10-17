# -*- coding: utf-8 -*-
"""Packaging smoke tests, independent of a WoT installation."""
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

import build


class BuildTests(unittest.TestCase):
    def test_deterministic_wotmod(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)
            reference = work / 'reference.zip'
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, 'w') as archive:
                archive.writestr(build.SWF_PATH, b'CWS' + b'\0' * 30)
            with zipfile.ZipFile(reference, 'w') as archive:
                archive.writestr('mods/2.4.0.0/oldskool/oldskool.modscore_1.4.1.wotmod',
                                 inner.getvalue())
            first, second = work / 'one.wotmod', work / 'two.wotmod'
            self.assertEqual(build.create_wotmod(reference, first),
                             build.create_wotmod(reference, second))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                files = set(archive.namelist())
                self.assertIn('meta.xml', files)
                self.assertIn(build.SWF_PATH, files)
                for path in build.PY_PATHS:
                    self.assertIn(path, files)
                for png in build.NAMES:
                    self.assertIn('res/gui/hpbars/' + png, files)
                self.assertNotIn('res/scripts/client/gui/oldskool/__init__.py', files)


if __name__ == '__main__':
    unittest.main()
