"""UI checks use explicit fixtures, never presented as live AI validation."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from reviewwise.pipeline import Analysis, BatchResult, Extraction, Review, ReviewWiseError


APP = str(Path(__file__).resolve().parent.parent / "app.py")


def button(app, label):
    return next(item for item in app.button if item.label == label)


class AppTests(unittest.TestCase):
    def test_initial_page_and_example_do_not_call_ai(self):
        with patch("reviewwise.pipeline.analyze_reviews") as analyze:
            app = AppTest.from_file(APP).run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(button(app, "Analyze reviews").disabled)
            button(app, "Load fictional M2 example").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("De Kaffi war kal", app.text_area[0].value)
            self.assertFalse(button(app, "Analyze reviews").disabled)
            analyze.assert_not_called()

    def test_reports_are_invalidated_when_input_changes(self):
        fixture = BatchResult([Analysis(Review(1, "Cold coffee."), Extraction(
            positives=[], complaints=[{"category": "cold_coffee", "quote": "Cold coffee."}],
        ))], 0.1, "offline-ui-fixture")
        with patch("reviewwise.pipeline.analyze_reviews", return_value=fixture) as analyze:
            app = AppTest.from_file(APP).run()
            app.text_area[0].input("Cold coffee.").run()
            button(app, "Analyze reviews").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.dataframe), 1)
            self.assertIn("result", app.session_state)
            app.text_area[0].input("Great coffee.").run()
            self.assertNotIn("result", app.session_state)
            analyze.assert_called_once()

    def test_ollama_failure_is_visible_without_a_report(self):
        with patch("reviewwise.pipeline.analyze_reviews", side_effect=ReviewWiseError("Ollama is unavailable. Open Ollama.")):
            app = AppTest.from_file(APP).run()
            app.text_area[0].input("Slow service.").run()
            button(app, "Analyze reviews").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("Ollama is unavailable", app.error[0].value)
            self.assertNotIn("result", app.session_state)
