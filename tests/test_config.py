import os
import tempfile
import unittest

from config import Config


class ConfigPathTests(unittest.TestCase):
    def test_resolve_path_uses_project_root(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                resolved = Config.resolve_path("database_backup.json")
            finally:
                os.chdir(old_cwd)

            self.assertTrue(os.path.isabs(resolved))
            self.assertTrue(resolved.endswith("database_backup.json"))
            self.assertTrue(os.path.exists(resolved))


if __name__ == "__main__":
    unittest.main()
