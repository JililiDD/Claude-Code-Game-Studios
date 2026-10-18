import tempfile
import unittest
from pathlib import Path

from pi.runtime.code_root import PACKAGE_ROOT, resolve


class CodeRootTests(unittest.TestCase):
    def test_configured_roots_three_engines_and_unambiguous_tree_fallback(self):
        for engine, directory in (("Godot", "src"), ("Unity", "Assets"), ("Unreal", "Source")):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as game:
                root = Path(game)
                (root / "project.yaml").write_text(f"engine:\n  name: {engine}\n")
                self.assertEqual(resolve(root)[0], directory)
        with tempfile.TemporaryDirectory() as game:
            root = Path(game)
            (root / "Assets").mkdir()
            self.assertEqual(resolve(root), ("Assets", "detected"))
            (root / "src").mkdir()
            self.assertEqual(resolve(root), (None, "unset"))

    def test_invalid_yaml_framework_and_empty_game_fail_or_remain_unassessed(self):
        with self.assertRaisesRegex(ValueError, "independent"):
            resolve(PACKAGE_ROOT)
        with tempfile.TemporaryDirectory() as game:
            root = Path(game)
            self.assertEqual(resolve(root), (None, "unset"))
            (root / "project.yaml").write_text("engine: [bad\n")
            with self.assertRaisesRegex(ValueError, "malformed YAML"):
                resolve(root)


if __name__ == "__main__":
    unittest.main()
