import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from pi.runtime.migrate import FRAMEWORK, migration


class MigrateTests(unittest.TestCase):
    def test_dry_run_approval_migration_and_separate_finalization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "production/stage.txt"
            legacy.parent.mkdir()
            legacy.write_text("Systems Design\n")
            original = legacy.read_bytes()
            preview = migration(root)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn("DRY RUN", preview.stdout)
            self.assertFalse((root / "project.yaml").exists())
            self.assertEqual(legacy.read_bytes(), original)
            with self.assertRaisesRegex(PermissionError, "approval for migrate"):
                migration(root, "migrate")
            applied = migration(root, "migrate", approved=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertIn("Systems Design", (root / "project.yaml").read_text())
            report = (root / "production/migration-report.md").read_text()
            self.assertIn("--mode finalize --approved", report)
            self.assertIn("separate explicit approval", report)
            self.assertIn("/skill:settings", report)
            self.assertNotIn("bash .claude/scripts/migrate-v1-config.sh --finalize", report)
            self.assertTrue(legacy.exists(), "Migrate must leave originals in place")
            with self.assertRaisesRegex(PermissionError, "approval for finalize"):
                migration(root, "finalize")
            final = migration(root, "finalize", approved=True)
            self.assertEqual(final.returncode, 0, final.stderr)
            self.assertFalse(legacy.exists())

    def test_claude_default_migration_still_prints_original_finalize_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "production/stage.txt"
            legacy.parent.mkdir()
            legacy.write_text("Systems Design\n")
            env = os.environ.copy()
            env["CCGS_GAME_ROOT"] = str(root)
            for key in ("CCGS_MIGRATION_LABEL", "CCGS_MIGRATION_FINALIZE_CMD",
                        "CCGS_SETTINGS_CMD", "CCGS_START_CMD"):
                env.pop(key, None)
            run = subprocess.run(["bash", str(FRAMEWORK / ".claude/scripts/migrate-v1-config.sh")],
                                 cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("bash .claude/scripts/migrate-v1-config.sh --finalize",
                          (root / "production/migration-report.md").read_text())

    def test_conflicts_framework_and_external_symlink_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "outside the framework"):
            migration(FRAMEWORK)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "game"
            root.mkdir()
            (root / "project.yaml").write_text("project:\n  stage: Concept\n")
            legacy = root / "production/stage.txt"
            legacy.parent.mkdir()
            legacy.write_text("Systems Design\n")
            result = migration(root, "migrate", approved=True)
            self.assertEqual(result.returncode, 3)
            self.assertIn("DISAGREE", result.stdout)
            self.assertEqual(legacy.read_text(), "Systems Design\n")
            self.assertEqual((root / "project.yaml").read_text(), "project:\n  stage: Concept\n")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "game"
            root.mkdir()
            outside = Path(directory) / "outside.yaml"
            outside.write_text("do not touch")
            (root / "project.yaml").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes via symlink"):
                migration(root, "migrate", approved=True)
            self.assertEqual(outside.read_text(), "do not touch")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "game"
            root.mkdir()
            foreign = Path(directory) / "foreign"
            (foreign / "docs").mkdir(parents=True)
            (root / ".claude").symlink_to(foreign)
            with self.assertRaisesRegex(ValueError, "escapes via symlink"):
                migration(root)


if __name__ == "__main__":
    unittest.main()
