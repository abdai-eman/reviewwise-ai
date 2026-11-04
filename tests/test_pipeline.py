"""Offline logic tests. Mock responses here are NOT evidence of working AI."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx
from pydantic import ValidationError

from reviewwise.config import MODEL
from reviewwise.pipeline import (
    Analysis, BatchResult, Extraction, Review, ReviewWiseError, analyze_reviews,
    complaint_rows, extract_review, make_reviews, require_model,
    reviews_from_csv, reviews_from_text, validate_extraction,
)
from reviewwise.report import render_report, suggested_actions


ROOT = Path(__file__).resolve().parent.parent


def response(content):
    return SimpleNamespace(message=SimpleNamespace(content=content))


class InputTests(unittest.TestCase):
    def test_multilingual_input_keeps_original_text_and_assigns_ids(self):
        reviews = reviews_from_text("  Café froid.\n\nDe Kaffi war kal.  ")
        self.assertEqual(reviews, [Review(1, "Café froid."), Review(2, "De Kaffi war kal.")])

    def test_empty_oversized_and_too_many_reviews_are_rejected(self):
        for texts in ([], [" "], ["x" * 2001], ["review"] * 11):
            with self.subTest(texts=len(texts)), self.assertRaises(ReviewWiseError):
                make_reviews(texts)

    def test_csv_supports_bom_multiline_quotes_and_accents(self):
        data = '\ufeffreview,unused\r\n"Café froid.\nPersonnel gentil.",ignore\r\n'.encode("utf-8")
        self.assertEqual(reviews_from_csv(data), [Review(1, "Café froid.\nPersonnel gentil.")])

    def test_bad_csv_is_explained(self):
        for data in (b"text\ncoffee", b"review,review\na,b", b"review\na,b", b'\xff', b'review\n"unterminated'):
            with self.subTest(data=data), self.assertRaises(ReviewWiseError):
                reviews_from_csv(data)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.review = Review(7, "Le café était froid, mais le personnel était sympathique.")
        self.good = json.dumps({
            "positives": ["le personnel était sympathique"],
            "complaints": [{"category": "cold_coffee", "quote": "Le café était froid"}],
        })

    def test_exact_nonenglish_evidence_is_accepted(self):
        extraction = validate_extraction(self.good, self.review)
        self.assertEqual(extraction.complaints[0].category, "cold_coffee")

    def test_invented_or_empty_evidence_is_rejected(self):
        for quote in ("the coffee was cold", "", " "):
            data = json.dumps({"positives": [quote], "complaints": []})
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                validate_extraction(data, self.review)

    def test_unknown_categories_extra_keys_and_bad_types_are_rejected(self):
        invalid = [
            {"positives": [], "complaints": [{"category": "service", "quote": "Le café"}]},
            {"positives": [], "complaints": [], "count": 10},
            {"positives": "friendly", "complaints": []},
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate_extraction(json.dumps(data), self.review)

    def test_retry_is_bounded_and_uses_structured_output(self):
        client = Mock()
        client.chat.side_effect = [response("not JSON"), response(self.good)]
        self.assertEqual(extract_review(client, self.review).complaints[0].category, "cold_coffee")
        self.assertEqual(client.chat.call_count, 2)
        self.assertEqual(client.chat.call_args.kwargs["model"], MODEL)
        self.assertEqual(client.chat.call_args.kwargs["format"], Extraction.model_json_schema())
        self.assertEqual(client.chat.call_args.kwargs["options"]["temperature"], 0)

    def test_invalid_extraction_and_timeout_do_not_fabricate_success(self):
        client = Mock()
        client.chat.return_value = response("{}")
        with self.assertRaisesRegex(ReviewWiseError, "No complete report"):
            extract_review(client, self.review)
        self.assertEqual(client.chat.call_count, 2)
        client.chat.side_effect = httpx.ReadTimeout("test timeout")
        with self.assertRaisesRegex(ReviewWiseError, "timed out"):
            extract_review(client, self.review)

    def test_unavailable_ollama_and_missing_model_have_specific_messages(self):
        client = Mock()
        client.list.side_effect = ConnectionError("test connection failure")
        with self.assertRaisesRegex(ReviewWiseError, "Ollama is unavailable"):
            require_model(client)
        client.list.side_effect = None
        client.list.return_value = SimpleNamespace(models=[])
        with self.assertRaisesRegex(ReviewWiseError, "model is missing"):
            require_model(client)

    def test_failed_batch_does_not_return_partial_results(self):
        with patch("reviewwise.pipeline.local_client") as factory:
            client = factory.return_value.__enter__.return_value
            client.list.return_value = SimpleNamespace(models=[SimpleNamespace(model=MODEL, digest="test")])
            client.chat.side_effect = [response(self.good), ConnectionError("test disconnect")]
            with self.assertRaisesRegex(ReviewWiseError, "review 2"):
                analyze_reviews(make_reviews([self.review.text, "The service was slow."]))


class CountingTests(unittest.TestCase):
    def test_m2_reference_counts_given_correct_extraction_labels(self):
        # This isolates counting; it does NOT test whether a real model produces these labels.
        texts = json.loads((ROOT / "experiments/reviews.json").read_text(encoding="utf-8"))
        expected = {
            "slow_service": [1, 6, 8], "cold_coffee": [4, 10], "high_prices": [7, 10],
            "dirty_tables": [5], "incorrect_order": [3], "unfriendly_staff": [9],
        }
        analyses = []
        for number, text in enumerate(texts, 1):
            complaints = [
                {"category": category, "quote": text}
                for category, ids in expected.items() if number in ids
            ]
            # Duplicate extraction of the same category must not inflate counts.
            analyses.append(Analysis(Review(number, text), Extraction(positives=[], complaints=complaints * 2)))
        rows = {row["category"]: row for row in complaint_rows(analyses)}
        for category, numbers in expected.items():
            self.assertEqual(rows[category]["Reviews"], len(numbers))
            self.assertEqual(rows[category]["Review numbers"], ", ".join(map(str, numbers)))
        report = render_report(BatchResult(analyses, 1.25, "test-fixture"))
        self.assertIn("Slow service: 3 review(s); reviews 1, 6, 8", report)
        self.assertEqual(len(suggested_actions(analyses)), 3)

    def test_positive_only_input_does_not_invent_complaints_or_actions(self):
        analyses = [Analysis(Review(1, "Excellent coffee!"), Extraction(positives=["Excellent coffee!"], complaints=[]))]
        self.assertEqual(complaint_rows(analyses), [])
        self.assertEqual(suggested_actions(analyses), [])
        self.assertIn("No complaints extracted", render_report(BatchResult(analyses, 0.1, "test")))

    def test_other_feedback_does_not_become_a_fabricated_specific_action(self):
        analyses = [Analysis(Review(1, "Too noisy."), Extraction(
            positives=[], complaints=[{"category": "other", "quote": "Too noisy."}],
        ))]
        self.assertEqual(complaint_rows(analyses)[0]["Reviews"], 1)
        self.assertEqual(suggested_actions(analyses), [])
