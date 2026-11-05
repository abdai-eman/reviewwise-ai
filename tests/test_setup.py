"""Exercise prerequisite and service failures without modifying a user's machine."""

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from scripts import manage


class SetupTests(unittest.TestCase):
    def test_wrong_python_has_a_specific_remedy(self):
        with patch.object(manage.sys, "version_info", (3, 10, 0)):
            with self.assertRaisesRegex(manage.SetupError, "64-bit Python 3.11-3.15"):
                manage.check_python()

    def test_supported_existing_python_versions_are_accepted(self):
        for minor in range(11, 16):
            with self.subTest(minor=minor), patch.object(manage.sys, "version_info", (3, minor, 0)), patch.object(manage.struct, "calcsize", return_value=8):
                manage.check_python()

    def test_32bit_python_is_rejected(self):
        with patch.object(manage.struct, "calcsize", return_value=4):
            with self.assertRaisesRegex(manage.SetupError, "64-bit"):
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
            with self.assertRaisesRegex(manage.SetupError, "START_REVIEWWISE.bat"):
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


class AutomaticLaunchTests(unittest.TestCase):
    def test_warm_start_does_not_reinstall_python_packages(self):
        with patch.object(manage, "check_dependencies"), \
             patch.object(manage.venv, "create") as create, \
             patch.object(manage, "run") as run:
            manage.ensure_dependencies()
            create.assert_not_called()
            run.assert_not_called()

    def test_missing_environment_is_created_with_verified_binary_packages(self):
        with patch.object(manage, "check_dependencies", side_effect=manage.SetupError("missing")), \
             patch.object(manage.Path, "is_file", return_value=False), \
             patch.object(manage.venv, "create") as create, \
             patch.object(manage, "run") as run, \
             patch.object(manage, "MARKER") as marker, \
             patch.object(manage, "requirements_digest", return_value="lock-hash"):
            manage.ensure_dependencies()
            create.assert_called_once_with(manage.VENV, with_pip=True)
            install = next(call.args[0] for call in run.call_args_list if "install" in call.args[0])
            self.assertIn("--require-hashes", install)
            self.assertIn("--only-binary=:all:", install)
            marker.write_text.assert_called_once_with("lock-hash")

    def test_dependency_failure_does_not_mark_setup_as_complete(self):
        with patch.object(manage, "check_dependencies", side_effect=manage.SetupError("missing")), \
             patch.object(manage.Path, "is_file", return_value=True), \
             patch.object(manage, "run", side_effect=[None, manage.SetupError("install failed")]), \
             patch.object(manage, "MARKER") as marker:
            with self.assertRaisesRegex(manage.SetupError, "install failed"):
                manage.ensure_dependencies()
            marker.write_text.assert_not_called()

    def test_existing_ollama_is_reused_without_winget(self):
        with patch.object(manage, "find_ollama", return_value="existing-ollama"), \
             patch.object(manage, "run") as run:
            self.assertEqual(manage.install_ollama_if_missing(), "existing-ollama")
            run.assert_not_called()

    def test_missing_ollama_uses_exact_official_winget_package_for_current_user(self):
        with patch.object(manage, "find_ollama", side_effect=[manage.SetupError("missing"), "installed-ollama"]), \
             patch.object(manage.platform, "system", return_value="Windows"), \
             patch.object(manage.shutil, "which", return_value="winget.exe"), \
             patch.object(manage, "run") as run:
            self.assertEqual(manage.install_ollama_if_missing(), "installed-ollama")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--id") + 1], "Ollama.Ollama")
            self.assertEqual(command[command.index("--source") + 1], "winget")
            self.assertEqual(command[command.index("--scope") + 1], "user")
            self.assertIn("--exact", command)
            self.assertNotIn("--ignore-security-hash", command)

    def test_missing_winget_has_a_manual_fallback(self):
        with patch.object(manage, "find_ollama", side_effect=manage.SetupError("missing")), \
             patch.object(manage.platform, "system", return_value="Windows"), \
             patch.object(manage.shutil, "which", return_value=None), \
             patch.object(manage, "run") as run:
            with self.assertRaisesRegex(manage.SetupError, "https://ollama.com/download/windows"):
                manage.install_ollama_if_missing()
            run.assert_not_called()

    def test_winget_install_failure_stops_before_claiming_success(self):
        with patch.object(manage, "find_ollama", side_effect=manage.SetupError("missing")), \
             patch.object(manage.platform, "system", return_value="Windows"), \
             patch.object(manage.shutil, "which", return_value="winget.exe"), \
             patch.object(manage, "run", side_effect=manage.SetupError("installation denied")):
            with self.assertRaisesRegex(manage.SetupError, "installation denied"):
                manage.install_ollama_if_missing()

    def test_ready_model_needs_no_download_or_installer(self):
        with patch.object(manage, "api_json", return_value={"version": "0.40.14"}), \
             patch.object(manage, "ensure_service", return_value="0.40.14"), \
             patch.object(manage, "installed_model", return_value={"name": manage.MODEL}), \
             patch.object(manage, "install_ollama_if_missing") as install, \
             patch.object(manage.subprocess, "run") as run:
            self.assertEqual(manage.ensure_model(), "0.40.14")
            install.assert_not_called()
            run.assert_not_called()

    def test_missing_model_is_pulled_and_checked_before_launch(self):
        with patch.object(manage, "api_json", return_value={"version": "0.40.14"}), \
             patch.object(manage, "ensure_service", return_value="0.40.14"), \
             patch.object(manage, "installed_model", side_effect=[None, {"name": manage.MODEL}]), \
             patch.object(manage, "install_ollama_if_missing", return_value="ollama.exe"), \
             patch.object(manage.subprocess, "run") as run:
            manage.ensure_model()
            self.assertEqual(run.call_args.args[0], ["ollama.exe", "pull", manage.MODEL])
            self.assertEqual(run.call_args.kwargs["env"]["OLLAMA_HOST"], "127.0.0.1:11434")

    def test_unregistered_model_download_does_not_report_success(self):
        with patch.object(manage, "api_json", return_value={"version": "0.40.14"}), \
             patch.object(manage, "ensure_service", return_value="0.40.14"), \
             patch.object(manage, "installed_model", return_value=None), \
             patch.object(manage, "install_ollama_if_missing", return_value="ollama.exe"), \
             patch.object(manage.subprocess, "run"):
            with self.assertRaisesRegex(manage.SetupError, "did not register the model"):
                manage.ensure_model()

    def test_launcher_prepares_dependencies_and_model_before_opening_app(self):
        order = []
        with patch.object(manage, "ensure_dependencies", side_effect=lambda: order.append("dependencies")), \
             patch.object(manage, "ensure_model", side_effect=lambda: order.append("model")), \
             patch.object(manage, "existing_app_url", return_value=None), \
             patch.object(manage, "available_port", return_value=8502), \
             patch.object(manage, "run_app", side_effect=lambda *args: order.append("app")) as run:
            manage.launch()
            self.assertEqual(order, ["dependencies", "model", "app"])
            self.assertIn("--server.headless=false", run.call_args.args[0])
            self.assertIn("--server.port=8502", run.call_args.args[0])

    def test_failed_model_preparation_does_not_launch_app(self):
        with patch.object(manage, "ensure_dependencies"), \
             patch.object(manage, "existing_app_url", return_value=None), \
             patch.object(manage, "ensure_model", side_effect=manage.SetupError("download blocked")), \
             patch.object(manage, "run") as run:
            with self.assertRaisesRegex(manage.SetupError, "download blocked"):
                manage.launch()
            run.assert_not_called()

    def test_repeated_launch_reuses_existing_app_without_dependencies_model_or_process_start(self):
        with patch.object(manage, 'existing_app_url', return_value='http://127.0.0.1:8501'), \
             patch.object(manage, 'ensure_dependencies') as dependencies, \
             patch.object(manage, 'ensure_model') as model, \
             patch.object(manage, 'run_app') as spawn, \
             patch.object(manage.webbrowser, 'open') as browser:
            manage.launch()
            dependencies.assert_not_called()
            model.assert_not_called()
            spawn.assert_not_called()
            browser.assert_called_once_with('http://127.0.0.1:8501')

    def test_stale_or_other_project_metadata_is_not_reused(self):
        with TemporaryDirectory() as directory, patch.object(manage, 'STATE', Path(directory)), patch.object(manage, 'process_alive', return_value=False):
            path = Path(directory) / 'app.json'
            for state in [{'root': str(manage.ROOT.resolve()), 'pid': 123, 'port': 8501},
                          {'root': '/another-project', 'pid': 123, 'port': 8501}]:
                path.write_text(json.dumps(state))
                self.assertIsNone(manage.existing_app_url())
            path.write_text('invalid JSON')
            self.assertIsNone(manage.existing_app_url())

    def test_interrupted_launcher_terminates_only_its_child_and_clears_metadata(self):
        child = Mock(pid=123)
        child.wait.side_effect = KeyboardInterrupt
        child.poll.return_value = None
        with TemporaryDirectory() as directory, patch.object(manage, 'STATE', Path(directory)), patch.object(manage.subprocess, 'Popen', return_value=child):
            with self.assertRaises(KeyboardInterrupt):
                manage.run_app(['fixture-streamlit'], 8501)
            child.terminate.assert_called_once()
            self.assertFalse((Path(directory) / 'app.json').exists())

    def test_real_model_smoke_does_not_claim_success_for_an_incomplete_result(self):
        from reviewwise.pipeline import BatchResult, Review
        partial = BatchResult([], .1, 'fixture', pending=[Review(1, 'Cold coffee.')])
        with patch.object(manage.sys, 'argv', ['manage.py', 'smoke', '--text', 'Cold coffee.']), \
             patch.object(manage, 'check_dependencies'), patch.object(manage, 'ensure_service'), \
             patch('reviewwise.pipeline.analyze_reviews', return_value=partial):
            with self.assertRaisesRegex(manage.SetupError, 'smoke test is incomplete'):
                manage.main()

    def test_busy_port_uses_an_available_loopback_port(self):
        with patch.object(manage.socket, "socket") as factory:
            probe = factory.return_value.__enter__.return_value
            probe.bind.side_effect = [OSError("busy"), None]
            probe.getsockname.return_value = ("127.0.0.1", 54321)
            self.assertEqual(manage.available_port(8501), 54321)
            self.assertEqual(probe.bind.call_args_list[1].args[0], ("127.0.0.1", 0))
