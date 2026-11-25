"""Offline checks of the M4 evaluation scoring; no model is called."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("run_eval", ROOT / "evaluation/run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


class EvaluationTests(unittest.TestCase):
    def test_cases_file_is_valid(self):
        cases = run_eval.load_cases()
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({case["case_id"] for case in cases}), len(cases))

    def test_score_counts_label_errors(self):
        cases = [{"gold": {"cold_coffee", "slow_service"}}, {"gold": set()}, {"gold": {"other"}}]
        predictions = [{"cold_coffee"}, {"high_prices"}, {"other"}]
        metrics = run_eval.score(cases, predictions)
        self.assertEqual((metrics["tp"], metrics["fp"], metrics["fn"]), (2, 1, 1))
        self.assertAlmostEqual(metrics["exact_match"], 1 / 3)
        self.assertAlmostEqual(metrics["complaint_detection_accuracy"], 2 / 3)
        self.assertEqual(metrics["count_abs_error"], 2)

    def test_keyword_baseline_matches_word_starts_only(self):
        self.assertEqual(run_eval.keyword_labels("Die Preise sind etwas hoch."), {"high_prices"})
        self.assertEqual(run_eval.keyword_labels("La salle était bruyante."), set())


if __name__ == "__main__":
    unittest.main()
