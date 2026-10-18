import tempfile
import unittest
from pathlib import Path

from pi.runtime.godot_check import PACKAGE_ROOT, SOURCE, command, stage


class GodotCheckTests(unittest.TestCase):
    def test_godot_stage_requires_approval_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "project.yaml").write_text("engine:\n  name: Godot\n  version: 4.6\n")
            (root / "src").mkdir()
            (root / "src/test.gd").write_text("extends Node\n")
            with self.assertRaises(PermissionError):
                stage(root)
            self.assertFalse((root / "addons").exists())
            created = stage(root, approved=True)
            self.assertEqual(created.read_bytes(), SOURCE.read_bytes())
            self.assertEqual(stage(root, approved=True), created)
            result = command(root, ("src/test.gd",))
            self.assertEqual(result[0:5], ["godot", "--headless", "--path", str(root), "-s"])
            self.assertEqual(result[-1], "res://src/test.gd")
            for path in ("../../README.md", "res://../../project.yaml", "src/not-there.gd"):
                with self.subTest(path=path), self.assertRaises((ValueError, FileNotFoundError)):
                    command(root, [path])
            created.write_text("modified")
            with self.assertRaises(FileExistsError):
                stage(root, approved=True)
            with self.assertRaises(FileNotFoundError):
                command(root, ["src/test.gd"])

    def test_wrong_engine_framework_and_escaping_symlink_are_refused(self):
        with self.assertRaisesRegex(ValueError, "separate game root"):
            stage(PACKAGE_ROOT, approved=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "game"
            root.mkdir()
            (root / "project.yaml").write_text("engine:\n  name: Unity\n")
            with self.assertRaisesRegex(ValueError, "Godot"):
                stage(root, approved=True)
            (root / "project.yaml").write_text("engine:\n  name: Godot\n")
            (root / "addons").symlink_to(Path(directory))
            with self.assertRaisesRegex(ValueError, "symlink"):
                stage(root, approved=True)


if __name__ == "__main__":
    unittest.main()
