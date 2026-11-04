"""Exercise prerequisite and service failures without modifying a user's machine."""

import unittest
from unittest.mock import Mock, patch

from scripts import manage


class SetupTests(unittest.TestCase):
    def test_wrong_python_has_a_specific_remedy(self):
        with patch.object(manage.sys, "version_info", (3, 11, 0)):
            with self.assertRaisesRegex(manage.SetupError, "64-bit Python 3.12"):
                manage.check_python()

    def test_missing_ollama_has_installation_instructions(self):
        with patch.object(manage.shutil, "which", return_value=None), patch.object(manage.Path, "is_file", return_value=False):
            with self.assertRaisesRegex(manage.SetupError, "Install Ollama"):
                manage.find_ollama()

    def test_existing_service_is_reused_without_starting_a_process(self):
        with patch.object(manage, "api_json", return_value={"version": "0.40.14"}), patch.object(manage.subprocess, "Popen") as spawn:
            self.assertEqual(manage.ensure_service(), "0.40.14")
            spawn.assert_not_called()

    def test_old_service_is_rejected(self):
        with patch.object(manage, "api_json", return_value={"version": "0.4.0"}):
            with self.assertRaisesRegex(manage.SetupError, "Update Ollama"):
                manage.ensure_service()

    def test_missing_model_is_not_reported_as_installed(self):
        with patch.object(manage, "api_json", return_value={"models": []}):
            self.assertIsNone(manage.installed_model())

    def test_missing_dependencies_have_a_setup_remedy(self):
        with patch.object(manage.Path, "is_file", return_value=False):
            with self.assertRaisesRegex(manage.SetupError, "Run setup.bat"):
                manage.check_dependencies()

    def test_service_that_exits_is_a_startup_failure(self):
        child = Mock()
        child.poll.return_value = 1
        with patch.object(manage, "api_json", return_value=None), \
             patch.object(manage, "find_ollama", return_value="ollama"), \
             patch.object(manage.Path, "mkdir"), \
             patch.object(manage.Path, "open", unittest.mock.mock_open()), \
             patch.object(manage.subprocess, "Popen", return_value=child):
            with self.assertRaisesRegex(manage.SetupError, "did not become ready"):
                manage.ensure_service()
