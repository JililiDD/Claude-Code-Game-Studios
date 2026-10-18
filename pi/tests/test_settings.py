import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pi.runtime.settings import PACKAGE_ROOT, all_settings, inspect, reserved, schema_errors, validate


class SettingTests(unittest.TestCase):
    def test_resolved_values_rigor_and_shadowed_local_override(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  rigor: full\n  automation: collaborative\n")
            (game / "project.local.yaml").write_text("modes:\n  automation: guided\n")
            value = inspect(game, "modes.automation")
            self.assertEqual(value["source"], "project.local.yaml")
            self.assertEqual(value["team_value"], "collaborative")
            self.assertEqual(value["value"], "guided")
            self.assertTrue(validate(game, "modes.automation", "autonomous")["shadowed_by_local"])
            self.assertIn("rigor:full", inspect(game, "modes.workflow")["source"])
            self.assertTrue(any(item["key"] == "team.size" for item in all_settings(game)))
            self.assertEqual(schema_errors(game), {})
            self.assertEqual((game / "project.yaml").read_text(),
                             "modes:\n  rigor: full\n  automation: collaborative\n")

    def test_reject_invalid_values_local_locked_malformed_and_empty_operands(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  rigor: full\n")
            with self.assertRaisesRegex(ValueError, "Invalid value"):
                validate(game, "modes.automation", "no-such-mode")
            with self.assertRaisesRegex(ValueError, "cannot be locally overridden"):
                validate(game, "engine.name", "Godot", local=True)
            with self.assertRaisesRegex(ValueError, "nonempty"):
                validate(game, "modes.automation", "")
            with self.assertRaisesRegex(ValueError, "Invalid dotted"):
                inspect(game, "../../outside")
            (game / "project.local.yaml").write_text("modes: [unfinished\n")
            with self.assertRaisesRegex(ValueError, "malformed YAML"):
                inspect(game, "modes.rigor")
        with self.assertRaisesRegex(ValueError, "separate game"):
            inspect(PACKAGE_ROOT, "modes.rigor")

    def test_cli_all_includes_file_tagged_schema_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  automation: unrecognized\n")
            run = subprocess.run([sys.executable, str(PACKAGE_ROOT / "pi/runtime/settings.py"),
                                  "--project", str(game), "--action", "all"],
                                 capture_output=True, text=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(run.stdout)
            self.assertTrue(data["entries"])
            self.assertIn("project.yaml", data["schema_errors"])

    def test_existing_bad_enum_is_not_reported_as_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  automation: unrecognized\n")
            self.assertIn("not a valid value", " ".join(schema_errors(game)["project.yaml"]))
            self.assertEqual(inspect(game, "modes.automation")["value"], "collaborative")
            self.assertEqual(inspect(game, "modes.automation")["team_value"], "unrecognized")

    def test_reserved_keys_are_discovered_and_flagged_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "project.yaml").write_text("modes:\n  rigor: minimal\n")
            for key in reserved():
                with self.subTest(key=key):
                    self.assertTrue(inspect(game, key)["reserved"])
                    value = "none" if key == "accessibility.target" else "example"
                    self.assertTrue(validate(game, key, value)["reserved_warning"])
            self.assertNotIn("platform.cert_tier", reserved(),
                             "A formerly reserved setting is now live")


if __name__ == "__main__":
    unittest.main()
