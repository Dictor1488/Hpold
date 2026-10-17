"""Gameface package smoke tests."""
import unittest
from pathlib import Path
import tempfile
import zipfile
import build


class BuildTests(unittest.TestCase):
    def test_all_gameface_assets_packaged(self):
        entries = build.content()
        self.assertIn(build.RESOURCE, entries)
        for name in build.GF_FILES:
            self.assertIn('res/gui/gameface/mods/inq_hpold/panel/' + name, entries)
        self.assertNotIn('res/gui/flash/inq_hpold.swf', entries)

    def test_deterministic_build(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / 'one.wotmod'
            second = Path(folder) / 'two.wotmod'
            self.assertEqual(build.create_wotmod(first), build.create_wotmod(second))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())


if __name__ == '__main__':
    unittest.main()
