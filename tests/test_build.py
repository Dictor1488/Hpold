"""Validate package assets without a WoT installation."""
import unittest
import json
import build


class BuildTests(unittest.TestCase):
    def test_assets(self):
        entries = build.assets()
        self.assertIn(build.RESOURCE, entries)
        for name in build.UI_FILES:
            self.assertIn(build.PANEL + name, entries)
        for name in build.IMAGES:
            self.assertIn(build.PANEL + name, entries)
        config = json.loads(entries[build.RESOURCE].decode('utf-8'))
        self.assertEqual(config[0]['parameters']['impl'], 'gameface')

    def test_client_python_sources(self):
        for name in build.SOURCES:
            self.assertTrue((build.ROOT / name).is_file())

    def test_compiler_is_mandatory(self):
        with self.assertRaises(ValueError):
            build.compile_scripts(None)


if __name__ == '__main__':
    unittest.main()
