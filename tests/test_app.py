"""UI checks use explicit fixtures, never presented as live AI validation."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from reviewwise.pipeline import Analysis, BatchResult, Extraction, Review, ReviewWiseError


APP = str(Path(__file__).resolve().parent.parent / "app.py")
ACTION = "Find my next improvements"


def open_app():
    return AppTest.from_file(APP, default_timeout=10).run()


def button(app, label):
    return next(item for item in app.button if item.label == label)


class AppTests(unittest.TestCase):
    def test_initial_page_and_example_do_not_call_ai(self):
        with patch("reviewwise.pipeline.analyze_reviews") as analyze:
            app = open_app()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(button(app, ACTION).disabled)
            button(app, "Try sample reviews").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("De Kaffi war kal", app.text_area[0].value)
            self.assertFalse(button(app, ACTION).disabled)
            analyze.assert_not_called()

    def test_reports_are_invalidated_when_input_changes(self):
        fixture = BatchResult([Analysis(Review(1, "Cold coffee."), Extraction(
            positives=[], complaints=[{"category": "cold_coffee", "quote": "Cold coffee."}],
        ))], 0.1, "offline-ui-fixture")
        with patch("reviewwise.pipeline.analyze_reviews", return_value=fixture) as analyze:
            app = open_app()
            app.text_area[0].input("Cold coffee.").run()
            button(app, ACTION).click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.dataframe), 1)
            self.assertIn("result", app.session_state)
            app.text_area[0].input("Great coffee.").run()
            self.assertNotIn("result", app.session_state)
            analyze.assert_called_once()

    def test_ollama_failure_is_visible_without_a_report(self):
        with patch("reviewwise.pipeline.analyze_reviews", side_effect=ReviewWiseError("Ollama is unavailable. Open Ollama.")):
            app = open_app()
            app.text_area[0].input("Slow service.").run()
            button(app, ACTION).click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("couldn’t reach your local AI", app.error[0].value)
            self.assertTrue(any("Ollama is unavailable" in item.value for item in app.text))
            self.assertNotIn("result", app.session_state)

    def test_pasted_draft_survives_switching_input_modes(self):
        app = open_app()
        app.text_area[0].input("Le café était froid.").run()
        app.radio[0].set_value("Upload CSV").run()
        app.radio[0].set_value("Paste reviews").run()
        self.assertEqual(app.text_area[0].value, "Le café était froid.")
        self.assertFalse(button(app, ACTION).disabled)

    def test_saved_csv_survives_switching_input_modes(self):
        app = open_app()
        app.session_state.saved_csv = b"review\nCold coffee.\nFriendly staff.\n"
        app.session_state.saved_csv_name = "my-reviews.csv"
        app.radio[0].set_value("Upload CSV").run()
        self.assertFalse(button(app, ACTION).disabled)
        app.radio[0].set_value("Paste reviews").run()
        app.radio[0].set_value("Upload CSV").run()
        self.assertEqual(app.session_state.saved_csv_name, "my-reviews.csv")
        self.assertEqual(app.session_state.saved_csv, b"review\nCold coffee.\nFriendly staff.\n")

    def test_matching_report_is_retained_when_switching_back_to_its_input(self):
        fixture = BatchResult([Analysis(Review(1, "Cold coffee."), Extraction(
            positives=[], complaints=[{"category": "cold_coffee", "quote": "Cold coffee."}],
        ))], 0.1, "offline-ui-fixture")
        with patch("reviewwise.pipeline.analyze_reviews", return_value=fixture) as analyze:
            app = open_app()
            app.text_area[0].input("Cold coffee.").run()
            button(app, ACTION).click().run()
            app.radio[0].set_value("Upload CSV").run()
            self.assertNotIn("result", app.session_state)
            app.radio[0].set_value("Paste reviews").run()
            self.assertIn("result", app.session_state)
            analyze.assert_called_once()

    def test_partial_failure_keeps_input_and_does_not_show_a_complete_report(self):
        def fail(reviews, progress=None):
            progress(1, len(reviews))
            raise ReviewWiseError("Review 2 could not be validated after two AI attempts.")

        with patch("reviewwise.pipeline.analyze_reviews", side_effect=fail):
            app = open_app()
            app.text_area[0].input("Cold coffee.\nSlow service.").run()
            button(app, ACTION).click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertNotIn("result", app.session_state)
            self.assertEqual(app.text_area[0].value, "Cold coffee.\nSlow service.")
            self.assertTrue(any("1 of 2 reviews completed" in item.value for item in app.caption))

    def test_positive_only_result_does_not_invent_complaints_or_actions(self):
        fixture = BatchResult([Analysis(Review(1, "Friendly staff."), Extraction(
            positives=["Friendly staff."], complaints=[],
        ))], 0.1, "offline-ui-fixture")
        with patch("reviewwise.pipeline.analyze_reviews", return_value=fixture):
            app = open_app()
            app.text_area[0].input("Friendly staff.").run()
            button(app, ACTION).click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.dataframe), 0)
            self.assertTrue(any("No complaints were identified" in item.value for item in app.info))
            self.assertEqual(app.metric[2].value, "0")

    def test_remote_configuration_does_not_claim_local_processing(self):
        with patch("reviewwise.config.OLLAMA_URL", "https://model.example.test"):
            app = open_app()
            markup = "\n".join(item.value for item in app.markdown)
            self.assertNotIn('>Local processing<', markup)
            self.assertIn('>Configured model service<', markup)
            self.assertTrue(any("model.example.test" in item.value for item in app.caption))
