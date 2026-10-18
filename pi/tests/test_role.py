import unittest

from pi.runtime.role import load, names


class RoleTests(unittest.TestCase):
    def test_all_roles_have_readable_body(self):
        roles = names()
        self.assertEqual(len(roles), 49)
        self.assertIn("creative-director", roles)
        for name in roles:
            with self.subTest(role=name):
                self.assertTrue(load(name))

    def test_role_name_is_restricted_to_known_files(self):
        with self.assertRaisesRegex(ValueError, "Unknown CCGS role"):
            load("../../project")


if __name__ == "__main__":
    unittest.main()
