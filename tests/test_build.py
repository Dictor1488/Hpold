"""Packaging tests for inq_hpold."""
import unittest
from pathlib import Path
from unittest import mock
import tempfile
import build


class BuildTests(unittest.TestCase):
    def test_missing_ui_fails_cleanly(self):
        with mock.patch.object(build, 'UI_ASSET', Path('/not-a-file/inq_hpold.swf')):
            with self.assertRaises(FileNotFoundError):
                build.content()

    def test_deterministic_build_with_valid_ui(self):
        with tempfile.TemporaryDirectory() as folder:
            asset = Path(folder) / 'inq_hpold.swf'
            asset.write_bytes(b'CWS' + b'\0' * 30)
            with mock.patch.object(build, 'UI_ASSET', asset):
                first = Path(folder) / 'one.wotmod'
                second = Path(folder) / 'two.wotmod'
                self.assertEqual(build.create_wotmod(first), build.create_wotmod(second))
                self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == '__main__':
    unittest.main()
